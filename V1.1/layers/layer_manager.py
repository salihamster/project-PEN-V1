"""
Layer Manager.

Coordinates all memory layers (L1, L2, L2.5, L4) and provides a unified interface
for the agent to interact with the memory system.

Responsibilities:
- Route queries to appropriate layers
- Manage layer interactions
- Handle sleep cycles
- Provide memory context to the agent
"""

from typing import Any, Optional
from datetime import datetime

from layers.L1 import L1, MessageRole
from layers.L2 import L2
from layers.L2_5 import L2_5
from layers.L4 import L4UserProfile
from layers.sleep_cycle_manager import SleepCycleManager


class LayerManager:
    """
    Unified interface for the layered memory system.
    
    Attributes:
        l1: Active session layer
        l2: Archive layer
        l2_5: Search index layer
        l4: User profile layer
        sleep_manager: Sleep cycle manager
    """
    
    def __init__(self) -> None:
        """Initialize layer manager with all layers."""
        self.l1 = L1()
        self.l2 = L2()
        self.l2_5 = L2_5()
        self.l4 = L4UserProfile()
        # Pass layer instances to sleep manager so they share the same state
        self.sleep_manager = SleepCycleManager(l1=self.l1, l2=self.l2, l2_5=self.l2_5)
    
    # ==================== L1 Operations ====================
    
    def add_user_message(self, content: str) -> bool:
        """
        Add a user message to L1.
        
        Args:
            content: User message content
            
        Returns:
            True if successful
        """
        try:
            self.l1.add_message(MessageRole.USER, content)
            return True
        except Exception as e:
            print(f"Error adding user message: {e}")
            return False
    
    def add_assistant_message(self, content: str) -> bool:
        """
        Add an assistant message to L1.
        
        Args:
            content: Assistant message content
            
        Returns:
            True if successful
        """
        try:
            self.l1.add_message(MessageRole.ASSISTANT, content)
            return True
        except Exception as e:
            print(f"Error adding assistant message: {e}")
            return False
    
    def add_tool_call(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: Any,
        execution_time_ms: Optional[float] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        Record a tool call in L1.
        
        Args:
            tool_name: Name of the tool
            tool_input: Input to the tool
            tool_output: Output from the tool
            execution_time_ms: Execution time in milliseconds
            error: Error message if tool failed
            
        Returns:
            True if successful
        """
        try:
            self.l1.add_tool_interaction(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                execution_time_ms=execution_time_ms,
                error=error
            )
            return True
        except Exception as e:
            print(f"Error recording tool call: {e}")
            return False
    
    def get_session_context(self) -> str:
        """
        Get formatted context for the current session.
        
        Returns:
            Formatted session context string
        """
        try:
            messages = self.l1.get_all_messages()
            
            if not messages:
                return "No messages in current session."
            
            context = "Current Session Context:\n"
            context += f"Session ID: {self.l1.session_metadata.session_id}\n"
            context += f"Messages: {len(messages)}\n"
            context += f"Tool Calls: {len(self.l1.tool_interactions)}\n\n"
            
            context += "Recent Messages:\n"
            for msg in messages[-10:]:  # Last 10 messages
                role = msg.get("role", "unknown").upper()
                content = msg.get("content", "")[:100]  # First 100 chars
                context += f"[{role}] {content}...\n"
            
            return context
        except Exception as e:
            print(f"Error getting session context: {e}")
            return "Error retrieving session context"
    
    # ==================== L2.5 Search Operations ====================
    
    def search_memory(
        self,
        query: str,
        max_results: int = 5
    ) -> list[dict[str, Any]]:
        """
        Search historical sessions using L2.5.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of matching sessions with summaries
        """
        try:
            results = self.l2_5.search_by_text(query, max_results)
            
            formatted_results = []
            for result in results:
                summary_data = result.get("summary_data", {})
                formatted_results.append({
                    "session_id": result.get("session_id"),
                    "summary": summary_data.get("summary", ""),
                    "keywords": summary_data.get("keywords", []),
                    "message_count": summary_data.get("message_count", 0),
                    "created_at": summary_data.get("created_at", ""),
                    "relevance_score": result.get("relevance_score", 0)
                })
            
            return formatted_results
        except Exception as e:
            print(f"Error searching memory: {e}")
            return []
    
    def get_detailed_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Get detailed information about a specific archived session from L2.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            Complete session data or None if not found
        """
        try:
            return self.l2.get_session_by_id(session_id)
        except Exception as e:
            print(f"Error retrieving detailed session: {e}")
            return None
    
    # ==================== Sleep Cycle Operations ====================
    
    def trigger_sleep_cycle(self) -> dict[str, Any]:
        """
        Trigger the sleep cycle to archive current session.
        
        Returns:
            Status dictionary with details
        """
        try:
            return self.sleep_manager.run_sleep_cycle()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Sleep cycle failed: {str(e)}",
                "details": {}
            }
    
    # ==================== Statistics and Monitoring ====================
    
    def get_memory_statistics(self) -> dict[str, Any]:
        """
        Get statistics about the entire memory system.
        
        Returns:
            Dictionary with memory statistics
        """
        try:
            l1_summary = self.l1.get_session_summary()
            l2_stats = self.l2.get_archive_statistics()
            l2_5_stats = self.l2_5.get_search_statistics()
            
            return {
                "l1_active_session": {
                    "session_id": self.l1.session_metadata.session_id,
                    "message_count": l1_summary.get("message_count", 0),
                    "tool_call_count": l1_summary.get("tool_interaction_count", 0),
                    "duration_seconds": l1_summary.get("session_duration_seconds", 0)
                },
                "l2_archive": l2_stats,
                "l2_5_search_index": l2_5_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error getting memory statistics: {e}")
            return {}
    
    def get_memory_health(self) -> dict[str, Any]:
        """
        Check the health of the memory system.
        
        Returns:
            Dictionary with health status
        """
        try:
            stats = self.get_memory_statistics()
            
            l1_messages = stats.get("l1_active_session", {}).get("message_count", 0)
            l2_sessions = stats.get("l2_archive", {}).get("total_sessions", 0)
            l2_5_summaries = stats.get("l2_5_search_index", {}).get("total_summaries", 0)
            
            health = {
                "status": "healthy",
                "checks": {
                    "l1_active": l1_messages >= 0,
                    "l2_archive": l2_sessions >= 0,
                    "l2_5_index": l2_5_summaries >= 0,
                    "l2_l2_5_sync": l2_sessions == l2_5_summaries
                },
                "warnings": []
            }
            
            # Check for warnings
            if l1_messages > 100:
                health["warnings"].append(
                    f"L1 has {l1_messages} messages - consider triggering sleep cycle"
                )
            
            if not health["checks"]["l2_l2_5_sync"]:
                health["warnings"].append(
                    f"L2 and L2.5 out of sync: {l2_sessions} vs {l2_5_summaries}"
                )
            
            if health["warnings"]:
                health["status"] = "warning"
            
            return health
        except Exception as e:
            print(f"Error checking memory health: {e}")
            return {"status": "error", "message": str(e)}
