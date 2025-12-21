"""Tool registry for managing available tools."""

import threading
from typing import Dict, Type, List, Optional

from mcp_framework.tools.base import BaseTool, ToolMetadata, ToolCategory


class ToolRegistry:
    """Thread-safe singleton registry for tools."""
    
    _instance: Optional["ToolRegistry"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "ToolRegistry":
        """Create or return singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize registry."""
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._lock_tools = threading.Lock()
        self._initialized = True
    
    def register(self, tool_class: Type[BaseTool]) -> None:
        """
        Register a tool.
        
        Args:
            tool_class: Tool class to register
        """
        if not issubclass(tool_class, BaseTool):
            raise ValueError(f"{tool_class.__name__} must inherit from BaseTool")
        
        tool_name = tool_class.get_name()
        
        with self._lock_tools:
            if tool_name in self._tools:
                raise ValueError(f"Tool '{tool_name}' already registered")
            self._tools[tool_name] = tool_class
            print(f"✓ Registered tool: {tool_name} ({tool_class.get_category().value})")
    
    def get_tool(self, name: str) -> Optional[Type[BaseTool]]:
        """Get tool class by name."""
        with self._lock_tools:
            return self._tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[str]:
        """
        List tool names, optionally filtered by category.
        
        Args:
            category: Optional category filter
        
        Returns:
            List of tool names
        """
        with self._lock_tools:
            if category is None:
                return list(self._tools.keys())
            return [
                name for name, cls in self._tools.items()
                if cls.get_category() == category
            ]
    
    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get tool metadata by name."""
        tool_class = self.get_tool(name)
        if tool_class is None:
            return None
        return tool_class.get_metadata()
    
    def get_all_metadata(self) -> List[ToolMetadata]:
        """Get metadata for all tools."""
        with self._lock_tools:
            return [cls.get_metadata() for cls in self._tools.values()]


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def register_tool(tool_class: Type[BaseTool]) -> Type[BaseTool]:
    """
    Decorator to register a tool.
    
    Usage:
        @register_tool
        class MyTool(BaseTool):
            ...
    """
    get_tool_registry().register(tool_class)
    return tool_class
