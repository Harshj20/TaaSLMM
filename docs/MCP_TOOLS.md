# MCP Tools Integration

The TaaS server now exposes all services via the Model Context Protocol (MCP), making them accessible to LLM agents like Claude Desktop, GPT, etc.

## Architecture

```
taas_server/tools/
├── mcp_server.py          # Main MCP server
├── macro_services.py      # MacroTasks (finetune, train, ptq, eval)
├── micro_services.py      # Microservices (load_dataset, load_config, etc.)
├── pipeline_services.py   # Pipeline orchestration
└── admin_services.py      # Management operations
```

## Service Classification

### 1. Macro Services
**Heavy ML operations requiring isolation**
- `macro_finetune`: Finetune a language model
- `macro_train`: Full training from scratch (placeholder)
- `macro_ptq`: Post-Training Quantization
- `macro_evaluate`: Model evaluation

### 2. Micro Services
**Utility operations returning resource IDs**
- `micro_load_config`: Load configuration → `config_id`
- `micro_load_dataset`: Load dataset → `dataset_id`
- `micro_load_lora`: Load LoRA adapter → `lora_id`
- `micro_create_env`: Create isolated environment → `env_id`

### 3. Pipeline Services
**Task orchestration**
- `pipeline_execute_custom`: Execute custom pipeline from JSON
- `pipeline_finetune`: Predefined finetune pipeline
- `pipeline_full_ml`: Full ML workflow (finetune → quantize → evaluate)
- `pipeline_get_schema`: Get required inputs for a pipeline

### 4. Admin Services
**Management and metadata**
- `admin_list_tasks`: List available tasks (filterable by type)
- `admin_get_task_info`: Get task details and schema
- `admin_get_task_schema`: Get combined input schema
- `admin_get_status`: Check task execution status
- `admin_get_system_status`: System metrics
- `admin_list_executions`: Recent task history

## Running the MCP Server

```bash
# Install dependencies (includes MCP)
uv sync

# Run MCP server (stdio mode for LLM integration)
uv run taas-mcp
```

## Using with Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "taas": {
      "command": "uv",
      "args": ["run", "taas-mcp"],
      "cwd": "E:/antigravity/taas-server"
    }
  }
}
```

## Example MCP Tool Usage

### List Available Tasks
```json
{
  "tool": "admin_list_tasks",
  "arguments": {
    "task_type": "MACROTASK"
  }
}
```

### Execute Micro Service
```json
{
  "tool": "micro_load_dataset",
  "arguments": {
    "dataset_path": "huggingface:squad"
  }
}
```

### Execute Pipeline
```json
{
  "tool": "pipeline_finetune",
  "arguments": {
    "dataset_path": "huggingface:squad",
    "config_dict": {
      "model_name": "llama-2-7b",
      "learning_rate": 0.0001
    }
  }
}
```

### Get Task Schema
```json
{
  "tool": "admin_get_task_schema",
  "arguments": {
    "task_name": "finetune",
    "as_pipeline": true
  }
}
```

## Benefits

1. **LLM Integration**: Any MCP-compatible LLM can use TaaS tools
2. **Type Safety**: JSON Schema validation for all inputs
3. **Service Isolation**: Clear separation of micro/macro/pipeline/admin
4. **Discoverability**: LLMs can query available tools and schemas
5. **Standardized**: Uses MCP protocol for interoperability

## Development

### Adding New Tools

All tools are automatically exposed from the task registry. To add a new tool:

1. Create a task class inheriting from `BaseTask`
2. Use `@register_task` decorator
3. Specify the `TaskType` (MICROSERVICE, MACROTASK, etc.)
4. Task automatically becomes an MCP tool!

### Custom MCP Tools

For operations that don't fit the task framework, add custom tools in the respective service modules (macro_services.py, etc.).
