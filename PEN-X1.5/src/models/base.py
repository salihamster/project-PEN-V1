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
    provider: str 
    model_id: str 
    display_name: str  
    max_tokens: int
    supports_tools: bool = True
    api_key_env: str = "" 


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


AVAILABLE_MODELS = {
    # Gemini Models (Google)
    # === Gemini 2.5 Series (Stable) ===
    "gemini-2.5-flash": ModelConfig(
        provider="gemini",
        model_id="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        max_tokens=65536,
        api_key_env="GEMINI_API_KEY"
    ),
    "gemini-2.5-pro": ModelConfig(
        provider="gemini",
        model_id="gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        max_tokens=65536,
        api_key_env="GEMINI_API_KEY"
    ),
    
    # === Gemini 3 Series (Preview) ===
    "gemini-3-flash-preview": ModelConfig(
        provider="gemini",
        model_id="gemini-3-flash-preview",
        display_name="Gemini 3 Flash (Preview)",
        max_tokens=65536,
        api_key_env="GEMINI_API_KEY"
    ),
    "gemini-3-pro-preview": ModelConfig(
        provider="gemini",
        model_id="gemini-3-pro-preview",
        display_name="Gemini 3 Pro (Preview) - Deep Think",
        max_tokens=65536,
        api_key_env="GEMINI_API_KEY"
    ),
    
    # === Gemini 2.0 Thinking (Experimental) ===
    "gemini-2.0-flash-thinking-exp": ModelConfig(
        provider="gemini",
        model_id="gemini-2.0-flash-thinking-exp",
        display_name="Gemini 2.0 Flash Thinking",
        max_tokens=32768,
        api_key_env="GEMINI_API_KEY"
    ),
    
    # Anthropic Claude Models
    "claude-sonnet-4-5-20250929": ModelConfig(
        provider="anthropic",
        model_id="claude-sonnet-4-5-20250929",
        display_name="Claude 4.5 Sonnet - Best for Agents",
        max_tokens=8192,
        api_key_env="ANTHROPIC_API_KEY"
    ),
    "claude-haiku-4-5-20251001": ModelConfig(
        provider="anthropic",
        model_id="claude-haiku-4-5-20251001",
        display_name="Claude 4.5 Haiku - Fast",
        max_tokens=8192,
        api_key_env="ANTHROPIC_API_KEY"
    ),
    "claude-3-5-haiku-20241022": ModelConfig(
        provider="anthropic",
        model_id="claude-3-5-haiku-20241022",
        display_name="Claude 3.5 Haiku - Cheapest",
        max_tokens=8192,
        api_key_env="ANTHROPIC_API_KEY"
    ),
    
    # OpenAI GPT Models
    "gpt-5.2": ModelConfig(
        provider="openai",
        model_id="gpt-5.2",
        display_name="GPT-5.2 - Main Model",
        max_tokens=128000,
        api_key_env="OPENAI_API_KEY"
    ),
    "o3-2025-04-16": ModelConfig(
        provider="openai",
        model_id="o3-2025-04-16",
        display_name="OpenAI o3 - Deep Reasoning",
        max_tokens=100000,
        api_key_env="OPENAI_API_KEY"
    ),
    "gpt-5-nano": ModelConfig(
        provider="openai",
        model_id="gpt-5-nano",
        display_name="GPT-5 Nano - Cheapest",
        max_tokens=16384,
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
