"""Context Tools - L4 User Profile Integration

Simplified context tools for new L4 architecture.
All methods proxy to L4UserProfile's context API.
"""

import json
from typing import Any, Dict, List, Optional
from layers.L4 import L4UserProfile
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ContextTools:
    """Context management tools integrated with L4UserProfile."""

    def __init__(self, l4: L4UserProfile) -> None:
        self.l4 = l4

    def create_context(
        self,
        title: str,
        content: str,
        type: str = "knowledge",
        tags: Optional[List[str]] = None,
        description: str = ""
    ) -> str:
        """Create a new context (Knowledge/Plan/Memory)."""
        try:
            # Handle potential list parsing if passed as string
            if tags and isinstance(tags, str):
                tags = [tags]
                
            context_id = self.l4.create_context(
                title=title,
                content=content,
                type=type,
                tags=tags or [],
                description=description
            )
            
            return json.dumps({
                "status": "success",
                "message": f"Context created: {title}",
                "context_id": context_id
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def read_context(self, context_id_or_title: str) -> str:
        """
        Retrieves full details and content of a context.
        """
        try:
            data = self.l4.read_context(context_id_or_title)
            if data:
                return json.dumps({
                    "status": "success",
                    "context": data
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    "status": "error", 
                    "message": "Context not found."
                }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def update_context(
        self,
        context_id: str,
        content_append: str = None,
        description: str = None,
        status: str = None,
        tags: List[str] = None
    ) -> str:
        """Update an existing context."""
        try:
            updates = {}
            if content_append: updates["append_content"] = content_append
            if description: updates["description"] = description
            if status: updates["status"] = status
            if tags: updates["tags"] = tags
            
            success = self.l4.update_context(context_id, updates)
            if success:
                return json.dumps({"status": "success", "message": "Context updated."}, ensure_ascii=False)
            return json.dumps({"status": "error", "message": "Context not found."}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def delete_context(self, context_id: str) -> str:
        """Delete a context."""
        try:
            success = self.l4.delete_context(context_id)
            if success:
                return json.dumps({"status": "success", "message": "Context deleted."}, ensure_ascii=False)
            return json.dumps({"status": "error", "message": "Context not found."}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def link_to_calendar(self, context_id: str, event_id: str) -> str:
        """Link a context to a calendar event."""
        try:
            success = self.l4.link_to_calendar(context_id, event_id)
            if success:
                return json.dumps({"status": "success", "message": "Linked to calendar."}, ensure_ascii=False)
            return json.dumps({"status": "error", "message": "Context not found."}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def add_behavioral_directive(self, directive: str) -> str:
        """Add a new behavioral directive to the user profile."""
        try:
            success = self.l4.add_behavioral_directive(directive)
            if success:
                return json.dumps({
                    "status": "success", 
                    "message": f"Directive added: {directive}"
                }, ensure_ascii=False)
            return json.dumps({
                "status": "warning", 
                "message": "Directive already exists."
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)
            
    def context_tools_open(self) -> str:
        """
        Returns a list of available context headers for the model.
        """
        try:
            headers = self.l4.get_contexts_headers()
            # Convert to string representation
            result = "=== AVAILABLE CONTEXTS ===\n"
            if not headers:
                result += "(No active contexts found)"
            else:
                for h in headers:
                    result += f"[{h['id']}] {h['title']} ({h['type']}): {h['description']}\n"
            
            result += "\nUse 'read_context(id)' to view full content."
            return json.dumps({
                "status": "success",
                "context_list": result
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)