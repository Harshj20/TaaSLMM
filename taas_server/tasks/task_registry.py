"""Task registry for managing available tasks."""

import threading
from typing import Dict, Type, List, Optional, Any

from taas_server.tasks.base_task import BaseTask


class TaskRegistry:
    """Thread-safe singleton registry for task registration and discovery."""
    
    _instance: Optional["TaskRegistry"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "TaskRegistry":
        """Create or return singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the registry."""
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        self._tasks: Dict[str, Type[BaseTask]] = {}
        self._lock_tasks = threading.Lock()
        self._initialized = True
    
    def register(self, task_class: Type[BaseTask]) -> None:
        """
        Register a task class.
        
        Args:
            task_class: Task class to register (must inherit from BaseTask)
        
        Raises:
            ValueError: If task is already registered or invalid
        """
        if not issubclass(task_class, BaseTask):
            raise ValueError(f"{task_class.__name__} must inherit from BaseTask")
        
        task_name = task_class.get_name()
        
        with self._lock_tasks:
            if task_name in self._tasks:
                raise ValueError(f"Task '{task_name}' is already registered")
            self._tasks[task_name] = task_class
            print(f"Registered task: {task_name} (v{task_class.get_version()})")
    
    def get_task(self, task_name: str) -> Optional[Type[BaseTask]]:
        """
        Get a task class by name.
        
        Args:
            task_name: Name of the task
        
        Returns:
            Task class or None if not found
        """
        with self._lock_tasks:
            return self._tasks.get(task_name)
    
    def list_tasks(self) -> List[str]:
        """
        List all registered task names.
        
        Returns:
            List of task names
        """
        with self._lock_tasks:
            return list(self._tasks.keys())
    
    def get_task_metadata(self, task_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific task.
        
        Args:
            task_name: Name of the task
        
        Returns:
            Task metadata dictionary or None if not found
        """
        task_class = self.get_task(task_name)
        if task_class is None:
            return None
        return task_class.get_metadata()
    
    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """
        Get metadata for all registered tasks.
        
        Returns:
            List of task metadata dictionaries
        """
        with self._lock_tasks:
            return [task_class.get_metadata() for task_class in self._tasks.values()]
    
    def get_pipeline_schema(self, task_names: List[str]) -> Dict[str, Any]:
        """
        Get combined input schema for a pipeline of tasks.
        
        This aggregates all required inputs across all tasks in the pipeline.
        
        Args:
            task_names: List of task names in the pipeline
        
        Returns:
            Combined JSON schema
        
        Raises:
            ValueError: If any task is not found
        """
        combined_properties = {}
        combined_required = []
        
        for task_name in task_names:
            task_class = self.get_task(task_name)
            if task_class is None:
                raise ValueError(f"Task '{task_name}' not found")
            
            schema = task_class.get_input_schema()
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            # Merge properties (later tasks override earlier ones if conflicts)
            for prop_name, prop_schema in properties.items():
                if prop_name not in combined_properties:
                    combined_properties[prop_name] = prop_schema
                    if prop_name in required:
                        combined_required.append(prop_name)
        
        return {
            "type": "object",
            "properties": combined_properties,
            "required": combined_required,
        }
    
    def clear(self) -> None:
        """Clear all registered tasks (primarily for testing)."""
        with self._lock_tasks:
            self._tasks.clear()


# Global registry instance
_registry: Optional[TaskRegistry] = None


def get_task_registry() -> TaskRegistry:
    """Get the global task registry."""
    global _registry
    if _registry is None:
        _registry = TaskRegistry()
    return _registry


# Decorator for easy task registration
def register_task(task_class: Type[BaseTask]) -> Type[BaseTask]:
    """
    Decorator to register a task class.
    
    Usage:
    ```python
    @register_task
    class MyTask(BaseTask):
        ...
    ```
    """
    get_task_registry().register(task_class)
    return task_class
