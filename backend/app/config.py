"""
Configuration management using pydantic-settings.

This is a placeholder that will be fully implemented in Phase 1.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://chatbot_user:password@localhost:5432/cloudvelous_chatbot"
    
    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    # GitHub Configuration
    GITHUB_TOKEN: Optional[str] = None
    
    # Admin Authentication
    ADMIN_JWT_SECRET: str = "change-me-in-production"
    ADMIN_API_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Embedding Model Configuration
    EMBED_MODEL: str = "all-MiniLM-L6-v2"
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = "openai"
    
    # Workflow Learning Configuration
    WORKFLOW_EMBEDDING_ENABLED: bool = True
    WORKFLOW_SIMILARITY_WEIGHT: float = 0.3
    FEEDBACK_THRESHOLD_FOR_RETRAIN: int = 50
    MIN_WORKFLOW_CLUSTER_SIZE: int = 3
    
    # Accuracy Tuning
    CHUNK_WEIGHT_ADJUSTMENT_RATE: float = 0.1
    MIN_CHUNK_WEIGHT: float = 0.5
    MAX_CHUNK_WEIGHT: float = 2.0
    
    # Retrieval Configuration
    TOP_K_RETRIEVAL: int = 5
    ALLOWED_QUESTION_SIMILARITY_THRESHOLD: float = 0.85
    WORKFLOW_BOOST_FACTOR: float = 1.2
    
    # Server Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

