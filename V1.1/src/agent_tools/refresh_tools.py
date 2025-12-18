"""
Data refresh tools for Agent
"""

import json
from typing import Optional, Dict
from datetime import datetime
from pathlib import Path

from ..parsers.email_parser import EmailParser
from ..parsers.drive_sync import auto_sync_from_drive
from ..storage.data_manager import DataManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RefreshTools:
    """Data refresh tools for Agent"""
    
    def __init__(self, data_manager: DataManager, email_config: Dict, 
                 service_account_file: Optional[str] = None):
        """
        Initialize RefreshTools
        
        Args:
            data_manager: DataManager instance
            email_config: Email configuration
            service_account_file: Service account JSON file (for Drive)
        """
        self.data_manager = data_manager
        self.email_config = email_config
        self.service_account_file = service_account_file
    
    def refresh_emails(self, search_query: Optional[str] = None, 
                      limit: int = 50) -> str:
        """
        Refresh emails (fetch fresh data) and add only new ones to local database.
        
        Args:
            search_query: Email search query (e.g., "from:penelope@ac.com")
            limit: Maximum email count
        
        Returns:
            JSON result: short list of newly added emails with metadata
        """
        try:
            logger.info(f"Agent: Refreshing emails (query: {search_query})")
            
            # Create email parser
            parser = EmailParser(
                email_address=self.email_config['address'],
                password=self.email_config['password'],
                imap_server=self.email_config['imap_server'],
                imap_port=self.email_config['imap_port'],
                max_workers=self.email_config.get('max_workers', 5)
            )
            
            # Connect
            if not parser.connect():
                return json.dumps({
                    "status": "error",
                    "message": "Failed to connect to email server"
                })
            
            try:
                # Load existing email keys (id or timestamp+subject fallback)
                try:
                    existing = self.data_manager.get_emails(exclude_spam=False)
                except Exception:
                    existing = []
                existing_keys = set()
                for e in existing:
                    if e.get('id'):
                        existing_keys.add(f"id::{e.get('id')}")
                    else:
                        existing_keys.add(f"ts_subj::{e.get('timestamp')}::{e.get('subject')}")
                
                # Fetch emails
                if search_query:
                    fetched = parser.fetch_emails_with_search(
                        search_criteria=search_query,
                        limit=limit,
                        parallel=True
                    )
                else:
                    fetched = parser.fetch_emails(
                        folder='INBOX',
                        limit=limit,
                        parallel=True
                    )
                
                if not fetched:
                    return json.dumps({
                        "status": "success",
                        "message": "No new emails found",
                        "total_emails": len(existing),
                        "new_emails": 0,
                        "new_emails_details": []
                    }, ensure_ascii=False, indent=2)
                
                # Detect NEW emails (only save new ones)
                def key_of(e):
                    return f"id::{e.get('id')}" if e.get('id') else f"ts_subj::{e.get('timestamp')}::{e.get('subject')}"
                new_emails = [e for e in fetched if key_of(e) not in existing_keys]
                
                if not new_emails:
                    return json.dumps({
                        "status": "success",
                        "message": "No new emails (all existing)",
                        "total_emails": len(existing),
                        "new_emails": 0,
                        "new_emails_details": []
                    }, ensure_ascii=False, indent=2)
                
                # Save only new emails
                save_result = self.data_manager.save_emails(new_emails)
                
                # Add short summary list to response
                short_list = []
                for e in new_emails[:100]:
                    short_list.append({
                        "id": e.get('id'),
                        "timestamp": e.get('timestamp'),
                        "from": e.get('from'),
                        "to": e.get('to'),
                        "subject": e.get('subject'),
                        "snippet": (e.get('snippet') or (e.get('body') or '')[:200]).strip()
                    })
                
                response = {
                    "status": "success",
                    "message": "Emails refreshed",
                    "total_emails": save_result.total_count,
                    "new_emails": save_result.new_count,
                    "existing_emails": save_result.existing_count,
                    "search_query": search_query,
                    "updated_at": datetime.now().isoformat(),
                    "new_emails_details": short_list
                }
                
                logger.info(f"Agent: {save_result.new_count} new emails added")
                return json.dumps(response, ensure_ascii=False, indent=2)
            
            finally:
                parser.disconnect()
        
        except Exception as e:
            logger.error(f"Email refresh error: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            }, ensure_ascii=False)
    
    def refresh_drive_files(self, folder_name: str = "Wpmesages") -> str:
        """
        Fetch new files from Google Drive
        
        Args:
            folder_name: Drive folder name
        
        Returns:
            JSON result
        """
        try:
            if not self.service_account_file:
                return json.dumps({
                    "status": "error",
                    "message": "Service account file not configured"
                })
            
            logger.info(f"Agent: Refreshing Drive files ({folder_name})")
            
            # WhatsApp export directory
            from pathlib import Path
            whatsapp_dir = Path("whatsapp_export")
            whatsapp_dir.mkdir(parents=True, exist_ok=True)
            
            # Fetch from Drive
            downloaded_files = auto_sync_from_drive(
                service_account_file=self.service_account_file,
                output_dir=whatsapp_dir,
                folder_name=folder_name
            )
            
            if not downloaded_files:
                return json.dumps({
                    "status": "success",
                    "message": "No new files in Drive",
                    "downloaded_files": 0
                })
            
            # Parse files
            from ..parsers.whatsapp_parser import WhatsAppParser
            parser = WhatsAppParser()
            
            processed_chats = []
            for file_path in downloaded_files:
                if file_path.endswith('.txt'):
                    messages = parser.parse_file(file_path)
                    if messages:
                        chat_name = Path(file_path).stem
                        result = self.data_manager.save_whatsapp_messages(messages, chat_name)
                        processed_chats.append({
                            "chat_name": chat_name,
                            "total_messages": result.total_count,
                            "new_messages": result.new_count
                        })
            
            response = {
                "status": "success",
                "message": "Drive files refreshed",
                "downloaded_files": len(downloaded_files),
                "processed_chats": len(processed_chats),
                "chats": processed_chats,
                "updated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Agent: {len(downloaded_files)} files downloaded, {len(processed_chats)} chats processed")
            return json.dumps(response, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Drive refresh error: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            }, ensure_ascii=False)
    
    def check_for_updates(self) -> str:
        """
        Check for updates (Drive and Email)
        
        Returns:
            JSON summary
        """
        try:
            logger.info("Agent: Checking for updates")
            
            updates = {
                "status": "success",
                "checked_at": datetime.now().isoformat(),
                "drive": {"available": False, "new_files": 0},
                "email": {"available": False, "estimated_new": 0}
            }
            
            # Drive check
            if self.service_account_file:
                try:
                    from ..parsers.drive_sync import list_drive_files
                    files = list_drive_files(
                        service_account_file=self.service_account_file,
                        folder_name="Wpmesages"
                    )
                    updates["drive"]["available"] = True
                    updates["drive"]["new_files"] = len(files)
                except:
                    pass
            
            # Email check (only estimate)
            if self.email_config.get('address'):
                updates["email"]["available"] = True
                updates["email"]["estimated_new"] = "Unknown (run refresh_emails)"
            
            logger.info("Agent: Update check completed")
            return json.dumps(updates, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Update check error: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            }, ensure_ascii=False)


def get_refresh_tools_description() -> str:
    """
    Return description of refresh tools
    
    Returns:
        Tool descriptions
    """
    return """
# Agent Data Refresh Tools

## 1. refresh_emails(search_query=None, limit=50)
Refresh emails (fetch fresh data).

**Parameters**:
- search_query: Email search query (e.g., "from:penelope@ac.com")
- limit: Maximum email count (default: 50)

**Example**:
```python
refresh_tools.refresh_emails(search_query="from:penelope@ac.com", limit=20)
```

## 2. refresh_drive_files(folder_name="Wpmesages")
Fetch new files from Google Drive.

**Parameters**:
- folder_name: Drive folder name (default: "Wpmesages")

**Example**:
```python
refresh_tools.refresh_drive_files()
```

## 3. check_for_updates()
Check for updates (Drive and Email).

**Parameters**: None

**Example**:
```python
refresh_tools.check_for_updates()
```

## Usage Scenarios:
- "Are there new emails from Penelope?" → refresh_emails(search_query="from:penelope@ac.com")
- "Are there new WhatsApp exports in Drive?" → refresh_drive_files()
- "Check for updates" → check_for_updates()
"""
