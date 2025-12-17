"""Admin services - Management and metadata operations."""

from typing import Dict, Any, List
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

from taas_server.tasks.task_registry import get_task_registry
from taas_server.tasks.base_task import TaskType
from taas_server.db.database import get_db_manager
from taas_server.db.models import Task, TaskStatusEnum
from taas_server.core.state_manager import get_state_manager


def register_admin_services(server: Server):
    """Register admin service tools."""
    
    registry = get_task_registry()
    db_manager = get_db_manager()
    state_manager = get_state_manager()
    
    @server.list_tools()
    async def list_admin_tools() -> List[Tool]:
        """List admin service tools."""
        return [
            Tool(
                name="admin_list_tasks",
                description="List all available tasks, optionally filtered by type",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_type": {
                            "type": "string",
                            "enum": ["MICROSERVICE", "MACROTASK", "PIPELINE", "MANAGERIAL"],
                            "description": "Filter by task type (optional)"
                        }
                    }
                }
            ),
            Tool(
                name="admin_get_task_info",
                description="Get detailed information about a specific task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_name": {
                            "type": "string",
                            "description": "Name of the task"
                        }
                    },
                    "required": ["task_name"]
                }
            ),
            Tool(
                name="admin_get_task_schema",
                description="Get combined input schema for a task (pipeline or standalone)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_name": {"type": "string"},
                        "as_pipeline": {
                            "type": "boolean",
                            "description": "Get pipeline schema (with dependencies)",
                            "default": False
                        }
                    },
                    "required": ["task_name"]
                }
            ),
            Tool(
                name="admin_get_status",
                description="Get execution status of a task by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task execution ID"
                        }
                    },
                    "required": ["task_id"]
                }
            ),
            Tool(
                name="admin_get_system_status",
                description="Get overall system status and metrics",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="admin_list_executions",
                description="List recent task executions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10
                        },
                        "status": {
                            "type": "string",
                            "enum": ["PENDING", "RUNNING", "COMPLETED", "FAILED"],
                            "description": "Filter by status (optional)"
                        }
                    }
                }
            )
        ]
    
    @server.call_tool()
    async def call_admin_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute an admin service."""
        try:
            if name == "admin_list_tasks":
                # List tasks
                task_type_str = arguments.get("task_type")
                task_type = TaskType(task_type_str) if task_type_str else None
                
                task_names = registry.list_tasks(task_type=task_type)
                tasks_info = []
                
                for task_name in task_names:
                    metadata = registry.get_task_metadata(task_name)
                    if metadata:
                        tasks_info.append({
                            "name": metadata["name"],
                            "description": metadata["description"],
                            "type": metadata["task_type"],
                            "version": metadata["version"]
                        })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "SUCCESS",
                        "count": len(tasks_info),
                        "filter": task_type_str or "ALL",
                        "tasks": tasks_info
                    }, indent=2)
                )]
            
            elif name == "admin_get_task_info":
                # Get task info
                task_name = arguments["task_name"]
                metadata = registry.get_task_metadata(task_name)
                
                if not metadata:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": f"Task '{task_name}' not found"})
                    )]
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "SUCCESS",
                        "task": metadata
                    }, indent=2)
                )]
            
            elif name == "admin_get_task_schema":
                # Get task schema
                task_name = arguments["task_name"]
                as_pipeline = arguments.get("as_pipeline", False)
                
                schema = registry.get_combined_input_schema(task_name, as_pipeline=as_pipeline)
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "SUCCESS",
                        "task": task_name,
                        "mode": "PIPELINE" if as_pipeline else "STANDALONE",
                        "schema": schema
                    }, indent=2)
                )]
            
            elif name == "admin_get_status":
                # Get task execution status
                task_id = arguments["task_id"]
                
                with db_manager.get_session() as session:
                    task = session.query(Task).filter_by(id=task_id).first()
                    
                    if not task:
                        return [TextContent(
                            type="text",
                            text=json.dumps({"error": f"Task ID '{task_id}' not found"})
                        )]
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "status": "SUCCESS",
                            "task_id": task.id,
                            "task_name": task.task_name,
                            "status": task.status.value,
                            "progress": task.progress,
                            "error": task.error_message
                        }, indent=2)
                    )]
            
            elif name == "admin_get_system_status":
                # Get system status
                status = state_manager.get_system_status()
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "SUCCESS",
                        "system": status
                    }, indent=2)
                )]
            
            elif name == "admin_list_executions":
                # List recent executions
                limit = arguments.get("limit", 10)
                status_filter = arguments.get("status")
                
                with db_manager.get_session() as session:
                    query = session.query(Task)
                    
                    if status_filter:
                        query = query.filter_by(status=TaskStatusEnum(status_filter))
                    
                    tasks = query.order_by(Task.created_at.desc()).limit(limit).all()
                    
                    executions = []
                    for task in tasks:
                        executions.append({
                            "id": task.id,
                            "name": task.task_name,
                            "status": task.status.value,
                            "created_at": task.created_at.isoformat(),
                            "progress": task.progress
                        })
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "status": "SUCCESS",
                            "count": len(executions),
                            "executions": executions
                        }, indent=2)
                    )]
            
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown admin tool: {name}"})
                )]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "status": "FAILED",
                    "tool": name
                })
            )]
