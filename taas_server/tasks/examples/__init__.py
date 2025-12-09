"""Example tasks package."""

# Import all example tasks to trigger registration
from taas_server.tasks.examples import config_tasks

__all__ = ["config_tasks"]
