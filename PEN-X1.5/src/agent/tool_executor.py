"""
Tool Executor for PEN Agent

This module is responsible for executing tools based on their names and inputs.
It decouples the tool execution logic from the main agent orchestration.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from ..agent_tools.data_tools import DataTools
from ..agent_tools.email_tools import EmailTools
from ..agent_tools.whatsapp_tools import WhatsAppTools
from ..agent_tools.drive_tools import DriveTools
from ..agent_tools.web_tools import WebTools
from ..agent_tools.refresh_tools import RefreshTools
from ..agent_tools.context_tools import ContextTools
from ..agent_tools.calendar_tools import CalendarTools
from ..agent_tools.file_system_tools import FileSystemTools
from ..agent_tools.penote_tools import PENoteTools
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Constants from the original agent file
DEFAULT_SEARCH_LIMIT = 50
DEFAULT_RECENT_DAYS = 7
DEFAULT_RECENT_LIMIT = 100
DEFAULT_DRIVE_LIMIT = 100
DEFAULT_DRIVE_SEARCH_LIMIT = 20
DRIVE_FOLDER_NAME = "Wpmesages"

class ToolExecutor:
    """Executes tools by name and input, handling all tool-related logic."""

    def __init__(
        self,
        data_tools: DataTools,
        email_tools: EmailTools,
        whatsapp_tools: WhatsAppTools,
        web_tools: WebTools,
        refresh_tools: RefreshTools,
        context_tools: ContextTools,
        calendar_tools: CalendarTools,
        file_system_tools: FileSystemTools,
        drive_tools: Optional[DriveTools] = None, # Drive tools are optional
        l1_layer = None,  # L1 layer for context management
        layer_manager = None, # Full Layer Manager for L2/L2.5 access
        penote_tools: Optional[PENoteTools] = None, # PENote-specific tools (only for PENote chat)
    ):
        self.data_tools = data_tools
        self.email_tools = email_tools
        self.whatsapp_tools = whatsapp_tools
        self.web_tools = web_tools
        self.refresh_tools = refresh_tools
        self.context_tools = context_tools
        self.calendar_tools = calendar_tools
        self.file_system_tools = file_system_tools
        self.drive_tools = drive_tools
        self.l1_layer = l1_layer
        self.layer_manager = layer_manager
        self.penote_tools = penote_tools

    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a tool by its name and return the result as a JSON string.

        Args:
            tool_name: The name of the tool to execute.
            tool_input: The parameters for the tool.

        Returns:
            A JSON string representing the result of the tool execution.
        """
        try:
            logger.info(f"Executing tool: {tool_name} with input: {tool_input}")

            # Time tool
            if tool_name == "get_current_time":
                now = datetime.now()
                return json.dumps({
                    "status": "success",
                    "current_time": now.isoformat(),
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M:%S"),
                    "day_of_week": now.strftime("%A"),
                    "formatted": now.strftime("%d %B %Y, %H:%M")
                }, ensure_ascii=False)
            
            # --- FILE SYSTEM TOOLS ---
            elif tool_name == "file_system_tools_open":
                return json.dumps({
                    "status": "success",
                    "message": "PEN WorkSpace File System Tools are now ACTIVE. You can use read_file, write_to_file, replace_in_file, search_files, get_file_info, list_files."
                }, ensure_ascii=False)

            elif tool_name == "read_file":
                path = tool_input.get("path")
                if not isinstance(path, str):
                    return json.dumps({"status": "error", "message": "path is required"})
                result = self.file_system_tools.read_file(path)
                return json.dumps({"status": "success", "content": result}, ensure_ascii=False)
            
            elif tool_name == "write_to_file":
                path = tool_input.get("path")
                content = tool_input.get("content")
                if not isinstance(path, str) or not isinstance(content, str):
                    return json.dumps({"status": "error", "message": "path and content required"})
                result = self.file_system_tools.write_to_file(path, content)
                return json.dumps({"status": "success", "message": result}, ensure_ascii=False)
            
            elif tool_name == "replace_in_file":
                path = tool_input.get("path")
                diff = tool_input.get("diff")
                if not isinstance(path, str) or not isinstance(diff, str):
                    return json.dumps({"status": "error", "message": "path and diff required"})
                result = self.file_system_tools.replace_in_file(path, diff)
                return json.dumps({"status": "success", "message": result}, ensure_ascii=False)
            
            elif tool_name == "search_files":
                pattern = tool_input.get("pattern")
                if not isinstance(pattern, str):
                    return json.dumps({"status": "error", "message": "pattern required"})
                result = self.file_system_tools.search_files(
                    pattern, 
                    tool_input.get("glob_pattern", "**/*")
                )
                return json.dumps({"status": "success", "matches": result}, ensure_ascii=False)
            
            elif tool_name == "get_file_info":
                path = tool_input.get("path")
                if not isinstance(path, str):
                    return json.dumps({"status": "error", "message": "path required"})
                result = self.file_system_tools.get_file_info(path)
                return json.dumps({"status": "success", "info": result}, ensure_ascii=False)
            
            elif tool_name == "list_files":
                path = tool_input.get("path", "")
                result = self.file_system_tools.list_files(path)
                return json.dumps({"status": "success", "files": result}, ensure_ascii=False)

            # Data tools
            elif tool_name == "list_whatsapp_chats":
                return self.data_tools.list_whatsapp_chats()

            elif tool_name == "get_whatsapp_messages":
                chat_name = tool_input.get("chat_name")
                if not isinstance(chat_name, str):
                    return json.dumps({"status": "error", "message": "chat_name is required and must be a string"})
                # Ensure limit is an integer
                limit = tool_input.get("limit", 100)
                try:
                    limit = int(limit) if limit is not None else 100
                except (ValueError, TypeError):
                    limit = 100
                return self.data_tools.get_whatsapp_messages(
                    chat_name=chat_name,
                    start_date=tool_input.get("start_date"),
                    end_date=tool_input.get("end_date"),
                    limit=limit
                )

            elif tool_name == "search_messages":
                query = tool_input.get("query")
                if not isinstance(query, str):
                    return json.dumps({"status": "error", "message": "query is required and must be a string"})
                return self.data_tools.search_messages(
                    query=query,
                    source=tool_input.get("source") or None,
                    start_date=tool_input.get("start_date"),
                    end_date=tool_input.get("end_date"),
                    limit=tool_input.get("limit", DEFAULT_SEARCH_LIMIT)
                )

            elif tool_name == "get_recent_messages":
                return self.data_tools.get_recent_messages(
                    days=tool_input.get("days", DEFAULT_RECENT_DAYS),
                    source=tool_input.get("source") or None,
                    limit=tool_input.get("limit", DEFAULT_RECENT_LIMIT)
                )

            elif tool_name == "get_statistics":
                return self.data_tools.get_statistics()

            # Email listing/search helpers
            elif tool_name == "list_email_subjects":
                return self.email_tools.list_email_subjects(
                    start_date=tool_input.get("start_date"),
                    end_date=tool_input.get("end_date"),
                    limit=tool_input.get("limit", 200),
                    sort_order=tool_input.get("sort_order", "desc"),
                )

            elif tool_name == "get_email_content":
                return self.email_tools.get_email_content(
                    email_id=tool_input.get("email_id"),
                    subject=tool_input.get("subject"),
                    timestamp=tool_input.get("timestamp"),
                )

            elif tool_name == "search_emails":
                return self.email_tools.search_emails(
                    sender=tool_input.get("sender"),
                    recipient=tool_input.get("recipient"),
                    subject=tool_input.get("subject"),
                    start_date=tool_input.get("start_date"),
                    end_date=tool_input.get("end_date"),
                    limit=tool_input.get("limit", 100),
                )

            # Drive tools
            elif tool_name == "search_drive_files":
                if not self.drive_tools:
                    return json.dumps({"status": "error", "message": "Drive tools are not available"})
                query = tool_input.get("query", "")
                # If query is empty, list all files (replaces list_drive_files)
                if query:
                    return self.drive_tools.search_files(
                        query=query,
                        limit=tool_input.get("limit", DEFAULT_DRIVE_LIMIT)
                    )
                else:
                    return self.drive_tools.list_files(
                        file_type=tool_input.get("file_type"),
                        limit=tool_input.get("limit", DEFAULT_DRIVE_LIMIT)
                    )

            # Web tools
            elif tool_name == "search_web":
                query = tool_input.get("query")
                if not isinstance(query, str):
                    return json.dumps({"status": "error", "message": "query is required and must be a string"})
                return self.web_tools.search_web(
                    query=query,
                    limit=tool_input.get("limit", 5)
                )

            elif tool_name == "fetch_webpage":
                url = tool_input.get("url")
                if not isinstance(url, str):
                    return json.dumps({"status": "error", "message": "url is required and must be a string"})
                return self.web_tools.fetch_webpage(
                    url=url,
                    max_length=tool_input.get("max_length", 5000)
                )

            # Refresh tools
            elif tool_name == "refresh_emails":
                return self.refresh_tools.refresh_emails(
                    search_query=tool_input.get("search_query"),
                    limit=tool_input.get("limit", 50)
                )

            elif tool_name == "refresh_drive_files":
                return self.refresh_tools.refresh_drive_files(
                    folder_name=tool_input.get("folder_name", DRIVE_FOLDER_NAME)
                )

            elif tool_name == "check_for_updates":
                return self.refresh_tools.check_for_updates()

            # --- CALENDAR TOOLS ---
            elif tool_name == "calendar_tools_open":
                return self.calendar_tools.calendar_tools_open()

            elif tool_name == "read_calendar":
                return self.calendar_tools.read_calendar(
                    start_date=tool_input.get("start_date"),
                    end_date=tool_input.get("end_date"),
                    view_mode=tool_input.get("view_mode", "daily")
                )

            elif tool_name == "create_event":
                return self.calendar_tools.create_event(
                    title=tool_input.get("title"),
                    description=tool_input.get("description"),
                    start_time=tool_input.get("start_time"),
                    end_time=tool_input.get("end_time"),
                    window_start=tool_input.get("window_start"),
                    window_end=tool_input.get("window_end"),
                    duration_minutes=tool_input.get("duration_minutes", 60),
                    tags=tool_input.get("tags"),
                    linked_context_id=tool_input.get("linked_context_id")
                )

            elif tool_name == "chain_events":
                return self.calendar_tools.chain_events(
                    prev_event_id=tool_input.get("prev_event_id"),
                    next_event_id=tool_input.get("next_event_id")
                )

            elif tool_name == "delete_event":
                event_id = tool_input.get("event_id")
                if not isinstance(event_id, str):
                    return json.dumps({"status": "error", "message": "event_id is required and must be a string"})
                return self.calendar_tools.delete_event(event_id)

            # --- CONTEXT TOOLS (L4) ---
            elif tool_name == "context_tools_open":
                return self.context_tools.context_tools_open()

            elif tool_name == "read_context":
                context_id_or_title = tool_input.get("context_id_or_title")
                if not isinstance(context_id_or_title, str):
                    return json.dumps({"status": "error", "message": "context_id_or_title is required"})
                return self.context_tools.read_context(context_id_or_title)

            elif tool_name == "create_context":
                return self.context_tools.create_context(
                    title=tool_input.get("title"),
                    content=tool_input.get("content"),
                    type=tool_input.get("type", "knowledge"),
                    tags=tool_input.get("tags"),
                    description=tool_input.get("description")
                )

            elif tool_name == "update_context":
                context_id = tool_input.get("context_id")
                if not isinstance(context_id, str):
                    return json.dumps({"status": "error", "message": "context_id is required"})
                return self.context_tools.update_context(
                    context_id=context_id,
                    content_append=tool_input.get("content_append"),
                    description=tool_input.get("description"),
                    status=tool_input.get("status"),
                    tags=tool_input.get("tags")
                )

            elif tool_name == "delete_context":
                context_id = tool_input.get("context_id")
                if not isinstance(context_id, str):
                    return json.dumps({"status": "error", "message": "context_id is required"})
                return self.context_tools.delete_context(context_id)

            elif tool_name == "link_to_calendar":
                context_id = tool_input.get("context_id")
                event_id = tool_input.get("event_id")
                if not isinstance(context_id, str) or not isinstance(event_id, str):
                    return json.dumps({"status": "error", "message": "context_id and event_id required"})
                return self.context_tools.link_to_calendar(context_id, event_id)

            elif tool_name == "add_behavioral_directive":
                directive = tool_input.get("directive")
                if not isinstance(directive, str):
                    return json.dumps({"status": "error", "message": "directive is required"})
                return self.context_tools.add_behavioral_directive(directive)

            elif tool_name == "search_memory":
                if not self.layer_manager:
                    return json.dumps({"status": "error", "message": "Memory layer not available"})
                
                query = tool_input.get("query")
                # query is required by schema, but empty string is fine for pure date search
                if query is None: 
                    query = ""
                
                results = self.layer_manager.search_memory(
                    query=query,
                    start_date=tool_input.get("start_date"),
                    end_date=tool_input.get("end_date"),
                    max_results=tool_input.get("max_results", 5)
                )
                return json.dumps({"status": "success", "results": results}, ensure_ascii=False)

            elif tool_name == "read_archived_session":
                if not self.layer_manager:
                    return json.dumps({"status": "error", "message": "Memory layer not available"})
                
                session_id = tool_input.get("session_id")
                if not isinstance(session_id, str):
                    return json.dumps({"status": "error", "message": "session_id is required"})
                
                # Get full session details from L2
                session_data = self.layer_manager.get_detailed_session(session_id)
                if not session_data:
                    return json.dumps({"status": "error", "message": "Session not found"}, ensure_ascii=False)
                
                # Extract ONLY messages (User/Model) and filter out Tool interactions
                messages = session_data.get("messages", [])
                chat_history = []
                
                for msg in messages:
                    role = msg.get("role")
                    content = msg.get("content", "")
                    # Skip tool outputs or system events if not relevant text
                    if role in ["user", "assistant", "model"]:
                        chat_history.append(f"[{role.upper()}]: {content}")
                
                return json.dumps({
                    "status": "success", 
                    "session_date": session_data.get("created_at"),
                    "chat_transcript": "\n\n".join(chat_history)
                }, ensure_ascii=False)

            # WhatsApp-specific tools
            elif tool_name == "get_whatsapp_participants":
                chat_name = tool_input.get("chat_name")
                if not isinstance(chat_name, str):
                    return json.dumps({"status": "error", "message": "chat_name is required and must be a string"})
                return self.whatsapp_tools.get_chat_participants(
                    chat_name=chat_name
                )

            elif tool_name == "get_whatsapp_chronology":
                chat_name = tool_input.get("chat_name")
                if not isinstance(chat_name, str):
                    return json.dumps({"status": "error", "message": "chat_name is required and must be a string"})
                return self.whatsapp_tools.get_chat_chronology(
                    chat_name=chat_name,
                    start_date=tool_input.get("start_date"),
                    end_date=tool_input.get("end_date"),
                    group_by=tool_input.get("group_by", "day")
                )

            elif tool_name == "get_whatsapp_media_references":
                chat_name = tool_input.get("chat_name")
                if not isinstance(chat_name, str):
                    return json.dumps({"status": "error", "message": "chat_name is required and must be a string"})
                return self.whatsapp_tools.get_media_references(
                    chat_name=chat_name,
                    media_type=tool_input.get("media_type")
                )
            
            elif tool_name == "search_across_chats":
                keyword = tool_input.get("keyword")
                if not isinstance(keyword, str):
                    return json.dumps({"status": "error", "message": "keyword is required and must be a string"})
                return self.whatsapp_tools.search_across_chats(
                    keyword=keyword,
                    start_date=tool_input.get("start_date"),
                    end_date=tool_input.get("end_date"),
                    limit=tool_input.get("limit", DEFAULT_SEARCH_LIMIT)
                )
            
            elif tool_name == "get_conversation_context":
                chat_name = tool_input.get("chat_name")
                target_timestamp = tool_input.get("target_timestamp")
                if not isinstance(chat_name, str):
                    return json.dumps({"status": "error", "message": "chat_name is required and must be a string"})
                if not isinstance(target_timestamp, str):
                    return json.dumps({"status": "error", "message": "target_timestamp is required and must be a string"})
                # Ensure context_size is an integer
                context_size = tool_input.get("context_size", 10)
                try:
                    context_size = int(context_size) if context_size is not None else 10
                except (ValueError, TypeError):
                    context_size = 10
                return self.whatsapp_tools.get_conversation_context(
                    chat_name=chat_name,
                    target_timestamp=target_timestamp,
                    context_size=context_size
                )

            # Invoice Processing Tools
            elif tool_name == "parse_email_html":
                email_html = tool_input.get("email_html")
                if not isinstance(email_html, str):
                    return json.dumps({"status": "error", "message": "email_html is required and must be a string"})
                from ..agent_tools.invoice_tools import parse_email_html
                result = parse_email_html(email_html)
                return json.dumps(result, ensure_ascii=False)
            
            elif tool_name == "scrape_invoice_url":
                url = tool_input.get("url")
                if not isinstance(url, str):
                    return json.dumps({"status": "error", "message": "url is required and must be a string"})
                require_trust = tool_input.get("require_trust", True)
                from ..agent_tools.invoice_tools import scrape_invoice_url
                result = scrape_invoice_url(url, require_trust)
                return json.dumps(result, ensure_ascii=False)
            
            elif tool_name == "extract_text_from_image":
                image_path = tool_input.get("image_path")
                if not isinstance(image_path, str):
                    return json.dumps({"status": "error", "message": "image_path is required and must be a string"})
                lang = tool_input.get("lang", "eng+tur")
                from ..agent_tools.invoice_tools import extract_text_from_image
                result = extract_text_from_image(image_path, lang)
                return json.dumps(result, ensure_ascii=False)
            
            elif tool_name == "add_trusted_domain":
                domain = tool_input.get("domain")
                if not isinstance(domain, str):
                    return json.dumps({"status": "error", "message": "domain is required and must be a string"})
                from ..agent_tools.invoice_tools import add_trusted_domain
                result = add_trusted_domain(domain)
                return json.dumps(result, ensure_ascii=False)
            
            elif tool_name == "get_trusted_domains":
                from ..agent_tools.invoice_tools import get_trusted_domains
                result = get_trusted_domains()
                return json.dumps(result, ensure_ascii=False)
            
            # Media tools
            elif tool_name == "analyze_whatsapp_media":
                from ..agent_tools.media_tools import MediaTools
                media_tools = MediaTools()
                media_id = tool_input.get("media_id", "")
                force_reprocess = tool_input.get("force_reprocess", False)
                result = media_tools.analyze_media(media_id, force_reprocess)
                return json.dumps(result, ensure_ascii=False)
            
            elif tool_name == "list_chat_media":
                from ..agent_tools.media_tools import MediaTools
                media_tools = MediaTools()
                chat_name = tool_input.get("chat_name", "")
                result = media_tools.list_chat_media(chat_name)
                return json.dumps(result, ensure_ascii=False)
            
            # Context Management Tools
            elif tool_name == "manage_tool_outputs":
                return self._manage_tool_outputs(tool_input)
            
            # --- PENOTE TOOLS (Only available in PENote chat context) ---
            elif tool_name == "penote_get_editor_state":
                if not self.penote_tools:
                    return json.dumps({"status": "error", "message": "PENote tools not available in this context"})
                return self.penote_tools.penote_get_editor_state()
            
            elif tool_name == "penote_get_active_file":
                if not self.penote_tools:
                    return json.dumps({"status": "error", "message": "PENote tools not available in this context"})
                return self.penote_tools.penote_get_active_file()
            
            elif tool_name == "penote_open_file":
                if not self.penote_tools:
                    return json.dumps({"status": "error", "message": "PENote tools not available in this context"})
                path = tool_input.get("path")
                if not isinstance(path, str):
                    return json.dumps({"status": "error", "message": "path is required"})
                return self.penote_tools.penote_open_file(path)

            else:
                logger.warning(f"Unknown tool called: {tool_name}")
                return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
            return json.dumps({"status": "error", "message": f"An unexpected error occurred in {tool_name}: {e}"})
    
    def _manage_tool_outputs(self, tool_input: Dict[str, Any]) -> str:
        """
        Manage tool outputs - expand, collapse, or list status.
        
        Args:
            tool_input: Dict with 'action' and optionally 'ids'
            
        Returns:
            JSON result string
        """
        if not self.l1_layer:
            return json.dumps({
                "status": "error",
                "message": "L1 layer not available for context management"
            })
        
        action = tool_input.get("action", "").lower()
        ids = tool_input.get("ids", [])
        
        if action == "list":
            # Get status of all tool outputs
            status = self.l1_layer.get_output_status()
            token_estimate = self.l1_layer.estimate_token_count()
            ttl_active = self.l1_layer.should_activate_ttl()
            
            return json.dumps({
                "status": "success",
                "action": "list",
                "token_estimate": token_estimate,
                "ttl_system_active": ttl_active,
                "aggressive_mode": self.l1_layer.is_aggressive_mode(),
                "outputs": status,
                "summary": {
                    "total": len(status),
                    "collapsed": sum(1 for s in status if s["collapsed"]),
                    "expanded": sum(1 for s in status if not s["collapsed"])
                }
            }, ensure_ascii=False)
        
        elif action == "expand":
            if not ids:
                return json.dumps({
                    "status": "error",
                    "message": "ids required for expand action"
                })
            
            expanded = []
            failed = []
            for interaction_id in ids:
                if self.l1_layer.expand_output(interaction_id):
                    expanded.append(interaction_id)
                else:
                    failed.append(interaction_id)
            
            return json.dumps({
                "status": "success",
                "action": "expand",
                "expanded": expanded,
                "failed": failed,
                "message": f"Expanded {len(expanded)} outputs"
            }, ensure_ascii=False)
        
        elif action == "collapse":
            if not ids:
                return json.dumps({
                    "status": "error",
                    "message": "ids required for collapse action"
                })
            
            collapsed = []
            failed = []
            for interaction_id in ids:
                if self.l1_layer.collapse_output(interaction_id):
                    collapsed.append(interaction_id)
                else:
                    failed.append(interaction_id)
            
            return json.dumps({
                "status": "success",
                "action": "collapse",
                "collapsed": collapsed,
                "failed": failed,
                "message": f"Collapsed {len(collapsed)} outputs"
            }, ensure_ascii=False)
        
        elif action == "collapse_all":
            count = self.l1_layer.collapse_all_outputs()
            return json.dumps({
                "status": "success",
                "action": "collapse_all",
                "collapsed_count": count,
                "message": f"Collapsed {count} outputs"
            }, ensure_ascii=False)
        
        else:
            return json.dumps({
                "status": "error",
                "message": f"Invalid action: {action}. Valid: expand, collapse, collapse_all, list"
            })