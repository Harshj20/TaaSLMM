"""Pipeline executor for running task graphs."""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from taas_server.tasks.pipeline_graph import PipelineGraph, PipelineNode
from taas_server.tasks.task_registry import get_task_registry
from taas_server.db.database import get_db_manager
from taas_server.db.models import Task, TaskStatusEnum, Pipeline


class PipelineExecutor:
    """Execute pipeline graphs with dependency resolution."""
    
    def __init__(self):
        """Initialize pipeline executor."""
        self.task_registry = get_task_registry()
        self.db_manager = get_db_manager()
    
    async def execute_pipeline(
        self,
        pipeline: PipelineGraph,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete pipeline.
        
        Args:
            pipeline: Pipeline graph to execute
            user_id: User identifier
        
        Returns:
            Dict with pipeline results
        """
        # Save pipeline to database
        with self.db_manager.get_session() as session:
            db_pipeline = Pipeline(
                id=pipeline.pipeline_id,
                pipeline_name=pipeline.name,
                user_id=user_id or "anonymous",
                status=TaskStatusEnum.RUNNING,
                task_ids=[],
                metadata={"graph": pipeline.to_dict()}
            )
            session.add(db_pipeline)
        
        try:
            # Get execution order
            execution_order = pipeline.get_execution_order()
            
            # Execute nodes in order
            for node_id in execution_order:
                node = pipeline.nodes[node_id]
                
                # Mark node as running
                node.status = "RUNNING"
                
                # Resolve inputs (static + mapped from upstream)
                try:
                    resolved_inputs = pipeline.resolve_node_inputs(node_id)
                except Exception as e:
                    node.status = "FAILED"
                    node.error = str(e)
                    raise RuntimeError(f"Failed to resolve inputs for {node_id}: {e}")
                
                # Get task class
                task_class = self.task_registry.get_task(node.task_name)
                if task_class is None:
                    node.status = "FAILED"
                    node.error = f"Task {node.task_name} not found"
                    raise ValueError(f"Task {node.task_name} not found in registry")
                
                # Create task instance
                task_instance = task_class()
                
                # Execute task
                try:
                    outputs = await task_instance.run(resolved_inputs)
                    node.status = "COMPLETED"
                    node.outputs = outputs
                except Exception as e:
                    node.status = "FAILED"
                    node.error = str(e)
                    raise RuntimeError(f"Task {node_id} failed: {e}")
            
            # Update pipeline status to completed
            with self.db_manager.get_session() as session:
                db_pipeline = session.query(Pipeline).filter_by(id=pipeline.pipeline_id).first()
                if db_pipeline:
                    db_pipeline.status = TaskStatusEnum.COMPLETED
                    db_pipeline.completed_at = datetime.utcnow()
                    db_pipeline.metadata = {"graph": pipeline.to_dict()}
            
            # Return results
            return {
                "pipeline_id": pipeline.pipeline_id,
                "status": "COMPLETED",
                "nodes": {
                    node_id: {
                        "task_name": node.task_name,
                        "status": node.status,
                        "outputs": node.outputs
                    }
                    for node_id, node in pipeline.nodes.items()
                }
            }
            
        except Exception as e:
            # Update pipeline status to failed
            with self.db_manager.get_session() as session:
                db_pipeline = session.query(Pipeline).filter_by(id=pipeline.pipeline_id).first()
                if db_pipeline:
                    db_pipeline.status = TaskStatusEnum.FAILED
                    db_pipeline.metadata = {
                        "graph": pipeline.to_dict(),
                        "error": str(e)
                    }
            
            raise
    
    async def execute_from_json(
        self,
        pipeline_json: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a pipeline from JSON definition.
        
        Args:
            pipeline_json: JSON string defining the pipeline
            user_id: User identifier
        
        Returns:
            Pipeline execution결과
        """
        pipeline = PipelineGraph.from_json(pipeline_json)
        return await self.execute_pipeline(pipeline, user_id)
