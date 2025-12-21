# MCP Framework

Production-grade ML task orchestration using **Model Context Protocol (MCP)** with HTTP-SSE transport.

## Architecture

```
User → User Agent → Session Manager → Task Planning Agent (LLM)
                                            ↓
                                       MCP Gateway (HTTP-SSE)
                                            ↓
                      Tool Registry + Workflow Executor + Debug Manager
                                            ↓
                      Utility/Training/Admin Tools → Isolated Runtime (Docker)
                                            ↓
                      Artifact Store + Model Store + Debug Context DB
```

## Features

- ✅ **MCP Protocol**: Standardized client-server communication via HTTP-SSE
- ✅ **Session Continuity**: Persistent context across conversations
- ✅ **Debug Intelligence**: Learns from failures and suggests fixes
- ✅ **Isolated Execution**: Training tasks run in Docker containers
- ✅ **Workflow DAGs**: Automatic dependency resolution and parallel execution

## Quick Start

```bash
# Install dependencies
uv sync

# Start MCP server
uv run mcp-server

# Use CLI agent
uv run mcp-agent "Finetune Llama-2-7b on SQuAD dataset"
```

## Components

### User Side
- **User Agent**: CLI interface for task specification
- **Session Manager**: Maintains conversation context
- **Context Summarizer**: Compresses history for LLM
- **Preference RAG**: Learns user preferences

### Agent Layer
- **Task Planning Agent**: LLM-powered workflow orchestration

### Server Side (MCP)
- **MCP Gateway**: HTTP-SSE endpoints
- **Tool Registry**: Catalog of available tools
- **Workflow Executor**: DAG execution engine
- **Debug Manager**: Error learning system

### Tools
- **Utility**: load_dataset, load_config, create_env
- **Training**: finetune, train, quantize, evaluate (isolated)
- **Admin**: list_tools, get_status, cancel_task

## Documentation

- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
- [API Reference](docs/API.md)
- [User Guide](docs/USER_GUIDE.md)

## License

MIT
