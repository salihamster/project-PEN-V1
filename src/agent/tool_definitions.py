"""
Tool Definitions for the PEN Agent

This module contains the static definition of all tools available to the agent.
Keeping this separate from the agent logic makes the agent code cleaner and
the tool definitions easier to manage.

ALL DESCRIPTIONS TRANSLATED TO ENGLISH
"""

from typing import List, Dict, Any

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "get_current_time",
        "description": "Returns the current date and time. Used for getting current time information.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "list_whatsapp_chats",
        "description": "Lists all WhatsApp chats. Provides information about which chats exist and message counts.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_whatsapp_messages",
        "description": "Retrieves messages from a specific WhatsApp chat. SMART USAGE: If searching for a specific topic, first use 'search_messages' to find the dates when the topic was discussed, then use that date range. For large chats, ALWAYS use a limit (50-100) or date range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chat_name": {
                    "type": "string",
                    "description": "Chat name (e.g., 'vitaminsizler_ile_WhatsApp_Sohbeti')"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD format). If searching for a specific topic, first find the date using search_messages!"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD format). Can be the same as start_date for single-day messages."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of messages. MUST use if no date range! Recommended: 50-100 messages"
                }
            },
            "required": ["chat_name"]
        }
    },
    {
        "name": "search_messages",
        "description": "Searches for keywords in messages. Can search in WhatsApp and Email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'homework', 'meeting', 'exam')"
                },
                "source": {
                    "type": "string",
                    "description": "Source filter: 'whatsapp', 'email', or empty (both)",
                    "enum": ["whatsapp", "email", ""]
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD format, optional)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD format, optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 50)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_recent_messages",
        "description": "Returns messages from the last N days. Used for viewing recent activity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to retrieve messages from (default: 7)"
                },
                "source": {
                    "type": "string",
                    "description": "Source filter: 'whatsapp', 'email', or empty (both)",
                    "enum": ["whatsapp", "email", ""]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of messages (default: 100)"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_statistics",
        "description": "Returns general statistics. Total chats, messages, email counts, etc.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "list_email_subjects",
        "description": "Lists email subjects within a date range, with minimal metadata (id, from, to, timestamp, subject).",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD or ISO)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD or ISO)"},
                "limit": {"type": "integer", "description": "Max number of results (default 200)"},
                "sort_order": {"type": "string", "description": "asc or desc (default desc)"}
            },
            "required": []
        }
    },
    {
        "name": "get_email_content",
        "description": "Returns full content of a specific email. Prefer email_id, or use subject+timestamp, or subject only (most recent).",
        "input_schema": {
            "type": "object",
            "properties": {
                "email_id": {"type": "string", "description": "Unique email id (preferred)"},
                "subject": {"type": "string", "description": "Subject text (used with timestamp or alone)"},
                "timestamp": {"type": "string", "description": "Exact timestamp to disambiguate subject"}
            },
            "required": []
        }
    },
    {
        "name": "search_emails",
        "description": "Search emails by sender, recipient, subject, and optional date range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sender": {"type": "string", "description": "Filter by sender (substring match)"},
                "recipient": {"type": "string", "description": "Filter by recipient (substring match)"},
                "subject": {"type": "string", "description": "Filter by subject (substring match)"},
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD or ISO)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD or ISO)"},
                "limit": {"type": "integer", "description": "Max results (default 100)"}
            },
            "required": []
        }
    },
    {
        "name": "search_drive_files",
        "description": "Searches or lists files in Google Drive. Searches in file names. If query is empty, lists all files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (searches in file name). Empty string = list all files"
                },
                "file_type": {
                    "type": "string",
                    "description": "File type filter (e.g., 'txt', 'zip', optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 100)"
                }
            },
            "required": []
        }
    },
    {
        "name": "search_web",
        "description": "Searches the web (Google, DuckDuckGo). Used for current information, news, research.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'Python async programming', 'today's news')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_webpage",
        "description": "Fetches a specific webpage and returns its content. Used for getting information from URLs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Webpage URL (e.g., 'https://example.com/article')"
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum content length (default: 5000)"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "refresh_emails",
        "description": "Refreshes emails (current data). Used for searching emails from a specific sender.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": "Email search query (e.g., 'FROM \"penelope@ac.com\"', 'SUBJECT \"meeting\"')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of emails (default: 50)"
                }
            },
            "required": []
        }
    },
    {
        "name": "refresh_drive_files",
        "description": "Fetches and processes new files from Google Drive. Used for updating WhatsApp exports.",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder_name": {
                    "type": "string",
                    "description": "Drive folder name (default: 'Wpmesages')"
                }
            },
            "required": []
        }
    },
    {
        "name": "check_for_updates",
        "description": "Checks for updates (Drive and Email). Used to find out if there is new data.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    # Context Management Tools
    {
        "name": "create_context",
        "description": "Creates a new context (event, project, meeting, task) and saves it to memory. Use when the user mentions an activity, meeting, project, or task. For remembering later.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context_type": {
                    "type": "string",
                    "description": "Context type: meeting, project, task, event, note"
                },
                "title": {
                    "type": "string",
                    "description": "Title (e.g., 'Project Meeting', 'Doctor Appointment')"
                },
                "date": {
                    "type": "string",
                    "description": "Date (YYYY-MM-DD format, optional)"
                },
                "time": {
                    "type": "string",
                    "description": "Time (HH:MM format, optional)"
                },
                "description": {
                    "type": "string",
                    "description": "Description (optional)"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags (e.g., ['work', 'important'], optional)"
                },
                "priority": {
                    "type": "string",
                    "description": "Priority: low, medium, high (default: medium)"
                },
                "location": {
                    "type": "string",
                    "description": "Location (optional)"
                },
                "notes": {
                    "type": "string",
                    "description": "Notes (optional)"
                }
            },
            "required": ["context_type", "title"]
        }
    },
        {
        "name": "update_context",
        "description": "Updates an existing context. Use to change activity details, add notes, update status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context_id": {
                    "type": "string",
                    "description": "Context ID"
                },
                "status": {
                    "type": "string",
                    "description": "New status (active, completed, cancelled, optional)"
                },
                "notes": {
                    "type": "string",
                    "description": "New notes (optional)"
                },
                "priority": {
                    "type": "string",
                    "description": "New priority (low, medium, high, optional)"
                }
            },
            "required": ["context_id"]
        }
    },
    {
        "name": "link_contexts",
        "description": "Links two contexts together. Use to connect related activities and projects.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context_id_1": {
                    "type": "string",
                    "description": "First context ID"
                },
                "context_id_2": {
                    "type": "string",
                    "description": "Second context ID"
                },
                "relation_type": {
                    "type": "string",
                    "description": "Relation type: related_to, follows, precedes, part_of (default: related_to)"
                }
            },
            "required": ["context_id_1", "context_id_2"]
        }
    },
    # WhatsApp-specific tools
    {
        "name": "get_whatsapp_participants",
        "description": "Lists all participants in a WhatsApp chat and their message counts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chat_name": {
                    "type": "string",
                    "description": "Chat name"
                }
            },
            "required": ["chat_name"]
        }
    }
]
