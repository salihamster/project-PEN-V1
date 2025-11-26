"""
Sleep Cycle Manager.

Handles the transition from L1 (active session) to L2 (archive) and L2.5 (search index).
Triggered when session ends or reaches a threshold.

Process:
1. Get complete session context from L1
2. Generate summary and keywords using Gemini
3. Archive to L2 (with summary/keywords)
4. Index in L2.5 (with same summary/keywords)
5. Clear L1 for new session
"""

from datetime import datetime
from typing import Any, Optional
import json
import google.generativeai as genai

from layers.L1 import L1
from layers.L2 import L2
from layers.L2_5 import L2_5
from src.config import GEMINI_API_KEY


class SleepCycleManager:
    """
    Manages the sleep cycle - archival of L1 sessions to L2 and L2.5.
    
    Attributes:
        l1: L1 active session layer
        l2: L2 archive layer
        l2_5: L2.5 search index layer
        gemini_model: Gemini model for summarization
    """
    
    def __init__(self, l1: Optional[L1] = None, l2: Optional[L2] = None, l2_5: Optional[L2_5] = None) -> None:
        """
        Initialize sleep cycle manager with Gemini.
        
        Args:
            l1: Optional L1 instance (if None, creates new one)
            l2: Optional L2 instance (if None, creates new one)
            l2_5: Optional L2.5 instance (if None, creates new one)
        """
        self.l1 = l1 if l1 is not None else L1()
        self.l2 = l2 if l2 is not None else L2()
        self.l2_5 = l2_5 if l2_5 is not None else L2_5()
        
        # Initialize Gemini
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            print("Warning: GEMINI_API_KEY not found. Sleep cycle summarization will be disabled.")
            self.gemini_model = None
    
    def run_sleep_cycle(self) -> dict[str, Any]:
        """
        Execute the complete sleep cycle.
        
        Returns:
            Dictionary with status and details
        """
        try:
            # Step 1: Get session context from L1
            session_context = self.l1.get_session_context()
            session_id = session_context.get("session_id")
            
            if not session_id:
                return {
                    "status": "error",
                    "message": "No active session to archive",
                    "details": {}
                }
            
            # Step 2: Generate summary and keywords FIRST
            summary_result = self._generate_session_summary(session_context)
            if not summary_result:
                return {
                    "status": "error",
                    "message": "Failed to generate session summary",
                    "details": {"session_id": session_id}
                }
            
            summary_text = summary_result.get("summary", "")
            keywords = summary_result.get("keywords", [])
            
            # Step 3: Archive to L2 WITH summary and keywords
            archive_success = self.l2.archive_session(
                session_context,
                summary=summary_text,
                keywords=keywords
            )
            if not archive_success:
                return {
                    "status": "error",
                    "message": "Failed to archive session to L2",
                    "details": {"session_id": session_id}
                }
            
            # Step 4: Index in L2.5 with SAME summary and keywords
            created_at = datetime.fromisoformat(
                session_context.get("metadata", {}).get("created_at", datetime.utcnow().isoformat())
            )
            message_count = len(session_context.get("messages", []))
            
            index_success = self.l2_5.add_summary(
                session_id=session_id,
                created_at=created_at,
                summary=summary_text,
                keywords=keywords,
                message_count=message_count
            )
            
            if not index_success:
                return {
                    "status": "error",
                    "message": "Failed to index session in L2.5",
                    "details": {"session_id": session_id}
                }
            
            # Step 5: Clear L1 for new session
            self.l1.clear_session()
            
            return {
                "status": "success",
                "message": "Sleep cycle completed successfully",
                "details": {
                    "session_id": session_id,
                    "message_count": message_count,
                    "keywords_count": len(keywords),
                    "archived_at": datetime.utcnow().isoformat()
                }
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Sleep cycle failed: {str(e)}",
                "details": {}
            }
    
    def _generate_session_summary(
        self,
        session_context: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """
        Generate summary and keywords for a session using Gemini.
        
        Args:
            session_context: Complete session context from L1
            
        Returns:
            Dictionary with 'summary' and 'keywords' keys, or None if failed
        """
        try:
            if not self.gemini_model:
                print("Gemini model not available, using fallback summary")
                return {
                    "summary": "Session archived (no LLM available)",
                    "keywords": ["session", "archived"]
                }
            
            messages = session_context.get("messages", [])
            if not messages:
                return {
                    "summary": "Empty session",
                    "keywords": []
                }
            
            # Build conversation text
            conversation_text = ""
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conversation_text += f"{role.upper()}: {content}\n"
            
            # Create summarization prompt
            prompt = f"""You are L2.5 Summarizer, part of Penelope's memory system.
Your task is to create a concise summary and extract keywords from a conversation session.

OUTPUT FORMAT (strictly follow):
SUMMARY: [One paragraph summary of the session]
KEYWORDS: [Comma-separated list of up to 10 keywords/keyword groups]

Focus on:
- Main topics discussed
- Key decisions or conclusions
- Important information for future reference
- Searchable terms users might use to find this session

Keep the summary to 2-3 sentences maximum.
Keep keywords concise and searchable.

SESSION TO SUMMARIZE:
Session ID: {session_context.get('session_id', 'unknown')}
Message Count: {len(messages)}

CONVERSATION:
{conversation_text}

Provide summary and keywords:"""
            
            # Call Gemini
            response = self.gemini_model.generate_content(prompt)
            result_text = response.text
            
            # Parse response
            summary = ""
            keywords = []
            
            lines = result_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith("SUMMARY:"):
                    summary = line.replace("SUMMARY:", "").strip()
                elif line.startswith("KEYWORDS:"):
                    keywords_str = line.replace("KEYWORDS:", "").strip()
                    keywords = [kw.strip() for kw in keywords_str.split(",")]
            
            return {
                "summary": summary or "Session archived",
                "keywords": keywords[:10]  # Limit to 10 keywords
            }
        
        except Exception as e:
            print(f"Error generating session summary: {e}")
            return None
