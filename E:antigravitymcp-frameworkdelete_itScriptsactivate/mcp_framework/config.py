"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "postgresql://localhost/mcp_framework"
    
    # Storage
    artifact_store_path: str = "./artifacts"
    model_store_path: str = "./models"
    storage_backend: str = "local"  # local or s3
    s3_bucket: Optional[str] = None
    s3_region: Optional[str] = "us-east-1"
    
    # Docker
    docker_base_url: str = "unix://var/run/docker.sock"
    training_image: str = "ml-training:latest"
    
    # LLM
    llm_provider: str = "openai"  # openai, anthropic, local
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_model: str = "gpt-4-turbo-preview"
    
    # Vector DB
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    
    # Logging
    log_level: str = "INFO"


# Global settings instance
settings = Settings()
