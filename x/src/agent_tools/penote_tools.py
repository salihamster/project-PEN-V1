"""PENote-Specific Tools for PEN Agent.

These tools are ONLY available when chatting from the PENote interface.
They provide context-aware access to the note editor state and allow
the agent to interact with the user's current editing session.
"""

import json
from typing import Dict, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PENoteTools:
    """Tools specific to PENote chat interface."""
    
    def __init__(self):
        # This will be populated by the web server with real-time editor state
        self._editor_state: Optional[Dict[str, Any]] = None
    
    def set_editor_state(self, state: Dict[str, Any]):
        """Update the current editor state (called by web server)."""
        self._editor_state = state
        
        # Safe logging
        path = "No file"
        if state and isinstance(state, dict):
            current_file = state.get("current_file")
            if current_file and isinstance(current_file, dict):
                path = current_file.get("path", "No file")
        
        logger.info(f"PENote editor state updated: {path}")
    
    def penote_get_editor_state(self) -> str:
        """
        Get the current state of the PENote editor.
        
        Returns information about:
        - Currently open file (if any)
        - Saved vs unsaved content
        - Word count, last saved time
        - Whether there are unsaved changes
        
        This is automatically called on the first message in PENote chat.
        """
        try:
            if not self._editor_state:
                return json.dumps({
                    "status": "no_file_open",
                    "message": "No file is currently open in the editor."
                }, ensure_ascii=False)
            
            current_file = self._editor_state.get("current_file", {})
            
            if not current_file or not current_file.get("path"):
                return json.dumps({
                    "status": "no_file_open",
                    "message": "No file is currently open in the editor."
                }, ensure_ascii=False)
            
            # Build response
            response = {
                "status": "file_open",
                "file": {
                    "path": current_file.get("path"),
                    "title": current_file.get("title"),
                    "word_count": current_file.get("word_count", 0),
                    "last_saved": current_file.get("last_saved"),
                    "has_unsaved_changes": current_file.get("has_unsaved_changes", False)
                }
            }
            
            # Add content info
            saved_content = current_file.get("saved_content", "")
            current_content = current_file.get("current_content", "")
            
            if current_file.get("has_unsaved_changes"):
                response["unsaved_changes"] = {
                    "saved_length": len(saved_content),
                    "current_length": len(current_content),
                    "diff_chars": len(current_content) - len(saved_content)
                }
                
                # Provide a preview of unsaved content (first 500 chars)
                if current_content:
                    response["current_content_preview"] = current_content[:500]
            else:
                # No unsaved changes, provide saved content preview
                if saved_content:
                    response["saved_content_preview"] = saved_content[:500]
            
            return json.dumps(response, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting editor state: {e}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Failed to get editor state: {str(e)}"
            }, ensure_ascii=False)
    
    def penote_get_active_file(self) -> str:
        """
        Get the path and basic info of the currently active file.
        
        Lighter version of penote_get_editor_state - just returns the file path
        and whether it has unsaved changes.
        """
        try:
            if not self._editor_state:
                return json.dumps({
                    "active_file": None,
                    "message": "No file is currently open."
                }, ensure_ascii=False)
            
            current_file = self._editor_state.get("current_file", {})
            
            if not current_file or not current_file.get("path"):
                return json.dumps({
                    "active_file": None,
                    "message": "No file is currently open."
                }, ensure_ascii=False)
            
            return json.dumps({
                "active_file": {
                    "path": current_file.get("path"),
                    "title": current_file.get("title"),
                    "has_unsaved_changes": current_file.get("has_unsaved_changes", False)
                }
            }, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error getting active file: {e}", exc_info=True)
            return json.dumps({
                "active_file": None,
                "error": str(e)
            }, ensure_ascii=False)
    
    def penote_open_file(self, path: str) -> str:
        """
        Request to open a file in the user's PENote editor.
        
        This sends a command to the frontend to open the specified file.
        The file must exist in the workspace (data/user_docs).
        
        Args:
            path: Relative path to the file (e.g., "projects/aliye/plan.md")
        
        Returns:
            JSON response indicating success or failure
        """
        try:
            # Validate path
            if not path or ".." in path:
                return json.dumps({
                    "status": "error",
                    "message": "Invalid file path"
                }, ensure_ascii=False)
            
            # This will be handled by the web server to send a command to frontend
            return json.dumps({
                "status": "success",
                "action": "open_file",
                "path": path,
                "message": f"Opening {path} in editor..."
            }, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error opening file: {e}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Failed to open file: {str(e)}"
            }, ensure_ascii=False)

    def penote_edit_document(self, old_text: str, new_text: str) -> str:
        """
        Edits the CURRENTLY OPEN document in PENote with visual animation.
        
        Args:
            old_text: The exact text to find and replace.
            new_text: The new text to insert.
            
        Returns:
            JSON with client action instructions.
        """
        try:
            if not self._editor_state:
                return json.dumps({
                    "status": "error",
                    "message": "No document is currently open for editing."
                }, ensure_ascii=False)

            # Return a special client action that the frontend will intercept
            return json.dumps({
                "status": "success",
                "client_action": "animate_edit",
                "old_text": old_text,
                "new_text": new_text,
                "message": "Sending edit command to editor..."
            }, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error editing document: {e}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Failed to perform edit: {str(e)}"
            }, ensure_ascii=False)
