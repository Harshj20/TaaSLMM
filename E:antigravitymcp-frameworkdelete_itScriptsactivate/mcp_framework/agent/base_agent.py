"""Base agent interface for Task Planning."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator
from pydantic import BaseModel
from enum import Enum


class AgentProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    QWEN = "qwen"
    CUSTOM = "custom"


class Message(BaseModel):
    """Chat message."""
    role: str  # user, assistant, system, tool
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class ToolCall(BaseModel):
    """Tool call request."""
    id: str
    name: str
    arguments: Dict[str, Any]


class AgentResponse(BaseModel):
    """Agent response."""
    message: str
    tool_calls: List[ToolCall] = []
    finish_reason: str = "stop"  # stop, tool_calls, length
    raw_response: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ):
        """
        Initialize agent.
        
        Args:
            model: Model name/identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Provider-specific arguments
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False
    ) -> AgentResponse:
        """
        Send chat request to agent.
        
        Args:
            messages: Conversation history
            tools: Available tools (MCP tool format)
            stream: Whether to stream response
        
        Returns:
            Agent response
        """
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncIterator[str]:
        """
        Stream chat response.
        
        Args:
            messages: Conversation history
            tools: Available tools
        
        Yields:
            Response chunks
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_provider(cls) -> AgentProvider:
        """Get provider type."""
        pass
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> "BaseAgent":
        """Create agent from configuration."""
        return cls(**config)
