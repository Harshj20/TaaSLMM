# TaaS Server - Task-as-a-Service for LLM Agentic Workflows

A production-ready Task-as-a-Service server enabling LLM agents to execute ML tasks (training, finetuning, quantization, evaluation) through a gRPC API.

## features

- **gRPC API**: Language-agnostic task execution with Protocol Buffers
- **Async Execution**: Celery + Redis for distributed task processing
- **Task Registry**: Easy registration and discovery of tasks with JSON schemas
- **State Persistence**: SQLAlchemy-based database with crash recovery
- **Artifact Management**: Upload/download with S3-compatible storage
- **Logging Service**: Real-time log streaming and download
- **LLM Agent**: Natural language interface with multi-turn conversations
- **Validators**: Input/output validation for deterministic execution

## Quick Start

```bash
# Install dependencies
uv sync

# Start the server
uv run taas-server

# In another terminal, try the example
uv run python examples/simple_task.py

# Or use the LLM agent (requires OPENAI_API_KEY)
export OPENAI_API_KEY='your-key-here'
uv run python examples/llm_agent_demo.py
```

See [docs/QUICK_START.md](docs/QUICK_START.md) for detailed instructions.

### Docker

```bash
docker-compose up --build
```

## Architecture

```
taas-server/
├── protos/              # Protocol Buffer definitions
├── taas_server/         # Core server implementation
│   ├── db/             # Database models and migrations
│   ├── tasks/          # Task framework and examples
│   ├── services/       # gRPC service implementations
│   ├── middleware/     # Validators and interceptors
│   └── artifacts/      # Artifact management
├── taas_client/        # Python client SDK
├── llm_agent/          # LLM-powered agent
└── tests/              # Test suite
```

## Documentation

- [Developer Guide](docs/DEVELOPER_GUIDE.md) - How to add new tasks
- [API Reference](docs/API_REFERENCE.md) - gRPC API documentation
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment

## License

MIT
