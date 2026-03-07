"""
Model Factory

Creates appropriate model provider based on configuration
"""

import os
from typing import Optional
from .base import BaseModelProvider, ModelConfig, get_model_config
from .gemini_provider import GeminiProvider
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider


class ModelFactory:
    """Factory for creating model providers"""
    
    @staticmethod
    def create_provider(model_id: str) -> Optional[BaseModelProvider]:
        """
        Create a model provider instance
        
        Args:
            model_id: Model identifier (e.g., "gemini-2.0-flash-exp")
        
        Returns:
            BaseModelProvider instance or None if model not found/API key missing
        """
        config = get_model_config(model_id)
        if not config:
            raise ValueError(f"Unknown model: {model_id}")
        
        # Get API key from environment
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise ValueError(f"API key not found: {config.api_key_env}")
        
        # Create appropriate provider
        if config.provider == "gemini":
            return GeminiProvider(api_key, config)
        elif config.provider == "anthropic":
            return AnthropicProvider(api_key, config)
        elif config.provider == "openai":
            return OpenAIProvider(api_key, config)
        else:
            raise ValueError(f"Unknown provider: {config.provider}")
    
    @staticmethod
    def get_available_models_with_keys() -> list:
        """Get list of models that have API keys configured"""
        from .base import AVAILABLE_MODELS
        
        available = []
        for model_id, config in AVAILABLE_MODELS.items():
            api_key = os.getenv(config.api_key_env)
            if api_key:
                available.append({
                    "id": model_id,
                    "provider": config.provider,
                    "display_name": config.display_name,
                    "max_tokens": config.max_tokens,
                    "supports_tools": config.supports_tools,
                })
        
        return available
