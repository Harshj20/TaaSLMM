"""Agent manager for switching between providers."""

from typing import Dict, Any, Optional, Type
from enum import Enum

from mcp_framework.agent.base_agent import BaseAgent, AgentProvider
from mcp_framework.agent.openai_agent import OpenAIAgent
from mcp_framework.agent.anthropic_agent import AnthropicAgent
from mcp_framework.config import settings


class AgentManager:
    """Manages agent instances and provider switching."""
    
    # Registry of available agents
    _agents: Dict[AgentProvider, Type[BaseAgent]] = {
        AgentProvider.OPENAI: OpenAIAgent,
        AgentProvider.ANTHROPIC: AnthropicAgent,
    }
    
    def __init__(self):
        """Initialize agent manager."""
        self._current_provider: AgentProvider = AgentProvider(settings.llm_provider)
        self._instances: Dict[AgentProvider, BaseAgent] = {}
    
    @classmethod
    def register_agent(cls, agent_class: Type[BaseAgent]) -> None:
        """
        Register a custom agent provider.
        
        Args:
            agent_class: Agent class to register
        """
        provider = agent_class.get_provider()
        cls._agents[provider] = agent_class
    
    def get_agent(self, provider: Optional[AgentProvider] = None) -> BaseAgent:
        """
        Get agent instance for provider.
        
        Args:
            provider: Provider to use (uses current if None)
        
        Returns:
            Agent instance
        """
        if provider is None:
            provider = self._current_provider
        
        # Return cached instance if exists
        if provider in self._instances:
            return self._instances[provider]
        
        # Create new instance
        agent_class = self._agents.get(provider)
        if agent_class is None:
            raise ValueError(f"Unknown provider: {provider}")
        
        # Get configuration
        config = self._get_provider_config(provider)
        
        # Create and cache instance
        agent = agent_class(**config)
        self._instances[provider] = agent
        
        return agent
    
    def switch_provider(self, provider: AgentProvider) -> BaseAgent:
        """
        Switch to different provider.
        
        Args:
            provider: New provider to use
        
        Returns:
            New agent instance
        """
        if provider not in self._agents:
            raise ValueError(f"Unknown provider: {provider}")
        
        self._current_provider = provider
        return self.get_agent(provider)
    
    def get_current_provider(self) -> AgentProvider:
        """Get current provider."""
        return self._current_provider
    
    def list_providers(self) -> list[AgentProvider]:
        """List available providers."""
        return list(self._agents.keys())
    
    def _get_provider_config(self, provider: AgentProvider) -> Dict[str, Any]:
        """Get configuration for provider."""
        if provider == AgentProvider.OPENAI:
            return {
                "model": settings.llm_model if "gpt" in settings.llm_model else "gpt-4-turbo-preview",
                "api_key": settings.openai_api_key,
                "temperature": 0.7,
                "max_tokens": 4096
            }
        elif provider == AgentProvider.ANTHROPIC:
            return {
                "model": settings.llm_model if "claude" in settings.llm_model else "claude-3-5-sonnet-20241022",
                "api_key": settings.anthropic_api_key,
                "temperature": 0.7,
                "max_tokens": 4096
            }
        else:
            return {}


# Global agent manager
_agent_manager: Optional[AgentManager] = None


def get_agent_manager() -> AgentManager:
    """Get global agent manager."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager
