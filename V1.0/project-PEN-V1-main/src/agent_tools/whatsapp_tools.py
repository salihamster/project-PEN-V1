"""
WhatsApp-specific agent tools for advanced chat operations.

This module provides specialized tools for WhatsApp chat search,
participant management, and chronological tracking.
"""

import json
from typing import Optional, List, Dict, Any, Set
from datetime import datetime

from ..storage.data_manager import DataManager
from ..utils.logger import get_logger
from ..exceptions import ToolExecutionError
from ..config import AGENT_CONFIG

logger = get_logger(__name__)


class WhatsAppTools:
    """
    Specialized tools for WhatsApp operations.
    
    Provides advanced WhatsApp search, participant tracking,
    and chronological analysis capabilities.
    
    Attributes:
        data_manager: DataManager instance for data operations
    """
    
    def __init__(self, data_manager: DataManager) -> None:
        """
        Initialize WhatsAppTools.
        
        Args:
            data_manager: DataManager instance
        """
        self.data_manager = data_manager
        logger.info("WhatsAppTools initialized")
    
    def search_by_sender(
        self,
        chat_name: str,
        sender: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = AGENT_CONFIG.default_search_limit
    ) -> str:
        """
        Search messages by sender in a specific chat.
        
        Args:
            chat_name: Name of the chat
            sender: Sender name (partial match supported)
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            limit: Maximum number of results
            
        Returns:
            JSON string with search results
        """
        try:
            messages = self.data_manager.get_whatsapp_messages(
                chat_name=chat_name,
                start_date=start_date,
                end_date=end_date
            )
            
            # Filter by sender
            sender_lower = sender.lower()
            filtered = [
                msg for msg in messages
                if sender_lower in msg.get('sender', '').lower()
            ]
            
            # Apply limit
            if len(filtered) > limit:
                filtered = filtered[-limit:]  # Last N messages
            
            result = {
                "status": "success",
                "chat_name": chat_name,
                "query": {
                    "sender": sender,
                    "start_date": start_date,
                    "end_date": end_date
                },
                "total_results": len(filtered),
                "messages": filtered
            }
            
            logger.info(f"Found {len(filtered)} messages from {sender} in {chat_name}")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to search by sender: {e}")
            return self._error_response(str(e))
    
    def get_chat_participants(
        self,
        chat_name: str
    ) -> str:
        """
        Get list of all participants in a chat with message counts.
        
        Args:
            chat_name: Name of the chat
            
        Returns:
            JSON string with participant information
        """
        try:
            messages = self.data_manager.get_whatsapp_messages(chat_name=chat_name)
            
            # Count messages per participant
            participant_stats: Dict[str, int] = {}
            for msg in messages:
                sender = msg.get('sender', 'Unknown')
                participant_stats[sender] = participant_stats.get(sender, 0) + 1
            
            # Sort by message count
            participants = [
                {"name": name, "message_count": count}
                for name, count in sorted(
                    participant_stats.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ]
            
            result = {
                "status": "success",
                "chat_name": chat_name,
                "total_participants": len(participants),
                "total_messages": len(messages),
                "participants": participants
            }
            
            logger.info(f"Found {len(participants)} participants in {chat_name}")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to get participants: {e}")
            return self._error_response(str(e))
    
    def get_chat_chronology(
        self,
        chat_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: str = "day"
    ) -> str:
        """
        Get chronological message distribution in a chat.
        
        Args:
            chat_name: Name of the chat
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            group_by: Grouping period (day, week, month)
            
        Returns:
            JSON string with chronological data
        """
        try:
            messages = self.data_manager.get_whatsapp_messages(
                chat_name=chat_name,
                start_date=start_date,
                end_date=end_date
            )
            
            # Group messages by time period
            chronology: Dict[str, int] = {}
            
            for msg in messages:
                timestamp = msg.get('timestamp', '')
                if not timestamp:
                    continue
                
                # Extract date part based on grouping
                if group_by == "day":
                    key = timestamp[:10]  # YYYY-MM-DD
                elif group_by == "week":
                    # Get ISO week
                    date_obj = datetime.fromisoformat(timestamp)
                    key = f"{date_obj.year}-W{date_obj.isocalendar()[1]:02d}"
                elif group_by == "month":
                    key = timestamp[:7]  # YYYY-MM
                else:
                    key = timestamp[:10]  # Default to day
                
                chronology[key] = chronology.get(key, 0) + 1
            
            # Sort by date
            sorted_chronology = [
                {"period": period, "message_count": count}
                for period, count in sorted(chronology.items())
            ]
            
            result = {
                "status": "success",
                "chat_name": chat_name,
                "group_by": group_by,
                "date_range": {
                    "start": start_date or (messages[0]['timestamp'][:10] if messages else None),
                    "end": end_date or (messages[-1]['timestamp'][:10] if messages else None)
                },
                "total_messages": len(messages),
                "chronology": sorted_chronology
            }
            
            logger.info(f"Generated chronology for {chat_name} ({len(sorted_chronology)} periods)")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to get chronology: {e}")
            return self._error_response(str(e))
    
    def search_across_chats(
        self,
        keyword: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = AGENT_CONFIG.default_search_limit
    ) -> str:
        """
        Search for keyword across all WhatsApp chats.
        
        Args:
            keyword: Keyword to search for
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            limit: Maximum total results
            
        Returns:
            JSON string with search results from all chats
        """
        try:
            chats = self.data_manager.get_whatsapp_chats()
            keyword_lower = keyword.lower()
            
            all_results = []
            
            for chat in chats:
                messages = self.data_manager.get_whatsapp_messages(
                    chat_name=chat.name,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # Filter by keyword
                for msg in messages:
                    if keyword_lower in msg.get('body', '').lower():
                        all_results.append({
                            **msg,
                            "chat_name": chat.name
                        })
            
            # Sort by timestamp (newest first) and limit
            all_results.sort(key=lambda x: x['timestamp'], reverse=True)
            if len(all_results) > limit:
                all_results = all_results[:limit]
            
            # Group by chat for summary
            chats_with_results: Dict[str, int] = {}
            for result in all_results:
                chat = result['chat_name']
                chats_with_results[chat] = chats_with_results.get(chat, 0) + 1
            
            result = {
                "status": "success",
                "keyword": keyword,
                "total_results": len(all_results),
                "chats_searched": len(chats),
                "chats_with_results": len(chats_with_results),
                "results_by_chat": chats_with_results,
                "messages": all_results
            }
            
            logger.info(f"Found {len(all_results)} messages with '{keyword}' across {len(chats)} chats")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to search across chats: {e}")
            return self._error_response(str(e))
    
    def get_conversation_context(
        self,
        chat_name: str,
        target_timestamp: str,
        context_size: int = 10
    ) -> str:
        """
        Get messages around a specific timestamp for context.
        
        Args:
            chat_name: Name of the chat
            target_timestamp: Target message timestamp
            context_size: Number of messages before and after (default: 10)
            
        Returns:
            JSON string with context messages
        """
        try:
            messages = self.data_manager.get_whatsapp_messages(chat_name=chat_name)
            
            # Find target message index
            target_index = -1
            for i, msg in enumerate(messages):
                if msg['timestamp'] == target_timestamp:
                    target_index = i
                    break
            
            if target_index == -1:
                return self._error_response(f"Message with timestamp {target_timestamp} not found")
            
            # Get context messages
            start_index = max(0, target_index - context_size)
            end_index = min(len(messages), target_index + context_size + 1)
            
            context_messages = messages[start_index:end_index]
            
            result = {
                "status": "success",
                "chat_name": chat_name,
                "target_timestamp": target_timestamp,
                "target_index": target_index,
                "context_size": context_size,
                "total_context_messages": len(context_messages),
                "messages": context_messages
            }
            
            logger.info(f"Retrieved {len(context_messages)} context messages around {target_timestamp}")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return self._error_response(str(e))
    
    def get_media_references(
        self,
        chat_name: str,
        media_type: Optional[str] = None
    ) -> str:
        """
        Get all media references from a chat.
        
        Args:
            chat_name: Name of the chat
            media_type: Optional filter by media type (image, video, audio, document)
            
        Returns:
            JSON string with media references
        """
        try:
            messages = self.data_manager.get_whatsapp_messages(chat_name=chat_name)
            
            media_messages = []
            for msg in messages:
                body = msg.get('body', '')
                
                # Check for media indicators
                has_media = (
                    '<Media omitted>' in body or
                    '<attached:' in body.lower() or
                    'image' in body.lower() or
                    'video' in body.lower() or
                    'audio' in body.lower() or
                    'document' in body.lower()
                )
                
                if has_media:
                    # Try to determine media type
                    detected_type = "unknown"
                    if 'image' in body.lower() or '.jpg' in body.lower() or '.png' in body.lower():
                        detected_type = "image"
                    elif 'video' in body.lower() or '.mp4' in body.lower():
                        detected_type = "video"
                    elif 'audio' in body.lower() or '.mp3' in body.lower():
                        detected_type = "audio"
                    elif 'document' in body.lower() or '.pdf' in body.lower():
                        detected_type = "document"
                    
                    # Filter by type if specified
                    if media_type is None or detected_type == media_type:
                        media_messages.append({
                            **msg,
                            "media_type": detected_type
                        })
            
            result = {
                "status": "success",
                "chat_name": chat_name,
                "media_type_filter": media_type,
                "total_media_messages": len(media_messages),
                "messages": media_messages
            }
            
            logger.info(f"Found {len(media_messages)} media messages in {chat_name}")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to get media references: {e}")
            return self._error_response(str(e))
    
    def _error_response(self, message: str) -> str:
        """Create standardized error response."""
        return json.dumps({
            "status": "error",
            "message": message
        }, ensure_ascii=False, indent=2)
