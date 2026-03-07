"""
L1: Active Session-Based Memory Layer.

Manages the current session's memory. All messages, tool outputs, and interactions
accumulate here during the session. This is the primary working memory.

Session lifecycle:
- Created when session starts
- Accumulates all interactions
- Archived to L2 when session ends (sleep initiated)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4
import json
import os

try:
    from src.utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class InteractionType(str, Enum):
    """Type of interaction in the session."""
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    TOOL_OUTPUT = "tool_output"
    SYSTEM_EVENT = "system_event"


@dataclass
class Message:
    """Represents a single message in the session."""
    
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)
    is_internal: bool = False  # Deep think, internal reasoning - not persisted
    
    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for serialization."""
        # Internal messages (deep think) are not persisted to L1.json
        if self.is_internal:
            return None
        
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "metadata": self.metadata,
        }


@dataclass
class ToolInteraction:
    """Represents a tool call and its output."""
    
    tool_name: str
    tool_input: dict[str, Any]
    tool_output: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    interaction_id: str = field(default_factory=lambda: str(uuid4()))
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None
    # Context management fields
    collapsed: bool = False
    ttl_counter: int = -1  # -1 = no TTL (system inactive), 0+ = active countdown
    output_size: int = 0  # Character count of output
    expand_count: int = 0  # How many times this output was expanded (for TTL doubling)
    pinned: bool = False  # If True, never auto-collapse (after 3+ expands)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert tool interaction to dictionary for serialization."""
        # Ensure tool_output is JSON-serializable
        tool_output = self.tool_output
        try:
            # Try to serialize directly
            json.dumps(tool_output)
        except (TypeError, ValueError):
            # If it fails, convert to string
            tool_output = str(tool_output)
        
        # Ensure tool_input is also JSON-serializable
        tool_input = self.tool_input
        try:
            json.dumps(tool_input)
        except (TypeError, ValueError):
            # Convert complex objects to strings
            tool_input = {k: str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v 
                         for k, v in tool_input.items()} if isinstance(tool_input, dict) else str(tool_input)
        
        return {
            "tool_name": self.tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output,
            "timestamp": self.timestamp.isoformat(),
            "interaction_id": self.interaction_id,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
            "collapsed": self.collapsed,
            "ttl_counter": self.ttl_counter,
            "output_size": self.output_size,
            "expand_count": self.expand_count,
            "pinned": self.pinned,
        }


@dataclass
class SessionMetadata:
    """Metadata for the current session."""
    
    session_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    tool_call_count: int = 0
    system_state: dict[str, bool] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": self.message_count,
            "tool_call_count": self.tool_call_count,
            "system_state": self.system_state,
        }


class L1:
    """
    Active Session Memory Layer.
    
    Maintains all interactions during the current session. No summarization,
    no archival - just accumulation of all data. Model has 1M context window,
    so 100 messages is not a problem.
    
    Attributes:
        session_metadata: Session information
        messages: List of all messages in session
        tool_interactions: List of all tool calls and outputs
        data_file: Path to L1.json storage
    """
    
    def __init__(self, data_dir: Optional[str] = None) -> None:
        """
        Initialize L1 session memory.
        
        Auto-loads from L1.json if exists, otherwise starts fresh.
        
        Args:
            data_dir: Optional custom data directory. Defaults to layers/data/
        """
        if data_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(script_dir, "data")
        
        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, "L1.json")
        
        self._ensure_data_directory()
        
        # Try to load existing session from disk
        if os.path.exists(self.data_file):
            loaded = self.load_from_file()
            if not loaded:
                # If load failed, start fresh
                self.session_metadata = SessionMetadata()
                self.messages: list[Message] = []
                self.tool_interactions: list[ToolInteraction] = []
        else:
            # No existing file, start fresh
            self.session_metadata = SessionMetadata()
            self.messages: list[Message] = []
            self.tool_interactions: list[ToolInteraction] = []
            # Save initial state to disk
            self.save_to_file()
    
    def _ensure_data_directory(self) -> None:
        """Ensure data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> Message:
        """
        Add a message to the session.
        
        Args:
            role: Message role (user, assistant, system, tool)
            content: Message content
            metadata: Optional metadata dictionary
            
        Returns:
            The created Message object
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.session_metadata.message_count += 1
        self._update_last_activity()
        
        # Auto-save to disk after state change
        self.save_to_file()
        
        return message
    
    def add_tool_interaction(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: Any,
        execution_time_ms: Optional[float] = None,
        error: Optional[str] = None
    ) -> ToolInteraction:
        """
        Record a tool call and its output.
        
        Args:
            tool_name: Name of the tool
            tool_input: Input parameters to the tool
            tool_output: Output from the tool
            execution_time_ms: Execution time in milliseconds
            error: Error message if tool failed
            
        Returns:
            The created ToolInteraction object
        """
        # Calculate output size for TTL system
        output_str = tool_output
        if not isinstance(output_str, str):
            try:
                output_str = json.dumps(output_str)
            except:
                output_str = str(output_str)
        output_size = len(output_str)
        
        interaction = ToolInteraction(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            execution_time_ms=execution_time_ms,
            error=error,
            output_size=output_size
        )
        self.tool_interactions.append(interaction)
        self.session_metadata.tool_call_count += 1
        self._update_last_activity()
        
        # Auto-save to disk after state change
        self.save_to_file()
        
        return interaction
    
    def get_session_summary(self) -> dict[str, Any]:
        """
        Get a summary of the current session.
        
        Returns:
            Dictionary containing session metadata and statistics
        """
        return {
            "metadata": self.session_metadata.to_dict(),
            "message_count": len(self.messages),
            "tool_interaction_count": len(self.tool_interactions),
            "session_duration_seconds": (
                datetime.utcnow() - self.session_metadata.created_at
            ).total_seconds()
        }
    
    def get_all_messages(self) -> list[dict[str, Any]]:
        """
        Get all messages in the session.
        
        Returns:
            List of message dictionaries (internal messages excluded)
        """
        return [msg.to_dict() for msg in self.messages if msg.to_dict() is not None]
    
    def get_all_tool_interactions(self) -> list[dict[str, Any]]:
        """
        Get all tool interactions in the session.
        
        Returns:
            List of tool interaction dictionaries
        """
        result = []
        for interaction in self.tool_interactions:
            try:
                result.append(interaction.to_dict())
            except Exception as e:
                # If serialization fails, create a minimal dict
                print(f"Warning: Failed to serialize tool interaction {interaction.tool_name}: {e}")
                result.append({
                    "tool_name": interaction.tool_name,
                    "tool_input": str(interaction.tool_input),
                    "tool_output": str(interaction.tool_output),
                    "timestamp": interaction.timestamp.isoformat(),
                    "interaction_id": interaction.interaction_id,
                    "error": str(e)
                })
        return result
    
    def get_session_context(self) -> dict[str, Any]:
        """
        Get the complete session context for archival or processing.
        
        Returns:
            Complete session data including metadata, messages, and tool interactions
        """
        return {
            "session_id": self.session_metadata.session_id,
            "metadata": self.session_metadata.to_dict(),
            "messages": self.get_all_messages(),
            "tool_interactions": self.get_all_tool_interactions()
        }
    
    def save_to_file(self) -> bool:
        """
        Save current session to L1.json file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "session_id": self.session_metadata.session_id,
                "metadata": self.session_metadata.to_dict(),
                "messages": self.get_all_messages(),
                "tool_interactions": self.get_all_tool_interactions(),
                "saved_at": datetime.utcnow().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving L1 session to file: {e}")
            return False
    
    def load_from_file(self) -> bool:
        """
        Load session from L1.json file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.data_file):
                return False
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Restore session metadata
            metadata_dict = data.get("metadata", {})
            self.session_metadata = SessionMetadata(
                session_id=data.get("session_id", str(uuid4())),
                created_at=datetime.fromisoformat(metadata_dict.get("created_at", datetime.utcnow().isoformat())),
                last_activity=datetime.fromisoformat(metadata_dict.get("last_activity", datetime.utcnow().isoformat())),
                message_count=metadata_dict.get("message_count", 0),
                tool_call_count=metadata_dict.get("tool_call_count", 0),
                system_state=metadata_dict.get("system_state", {})
            )
            
            # Restore messages
            self.messages = []
            for msg_dict in data.get("messages", []):
                message = Message(
                    role=MessageRole(msg_dict.get("role", "user")),
                    content=msg_dict.get("content", ""),
                    timestamp=datetime.fromisoformat(msg_dict.get("timestamp", datetime.utcnow().isoformat())),
                    message_id=msg_dict.get("message_id", str(uuid4())),
                    metadata=msg_dict.get("metadata", {})
                )
                self.messages.append(message)
            
            # Restore tool interactions
            self.tool_interactions = []
            for interaction_dict in data.get("tool_interactions", []):
                interaction = ToolInteraction(
                    tool_name=interaction_dict.get("tool_name", ""),
                    tool_input=interaction_dict.get("tool_input", {}),
                    tool_output=interaction_dict.get("tool_output"),
                    timestamp=datetime.fromisoformat(interaction_dict.get("timestamp", datetime.utcnow().isoformat())),
                    interaction_id=interaction_dict.get("interaction_id", str(uuid4())),
                    execution_time_ms=interaction_dict.get("execution_time_ms"),
                    error=interaction_dict.get("error"),
                    # Context management fields
                    collapsed=interaction_dict.get("collapsed", False),
                    ttl_counter=interaction_dict.get("ttl_counter", -1),
                    output_size=interaction_dict.get("output_size", 0),
                    expand_count=interaction_dict.get("expand_count", 0),
                    pinned=interaction_dict.get("pinned", False)
                )
                self.tool_interactions.append(interaction)
            
            return True
        except Exception as e:
            print(f"Error loading L1 session from file: {e}")
            return False
    
    def _update_last_activity(self) -> None:
        """Update the last activity timestamp."""
        self.session_metadata.last_activity = datetime.utcnow()
    
    def clear_session(self) -> None:
        """
        Clear the current session (typically called after archival).
        
        This resets L1 for a new session and saves to disk.
        """
        self.session_metadata = SessionMetadata()
        self.messages.clear()
        self.tool_interactions.clear()
        
        # Auto-save to disk after clearing
        self.save_to_file()
    
    def undo_from_index(self, message_index: int) -> dict[str, Any]:
        """
        Remove messages from the given index onwards (undo functionality).
        Also removes tool interactions that occurred after the message timestamp.
        
        Args:
            message_index: Index of the message to undo from (inclusive)
            
        Returns:
            Dictionary with status and removed count
        """
        if message_index < 0 or message_index >= len(self.messages):
            return {"status": "error", "message": "Invalid index", "removed_count": 0}
        
        # Get the timestamp of the message being undone
        target_message = self.messages[message_index]
        target_timestamp = target_message.timestamp
        
        # Count messages to remove
        messages_to_remove = len(self.messages) - message_index
        
        # Remove messages from index onwards
        self.messages = self.messages[:message_index]
        
        # Remove tool interactions that occurred at or after the target timestamp
        original_tool_count = len(self.tool_interactions)
        self.tool_interactions = [
            ti for ti in self.tool_interactions 
            if ti.timestamp < target_timestamp
        ]
        tools_removed = original_tool_count - len(self.tool_interactions)
        
        # Update metadata counts
        self.session_metadata.message_count = len(self.messages)
        self.session_metadata.tool_call_count = len(self.tool_interactions)
        self._update_last_activity()
        
        # Save to disk
        self.save_to_file()
        
        return {
            "status": "ok",
            "removed_count": messages_to_remove,
            "tools_removed": tools_removed
        }
    
    # ==================== Context Management (TTL System) ====================
    
    # Token thresholds for adaptive TTL
    TOKEN_THRESHOLD_ACTIVE = 15000  # Activate TTL system above this
    TOKEN_THRESHOLD_AGGRESSIVE = 25000  # Aggressive collapse above this
    TTL_SHORT = 2  # TTL for long outputs (>=1000 chars)
    TTL_LONG = 10  # TTL for short outputs (<1000 chars)
    TTL_IMMEDIATE = 1 # TTL for huge outputs (>=100k chars)
    OUTPUT_SIZE_THRESHOLD = 1000  # Chars threshold for short vs long
    OUTPUT_SIZE_HUGE = 100000 # Chars threshold for immediate collapse
    PREVIEW_SIZE = 400  # Characters to show in preview
    
    def estimate_token_count(self) -> int:
        """
        Estimate total token count in context.
        Rough estimate: 1 token ≈ 4 characters.
        
        Returns:
            Estimated token count
        """
        total_chars = 0
        
        # Messages
        for msg in self.messages:
            total_chars += len(msg.content)
        
        # Tool outputs (only non-collapsed)
        for ti in self.tool_interactions:
            if not ti.collapsed:
                output_str = json.dumps(ti.tool_output) if not isinstance(ti.tool_output, str) else ti.tool_output
                total_chars += len(output_str)
                total_chars += len(json.dumps(ti.tool_input))
        
        return total_chars // 4
    
    def should_activate_ttl(self) -> bool:
        """Check if TTL system should be active based on context size."""
        return self.estimate_token_count() >= self.TOKEN_THRESHOLD_ACTIVE
    
    def is_aggressive_mode(self) -> bool:
        """Check if we're in aggressive collapse mode."""
        return self.estimate_token_count() >= self.TOKEN_THRESHOLD_AGGRESSIVE
    
    def tick_ttl(self) -> list[str]:
        """
        Decrement TTL counters and auto-collapse expired outputs.
        Called after each user message.
        
        Returns:
            List of interaction IDs that were auto-collapsed
        """
        if not self.should_activate_ttl():
            return []
        
        collapsed_ids = []
        aggressive = self.is_aggressive_mode()
        
        if aggressive:
            logger.info(f"TTL: Aggressive mode ACTIVE (Tokens: {self.estimate_token_count()})")
        
        for ti in self.tool_interactions:
            # Skip pinned outputs
            if ti.pinned:
                continue
            
            # Initialize TTL if not set (-1 means uninitialized)
            # This applies to both new outputs and loaded outputs that haven't been initialized
            if ti.ttl_counter == -1:
                # Calculate output size if not set
                if ti.output_size == 0:
                    output_str = json.dumps(ti.tool_output) if not isinstance(ti.tool_output, str) else ti.tool_output
                    ti.output_size = len(output_str)
                
                # Set initial TTL based on output size
                if ti.output_size >= self.OUTPUT_SIZE_HUGE:
                    ti.ttl_counter = self.TTL_IMMEDIATE
                elif ti.output_size >= self.OUTPUT_SIZE_THRESHOLD:
                    ti.ttl_counter = self.TTL_SHORT
                else:
                    ti.ttl_counter = self.TTL_LONG
                
                # In aggressive mode, reduce TTL
                if aggressive:
                    ti.ttl_counter = max(1, ti.ttl_counter // 2)
                    
                logger.debug(f"TTL Init: {ti.tool_name} (ID: {ti.interaction_id[:8]}) -> {ti.ttl_counter} turns (Size: {ti.output_size})")
                continue  # Don't decrement on first tick
            
            # Skip already at minimum TTL (-2)
            if ti.ttl_counter <= -2:
                continue
            
            # Decrement TTL (goes negative: 0 -> -1 -> -2)
            ti.ttl_counter -= 1
            logger.debug(f"TTL Tick: {ti.tool_name} (ID: {ti.interaction_id[:8]}) -> {ti.ttl_counter}")
            
            # Collapse when TTL hits 0
            if ti.ttl_counter == 0 and not ti.collapsed:
                ti.collapsed = True
                collapsed_ids.append(ti.interaction_id)
                logger.info(f"TTL Collapse: {ti.tool_name} (ID: {ti.interaction_id[:8]}) - Output size: {ti.output_size} chars")
        
        if collapsed_ids:
            self.save_to_file()
        
        return collapsed_ids
    
    def collapse_output(self, interaction_id: str) -> bool:
        """
        Collapse a specific tool output.
        
        Args:
            interaction_id: ID of the tool interaction
            
        Returns:
            True if successful
        """
        for ti in self.tool_interactions:
            if ti.interaction_id == interaction_id:
                ti.collapsed = True
                ti.ttl_counter = 0
                self.save_to_file()
                return True
        return False
    
    def expand_output(self, interaction_id: str) -> bool:
        """
        Expand a collapsed tool output with TTL doubling logic.
        
        TTL doubles each time: 2 -> 4 -> 8 -> pinned (never collapse)
        This rewards frequently accessed outputs.
        
        Args:
            interaction_id: ID of the tool interaction
            
        Returns:
            True if successful
        """
        for ti in self.tool_interactions:
            if ti.interaction_id == interaction_id:
                ti.collapsed = False
                ti.expand_count += 1
                
                # After 3 expands (2->4->8), pin it permanently
                if ti.expand_count >= 3:
                    ti.pinned = True
                    ti.ttl_counter = -1  # No TTL for pinned
                else:
                    # Double TTL each expand: base * (2 ^ expand_count)
                    base_ttl = self.TTL_SHORT if ti.output_size >= self.OUTPUT_SIZE_THRESHOLD else self.TTL_LONG
                    ti.ttl_counter = base_ttl * (2 ** ti.expand_count)
                
                self.save_to_file()
                return True
        return False
    
    def collapse_all_outputs(self) -> int:
        """
        Collapse all tool outputs.
        
        Returns:
            Number of outputs collapsed
        """
        count = 0
        for ti in self.tool_interactions:
            if not ti.collapsed:
                ti.collapsed = True
                ti.ttl_counter = 0
                count += 1
        
        if count > 0:
            self.save_to_file()
        return count
    
    def get_output_status(self) -> list[dict[str, Any]]:
        """
        Get status of all tool outputs.
        
        Returns:
            List of dicts with output status info
        """
        result = []
        for ti in self.tool_interactions:
            result.append({
                "interaction_id": ti.interaction_id,
                "tool_name": ti.tool_name,
                "collapsed": ti.collapsed,
                "ttl_counter": ti.ttl_counter,
                "output_size": ti.output_size,
                "timestamp": ti.timestamp.isoformat()
            })
        return result
    
    def get_collapsed_preview(self, interaction: ToolInteraction) -> str:
        """
        Generate a preview string for a collapsed tool output.
        
        Args:
            interaction: The tool interaction
            
        Returns:
            Formatted preview string with metadata
        """
        # Format input summary
        input_str = json.dumps(interaction.tool_input, ensure_ascii=False)
        if len(input_str) > 100:
            input_str = input_str[:100] + "..."
        
        # Generate output preview
        output_str = interaction.tool_output
        if not isinstance(output_str, str):
            try:
                output_str = json.dumps(output_str, ensure_ascii=False, indent=None)
            except:
                output_str = str(output_str)
        
        preview = output_str[:self.PREVIEW_SIZE]
        if len(output_str) > self.PREVIEW_SIZE:
            preview += "..."
        
        return f"""[COLLAPSED TOOL OUTPUT]
Tool: {interaction.tool_name}
Input: {input_str}
Preview: {preview}
Full Size: {interaction.output_size} chars | ID: {interaction.interaction_id}
-> Use manage_tool_outputs(action="expand", ids=["{interaction.interaction_id}"]) to view full output"""
    
    def get_tool_outputs_for_context(self) -> list[dict[str, Any]]:
        """
        Get tool outputs formatted for model context.
        Collapsed outputs return preview, expanded return full.
        
        Returns:
            List of tool output dicts ready for model
        """
        result = []
        for ti in self.tool_interactions:
            if ti.collapsed:
                result.append({
                    "interaction_id": ti.interaction_id,
                    "tool_name": ti.tool_name,
                    "tool_input": ti.tool_input,
                    "tool_output": self.get_collapsed_preview(ti),
                    "collapsed": True
                })
            else:
                result.append({
                    "interaction_id": ti.interaction_id,
                    "tool_name": ti.tool_name,
                    "tool_input": ti.tool_input,
                    "tool_output": ti.tool_output,
                    "collapsed": False
                })
        return result
    
    def get_tool_context_for_model(self) -> str:
        """
        Generate a formatted string of tool outputs for model context.
        
        Expanded outputs show full content, collapsed show preview.
        This allows model to see past tool results and expand if needed.
        
        Returns:
            Formatted string for system prompt or context injection
        """
        if not self.tool_interactions:
            return ""
        
        lines = ["=== TOOL OUTPUT HISTORY ==="]
        lines.append(f"(Total: {len(self.tool_interactions)} tool calls, use manage_tool_outputs to expand/collapse)")
        lines.append("")
        
        for ti in self.tool_interactions:
            # Determine status based on TTL level
            if ti.pinned:
                status = "PINNED"
            elif ti.ttl_counter <= -2:
                status = "ARCHIVED"  # Metadata only
            elif ti.collapsed:
                status = "COLLAPSED"
            else:
                status = "EXPANDED"
            
            ttl_info = f"TTL={ti.ttl_counter}" if not ti.pinned else ""
            
            lines.append(f"[{status}] {ti.tool_name} | {ti.output_size} chars {ttl_info}")
            
            # TTL <= -2: ARCHIVED - metadata only, no content
            if ti.ttl_counter <= -2 and not ti.pinned:
                lines.append(f"  -> expand with: manage_tool_outputs(action='expand', ids=['{ti.interaction_id}'])")
            # TTL = -1: minimal preview (100 chars)
            elif ti.ttl_counter == -1 and ti.collapsed:
                lines.append(f"  Input: {json.dumps(ti.tool_input, ensure_ascii=False)[:50]}...")
                preview = self._get_output_preview(ti.tool_output, 100)
                lines.append(f"  Preview: {preview}")
                lines.append(f"  -> expand with: manage_tool_outputs(action='expand', ids=['{ti.interaction_id}'])")
            # TTL = 0: collapsed with 200 char preview
            elif ti.collapsed:
                lines.append(f"  Input: {json.dumps(ti.tool_input, ensure_ascii=False)[:100]}...")
                preview = self._get_output_preview(ti.tool_output, 200)
                lines.append(f"  Preview: {preview}")
                lines.append(f"  -> expand with: manage_tool_outputs(action='expand', ids=['{ti.interaction_id}'])")
            else:
                # Expanded - show full output (max 2000 chars)
                lines.append(f"  Input: {json.dumps(ti.tool_input, ensure_ascii=False)[:100]}...")
                output_str = ti.tool_output
                if not isinstance(output_str, str):
                    try:
                        output_str = json.dumps(output_str, ensure_ascii=False)
                    except:
                        output_str = str(output_str)
                
                if len(output_str) > 2000:
                    lines.append(f"  Output: {output_str[:2000]}...")
                    lines.append(f"  [truncated, {ti.output_size} total chars]")
                else:
                    lines.append(f"  Output: {output_str}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_output_preview(self, output: Any, max_len: int = 200) -> str:
        """Get a short preview of tool output."""
        output_str = output
        if not isinstance(output_str, str):
            try:
                output_str = json.dumps(output_str, ensure_ascii=False)
            except:
                output_str = str(output_str)
        
        if len(output_str) > max_len:
            return output_str[:max_len] + "..."
        return output_str
