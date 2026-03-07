"""
OpenAI Model Provider

Handles OpenAI API interactions
"""

from openai import OpenAI
from typing import List, Dict, Any
from .base import BaseModelProvider, ModelConfig


class OpenAIProvider(BaseModelProvider):
    """OpenAI model provider implementation"""
    
    def initialize(self, system_prompt: str, tools: List[Dict[str, Any]]):
        """Initialize OpenAI model"""
        self.client = OpenAI(api_key=self.api_key)
        self.system_prompt = system_prompt
        
        # Convert tools to OpenAI format
        self.tools = []
        if self.config.supports_tools:
            for tool in tools:
                self.tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["input_schema"]
                    }
                })
    
    def generate(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response from OpenAI"""
        # Convert messages to OpenAI format
        openai_messages = [{"role": "system", "content": self.system_prompt}]
        
        for msg in messages:
            role = msg.get("role")
            if role == "model":
                role = "assistant"
            
            # Handle different content types
            if "parts" in msg:
                # Gemini format - convert to text
                content = ""
                for part in msg["parts"]:
                    if isinstance(part, str):
                        content += part
                    elif hasattr(part, 'text'):
                        content += part.text
                openai_messages.append({"role": role, "content": content})
            else:
                openai_messages.append({"role": role, "content": msg.get("content", "")})
        
        # Make API call
        kwargs = {
            "model": self.config.model_id,
            "messages": openai_messages,
            "max_tokens": self.config.max_tokens
        }
        
        if self.tools and self.config.supports_tools:
            kwargs["tools"] = self.tools
            kwargs["tool_choice"] = "auto"
        
        response = self.client.chat.completions.create(**kwargs)
        
        # Parse response
        message = response.choices[0].message
        tool_calls = []
        
        if message.tool_calls:
            for tc in message.tool_calls:
                import json
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments)
                })
        
        return {
            "content": message.content or "",
            "tool_calls": tool_calls,
            "finish_reason": response.choices[0].finish_reason,
            "raw_response": response
        }
    
    def format_tool_result(self, tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool result for OpenAI"""
        return {
            "role": "tool",
            "tool_call_id": result.get("tool_call_id", ""),
            "content": str(result)
        }
