"""Pipeline services - Task orchestration and pipeline execution."""

from typing import Dict, Any, List
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

from taas_server.tasks.pipeline_graph import PipelineGraph, create_finetune_pipeline, create_full_ml_pipeline
from taas_server.tasks.pipeline_executor import PipelineExecutor
from taas_server.tasks.task_registry import get_task_registry


def register_pipeline_services(server: Server):
    """Register pipeline service tools."""
    
    executor = PipelineExecutor()
    registry = get_task_registry()
    
    @server.list_tools()
    async def list_pipeline_tools() -> List[Tool]:
        """List pipeline service tools."""
        return [
            Tool(
                name="pipeline_execute_custom",
                description="Execute a custom pipeline from JSON definition",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pipeline_json": {
                            "type": "string",
                            "description": "JSON pipeline graph definition"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "User identifier"
                        }
                    },
                    "required": ["pipeline_json"]
                }
            ),
            Tool(
                name="pipeline_finetune",
                description="Execute predefined finetune pipeline (load_dataset + load_config + finetune)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset_path": {"type": "string"},
                        "config_dict": {"type": "object"},
                        "model_name": {"type": "string"}
                    },
                    "required": ["dataset_path", "config_dict"]
                }
            ),
            Tool(
                name="pipeline_full_ml",
                description="Execute full ML pipeline (load -> finetune -> quantize -> evaluate)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dataset_path": {"type": "string"},
                        "config_dict": {"type": "object"},
                        "model_name": {"type": "string"}
                    },
                    "required": ["dataset_path", "config_dict", "model_name"]
                }
            ),
            Tool(
                name="pipeline_get_schema",
                description="Get required inputs schema for a task pipeline",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of task names in pipeline"
                        }
                    },
                    "required": ["task_names"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_pipeline_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a pipeline service."""
        try:
            if name == "pipeline_execute_custom":
                # Execute custom pipeline from JSON
                pipeline_json = arguments["pipeline_json"]
                user_id = arguments.get("user_id")
                
                results = await executor.execute_from_json(pipeline_json, user_id)
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "COMPLETED",
                        "type": "CUSTOM_PIPELINE",
                        "results": results
                    }, indent=2)
                )]
            
            elif name == "pipeline_finetune":
                # Execute predefined finetune pipeline
                pipeline = create_finetune_pipeline()
                pipeline.set_global_inputs(arguments)
                
                results = await executor.execute_pipeline(
                    pipeline,
                    user_id=arguments.get("user_id")
                )
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "COMPLETED",
                        "type": "FINETUNE_PIPELINE",
                        "results": results
                    }, indent=2)
                )]
            
            elif name == "pipeline_full_ml":
                # Execute full ML pipeline
                pipeline = create_full_ml_pipeline()
                pipeline.set_global_inputs(arguments)
                
                results = await executor.execute_pipeline(
                    pipeline,
                    user_id=arguments.get("user_id")
                )
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "COMPLETED",
                        "type": "FULL_ML_PIPELINE",
                        "results": results
                    }, indent=2)
                )]
            
            elif name == "pipeline_get_schema":
                # Get pipeline schema
                task_names = arguments["task_names"]
                schema = registry.get_pipeline_schema(task_names)
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "SUCCESS",
                        "pipeline": task_names,
                        "required_inputs": schema
                    }, indent=2)
                )]
            
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown pipeline tool: {name}"})
                )]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "status": "FAILED",
                    "tool": name
                })
            )]
