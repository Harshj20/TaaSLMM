"""Pipeline graph system for chaining tasks with intermediate results."""

import uuid
from typing import Dict, Any, List, Optional, Set
from enum import Enum
import json


class PipelineNode:
    """Represents a single task in a pipeline graph."""
    
    def __init__(
        self,
        node_id: str,
        task_name: str,
        inputs: Dict[str, Any],
        input_mappings: Optional[Dict[str, str]] = None
    ):
        """
        Initialize a pipeline node.
        
        Args:
            node_id: Unique identifier for this node in the pipeline
            task_name: Name of the task to execute
            inputs: Static inputs for this task
            input_mappings: Map upstream node outputs to this node's inputs
                           Format: {"upstream_node_id.output_key": "my_input_key"}
        """
        self.node_id = node_id
        self.task_name = task_name
        self.inputs = inputs
        self.input_mappings = input_mappings or {}
        self.status = "PENDING"
        self.outputs: Dict[str, Any] = {}
        self.error: Optional[str] = None


class PipelineGraph:
    """
    Directed acyclic graph (DAG) representing a task pipeline.
    
    Supports:
    - Global inputs from user
    - Intermediate results passed between tasks
    - Dependency resolution and execution order
    """
    
    def __init__(self, pipeline_id: Optional[str] = None, name: Optional[str] = None):
        """Initialize an empty pipeline graph."""
        self.pipeline_id = pipeline_id or str(uuid.uuid4())
        self.name = name or f"pipeline_{self.pipeline_id[:8]}"
        self.nodes: Dict[str, PipelineNode] = {}
        self.global_inputs: Dict[str, Any] = {}
        self.edges: Dict[str, List[str]] = {}  # node_id -> [dependent_node_ids]
    
    def add_node(
        self,
        node_id: str,
        task_name: str,
        inputs: Optional[Dict[str, Any]] = None,
        input_mappings: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Add a node to the pipeline.
        
        Args:
            node_id: Unique identifier for this node
            task_name: Task to execute
            inputs: Static inputs
            input_mappings: Dynamic inputs from upstream nodes
        """
        if node_id in self.nodes:
            raise ValueError(f"Node {node_id} already exists in pipeline")
        
        self.nodes[node_id] = PipelineNode(
            node_id=node_id,
            task_name=task_name,
            inputs=inputs or {},
            input_mappings=input_mappings or {}
        )
        self.edges[node_id] = []
    
    def add_edge(self, from_node: str, to_node: str) -> None:
        """
        Add a dependency edge (from_node must complete before to_node).
        
        Args:
            from_node: Source node ID
            to_node: Destination node ID
        """
        if from_node not in self.nodes:
            raise ValueError(f"Node {from_node} not found")
        if to_node not in self.nodes:
            raise ValueError(f"Node {to_node} not found")
        
        if to_node not in self.edges[from_node]:
            self.edges[from_node].append(to_node)
    
    def set_global_inputs(self, inputs: Dict[str, Any]) -> None:
        """Set global inputs provided by the user."""
        self.global_inputs = inputs
    
    def get_execution_order(self) -> List[str]:
        """
        Get topologically sorted execution order.
        
        Returns:
            List of node IDs in execution order
        
        Raises:
            ValueError: If graph has cycles
        """
        # Kahn's algorithm for topological sort
        in_degree = {node_id: 0 for node_id in self.nodes}
        
        for node_id in self.nodes:
            for dependent in self.edges[node_id]:
                in_degree[dependent] += 1
        
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for dependent in self.edges[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        if len(result) != len(self.nodes):
            raise ValueError("Pipeline graph contains cycles")
        
        return result
    
    def resolve_node_inputs(self, node_id: str) -> Dict[str, Any]:
        """
        Resolve all inputs for a node (static + mapped from upstream).
        
        Args:
            node_id: Node to resolve inputs for
        
        Returns:
            Complete input dictionary
        """
        node = self.nodes[node_id]
        resolved_inputs = {**node.inputs}  # Start with static inputs
        
        # Add global inputs
        for key, value in self.global_inputs.items():
            if key not in resolved_inputs:
                resolved_inputs[key] = value
        
        # Add mapped inputs from upstream nodes
        for mapping_key, input_key in node.input_mappings.items():
            # mapping_key format: "upstream_node_id.output_key"
            if "." in mapping_key:
                upstream_node_id, output_key = mapping_key.split(".", 1)
                
                if upstream_node_id not in self.nodes:
                    raise ValueError(f"Upstream node {upstream_node_id} not found")
                
                upstream_node = self.nodes[upstream_node_id]
                
                if upstream_node.status != "COMPLETED":
                    raise ValueError(f"Upstream node {upstream_node_id} not completed")
                
                if output_key not in upstream_node.outputs:
                    raise ValueError(
                        f"Output key {output_key} not found in {upstream_node_id}"
                    )
                
                resolved_inputs[input_key] = upstream_node.outputs[output_key]
        
        return resolved_inputs
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize pipeline to dictionary."""
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "global_inputs": self.global_inputs,
            "nodes": [
                {
                    "node_id": node.node_id,
                    "task_name": node.task_name,
                    "inputs": node.inputs,
                    "input_mappings": node.input_mappings,
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {"from": from_node, "to": to_node}
                for from_node, to_nodes in self.edges.items()
                for to_node in to_nodes
            ]
        }
    
    def to_json(self) -> str:
        """Serialize pipeline to JSON."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineGraph":
        """Deserialize pipeline from dictionary."""
        pipeline = cls(
            pipeline_id=data.get("pipeline_id"),
            name=data.get("name")
        )
        
        pipeline.set_global_inputs(data.get("global_inputs", {}))
        
        # Add nodes
        for node_data in data.get("nodes", []):
            pipeline.add_node(
                node_id=node_data["node_id"],
                task_name=node_data["task_name"],
                inputs=node_data.get("inputs", {}),
                input_mappings=node_data.get("input_mappings", {})
            )
        
        # Add edges
        for edge in data.get("edges", []):
            pipeline.add_edge(edge["from"], edge["to"])
        
        return pipeline
    
    @classmethod
    def from_json(cls, json_str: str) -> "PipelineGraph":
        """Deserialize pipeline from JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# Example pipeline definitions

def create_finetune_pipeline() -> PipelineGraph:
    """
    Example: Complete finetuning pipeline.
    
    Flow:
    1. load_dataset -> dataset_id
    2. load_config -> config_id
    3. load_lora -> lora_id (optional)
    4. finetune(dataset_id, config_id, lora_id) -> model_id
    """
    pipeline = PipelineGraph(name="finetune_pipeline")
    
    # Add nodes
    pipeline.add_node(
        node_id="load_dataset",
        task_name="load_dataset",
        inputs={}  # Will come from global inputs
    )
    
    pipeline.add_node(
        node_id="load_config",
        task_name="load_config",
        inputs={}
    )
    
    pipeline.add_node(
        node_id="finetune",
        task_name="finetune",
        inputs={},
        input_mappings={
            "load_dataset.dataset_id": "dataset_id",
            "load_config.config_id": "config_id"
        }
    )
    
    # Add dependencies
    pipeline.add_edge("load_dataset", "finetune")
    pipeline.add_edge("load_config", "finetune")
    
    return pipeline


def create_full_ml_pipeline() -> PipelineGraph:
    """
    Example: Full ML workflow with evaluation.
    
    Flow:
    1. load_dataset
    2. load_config  
    3. finetune(dataset_id, config_id) -> model_id
    4. ptq(model_id) -> quantized_model_id
    5. evaluate(quantized_model_id, dataset_id) -> metrics
    """
    pipeline = PipelineGraph(name="full_ml_pipeline")
    
    # Load data and config
    pipeline.add_node("load_dataset", "load_dataset", {})
    pipeline.add_node("load_config", "load_config", {})
    
    # Finetune
    pipeline.add_node(
        "finetune",
        "finetune",
        {},
        {
            "load_dataset.dataset_id": "dataset_id",
            "load_config.config_id": "config_id"
        }
    )
    
    # Quantize
    pipeline.add_node(
        "ptq",
        "ptq",
        {},
        {"finetune.model_id": "model_id"}
    )
    
    # Evaluate
    pipeline.add_node(
        "evaluate",
        "evaluate",
        {},
        {
            "ptq.quantized_model_id": "model_id",
            "load_dataset.dataset_id": "dataset_id"
        }
    )
    
    # Dependencies
    pipeline.add_edge("load_dataset", "finetune")
    pipeline.add_edge("load_config", "finetune")
    pipeline.add_edge("finetune", "ptq")
    pipeline.add_edge("ptq", "evaluate")
    pipeline.add_edge("load_dataset", "evaluate")
    
    return pipeline
