"""Example workflow demonstration."""

import asyncio
import json
from mcp_framework.server.mcp_gateway import app
from mcp_framework.server.workflow_executor import WorkflowExecutor
from mcp_framework.storage.database import init_database
from mcp_framework.tools import utility  # Import to register tools


async def demo_simple_workflow():
    """Demonstrate simple workflow execution."""
    print("="*60)
    print("Demo: Simple Workflow Execution")
    print("="*60)
    
    # Initialize
    init_database("sqlite:///workflow_demo.db")
    executor = WorkflowExecutor()
    
    # Define a simple DAG: load_dataset -> load_config
    dag = {
        "nodes": [
            {
                "id": "load_data",
                "tool": "load_dataset",
                "inputs": {
                    "dataset_path": "huggingface:squad"
                },
                "input_mappings": {}
            },
            {
                "id": "load_cfg",
                "tool": "load_config",
                "inputs": {
                    "config": {
                        "model": "llama-2-7b",
                        "learning_rate": 0.0001
                    }
                },
                "input_mappings": {}
            }
        ],
        "edges": []  # No dependencies - will run in parallel
    }
    
    print("\nWorkflow DAG:")
    print(json.dumps(dag, indent=2))
    
    print("\n" + "-"*60)
    print("Executing Workflow...")
    print("-"*60)
    
    # Execute with streaming
    async for event in executor.execute_streaming(dag):
        event_type = event.get("type")
        
        if event_type == "start":
            print(f"\n✓ Started workflow {event['workflow_id']}")
            print(f"  Total nodes: {event['total_nodes']}")
        
        elif event_type == "node_completed":
            node_id = event["node_id"]
            progress = event["progress"]
            result = event["result"]
            print(f"\n✓ Completed: {node_id}")
            print(f"  Progress: {progress:.0%}")
            print(f"  Result: {json.dumps(result, indent=4)}")
        
        elif event_type == "workflow_completed":
            print(f"\n🎉 Workflow Completed!")
            print(f"  Results: {json.dumps(event['results'], indent=2)}")
        
        elif event_type == "node_failed":
            print(f"\n✗ Failed: {event['node_id']}")
            print(f"  Error: {event['error']}")
        
        elif event_type == "workflow_failed":
            print(f"\n✗ Workflow Failed: {event['error']}")
    
    print("\n" + "="*60)


async def demo_dag_workflow():
    """Demonstrate workflow with dependencies."""
    print("\n" + "="*60)
    print("Demo: DAG Workflow with Dependencies")
    print("="*60)
    
    executor = WorkflowExecutor()
    
    # Define DAG with dependencies
    # load_dataset and load_config run in parallel
    # Then results can be used by downstream tasks (when we add them)
    dag = {
        "nodes": [
            {
                "id": "dataset",
                "tool": "load_dataset",
                "inputs": {"dataset_path": "huggingface:squad"},
                "input_mappings": {}
            },
            {
                "id": "config",
                "tool": "load_config",
                "inputs": {
                    "config": {"model": "gpt-4", "temp": 0.7}
                },
                "input_mappings": {}
            },
            {
                "id": "config2",
                "tool": "load_config",
                "inputs": {
                    "config": {"eval": True}
                },
                "input_mappings": {}
            }
        ],
        "edges": [
            {"from": "dataset", "to": "config2"},
            {"from": "config", "to": "config2"}
        ]
    }
    
    print("\nWorkflow Structure:")
    print("  dataset \\")
    print("            → config2")
    print("  config  /")
    
    print("\n" + "-"*60)
    print("Executing DAG...")
    print("-"*60)
    
    batch_num = 0
    async for event in executor.execute_streaming(dag):
        event_type = event.get("type")
        
        if event_type == "node_completed":
            print(f"  [{event['progress']:.0%}] {event['node_id']} completed")
        
        elif event_type == "workflow_completed":
            print(f"\n✓ All nodes executed successfully!")
    
    print("\n" + "="*60)


async def main():
    """Run all demos."""
    await demo_simple_workflow()
    await demo_dag_workflow()
    
    print("\n✓ All workflow demos completed!")


if __name__ == "__main__":
    asyncio.run(main())
