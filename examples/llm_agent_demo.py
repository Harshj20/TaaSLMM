"""Example: Using LLM agent for natural language task execution."""

import asyncio
import os
from llm_agent.agent import SimpleLLMAgent


async def main():
    """Demo LLM agent."""
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("⚠ OPENAI_API_KEY not set. Set it to use the LLM agent.")
        print("Example: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Create and initialize agent
    agent = SimpleLLMAgent(llm_api_key=api_key)
    await agent.initialize()
    
    print("\n" + "="*60)
    print("LLM Agent Demo - Natural Language Task Execution")
    print("="*60 + "\n")
    
    # Example queries
    queries = [
        "Load a config with model name gpt-4 and learning rate 0.001",
        "Create a training config with batch size 64 and epochs 10",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n[Query {i}] {query}")
        print("-" * 60)
        
        response = await agent.process_message(query)
        
        if response.get("success"):
            print(f"✓ Task Submitted:")
            print(f"  Task: {response['task_name']}")
            print(f"  Task ID: {response['task_id']}")
            print(f"  Status: {response['status']}")
        elif response.get("clarification_needed"):
            print(f"❓ Clarification needed:")
            print(f"  {response['question']}")
        else:
            print(f"✗ Error: {response.get('error')}")
    
    await agent.close()
    print("\n" + "="*60)
    print("Demo complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
