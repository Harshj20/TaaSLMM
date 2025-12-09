"""Database models for TaaS server."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TaskStatusEnum(str, Enum):
    """Task status enumeration."""
    
    UNKNOWN = "UNKNOWN"
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Task(Base):
    """Task execution record."""
    
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, index=True)
    task_name = Column(String, nullable=False, index=True)
    status = Column(SAEnum(TaskStatusEnum), default=TaskStatusEnum.PENDING, index=True)
    user_id = Column(String, index=True)
    
    # Task data
    inputs = Column(JSON)  # JSON-serialized inputs
    outputs = Column(JSON)  # JSON-serialized outputs
    metadata = Column(JSON)  # Additional metadata
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Progress tracking
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    artifacts = relationship("Artifact", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("Log", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name={self.task_name}, status={self.status})>"


class Artifact(Base):
    """Artifact metadata."""
    
    __tablename__ = "artifacts"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    path = Column(String, nullable=False)  # Local or S3 path
    size = Column(Integer, default=0)
    content_type = Column(String)
    version = Column(String, default="1.0")
    
    # Relationships
    task_id = Column(String, ForeignKey("tasks.id"))
    task = relationship("Task", back_populates="artifacts")
    
    # Metadata
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self) -> str:
        return f"<Artifact(id={self.id}, name={self.name}, size={self.size})>"


class Pipeline(Base):
    """Pipeline execution record."""
    
    __tablename__ = "pipelines"
    
    id = Column(String, primary_key=True, index=True)
    pipeline_name = Column(String, nullable=False)
    user_id = Column(String, index=True)
    status = Column(SAEnum(TaskStatusEnum), default=TaskStatusEnum.PENDING)
    
    # Pipeline data
    task_ids = Column(JSON)  # List of task IDs in execution order
    metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Pipeline(id={self.id}, name={self.pipeline_name}, status={self.status})>"


class TaskDefinitionModel(Base):
    """Registry of available task definitions."""
    
    __tablename__ = "task_definitions"
    
    name = Column(String, primary_key=True, index=True)
    description = Column(Text)
    version = Column(String, default="1.0")
    input_schema = Column(JSON)  # JSON Schema
    output_schema = Column(JSON)  # JSON Schema
    dependencies = Column(JSON)  # List of task dependencies
    metadata = Column(JSON)
    
    # Registration info
    registered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<TaskDefinition(name={self.name}, version={self.version})>"


class Log(Base):
    """Task log entries."""
    
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String, index=True)  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text)
    context = Column(JSON)  # Additional context
    
    # Relationships
    task = relationship("Task", back_populates="logs")
    
    def __repr__(self) -> str:
        return f"<Log(task_id={self.task_id}, level={self.level}, timestamp={self.timestamp})>"
