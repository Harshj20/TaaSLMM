"""Workflow executor for DAG execution."""

import asyncio
from typing import Dict, Any, AsyncGenerator, List, Set
from datetime import datetime
import uuid

from mcp_framework.server.tool_registry import get_tool_registry
from mcp_framework.storage.database import get_db_manager
from mcp_framework.storage.models import WorkflowExecution, ToolExecution
import structlog

logger = structlog.get_logger()


class WorkflowExecutor:
    """Executes workflow DAGs with dependency resolution."""
    
    def __init__(self):
        """Initialize executor."""
        self.tool_registry = get_tool_registry()
        self.db_manager = get_db_manager()
    
    def _topological_sort(self, dag: Dict[str, Any]) -> List[List[str]]:
        """
        Perform topological sort to get execution batches.
        
        Returns batches of nodes that can be executed in parallel.
        
        Args:
            dag: Workflow DAG with nodes and edges
        
        Returns:
            List of batches (each batch can be executed in parallel)
        """
        nodes = {node["id"]: node for node in dag.get("nodes", [])}
        edges = dag.get("edges", [])
        
        # Build adjacency list and in-degree
        in_degree = {node_id: 0 for node_id in nodes}
        adjacency = {node_id: [] for node_id in nodes}
        
        for edge in edges:
            from_node = edge["from"]
            to_node = edge["to"]
            adjacency[from_node].append(to_node)
            in_degree[to_node] += 1
        
        # Get nodes with no dependencies
        batches = []
        current_batch = [node_id for node_id, degree in in_degree.items() if degree == 0]
        
        while current_batch:
            batches.append(current_batch)
            next_batch = []
            
            for node_id in current_batch:
                for neighbor in adjacency[node_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_batch.append(neighbor)
            
            current_batch = next_batch
        
        # Check for cycles
        if sum(in_degree.values()) > 0:
            raise ValueError("Workflow DAG contains cycles")
        
        return batches
    
    async def execute_streaming(
        self,
        dag: Dict[str, Any],
        user_id: str = "anonymous"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute workflow with streaming progress.
        
        Args:
            dag: Workflow DAG
            user_id: User identifier
        
        Yields:
            Progress events
        """
        workflow_id = str(uuid.uuid4())
        
        # Create workflow execution record
        with self.db_manager.get_session() as session:
            workflow = WorkflowExecution(
                id=workflow_id,
                workflow_dag=dag,
                status="RUNNING",
                started_at=datetime.utcnow()
            )
            session.add(workflow)
        
        try:
            # Get execution order
            batches = self._topological_sort(dag)
            total_nodes = sum(len(batch) for batch in batches)
            completed_nodes = 0
            
            # Yield start event
            yield {
                "type": "start",
                "workflow_id": workflow_id,
                "total_nodes": total_nodes
            }
            
            # Store intermediate results
            results = {}
            
            # Execute batches
            for batch_idx, batch in enumerate(batches):
                # Execute batch in parallel
                tasks = []
                for node_id in batch:
                    task = self._execute_node(workflow_id, node_id, dag, results)
                    tasks.append(task)
                
                # Wait for batch completion
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for node_id, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        # Handle error
                        error_msg = str(result)
                        
                        yield {
                            "type": "node_failed",
                            "node_id": node_id,
                            "error": error_msg
                        }
                        
                        # Update workflow as failed
                        with self.db_manager.get_session() as session:
                            workflow = session.query(WorkflowExecution).filter_by(id=workflow_id).first()
                            if workflow:
                                workflow.status = "FAILED"
                                workflow.error_message = f"Node {node_id} failed: {error_msg}"
                                workflow.completed_at = datetime.utcnow()
                        
                        return
                    
                    # Store result
                    results[node_id] = result
                    completed_nodes += 1
                    
                    # Yield progress
                    yield {
                        "type": "node_completed",
                        "node_id": node_id,
                        "progress": completed_nodes / total_nodes,
                        "result": result
                    }
            
            # Update workflow as completed
            with self.db_manager.get_session() as session:
                workflow = session.query(WorkflowExecution).filter_by(id=workflow_id).first()
                if workflow:
                    workflow.status = "COMPLETED"
                    workflow.progress = 1.0
                    workflow.completed_at = datetime.utcnow()
                    workflow.results = results
            
            yield {
                "type": "workflow_completed",
                "workflow_id": workflow_id,
                "results": results
            }
        
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            
            # Update workflow as failed
            with self.db_manager.get_session() as session:
                workflow = session.query(WorkflowExecution).filter_by(id=workflow_id).first()
                if workflow:
                    workflow.status = "FAILED"
                    workflow.error_message = str(e)
                    workflow.completed_at = datetime.utcnow()
            
            yield {
                "type": "workflow_failed",
                "workflow_id": workflow_id,
                "error": str(e)
            }
    
    async def _execute_node(
        self,
        workflow_id: str,
        node_id: str,
        dag: Dict[str, Any],
        intermediate_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single node in the workflow."""
        # Find node definition
        node = next((n for n in dag["nodes"] if n["id"] == node_id), None)
        if not node:
            raise ValueError(f"Node {node_id} not found in DAG")
        
        tool_name = node["tool"]
        inputs = node.get("inputs", {})
        
        # Resolve inputs from intermediate results
        input_mappings = node.get("input_mappings", {})
        for source_key, target_key in input_mappings.items():
            if "." in source_key:
                source_node_id, output_key = source_key.split(".", 1)
                if source_node_id in intermediate_results:
                    source_result = intermediate_results[source_node_id]
                    if output_key in source_result:
                        inputs[target_key] = source_result[output_key]
        
        # Create tool execution record
        tool_exec_id = str(uuid.uuid4())
        with self.db_manager.get_session() as session:
            tool_exec = ToolExecution(
                id=tool_exec_id,
                workflow_id=workflow_id,
                tool_name=tool_name,
                inputs=inputs,
                status="RUNNING",
                started_at=datetime.utcnow()
            )
            session.add(tool_exec)
        
        try:
            # Get tool and execute
            tool_class = self.tool_registry.get_tool(tool_name)
            if not tool_class:
                raise ValueError(f"Tool {tool_name} not found")
            
            tool_instance = tool_class()
            result = await tool_instance.execute(inputs)
            
            # Update tool execution as completed
            with self.db_manager.get_session() as session:
                tool_exec = session.query(ToolExecution).filter_by(id=tool_exec_id).first()
                if tool_exec:
                    tool_exec.status = "COMPLETED"
                    tool_exec.outputs = result
                    tool_exec.completed_at = datetime.utcnow()
            
            return result
        
        except Exception as e:
            # Update tool execution as failed
            with self.db_manager.get_session() as session:
                tool_exec = session.query(ToolExecution).filter_by(id=tool_exec_id).first()
                if tool_exec:
                    tool_exec.status = "FAILED"
                    tool_exec.error_message = str(e)
                    tool_exec.completed_at = datetime.utcnow()
            
            raise
