"""Base tool interface for MCP Framework."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ToolCategory(str, Enum):
    """Tool category classification."""
    
    UTILITY = "UTILITY"  # Lightweight utilities
    TRAINING = "TRAINING"  # Heavy ML tasks requiring isolation
    ADMIN = "ADMIN"  # Management operations


class ToolMetadata(BaseModel):
    """Tool metadata."""
    
    name: str
    description: str
    category: ToolCategory
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    requires_isolation: bool = False
    dependencies: List[str] = Field(default_factory=list)


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """Get tool name."""
        pass
    
    @classmethod
    @abstractmethod
    def get_description(cls) -> str:
        """Get tool description."""
        pass
    
    @classmethod
    @abstractmethod
    def get_category(cls) -> ToolCategory:
        """Get tool category."""
        pass
    
    @classmethod
    def requires_isolation(cls) -> bool:
        """Whether tool requires isolated execution."""
        return cls.get_category() == ToolCategory.TRAINING
    
    @classmethod
    @abstractmethod
    def get_input_schema(cls) -> Dict[str, Any]:
        """Get JSON Schema for inputs."""
        pass
    
    @classmethod
    @abstractmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        """Get JSON Schema for outputs."""
        pass
    
    @classmethod
    def get_dependencies(cls) -> List[str]:
        """Get list of dependent tool names."""
        return []
    
    @classmethod
    def get_metadata(cls) -> ToolMetadata:
        """Get complete tool metadata."""
        return ToolMetadata(
            name=cls.get_name(),
            description=cls.get_description(),
            category=cls.get_category(),
            input_schema=cls.get_input_schema(),
            output_schema=cls.get_output_schema(),
            requires_isolation=cls.requires_isolation(),
            dependencies=cls.get_dependencies()
        )
    
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any], runtime: Optional[Any] = None) -> Dict[str, Any]:
        """
        Execute the tool.
        
        Args:
            inputs: Validated inputs
            runtime: Optional isolated runtime for training tools
        
        Returns:
            Tool outputs
        """
        pass
