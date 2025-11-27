"""
Application configuration constants with environment variable support.
"""

import os
from typing import List


class Config:
    """Application configuration with environment variable support."""
    
    # Model configuration
    MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3.2:3b")
    
    # RAG configuration
    RAG_MAX_DISTANCE: float = float(os.getenv("RAG_MAX_DISTANCE", "0.8"))
    RAG_TOP_DOCS: int = int(os.getenv("RAG_TOP_DOCS", "5"))
    RAG_CONTEXT_LENGTH: int = int(os.getenv("RAG_CONTEXT_LENGTH", "500"))
    RAG_PREVIEW_LENGTH: int = int(os.getenv("RAG_PREVIEW_LENGTH", "200"))
    
    # Code detection thresholds
    MIN_TEXT_LENGTH_FOR_EXTRACTION: int = int(os.getenv("MIN_TEXT_LENGTH_FOR_EXTRACTION", "10"))
    MIN_CODE_LENGTH: int = int(os.getenv("MIN_CODE_LENGTH", "5"))
    MAX_WORDS_FOR_CODE: int = int(os.getenv("MAX_WORDS_FOR_CODE", "8"))
    MAX_WORDS_FOR_SENTENCE: int = int(os.getenv("MAX_WORDS_FOR_SENTENCE", "6"))
    
    # CORS origins - can be set via environment variable (comma-separated)
    _default_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://supportron-demo.loca.lt",
        "https://supportron-api.loca.lt",
    ]
    ALLOWED_ORIGINS: List[str] = (
        [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]
        if os.getenv("ALLOWED_ORIGINS")
        else _default_origins
    )
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Database configuration
    DB_DIRECTORY: str = os.getenv("DB_DIRECTORY", "databases")
    
    # Vector database path
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "data-processing/vector_db")
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration values."""
        if cls.RAG_MAX_DISTANCE < 0 or cls.RAG_MAX_DISTANCE > 1:
            raise ValueError("RAG_MAX_DISTANCE must be between 0 and 1")
        if cls.RAG_TOP_DOCS < 1:
            raise ValueError("RAG_TOP_DOCS must be at least 1")
        if cls.PORT < 1 or cls.PORT > 65535:
            raise ValueError("PORT must be between 1 and 65535")
        if not cls.MODEL:
            raise ValueError("MODEL must be specified")

