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
    
    # === CALENDAR TOOLS (NEW) ===
    {
        "name": "calendar_tools_open",
        "description": "Opens the Calendar System context. Call this when user asks about schedule, plans, dates, or time.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "read_calendar",
        "description": "Reads calendar events. Use view_mode='weekly' for overview, 'daily' for specific availability.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                "view_mode": {"type": "string", "description": "daily, weekly, monthly", "enum": ["daily", "weekly", "monthly"]}
            },
            "required": ["start_date"]
        }
    },
    {
        "name": "create_event",
        "description": "Creates a new calendar event. System automatically determines type (Fixed/Flexible).",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title"},
                "description": {"type": "string", "description": "Details"},
                "start_time": {"type": "string", "description": "For Fixed events: YYYY-MM-DDTHH:MM:SS"},
                "end_time": {"type": "string", "description": "For Fixed events"},
                "window_start": {"type": "string", "description": "For Flexible events: Earliest start"},
                "window_end": {"type": "string", "description": "For Flexible events: Latest end"},
                "duration_minutes": {"type": "integer", "description": "For Flexible events"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                "linked_context_id": {"type": "string", "description": "Optional L4 context ID"},
                "linked_file": {"type": "string", "description": "Optional: Path to a file in user_docs (e.g. daily_plans/...)"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "chain_events",
        "description": "Links two events sequentially (Event A must happen before Event B).",
        "input_schema": {
            "type": "object",
            "properties": {
                "prev_event_id": {"type": "string", "description": "ID of the first event"},
                "next_event_id": {"type": "string", "description": "ID of the second event"}
            },
            "required": ["prev_event_id", "next_event_id"]
        }
    },
    {
        "name": "delete_event",
        "description": "Deletes a calendar event by its ID. Use this to remove unwanted or mistakenly created events.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The unique ID of the event to delete (e.g., evt_abc12345)"}
            },
            "required": ["event_id"]
        }
    },

    # === FILE SYSTEM TOOLS (GATEKEEPER) ===
    {
        "name": "file_system_tools_open",
        "description": "Opens the PEN WorkSpace File System tools. Call this when the user wants to read, write, search, or manage files in the secure workspace.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },

    # === CONTEXT/MEMORY TOOLS (UPDATED L4) ===
    {
        "name": "context_tools_open",
        "description": "Opens the L4 Context System. Call this when user asks about Projects, Knowledge, or Memories.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "add_behavioral_directive",
        "description": "Adds a PERMANENT rule about how you should behave/act. Use this when user says 'from now on...', 'don't do X', 'always do Y'. This persists across sessions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directive": {"type": "string", "description": "The specific rule or instruction to remember permanently"}
            },
            "required": ["directive"]
        }
    },
    {
        "name": "search_memory",
        "description": "Searches past conversations (Archived Sessions). Use 'query' for keywords. Use 'start_date'/'end_date' (YYYY-MM-DD) to find sessions by date (e.g. yesterday).",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword or question"},
                "start_date": {"type": "string", "description": "Optional: Start date (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "Optional: End date (YYYY-MM-DD)"},
                "max_results": {"type": "integer", "description": "Max number of sessions to retrieve (default: 5)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "read_archived_session",
        "description": "Retrieves the FULL chat history (messages only) of a specific past session using its ID. Use this AFTER search_memory to see exactly what was said.",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The ID of the session to read (e.g. sess_2023...)"}
            },
            "required": ["session_id"]
        }
    },
    {
        "name": "read_context",
        "description": "Retrieves the FULL content of a specific context/knowledge item.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context_id_or_title": {"type": "string", "description": "ID or Exact Title of the context"}
            },
            "required": ["context_id_or_title"]
        }
    },
    {
        "name": "create_context",
        "description": "Creates a new Knowledge/Plan/Memory context. DO NOT use for calendar events.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Unique title"},
                "content": {"type": "string", "description": "Markdown content/notes"},
                "type": {"type": "string", "description": "knowledge, plan, memory", "enum": ["knowledge", "plan", "memory"]},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                "description": {"type": "string", "description": "Short summary"}
            },
            "required": ["title", "content"]
        }
    },
    {
        "name": "update_context",
        "description": "Updates an existing context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context_id": {"type": "string", "description": "Context ID"},
                "content_append": {"type": "string", "description": "Text to append to content"},
                "description": {"type": "string", "description": "New summary"},
                "status": {"type": "string", "description": "active, archived"},
                "tags": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["context_id"]
        }
    },
    {
        "name": "delete_context",
        "description": "Permanently deletes a context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context_id": {"type": "string", "description": "Context ID"}
            },
            "required": ["context_id"]
        }
    },
    {
        "name": "link_to_calendar",
        "description": "Links a context to a calendar event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context_id": {"type": "string", "description": "Context ID"},
                "event_id": {"type": "string", "description": "Calendar Event ID"}
            },
            "required": ["context_id", "event_id"]
        }
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
                "source": {"type": "string", "description": "whatsapp, email, or both (leave empty for both)"},
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
                "source": {"type": "string", "description": "whatsapp, email, or both (leave empty for both)"},
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
    },
    
    # === MEDIA TOOLS ===
    {
        "name": "analyze_whatsapp_media",
        "description": "WhatsApp sohbetlerindeki medya dosyalarını (görsel, ses, PDF, PPTX, DOCX) analiz eder. "
                      "Görsel ve Ses dosyaları için Gemini Multimodal, dökümanlar için metin çıkarır. "
                      "Sesli mesajları dinlemek ve transkriptini almak için de bunu kullan. "
                      "ÖNEMLİ: Önce list_chat_media ile medya ID'lerini öğren, sonra bu tool'u kullan. "
                      "Kullanıcı 'slayt', 'görsel', 'ses kaydı', 'dosya', 'not' gibi kelimeler kullandığında bu tool'u düşün. "
                      "Media ID formatları: IMG-..., PTT-... (ses), PPTX-..., PDF-... gibi.",
        "input_schema": {
            "type": "object",
            "properties": {
                "media_id": {"type": "string", "description": "list_chat_media'dan alınan media ID"},
                "force_reprocess": {"type": "boolean", "description": "Önbellekteki sonucu yoksay ve yeniden işle (varsayılan: false)"}
            },
            "required": ["media_id"]
        }
    },
    {
        "name": "list_chat_media",
        "description": "Lists media files in a chat.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chat_name": {"type": "string", "description": "Chat name"}
            },
            "required": ["chat_name"]
        }
    },
    
    # === CONTEXT MANAGEMENT TOOLS ===
    {
        "name": "manage_tool_outputs",
        "description": "Manage tool outputs in context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "expand, collapse, collapse_all, list"},
                "ids": {"type": "array", "items": {"type": "string"}, "description": "IDs to expand/collapse"}
            },
            "required": ["action"]
        }
    }
]

# PENote-Specific Tools (only active in PENote chat context)
PENOTE_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "penote_get_editor_state",
        "description": "Get the current state of the PENote editor. Shows: currently open file, saved vs unsaved content, word count, last saved time. Automatically called on first message.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "penote_get_active_file",
        "description": "Get the path and basic info of the currently active file in PENote editor. Lighter version of penote_get_editor_state.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "penote_open_file",
        "description": "Open a file in the user's PENote editor. The file must exist in workspace (data/user_docs).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path to the file (e.g., 'projects/aliye/plan.md')"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "penote_edit_document",
        "description": "Edits the CURRENTLY OPEN document in PENote with visual animation. Use this to change text. The user will see the deletion and typing happen in real-time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "old_text": {"type": "string", "description": "The exact text to find and replace. Must match exactly."},
                "new_text": {"type": "string", "description": "The new text to insert."}
            },
            "required": ["old_text", "new_text"]
        }
    }
]

FILE_SYSTEM_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "read_file",
        "description": "Read and return the full contents of a text file. Accepts a relative path within user_docs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path to the file"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_to_file",
        "description": "Write content to a file. Creates/Overwrites. Use for creating new documents or full updates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path to the file"},
                "content": {"type": "string", "description": "Full content to write"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "replace_in_file",
        "description": "Modify a file using search/replace blocks. Format:\n<<<<<<< SEARCH\noriginal\n=======\nnew\n>>>>>>> REPLACE",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path to the file"},
                "diff": {"type": "string", "description": "Diff string with SEARCH/REPLACE blocks"}
            },
            "required": ["path", "diff"]
        }
    },
    {
        "name": "search_files",
        "description": "Search for a regex pattern in files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex or text pattern"},
                "glob_pattern": {"type": "string", "description": "Optional glob pattern (default **/*)"}
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "get_file_info",
        "description": "Get metadata (size, date) for a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path to file"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_files",
        "description": "List files in a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path to directory (default root)"}
            },
            "required": []
        }
    }
]