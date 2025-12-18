"""
Enumerations for type-safe constants across the project.

This module defines all enum types used throughout the PEN project
to avoid magic strings and improve code maintainability.
"""

from enum import Enum, auto


class MessageSource(str, Enum):
    """Source types for messages."""
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    ALL = ""  # Empty string for all sources


class ContextType(str, Enum):
    """Types of contexts that can be stored in L4 memory."""
    MEETING = "meeting"
    PROJECT = "project"
    TASK = "task"
    EVENT = "event"
    NOTE = "note"


class Priority(str, Enum):
    """Priority levels for tasks and contexts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Status(str, Enum):
    """Status values for contexts and tasks."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PENDING = "pending"


class RelationType(str, Enum):
    """Types of relationships between contexts."""
    RELATED_TO = "related_to"
    FOLLOWS = "follows"
    PRECEDES = "precedes"
    PART_OF = "part_of"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class FileType(str, Enum):
    """File types for Drive operations."""
    TXT = "txt"
    ZIP = "zip"
    JSON = "json"
    PDF = "pdf"
    ALL = ""  # Empty string for all types


class SearchField(str, Enum):
    """Search fields for email and messages."""
    ALL = "all"
    SENDER = "sender"
    RECIPIENT = "recipient"
    SUBJECT = "subject"
    BODY = "body"
    KEYWORD = "keyword"


class MediaType(str, Enum):
    """Media types in messages."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    STICKER = "sticker"
    CONTACT = "contact"
    LOCATION = "location"
