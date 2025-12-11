"""Example tasks package."""

# Import all example tasks to trigger registration
from taas_server.tasks.examples import config_tasks
from taas_server.tasks.examples import microservice_tasks
from taas_server.tasks.examples import macrotask_tasks

__all__ = ["config_tasks", "microservice_tasks", "macrotask_tasks"]
