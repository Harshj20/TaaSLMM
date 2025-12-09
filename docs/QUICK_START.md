"""Quick Start Guide."""

# Quick Start

This guide will get you up and running with TaaS in 5 minutes.

## Installation

```bash
cd taas-server
uv sync
```

## Start the Server

```bash
uv run taas-server
```

You should see:
```
Initializing TaaS Server...
Connecting to database: sqlite:///taas.db
Recovering state from last session...
...
✓ TaaS Server started on [::]:50051
✓ Ready to accept task requests
```

## Submit Your First Task

In another terminal:

```bash
uv run python examples/simple_task.py
```

This will:
1. List available tasks
2. Submit a `load_config` task
3. Check task status

## Try the LLM Agent

```bash
export OPENAI_API_KEY='your-key-here'
uv run python examples/llm_agent_demo.py
```

The agent will process natural language queries like:
- "Load a config with model name gpt-4"
- "Create a training config with batch size 64"

## Next Steps

- Read [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) to learn how to add custom tasks
- Check [docker-compose.yml](../docker-compose.yml) for production deployment
- Explore [implementation_plan.md](../implementation_plan.md) for the full architecture

## API Reference

### Python SDK

```python
from taas_client.client import TaasClient

async with TaasClient() as client:
    # List tasks
    tasks = await client.list_tasks()
    
    # Submit task
    result = await client.submit_task(
        task_name="load_config",
        inputs={"config_dict": {...}}
    )
    
    # Get status
    status = await client.get_status(result["task_id"])
```

### gRPC (Any Language)

Connect to `localhost:50051` and use the services defined in `protos/taas.proto`.

## Troubleshooting

**Server won't start:**
- Check if port 50051 is available
- Verify database file permissions

**Tasks not registering:**
- Ensure task module is imported in `taas_server/tasks/examples/__init__.py`
- Check task inherits from `BaseTask` and uses `@register_task`

**LLM agent fails:**
- Verify `OPENAI_API_KEY` is set
- Check API key has credits/quota
