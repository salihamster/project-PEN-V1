"""
L2: Historical Archive Layer.

Stores archived sessions from L1. When a session ends (sleep cycle initiated),
L1 data is archived to L2 as complete, immutable records.

L2 is accessed via tools only - not directly by the agent during normal operation.
L2.5 provides the search interface for L2 data.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4
import json
import os


@dataclass
class ArchivedSession:
    """Represents a complete archived session."""
    
    session_id: str
    created_at: datetime
    archived_at: datetime
    messages: list[dict[str, Any]]
    tool_interactions: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["archived_at"] = self.archived_at.isoformat()
        return data


class L2:
    """
    Historical Archive Layer.
    
    Stores complete archived sessions. Each session is immutable once archived.
    Provides methods to retrieve full session data by session_id.
    
    Attributes:
        data_file: Path to L2.json storage
        sessions: Dictionary mapping session_id to archived session data
    """
    
    def __init__(self, data_dir: Optional[str] = None) -> None:
        """
        Initialize L2 archive.
        
        Args:
            data_dir: Optional custom data directory. Defaults to layers/data/
        """
        if data_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(script_dir, "data")
        
        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, "L2.json")
        
        self._ensure_data_directory()
        self._ensure_data_file()
        self.sessions: dict[str, dict[str, Any]] = {}
        self._load_all_sessions()
    
    def _ensure_data_directory(self) -> None:
        """Ensure data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _ensure_data_file(self) -> None:
        """Ensure L2.json exists with proper structure."""
        if not os.path.exists(self.data_file):
            initial_data = {
                "archive": {
                    "sessions": [],
                    "total_sessions": 0,
                    "session_index": {}
                },
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "last_updated": None,
                    "version": "2.0"
                }
            }

            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
        else:
            # Normalize existing file
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                normalized = self._normalize_data(data)
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(normalized, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Error normalizing L2.json: {e}")
                # Recreate file
                initial_data = {
                    "archive": {
                        "sessions": [],
                        "total_sessions": 0,
                        "session_index": {}
                    },
                    "metadata": {
                        "created_at": datetime.utcnow().isoformat(),
                        "last_updated": None,
                        "version": "2.0"
                    }
                }
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, ensure_ascii=False, indent=2)

    def _normalize_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Ensure data structure matches expected schema."""
        if "archive" not in data or not isinstance(data["archive"], dict):
            data["archive"] = {
                "sessions": [],
                "total_sessions": 0,
                "session_index": {}
            }
        archive = data["archive"]
        if "sessions" not in archive or not isinstance(archive["sessions"], list):
            archive["sessions"] = []
        if "total_sessions" not in archive or not isinstance(archive["total_sessions"], int):
            archive["total_sessions"] = len(archive["sessions"])
        if "session_index" not in archive or not isinstance(archive["session_index"], dict):
            archive["session_index"] = {}
        data["archive"] = archive

        if "metadata" not in data or not isinstance(data["metadata"], dict):
            data["metadata"] = {}
        metadata = data["metadata"]
        metadata.setdefault("created_at", datetime.utcnow().isoformat())
        metadata.setdefault("last_updated", None)
        metadata.setdefault("version", "2.0")
        data["metadata"] = metadata

        return data
    
    def _load_all_sessions(self) -> None:
        """Load all sessions from L2.json into memory."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for session_data in data.get("archive", {}).get("sessions", []):
                session_id = session_data.get("session_id")
                if session_id:
                    self.sessions[session_id] = session_data
        except Exception as e:
            print(f"Error loading L2 sessions: {e}")
    
    def archive_session(
        self,
        l1_session_context: dict[str, Any],
        summary: str = "",
        keywords: list[str] = None
    ) -> bool:
        """
        Archive a completed L1 session to L2.
        
        Args:
            l1_session_context: Complete session context from L1.get_session_context()
            summary: Session summary (from sleep cycle)
            keywords: Session keywords (from sleep cycle)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_id = l1_session_context.get("session_id")
            if not session_id:
                print("Error: No session_id in L1 context")
                return False
            
            if keywords is None:
                keywords = []
            
            # Create archived session entry
            archived_session = {
                "session_id": session_id,
                "created_at": l1_session_context.get("metadata", {}).get("created_at"),
                "archived_at": datetime.utcnow().isoformat(),
                "messages": l1_session_context.get("messages", []),
                "tool_interactions": l1_session_context.get("tool_interactions", []),
                "metadata": {
                    "message_count": len(l1_session_context.get("messages", [])),
                    "tool_call_count": len(l1_session_context.get("tool_interactions", [])),
                    "summary": summary,
                    "keywords": keywords
                }
            }
            
            # Load current archive
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Add session to archive
            data["archive"]["sessions"].append(archived_session)
            data["archive"]["total_sessions"] += 1
            session_index = len(data["archive"]["sessions"]) - 1
            data["archive"]["session_index"][session_id] = session_index
            data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
            
            # Save updated archive
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Update in-memory cache
            self.sessions[session_id] = archived_session
            
            return True
        except Exception as e:
            print(f"Error archiving session to L2: {e}")
            return False
    
    def get_session_by_id(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieve a complete archived session by session_id.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            Session data if found, None otherwise
        """
        return self.sessions.get(session_id)
    
    def get_session_messages(self, session_id: str) -> list[dict[str, Any]]:
        """
        Get all messages from a specific session.
        
        Args:
            session_id: The session ID
            
        Returns:
            List of messages, empty list if session not found
        """
        session = self.get_session_by_id(session_id)
        if session:
            return session.get("messages", [])
        return []
    
    def get_session_tool_interactions(self, session_id: str) -> list[dict[str, Any]]:
        """
        Get all tool interactions from a specific session.
        
        Args:
            session_id: The session ID
            
        Returns:
            List of tool interactions, empty list if session not found
        """
        session = self.get_session_by_id(session_id)
        if session:
            return session.get("tool_interactions", [])
        return []
    
    def get_all_session_ids(self) -> list[str]:
        """
        Get list of all archived session IDs.
        
        Returns:
            List of session IDs
        """
        return list(self.sessions.keys())
    
    def get_session_count(self) -> int:
        """
        Get total number of archived sessions.
        
        Returns:
            Number of sessions
        """
        return len(self.sessions)
    
    def search_sessions_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> list[dict[str, Any]]:
        """
        Find sessions within a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of sessions within the date range
        """
        results = []
        
        for session in self.sessions.values():
            try:
                created_at = datetime.fromisoformat(session.get("created_at", ""))
                if start_date <= created_at <= end_date:
                    results.append(session)
            except (ValueError, TypeError):
                continue
        
        return sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def get_archive_statistics(self) -> dict[str, Any]:
        """
        Get statistics about the archive.
        
        Returns:
            Dictionary with archive statistics
        """
        total_messages = 0
        total_tool_calls = 0
        
        for session in self.sessions.values():
            total_messages += len(session.get("messages", []))
            total_tool_calls += len(session.get("tool_interactions", []))
        
        return {
            "total_sessions": len(self.sessions),
            "total_messages": total_messages,
            "total_tool_calls": total_tool_calls,
            "average_messages_per_session": (
                total_messages / len(self.sessions) if self.sessions else 0
            )
        }
