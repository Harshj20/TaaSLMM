"""Enhanced task registry with automatic schema resolution."""

import threading
from typing import Dict, Type, List, Optional, Any

from taas_server.tasks.base_task import BaseTask, TaskType


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
            print(f"Registered task: {task_name} (v{task_class.get_version()}, {task_class.get_task_type().value})")
    
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
    
    def list_tasks(self, task_type: Optional[TaskType] = None) -> List[str]:
        """
        List registered task names, optionally filtered by type.
        
        Args:
            task_type: Optional filter by task type
        
        Returns:
            List of task names
        """
        with self._lock_tasks:
            if task_type is None:
                return list(self._tasks.keys())
            return [
                name for name, cls in self._tasks.items()
                if cls.get_task_type() == task_type
            ]
    
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
    
    def get_combined_input_schema(self, task_name: str, as_pipeline: bool = True) -> Dict[str, Any]:
        """
        Get combined input schema for a task.
        
        If as_pipeline=True and task has dependencies:
            Returns merged schema of dependency inputs (for mini-pipeline execution)
            Example: finetune with deps [load_config, load_data] returns:
                {config: dict, data_path: str}
        
        If as_pipeline=False or no dependencies:
            Returns task's direct input schema
            Example: finetune returns {config_id: str, dataset_id: str}
        
        Args:
            task_name: Name of the task
            as_pipeline: Whether to compute pipeline schema
        
        Returns:
            Combined JSON schema
        
        Raises:
            ValueError: If task not found or circular dependencies detected
        """
        task_class = self.get_task(task_name)
        if task_class is None:
            raise ValueError(f"Task '{task_name}' not found")
        
        # If not pipeline mode or no dependencies, return direct schema
        dependencies = task_class.get_dependencies()
        if not as_pipeline or not dependencies:
            return task_class.get_input_schema()
        
        # Build combined schema from dependencies
        combined_properties = {}
        combined_required = []
        visited = set()
        
        def collect_schemas(dep_name: str, depth: int = 0):
            """Recursively collect schemas from dependencies."""
            if depth > 10:  # Prevent infinite recursion
                raise ValueError(f"Dependency chain too deep (possible cycle)")
            
            if dep_name in visited:
                return  # Already processed
            visited.add(dep_name)
            
            dep_class = self.get_task(dep_name)
            if dep_class is None:
                raise ValueError(f"Dependency task '{dep_name}' not found")
            
            # Process this task's dependencies first
            for sub_dep in dep_class.get_dependencies():
                collect_schemas(sub_dep, depth + 1)
            
            # Add this task's input schema
            schema = dep_class.get_input_schema()
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            for prop_name, prop_schema in properties.items():
                # Skip if this property is an output from another dependency
                # (it will be filled automatically by pipeline)
                if not self._is_output_from_dependency(prop_name, dependencies):
                    combined_properties[prop_name] = prop_schema
                    if prop_name in required and prop_name not in combined_required:
                        combined_required.append(prop_name)
        
        # Collect schemas from all dependencies
        for dep in dependencies:
            collect_schemas(dep)
        
        return {
            "type": "object",
            "properties": combined_properties,
            "required": combined_required,
        }
    
    def _is_output_from_dependency(self, param_name: str, dependencies: List[str]) -> bool:
        """Check if a parameter is an output from any dependency task."""
        for dep_name in dependencies:
            dep_class = self.get_task(dep_name)
            if dep_class is None:
                continue
            
            output_mappings = dep_class.get_output_mappings()
            if param_name in output_mappings.values():
                return True
        
        return False
    
    def get_pipeline_schema(self, task_names: List[str]) -> Dict[str, Any]:
        """
        Get combined input schema for a pipeline of tasks.
        
        This aggregates all required USER inputs across all tasks in the pipeline,
        excluding intermediate values that are passed between tasks.
        
        Args:
            task_names: List of task names in the pipeline
        
        Returns:
            Combined JSON schema for user inputs
        
        Raises:
            ValueError: If any task is not found
        """
        combined_properties = {}
        combined_required = []
        all_outputs = set()
        
        # First pass: collect all outputs from all tasks
        for task_name in task_names:
            task_class = self.get_task(task_name)
            if task_class is None:
                raise ValueError(f"Task '{task_name}' not found")
            
            output_mappings = task_class.get_output_mappings()
            all_outputs.update(output_mappings.values())
        
        # Second pass: collect inputs that are NOT outputs from other tasks
        for task_name in task_names:
            task_class = self.get_task(task_name)
            schema = task_class.get_input_schema()
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            for prop_name, prop_schema in properties.items():
                # Only include if it's not an output from another task
                if prop_name not in all_outputs:
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
