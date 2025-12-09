"""Example: Simple task submission."""

import asyncio
from taas_client.client import TaasClient


async def main():
    """Submit a simple task."""
    # Create client
    async with TaasClient() as client:
        # List available tasks
        print("Available tasks:")
        tasks = await client.list_tasks()
        for task in tasks:
            print(f"  - {task['name']}: {task['description']}")
        
        print("\n" + "="*60 + "\n")
        
        # Submit a load_config task
        print("Submitting load_config task...")
        result = await client.submit_task(
            task_name="load_config",
            inputs={
                "config_dict": {
                    "model_name": "llama-7b",
                    "learning_rate": 0.0001,
                    "batch_size": 32
                }
            }
        )
        
        print(f"✓ Task submitted!")
        print(f"  Task ID: {result['task_id']}")
        print(f"  Status: {result['status']}")
        print(f"  Message: {result['message']}")
        
        # Get task status
        print("\n" + "="*60 + "\n")
        print("Checking task status...")
        status = await client.get_status(result['task_id'])
        
        print(f"  Task: {status['task_name']}")
        print(f"  Status: {status['status']}")
        print(f"  Progress: {status['progress']:.0%}")
        print(f"  Inputs: {status['inputs']}")


if __name__ == "__main__":
    asyncio.run(main())
