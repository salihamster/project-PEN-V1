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
        drive_tools: Optional[DriveTools] = None, # Drive tools are optional
    ):
        self.data_tools = data_tools
        self.email_tools = email_tools
        self.whatsapp_tools = whatsapp_tools
        self.web_tools = web_tools
        self.refresh_tools = refresh_tools
        self.context_tools = context_tools
        self.drive_tools = drive_tools

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

            # Context tools
            elif tool_name == "create_context":
                # Check for invalid parameters
                invalid_params = [k for k in tool_input.keys() if k not in [
                    "context_type", "title", "date", "time", "description", "tags",
                    "status", "priority", "location", "attendees", "notes",
                    "calendar_event_id", "task_id", "related_context_ids"
                ]]
                if invalid_params:
                    logger.warning(f"Invalid parameters for create_context: {invalid_params}")
                    return json.dumps({
                        "status": "error",
                        "message": f"Invalid parameters: {', '.join(invalid_params)}. Valid parameters are: context_type, title, date, time, description, tags, status, priority, location, attendees, notes, calendar_event_id, task_id, related_context_ids"
                    })
                
                context_type = tool_input.get("context_type")
                title = tool_input.get("title")
                if not isinstance(context_type, str) or not isinstance(title, str):
                    return json.dumps({"status": "error", "message": "context_type and title are required strings"})
                return self.context_tools.create_context(
                    context_type=context_type,
                    title=title,
                    date=tool_input.get("date"),
                    time=tool_input.get("time"),
                    description=tool_input.get("description"),
                    tags=tool_input.get("tags"),
                    status=tool_input.get("status", "active"),
                    priority=tool_input.get("priority", "medium"),
                    location=tool_input.get("location"),
                    attendees=tool_input.get("attendees"),
                    notes=tool_input.get("notes"),
                    calendar_event_id=tool_input.get("calendar_event_id"),
                    task_id=tool_input.get("task_id"),
                    related_context_ids=tool_input.get("related_context_ids")
                )

            elif tool_name == "update_context":
                context_id = tool_input.get("context_id")
                if not isinstance(context_id, str):
                    return json.dumps({"status": "error", "message": "context_id is required and must be a string"})
                return self.context_tools.update_context(
                    context_id=context_id,
                    title=tool_input.get("title"),
                    date=tool_input.get("date"),
                    time=tool_input.get("time"),
                    description=tool_input.get("description"),
                    tags=tool_input.get("tags"),
                    status=tool_input.get("status"),
                    priority=tool_input.get("priority"),
                    location=tool_input.get("location"),
                    attendees=tool_input.get("attendees"),
                    notes=tool_input.get("notes"),
                    calendar_event_id=tool_input.get("calendar_event_id"),
                    task_id=tool_input.get("task_id")
                )

            elif tool_name == "link_contexts":
                context_id_1 = tool_input.get("context_id_1")
                context_id_2 = tool_input.get("context_id_2")
                if not isinstance(context_id_1, str) or not isinstance(context_id_2, str):
                    return json.dumps({"status": "error", "message": "context_id_1 and context_id_2 are required strings"})
                return self.context_tools.link_contexts(
                    context_id_1=context_id_1,
                    context_id_2=context_id_2,
                    relation_type=tool_input.get("relation_type", "related_to")
                )

            elif tool_name == "search_contexts":
                query = tool_input.get("query")
                if not isinstance(query, str):
                    return json.dumps({"status": "error", "message": "query is required and must be a string"})
                return self.context_tools.search_contexts(
                    query=query,
                    context_type=tool_input.get("context_type"),
                    tags=tool_input.get("tags"),
                    status=tool_input.get("status"),
                    priority=tool_input.get("priority"),
                    date_start=tool_input.get("date_start"),
                    date_end=tool_input.get("date_end"),
                    limit=tool_input.get("limit", 10)
                )

            elif tool_name == "get_context_details":
                context_id = tool_input.get("context_id")
                if not isinstance(context_id, str):
                    return json.dumps({"status": "error", "message": "context_id is required and must be a string"})
                return self.context_tools.get_context_details(
                    context_id=context_id,
                    include_linked=tool_input.get("include_linked", True)
                )

            elif tool_name == "delete_context":
                context_id = tool_input.get("context_id")
                if not isinstance(context_id, str):
                    return json.dumps({"status": "error", "message": "context_id is required and must be a string"})
                return self.context_tools.delete_context(
                    context_id=context_id
                )

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

            else:
                logger.warning(f"Unknown tool called: {tool_name}")
                return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
            return json.dumps({"status": "error", "message": f"An unexpected error occurred in {tool_name}: {e}"})
