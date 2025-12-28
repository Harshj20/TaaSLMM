"""OpenAI agent implementation."""

import json
from typing import List, Dict, Any, Optional, AsyncIterator
from openai import AsyncOpenAI

from mcp_framework.agent.base_agent import (
    BaseAgent, AgentProvider, Message, AgentResponse, ToolCall
)


class OpenAIAgent(BaseAgent):
    """OpenAI GPT agent."""
    
    def __init__(
        self,
        model: str = "gpt-4-turbo-preview",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize OpenAI agent."""
        super().__init__(model=model, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key)
    
    @classmethod
    def get_provider(cls) -> AgentProvider:
        return AgentProvider.OPENAI
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert to OpenAI message format."""
        openai_messages = []
        
        for msg in messages:
            message_dict = {
                "role": msg.role,
                "content": msg.content
            }
            
            if msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls
            
            if msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id
            
            openai_messages.append(message_dict)
        
        return openai_messages
    
    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert MCP tools to OpenAI function format."""
        openai_tools = []
        
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                }
            })
        
        return openai_tools
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False
    ) -> AgentResponse:
        """Send chat request to OpenAI."""
        openai_messages = self._convert_messages(messages)
        
        kwargs = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
            kwargs["tool_choice"] = "auto"
        
        response = await self.client.chat.completions.create(**kwargs)
        
        choice = response.choices[0]
        message = choice.message
        
        # Extract tool calls
        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments)
                ))
        
        return AgentResponse(
            message=message.content or "",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            raw_response=response.model_dump()
        )
    
    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncIterator[str]:
        """Stream chat response from OpenAI."""
        openai_messages = self._convert_messages(messages)
        
        kwargs = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True
        }
        
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
            kwargs["tool_choice"] = "auto"
        
        stream = await self.client.chat.completions.create(**kwargs)
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
