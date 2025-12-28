"""Example: Using Task Planning Agent."""

import asyncio
from mcp_framework.agent.task_planning_agent import TaskPlanningAgent
from mcp_framework.storage.database import init_database


async def demo_agent():
    """Demonstrate task planning agent."""
    print("="*60)
    print("Task Planning Agent Demo")
    print("="*60)
    
    # Initialize database
    init_database()
    
    # Create agent
    agent = TaskPlanningAgent(user_id="demo_user")
    await agent.initialize()
    
    print(f"\nCurrent provider: {agent.get_current_provider()}")
    print(f"Available tools: {len(agent.available_tools)}\n")
    
    # Example 1: Simple request
    print("Example 1: Load dataset")
    print("-"*60)
    user_msg = "Load the SQuAD dataset from HuggingFace"
    print(f"User: {user_msg}")
    
    response = await agent.chat(user_msg)
    print(f"Agent: {response}\n")
    
    # Example 2: Multi-step request
    print("Example 2: Multi-step task")
    print("-"*60)
    user_msg = "Load the SQuAD dataset and create a training config with learning rate 0.001"
    print(f"User: {user_msg}")
    
    response = await agent.chat(user_msg)
    print(f"Agent: {response}\n")
    
    # Example 3: Switch provider
    print("Example 3: Switch provider")
    print("-"*60)
    
    # Note: This will fail if Anthropic key is not set
    # Uncomment to test:
    # result = agent.switch_provider("anthropic")
    # print(result)
    
    await agent.close()
    
    print("\n" + "="*60)
    print("✓ Agent demo completed!")
    print("="*60)


if __name__ == "__main__":
    print("\nNOTE: Make sure MCP server is running (uv run mcp-server)\n")
    print("NOTE: Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env\n")
    asyncio.run(demo_agent())
