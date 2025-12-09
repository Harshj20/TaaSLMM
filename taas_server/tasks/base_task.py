"""Base task interface for all TaaS tasks."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import uuid
import asyncio


class BaseTask(ABC):
    """
    Abstract base class for all tasks.
    
    All tasks must inherit from this class and implement the required methods.
    """
    
    def __init__(self, task_id: Optional[str] = None):
        """Initialize the task."""
        self.task_id = task_id or str(uuid.uuid4())
        self.status = "PENDING"
        self.progress = 0.0
        self.error_message: Optional[str] = None
        self.outputs: Dict[str, Any] = {}
    
    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """Return the task name (used for registration)."""
        pass
    
    @classmethod
    @abstractmethod
    def get_description(cls) -> str:
        """Return a human-readable description of the task."""
        pass
    
    @classmethod
    @abstractmethod
    def get_version(cls) -> str:
        """Return the task version."""
        pass
    
    @classmethod
    @abstractmethod
    def get_input_schema(cls) -> Dict[str, Any]:
        """
        Return JSON Schema for required inputs.
        
        Example:
        {
            "type": "object",
            "properties": {
                "model_name": {"type": "string", "description": "Model to finetune"},
                "dataset_path": {"type": "string", "description": "Path to dataset"}
            },
            "required": ["model_name", "dataset_path"]
        }
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        """
        Return JSON Schema for expected outputs.
        
        Example:
        {
            "type": "object",
            "properties": {
                "model_path": {"type": "string"},
                "metrics": {"type": "object"}
            }
        }
        """
        pass
    
    @classmethod
    def get_dependencies(cls) -> List[str]:
        """Return list of task dependencies (task names that must run before this)."""
        return []
    
    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Return additional metadata about the task."""
        return {
            "name": cls.get_name(),
            "description": cls.get_description(),
            "version": cls.get_version(),
            "input_schema": cls.get_input_schema(),
            "output_schema": cls.get_output_schema(),
            "dependencies": cls.get_dependencies(),
        }
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate inputs against the schema.
        
        Returns:
            (is_valid, error_message)
        """
        from jsonschema import validate, ValidationError
        
        schema = self.get_input_schema()
        try:
            validate(instance=inputs, schema=schema)
            return True, None
        except ValidationError as e:
            return False, str(e)
    
    def validate_outputs(self, outputs: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate outputs against the schema.
        
        Returns:
            (is_valid, error_message)
        """
        from jsonschema import validate, ValidationError
        
        schema = self.get_output_schema()
        try:
            validate(instance=outputs, schema=schema)
            return True, None
        except ValidationError as e:
            return False, str(e)
    
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the task asynchronously.
        
        Args:
            inputs: Validated input parameters
        
        Returns:
            Dictionary of output values
        
        Raises:
            Exception: If task execution fails
        """
        pass
    
    def update_progress(self, progress: float, message: Optional[str] = None) -> None:
        """
        Update task progress (0.0 to 1.0).
        
        This can be used within execute() to report progress.
        """
        self.progress = max(0.0, min(1.0, progress))
        if message:
            # This will be logged by the executor
            pass
    
    async def pre_execute(self, inputs: Dict[str, Any]) -> None:
        """Hook called before execute(). Override for setup logic."""
        pass
    
    async def post_execute(self, outputs: Dict[str, Any]) -> None:
        """Hook called after execute(). Override for cleanup logic."""
        pass
    
    async def on_error(self, error: Exception) -> None:
        """Hook called when execute() raises an exception."""
        self.error_message = str(error)
    
    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution workflow.
        
        This method handles validation, execution, and error handling.
        """
        # Validate inputs
        is_valid, error_msg = self.validate_inputs(inputs)
        if not is_valid:
            raise ValueError(f"Input validation failed: {error_msg}")
        
        try:
            # Pre-execute hook
            await self.pre_execute(inputs)
            
            # Execute the task
            self.status = "RUNNING"
            outputs = await self.execute(inputs)
            
            # Validate outputs
            is_valid, error_msg = self.validate_outputs(outputs)
            if not is_valid:
                raise ValueError(f"Output validation failed: {error_msg}")
            
            # Post-execute hook
            await self.post_execute(outputs)
            
            self.status = "COMPLETED"
            self.progress = 1.0
            self.outputs = outputs
            return outputs
            
        except Exception as e:
            self.status = "FAILED"
            await self.on_error(e)
            raise
