"""Task Planning Agent - Integrates LLM with MCP tools."""

import json
from typing import List, Dict, Any, Optional

from mcp_framework.agent.base_agent import BaseAgent, Message, ToolCall
from mcp_framework.agent.agent_manager import get_agent_manager
from mcp_framework.client.mcp_client import MCPClient
from mcp_framework.user_side.session_manager import get_session_manager
import structlog

logger = structlog.get_logger()


class TaskPlanningAgent:
    """High-level agent that uses LLM to plan and execute tasks using MCP tools."""
    
    def __init__(self, mcp_url: str = "http://localhost:8000", user_id: str = "default"):
        """
        Initialize task planning agent.
        
        Args:
            mcp_url: MCP Gateway URL
            user_id: User identifier
        """
        self.mcp_client = MCPClient(mcp_url)
        self.agent_manager = get_agent_manager()
        self.session_manager = get_session_manager()
        self.user_id = user_id
        self.session_id: Optional[str] = None
        self.conversation_history: List[Message] = []
        self.available_tools: List[Dict[str, Any]] = []
    
    async def initialize(self) -> None:
        """Initialize session and fetch available tools."""
        # Create or get session
        self.session_id = await self.session_manager.get_or_create_session(self.user_id)
        
        # Fetch available tools
        tools_response = await self.mcp_client.list_tools()
        self.available_tools = tools_response['tools']
        
        logger.info(f"Initialized with {len(self.available_tools)} tools")
        
        # Add system message
        system_msg = self._create_system_message()
        self.conversation_history.append(system_msg)
    
    def _create_system_message(self) -> Message:
        """Create system message with tool information."""
        tools_desc = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self.available_tools
        ])
        
        system_prompt = f"""You are a helpful AI assistant with access to the following tools via MCP:

{tools_desc}

When a user asks you to perform a task, you should:
1. Determine which tools are needed
2. Call the appropriate tools with correct arguments
3. Use tool results to provide helpful responses

Be concise and helpful. Always explain what you're doing."""
        
        return Message(role="system", content=system_prompt)
    
    async def chat(self, user_message: str) -> str:
        """
        Chat with the agent.
        
        Args:
            user_message: User's message
        
        Returns:
            Agent's response
        """
        # Add user message
        self.conversation_history.append(Message(role="user", content=user_message))
        
        # Log to session
        await self.session_manager.add_event(
            self.session_id,
            "user_message",
            {"message": user_message}
        )
        
        # Get current agent
        agent = self.agent_manager.get_agent()
        
        # Chat loop (handle tool calls)
        max_iterations = 5
        for iteration in range(max_iterations):
            # Get agent response
            response = await agent.chat(
                messages=self.conversation_history,
                tools=self.available_tools
            )
            
            # If no tool calls, return response
            if not response.tool_calls:
                assistant_msg = Message(role="assistant", content=response.message)
                self.conversation_history.append(assistant_msg)
                
                # Log to session
                await self.session_manager.add_event(
                    self.session_id,
                    "assistant_message",
                    {"message": response.message}
                )
                
                return response.message
            
            # Execute tool calls
            tool_results = await self._execute_tool_calls(response.tool_calls)
            
            # Add assistant message with tool calls
            self.conversation_history.append(Message(
                role="assistant",
                content=response.message or "Using tools...",
                tool_calls=[tc.model_dump() for tc in response.tool_calls]
            ))
            
            # Add tool results
            for tool_call, result in zip(response.tool_calls, tool_results):
                self.conversation_history.append(Message(
                    role="tool",
                    content=json.dumps(result),
                    tool_call_id=tool_call.id
                ))
        
        return "Maximum iterations reached. Please try rephrasing your request."
    
    async def _execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[Dict[str, Any]]:
        """Execute MCP tool calls."""
        results = []
        
        for tool_call in tool_calls:
            logger.info(f"Executing tool: {tool_call.name}")
            
            # Log to session
            await self.session_manager.add_event(
                self.session_id,
                "tool_call",
                {
                    "tool": tool_call.name,
                    "arguments": tool_call.arguments
                }
            )
            
            try:
                # Call tool via MCP
                result = await self.mcp_client.call_tool(
                    tool_call.name,
                    tool_call.arguments
                )
                results.append(result)
                
                # Log result
                await self.session_manager.add_event(
                    self.session_id,
                    "tool_result",
                    {
                        "tool": tool_call.name,
                        "result": result
                    }
                )
            
            except Exception as e:
                logger.error(f"Tool call failed: {e}")
                results.append({
                    "error": str(e),
                    "status": "FAILED"
                })
        
        return results
    
    def switch_provider(self, provider: str) -> str:
        """Switch LLM provider."""
        from mcp_framework.agent.base_agent import AgentProvider
        
        try:
            new_provider = AgentProvider(provider)
            self.agent_manager.switch_provider(new_provider)
            return f"Switched to {provider}"
        except Exception as e:
            return f"Error switching provider: {e}"
    
    def get_current_provider(self) -> str:
        """Get current LLM provider."""
        return self.agent_manager.get_current_provider().value
    
    async def close(self) -> None:
        """Close connections."""
        await self.mcp_client.close()
