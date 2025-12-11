"""Example macrotask tasks (main user-facing tasks)."""

from typing import Dict, Any
import uuid

from taas_server.tasks.base_task import BaseTask, TaskType
from taas_server.tasks.task_registry import register_task


@register_task
class FinetuneTask(BaseTask):
    """MacroTask: Finetune a model (runs in isolated environment)."""
    
    @classmethod
    def get_name(cls) -> str:
        return "finetune"
    
    @classmethod
    def get_description(cls) -> str:
        return "Finetune a language model on a dataset with LoRA"
    
    @classmethod
    def get_version(cls) -> str:
        return "1.0.0"
    
    @classmethod
    def get_task_type(cls) -> TaskType:
        return TaskType.MACROTASK
    
    @classmethod
    def get_input_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "model_name": {
                    "type": "string",
                    "description": "Base model to finetune (e.g., 'meta-llama/Llama-2-7b')"
                },
                "dataset_id": {
                    "type": "string",
                    "description": "Dataset ID from load_dataset task"
                },
                "config_id": {
                    "type": "string",
                    "description": "Training config ID from load_config task"
                },
                "lora_id": {
                    "type": "string",
                    "description": "LoRA adapter ID (optional)"
                },
                "epochs": {
                    "type": "integer",
                    "description": "Number of training epochs",
                    "default": 3
                },
                "learning_rate": {
                    "type": "number",
                    "description": "Learning rate",
                    "default": 0.0001
                }
            },
            "required": ["model_name", "dataset_id", "config_id"]
        }
    
    @classmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "model_id": {
                    "type": "string",
                    "description": "Unique identifier for finetuned model"
                },
                "model_path": {
                    "type": "string",
                    "description": "Path to saved model"
                },
                "metrics": {
                    "type": "object",
                    "description": "Training metrics (loss, accuracy, etc.)"
                }
            },
            "required": ["model_id", "model_path"]
        }
    
    @classmethod
    def get_output_mappings(cls) -> Dict[str, str]:
        return {
            "model_id": "model_id",
            "model_path": "model_path"
        }
    
    @classmethod
    def get_dependencies(cls) -> list[str]:
        return ["load_dataset", "load_config"]
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute finetuning in isolated container."""
        model_name = inputs["model_name"]
        dataset_id = inputs["dataset_id"]
        epochs = inputs.get("epochs", 3)
        
        model_id = f"model_{uuid.uuid4().hex[:12]}"
        model_path = f"/artifacts/models/{model_id}"
        
        # Mock training process
        self.update_progress(0.1, "Setting up training environment...")
        self.update_progress(0.2, "Loading model...")
        self.update_progress(0.3, "Loading dataset...")
        
        for epoch in range(1, epochs + 1):
            progress = 0.3 + (0.6 * epoch / epochs)
            self.update_progress(progress, f"Training epoch {epoch}/{epochs}...")
        
        self.update_progress(0.95, "Saving model...")
        self.update_progress(1.0, "Training complete")
        
        return {
            "model_id": model_id,
            "model_path": model_path,
            "metrics": {
                "final_loss": 0.42,
                "accuracy": 0.89,
                "training_time_seconds": 3600
            }
        }


@register_task
class PTQTask(BaseTask):
    """MacroTask: Post-Training Quantization."""
    
    @classmethod
    def get_name(cls) -> str:
        return "ptq"
    
    @classmethod
    def get_description(cls) -> str:
        return "Apply post-training quantization to a model"
    
    @classmethod
    def get_version(cls) -> str:
        return "1.0.0"
    
    @classmethod
    def get_task_type(cls) -> TaskType:
        return TaskType.MACROTASK
    
    @classmethod
    def get_input_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "model_id": {
                    "type": "string",
                    "description": "Model ID to quantize"
                },
                "quantization_bits": {
                    "type": "integer",
                    "description": "Number of bits (4, 8, 16)",
                    "default": 8
                },
                "calibration_dataset_id": {
                    "type": "string",
                    "description": "Dataset for calibration (optional)"
                }
            },
            "required": ["model_id"]
        }
    
    @classmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "quantized_model_id": {
                    "type": "string"
                },
                "quantized_model_path": {
                    "type": "string"
                },
                "compression_ratio": {
                    "type": "number"
                }
            },
            "required": ["quantized_model_id"]
        }
    
    @classmethod
    def get_output_mappings(cls) -> Dict[str, str]:
        return {
            "quantized_model_id": "model_id"
        }
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PTQ."""
        model_id = inputs["model_id"]
        bits = inputs.get("quantization_bits", 8)
        
        quantized_id = f"quantized_{uuid.uuid4().hex[:12]}"
        
        self.update_progress(0.2, "Loading model...")
        self.update_progress(0.5, f"Quantizing to {bits}-bit...")
        self.update_progress(0.9, "Saving quantized model...")
        self.update_progress(1.0, "Quantization complete")
        
        return {
            "quantized_model_id": quantized_id,
            "quantized_model_path": f"/artifacts/models/{quantized_id}",
            "compression_ratio": 4.2
        }


@register_task
class EvaluateTask(BaseTask):
    """MacroTask: Evaluate model performance."""
    
    @classmethod
    def get_name(cls) -> str:
        return "evaluate"
    
    @classmethod
    def get_description(cls) -> str:
        return "Evaluate a model on a dataset and return metrics"
    
    @classmethod
    def get_version(cls) -> str:
        return "1.0.0"
    
    @classmethod
    def get_task_type(cls) -> TaskType:
        return TaskType.MACROTASK
    
    @classmethod
    def get_input_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "model_id": {
                    "type": "string",
                    "description": "Model to evaluate"
                },
                "dataset_id": {
                    "type": "string",
                    "description": "Evaluation dataset"
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Metrics to compute (e.g., ['accuracy', 'f1'])",
                    "default": ["accuracy", "loss"]
                }
            },
            "required": ["model_id", "dataset_id"]
        }
    
    @classmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "metrics": {
                    "type": "object",
                    "description": "Evaluation metrics"
                },
                "report_path": {
                    "type": "string",
                    "description": "Path to detailed evaluation report"
                }
            },
            "required": ["metrics"]
        }
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute evaluation."""
        model_id = inputs["model_id"]
        dataset_id = inputs["dataset_id"]
        
        self.update_progress(0.2, "Loading model and dataset...")
        self.update_progress(0.5, "Running evaluation...")
        self.update_progress(0.9, "Computing metrics...")
        self.update_progress(1.0, "Evaluation complete")
        
        report_id = f"report_{uuid.uuid4().hex[:12]}"
        
        return {
            "metrics": {
                "accuracy": 0.92,
                "f1_score": 0.90,
                "precision": 0.91,
                "recall": 0.89,
                "loss": 0.35
            },
            "report_path": f"/artifacts/reports/{report_id}.json"
        }
