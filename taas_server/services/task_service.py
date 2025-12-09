"""Task service gRPC implementation."""

import uuid
import json
from datetime import datetime
from typing import Optional

import grpc
from taas_server.generated import taas_pb2, taas_pb2_grpc
from taas_server.tasks import get_task_registry
from taas_server.db.database import get_db_manager
from taas_server.db.models import Task, TaskStatusEnum, TaskDefinitionModel
from taas_server.core import get_state_manager


class TaskServiceServicer(taas_pb2_grpc.TaskServiceServicer):
    """gRPC service for task execution."""
    
    async def SubmitTask(
        self,
        request: taas_pb2.TaskRequest,
        context: grpc.ServicerContext
    ) -> taas_pb2.TaskResponse:
        """Submit a single task for execution."""
        try:
            # Get task registry
            registry = get_task_registry()
            task_class = registry.get_task(request.task_name)
            
            if task_class is None:
                return taas_pb2.TaskResponse(
                    task_id="",
                    status=taas_pb2.UNKNOWN,
                    message=f"Task '{request.task_name}' not found"
                )
            
            # Parse inputs
            inputs = {k: json.loads(v) if v else None for k, v in request.inputs.items()}
            
            # Validate inputs
            task_instance = task_class()
            is_valid, error_msg = task_instance.validate_inputs(inputs)
            
           if not is_valid:
                return taas_pb2.TaskResponse(
                    task_id="",
                    status=taas_pb2.FAILED,
                    message=f"Input validation failed: {error_msg}"
                )
            
            # Create task record in database
            task_id = str(uuid.uuid4())
            db_manager = get_db_manager()
            
            with db_manager.get_session() as session:
                db_task = Task(
                    id=task_id,
                    task_name=request.task_name,
                    status=TaskStatusEnum.QUEUED,
                    user_id=request.user_id or "anonymous",
                    inputs=inputs,
                    metadata=dict(request.metadata) if request.metadata else {}
                )
                session.add(db_task)
            
            # Add to state manager
            state_manager = get_state_manager()
            state_manager.add_task(task_id, {
                "task_name": request.task_name,
                "status": "QUEUED",
                "progress": 0.0
            })
            
            # TODO: Queue for async execution via Celery
            # For now, just return queued status
            
            return taas_pb2.TaskResponse(
                task_id=task_id,
                status=taas_pb2.QUEUED,
                message="Task queued for execution"
            )
            
        except Exception as e:
            return taas_pb2.TaskResponse(
                task_id="",
                status=taas_pb2.FAILED,
                message=f"Error submitting task: {str(e)}"
            )
    
    async def GetTaskStatus(
        self,
        request: taas_pb2.TaskStatusRequest,
        context: grpc.ServicerContext
    ) -> taas_pb2.TaskStatus:
        """Get status of a task."""
        try:
            db_manager = get_db_manager()
            
            with db_manager.get_session() as session:
                db_task = session.query(Task).filter_by(id=request.task_id).first()
                
                if db_task is None:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"Task {request.task_id} not found")
                    return taas_pb2.TaskStatus()
                
                # Map status
                status_map = {
                    TaskStatusEnum.PENDING: taas_pb2.PENDING,
                    TaskStatusEnum.QUEUED: taas_pb2.QUEUED,
                    TaskStatusEnum.RUNNING: taas_pb2.RUNNING,
                    TaskStatusEnum.COMPLETED: taas_pb2.COMPLETED,
                    TaskStatusEnum.FAILED: taas_pb2.FAILED,
                    TaskStatusEnum.CANCELLED: taas_pb2.CANCELLED,
                }
                
                return taas_pb2.TaskStatus(
                    task_id=db_task.id,
                    task_name=db_task.task_name,
                    status=status_map.get(db_task.status, taas_pb2.UNKNOWN),
                    inputs={k: json.dumps(v) for k, v in (db_task.inputs or {}).items()},
                    outputs={k: json.dumps(v) for k, v in (db_task.outputs or {}).items()},
                    error_message=db_task.error_message or "",
                    created_at=int(db_task.created_at.timestamp()),
                    updated_at=int(db_task.updated_at.timestamp()),
                    started_at=int(db_task.started_at.timestamp()) if db_task.started_at else 0,
                    completed_at=int(db_task.completed_at.timestamp()) if db_task.completed_at else 0,
                    progress=db_task.progress,
                )
                
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting task status: {str(e)}")
            return taas_pb2.TaskStatus()
    
    async def ListTasks(
        self,
        request: taas_pb2.ListTasksRequest,
        context: grpc.ServicerContext
    ) -> taas_pb2.ListTasksResponse:
        """List all available tasks."""
        try:
            registry = get_task_registry()
            all_metadata = registry.get_all_metadata()
            
            task_definitions = []
            for metadata in all_metadata:
                task_def = taas_pb2.TaskDefinition(
                    name=metadata["name"],
                    description=metadata["description"],
                    version=metadata["version"],
                    input_schema=json.dumps(metadata["input_schema"]),
                    output_schema=json.dumps(metadata["output_schema"]),
                    dependencies=metadata.get("dependencies", []),
                )
                task_definitions.append(task_def)
            
            return taas_pb2.ListTasksResponse(tasks=task_definitions)
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error listing tasks: {str(e)}")
            return taas_pb2.ListTasksResponse()
    
    async def GetTaskInfo(
        self,
        request: taas_pb2.TaskInfoRequest,
        context: grpc.ServicerContext
    ) -> taas_pb2.TaskDefinition:
        """Get detailed information about a specific task."""
        try:
            registry = get_task_registry()
            metadata = registry.get_task_metadata(request.task_name)
            
            if metadata is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Task '{request.task_name}' not found")
                return taas_pb2.TaskDefinition()
            
            return taas_pb2.TaskDefinition(
                name=metadata["name"],
                description=metadata["description"],
                version=metadata["version"],
                input_schema=json.dumps(metadata["input_schema"]),
                output_schema=json.dumps(metadata["output_schema"]),
                dependencies=metadata.get("dependencies", []),
            )
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting task info: {str(e)}")
            return taas_pb2.TaskDefinition()
    
    async def ExecutePipeline(
        self,
        request: taas_pb2.PipelineRequest,
        context: grpc.ServicerContext
    ) -> taas_pb2.PipelineResponse:
        """Execute a pipeline of tasks."""
        # For now, return a simple implementation
        # TODO: Implement full pipeline orchestration
        return taas_pb2.PipelineResponse(
            pipeline_id=str(uuid.uuid4()),
            task_ids=[],
            status=taas_pb2.PENDING,
            message="Pipeline execution not yet implemented"
        )
    
    async def CancelTask(
        self,
        request: taas_pb2.CancelTaskRequest,
        context: grpc.ServicerContext
    ) -> taas_pb2.CancelTaskResponse:
        """Cancel a running task."""
        # TODO: Implement task cancellation
        return taas_pb2.CancelTaskResponse(
            success=False,
            message="Task cancellation not yet implemented"
        )
