# TaaS Developer Guide

## Adding New Tasks

Tasks are the core building blocks of TaaS. Here's how to create custom tasks.

### Step 1: Create Your Task Class

```python
from taas_server.tasks.base_task import BaseTask
from taas_server.tasks.task_registry import register_task
from typing import Dict, Any

@register_task
class MyCustomTask(BaseTask):
    @classmethod
    def get_name(cls) -> str:
        return "my_custom_task"
    
    @classmethod
    def get_description(cls) -> str:
        return "Description of what your task does"
    
    @classmethod
    def get_version(cls) -> str:
        return "1.0.0"
    
    @classmethod
    def get_input_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "First parameter"},
                "param2": {"type": "number", "description": "Second parameter"}
            },
            "required": ["param1"]
        }
    
    @classmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            },
            "required": ["result"]
        }
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # Your task logic here
        param1 = inputs["param1"]
        param2 = inputs.get("param2", 0)
        
        # Report progress (optional)
        self.update_progress(0.5, "Processing...")
        
        result = f"Processed {param1} with {param2}"
        
        return {"result": result}
```

### Step 2: Register the Task

Simply import your task module in `taas_server/tasks/examples/__init__.py`:

```python
from taas_server.tasks.examples import my_custom_task
```

### Step 3: Test Your Task

```python
import asyncio
from taas_client.client import TaasClient

async def test_task():
    async with TaasClient() as client:
        result = await client.submit_task(
            task_name="my_custom_task",
            inputs={"param1": "test", "param2": 42}
        )
        print(f"Task ID: {result['task_id']}")

asyncio.run(test_task())
```

## Task Best Practices

1. **Use JSON Schema**: Always define comprehensive input/output schemas for validation
2. **Report Progress**: Use `self.update_progress()` for long-running tasks  
3. **Handle Errors**: Use try/except and provide meaningful error messages
4. **Idempotent Operations**: Design tasks to be safely retryable
5. **Document Well**: Provide clear descriptions and parameter documentation

## Example Tasks

See `taas_server/tasks/examples/config_tasks.py` for complete examples of:
- Loading configurations from files or dictionaries
- Creating and validating configurations
- Saving outputs to disk

## Testing

```bash
# Run tests
uv run pytest

# Run specific test
uv run pytest tests/unit/test_task_registry.py

# With coverage
uv run pytest --cov=taas_server
```

## Deployment

### Local Development

```bash
# Start server
uv run taas-server

# In another terminal, run examples
uv run python examples/simple_task.py
```

### Docker

```bash
# Build and run
docker-compose up --build

# Stop
docker-compose down
```

### Production

For production, use PostgreSQL instead of SQLite:

```yaml
# docker-compose.yml
environment:
  - DATABASE_URL=postgresql://user:pass@postgres:5432/taas
```

## Architecture

```
Client (Python/Any Language)
    ↓ gRPC
TaaS Server
    ├── Task Service (Submit, Status, List)
    ├── State Manager (Crash Recovery)
    ├── Task Registry (Discovery)
    └── Database (SQLAlchemy)
```

## Extending the System

- **Add Services**: Implement new gRPC services in `taas_server/services/`
- **Add Validators**: Create validators in `taas_server/middleware/`
- **Add LLM Providers**: Extend `llm_agent/llm_providers/`
