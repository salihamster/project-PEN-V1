"""
Email-specific agent tools for advanced email operations.

This module provides specialized tools for email search, filtering,
and management with metadata-based queries.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..storage.data_manager import DataManager
from ..utils.logger import get_logger
from ..exceptions import ToolExecutionError
from ..enums import SearchField
from ..config import AGENT_CONFIG

logger = get_logger(__name__)


class EmailTools:
    """
    Specialized tools for email operations.
    
    Provides advanced email search and filtering capabilities
    including sender-based, subject-based, and metadata queries.
    
    Attributes:
        data_manager: DataManager instance for data operations
    """
    
    def __init__(self, data_manager: DataManager) -> None:
        """
        Initialize EmailTools.
        
        Args:
            data_manager: DataManager instance
        """
        self.data_manager = data_manager
        logger.info("EmailTools initialized")
    
    def search_by_sender(
        self,
        sender: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = AGENT_CONFIG.default_search_limit
    ) -> str:
        """
        Search emails by sender address.
        
        Args:
            sender: Sender email address or name (partial match supported)
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            limit: Maximum number of results
            
        Returns:
            JSON string with search results
        """
        try:
            emails = self.data_manager.get_emails(
                start_date=start_date,
                end_date=end_date,
                exclude_spam=True
            )
            
            # Filter by sender
            sender_lower = sender.lower()
            filtered = [
                email for email in emails
                if sender_lower in email.get('from', '').lower()
            ]
            
            # Sort by date (newest first) and apply limit
            filtered.sort(key=lambda x: x['timestamp'], reverse=True)
            if len(filtered) > limit:
                filtered = filtered[:limit]
            
            result = {
                "status": "success",
                "query": {
                    "sender": sender,
                    "start_date": start_date,
                    "end_date": end_date
                },
                "total_results": len(filtered),
                "emails": filtered
            }
            
            logger.info(f"Found {len(filtered)} emails from sender: {sender}")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to search emails by sender: {e}")
            return self._error_response(str(e))
    
    def search_by_subject(
        self,
        subject: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = AGENT_CONFIG.default_search_limit
    ) -> str:
        """
        Search emails by subject line.
        
        Args:
            subject: Subject text to search for (partial match)
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            limit: Maximum number of results
            
        Returns:
            JSON string with search results
        """
        try:
            emails = self.data_manager.get_emails(
                start_date=start_date,
                end_date=end_date,
                exclude_spam=True
            )
            
            # Filter by subject
            subject_lower = subject.lower()
            filtered = [
                email for email in emails
                if subject_lower in email.get('subject', '').lower()
            ]
            
            # Sort by date (newest first) and apply limit
            filtered.sort(key=lambda x: x['timestamp'], reverse=True)
            if len(filtered) > limit:
                filtered = filtered[:limit]
            
            result = {
                "status": "success",
                "query": {
                    "subject": subject,
                    "start_date": start_date,
                    "end_date": end_date
                },
                "total_results": len(filtered),
                "emails": filtered
            }
            
            logger.info(f"Found {len(filtered)} emails with subject: {subject}")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to search emails by subject: {e}")
            return self._error_response(str(e))
    
    def search_by_recipient(
        self,
        recipient: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = AGENT_CONFIG.default_search_limit
    ) -> str:
        """
        Search emails by recipient address.
        
        Args:
            recipient: Recipient email address or name (partial match)
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            limit: Maximum number of results
            
        Returns:
            JSON string with search results
        """
        try:
            emails = self.data_manager.get_emails(
                start_date=start_date,
                end_date=end_date,
                exclude_spam=True
            )
            
            # Filter by recipient (check 'to' field)
            recipient_lower = recipient.lower()
            filtered = [
                email for email in emails
                if recipient_lower in email.get('to', '').lower()
            ]
            
            # Sort by date (newest first) and apply limit
            filtered.sort(key=lambda x: x['timestamp'], reverse=True)
            if len(filtered) > limit:
                filtered = filtered[:limit]
            
            result = {
                "status": "success",
                "query": {
                    "recipient": recipient,
                    "start_date": start_date,
                    "end_date": end_date
                },
                "total_results": len(filtered),
                "emails": filtered
            }
            
            logger.info(f"Found {len(filtered)} emails to recipient: {recipient}")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to search emails by recipient: {e}")
            return self._error_response(str(e))
    
    def get_email_thread(
        self,
        subject: str,
        limit: int = 50
    ) -> str:
        """
        Get email thread by subject (all emails with same/similar subject).
        
        Args:
            subject: Subject line to find thread
            limit: Maximum emails in thread
            
        Returns:
            JSON string with thread emails
        """
        try:
            emails = self.data_manager.get_emails(exclude_spam=True)
            
            # Find emails with matching subject (handle Re:, Fwd:, etc.)
            subject_clean = subject.lower().replace('re:', '').replace('fwd:', '').strip()
            
            thread_emails = [
                email for email in emails
                if subject_clean in email.get('subject', '').lower().replace('re:', '').replace('fwd:', '').strip()
            ]
            
            # Sort chronologically
            thread_emails.sort(key=lambda x: x['timestamp'])
            if len(thread_emails) > limit:
                thread_emails = thread_emails[:limit]
            
            result = {
                "status": "success",
                "subject": subject,
                "thread_length": len(thread_emails),
                "emails": thread_emails
            }
            
            logger.info(f"Found thread with {len(thread_emails)} emails")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to get email thread: {e}")
            return self._error_response(str(e))
    
    def advanced_search(
        self,
        query: str,
        search_field: str = SearchField.ALL.value,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exclude_spam: bool = True,
        limit: int = AGENT_CONFIG.default_search_limit
    ) -> str:
        """
        Advanced email search with field-specific queries.
        
        Args:
            query: Search query
            search_field: Field to search in (all, sender, recipient, subject, body)
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            exclude_spam: Exclude spam emails
            limit: Maximum results
            
        Returns:
            JSON string with search results
        """
        try:
            emails = self.data_manager.get_emails(
                start_date=start_date,
                end_date=end_date,
                exclude_spam=exclude_spam
            )
            
            query_lower = query.lower()
            filtered = []
            
            # Field-specific search
            for email in emails:
                match = False
                
                if search_field == SearchField.ALL.value:
                    # Search in all fields
                    match = (
                        query_lower in email.get('from', '').lower() or
                        query_lower in email.get('to', '').lower() or
                        query_lower in email.get('subject', '').lower() or
                        query_lower in email.get('body', '').lower()
                    )
                elif search_field == SearchField.SENDER.value:
                    match = query_lower in email.get('from', '').lower()
                elif search_field == SearchField.RECIPIENT.value:
                    match = query_lower in email.get('to', '').lower()
                elif search_field == SearchField.SUBJECT.value:
                    match = query_lower in email.get('subject', '').lower()
                elif search_field == SearchField.BODY.value:
                    match = query_lower in email.get('body', '').lower()
                
                if match:
                    filtered.append(email)
            
            # Sort and limit
            filtered.sort(key=lambda x: x['timestamp'], reverse=True)
            if len(filtered) > limit:
                filtered = filtered[:limit]
            
            result = {
                "status": "success",
                "query": {
                    "text": query,
                    "field": search_field,
                    "start_date": start_date,
                    "end_date": end_date
                },
                "total_results": len(filtered),
                "emails": filtered
            }
            
            logger.info(f"Advanced search found {len(filtered)} emails")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Advanced email search failed: {e}")
            return self._error_response(str(e))
    
    def list_email_subjects(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 200,
        sort_order: str = "desc",
    ) -> str:
        """List email subjects within a date range with basic metadata.

        Args:
            start_date: Optional start date (YYYY-MM-DD or ISO timestamp)
            end_date: Optional end date (YYYY-MM-DD or ISO timestamp)
            limit: Max number of results (default 200)
            sort_order: 'asc' for oldest first, 'desc' for newest first
        Returns:
            JSON string with minimal email metadata (id, timestamp, from, to, subject)
        """
        try:
            emails = self.data_manager.get_emails(
                start_date=start_date,
                end_date=end_date,
                exclude_spam=True,
            )

            # Sort
            reverse = (str(sort_order).lower() != "asc")
            emails.sort(key=lambda x: x.get("timestamp", ""), reverse=reverse)

            # Limit
            if limit and isinstance(limit, int) and limit > 0:
                emails = emails[:limit]

            items = []
            for e in emails:
                items.append(
                    {
                        "id": e.get("id"),
                        "timestamp": e.get("timestamp"),
                        "from": e.get("from"),
                        "to": e.get("to"),
                        "subject": e.get("subject"),
                        "snippet": (e.get("snippet") or e.get("body", "")[:140]).strip(),
                    }
                )

            return json.dumps(
                {
                    "status": "success",
                    "query": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit,
                        "sort_order": sort_order,
                    },
                    "total_results": len(items),
                    "emails": items,
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            logger.error(f"Failed to list email subjects: {e}")
            return self._error_response(str(e))

    def get_email_content(
        self,
        email_id: Optional[str] = None,
        subject: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> str:
        """Get the full content of a specific email.

        Priority of selection:
        1) by unique email_id
        2) by subject + timestamp match
        3) by subject only (most recent)
        """
        try:
            emails = self.data_manager.get_emails(exclude_spam=False)

            target = None
            if email_id:
                for e in emails:
                    if e.get("id") == email_id:
                        target = e
                        break
            elif subject and timestamp:
                subj_norm = subject.strip().lower()
                for e in emails:
                    if (
                        e.get("timestamp") == timestamp
                        and subj_norm in (e.get("subject", "").lower())
                    ):
                        target = e
                        break
            elif subject:
                subj_norm = subject.strip().lower()
                candidates = [e for e in emails if subj_norm in (e.get("subject", "").lower())]
                candidates.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                if candidates:
                    target = candidates[0]

            if not target:
                return json.dumps(
                    {"status": "error", "message": "Email not found with given criteria"},
                    ensure_ascii=False,
                    indent=2,
                )

            # Build response with safe defaults
            # Check if body contains HTML (starts with <!DOCTYPE or <html)
            body_content = target.get("body") or target.get("text") or ""
            html_content = target.get("html_body") or target.get("html") or ""
            
            # If html_body is empty but body contains HTML, use body as html_body
            if not html_content and body_content.strip().startswith(("<!", "<html")):
                html_content = body_content
            
            resp = {
                "status": "success",
                "email": {
                    "id": target.get("id"),
                    "timestamp": target.get("timestamp"),
                    "from": target.get("from"),
                    "to": target.get("to"),
                    "subject": target.get("subject"),
                    "body": body_content,
                    "html_body": html_content,
                    "attachments": target.get("attachments", []),
                    "headers": target.get("headers", {}),
                },
            }
            return json.dumps(resp, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to get email content: {e}")
            return self._error_response(str(e))

    def search_emails(
        self,
        sender: Optional[str] = None,
        recipient: Optional[str] = None,
        subject: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
    ) -> str:
        """Search emails by sender/recipient/subject with optional date range.

        Args:
            sender: Filter by sender (substring match)
            recipient: Filter by recipient (substring match)
            subject: Filter by subject (substring match)
            start_date: Start date (YYYY-MM-DD or ISO)
            end_date: End date (YYYY-MM-DD or ISO)
            limit: Max results (default 100)
        """
        try:
            emails = self.data_manager.get_emails(
                start_date=start_date,
                end_date=end_date,
                exclude_spam=True,
            )

            def _contains(val: Optional[str], needle: Optional[str]) -> bool:
                if not needle:
                    return True
                return (needle.lower() in (val or "").lower())

            filtered = []
            for e in emails:
                if not _contains(e.get("from"), sender):
                    continue
                if not _contains(e.get("to"), recipient):
                    continue
                if not _contains(e.get("subject"), subject):
                    continue
                filtered.append(e)

            # Sort newest first and limit
            filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            if limit and isinstance(limit, int) and limit > 0:
                filtered = filtered[:limit]

            items = []
            for e in filtered:
                items.append(
                    {
                        "id": e.get("id"),
                        "timestamp": e.get("timestamp"),
                        "from": e.get("from"),
                        "to": e.get("to"),
                        "subject": e.get("subject"),
                        "snippet": (e.get("snippet") or e.get("body", "")[:200]).strip(),
                    }
                )

            return json.dumps(
                {
                    "status": "success",
                    "query": {
                        "sender": sender,
                        "recipient": recipient,
                        "subject": subject,
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit,
                    },
                    "total_results": len(items),
                    "emails": items,
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            logger.error(f"Failed to search emails: {e}")
            return self._error_response(str(e))

    def _error_response(self, message: str) -> str:
        """Create standardized error response."""
        return json.dumps({
            "status": "error",
            "message": message
        }, ensure_ascii=False, indent=2)
