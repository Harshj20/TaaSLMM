"""MCP SSE Client for connecting to MCP Gateway."""

import asyncio
import httpx
import json
from typing import Dict, Any, Optional, AsyncIterator
from rich.console import Console
from rich.json import JSON

console = Console()


class MCPClient:
    """HTTP-SSE client for MCP Gateway."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize MCP client.
        
        Args:
            base_url: Base URL of MCP Gateway
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health."""
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    async def list_tools(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        List available tools.
        
        Args:
            category: Optional category filter (UTILITY, TRAINING, ADMIN)
        
        Returns:
            Dictionary with tools list
        """
        params = {}
        if category:
            params["category"] = category
        
        response = await self.client.get(f"{self.base_url}/mcp/tools", params=params)
        response.raise_for_status()
        return response.json()
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a single tool.
        
        Args:
            name: Tool name
            arguments: Tool arguments
        
        Returns:
            Tool execution result
        """
        response = await self.client.post(
            f"{self.base_url}/mcp/call",
            json={"name": name, "arguments": arguments}
        )
        response.raise_for_status()
        return response.json()
    
    async def execute_workflow_streaming(
        self,
        dag: Dict[str, Any],
        user_id: str = "test_user"
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute workflow with SSE streaming.
        
        Args:
            dag: Workflow DAG
            user_id: User identifier
        
        Yields:
            Progress events
        """
        async with self.client.stream(
            "POST",
            f"{self.base_url}/mcp/workflow",
            json={"dag": dag, "user_id": user_id},
            headers={"Accept": "text/event-stream"}
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    try:
                        event = json.loads(data)
                        yield event
                    except json.JSONDecodeError:
                        console.print(f"[yellow]Invalid JSON: {data}[/yellow]")
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow status.
        
        Args:
            workflow_id: Workflow execution ID
        
        Returns:
            Workflow status
        """
        response = await self.client.get(f"{self.base_url}/mcp/status/{workflow_id}")
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close client connection."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager enter."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


async def demo_client():
    """Demonstrate MCP client usage."""
    console.print("\n[bold cyan]MCP Client Demo[/bold cyan]\n")
    
    async with MCPClient() as client:
        # Health check
        console.print("[bold]1. Health Check[/bold]")
        health = await client.health_check()
        console.print(JSON(json.dumps(health)))
        
        # List tools
        console.print("\n[bold]2. List Tools[/bold]")
        tools_response = await client.list_tools()
        console.print(f"Found {tools_response['count']} tools:")
        for tool in tools_response['tools']:
            console.print(f"  • [green]{tool['name']}[/green] ({tool['category']})")
        
        # Call tool
        console.print("\n[bold]3. Call Tool[/bold]")
        result = await client.call_tool(
            "load_dataset",
            {"dataset_path": "huggingface:squad"}
        )
        console.print(JSON(json.dumps(result, indent=2)))
        
        # Execute workflow
        console.print("\n[bold]4. Execute Workflow (SSE)[/bold]")
        dag = {
            "nodes": [
                {
                    "id": "dataset",
                    "tool": "load_dataset",
                    "inputs": {"dataset_path": "test/data"},
                    "input_mappings": {}
                }
            ],
            "edges": []
        }
        
        async for event in client.execute_workflow_streaming(dag):
            event_type = event.get("type")
            if event_type == "start":
                console.print(f"[cyan]Started workflow: {event['workflow_id'][:8]}...[/cyan]")
            elif event_type == "node_completed":
                console.print(f"[green]✓ {event['node_id']} completed ({event['progress']:.0%})[/green]")
            elif event_type == "workflow_completed":
                console.print("[bold green]Workflow completed![/bold green]")
            elif event_type == "complete":
                break


if __name__ == "__main__":
    asyncio.run(demo_client())
