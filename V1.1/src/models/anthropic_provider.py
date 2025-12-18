"""
Anthropic (Claude) Model Provider

Handles Claude API interactions
"""

from anthropic import Anthropic
from typing import List, Dict, Any
from .base import BaseModelProvider, ModelConfig


class AnthropicProvider(BaseModelProvider):
    """Anthropic (Claude) model provider implementation"""
    
    def initialize(self, system_prompt: str, tools: List[Dict[str, Any]]):
        """Initialize Anthropic model"""
        self.client = Anthropic(api_key=self.api_key)
        self.system_prompt = system_prompt
        
        # Convert tools to Anthropic format
        self.tools = []
        for tool in tools:
            self.tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            })
    
    def generate(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response from Claude"""
        # Convert messages to Anthropic format
        anthropic_messages = []
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
                anthropic_messages.append({"role": role, "content": content})
            else:
                anthropic_messages.append({"role": role, "content": msg.get("content", "")})
        
        # Make API call
        response = self.client.messages.create(
            model=self.config.model_id,
            max_tokens=self.config.max_tokens,
            system=self.system_prompt,
            messages=anthropic_messages,
            tools=self.tools if self.tools else None
        )
        
        # Parse response
        tool_calls = []
        text_content = ""
        
        for block in response.content:
            if block.type == "text":
                text_content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input
                })
        
        return {
            "content": text_content,
            "tool_calls": tool_calls,
            "finish_reason": response.stop_reason,
            "raw_response": response
        }
    
    def format_tool_result(self, tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool result for Claude"""
        return {
            "type": "tool_result",
            "tool_use_id": result.get("tool_use_id", ""),
            "content": str(result)
        }
