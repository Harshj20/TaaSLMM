"""Example: Using MCP client programmatically."""

import asyncio
from mcp_framework.client.mcp_client import MCPClient


async def example_client_usage():
    """Demonstrate programmatic client usage."""
    print("="*60)
    print("MCP Client - Programmatic Usage Example")
    print("="*60)
    
    async with MCPClient("http://localhost:8000") as client:
        # 1. Check server health
        print("\n1. Health Check")
        print("-"*60)
        health = await client.health_check()
        print(f"Status: {health['status']}")
        print(f"Service: {health['service']}")
        
        # 2. List all tools
        print("\n2. List All Tools")
        print("-"*60)
        tools_response = await client.list_tools()
        print(f"Total tools: {tools_response['count']}")
        for tool in tools_response['tools']:
            print(f"  - {tool['name']} ({tool['category']})")
        
        # 3. List tools by category
        print("\n3. List Utility Tools Only")
        print("-"*60)
        utility_tools = await client.list_tools(category="UTILITY")
        print(f"Utility tools: {utility_tools['count']}")
        for tool in utility_tools['tools']:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # 4. Call a tool
        print("\n4. Call load_dataset Tool")
        print("-"*60)
        result = await client.call_tool(
            "load_dataset",
            {"dataset_path": "huggingface:squad", "split": "train"}
        )
        print(f"Status: {result['status']}")
        print(f"Result: {result['result']}")
        
        # 5. Execute workflow with streaming
        print("\n5. Execute Workflow with Streaming")
        print("-"*60)
        
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
                    "inputs": {"config": {"model": "llama-2", "lr": 0.001}},
                    "input_mappings": {}
                }
            ],
            "edges": []
        }
        
        workflow_id = None
        async for event in client.execute_workflow_streaming(dag):
            event_type = event.get("type")
            
            if event_type == "start":
                workflow_id = event['workflow_id']
                print(f"Started workflow: {workflow_id[:8]}...")
                print(f"Total nodes: {event['total_nodes']}")
            
            elif event_type == "node_completed":
                node_id = event['node_id']
                progress = event['progress']
                print(f"  ✓ Completed: {node_id} ({progress:.0%})")
                print(f"    Result: {event['result']}")
            
            elif event_type == "workflow_completed":
                print("\n✓ Workflow completed successfully!")
                print(f"Final results: {event.get('results', {})}")
            
            elif event_type == "node_failed":
                print(f"\n✗ Node failed: {event['node_id']}")
                print(f"  Error: {event['error']}")
            
            elif event_type == "complete":
                break
        
        # 6. Query workflow status (if we got a workflow_id)
        if workflow_id:
            print("\n6. Query Workflow Status")
            print("-"*60)
            status = await client.get_workflow_status(workflow_id)
            print(f"Workflow ID: {workflow_id[:8]}...")
            print(f"Status: {status['status']}")
            print(f"Progress: {status['progress']:.0%}")
            if status.get('completed_at'):
                print(f"Completed at: {status['completed_at']}")
    
    print("\n" + "="*60)
    print("✓ Client demo completed!")
    print("="*60)


if __name__ == "__main__":
    print("\nNOTE: Make sure MCP server is running (uv run mcp-server)\n")
    asyncio.run(example_client_usage())
