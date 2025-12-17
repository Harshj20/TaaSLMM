"""Micro services - Utility operations (load_dataset, load_config, etc.)."""

from typing import Dict, Any, List
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

from taas_server.tasks.task_registry import get_task_registry
from taas_server.tasks.base_task import TaskType


def register_micro_services(server: Server):
    """Register micro service tools (Microservices)."""
    
    registry = get_task_registry()
    
    # Get all microservice tasks
    micro_tasks = registry.list_tasks(task_type=TaskType.MICROSERVICE)
    
    @server.list_tools()
    async def list_micro_tools() -> List[Tool]:
        """List micro service tools."""
        tools = []
        
        for task_name in micro_tasks:
            metadata = registry.get_task_metadata(task_name)
            if metadata:
                tool = Tool(
                    name=f"micro_{metadata['name']}",
                    description=f"[MICRO] {metadata['description']}",
                    inputSchema=metadata["input_schema"]
                )
                tools.append(tool)
        
        return tools
    
    @server.call_tool()
    async def call_micro_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a micro service."""
        # Remove 'micro_' prefix
        task_name = name.replace("micro_", "", 1)
        
        task_class = registry.get_task(task_name)
        if not task_class or task_class.get_task_type() != TaskType.MICROSERVICE:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Micro task '{task_name}' not found"})
            )]
        
        try:
            task_instance = task_class()
            outputs = await task_instance.run(arguments)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "COMPLETED",
                    "task": task_name,
                    "type": "MICROSERVICE",
                    "outputs": outputs
                }, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "status": "FAILED",
                    "task": task_name
                })
            )]


# Available micro services:
# - load_config: Load configuration from file or dict
# - create_config: Create a new configuration
# - load_dataset: Load dataset and return dataset_id
# - load_lora: Load LoRA adapter and return lora_id
# - create_env: Create isolated Python environment
