"""Simple LLM agent for TaaS."""

import json
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI

from taas_client.client import TaasClient


class SimpleLLMAgent:
    """
    Simple LLM agent that can understand natural language and execute tasks.
    
    This is a minimal implementation focusing on core functionality.
    """
    
    def __init__(
        self,
        taas_host: str = "localhost",
        taas_port: int = 50051,
        llm_api_key: Optional[str] = None,
        llm_model: str = "gpt-4"
    ):
        """Initialize the LLM agent."""
        self.taas_client = TaasClient(host=taas_host, port=taas_port)
        self.llm_client = AsyncOpenAI(api_key=llm_api_key) if llm_api_key else None
        self.llm_model = llm_model
       self.available_tasks: List[Dict[str, Any]] = []
    
    async def initialize(self) -> None:
        """Initialize the agent (connect to TaaS and fetch available tasks)."""
        await self.taas_client.connect()
        self.available_tasks = await self.taas_client.list_tasks()
        print(f"✓ Connected to TaaS server")
        print(f"✓ Found {len(self.available_tasks)} available tasks")
    
    async def close(self) -> None:
        """Close connections."""
        await self.taas_client.close()
    
    def _create_system_prompt(self) -> str:
        """Create system prompt with available tasks."""
        tasks_desc = "\n".join([
            f"- {task['name']}: {task['description']}"
            for task in self.available_tasks
        ])
        
        return f"""You are a helpful AI assistant that can execute ML tasks on a TaaS server.

Available tasks:
{tasks_desc}

When a user asks to perform a task, you should:
1. Identify which task to use
2. Extract the required inputs from the user's message
3. Return a JSON object with the task name and inputs

Respond ONLY with JSON in this format:
{{
    "task_name": "task_name_here",
    "inputs": {{"param1": "value1", "param2": "value2"}}
}}

If you need more information from the user, respond with:
{{
    "clarification_needed": true,
    "question": "What information do you need?"
}}
"""
    
    async def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Process a user message and execute tasks.
        
        Args:
            user_message: Natural language message from user
        
        Returns:
            Response dictionary with results or clarification request
        """
        if self.llm_client is None:
            # Fallback: try to parse as JSON input directly
            return {
                "error": "LLM not configured. Please provide task name and inputs as JSON."
            }
        
        # Call LLM to extract task and inputs
        response = await self.llm_client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": self._create_system_prompt()},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1
        )
        
        llm_response = response.choices[0].message.content
        
        try:
            parsed = json.loads(llm_response)
            
            # Check if clarification needed
            if parsed.get("clarification_needed"):
                return {
                    "clarification_needed": True,
                    "question": parsed.get("question", "Could you provide more details?")
                }
            
            # Extract task info
            task_name = parsed.get("task_name")
            inputs = parsed.get("inputs", {})
            
            if not task_name:
                return {"error": "Could not determine which task to execute"}
            
            # Submit the task
            result = await self.taas_client.submit_task(
                task_name=task_name,
                inputs=inputs
            )
            
            return {
                "success": True,
                "task_name": task_name,
                "task_id": result["task_id"],
                "status": result["status"],
                "message": result["message"]
            }
            
        except json.JSONDecodeError:
            return {
                "error": "Could not parse LLM response",
                "llm_response": llm_response
            }
        except Exception as e:
            return {
                "error": f"Error executing task: {str(e)}"
            }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a task."""
        return await self.taas_client.get_status(task_id)
