"""MCP Inspector - Interactive debugger for MCP server."""

import asyncio
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.json import JSON
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn

from mcp_framework.client.mcp_client import MCPClient

console = Console()


class MCPInspector:
    """Interactive inspector/debugger for MCP server."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize inspector."""
        self.base_url = base_url
        self.client: Optional[MCPClient] = None
        self.current_tools = []
    
    async def start(self):
        """Start inspector session."""
        self.client = MCPClient(self.base_url)
        
        console.print(Panel.fit(
            "[bold cyan]MCP Inspector[/bold cyan]\n"
            f"Connected to: {self.base_url}",
            border_style="cyan"
        ))
        
        # Test connection
        try:
            health = await self.client.health_check()
            console.print(f"[green]✓ Server is healthy: {health['status']}[/green]\n")
        except Exception as e:
            console.print(f"[red]✗ Failed to connect: {e}[/red]")
            return
        
        # Main menu loop
        while True:
            choice = await self.show_menu()
            
            if choice == "1":
                await self.inspect_tools()
            elif choice == "2":
                await self.call_tool_interactive()
            elif choice == "3":
                await self.execute_workflow_interactive()
            elif choice == "4":
                await self.query_workflow_status()
            elif choice == "5":
                await self.run_quick_test()
            elif choice == "6":
                console.print("[yellow]Exiting...[/yellow]")
                break
            else:
                console.print("[red]Invalid choice[/red]")
        
        await self.client.close()
    
    async def show_menu(self) -> str:
        """Show main menu and get choice."""
        console.print("\n[bold]MCP Inspector Menu[/bold]")
        console.print("1. Inspect Tools")
        console.print("2. Call Tool")
        console.print("3. Execute Workflow")
        console.print("4. Query Workflow Status")
        console.print("5. Run Quick Test")
        console.print("6. Exit")
        
        return Prompt.ask("\nChoice", choices=["1", "2", "3", "4", "5", "6"])
    
    async def inspect_tools(self):
        """Inspect available tools."""
        console.print("\n[bold cyan]Tool Inspection[/bold cyan]")
        
        # Get category filter
        category = Prompt.ask(
            "Filter by category (or press Enter for all)",
            choices=["", "UTILITY", "TRAINING", "ADMIN"],
            default=""
        )
        
        with console.status("[bold green]Fetching tools..."):
            tools_response = await self.client.list_tools(category if category else None)
        
        self.current_tools = tools_response['tools']
        
        # Create table
        table = Table(title=f"Available Tools ({tools_response['count']} total)")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Name", style="green")
        table.add_column("Category", style="yellow")
        table.add_column("Description", style="white")
        table.add_column("Requires Isolation", style="magenta")
        
        for idx, tool in enumerate(self.current_tools, 1):
            table.add_row(
                str(idx),
                tool['name'],
                tool['category'],
                tool['description'][:50] + "..." if len(tool['description']) > 50 else tool['description'],
                "Yes" if tool['requiresIsolation'] else "No"
            )
        
        console.print(table)
        
        # Option to view details
        if Confirm.ask("\nView tool details?", default=False):
            tool_idx = int(Prompt.ask("Tool number")) - 1
            if 0 <= tool_idx < len(self.current_tools):
                tool = self.current_tools[tool_idx]
                console.print(Panel(
                    JSON(json.dumps(tool, indent=2)),
                    title=f"[bold]{tool['name']}[/bold]",
                    border_style="green"
                ))
    
    async def call_tool_interactive(self):
        """Interactively call a tool."""
        console.print("\n[bold cyan]Call Tool[/bold cyan]")
        
        # Get tool list if not cached
        if not self.current_tools:
            tools_response = await self.client.list_tools()
            self.current_tools = tools_response['tools']
        
        # Show tools
        for idx, tool in enumerate(self.current_tools, 1):
            console.print(f"{idx}. [green]{tool['name']}[/green]")
        
        tool_idx = int(Prompt.ask("Select tool")) - 1
        if not (0 <= tool_idx < len(self.current_tools)):
            console.print("[red]Invalid selection[/red]")
            return
        
        tool = self.current_tools[tool_idx]
        console.print(f"\n[bold]Selected: {tool['name']}[/bold]")
        console.print("Input Schema:")
        console.print(JSON(json.dumps(tool['inputSchema'], indent=2)))
        
        # Get arguments
        console.print("\n[yellow]Enter arguments as JSON:[/yellow]")
        args_str = Prompt.ask("Arguments", default="{}")
        
        try:
            arguments = json.loads(args_str)
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON[/red]")
            return
        
        # Call tool
        with console.status(f"[bold green]Calling {tool['name']}..."):
            result = await self.client.call_tool(tool['name'], arguments)
        
        # Show result
        console.print(Panel(
            JSON(json.dumps(result, indent=2)),
            title="[bold green]Result[/bold green]",
            border_style="green"
        ))
    
    async def execute_workflow_interactive(self):
        """Interactively execute a workflow."""
        console.print("\n[bold cyan]Execute Workflow[/bold cyan]")
        
        # Example DAG templates
        console.print("\n[bold]Workflow Templates:[/bold]")
        console.print("1. Simple (single node)")
        console.print("2. Parallel (two independent nodes)")
        console.print("3. Custom (enter JSON)")
        
        choice = Prompt.ask("Template", choices=["1", "2", "3"])
        
        if choice == "1":
            dag = {
                "nodes": [
                    {
                        "id": "node1",
                        "tool": "load_dataset",
                        "inputs": {"dataset_path": "test/data"},
                        "input_mappings": {}
                    }
                ],
                "edges": []
            }
        elif choice == "2":
            dag = {
                "nodes": [
                    {
                        "id": "dataset",
                        "tool": "load_dataset",
                        "inputs": {"dataset_path": "test/data"},
                        "input_mappings": {}
                    },
                    {
                        "id": "config",
                        "tool": "load_config",
                        "inputs": {"config": {"model": "test"}},
                        "input_mappings": {}
                    }
                ],
                "edges": []
            }
        else:
            dag_str = Prompt.ask("Enter DAG JSON")
            try:
                dag = json.loads(dag_str)
            except json.JSONDecodeError:
                console.print("[red]Invalid JSON[/red]")
                return
        
        console.print("\n[bold]Workflow DAG:[/bold]")
        console.print(JSON(json.dumps(dag, indent=2)))
        
        if not Confirm.ask("\nExecute this workflow?", default=True):
            return
        
        # Execute with progress
        console.print("\n[bold green]Executing workflow...[/bold green]")
        
        workflow_id = None
        total_nodes = 0
        completed = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Starting...", total=None)
            
            async for event in self.client.execute_workflow_streaming(dag):
                event_type = event.get("type")
                
                if event_type == "start":
                    workflow_id = event['workflow_id']
                    total_nodes = event['total_nodes']
                    progress.update(task, description=f"Workflow {workflow_id[:8]}...", total=total_nodes)
                
                elif event_type == "node_completed":
                    completed += 1
                    progress.update(
                        task,
                        completed=completed,
                        description=f"[green]Completed: {event['node_id']}[/green]"
                    )
                    console.print(f"  Result: {event.get('result', {})}")
                
                elif event_type == "workflow_completed":
                    progress.update(task, description="[bold green]✓ Workflow completed![/bold green]")
                    console.print(Panel(
                        JSON(json.dumps(event.get('results', {}), indent=2)),
                        title="Final Results",
                        border_style="green"
                    ))
                
                elif event_type == "node_failed":
                    progress.update(task, description=f"[red]✗ Failed: {event['node_id']}[/red]")
                    console.print(f"[red]Error: {event.get('error')}[/red]")
                
                elif event_type == "complete":
                    break
    
    async def query_workflow_status(self):
        """Query workflow status by ID."""
        console.print("\n[bold cyan]Query Workflow Status[/bold cyan]")
        
        workflow_id = Prompt.ask("Workflow ID")
        
        try:
            with console.status("[bold green]Fetching status..."):
                status = await self.client.get_workflow_status(workflow_id)
            
            console.print(Panel(
                JSON(json.dumps(status, indent=2)),
                title=f"Workflow {workflow_id[:8]}...",
                border_style="cyan"
            ))
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    async def run_quick_test(self):
        """Run quick test suite."""
        console.print("\n[bold cyan]Quick Test Suite[/bold cyan]\n")
        
        tests_passed = 0
        tests_total = 0
        
        # Test 1: Health check
        tests_total += 1
        try:
            health = await self.client.health_check()
            if health.get("status") == "healthy":
                console.print("[green]✓ Health check passed[/green]")
                tests_passed += 1
            else:
                console.print("[red]✗ Health check failed[/red]")
        except Exception as e:
            console.print(f"[red]✗ Health check error: {e}[/red]")
        
        # Test 2: List tools
        tests_total += 1
        try:
            tools = await self.client.list_tools()
            if tools.get("count", 0) > 0:
                console.print(f"[green]✓ List tools passed ({tools['count']} tools)[/green]")
                tests_passed += 1
            else:
                console.print("[yellow]⚠ No tools registered[/yellow]")
        except Exception as e:
            console.print(f"[red]✗ List tools error: {e}[/red]")
        
        # Test 3: Call tool
        tests_total += 1
        try:
            result = await self.client.call_tool(
                "load_dataset",
                {"dataset_path": "test"}
            )
            if result.get("status") == "COMPLETED":
                console.print("[green]✓ Tool call passed[/green]")
                tests_passed += 1
            else:
                console.print(f"[yellow]⚠ Tool call status: {result.get('status')}[/yellow]")
        except Exception as e:
            console.print(f"[red]✗ Tool call error: {e}[/red]")
        
        # Summary
        console.print(f"\n[bold]Test Results: {tests_passed}/{tests_total} passed[/bold]")
        if tests_passed == tests_total:
            console.print("[bold green]All tests passed! ✓[/bold green]")
        else:
            console.print(f"[bold yellow]{tests_total - tests_passed} test(s) failed[/bold yellow]")


async def main():
    """Run MCP inspector."""
    inspector = MCPInspector()
    await inspector.start()


if __name__ == "__main__":
    asyncio.run(main())
