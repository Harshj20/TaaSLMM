"""Python client SDK for TaaS server."""

import json
from typing import Dict, Any, Optional, List

import grpc
from taas_server.generated import taas_pb2, taas_pb2_grpc


class TaasClient:
    """High-level Python client for TaaS server."""
    
    def __init__(self, host: str = "localhost", port: int = 50051):
        """
        Initialize the client.
        
        Args:
            host: Server hostname
            port: Server port
        """
        self.address = f"{host}:{port}"
        self.channel: Optional[grpc.aio.Channel] = None
        self.task_stub: Optional[taas_pb2_grpc.TaskServiceStub] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def connect(self) -> None:
        """Connect to the TaaS server."""
        self.channel = grpc.aio.insecure_channel(self.address)
        self.task_stub = taas_pb2_grpc.TaskServiceStub(self.channel)
    
    async def close(self) -> None:
        """Close the connection."""
        if self.channel:
            await self.channel.close()
    
    async def submit_task(
        self,
        task_name: str,
        inputs: Dict[str, Any],
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Submit a task for execution.
        
        Args:
            task_name: Name of the task to execute
            inputs: Task input parameters
            user_id: Optional user identifier
            metadata: Optional metadata
        
        Returns:
            Dictionary with task_id, status, and message
        """
        if self.task_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        # Convert inputs to JSON strings
        json_inputs = {k: json.dumps(v) for k, v in inputs.items()}
        
        request = taas_pb2.TaskRequest(
            task_name=task_name,
            inputs=json_inputs,
            user_id=user_id or "anonymous",
            metadata=metadata or {}
        )
        
        response = await self.task_stub.SubmitTask(request)
        
        # Map status enum to string
        status_names = {
            taas_pb2.PENDING: "PENDING",
            taas_pb2.QUEUED: "QUEUED",
            taas_pb2.RUNNING: "RUNNING",
            taas_pb2.COMPLETED: "COMPLETED",
            taas_pb2.FAILED: "FAILED",
            taas_pb2.CANCELLED: "CANCELLED",
        }
        
        return {
            "task_id": response.task_id,
            "status": status_names.get(response.status, "UNKNOWN"),
            "message": response.message
        }
    
    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get task status.
        
        Args:
            task_id: Task ID
        
        Returns:
            Task status dictionary
        """
        if self.task_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        request = taas_pb2.TaskStatusRequest(task_id=task_id)
        response = await self.task_stub.GetTaskStatus(request)
        
        # Map status enum
        status_names = {
            taas_pb2.PENDING: "PENDING",
            taas_pb2.QUEUED: "QUEUED",
            taas_pb2.RUNNING: "RUNNING",
            taas_pb2.COMPLETED: "COMPLETED",
            taas_pb2.FAILED: "FAILED",
            taas_pb2.CANCELLED: "CANCELLED",
        }
        
        return {
            "task_id": response.task_id,
            "task_name": response.task_name,
            "status": status_names.get(response.status, "UNKNOWN"),
            "inputs": {k: json.loads(v) for k, v in response.inputs.items()} if response.inputs else {},
            "outputs": {k: json.loads(v) for k, v in response.outputs.items()} if response.outputs else {},
            "error_message": response.error_message,
            "progress": response.progress,
            "created_at": response.created_at,
            "updated_at": response.updated_at,
        }
    
    async def list_tasks(self) -> List[Dict[str, Any]]:
        """
        List all available tasks.
        
        Returns:
            List of task definitions
        """
        if self.task_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        request = taas_pb2.ListTasksRequest()
        response = await self.task_stub.ListTasks(request)
        
        tasks = []
        for task_def in response.tasks:
            tasks.append({
                "name": task_def.name,
                "description": task_def.description,
                "version": task_def.version,
                "input_schema": json.loads(task_def.input_schema) if task_def.input_schema else {},
                "output_schema": json.loads(task_def.output_schema) if task_def.output_schema else {},
                "dependencies": list(task_def.dependencies),
            })
        
        return tasks
    
    async def get_task_info(self, task_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed task information.
        
        Args:
            task_name: Name of the task
        
        Returns:
            Task definition or None if not found
        """
        if self.task_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        request = taas_pb2.TaskInfoRequest(task_name=task_name)
        
        try:
            response = await self.task_stub.GetTaskInfo(request)
            
            return {
                "name": response.name,
                "description": response.description,
                "version": response.version,
                "input_schema": json.loads(response.input_schema) if response.input_schema else {},
                "output_schema": json.loads(response.output_schema) if response.output_schema else {},
                "dependencies": list(response.dependencies),
            }
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            raise
