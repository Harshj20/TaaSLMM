# MCP Framework

Production-grade ML task orchestration using **Model Context Protocol (MCP)** with HTTP-SSE transport.

## 🚀 Quick Start

```bash
# Install
cd mcp-framework
uv sync

# Terminal 1: Start server
uv run mcp-server

# Terminal 2: Launch inspector
uv run mcp-inspector
```

## ✨ Features

- ✅ **MCP Protocol** - Standardized HTTP-SSE communication
- ✅ **Workflow DAGs** - Automatic dependency resolution & parallel execution
- ✅ **Debug Intelligence** - Learns from errors, suggests fixes
- ✅ **Session Continuity** - Persistent context across conversations
- ✅ **Interactive Inspector** - Rich CLI for testing and debugging

## 📋 Tools

### Inspector (Interactive Debugger)

```bash
uv run mcp-inspector
```

**Features**:
- Inspect tools with category filters
- Call tools interactively
- Execute workflows with real-time SSE streaming
- Query workflow status
- Run automated test suite

### Client (Programmatic API)

```python
from mcp_framework.client import MCPClient

async with MCPClient() as client:
    # List tools
    tools = await client.list_tools(category="UTILITY")
    
    # Call tool
    result = await client.call_tool("load_dataset", {...})
    
    # Execute workflow with streaming
    async for event in client.execute_workflow_streaming(dag):
        print(event)
```

## 📚 Documentation

- [Quick Start Guide](docs/QUICK_START.md) - Setup and basic usage
- [Implementation Walkthrough](../brain/.../mcp_framework_walkthrough.md) - Architecture deep dive
- [Implementation Plan](../brain/.../mcp_framework_plan.md) - Design decisions

## 🎯 Examples

```bash
# Workflow DAG execution
python examples/workflow_demo.py

# Debug learning system
python examples/debug_demo.py

# Client usage
python examples/client_demo.py
```

## 🏗️ Architecture

```
User → Session Manager → Task Planning Agent (LLM)
             ↓
         MCP Gateway (HTTP-SSE)
             ↓
   Tool Registry + Workflow Executor + Debug Manager
             ↓
   Utility/Training/Admin Tools
             ↓
   Database + Artifact Store
```

## 🔧 Configuration

Create `.env`:
```bash
HOST=0.0.0.0
PORT=8000
DATABASE_URL=postgresql://localhost/mcp_framework
LOG_LEVEL=INFO
```

## 🛠️ Development

Add a new tool:

```python
from mcp_framework.tools.base import BaseTool, ToolCategory
from mcp_framework.server.tool_registry import register_tool

@register_tool
class MyTool(BaseTool):
    @classmethod
    def get_name(cls) -> str:
        return "my_tool"
    
    # Implement required methods...
```

## 📊 Status

**Phase 1-2 Complete**:
- ✅ MCP Gateway with HTTP-SSE
- ✅ Tool Registry
- ✅ Workflow Executor (DAG + streaming)
- ✅ Debug Context Manager
- ✅ Session Manager
- ✅ Interactive Inspector
- ✅ Client Library

**Next**:
- Phase 3: Docker isolation for training tools
- Phase 4: Task Planning Agent (LLM)
- Phase 5: User Agent CLI

## 📝 License

MIT
