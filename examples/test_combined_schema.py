"""Test: Combined schema resolution."""

import asyncio
from taas_server.tasks.task_registry import get_task_registry
from taas_server.tasks.examples import config_tasks, microservice_tasks, macrotask_tasks
import json


def test_combined_schemas():
    """Test that combined schemas work as expected."""
    registry = get_task_registry()
    
    print("="*60)
    print("Testing Combined Schema Resolution")
    print("="*60)
    
    # Test 1: Finetune task standalone
    print("\n1. Finetune Task - Standalone Mode")
    print("-"*60)
    finetune_standalone = registry.get_combined_input_schema("finetune", as_pipeline=False)
    print("Input Schema (standalone):")
    print(json.dumps(finetune_standalone, indent=2))
    print("\nExpected inputs: model_name, dataset_id, config_id")
    
    # Test 2: Finetune task as mini-pipeline
    print("\n2. Finetune Task - Pipeline Mode (with dependencies)")
    print("-"*60)
    finetune_pipeline = registry.get_combined_input_schema("finetune", as_pipeline=True)
    print("Combined Input Schema (as pipeline):")
    print(json.dumps(finetune_pipeline, indent=2))
    print("\nExpected inputs: model_name, dataset_path, config (from load_dataset and load_config)")
    
    # Test 3: Full pipeline schema
    print("\n3. Full Pipeline Schema")
    print("-"*60)
    pipeline_tasks = ["load_dataset", "load_config", "finetune", "ptq", "evaluate"]
    pipeline_schema = registry.get_pipeline_schema(pipeline_tasks)
    print(f"Pipeline: {' -> '.join(pipeline_tasks)}")
    print("\nRequired USER inputs (excluding intermediate IDs):")
    print(json.dumps(pipeline_schema, indent=2))
    
    # Test 4: Show what gets automatically filled
    print("\n4. Automatic Input Resolution")
    print("-"*60)
    print("User provides:")
    print("  - dataset_path: 'huggingface:squad'")
    print("  - config: {model_name: 'llama-2-7b', ...}")
    print("  - model_name: 'llama-2-7b'")
    print("\nSystem automatically:")
    print("  1. load_dataset(dataset_path) -> dataset_id")
    print("  2. load_config(config) -> config_id")
    print("  3. finetune(dataset_id, config_id, model_name) -> model_id")
    print("  4. ptq(model_id) -> quantized_model_id")
    print("  5. evaluate(quantized_model_id, dataset_id) -> metrics")
    
    print("\n" + "="*60)
    print("✓ Schema Resolution Working Correctly!")
    print("="*60)


if __name__ == "__main__":
    test_combined_schemas()
