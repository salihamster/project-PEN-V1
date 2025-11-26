"""
Project configuration settings with type-safe environment variable loading.

This module centralizes all configuration management, ensuring that
environment variables are properly typed and validated.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

from .enums import LogLevel

# Load environment variables from .env file
load_dotenv()


# ============================================================================
# Directory Configuration
# ============================================================================

PROJECT_ROOT: Path = Path(__file__).parent.parent
DATA_DIR: Path = PROJECT_ROOT / "data"
BACKUPS_DIR: Path = DATA_DIR / "backups"
EXPORTS_DIR: Path = DATA_DIR / "exports"
LOGS_DIR: Path = PROJECT_ROOT / "logs"

# Create directories if they don't exist
for directory in [DATA_DIR, BACKUPS_DIR, EXPORTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Google Drive Configuration
# ============================================================================

@dataclass(frozen=True)
class GoogleDriveConfig:
    """Google Drive configuration settings."""
    auth_mode: str
    service_account_file: Path
    folder_name: str
    
    @classmethod
    def from_env(cls) -> "GoogleDriveConfig":
        """Create configuration from environment variables."""
        return cls(
            auth_mode=os.getenv("GOOGLE_AUTH_MODE", "service_account"),
            service_account_file=PROJECT_ROOT / os.getenv(
                "SERVICE_ACCOUNT_FILE", 
                "service_account.json"
            ),
            folder_name=os.getenv("DRIVE_FOLDER_NAME", "Wpmesages")
        )


GOOGLE_DRIVE_CONFIG = GoogleDriveConfig.from_env()
# Backward compatibility
SERVICE_ACCOUNT_FILE = GOOGLE_DRIVE_CONFIG.service_account_file


# ============================================================================
# Email Configuration
# ============================================================================

@dataclass(frozen=True)
class EmailConfig:
    """Email configuration settings."""
    enabled: bool
    address: Optional[str]
    password: Optional[str]
    imap_server: str
    imap_port: int
    
    @classmethod
    def from_env(cls) -> "EmailConfig":
        """Create configuration from environment variables."""
        return cls(
            enabled=os.getenv("EMAIL_ENABLED", "false").lower() == "true",
            address=os.getenv("EMAIL_ADDRESS"),
            password=os.getenv("EMAIL_PASSWORD"),
            imap_server=os.getenv("IMAP_SERVER", "imap.gmail.com"),
            imap_port=int(os.getenv("IMAP_PORT", "993"))
        )
    
    def is_configured(self) -> bool:
        """Check if email is properly configured."""
        return bool(self.address and self.password)


EMAIL_CONFIG_OBJ = EmailConfig.from_env()
# Backward compatibility
EMAIL_ENABLED = EMAIL_CONFIG_OBJ.enabled
EMAIL_CONFIG = {
    "address": EMAIL_CONFIG_OBJ.address,
    "password": EMAIL_CONFIG_OBJ.password,
    "imap_server": EMAIL_CONFIG_OBJ.imap_server,
    "imap_port": EMAIL_CONFIG_OBJ.imap_port
}


# ============================================================================
# LLM Configuration
# ============================================================================

@dataclass(frozen=True)
class LLMConfig:
    """LLM API configuration settings."""
    gemini_api_key: Optional[str]
    minimax_api_key: Optional[str]
    openai_api_key: Optional[str]
    default_model: str
    max_tokens: int
    temperature: float
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create configuration from environment variables."""
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            minimax_api_key=os.getenv("MINIMAX_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            default_model=os.getenv("LLM_MODEL", "gemini-2.5-pro"),
            max_tokens=int(os.getenv("MAX_TOKENS", "24576")),
            temperature=float(os.getenv("TEMPERATURE", "0.7"))
        )


LLM_CONFIG_OBJ = LLMConfig.from_env()
# Backward compatibility
GEMINI_API_KEY = LLM_CONFIG_OBJ.gemini_api_key
LLM_CONFIG = {
    "api_key": LLM_CONFIG_OBJ.openai_api_key,
    "model": LLM_CONFIG_OBJ.default_model
}


# ============================================================================
# System Configuration
# ============================================================================

@dataclass(frozen=True)
class SystemConfig:
    """System-level configuration settings."""
    debug: bool
    log_level: LogLevel
    max_workers: int
    batch_size: int
    
    @classmethod
    def from_env(cls) -> "SystemConfig":
        """Create configuration from environment variables."""
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        try:
            log_level = LogLevel(log_level_str)
        except ValueError:
            log_level = LogLevel.INFO
        
        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=log_level,
            max_workers=int(os.getenv("MAX_WORKERS", "5")),
            batch_size=int(os.getenv("BATCH_SIZE", "100"))
        )


SYSTEM_CONFIG = SystemConfig.from_env()
# Backward compatibility
DEBUG = SYSTEM_CONFIG.debug
LOG_LEVEL = SYSTEM_CONFIG.log_level.value
MAX_WORKERS = SYSTEM_CONFIG.max_workers
BATCH_SIZE = SYSTEM_CONFIG.batch_size


# ============================================================================
# Data Source Configuration
# ============================================================================

@dataclass(frozen=True)
class DataSourceConfig:
    """Configuration for enabled data sources."""
    whatsapp_enabled: bool
    email_enabled: bool
    calendar_enabled: bool
    
    @classmethod
    def from_env(cls) -> "DataSourceConfig":
        """Create configuration from environment variables."""
        return cls(
            whatsapp_enabled=os.getenv("WHATSAPP_ENABLED", "true").lower() == "true",
            email_enabled=os.getenv("EMAIL_ENABLED", "true").lower() == "true",
            calendar_enabled=os.getenv("CALENDAR_ENABLED", "false").lower() == "true"
        )


DATA_SOURCE_CONFIG = DataSourceConfig.from_env()
# Backward compatibility
DATA_SOURCES = {
    "whatsapp": DATA_SOURCE_CONFIG.whatsapp_enabled,
    "email": DATA_SOURCE_CONFIG.email_enabled,
    "calendar": DATA_SOURCE_CONFIG.calendar_enabled
}


# ============================================================================
# Agent Configuration
# ============================================================================

@dataclass(frozen=True)
class AgentConfig:
    """Agent-specific configuration settings."""
    default_search_limit: int
    default_recent_days: int
    default_recent_limit: int
    default_drive_limit: int
    default_drive_search_limit: int
    context_window_size: int
    reading_agent_threshold: int  # Characters, not KB
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create configuration from environment variables."""
        return cls(
            default_search_limit=int(os.getenv("DEFAULT_SEARCH_LIMIT", "50")),
            default_recent_days=int(os.getenv("DEFAULT_RECENT_DAYS", "7")),
            default_recent_limit=int(os.getenv("DEFAULT_RECENT_LIMIT", "100")),
            default_drive_limit=int(os.getenv("DEFAULT_DRIVE_LIMIT", "100")),
            default_drive_search_limit=int(os.getenv("DEFAULT_DRIVE_SEARCH_LIMIT", "20")),
            context_window_size=int(os.getenv("CONTEXT_WINDOW_SIZE", "1000000")),
            reading_agent_threshold=int(os.getenv("READING_AGENT_THRESHOLD", "30000"))  # 30KB default
        )


AGENT_CONFIG = AgentConfig.from_env()
