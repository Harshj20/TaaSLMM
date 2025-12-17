"""MCP Server for TaaS - Exposes tasks as MCP tools."""

import asyncio
import json
from typing import Any, Callable, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from taas_server.db.database import init_database
from taas_server.tasks.task_registry import get_task_registry
from taas_server.tasks.examples import config_tasks, microservice_tasks, macrotask_tasks
from taas_server.tasks.base_task import TaskType


class TaasMCPServer:
    """MCP Server exposing TaaS tasks as tools."""
    
    def __init__(self):
        """Initialize MCP server."""
        self.server = Server("taas-server")
        self.task_registry = get_task_registry()
        
        # Initialize database
        init_database("sqlite:///taas_mcp.db")
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP protocol handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools (tasks)."""
            tools = []
            
            # Get all registered tasks
            all_metadata = self.task_registry.get_all_metadata()
            
            for metadata in all_metadata:
                # Convert task to MCP tool
                tool = Tool(
                    name=metadata["name"],
                    description=metadata["description"],
                    inputSchema=metadata["input_schema"]
                )
                tools.append(tool)
            
            return tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Execute a task (tool call)."""
            try:
                # Get task class
                task_class = self.task_registry.get_task(name)
                
                if task_class is None:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Task '{name}' not found",
                            "status": "FAILED"
                        })
                    )]
                
                # Create and execute task
                task_instance = task_class()
                
                # Validate and execute
                outputs = await task_instance.run(arguments)
                
                # Return results
                result = {
                    "status": "COMPLETED",
                    "task_name": name,
                    "outputs": outputs
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "status": "FAILED",
                        "task_name": name
                    })
                )]
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point for MCP server."""
    server = TaasMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
