"""
Base Model Provider Interface

Defines the common interface for all LLM providers (Gemini, Claude, OpenAI)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    provider: str  # gemini, anthropic, openai
    model_id: str  # gemini-2.0-flash-exp, claude-3-5-sonnet-20241022, gpt-4o
    display_name: str  # User-friendly name
    max_tokens: int
    supports_tools: bool = True
    api_key_env: str = ""  # Environment variable name for API key


class BaseModelProvider(ABC):
    """Base class for all model providers"""
    
    def __init__(self, api_key: str, model_config: ModelConfig):
        self.api_key = api_key
        self.config = model_config
        self.client = None
    
    @abstractmethod
    def initialize(self, system_prompt: str, tools: List[Dict[str, Any]]):
        """Initialize the model with system prompt and tools"""
        pass
    
    @abstractmethod
    def generate(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a response from the model
        
        Returns:
            {
                "content": str,  # Text response
                "tool_calls": List[Dict],  # Tool calls if any
                "finish_reason": str
            }
        """
        pass
    
    @abstractmethod
    def format_tool_result(self, tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool result for the model"""
        pass


# Available models configuration
AVAILABLE_MODELS = {
    # Gemini Models (Google)
    "gemini-2.0-flash-thinking": ModelConfig(
        provider="gemini",
        model_id="gemini-2.0-flash-thinking",
        display_name="Gemini 2.0 Flash Thinking",
        max_tokens=8192,
        api_key_env="GEMINI_API_KEY"
    ),
    "gemini-2.5-flash": ModelConfig(
        provider="gemini",
        model_id="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        max_tokens=1000000,
        api_key_env="GEMINI_API_KEY"
    ),
    "gemini-2.5-flash-lite": ModelConfig(
        provider="gemini",
        model_id="gemini-2.5-flash-lite",
        display_name="Gemini 2.5 Flash Lite",
        max_tokens=1000000,
        api_key_env="GEMINI_API_KEY"
    ),
    "gemini-2.5-pro": ModelConfig(
        provider="gemini",
        model_id="gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        max_tokens=1000000,
        api_key_env="GEMINI_API_KEY"
    ),
    "gemini-3-pro": ModelConfig(
        provider="gemini",
        model_id="gemini-3-pro",
        display_name="Gemini 3 Pro",
        max_tokens=1000000,
        api_key_env="GEMINI_API_KEY"
    ),
    
    # Anthropic Claude Models
    "claude-haiku-4.5": ModelConfig(
        provider="anthropic",
        model_id="claude-haiku-4.5",
        display_name="Claude Haiku 4.5",
        max_tokens=8192,
        api_key_env="ANTHROPIC_API_KEY"
    ),
    "claude-sonnet-4": ModelConfig(
        provider="anthropic",
        model_id="claude-sonnet-4",
        display_name="Claude Sonnet 4",
        max_tokens=8192,
        api_key_env="ANTHROPIC_API_KEY"
    ),
    "claude-sonnet-4.5": ModelConfig(
        provider="anthropic",
        model_id="claude-sonnet-4.5",
        display_name="Claude Sonnet 4.5",
        max_tokens=8192,
        api_key_env="ANTHROPIC_API_KEY"
    ),
    
    # OpenAI GPT Models
    "gpt-4o": ModelConfig(
        provider="openai",
        model_id="gpt-4o",
        display_name="GPT-4o",
        max_tokens=16384,
        api_key_env="OPENAI_API_KEY"
    ),
    "gpt-4o-mini": ModelConfig(
        provider="openai",
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        max_tokens=16384,
        api_key_env="OPENAI_API_KEY"
    ),
    "gpt-5": ModelConfig(
        provider="openai",
        model_id="gpt-5",
        display_name="GPT-5",
        max_tokens=128000,
        api_key_env="OPENAI_API_KEY"
    ),
    "gpt-5.1-instant": ModelConfig(
        provider="openai",
        model_id="gpt-5.1-instant",
        display_name="GPT-5.1 Instant",
        max_tokens=128000,
        api_key_env="OPENAI_API_KEY"
    ),
    "gpt-5.1-thinking": ModelConfig(
        provider="openai",
        model_id="gpt-5.1-thinking",
        display_name="GPT-5.1 Thinking",
        max_tokens=128000,
        api_key_env="OPENAI_API_KEY"
    ),
}


def get_available_models() -> List[Dict[str, Any]]:
    """Get list of available models with their metadata"""
    return [
        {
            "id": model_id,
            "provider": config.provider,
            "display_name": config.display_name,
            "max_tokens": config.max_tokens,
            "supports_tools": config.supports_tools,
        }
        for model_id, config in AVAILABLE_MODELS.items()
    ]


def get_model_config(model_id: str) -> Optional[ModelConfig]:
    """Get configuration for a specific model"""
    return AVAILABLE_MODELS.get(model_id)
