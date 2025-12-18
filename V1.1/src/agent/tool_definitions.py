"""
Tool Definitions for the PEN Agent

Optimized and concise tool definitions.
Faster model parsing with reduced confusion.
"""

from typing import List, Dict, Any

TOOLS: List[Dict[str, Any]] = [
    # === CORE TOOLS ===
    {
        "name": "get_current_time",
        "description": "Returns current date and time.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_statistics",
        "description": "Returns general statistics (chat count, message count, email count).",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    
    # === WHATSAPP TOOLS ===
    {
        "name": "list_whatsapp_chats",
        "description": "Lists all WhatsApp chats.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_whatsapp_messages",
        "description": "Gets messages from a specific chat. Use limit or date range for large chats.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chat_name": {"type": "string", "description": "Chat name"},
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                "limit": {"type": "integer", "description": "Max messages (recommended: 50-100)"}
            },
            "required": ["chat_name"]
        }
    },
    {
        "name": "get_whatsapp_participants",
        "description": "Lists participants and their message counts in a chat.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chat_name": {"type": "string", "description": "Chat name"}
            },
            "required": ["chat_name"]
        }
    },
    {
        "name": "search_across_chats",
        "description": "Searches for a keyword across ALL WhatsApp chats.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Search keyword"},
                "start_date": {"type": "string", "description": "Start date"},
                "end_date": {"type": "string", "description": "End date"},
                "limit": {"type": "integer", "description": "Max results (default: 50)"}
            },
            "required": ["keyword"]
        }
    },
    {
        "name": "get_conversation_context",
        "description": "Gets surrounding messages around a specific message.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chat_name": {"type": "string", "description": "Chat name"},
                "target_timestamp": {"type": "string", "description": "Target message timestamp (ISO)"},
                "context_size": {"type": "integer", "description": "Messages before/after (default: 10)"}
            },
            "required": ["chat_name", "target_timestamp"]
        }
    },
    
    # === SEARCH TOOLS ===
    {
        "name": "search_messages",
        "description": "Searches for keywords in WhatsApp and Email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword"},
                "source": {"type": "string", "description": "whatsapp, email, or empty (both)", "enum": ["whatsapp", "email", ""]},
                "start_date": {"type": "string", "description": "Start date"},
                "end_date": {"type": "string", "description": "End date"},
                "limit": {"type": "integer", "description": "Max results (default: 50)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_recent_messages",
        "description": "Gets messages from the last N days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Days back (default: 7)"},
                "source": {"type": "string", "description": "whatsapp, email, or empty", "enum": ["whatsapp", "email", ""]},
                "limit": {"type": "integer", "description": "Max messages (default: 100)"}
            },
            "required": []
        }
    },
    
    # === EMAIL TOOLS ===
    {
        "name": "list_email_subjects",
        "description": "Lists email subjects (id, from, date, subject).",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date"},
                "end_date": {"type": "string", "description": "End date"},
                "limit": {"type": "integer", "description": "Max results (default: 200)"},
                "sort_order": {"type": "string", "description": "asc or desc"}
            },
            "required": []
        }
    },
    {
        "name": "get_email_content",
        "description": "Gets full email content. email_id preferred.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email_id": {"type": "string", "description": "Email ID (preferred)"},
                "subject": {"type": "string", "description": "Subject text"},
                "timestamp": {"type": "string", "description": "Timestamp"}
            },
            "required": []
        }
    },
    {
        "name": "search_emails",
        "description": "Searches emails by sender, recipient, or subject.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sender": {"type": "string", "description": "Sender filter"},
                "recipient": {"type": "string", "description": "Recipient filter"},
                "subject": {"type": "string", "description": "Subject filter"},
                "start_date": {"type": "string", "description": "Start date"},
                "end_date": {"type": "string", "description": "End date"},
                "limit": {"type": "integer", "description": "Max results (default: 100)"}
            },
            "required": []
        }
    },
    {
        "name": "refresh_emails",
        "description": "Refreshes emails from IMAP.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_query": {"type": "string", "description": "IMAP query (e.g., FROM \"x@y.com\")"},
                "limit": {"type": "integer", "description": "Max emails (default: 50)"}
            },
            "required": []
        }
    },
    
    # === DRIVE TOOLS ===
    {
        "name": "search_drive_files",
        "description": "Searches files in Drive. Empty query = list all files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (in filename)"},
                "file_type": {"type": "string", "description": "File type (txt, zip, etc.)"},
                "limit": {"type": "integer", "description": "Max results (default: 100)"}
            },
            "required": []
        }
    },
    {
        "name": "refresh_drive_files",
        "description": "Fetches and processes new files from Drive.",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder_name": {"type": "string", "description": "Folder name (default: Wpmesages)"}
            },
            "required": []
        }
    },
    {
        "name": "check_for_updates",
        "description": "Checks for new data in Drive and Email.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    
    # === WEB TOOLS ===
    {
        "name": "search_web",
        "description": "Searches the web. For current info, news.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results (default: 5)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_webpage",
        "description": "Fetches URL content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Web page URL"},
                "max_length": {"type": "integer", "description": "Max content (default: 5000)"}
            },
            "required": ["url"]
        }
    },
    
    # === CONTEXT/MEMORY TOOLS ===
    {
        "name": "create_context",
        "description": "Creates a new context. Use IMMEDIATELY when user mentions future plans or important info.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context_type": {"type": "string", "description": "Type: meeting, project, task, event, note"},
                "title": {"type": "string", "description": "Title"},
                "date": {"type": "string", "description": "Date (YYYY-MM-DD)"},
                "time": {"type": "string", "description": "Time (HH:MM)"},
                "description": {"type": "string", "description": "Description"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                "priority": {"type": "string", "description": "low, medium, high"},
                "location": {"type": "string", "description": "Location"},
                "notes": {"type": "string", "description": "Notes"}
            },
            "required": ["context_type", "title"]
        }
    },
    {
        "name": "update_context",
        "description": "Updates an existing context. For status, notes, or priority changes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context_id": {"type": "string", "description": "Context ID"},
                "status": {"type": "string", "description": "active, completed, cancelled"},
                "notes": {"type": "string", "description": "New notes"},
                "priority": {"type": "string", "description": "low, medium, high"}
            },
            "required": ["context_id"]
        }
    },
    {
        "name": "search_contexts",
        "description": "Searches contexts. Empty query + filter = list by category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search text"},
                "context_type": {"type": "string", "description": "project, task, event, meeting, note"},
                "status": {"type": "string", "description": "planned, active, completed"},
                "priority": {"type": "string", "description": "low, medium, high"},
                "date_start": {"type": "string", "description": "Date range start"},
                "date_end": {"type": "string", "description": "Date range end"},
                "limit": {"type": "integer", "description": "Max results (default: 10)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_context_details",
        "description": "Gets full details of a context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context_id": {"type": "string", "description": "Context ID"},
                "include_linked": {"type": "boolean", "description": "Include linked contexts"}
            },
            "required": ["context_id"]
        }
    },
    {
        "name": "link_contexts",
        "description": "Links two contexts together.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context_id_1": {"type": "string", "description": "First context ID"},
                "context_id_2": {"type": "string", "description": "Second context ID"},
                "relation_type": {"type": "string", "description": "related_to, follows, part_of"}
            },
            "required": ["context_id_1", "context_id_2"]
        }
    },
    {
        "name": "delete_context",
        "description": "PERMANENTLY deletes a context. Cannot be undone! Only for wrong/unnecessary items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context_id": {"type": "string", "description": "Context ID to delete"}
            },
            "required": ["context_id"]
        }
    },
    
    # === INVOICE TOOLS ===
    {
        "name": "parse_email_html",
        "description": "Extracts invoice data from HTML email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email_html": {"type": "string", "description": "Email HTML content"}
            },
            "required": ["email_html"]
        }
    },
    {
        "name": "scrape_invoice_url",
        "description": "Extracts data from invoice URL (trusted domains only).",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Invoice URL"},
                "require_trust": {"type": "boolean", "description": "Require trusted domain"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "extract_text_from_image",
        "description": "Extracts text from image/PDF using OCR.",
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Image file path"},
                "lang": {"type": "string", "description": "OCR language (default: eng+tur)"}
            },
            "required": ["image_path"]
        }
    },
    {
        "name": "add_trusted_domain",
        "description": "Adds a trusted domain for scraping.",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain"}
            },
            "required": ["domain"]
        }
    },
    {
        "name": "get_trusted_domains",
        "description": "Returns the list of trusted domains.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    }
]
