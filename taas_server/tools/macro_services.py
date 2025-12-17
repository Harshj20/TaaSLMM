"""Macro services - Main ML operations (finetune, train, etc.)."""

from typing import Dict, Any, List
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

from taas_server.tasks.task_registry import get_task_registry
from taas_server.tasks.base_task import TaskType


def register_macro_services(server: Server):
    """Register macro service tools (MacroTasks)."""
    
    registry = get_task_registry()
    
    # Get all macro tasks
    macro_tasks = registry.list_tasks(task_type=TaskType.MACROTASK)
    
    @server.list_tools()
    async def list_macro_tools() -> List[Tool]:
        """List macro service tools."""
        tools = []
        
        for task_name in macro_tasks:
            metadata = registry.get_task_metadata(task_name)
            if metadata:
                tool = Tool(
                    name=f"macro_{metadata['name']}",
                    description=f"[MACRO] {metadata['description']}",
                    inputSchema=metadata["input_schema"]
                )
                tools.append(tool)
        
        return tools
    
    @server.call_tool()
    async def call_macro_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a macro service."""
        # Remove 'macro_' prefix
        task_name = name.replace("macro_", "", 1)
        
        task_class = registry.get_task(task_name)
        if not task_class or task_class.get_task_type() != TaskType.MACROTASK:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Macro task '{task_name}' not found"})
            )]
        
        try:
            # Execute in isolated environment (MacroTasks require isolation)
            task_instance = task_class()
            outputs = await task_instance.run(arguments)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "COMPLETED",
                    "task": task_name,
                    "type": "MACROTASK",
                    "requires_isolation": True,
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


# Available macro services:
# - finetune: Finetune a language model
# - train: Full training from scratch
# - ptq: Post-Training Quantization
# - qat: Quantization-Aware Training (to be implemented)
# - evaluate: Model evaluation
