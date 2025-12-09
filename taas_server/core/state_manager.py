"""State manager for session recovery and state persistence."""

import threading
import time
from typing import Dict, Optional, Any
from datetime import datetime

from taas_server.db.database import get_db_manager
from taas_server.db.models import Task, Pipeline, TaskStatusEnum


class StateManager:
    """Thread-safe singleton state manager for crash recovery and session persistence."""
    
    _instance: Optional["StateManager"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "StateManager":
        """Create or return singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize state manager."""
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        # In-memory cache of active tasks
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._active_pipelines: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
        # Checkpoint interval (seconds)
        self._checkpoint_interval = 30
        self._last_checkpoint = time.time()
        
        self._initialized = True
    
    def add_task(self, task_id: str, task_info: Dict[str, Any]) -> None:
        """Add a task to active tracking."""
        with self._lock:
            self._active_tasks[task_id] = {
                **task_info,
                "last_updated": datetime.utcnow()
            }
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> None:
        """Update task information."""
        with self._lock:
            if task_id in self._active_tasks:
                self._active_tasks[task_id].update(updates)
                self._active_tasks[task_id]["last_updated"] = datetime.utcnow()
   
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task information from cache."""
        with self._lock:
            return self._active_tasks.get(task_id)
    
    def remove_task(self, task_id: str) -> None:
        """Remove task from active tracking."""
        with self._lock:
            self._active_tasks.pop(task_id, None)
    
    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all active tasks."""
        with self._lock:
            return self._active_tasks.copy()
    
    def add_pipeline(self, pipeline_id: str, pipeline_info: Dict[str, Any]) -> None:
        """Add a pipeline to active tracking."""
        with self._lock:
            self._active_pipelines[pipeline_id] = {
                **pipeline_info,
                "last_updated": datetime.utcnow()
            }
    
    def update_pipeline(self, pipeline_id: str, updates: Dict[str, Any]) -> None:
        """Update pipeline information."""
        with self._lock:
            if pipeline_id in self._active_pipelines:
                self._active_pipelines[pipeline_id].update(updates)
                self._active_pipelines[pipeline_id]["last_updated"] = datetime.utcnow()
    
    def get_pipeline(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get pipeline information from cache."""
        with self._lock:
            return self._active_pipelines.get(pipeline_id)
    
    def checkpoint(self) -> None:
        """Synchronize in-memory state to database."""
        current_time = time.time()
        if current_time - self._last_checkpoint < self._checkpoint_interval:
            return
        
        db_manager = get_db_manager()
        
        with self._lock:
            with db_manager.get_session() as session:
                # Update all active tasks
                for task_id, task_info in self._active_tasks.items():
                    task = session.query(Task).filter_by(id=task_id).first()
                    if task:
                        task.status = TaskStatusEnum(task_info.get("status", "PENDING"))
                        task.progress = task_info.get("progress", 0.0)
                        task.updated_at = datetime.utcnow()
                
                # Update all active pipelines
                for pipeline_id, pipeline_info in self._active_pipelines.items():
                    pipeline = session.query(Pipeline).filter_by(id=pipeline_id).first()
                    if pipeline:
                        pipeline.status = TaskStatusEnum(pipeline_info.get("status", "PENDING"))
                        pipeline.updated_at = datetime.utcnow()
        
        self._last_checkpoint = current_time
    
    def recover_from_last_session(self) -> None:
        """Recover state from database after crash/restart."""
        db_manager = get_db_manager()
        
        with db_manager.get_session() as session:
            # Find all tasks that were running when server stopped
            running_tasks = session.query(Task).filter(
                Task.status.in_([TaskStatusEnum.RUNNING, TaskStatusEnum.QUEUED])
            ).all()
            
            for task in running_tasks:
                # Mark as PENDING for restart or FAILED depending on policy
                task.status = TaskStatusEnum.PENDING
                task.error_message = "Task interrupted by server restart"
                
                # Add to active tracking
                self._active_tasks[task.id] = {
                    "task_name": task.task_name,
                    "status": "PENDING",
                    "progress": task.progress,
                    "last_updated": datetime.utcnow()
                }
            
            # Find all pipelines that were running
            running_pipelines = session.query(Pipeline).filter(
                Pipeline.status.in_([TaskStatusEnum.RUNNING, TaskStatusEnum.QUEUED])
            ).all()
            
            for pipeline in running_pipelines:
                pipeline.status = TaskStatusEnum.PENDING
                
                self._active_pipelines[pipeline.id] = {
                    "pipeline_name": pipeline.pipeline_name,
                    "status": "PENDING",
                    "task_ids": pipeline.task_ids,
                    "last_updated": datetime.utcnow()
                }
        
        print(f"Recovered {len(running_tasks)} tasks and {len(running_pipelines)} pipelines from last session")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system-wide status."""
        db_manager = get_db_manager()
        
        with db_manager.get_session() as session:
            total_tasks = session.query(Task).count()
            completed_tasks = session.query(Task).filter_by(status=TaskStatusEnum.COMPLETED).count()
            failed_tasks = session.query(Task).filter_by(status=TaskStatusEnum.FAILED).count()
            
            with self._lock:
                active_count = len(self._active_tasks)
        
        return {
            "total_tasks": total_tasks,
            "active_tasks": active_count,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "uptime": int(time.time() - self._last_checkpoint),
        }


# Global state manager
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get the global state manager."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
