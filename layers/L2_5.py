"""
L2.5: Keyword-Indexed Search Layer.

Fast search interface for L2 archive. When sessions are archived to L2,
they are also indexed with keywords and summaries for quick retrieval.

L2.5 is continuously active and searches on every message to find relevant
past sessions. If detailed information is needed, it retrieves from L2.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4
import json
import os


@dataclass
class SessionSummary:
    """Summary entry for fast search in L2.5."""
    
    session_id: str
    created_at: datetime
    summary: str  # One paragraph summary
    keywords: list[str]  # Up to 10 keywords/keyword groups
    message_count: int
    indexed_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["indexed_at"] = self.indexed_at.isoformat()
        return data


class L2_5:
    """
    Keyword-Indexed Search Layer.
    
    Maintains searchable summaries and keywords for all archived sessions.
    Continuously active - searches on every message to find relevant context.
    
    Attributes:
        data_file: Path to L2.5.json storage
        summaries: Dictionary mapping session_id to summary data
    """
    
    def __init__(self, data_dir: Optional[str] = None) -> None:
        """
        Initialize L2.5 search layer.
        
        Args:
            data_dir: Optional custom data directory. Defaults to layers/data/
        """
        if data_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(script_dir, "data")
        
        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, "L2.5.json")
        
        self._ensure_data_directory()
        self._ensure_data_file()
        self.summaries: dict[str, dict[str, Any]] = {}
        self._load_all_summaries()
    
    def _ensure_data_directory(self) -> None:
        """Ensure data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _ensure_data_file(self) -> None:
        """Ensure L2.5.json exists with proper structure."""
        if not os.path.exists(self.data_file):
            initial_data = {
                "search_index": {
                    "summaries": [],
                    "total_summaries": 0,
                    "summary_index": {}
                },
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "last_updated": None,
                    "version": "2.5"
                }
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
    
    def _load_all_summaries(self) -> None:
        """Load all summaries from L2.5.json into memory."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for summary_data in data.get("search_index", {}).get("summaries", []):
                session_id = summary_data.get("session_id")
                if session_id:
                    self.summaries[session_id] = summary_data
        except Exception as e:
            print(f"Error loading L2.5 summaries: {e}")
    
    def add_summary(
        self,
        session_id: str,
        created_at: datetime,
        summary: str,
        keywords: list[str],
        message_count: int
    ) -> bool:
        """
        Add a session summary to the search index.
        
        Args:
            session_id: The session ID
            created_at: When the session was created
            summary: One paragraph summary of the session
            keywords: List of up to 10 keywords/keyword groups
            message_count: Number of messages in the session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Limit keywords to 10
            keywords = keywords[:10]
            
            summary_entry = {
                "session_id": session_id,
                "created_at": created_at.isoformat(),
                "summary": summary,
                "keywords": keywords,
                "message_count": message_count,
                "indexed_at": datetime.utcnow().isoformat()
            }
            
            # Load current index
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Add summary to index
            data["search_index"]["summaries"].append(summary_entry)
            data["search_index"]["total_summaries"] += 1
            summary_index = len(data["search_index"]["summaries"]) - 1
            data["search_index"]["summary_index"][session_id] = summary_index
            data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
            
            # Save updated index
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Update in-memory cache
            self.summaries[session_id] = summary_entry
            
            return True
        except Exception as e:
            print(f"Error adding summary to L2.5: {e}")
            return False
    
    def search_by_keywords(
        self,
        query_keywords: list[str],
        max_results: int = 5
    ) -> list[dict[str, Any]]:
        """
        Search for sessions by keywords.
        
        Args:
            query_keywords: List of keywords to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of matching sessions with relevance scores
        """
        scored_results = []
        query_keywords_lower = [kw.lower() for kw in query_keywords]
        
        for session_id, summary_data in self.summaries.items():
            score = 0
            
            # Score based on keyword matches
            for keyword in summary_data.get("keywords", []):
                keyword_lower = keyword.lower()
                for query_kw in query_keywords_lower:
                    if query_kw in keyword_lower or keyword_lower in query_kw:
                        score += 2
            
            # Score based on summary text matches
            summary_lower = summary_data.get("summary", "").lower()
            for query_kw in query_keywords_lower:
                if query_kw in summary_lower:
                    score += 1
            
            if score > 0:
                scored_results.append({
                    "session_id": session_id,
                    "summary_data": summary_data,
                    "relevance_score": score
                })
        
        # Sort by relevance and return top results
        scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_results[:max_results]
    
    def search_by_text(
        self,
        query_text: str,
        max_results: int = 5
    ) -> list[dict[str, Any]]:
        """
        Search for sessions by free-form text query.
        
        Args:
            query_text: Free-form search text
            max_results: Maximum number of results to return
            
        Returns:
            List of matching sessions with relevance scores
        """
        # Extract keywords from query text
        query_keywords = query_text.lower().split()
        return self.search_by_keywords(query_keywords, max_results)
    
    def get_summary_by_session_id(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Get summary for a specific session.
        
        Args:
            session_id: The session ID
            
        Returns:
            Summary data if found, None otherwise
        """
        return self.summaries.get(session_id)
    
    def get_all_keywords(self) -> list[str]:
        """
        Get all unique keywords across all sessions.
        
        Returns:
            List of unique keywords
        """
        all_keywords = set()
        
        for summary_data in self.summaries.values():
            for keyword in summary_data.get("keywords", []):
                all_keywords.add(keyword)
        
        return sorted(list(all_keywords))
    
    def get_search_statistics(self) -> dict[str, Any]:
        """
        Get statistics about the search index.
        
        Returns:
            Dictionary with search index statistics
        """
        all_keywords = self.get_all_keywords()
        
        return {
            "total_summaries": len(self.summaries),
            "unique_keywords": len(all_keywords),
            "total_keywords": sum(
                len(s.get("keywords", [])) for s in self.summaries.values()
            ),
            "average_keywords_per_session": (
                sum(len(s.get("keywords", [])) for s in self.summaries.values()) / len(self.summaries)
                if self.summaries else 0
            )
        }
    
    def get_recent_sessions(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get most recently indexed sessions.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of recent sessions sorted by indexed_at
        """
        sorted_summaries = sorted(
            self.summaries.values(),
            key=lambda x: x.get("indexed_at", ""),
            reverse=True
        )
        return sorted_summaries[:limit]
