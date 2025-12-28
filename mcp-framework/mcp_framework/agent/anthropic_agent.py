"""Anthropic Claude agent implementation."""

import json
from typing import List, Dict, Any, Optional, AsyncIterator
from anthropic import AsyncAnthropic

from mcp_framework.agent.base_agent import (
    BaseAgent, AgentProvider, Message, AgentResponse, ToolCall
)


class AnthropicAgent(BaseAgent):
    """Anthropic Claude agent."""
    
    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize Anthropic agent."""
        super().__init__(model=model, **kwargs)
        self.client = AsyncAnthropic(api_key=api_key)
    
    @classmethod
    def get_provider(cls) -> AgentProvider:
        return AgentProvider.ANTHROPIC
    
    def _convert_messages(self, messages: List[Message]) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """Convert to Anthropic message format. Returns (system, messages)."""
        system = None
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                message_dict = {
                    "role": "user" if msg.role == "user" else "assistant",
                    "content": msg.content
                }
                anthropic_messages.append(message_dict)
        
        return system, anthropic_messages
    
    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert MCP tools to Anthropic format."""
        anthropic_tools = []
        
        for tool in tools:
            anthropic_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["inputSchema"]
            })
        
        return anthropic_tools
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False
    ) -> AgentResponse:
        """Send chat request to Anthropic."""
        system, anthropic_messages = self._convert_messages(messages)
        
        kwargs = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        if system:
            kwargs["system"] = system
        
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
        
        response = await self.client.messages.create(**kwargs)
        
        # Extract content and tool calls
        message_content = ""
        tool_calls = []
        
        for content_block in response.content:
            if content_block.type == "text":
                message_content += content_block.text
            elif content_block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=content_block.id,
                    name=content_block.name,
                    arguments=content_block.input
                ))
        
        return AgentResponse(
            message=message_content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason,
            raw_response=response.model_dump()
        )
    
    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncIterator[str]:
        """Stream chat response from Anthropic."""
        system, anthropic_messages = self._convert_messages(messages)
        
        kwargs = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        if system:
            kwargs["system"] = system
        
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
        
        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text
