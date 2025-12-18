"""
Data management module for categorized data storage and retrieval.

This module provides a centralized interface for managing WhatsApp messages,
emails, and other data sources with proper categorization and persistence.
"""

import json
import re
import unicodedata
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from ..utils.logger import get_logger
from ..exceptions import DataManagerError, ValidationError
from ..enums import MessageSource

logger = get_logger(__name__)


@dataclass
class SaveResult:
    """Result of a save operation."""
    status: str
    total_count: int
    new_count: int
    existing_count: int
    file_path: Optional[str] = None
    chat_name: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ChatInfo:
    """Information about a WhatsApp chat."""
    name: str
    file_path: str
    message_count: int
    date_range_start: str
    date_range_end: str
    last_updated: str


@dataclass
class Statistics:
    """Overall statistics for all data sources."""
    whatsapp_total_chats: int
    whatsapp_total_messages: int
    whatsapp_chats: List[ChatInfo]
    email_total_count: int
    email_spam_count: int
    last_updated: str


class DataManager:
    """
    Manages categorized data storage and retrieval.
    
    This class handles all data persistence operations including:
    - WhatsApp message storage and retrieval
    - Email storage and retrieval
    - Statistics generation
    - Log management
    
    Attributes:
        data_dir: Root directory for all data storage
        whatsapp_dir: Directory for WhatsApp data
        email_dir: Directory for email data
        logs_dir: Directory for operation logs
    """
    
    def __init__(self, data_dir: Path) -> None:
        """
        Initialize the DataManager.
        
        Args:
            data_dir: Root directory for data storage
            
        Raises:
            DataManagerError: If directory creation fails
        """
        try:
            self.data_dir = Path(data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            # Create categorized data directories
            self.whatsapp_dir = self.data_dir / "whatsapp"
            self.email_dir = self.data_dir / "email"
            self.logs_dir = self.data_dir / "logs"
            
            for directory in [self.whatsapp_dir, self.email_dir, self.logs_dir]:
                directory.mkdir(parents=True, exist_ok=True)
                
            logger.info(f"DataManager initialized with data_dir: {self.data_dir}")
            
        except Exception as e:
            raise DataManagerError(f"Failed to initialize DataManager: {e}") from e
    
    def save_whatsapp_messages(
        self, 
        messages: List[Dict[str, Any]], 
        chat_name: str
    ) -> SaveResult:
        """
        Save WhatsApp messages with deduplication.
        
        This method merges new messages with existing ones, avoiding duplicates
        based on timestamp, and maintains chronological order.
        
        Args:
            messages: List of message dictionaries
            chat_name: Name of the chat (used for filename)
            
        Returns:
            SaveResult containing operation details
            
        Raises:
            DataManagerError: If save operation fails
            ValidationError: If input data is invalid
        """
        if not messages:
            raise ValidationError("Cannot save empty message list")
        
        if not chat_name:
            raise ValidationError("Chat name cannot be empty")
        
        try:
            # Sanitize filename
            safe_chat_name = self._sanitize_filename(chat_name)
            chat_file = self.whatsapp_dir / f"{safe_chat_name}.json"
            
            # Load existing messages
            existing_messages = self._load_json_file(chat_file, default=[])
            logger.info(
                f"Loaded {len(existing_messages)} existing messages for: {safe_chat_name}"
            )
            
            # Deduplicate based on timestamp
            existing_timestamps = {msg['timestamp'] for msg in existing_messages}
            new_messages = [
                msg for msg in messages 
                if msg['timestamp'] not in existing_timestamps
            ]
            
            # Merge and sort chronologically
            all_messages = existing_messages + new_messages
            all_messages.sort(key=lambda x: x['timestamp'])
            
            # Save to file
            self._save_json_file(chat_file, all_messages)
            
            # Log the operation
            self._log_operation(
                category="whatsapp",
                log_entry={
                    "timestamp": datetime.now().isoformat(),
                    "chat_name": safe_chat_name,
                    "action": "update",
                    "total_messages": len(all_messages),
                    "new_messages": len(new_messages),
                    "existing_messages": len(existing_messages),
                    "date_range": {
                        "start": all_messages[0]['timestamp'] if all_messages else None,
                        "end": all_messages[-1]['timestamp'] if all_messages else None
                    }
                }
            )
            
            logger.info(
                f"WhatsApp chat saved: {safe_chat_name} "
                f"(Total: {len(all_messages)}, New: {len(new_messages)})"
            )
            
            return SaveResult(
                status="success",
                total_count=len(all_messages),
                new_count=len(new_messages),
                existing_count=len(existing_messages),
                file_path=str(chat_file),
                chat_name=safe_chat_name
            )
            
        except (ValidationError, DataManagerError):
            raise
        except Exception as e:
            raise DataManagerError(
                f"Failed to save WhatsApp messages for {chat_name}: {e}"
            ) from e
    
    def save_emails(self, emails: List[Dict[str, Any]]) -> SaveResult:
        """
        Save emails with deduplication.
        
        This method merges new emails with existing ones, avoiding duplicates
        based on email ID or timestamp+subject combination.
        
        Args:
            emails: List of email dictionaries
            
        Returns:
            SaveResult containing operation details
            
        Raises:
            DataManagerError: If save operation fails
            ValidationError: If input data is invalid
        """
        if not emails:
            raise ValidationError("Cannot save empty email list")
        
        try:
            email_file = self.email_dir / "all_emails.json"
            
            # Load existing emails
            existing_emails = self._load_json_file(email_file, default=[])
            logger.info(f"Loaded {len(existing_emails)} existing emails")
            
            # Deduplicate based on ID
            existing_ids = {
                email['id'] for email in existing_emails 
                if email.get('id')
            }
            new_emails = [
                email for email in emails 
                if email.get('id') and email['id'] not in existing_ids
            ]
            
            # Handle emails without ID (use timestamp + subject)
            for email in emails:
                if not email.get('id'):
                    is_duplicate = any(
                        e['timestamp'] == email['timestamp'] and 
                        e.get('subject') == email.get('subject')
                        for e in existing_emails
                    )
                    if not is_duplicate:
                        new_emails.append(email)
            
            # Merge and sort chronologically
            all_emails = existing_emails + new_emails
            all_emails.sort(key=lambda x: x['timestamp'])
            
            # Save to file
            self._save_json_file(email_file, all_emails)
            
            # Calculate spam count
            spam_count = sum(1 for e in all_emails if e.get('is_spam', False))
            
            # Log the operation
            self._log_operation(
                category="email",
                log_entry={
                    "timestamp": datetime.now().isoformat(),
                    "action": "update",
                    "total_emails": len(all_emails),
                    "new_emails": len(new_emails),
                    "existing_emails": len(existing_emails),
                    "spam_count": spam_count,
                    "date_range": {
                        "start": all_emails[0]['timestamp'] if all_emails else None,
                        "end": all_emails[-1]['timestamp'] if all_emails else None
                    }
                }
            )
            
            logger.info(
                f"Emails saved: Total: {len(all_emails)}, "
                f"New: {len(new_emails)}, Spam: {spam_count}"
            )
            
            return SaveResult(
                status="success",
                total_count=len(all_emails),
                new_count=len(new_emails),
                existing_count=len(existing_emails),
                file_path=str(email_file)
            )
            
        except (ValidationError, DataManagerError):
            raise
        except Exception as e:
            raise DataManagerError(f"Failed to save emails: {e}") from e
    
    def get_whatsapp_chats(self) -> List[ChatInfo]:
        """
        List all WhatsApp chats with metadata.
        
        Returns:
            List of ChatInfo objects sorted by last update time
            
        Raises:
            DataManagerError: If listing operation fails
        """
        try:
            chats = []
            
            for chat_file in self.whatsapp_dir.glob("*.json"):
                try:
                    messages = self._load_json_file(chat_file, default=[])
                    
                    if messages:
                        sanitized_name = self._sanitize_filename(chat_file.stem)
                        
                        chats.append(ChatInfo(
                            name=sanitized_name,
                            file_path=str(chat_file),
                            message_count=len(messages),
                            date_range_start=messages[0]['timestamp'],
                            date_range_end=messages[-1]['timestamp'],
                            last_updated=datetime.fromtimestamp(
                                chat_file.stat().st_mtime
                            ).isoformat()
                        ))
                        
                except Exception as e:
                    logger.error(f"Failed to read chat file {chat_file}: {e}")
                    continue
            
            # Sort by last updated (most recent first)
            chats.sort(key=lambda x: x.last_updated, reverse=True)
            
            return chats
            
        except Exception as e:
            raise DataManagerError(f"Failed to list WhatsApp chats: {e}") from e
    
    def get_whatsapp_messages(
        self,
        chat_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve messages from a specific WhatsApp chat.
        
        Args:
            chat_name: Name of the chat
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            
        Returns:
            List of message dictionaries
            
        Raises:
            DataManagerError: If retrieval operation fails
            ValidationError: If chat doesn't exist
        """
        try:
            safe_chat_name = self._sanitize_filename(chat_name)
            chat_file = self.whatsapp_dir / f"{safe_chat_name}.json"
            
            if not chat_file.exists():
                raise ValidationError(f"Chat not found: {chat_name}")
            
            messages = self._load_json_file(chat_file, default=[])
            
            # Apply date filters
            if start_date:
                messages = [m for m in messages if m['timestamp'] >= start_date]
            if end_date:
                messages = [m for m in messages if m['timestamp'] <= end_date]
            
            return messages
            
        except ValidationError:
            raise
        except Exception as e:
            raise DataManagerError(
                f"Failed to get messages for {chat_name}: {e}"
            ) from e
    
    def get_emails(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exclude_spam: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve emails with optional filtering.
        
        Args:
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            exclude_spam: Whether to exclude spam emails
            
        Returns:
            List of email dictionaries
            
        Raises:
            DataManagerError: If retrieval operation fails
        """
        try:
            email_file = self.email_dir / "all_emails.json"
            
            if not email_file.exists():
                logger.warning("Email file not found")
                return []
            
            emails = self._load_json_file(email_file, default=[])
            
            # Apply filters
            if exclude_spam:
                emails = [e for e in emails if not e.get('is_spam', False)]
            
            if start_date:
                emails = [e for e in emails if e['timestamp'] >= start_date]
            if end_date:
                emails = [e for e in emails if e['timestamp'] <= end_date]
            
            return emails
            
        except Exception as e:
            raise DataManagerError(f"Failed to get emails: {e}") from e
    
    def get_statistics(self) -> Statistics:
        """
        Generate overall statistics for all data sources.
        
        Returns:
            Statistics object with comprehensive data
            
        Raises:
            DataManagerError: If statistics generation fails
        """
        try:
            # WhatsApp statistics
            chats = self.get_whatsapp_chats()
            whatsapp_total_messages = sum(chat.message_count for chat in chats)
            
            # Email statistics
            email_file = self.email_dir / "all_emails.json"
            email_total = 0
            email_spam = 0
            
            if email_file.exists():
                emails = self._load_json_file(email_file, default=[])
                email_total = len(emails)
                email_spam = sum(1 for e in emails if e.get('is_spam', False))
            
            return Statistics(
                whatsapp_total_chats=len(chats),
                whatsapp_total_messages=whatsapp_total_messages,
                whatsapp_chats=chats,
                email_total_count=email_total,
                email_spam_count=email_spam,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            raise DataManagerError(f"Failed to generate statistics: {e}") from e
    
    def _load_json_file(
        self, 
        file_path: Path, 
        default: Any = None
    ) -> Any:
        """
        Load JSON data from file with error handling.
        
        Args:
            file_path: Path to JSON file
            default: Default value if file doesn't exist
            
        Returns:
            Parsed JSON data or default value
            
        Raises:
            DataManagerError: If file exists but cannot be read
        """
        if not file_path.exists():
            return default
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise DataManagerError(
                f"Invalid JSON in file {file_path}: {e}"
            ) from e
        except Exception as e:
            raise DataManagerError(
                f"Failed to read file {file_path}: {e}"
            ) from e
    
    def _save_json_file(self, file_path: Path, data: Any) -> None:
        """
        Save data to JSON file with error handling.
        
        Args:
            file_path: Path to JSON file
            data: Data to save
            
        Raises:
            DataManagerError: If save operation fails
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise DataManagerError(
                f"Failed to write file {file_path}: {e}"
            ) from e
    
    def _log_operation(self, category: str, log_entry: Dict[str, Any]) -> None:
        """
        Log an operation to the appropriate log file.
        
        Args:
            category: Category of the operation (whatsapp, email)
            log_entry: Dictionary containing log data
        """
        log_file = self.logs_dir / f"{category}_log.jsonl"
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Failed to write log: {e}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing invalid characters and emojis.
        
        This method ensures filenames are safe for all operating systems
        by removing Unicode control characters, emojis, and invalid path characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem use
        """
        # Remove Unicode format characters (Left-to-Right Mark, etc.)
        filename = ''.join(
            char for char in filename 
            if unicodedata.category(char) != 'Cf'
        )
        
        # Normalize Unicode and remove non-ASCII characters (including emojis)
        normalized = unicodedata.normalize('NFKD', filename)
        ascii_only = normalized.encode('ascii', 'ignore').decode('ascii')
        
        # Remove invalid filesystem characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            ascii_only = ascii_only.replace(char, '_')
        
        # Replace spaces with underscores
        ascii_only = ascii_only.replace(' ', '_')
        
        # Remove leading/trailing dots
        ascii_only = ascii_only.strip('.')
        
        # Collapse multiple underscores
        ascii_only = re.sub(r'_+', '_', ascii_only)
        
        # Ensure non-empty result
        return ascii_only if ascii_only else "unknown"
