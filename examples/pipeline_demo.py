"""Example: Pipeline execution demonstration."""

import asyncio
import json
from taas_server.tasks.pipeline_graph import PipelineGraph, create_finetune_pipeline, create_full_ml_pipeline
from taas_server.tasks.pipeline_executor import PipelineExecutor
from taas_server.db.database import init_database
from taas_server.tasks.examples import config_tasks, microservice_tasks, macrotask_tasks


async def example_finetune_pipeline():
    """Example: Simple finetune pipeline with microservices."""
    print("="*60)
    print("Example 1: Finetune Pipeline")
    print("="*60)
    
    # Create pipeline
    pipeline = create_finetune_pipeline()
    
    # Set global inputs from user
    pipeline.set_global_inputs({
        "dataset_path": "huggingface:squad",
        "config_dict": {
            "model_name": "meta-llama/Llama-2-7b",
            "learning_rate": 0.0001,
            "batch_size": 32
        }
    })
    
    print("\nPipeline Graph:")
    print(json.dumps(pipeline.to_dict(), indent=2))
    
    print("\nExecution Order:")
    print(" -> ".join(pipeline.get_execution_order()))
    
    # Execute pipeline
    print("\n" + "-"*60)
    print("Executing Pipeline...")
    print("-"*60)
    
    executor = PipelineExecutor()
    results = await executor.execute_pipeline(pipeline)
    
    print("\n✓ Pipeline Completed!")
    print(f"  Pipeline ID: {results['pipeline_id']}")
    print(f"  Status: {results['status']}")
    
    print("\nNode Results:")
    for node_id, node_result in results['nodes'].items():
        print(f"\n  [{node_id}] {node_result['task_name']}")
        print(f"    Status: {node_result['status']}")
        print(f"    Outputs: {json.dumps(node_result['outputs'], indent=6)}")


async def example_full_ml_pipeline():
    """Example: Full ML workflow (finetune -> quantize -> evaluate)."""
    print("\n" + "="*60)
    print("Example 2: Full ML Pipeline (Finetune -> PTQ -> Evaluate)")
    print("="*60)
    
    # Create pipeline
    pipeline = create_full_ml_pipeline()
    
    # Set global inputs
    pipeline.set_global_inputs({
        "dataset_path": "huggingface:squad",
        "config_dict": {
            "model_name": "meta-llama/Llama-2-7b",
            "learning_rate": 0.0001,
            "epochs": 3
        }
    })
    
    print("\nPipeline Graph:")
    execution_order = pipeline.get_execution_order()
    print(f"Nodes: {len(execution_order)}")
    print(f"Execution Order: {' -> '.join(execution_order)}")
    
    # Execute pipeline
    print("\n" + "-"*60)
    print("Executing Full ML Pipeline...")
    print("-"*60)
    
    executor = PipelineExecutor()
    results = await executor.execute_pipeline(pipeline)
    
    print("\n✓ Pipeline Completed!")
    
    # Show key results
    print("\nKey Results:")
    
    finetune_outputs = results['nodes']['finetune']['outputs']
    print(f"\n  Finetuned Model:")
    print(f"    Model ID: {finetune_outputs['model_id']}")
    print(f"    Metrics: {finetune_outputs['metrics']}")
    
    ptq_outputs = results['nodes']['ptq']['outputs']
    print(f"\n  Quantized Model:")
    print(f"    Model ID: {ptq_outputs['quantized_model_id']}")
    print(f"    Compression: {ptq_outputs['compression_ratio']}x")
    
    eval_outputs = results['nodes']['evaluate']['outputs']
    print(f"\n  Evaluation:")
    print(f"    Metrics: {json.dumps(eval_outputs['metrics'], indent=6)}")


async def example_custom_pipeline():
    """Example: Custom pipeline defined from scratch."""
    print("\n" + "="*60)
    print("Example 3: Custom Pipeline (Load Dataset -> Load Config)")
    print("="*60)
    
    # Create custom pipeline
    pipeline = PipelineGraph(name="custom_pipeline")
    
    # Add nodes
    pipeline.add_node(
        node_id="load_data",
        task_name="load_dataset",
        inputs={"dataset_path": "custom/path/data.jsonl"}
    )
    
    pipeline.add_node(
        node_id="load_cfg",
        task_name="load_config",
        inputs={}
    )
    
    # Set global inputs
    pipeline.set_global_inputs({
        "config_dict": {
            "model": "gpt-4",
            "temperature": 0.7
        }
    })
    
    # Execute
    executor = PipelineExecutor()
    results = await executor.execute_pipeline(pipeline)
    
    print("\n✓ Custom Pipeline Completed!")
    print(f"\nDataset ID: {results['nodes']['load_data']['outputs']['dataset_id']}")
    print(f"Config ID: {results['nodes']['load_cfg']['outputs']['config_id']}")


async def main():
    """Run all examples."""
    # Initialize database  init_database("sqlite:///pipeline_demo.db")
    
    await example_finetune_pipeline()
    await example_full_ml_pipeline()
    await example_custom_pipeline()
    
    print("\n" + "="*60)
    print("All Pipeline Examples Completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
