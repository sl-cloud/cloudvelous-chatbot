"""
Configuration management using pydantic-settings.

This is a placeholder that will be fully implemented in Phase 1.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    ENV: str = "development"

    # Database Configuration
    DATABASE_URL: str = "postgresql://chatbot_user:password@localhost:5432/cloudvelous_chatbot"

    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # GitHub Configuration
    GITHUB_TOKEN: Optional[str] = None

    # Admin Authentication
    ADMIN_JWT_SECRET: str = "change-me-in-development"
    ADMIN_API_KEY: str = "change-me-in-development"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    @field_validator("ADMIN_JWT_SECRET", "ADMIN_API_KEY")
    @classmethod
    def validate_production_secrets(cls, v: str, info) -> str:
        """Ensure production environments don't use default secrets with strong validation."""
        env = os.getenv("ENV", "development")
        
        # Fail fast if using default secrets in production
        if env == "production" and v.startswith("change-me"):
            raise ValueError(
                f"{info.field_name} must be set via environment variables in production. "
                f"Using default secrets in production is a security risk."
            )
        
        # Enforce minimum length for production secrets
        if env == "production" and len(v) < 32:
            raise ValueError(
                f"{info.field_name} must be at least 32 characters in production. "
                f"Current length: {len(v)}"
            )
        
        # Warn about weak secrets (but allow for backward compatibility)
        if env == "production" and v.isalnum() and len(v) < 64:
            import warnings
            warnings.warn(
                f"{info.field_name} should include special characters and be at least 64 characters "
                f"for maximum security. Consider using a cryptographically secure random string.",
                UserWarning
            )
        
        return v
    
    # Embedding Model Configuration
    EMBED_MODEL: str = "text-embedding-3-small"
    
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

    # CORS Configuration
    CORS_ORIGINS: str = "*"  # Comma-separated list of allowed origins, or "*" for all
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "GET,POST,PUT,DELETE,OPTIONS"
    CORS_ALLOW_HEADERS: str = "Content-Type,Authorization,X-API-Key,X-Request-ID"

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False  # Set to True for production JSON logs

    # Admin Configuration
    SESSION_LIST_PAGE_SIZE: int = 20
    MAX_BULK_FEEDBACK_SIZE: int = 100

    # Rate Limiting Configuration
    RATE_LIMITING_ENABLED: bool = True  # Disable in tests

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

