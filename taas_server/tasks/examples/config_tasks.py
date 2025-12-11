"""Example configuration tasks."""

from typing import Dict, Any
import yaml
import json

from taas_server.tasks.base_task import BaseTask, TaskType
from taas_server.tasks.task_registry import register_task


@register_task
class LoadConfigTask(BaseTask):
    """Load configuration from file or dictionary."""
    
    @classmethod
    def get_name(cls) -> str:
        return "load_config"
    
    @classmethod
    def get_description(cls) -> str:
        return "Load training/model configuration from a YAML or JSON file, or from a dictionary"
    
    @classmethod
    def get_version(cls) -> str:
        return "1.0.0"
    
    @classmethod
    def get_task_type(cls) -> TaskType:
        return TaskType.MICROSERVICE
    
    @classmethod
    def get_input_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "config_path": {
                    "type": "string",
                    "description": "Path to config file (YAML or JSON)"
                },
                "config_dict": {
                    "type": "object",
                    "description": "Configuration as dictionary (alternative to file)"
                },
            },
            "oneOf": [
                {"required": ["config_path"]},
                {"required": ["config_dict"]}
            ]
        }
    
    @classmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "config": {"type": "object", "description": "Loaded configuration"},
                "config_id": {"type": "string", "description": "Unique config identifier"}
            },
            "required": ["config", "config_id"]
        }
    
    @classmethod
    def get_output_mappings(cls) -> Dict[str, str]:
        return {
            "config_id": "config_id",
            "config": "config"
        }
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load the configuration."""
        import uuid
        
        config = None
        
        if "config_path" in inputs:
            path = inputs["config_path"]
            with open(path, "r") as f:
                if path.endswith(".yaml") or path.endswith(".yml"):
                    config = yaml.safe_load(f)
                elif path.endswith(".json"):
                    config = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {path}")
        elif "config_dict" in inputs:
            config = inputs["config_dict"]
        
        if config is None:
            raise ValueError("No configuration provided")
        
        config_id = f"config_{uuid.uuid4().hex[:12]}"
        
        return {"config": config, "config_id": config_id}


@register_task
class CreateConfigTask(BaseTask):
    """Create a new configuration with validation."""
    
    @classmethod
    def get_name(cls) -> str:
        return "create_config"
    
    @classmethod
    def get_description(cls) -> str:
        return "Create a new training/model configuration with validation"
    
    @classmethod
    def get_version(cls) -> str:
        return "1.0.0"
    
    @classmethod
    def get_task_type(cls) -> TaskType:
        return TaskType.MICROSERVICE
    
    @classmethod
    def get_input_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "config_type": {
                    "type": "string",
                    "enum": ["training", "model", "data"],
                    "description": "Type of configuration to create"
                },
                "parameters": {
                    "type": "object",
                    "description": "Configuration parameters"
                },
                "output_path": {
                    "type": "string",
                    "description": "Path to save the configuration (optional)"
                }
            },
            "required": ["config_type", "parameters"]
        }
    
    @classmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "config": {"type": "object"},
                "saved_path": {"type": "string"}
            },
            "required": ["config"]
        }
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Create and optionally save the configuration."""
        config_type = inputs["config_type"]
        parameters = inputs["parameters"]
        
        # Add metadata
        config = {
            "type": config_type,
            "version": "1.0",
            **parameters
        }
        
        result = {"config": config}
        
        # Save if output path provided
        if "output_path" in inputs:
            output_path = inputs["output_path"]
            with open(output_path, "w") as f:
                if output_path.endswith(".yaml") or output_path.endswith(".yml"):
                    yaml.dump(config, f)
                elif output_path.endswith(".json"):
                    json.dump(config, f, indent=2)
                else:
                    raise ValueError(f"Unsupported format: {output_path}")
            result["saved_path"] = output_path
        
        return result
