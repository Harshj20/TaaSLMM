"""Example utility tools."""

from typing import Dict, Any
import uuid

from mcp_framework.tools.base import BaseTool, ToolCategory
from mcp_framework.server.tool_registry import register_tool


@register_tool
class LoadDatasetTool(BaseTool):
    """Load dataset and return dataset ID."""
    
    @classmethod
    def get_name(cls) -> str:
        return "load_dataset"
    
    @classmethod
    def get_description(cls) -> str:
        return "Load a dataset from path or HuggingFace and return dataset identifier"
    
    @classmethod
    def get_category(cls) -> ToolCategory:
        return ToolCategory.UTILITY
    
    @classmethod
    def get_input_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "dataset_path": {"type": "string", "description": "Dataset path or HF name"},
                "split": {"type": "string", "description": "Dataset split", "default": "train"}
            },
            "required": ["dataset_path"]
        }
    
    @classmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "dataset_id": {"type": "string"},
                "num_samples": {"type": "integer"}
            },
            "required": ["dataset_id"]
        }
    
    async def execute(self, inputs: Dict[str, Any], runtime: Any = None) -> Dict[str, Any]:
        """Execute tool."""
        dataset_id = f"dataset_{uuid.uuid4().hex[:12]}"
        
        # TODO: Actually load dataset
        # For now, mock implementation
        
        return {
            "dataset_id": dataset_id,
            "dataset_path": inputs["dataset_path"],
            "num_samples": 1000
        }


@register_tool
class LoadConfigTool(BaseTool):
    """Load configuration."""
    
    @classmethod
    def get_name(cls) -> str:
        return "load_config"
    
    @classmethod
    def get_description(cls) -> str:
        return "Load training configuration and return config ID"
    
    @classmethod
    def get_category(cls) -> ToolCategory:
        return ToolCategory.UTILITY
    
    @classmethod
    def get_input_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "config": {"type": "object", "description": "Configuration dictionary"}
            },
            "required": ["config"]
        }
    
    @classmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "config_id": {"type": "string"}
            },
            "required": ["config_id"]
        }
    
    async def execute(self, inputs: Dict[str, Any], runtime: Any = None) -> Dict[str, Any]:
        """Execute tool."""
        config_id = f"config_{uuid.uuid4().hex[:12]}"
        
        return {
            "config_id": config_id,
            "config": inputs["config"]
        }
