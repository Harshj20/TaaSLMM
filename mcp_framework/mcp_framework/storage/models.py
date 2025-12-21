"""Database models for MCP Framework."""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid() -> str:
    """Generate UUID string."""
    return str(uuid.uuid4())


class Session(Base):
    """User session model."""
    
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    context = Column(JSON, default=dict)
    preferences = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    events = relationship("SessionEvent", back_populates="session", cascade="all, delete-orphan")


class SessionEvent(Base):
    """Session event log."""
    
    __tablename__ = "session_events"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    event_data = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    session = relationship("Session", back_populates="events")


class ErrorSignature(Base):
    """Error signature for debug context."""
    
    __tablename__ = "error_signatures"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    error_type = Column(String, nullable=False)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text)
    signature_hash = Column(String, unique=True, nullable=False, index=True)
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    occurrence_count = Column(Integer, default=1)
    
    # Relationships
    resolutions = relationship("Resolution", back_populates="error_signature", cascade="all, delete-orphan")


class Resolution(Base):
    """Resolution for an error signature."""
    
    __tablename__ = "resolutions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    error_signature_id = Column(String, ForeignKey("error_signatures.id"), nullable=False, index=True)
    resolution_type = Column(String, nullable=False)
    resolution_data = Column(JSON, nullable=False)
    success_rate = Column(Float, default=0.0)
    applied_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    error_signature = relationship("ErrorSignature", back_populates="resolutions")


class WorkflowExecution(Base):
    """Workflow execution tracking."""
    
    __tablename__ = "workflow_executions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=True, index=True)
    workflow_dag = Column(JSON, nullable=False)
    status = Column(String, default="PENDING", nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    results = Column(JSON, default=dict)
    
    # Relationships
    tool_executions = relationship("ToolExecution", back_populates="workflow", cascade="all, delete-orphan")


class ToolExecution(Base):
    """Individual tool execution within a workflow."""
    
    __tablename__ = "tool_executions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("workflow_executions.id"), nullable=False, index=True)
    tool_name = Column(String, nullable=False)
    inputs = Column(JSON, nullable=False)
    outputs = Column(JSON, default=dict)
    status = Column(String, default="PENDING", nullable=False)
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    container_id = Column(String)  # For isolated executions
    
    # Relationships
    workflow = relationship("WorkflowExecution", back_populates="tool_executions")
