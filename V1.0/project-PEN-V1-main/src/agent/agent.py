"""
PEN Agent - Main Orchestrator

This module defines the core PENAgent class, which orchestrates the conversation
flow, memory management, and tool execution.

Refactored to use new layered memory architecture (L1, L2, L2.5, L4).
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import time

# Ensure the project root is in the Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.config import DATA_DIR, SERVICE_ACCOUNT_FILE, EMAIL_CONFIG, MAX_WORKERS, GEMINI_API_KEY  # type: ignore
from src.storage.data_manager import DataManager  # type: ignore
from src.agent_tools.data_tools import DataTools  # type: ignore
from src.agent_tools.email_tools import EmailTools  # type: ignore
from src.agent_tools.whatsapp_tools import WhatsAppTools  # type: ignore
from src.agent_tools.drive_tools import DriveTools  # type: ignore
from src.agent_tools.web_tools import WebTools  # type: ignore
from src.agent_tools.refresh_tools import RefreshTools  # type: ignore
from src.agent_tools.context_tools import ContextTools  # type: ignore
# L4 removed - using new layer architecture L4
from src.utils.logger import get_logger  # type: ignore
from src.agent.tool_executor import ToolExecutor  # type: ignore
from src.agent.tool_definitions import TOOLS  # type: ignore

# Memory layers - New architecture
from layers.layer_manager import LayerManager  # type: ignore
from layers.L1 import MessageRole  # type: ignore
from layers.L4 import L4UserProfile  # type: ignore

logger = get_logger(__name__)

# ============================================================================
# Constants
# ============================================================================

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_MAX_TOKENS = 24576
RATE_LIMIT_DELAY = 2  # seconds between API calls

# ============================================================================
# PEN Agent Class
# ============================================================================

class PENAgent:
    """
    Orchestrates the conversational flow, memory, and tool use for the PEN assistant.
    
    Uses new layered memory architecture:
    - L1: Active session memory (auto-persisted to JSON)
    - L2: Archived sessions
    - L2.5: Keyword-indexed search
    - L4: User profile (existing system)
    """

    def __init__(self, api_key: str, minimax_api_key: Optional[str] = None):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required.")

        genai.configure(api_key=api_key)

        # Memory Layers - New Architecture
        self.layer_manager = LayerManager()
        
        # L4 User Profile - New Architecture
        self.l4 = L4UserProfile()

        # System Prompt Template
        self.system_prompt_template = self._load_system_prompt_template()

        # Gemini Model Client (initialized on first use)
        self.client: Optional[genai.GenerativeModel] = None
        self.model_name = DEFAULT_MODEL

        # Tool Setup
        self.data_manager = DataManager(DATA_DIR)
        self.tool_declarations = self._build_tool_declarations()
        self.tool_executor = self._initialize_tool_executor()
        self.valid_tool_names = [tool["name"] for tool in TOOLS]

        # Conversation History for the current session (for the model)
        # Load existing L1 messages into Gemini conversation history
        self.messages: List[Any] = []
        self._load_l1_into_conversation()

    def _load_l1_into_conversation(self) -> None:
        """Load existing L1 messages into Gemini conversation history."""
        try:
            l1_messages = self.layer_manager.l1.get_all_messages()
            
            for msg in l1_messages:
                role = msg.get("role")
                content = msg.get("content", "")
                
                # Convert L1 roles to Gemini roles
                if role == "user":
                    self.messages.append({"role": "user", "parts": [content]})
                elif role == "assistant":
                    self.messages.append({"role": "model", "parts": [content]})
                # Skip tool messages for now (they need special handling)
            
            if l1_messages:
                logger.info(f"Loaded {len(l1_messages)} messages from L1 into conversation history")
        except Exception as e:
            logger.warning(f"Could not load L1 messages: {e}")

    def _load_system_prompt_template(self) -> str:
        """Loads the system prompt from a file."""
        return """You are PENNY (Personal Assistant), an AI assistant. Your goal is to support the user, acting as a friend or assistant depending on the situation.
To do this, you use tools. You can help the user proactively or in a question-answer format as needed.

You are an agent, and the user doesn't communicate with you through a single chat session. Your memory and information are preserved based on how you save them. Use memory tools to remember and maintain continuity.

IMPORTANT: Current time is {current_time}.

{l4_context}

{episodic_context}
"""

    def _initialize_tool_executor(self) -> ToolExecutor:
        """Initializes all tool classes and the ToolExecutor."""
        data_tools = DataTools(self.data_manager)
        email_tools = EmailTools(self.data_manager)
        whatsapp_tools = WhatsAppTools(self.data_manager)
        brave_api_key = os.getenv("BRAVE_API_KEY")
        web_tools = WebTools(brave_api_key=brave_api_key)
        refresh_tools = RefreshTools(
            data_manager=self.data_manager,
            email_config=EMAIL_CONFIG,
            service_account_file=str(SERVICE_ACCOUNT_FILE) if SERVICE_ACCOUNT_FILE.exists() else None
        )
        context_tools = ContextTools(self.l4)
        
        drive_tools: Optional[DriveTools] = None
        if SERVICE_ACCOUNT_FILE.exists():
            try:
                drive_tools = DriveTools(str(SERVICE_ACCOUNT_FILE), folder_name="Wpmesages")
            except Exception as e:
                logger.error(f"Failed to initialize DriveTools: {e}")

        return ToolExecutor(
            data_tools=data_tools,
            email_tools=email_tools,
            whatsapp_tools=whatsapp_tools,
            web_tools=web_tools,
            refresh_tools=refresh_tools,
            context_tools=context_tools,
            drive_tools=drive_tools,
        )

    def _build_tool_declarations(self) -> List[genai.protos.FunctionDeclaration]:
        """Builds the list of tool declarations for the Gemini API."""
        tool_declarations = []
        for tool in TOOLS:
            properties = {}
            for k, v in tool["input_schema"].get("properties", {}).items():
                prop_type = v.get("type", "string").upper()
                if prop_type == "INTEGER":
                    prop_type = "NUMBER"
                
                # Array tipi için items field'ı ekle
                if prop_type == "ARRAY":
                    items_type = v.get("items", {}).get("type", "string").upper()
                    properties[k] = genai.protos.Schema(
                        type_=prop_type,
                        description=v.get("description", ""),
                        items=genai.protos.Schema(type_=items_type)
                    )
                else:
                    properties[k] = genai.protos.Schema(
                        type_=prop_type,
                        description=v.get("description", "")
                    )
            
            tool_declarations.append(
                genai.protos.FunctionDeclaration(
                    name=tool["name"],
                    description=tool["description"],
                    parameters=genai.protos.Schema(
                        type_="OBJECT",
                        properties=properties,
                        required=tool["input_schema"].get("required", [])
                    )
                )
            )
        return tool_declarations

    def _get_system_prompt(self) -> str:
        """Constructs the final system prompt with dynamic context."""
        # L4 Context - Complete user profile and all contexts
        l4_data = self.l4.load_profile()
        user_profile = l4_data.get("user_profile", {})
        contexts = l4_data.get("contexts", {}).get("by_id", {})
        
        # Format L4 context with user profile and all stored contexts
        l4_context_parts = ["=== L4 User Profile & Contexts ==="]
        
        # User profile section
        if user_profile:
            l4_context_parts.append("\n📋 User Profile:")
            for key, value in user_profile.items():
                if value:
                    if isinstance(value, list):
                        if value:
                            l4_context_parts.append(f"  {key}: {', '.join(str(v) for v in value)}")
                    else:
                        l4_context_parts.append(f"  {key}: {value}")
        
        # Contexts section
        if contexts:
            l4_context_parts.append(f"\n📌 Stored Contexts ({len(contexts)} total):")
            for ctx_id, ctx_data in contexts.items():
                ctx_type = ctx_data.get("type", "unknown")
                title = ctx_data.get("title", "Untitled")
                date = ctx_data.get("date", "")
                status = ctx_data.get("status", "")
                priority = ctx_data.get("priority", "")
                description = ctx_data.get("description", "")
                notes = ctx_data.get("notes", "")
                
                ctx_str = f"  • [{ctx_type}] {title}"
                if date:
                    ctx_str += f" ({date})"
                if status:
                    ctx_str += f" - {status}"
                if priority:
                    ctx_str += f" [priority: {priority}]"
                l4_context_parts.append(ctx_str)
                
                if description:
                    l4_context_parts.append(f"    Description: {description}")
                if notes:
                    l4_context_parts.append(f"    Notes: {notes}")
        
        l4_context = "\n".join(l4_context_parts)

        # L2.5 Context (Recent Episodes) - New architecture
        recent_sessions = self.layer_manager.l2_5.get_recent_sessions(limit=3)
        episodic_context = ""
        if recent_sessions:
            episodic_context = "Recent Episodes (L2.5):\n"
            for session_data in recent_sessions:
                date = session_data.get("created_at", "")[:10]  # YYYY-MM-DD
                summary = session_data.get("summary", "")
                episodic_context += f"- {date}: {summary}\n"

        current_time = datetime.now().strftime("%d %B %Y, %H:%M")

        return self.system_prompt_template.format(
            current_time=current_time,
            l4_context=l4_context,
            episodic_context=episodic_context.strip()
        )

    def _ensure_client(self):
        """Ensures the Gemini client is initialized with the latest system prompt."""
        if self.client is None:
            final_prompt = self._get_system_prompt()
            logger.info(f"==== FINAL SYSTEM PROMPT ====\n{final_prompt}")
            self.client = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=final_prompt
            )

    def chat(self, user_message: str) -> str:
        """
        Main chat loop for processing user input.
        
        Uses new layer architecture:
        - Adds messages to L1 (auto-persisted)
        - Maintains Gemini conversation history
        - Handles tool calls
        """
        self._ensure_client()
        assert self.client is not None, "Client should be initialized"

        # Add user message to L1 (new architecture)
        self.layer_manager.add_user_message(user_message)
        self.messages.append({"role": "user", "parts": [user_message]})

        while True:
            try:
                # Rate limiting
                time.sleep(RATE_LIMIT_DELAY)
                
                response = self.client.generate_content(
                    self.messages,
                    tools=[genai.protos.Tool(function_declarations=self.tool_declarations)],
                    generation_config=genai.types.GenerationConfig(max_output_tokens=DEFAULT_MAX_TOKENS)
                )

                candidate = response.candidates[0]
                if not candidate.content.parts:
                    return "I'm sorry, I couldn't generate a response."

                # Check for tool calls
                tool_calls = [part.function_call for part in candidate.content.parts if hasattr(part, 'function_call')]

                if not tool_calls:
                    # No tool calls, it's a final text response
                    text_response = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                    self.layer_manager.add_assistant_message(text_response)
                    self.messages.append({"role": "model", "parts": [text_response]})
                    return text_response

                # Execute tool calls
                self.messages.append(candidate.content)  # Add assistant's turn with tool calls
                tool_results = []
                tool_names = []
                
                for tool_call in tool_calls:
                    tool_name = tool_call.name
                    
                    # Skip invalid tool calls
                    if not tool_name or not isinstance(tool_name, str):
                        logger.warning(f"Skipping invalid tool call with name: {tool_name}")
                        print(f"Skipping invalid tool call with name: {tool_name}")
                        continue
                    
                    tool_names.append(tool_name)
                    tool_input = dict(tool_call.args) if tool_call.args else {}
                    
                    # Log the tool call for debugging
                    logger.debug(f"Tool call: {tool_name} with args: {tool_input}")
                    
                    result_str = self.tool_executor.execute(tool_name, tool_input)
                    
                    try:
                        result_dict = json.loads(result_str)
                    except json.JSONDecodeError:
                        result_dict = {"error": "Invalid JSON response from tool"}
                    
                    # Record tool call in L1 (convert to JSON-serializable format)
                    try:
                        # Ensure tool_output is JSON-serializable
                        serializable_output = json.loads(json.dumps(result_dict, default=str))
                    except:
                        serializable_output = {"result": str(result_dict)}
                    
                    self.layer_manager.add_tool_call(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        tool_output=serializable_output
                    )
                    
                    tool_results.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tool_name,
                                response=result_dict
                            )
                        )
                    )

                # Log and append tool results to history
                if tool_names:
                    tools_str = ", ".join(tool_names)
                    print(f"🔧 [{tools_str}]", end=" ", flush=True)
                    self.messages.append({"role": "user", "parts": tool_results})
                    # Continue loop to get model's final response based on tool results
                else:
                    # No valid tool calls, treat as text response
                    text_response = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                    if text_response:
                        self.layer_manager.add_assistant_message(text_response)
                        self.messages.append({"role": "model", "parts": [text_response]})
                        return text_response
                    else:
                        return "I'm sorry, I couldn't generate a response."
            
            except Exception as e:
                logger.error(f"Error in chat loop: {e}", exc_info=True)
                return f"An error occurred: {str(e)}"

    def sleep(self):
        """
        Archives the current session and prepares for a new one.
        
        Complete sleep cycle:
        1. Update L4 from conversation
        2. Trigger layer sleep cycle (L1 → Gemini → L2 + L2.5)
        3. Clear L1 for new session
        4. Reset Gemini conversation history
        """
        logger.info("Initiating sleep cycle...")
        
        # Step 1: Update L4 from L1 session data
        logger.info("Updating L4 user profile from L1 session...")
        try:
            l4_result = self.update_l4_from_conversation()
            
            if l4_result.get("status") == "success":
                updates_count = l4_result.get("updates_count", 0)
                logger.info(f"L4 updated successfully: {updates_count} new insights")
            elif l4_result.get("status") != "no_messages":
                logger.warning(f"L4 update issue: {l4_result.get('message', 'Unknown')}")
        except Exception as e:
            logger.error(f"L4 update error (non-critical): {e}")
        
        # Step 2: Trigger layer sleep cycle (L1 → L2 + L2.5)
        result = self.layer_manager.trigger_sleep_cycle()
        
        if result.get("status") == "success":
            logger.info(f"Sleep cycle completed: {result.get('message')}")
            logger.info(f"Details: {result.get('details')}")
        else:
            logger.error(f"Sleep cycle failed: {result.get('message')}")
        
        # Step 3: Reset Gemini conversation history
        self.reset()

    def reset(self):
        """Resets the in-memory conversation history for the model."""
        self.messages = []
        logger.info("Agent conversation history reset.")

    def update_l4_from_conversation(self) -> Dict[str, Any]:
        """
        Updates L4 user profile from L1 session data.
        
        Returns:
            Dictionary with update status and details
        """
        try:
            l1_session_context = self.layer_manager.l1.get_session_context()
            if not l1_session_context.get("messages"):
                return {"status": "no_messages"}
            
            result = self.l4.update_profile_from_session(l1_session_context)
            logger.info(f"L4 updated from L1 session: {result.get('status', 'success')}")
            return result
        except Exception as e:
            logger.error(f"L4 update error: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
