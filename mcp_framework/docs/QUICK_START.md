# Quick Start Guide - MCP Framework

## Installation

```bash
cd mcp-framework
uv sync
```

## Running the Server

```bash
# Terminal 1: Start MCP server
uv run mcp-server
```

Server will start on `http://localhost:8000`

## Testing with Inspector

```bash
# Terminal 2: Launch interactive inspector
uv run mcp-inspector
```

### Inspector Features

**Main Menu**:
1. **Inspect Tools** - Browse available tools with filters
2. **Call Tool** - Interactively execute tools
3. **Execute Workflow** - Run DAG workflows with streaming
4. **Query Workflow Status** - Check workflow by ID
5. **Run Quick Test** - Automated test suite
6. **Exit**

### inspector Screenshots

**Tool Inspection**:
```
┌─ Available Tools (2 total) ──────────────────────┐
│ #  │ Name          │ Category │ Description      │
├────┼───────────────┼──────────┼──────────────────┤
│ 1  │ load_dataset  │ UTILITY  │ Load dataset...  │
│ 2  │ load_config   │ UTILITY  │ Load config...   │
└──────────────────────────────────────────────────┘
```

**Workflow Execution** (with SSE streaming):
```
⠋ Workflow abc123... [0/2]
✓ Completed: dataset
  Result: {'dataset_id': 'dataset_abc123', 'num_samples': 1000}
✓ Completed: config  
  Result: {'config_id': 'config_xyz789'}
✓ Workflow completed!
```

## Quick Examples

### Example 1: SSE Client Demo

```bash
python -m mcp_framework.client.mcp_client
```

### Example 2: Workflow Demo

```bash
python examples/workflow_demo.py
```

### Example 3: Debug Learning Demo

```bash
python examples/debug_demo.py
```

## HTTP API Examples (curl)

```bash
# Health check
curl http://localhost:8000/health

# List tools
curl http://localhost:8000/mcp/tools

# List by category
curl "http://localhost:8000/mcp/tools?category=UTILITY"

# Call tool
curl -X POST http://localhost:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "load_dataset",
    "arguments": {"dataset_path": "test"}
  }'

# Execute workflow (SSE streaming)
curl -N -X POST http://localhost:8000/mcp/workflow \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "dag": {
      "nodes": [{
        "id": "test",
        "tool": "load_dataset",
        "inputs": {"dataset_path": "test"},
        "input_mappings": {}
      }],
      "edges": []
    },
    "user_id": "test"
  }'
```

## Configuration

Create `.env` file:

```bash
# Server
HOST=0.0.0.0
PORT=8000

# Database (default: SQLite)
DATABASE_URL=sqlite:///mcp_framework.db
# Or PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/mcp_framework

# LLM (for future agent)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Logging
LOG_LEVEL=INFO
```

## Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Use different port
PORT=8001 uv run mcp-server
```

### Database errors
```bash
# Reset database
rm mcp_framework.db
uv run mcp-server  # Will recreate tables
```

### Import errors
```bash
# Reinstall dependencies
uv sync --reinstall
```

## Development

### Adding a New Tool

```python
# Create: mcp_framework/tools/utility/my_tool.py

from mcp_framework.tools.base import BaseTool, ToolCategory
from mcp_framework.server.tool_registry import register_tool

@register_tool
class MyTool(BaseTool):
    @classmethod
    def get_name(cls) -> str:
        return "my_tool"
    
    @classmethod
    def get_description(cls) -> str:
        return "My custom tool"
    
    @classmethod
    def get_category(cls) -> ToolCategory:
        return ToolCategory.UTILITY
    
    @classmethod
    def get_input_schema(cls):
        return {
            "type": "object",
            "properties": {
                "input_param": {"type": "string"}
            },
            "required": ["input_param"]
        }
    
    @classmethod
    def get_output_schema(cls):
        return {
            "type": "object",
            "properties": {
                "result_id": {"type": "string"}
            }
        }
    
    async def execute(self, inputs, runtime=None):
        # Your logic here
        return {"result_id": "success"}
```

Then import in `tools/utility/__init__.py`:
```python
from mcp_framework.tools.utility import my_tool
```

### Running Tests

```bash
# Quick test via inspector
uv run mcp-inspector
# Select option 5: Run Quick Test

# Or programmatically
python examples/workflow_demo.py
python examples/debug_demo.py
```

## Next Steps

1. ✅ Start server: `uv run mcp-server`
2. ✅ Test with inspector: `uv run mcp-inspector`
3. ✅ Try workflow demo: `python examples/workflow_demo.py`
4. 📝 Add your own tools
5. 🚀 Build the Task Planning Agent (Phase 4)
