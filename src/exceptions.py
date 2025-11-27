"""
Custom exceptions for the PEN project.

This module defines all custom exception types used throughout the project
for better error handling and debugging.
"""


class PENException(Exception):
    """Base exception for all PEN-related errors."""
    pass


class ConfigurationError(PENException):
    """Raised when configuration is invalid or missing."""
    pass


class DataManagerError(PENException):
    """Raised when data management operations fail."""
    pass


class ParserError(PENException):
    """Raised when parsing operations fail."""
    pass


class WhatsAppParserError(ParserError):
    """Raised when WhatsApp message parsing fails."""
    pass


class EmailParserError(ParserError):
    """Raised when email parsing fails."""
    pass


class DriveError(PENException):
    """Raised when Google Drive operations fail."""
    pass


class MemoryError(PENException):
    """Raised when L4 memory operations fail."""
    pass


class ToolExecutionError(PENException):
    """Raised when agent tool execution fails."""
    pass


class APIError(PENException):
    """Raised when external API calls fail."""
    pass


class ValidationError(PENException):
    """Raised when data validation fails."""
    pass
