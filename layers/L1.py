"""
L1: Active Session-Based Memory Layer.

Manages the current session's memory. All messages, tool outputs, and interactions
accumulate here during the session. This is the primary working memory.

Session lifecycle:
- Created when session starts
- Accumulates all interactions
- Archived to L2 when session ends (sleep initiated)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4
import json
import os


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class InteractionType(str, Enum):
    """Type of interaction in the session."""
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    TOOL_OUTPUT = "tool_output"
    SYSTEM_EVENT = "system_event"


@dataclass
class Message:
    """Represents a single message in the session."""
    
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "metadata": self.metadata,
        }


@dataclass
class ToolInteraction:
    """Represents a tool call and its output."""
    
    tool_name: str
    tool_input: dict[str, Any]
    tool_output: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    interaction_id: str = field(default_factory=lambda: str(uuid4()))
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert tool interaction to dictionary for serialization."""
        # Ensure tool_output is JSON-serializable
        tool_output = self.tool_output
        try:
            # Try to serialize directly
            json.dumps(tool_output)
        except (TypeError, ValueError):
            # If it fails, convert to string
            tool_output = str(tool_output)
        
        # Ensure tool_input is also JSON-serializable
        tool_input = self.tool_input
        try:
            json.dumps(tool_input)
        except (TypeError, ValueError):
            # Convert complex objects to strings
            tool_input = {k: str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v 
                         for k, v in tool_input.items()} if isinstance(tool_input, dict) else str(tool_input)
        
        return {
            "tool_name": self.tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output,
            "timestamp": self.timestamp.isoformat(),
            "interaction_id": self.interaction_id,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
        }


@dataclass
class SessionMetadata:
    """Metadata for the current session."""
    
    session_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    tool_call_count: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": self.message_count,
            "tool_call_count": self.tool_call_count,
        }


class L1:
    """
    Active Session Memory Layer.
    
    Maintains all interactions during the current session. No summarization,
    no archival - just accumulation of all data. Model has 1M context window,
    so 100 messages is not a problem.
    
    Attributes:
        session_metadata: Session information
        messages: List of all messages in session
        tool_interactions: List of all tool calls and outputs
        data_file: Path to L1.json storage
    """
    
    def __init__(self, data_dir: Optional[str] = None) -> None:
        """
        Initialize L1 session memory.
        
        Auto-loads from L1.json if exists, otherwise starts fresh.
        
        Args:
            data_dir: Optional custom data directory. Defaults to layers/data/
        """
        if data_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(script_dir, "data")
        
        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, "L1.json")
        
        self._ensure_data_directory()
        
        # Try to load existing session from disk
        if os.path.exists(self.data_file):
            loaded = self.load_from_file()
            if not loaded:
                # If load failed, start fresh
                self.session_metadata = SessionMetadata()
                self.messages: list[Message] = []
                self.tool_interactions: list[ToolInteraction] = []
        else:
            # No existing file, start fresh
            self.session_metadata = SessionMetadata()
            self.messages: list[Message] = []
            self.tool_interactions: list[ToolInteraction] = []
            # Save initial state to disk
            self.save_to_file()
    
    def _ensure_data_directory(self) -> None:
        """Ensure data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> Message:
        """
        Add a message to the session.
        
        Args:
            role: Message role (user, assistant, system, tool)
            content: Message content
            metadata: Optional metadata dictionary
            
        Returns:
            The created Message object
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.session_metadata.message_count += 1
        self._update_last_activity()
        
        # Auto-save to disk after state change
        self.save_to_file()
        
        return message
    
    def add_tool_interaction(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: Any,
        execution_time_ms: Optional[float] = None,
        error: Optional[str] = None
    ) -> ToolInteraction:
        """
        Record a tool call and its output.
        
        Args:
            tool_name: Name of the tool
            tool_input: Input parameters to the tool
            tool_output: Output from the tool
            execution_time_ms: Execution time in milliseconds
            error: Error message if tool failed
            
        Returns:
            The created ToolInteraction object
        """
        interaction = ToolInteraction(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            execution_time_ms=execution_time_ms,
            error=error
        )
        self.tool_interactions.append(interaction)
        self.session_metadata.tool_call_count += 1
        self._update_last_activity()
        
        # Auto-save to disk after state change
        self.save_to_file()
        
        return interaction
    
    def get_session_summary(self) -> dict[str, Any]:
        """
        Get a summary of the current session.
        
        Returns:
            Dictionary containing session metadata and statistics
        """
        return {
            "metadata": self.session_metadata.to_dict(),
            "message_count": len(self.messages),
            "tool_interaction_count": len(self.tool_interactions),
            "session_duration_seconds": (
                datetime.utcnow() - self.session_metadata.created_at
            ).total_seconds()
        }
    
    def get_all_messages(self) -> list[dict[str, Any]]:
        """
        Get all messages in the session.
        
        Returns:
            List of message dictionaries
        """
        return [msg.to_dict() for msg in self.messages]
    
    def get_all_tool_interactions(self) -> list[dict[str, Any]]:
        """
        Get all tool interactions in the session.
        
        Returns:
            List of tool interaction dictionaries
        """
        result = []
        for interaction in self.tool_interactions:
            try:
                result.append(interaction.to_dict())
            except Exception as e:
                # If serialization fails, create a minimal dict
                print(f"Warning: Failed to serialize tool interaction {interaction.tool_name}: {e}")
                result.append({
                    "tool_name": interaction.tool_name,
                    "tool_input": str(interaction.tool_input),
                    "tool_output": str(interaction.tool_output),
                    "timestamp": interaction.timestamp.isoformat(),
                    "interaction_id": interaction.interaction_id,
                    "error": str(e)
                })
        return result
    
    def get_session_context(self) -> dict[str, Any]:
        """
        Get the complete session context for archival or processing.
        
        Returns:
            Complete session data including metadata, messages, and tool interactions
        """
        return {
            "session_id": self.session_metadata.session_id,
            "metadata": self.session_metadata.to_dict(),
            "messages": self.get_all_messages(),
            "tool_interactions": self.get_all_tool_interactions()
        }
    
    def save_to_file(self) -> bool:
        """
        Save current session to L1.json file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "session_id": self.session_metadata.session_id,
                "metadata": self.session_metadata.to_dict(),
                "messages": self.get_all_messages(),
                "tool_interactions": self.get_all_tool_interactions(),
                "saved_at": datetime.utcnow().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving L1 session to file: {e}")
            return False
    
    def load_from_file(self) -> bool:
        """
        Load session from L1.json file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.data_file):
                return False
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Restore session metadata
            metadata_dict = data.get("metadata", {})
            self.session_metadata = SessionMetadata(
                session_id=data.get("session_id", str(uuid4())),
                created_at=datetime.fromisoformat(metadata_dict.get("created_at", datetime.utcnow().isoformat())),
                last_activity=datetime.fromisoformat(metadata_dict.get("last_activity", datetime.utcnow().isoformat())),
                message_count=metadata_dict.get("message_count", 0),
                tool_call_count=metadata_dict.get("tool_call_count", 0)
            )
            
            # Restore messages
            self.messages = []
            for msg_dict in data.get("messages", []):
                message = Message(
                    role=MessageRole(msg_dict.get("role", "user")),
                    content=msg_dict.get("content", ""),
                    timestamp=datetime.fromisoformat(msg_dict.get("timestamp", datetime.utcnow().isoformat())),
                    message_id=msg_dict.get("message_id", str(uuid4())),
                    metadata=msg_dict.get("metadata", {})
                )
                self.messages.append(message)
            
            # Restore tool interactions
            self.tool_interactions = []
            for interaction_dict in data.get("tool_interactions", []):
                interaction = ToolInteraction(
                    tool_name=interaction_dict.get("tool_name", ""),
                    tool_input=interaction_dict.get("tool_input", {}),
                    tool_output=interaction_dict.get("tool_output"),
                    timestamp=datetime.fromisoformat(interaction_dict.get("timestamp", datetime.utcnow().isoformat())),
                    interaction_id=interaction_dict.get("interaction_id", str(uuid4())),
                    execution_time_ms=interaction_dict.get("execution_time_ms"),
                    error=interaction_dict.get("error")
                )
                self.tool_interactions.append(interaction)
            
            return True
        except Exception as e:
            print(f"Error loading L1 session from file: {e}")
            return False
    
    def _update_last_activity(self) -> None:
        """Update the last activity timestamp."""
        self.session_metadata.last_activity = datetime.utcnow()
    
    def clear_session(self) -> None:
        """
        Clear the current session (typically called after archival).
        
        This resets L1 for a new session and saves to disk.
        """
        self.session_metadata = SessionMetadata()
        self.messages.clear()
        self.tool_interactions.clear()
        
        # Auto-save to disk after clearing
        self.save_to_file()
