"""Example microservice tasks (utilities)."""

from typing import Dict, Any
import uuid
import os

from taas_server.tasks.base_task import BaseTask, TaskType
from taas_server.tasks.task_registry import register_task


@register_task
class LoadDatasetTask(BaseTask):
    """Microservice: Load dataset and return dataset ID."""
    
    @classmethod
    def get_name(cls) -> str:
        return "load_dataset"
    
    @classmethod
    def get_description(cls) -> str:
        return "Load a dataset from path or HuggingFace and return a unique dataset identifier"
    
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
                "dataset_path": {
                    "type": "string",
                    "description": "Local path or HuggingFace dataset name"
                },
                "split": {
                    "type": "string",
                    "description": "Dataset split (train/validation/test)",
                    "default": "train"
                }
            },
            "required": ["dataset_path"]
        }
    
    @classmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "dataset_id": {
                    "type": "string",
                    "description": "Unique identifier for the loaded dataset"
                },
                "dataset_path": {
                    "type": "string",
                    "description": "Resolved path to dataset"
                },
                "num_samples": {
                    "type": "integer",
                    "description": "Number of samples in dataset"
                }
            },
            "required": ["dataset_id", "dataset_path"]
        }
    
    @classmethod
    def get_output_mappings(cls) -> Dict[str, str]:
        return {
            "dataset_id": "dataset_id",
            "dataset_path": "dataset_path"
        }
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load the dataset and return identifier."""
        dataset_path = inputs["dataset_path"]
        split = inputs.get("split", "train")
        
        # Generate unique dataset ID
        dataset_id = f"dataset_{uuid.uuid4().hex[:12]}"
        
        # In a real implementation, you would:
        # 1. Download/load the dataset
        # 2. Cache it with the dataset_id
        # 3. Store metadata in database
        
        # For now, simulate loading
        self.update_progress(0.5, "Loading dataset...")
        
        # Mock: assume dataset exists
        num_samples = 1000  # Would come from actual dataset
        
        self.update_progress(1.0, "Dataset loaded")
        
        return {
            "dataset_id": dataset_id,
            "dataset_path": dataset_path,
            "num_samples": num_samples
        }


@register_task
class LoadLoRATask(BaseTask):
    """Microservice: Load LoRA adapter and return adapter ID."""
    
    @classmethod
    def get_name(cls) -> str:
        return "load_lora"
    
    @classmethod
    def get_description(cls) -> str:
        return "Load a LoRA adapter from path or HuggingFace and return adapter identifier"
    
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
                "lora_path": {
                    "type": "string",
                    "description": "Path to LoRA adapter"
                },
                "base_model": {
                    "type": "string",
                    "description": "Base model name for the adapter"
                }
            },
            "required": ["lora_path"]
        }
    
    @classmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "lora_id": {
                    "type": "string",
                    "description": "Unique identifier for the LoRA adapter"
                },
                "lora_path": {
                    "type": "string",
                    "description": "Path to LoRA adapter"
                }
            },
            "required": ["lora_id"]
        }
    
    @classmethod
    def get_output_mappings(cls) -> Dict[str, str]:
        return {
            "lora_id": "lora_id",
            "lora_path": "lora_path"
        }
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load LoRA adapter."""
        lora_path = inputs["lora_path"]
        
        lora_id = f"lora_{uuid.uuid4().hex[:12]}"
        
        self.update_progress(0.5, "Loading LoRA adapter...")
        
        # Mock loading
        
        self.update_progress(1.0, "LoRA loaded")
        
        return {
            "lora_id": lora_id,
            "lora_path": lora_path
        }


@register_task
class CreateEnvTask(BaseTask):
    """Microservice: Create isolated environment for task execution."""
    
    @classmethod
    def get_name(cls) -> str:
        return "create_env"
    
    @classmethod
    def get_description(cls) -> str:
        return "Create an isolated Python environment with specified dependencies"
    
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
                "python_version": {
                    "type": "string",
                    "description": "Python version (e.g., '3.11')",
                    "default": "3.11"
                },
                "requirements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of Python packages to install"
                }
            }
        }
    
    @classmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "env_id": {
                    "type": "string",
                    "description": "Unique environment identifier"
                },
                "env_path": {
                    "type": "string",
                    "description": "Path to environment"
                }
            },
            "required": ["env_id"]
        }
    
    @classmethod
    def get_output_mappings(cls) -> Dict[str, str]:
        return {
            "env_id": "env_id"
        }
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Create isolated environment."""
        python_version = inputs.get("python_version", "3.11")
        requirements = inputs.get("requirements", [])
        
        env_id = f"env_{uuid.uuid4().hex[:12]}"
        env_path = f"/tmp/envs/{env_id}"
        
        self.update_progress(0.3, "Creating virtual environment...")
        
        # Mock: In real implementation, would use uv or virtualenv
        
        self.update_progress(0.7, "Installing dependencies...")
        
        # Mock install packages
        
        self.update_progress(1.0, "Environment ready")
        
        return {
            "env_id": env_id,
            "env_path": env_path
        }
