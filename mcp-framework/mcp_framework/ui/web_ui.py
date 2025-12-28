"""Gradio Web UI for MCP Framework."""

import asyncio
import gradio as gr
from typing import List, Tuple, Optional
import json

from mcp_framework.agent.task_planning_agent import TaskPlanningAgent
from mcp_framework.client.mcp_client import MCPClient
from mcp_framework.storage.database import init_database


class MCPWebUI:
    """Web UI for MCP Framework with chat and tool inspection."""
    
    def __init__(self, mcp_url: str = "http://localhost:8000"):
        """Initialize web UI."""
        self.mcp_url = mcp_url
        self.agent: Optional[TaskPlanningAgent] = None
        self.mcp_client = MCPClient(mcp_url)
        self.available_tools = []
    
    async def initialize(self):
        """Initialize agent and fetch tools."""
        # Initialize database
        init_database()
        
        # Create agent
        self.agent = TaskPlanningAgent(self.mcp_url, user_id="web_user")
        await self.agent.initialize()
        
        # Fetch tools
        tools_response = await self.mcp_client.list_tools()
        self.available_tools = tools_response['tools']
    
    async def chat_fn(
        self,
        message: str,
        history: List[Tuple[str, str]]
    ) -> Tuple[List[Tuple[str, str]], str]:
        """
        Chat function for Gradio.
        
        Args:
            message: User message
            history: Chat history
        
        Returns:
            Updated history and empty string
        """
        if not self.agent:
            await self.initialize()
        
        # Get response
        response = await self.agent.chat(message)
        
        # Update history
        history.append((message, response))
        
        return history, ""
    
    async def list_tools_fn(self, category_filter: str) -> str:
        """List tools with optional category filter."""
        if category_filter and category_filter != "All":
            filtered = [t for t in self.available_tools if t['category'] == category_filter]
        else:
            filtered = self.available_tools
        
        # Format as table
        output = f"**Available Tools ({len(filtered)})**\n\n"
        for tool in filtered:
            output += f"### {tool['name']}\n"
            output += f"- **Category**: {tool['category']}\n"
            output += f"- **Description**: {tool['description']}\n"
            output += f"- **Requires Isolation**: {'Yes' if tool['requiresIsolation'] else 'No'}\n\n"
        
        return output
    
    async def call_tool_fn(self, tool_name: str, arguments_json: str) -> str:
        """Manually call a tool."""
        try:
            arguments = json.loads(arguments_json)
            result = await self.mcp_client.call_tool(tool_name, arguments)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError:
            return "Error: Invalid JSON arguments"
        except Exception as e:
            return f"Error: {e}"
    
    async def switch_provider_fn(self, provider: str) -> str:
        """Switch LLM provider."""
        if not self.agent:
            await self.initialize()
        
        return self.agent.switch_provider(provider.lower())
    
    def create_ui(self) -> gr.Blocks:
        """Create Gradio UI."""
        
        with gr.Blocks(
            title="MCP Framework",
            theme=gr.themes.Soft(),
            css="""
                .header {background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;}
                .header h1 {color: white; margin: 0;}
                .chat-container {height: 500px;}
            """
        ) as demo:
            gr.HTML("""
                <div class="header">
                    <h1>🚀 MCP Framework</h1>
                    <p style="color: white; margin: 5px 0 0 0;">AI Agent with MCP Tools</p>
                </div>
            """)
            
            with gr.Tabs() as tabs:
                # Tab 1: Chat Interface
                with gr.Tab("💬 Chat"):
                    gr.Markdown("Chat with the AI agent. It can use MCP tools automatically.")
                    
                    with gr.Row():
                        with gr.Column(scale=4):
                            chatbot = gr.Chatbot(
                                label="Conversation",
                                height=500,
                                show_copy_button=True
                            )
                            
                            with gr.Row():
                                msg = gr.Textbox(
                                    label="Message",
                                    placeholder="Ask me anything or request a task...",
                                    scale=4
                                )
                                send_btn = gr.Button("Send", variant="primary", scale=1)
                        
                        with gr.Column(scale=1):
                            gr.Markdown("### Settings")
                            
                            provider_dropdown = gr.Dropdown(
                                choices=["OpenAI", "Anthropic"],
                                value="OpenAI",
                                label="LLM Provider"
                            )
                            
                            switch_btn = gr.Button("Switch Provider")
                            provider_status = gr.Textbox(label="Status", interactive=False)
                            
                            gr.Markdown("### Current Provider")
                            current_provider = gr.Textbox(
                                value="openai",
                                label="Active",
                                interactive=False
                            )
                            
                            clear_btn = gr.Button("Clear Chat")
                    
                    # Event handlers
                    send_btn.click(
                        self.chat_fn,
                        inputs=[msg, chatbot],
                        outputs=[chatbot, msg]
                    )
                    
msg.submit(
                        self.chat_fn,
                        inputs=[msg, chatbot],
                        outputs=[chatbot, msg]
                    )
                    
                    clear_btn.click(lambda: [], outputs=chatbot)
                    
                    switch_btn.click(
                        self.switch_provider_fn,
                        inputs=provider_dropdown,
                        outputs=provider_status
                    )
                
                # Tab 2: Tool Inspector
                with gr.Tab("🔧 Tools"):
                    gr.Markdown("Browse and manually execute MCP tools.")
                    
                    with gr.Row():
                        category_filter = gr.Dropdown(
                            choices=["All", "UTILITY", "TRAINING", "ADMIN"],
                            value="All",
                            label="Filter by Category"
                        )
                        refresh_btn = gr.Button("Refresh", variant="secondary")
                    
                    tools_display = gr.Markdown(value="Loading tools...")
                    
                    gr.Markdown("### Manual Tool Execution")
                    
                    with gr.Row():
                        tool_name_input = gr.Dropdown(
                            choices=[],
                            label="Tool Name",
                            interactive=True
                        )
                        
                    arguments_input = gr.Code(
                        label="Arguments (JSON)",
                        language="json",
                        value='{"example": "value"}'
                    )
                    
                    execute_btn = gr.Button("Execute Tool", variant="primary")
                    tool_result = gr.Code(label="Result", language="json")
                    
                    # Event handlers
                    refresh_btn.click(
                        self.list_tools_fn,
                        inputs=category_filter,
                        outputs=tools_display
                    )
                    
                    category_filter.change(
                        self.list_tools_fn,
                        inputs=category_filter,
                        outputs=tools_display
                    )
                    
                    execute_btn.click(
                        self.call_tool_fn,
                        inputs=[tool_name_input, arguments_input],
                        outputs=tool_result
                    )
                    
                    # Update tool dropdown
                    def update_tools():
                        return gr.Dropdown(choices=[t['name'] for t in self.available_tools])
                    
                    demo.load(update_tools, outputs=tool_name_input)
                
                # Tab 3: System Info
                with gr.Tab("ℹ️ Info"):
                    gr.Markdown(f"""
                    ## MCP Framework
                    
                    **Version**: 0.1.0
                    
                    **MCP Gateway**: {self.mcp_url}
                    
                    ### Features
                    - ✅ Multi-provider AI agents (OpenAI, Anthropic)
                    - ✅ MCP tool integration
                    - ✅ Workflow DAG execution
                    - ✅ Debug context learning
                    - ✅ Session management
                    
                    ### Available Providers
                    - **OpenAI**: GPT-4, GPT-3.5
                    - **Anthropic**: Claude 3.5 Sonnet
                    
                    ### Documentation
                    - [Quick Start](docs/QUICK_START.md)
                    - [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
                    """)
            
            # Initialize on load
            demo.load(self.initialize)
            demo.load(self.list_tools_fn, inputs=gr.Textbox(value="All", visible=False), outputs=tools_display)
        
        return demo
    
    def launch(self, **kwargs):
        """Launch the web UI."""
        demo = self.create_ui()
        demo.launch(**kwargs)


def main():
    """Launch web UI."""
    ui = MCPWebUI()
    ui.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    main()
