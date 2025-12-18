"""
Agent data access tools for WhatsApp and email data retrieval.

This module provides a clean interface for the agent to access
stored data with proper error handling and result formatting.
"""

import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..storage.data_manager import DataManager
from ..utils.logger import get_logger
from ..exceptions import ToolExecutionError, ValidationError
from ..enums import MessageSource
from ..config import AGENT_CONFIG

logger = get_logger(__name__)


class DataTools:
    """
    Agent tools for data access operations.
    
    This class provides methods that the agent can call to retrieve
    WhatsApp messages, emails, and statistics. All methods return
    JSON-formatted strings for easy agent consumption.
    
    Attributes:
        data_manager: DataManager instance for data operations
    """
    
    def __init__(self, data_manager: DataManager) -> None:
        """
        Initialize DataTools.
        
        Args:
            data_manager: DataManager instance for data operations
        """
        self.data_manager = data_manager
        logger.info("DataTools initialized")
    
    def list_whatsapp_chats(self) -> str:
        """
        List all available WhatsApp chats.
        
        Returns:
            JSON string containing chat list with metadata
            
        Example:
            {
                "status": "success",
                "total_chats": 5,
                "chats": [...]
            }
        """
        try:
            chats = self.data_manager.get_whatsapp_chats()
            
            # Convert ChatInfo objects to dictionaries
            chat_dicts = [
                {
                    "name": chat.name,
                    "message_count": chat.message_count,
                    "date_range": {
                        "start": chat.date_range_start,
                        "end": chat.date_range_end
                    },
                    "last_updated": chat.last_updated
                }
                for chat in chats
            ]
            
            result = {
                "status": "success",
                "total_chats": len(chats),
                "chats": chat_dicts
            }
            
            logger.info(f"Agent: Listed {len(chats)} WhatsApp chats")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to list WhatsApp chats: {e}")
            return self._error_response(str(e))
    
    def get_whatsapp_messages(
        self,
        chat_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> str:
        """
        Retrieve messages from a specific WhatsApp chat.
        
        Args:
            chat_name: Name of the chat
            start_date: Optional start date (YYYY-MM-DD format)
            end_date: Optional end date (YYYY-MM-DD format)
            limit: Optional maximum number of messages to return
            
        Returns:
            JSON string containing messages
            
        Example:
            {
                "status": "success",
                "chat_name": "example_chat",
                "total_messages": 100,
                "messages": [...]
            }
        """
        try:
            # Validate and convert limit
            if limit is not None:
                limit = int(limit)
            
            messages = self.data_manager.get_whatsapp_messages(
                chat_name=chat_name,
                start_date=start_date,
                end_date=end_date
            )
            
            # Handle chat not found
            if not messages:
                chats = self.data_manager.get_whatsapp_chats()
                available_chats = [chat.name for chat in chats]
                
                logger.warning(f"Chat not found: {chat_name}")
                return json.dumps({
                    "status": "error",
                    "message": f"Chat not found: {chat_name}",
                    "suggestion": "Use list_whatsapp_chats to see available chats",
                    "available_chats": available_chats[:10]
                }, ensure_ascii=False, indent=2)
            
            # Apply limit (take last N messages)
            if limit and len(messages) > limit:
                messages = messages[-limit:]
            
            result = {
                "status": "success",
                "chat_name": chat_name,
                "total_messages": len(messages),
                "messages": messages
            }
            
            logger.info(
                f"Agent: Retrieved {len(messages)} messages from {chat_name}"
            )
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return self._error_response(str(e))
        except Exception as e:
            logger.error(f"Failed to get WhatsApp messages: {e}")
            return self._error_response(str(e))
    
    def get_emails(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exclude_spam: bool = True,
        limit: Optional[int] = None
    ) -> str:
        """
        Retrieve emails with optional filtering.
        
        Args:
            start_date: Optional start date (YYYY-MM-DD format)
            end_date: Optional end date (YYYY-MM-DD format)
            exclude_spam: Whether to exclude spam emails (default: True)
            limit: Optional maximum number of emails to return
            
        Returns:
            JSON string containing emails
            
        Example:
            {
                "status": "success",
                "total_emails": 50,
                "emails": [...]
            }
        """
        try:
            # Validate and convert limit
            if limit is not None:
                limit = int(limit)
            
            emails = self.data_manager.get_emails(
                start_date=start_date,
                end_date=end_date,
                exclude_spam=exclude_spam
            )
            
            # Apply limit (take last N emails)
            if limit and len(emails) > limit:
                emails = emails[-limit:]
            
            result = {
                "status": "success",
                "total_emails": len(emails),
                "emails": emails
            }
            
            logger.info(f"Agent: Retrieved {len(emails)} emails")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to get emails: {e}")
            return self._error_response(str(e))
    
    def get_statistics(self) -> str:
        """
        Get overall statistics for all data sources.
        
        Returns:
            JSON string containing comprehensive statistics
            
        Example:
            {
                "status": "success",
                "statistics": {
                    "whatsapp": {...},
                    "email": {...}
                }
            }
        """
        try:
            stats = self.data_manager.get_statistics()
            
            # Convert to dictionary
            result = {
                "status": "success",
                "statistics": {
                    "whatsapp": {
                        "total_chats": stats.whatsapp_total_chats,
                        "total_messages": stats.whatsapp_total_messages
                    },
                    "email": {
                        "total_emails": stats.email_total_count,
                        "spam_count": stats.email_spam_count
                    },
                    "last_updated": stats.last_updated
                }
            }
            
            logger.info("Agent: Retrieved statistics")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return self._error_response(str(e))
    
    def search_messages(
        self,
        query: str,
        source: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = AGENT_CONFIG.default_search_limit
    ) -> str:
        """
        Search for messages across WhatsApp and/or email.
        
        Args:
            query: Search query string
            source: Optional source filter ("whatsapp", "email", or None for all)
            start_date: Optional start date (YYYY-MM-DD format)
            end_date: Optional end date (YYYY-MM-DD format)
            limit: Maximum number of results (default from config)
            
        Returns:
            JSON string containing search results
            
        Example:
            {
                "status": "success",
                "query": "meeting",
                "total_results": 15,
                "results": [...]
            }
        """
        try:
            # Validate and convert limit
            limit = int(limit) if limit is not None else AGENT_CONFIG.default_search_limit
            
            results = []
            query_lower = query.lower()
            
            # Search in WhatsApp
            if source is None or source == MessageSource.WHATSAPP.value:
                chats = self.data_manager.get_whatsapp_chats()
                for chat in chats:
                    messages = self.data_manager.get_whatsapp_messages(
                        chat_name=chat.name,
                        start_date=start_date,
                        end_date=end_date
                    )
                    for msg in messages:
                        if query_lower in msg.get('body', '').lower():
                            results.append({
                                **msg,
                                "source": MessageSource.WHATSAPP.value,
                                "chat_name": chat.name
                            })
            
            # Search in emails
            if source is None or source == MessageSource.EMAIL.value:
                emails = self.data_manager.get_emails(
                    start_date=start_date,
                    end_date=end_date,
                    exclude_spam=True
                )
                for email in emails:
                    if (query_lower in email.get('subject', '').lower() or
                        query_lower in email.get('body', '').lower()):
                        results.append({
                            **email,
                            "source": MessageSource.EMAIL.value
                        })
            
            # Sort by timestamp (most recent first) and apply limit
            results.sort(key=lambda x: x['timestamp'], reverse=True)
            if len(results) > limit:
                results = results[:limit]
            
            result = {
                "status": "success",
                "query": query,
                "total_results": len(results),
                "results": results
            }
            
            logger.info(f"Agent: Found {len(results)} results for query '{query}'")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to search messages: {e}")
            return self._error_response(str(e))
    
    def get_recent_messages(
        self,
        days: int = AGENT_CONFIG.default_recent_days,
        source: Optional[str] = None,
        limit: int = AGENT_CONFIG.default_recent_limit
    ) -> str:
        """
        Get messages from the last N days.
        
        Args:
            days: Number of days to look back (default from config)
            source: Optional source filter ("whatsapp", "email", or None for all)
            limit: Maximum number of messages (default from config)
            
        Returns:
            JSON string containing recent messages
            
        Example:
            {
                "status": "success",
                "days": 7,
                "total_messages": 50,
                "messages": [...]
            }
        """
        try:
            # Validate and convert parameters
            days = int(days) if days is not None else AGENT_CONFIG.default_recent_days
            limit = int(limit) if limit is not None else AGENT_CONFIG.default_recent_limit
            
            # Calculate date range
            end_date = datetime.now().isoformat()
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            messages = []
            
            # Get WhatsApp messages
            if source is None or source == MessageSource.WHATSAPP.value:
                chats = self.data_manager.get_whatsapp_chats()
                for chat in chats:
                    chat_messages = self.data_manager.get_whatsapp_messages(
                        chat_name=chat.name,
                        start_date=start_date,
                        end_date=end_date
                    )
                    for msg in chat_messages:
                        messages.append({
                            **msg,
                            "source": MessageSource.WHATSAPP.value,
                            "chat_name": chat.name
                        })
            
            # Get emails
            if source is None or source == MessageSource.EMAIL.value:
                emails = self.data_manager.get_emails(
                    start_date=start_date,
                    end_date=end_date,
                    exclude_spam=True
                )
                for email in emails:
                    messages.append({
                        **email,
                        "source": MessageSource.EMAIL.value
                    })
            
            # Sort by timestamp (most recent first) and apply limit
            messages.sort(key=lambda x: x['timestamp'], reverse=True)
            if len(messages) > limit:
                messages = messages[:limit]
            
            result = {
                "status": "success",
                "days": days,
                "start_date": start_date[:10],
                "end_date": end_date[:10],
                "total_messages": len(messages),
                "messages": messages
            }
            
            logger.info(
                f"Agent: Retrieved {len(messages)} messages from last {days} days"
            )
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return self._error_response(str(e))
    
    def _error_response(self, message: str) -> str:
        """
        Create a standardized error response.
        
        Args:
            message: Error message
            
        Returns:
            JSON string with error details
        """
        return json.dumps({
            "status": "error",
            "message": message
        }, ensure_ascii=False, indent=2)
