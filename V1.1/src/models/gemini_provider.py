"""
Gemini Model Provider

Handles Gemini API interactions
"""

import google.generativeai as genai
from typing import List, Dict, Any
from .base import BaseModelProvider, ModelConfig


class GeminiProvider(BaseModelProvider):
    """Gemini model provider implementation"""
    
    def initialize(self, system_prompt: str, tools: List[Dict[str, Any]]):
        """Initialize Gemini model"""
        genai.configure(api_key=self.api_key)
        
        # Convert tools to Gemini format
        tool_declarations = []
        for tool in tools:
            properties = {}
            for k, v in tool["input_schema"].get("properties", {}).items():
                prop_type = v.get("type", "string").upper()
                if prop_type == "INTEGER":
                    prop_type = "NUMBER"
                
                if prop_type == "ARRAY":
                    items_type = v.get("items", {}).get("type", "string").upper()
                    properties[k] = genai.protos.Schema(
                        type_=prop_type,
                        description=v.get("description", ""),
                        items=genai.protos.Schema(type_=items_type)
                    )
                else:
                    properties[k] = genai.protos.Schema(
                        type_=prop_type,
                        description=v.get("description", "")
                    )
            
            # Clean description
            description = tool["description"]
            if isinstance(description, str):
                description = " ".join(description.split())
            
            tool_declarations.append(
                genai.protos.FunctionDeclaration(
                    name=tool["name"],
                    description=description,
                    parameters=genai.protos.Schema(
                        type_="OBJECT",
                        properties=properties,
                        required=tool["input_schema"].get("required", [])
                    )
                )
            )
        
        self.tool_declarations = tool_declarations
        self.client = genai.GenerativeModel(
            model_name=self.config.model_id,
            system_instruction=system_prompt
        )
    
    def generate(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response from Gemini"""
        response = self.client.generate_content(
            messages,
            tools=[genai.protos.Tool(function_declarations=self.tool_declarations)] if self.tool_declarations else None,
            generation_config=genai.types.GenerationConfig(max_output_tokens=self.config.max_tokens)
        )
        
        candidate = response.candidates[0]
        if not candidate.content.parts:
            return {
                "content": "",
                "tool_calls": [],
                "finish_reason": "error"
            }
        
        # Check for tool calls
        tool_calls = []
        for part in candidate.content.parts:
            if hasattr(part, 'function_call'):
                tool_call = part.function_call
                if tool_call.name:
                    tool_calls.append({
                        "name": tool_call.name,
                        "arguments": dict(tool_call.args) if tool_call.args else {}
                    })
        
        # Get text content
        text_content = "".join(
            part.text for part in candidate.content.parts 
            if hasattr(part, 'text')
        )
        
        return {
            "content": text_content,
            "tool_calls": tool_calls,
            "finish_reason": "stop" if not tool_calls else "tool_calls",
            "raw_response": candidate.content
        }
    
    def format_tool_result(self, tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool result for Gemini"""
        return genai.protos.Part(
            function_response=genai.protos.FunctionResponse(
                name=tool_name,
                response=result
            )
        )
