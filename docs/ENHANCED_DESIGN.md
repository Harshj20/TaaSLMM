# Enhanced Design Document

## Task Classification System

### 1. Microservices (Utilities)
**Purpose**: Reusable building blocks that perform specific operations and return identifiers for pipelining

**Examples**:
- `load_dataset`: Load dataset and return `dataset_id`
- `load_config`: Load configuration and return `config_id`
- `load_lora`: Load LoRA adapter and return `lora_id`
- `create_env`: Create isolated environment and return `env_id`

**Characteristics**:
- Return unique identifiers for resources
- Lightweight and fast execution
- No isolation required (run in main server process)
- Can be chained in pipelines

### 2. MacroTasks (Main Operations)
**Purpose**: Heavy-weight user-facing tasks that perform substantial ML operations

**Examples**:
- `finetune`: Finetune a model with LoRA
- `train`: Full training from scratch
- `ptq`: Post-Training Quantization
- `qat`: Quantization-Aware Training
- `evaluate`: Model evaluation

**Characteristics**:
- **Require isolation** (run in separate containers/environments)
- Accept IDs from microservices as inputs
- Long-running operations
- Return model IDs and metrics

### 3. Pipeline Tasks
**Purpose**: Orchestrate multiple tasks with intermediate result passing

**Architecture**:
```python
{
    "pipeline_id": "pipeline_xyz",
    "name": "finetune_and_eval",
    "global_inputs": {
        "dataset_path": "huggingface:squad",
        "model_name": "llama-2-7b"
    },
    "nodes": [
        {
            "node_id": "load_dataset",
            "task_name": "load_dataset",
            "inputs": {},  # Uses global inputs
            "input_mappings": {}
        },
        {
            "node_id": "finetune",
            "task_name": "finetune",
            "inputs": {},
            "input_mappings": {
                "load_dataset.dataset_id": "dataset_id"  // Pipe output to input
            }
        }
    ],
    "edges": [
        {"from": "load_dataset", "to": "finetune"}
    ]
}
```

**Features**:
- JSON-based graph definition
- Automatic dependency resolution (topological sort)
- Intermediate result passing via `input_mappings`
- Global inputs from user
- Support for DAGs (no cycles allowed)

### 4. Managerial Services
**Purpose**: Administrative and metadata operations

**Examples**:
- `get_task_info`: Get task metadata and schema
- `list_tasks`: List all available tasks by type
- `submit_task`: Submit single task for execution
- `submit_pipeline`: Submit pipeline graph
- `get_status`: Query task/pipeline status
- `upload_artifact` / `download_artifact`: Artifact management

## Pipeline Examples

### Example 1: Simple Finetune Pipeline
```python
pipeline = {
    "nodes": [
        {"node_id": "load_data", "task_name": "load_dataset"},
        {"node_id": "load_cfg", "task_name": "load_config"},
        {
            "node_id": "finetune",
            "task_name": "finetune",
            "input_mappings": {
                "load_data.dataset_id": "dataset_id",
                "load_cfg.config_id": "config_id"
            }
        }
    ]
}
```

**Flow**:
1. `load_dataset` returns `{dataset_id: "ds_abc", dataset_path: "..."}`
2. `load_config` returns `{config_id: "cfg_xyz", config: {...}}`
3. `finetune` receives `dataset_id="ds_abc"` and `config_id="cfg_xyz"` automatically

### Example 2: Full ML Pipeline
```python
# load_dataset -> load_config -> finetune -> ptq -> evaluate
#      |                                           ^
#      +-------------------------------------------+
```

**Flow**:
1. Load dataset and config (parallel)
2. Finetune model with dataset + config
3. Quantize finetuned model (PTQ)
4. Evaluate quantized model on same dataset

## Isolation Strategy

### MacroTask Isolation
**Problem**: MacroTasks have conflicting dependencies and can interfere with each other

**Solution**: Container-based isolation

```python
class BaseTask:
    @classmethod
    def requires_isolation(cls) -> bool:
        return cls.get_task_type() == TaskType.MACROTASK
```

**Implementation Options**:
1. **Docker containers** (most isolation)
   - Each MacroTask runs in its own container
   - Resources mounted via volumes
   - CPU/GPU allocation controlled

2. **Virtual environments** (lightweight)
   - Each MacroTask gets its own venv
   - Package isolation without full containerization
   - Use `uv` for fast environment creation

3. **Process isolation** (minimal)
   - Separate Python processes
   - Shared filesystem but isolated runtime

**Recommended**: Docker for production, venv for development

## LLM Agent Integration

### Singleton Task Execution
```python
agent.process_message("Load the SQuAD dataset")
# -> Submits load_dataset task
```

### Pipeline Registration
```python
agent.process_message(
    "Finetune Llama-2-7b on SQuAD dataset, then quantize and evaluate"
)
# -> LLM extracts:
# 1. model_name= "meta-llama/Llama-2-7b"
# 2. dataset_path = "huggingface:squad"
# 3. Identifies pipeline: load_dataset -> load_config -> finetune -> ptq -> evaluate
# 4. Registers and submits pipeline
```

### Agent Capabilities
1. **Intent Classification**:
   - Single task vs pipeline
   - Which task type to use

2. **Input Extraction**:
   - Parse natural language to structured inputs
   - Map to task schemas

3. **Pipeline Construction**:
   - Identify task sequence from description
   - Create pipeline JSON graph
   - Wire intermediate results

4. **Clarification**:
   - Ask for missing required inputs
   - Validate extracted values

## API Enhancements

### Classify Tasks by Type
```grpc
message ListTasksRequest {
  optional TaskType filter_type = 1;  // Filter by task type
}

message TaskDefinition {
  string task_type = 8;  // MICROSERVICE, MACROTASK, etc.
  bool requires_isolation = 9;
}
```

### Pipeline Submission
```grpc
message PipelineRequest {
  string pipeline_json = 1;  // JSON pipeline graph
  string user_id = 2;
}

message PipelineResponse {
  string pipeline_id = 1;
  repeated string task_ids = 2;  // IDs of all tasks in pipeline
  TaskStatusEnum status = 3;
}
```

## Implementation Status

✅ **Completed**:
- BaseTask with TaskType classification
- PipelineGraph system with JSON serialization
- Intermediate result passing via input_mappings
- Microservice task examples (load_dataset, load_lora, create_env)
- MacroTask examples (finetune, ptq, evaluate)
- PipelineExecutor with dependency resolution
- Pipeline demonstration examples

🔄 **In Progress**:
- Container isolation for MacroTasks
- Enhanced LLM agent for pipeline construction
- gRPC pipeline submission endpoint

📋 **Planned**:
- Parallel execution for independent nodes
- Pipeline status streaming
- Artifact management integration
- Authentication for multi-user scenarios
