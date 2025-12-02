"""
Application configuration constants with environment variable support.
"""

import os
from pathlib import Path
from typing import List


class Config:
    """Application configuration with environment variable support."""
    
    # Model configuration - supports multiple models with fallback
    # Priority: qwen2.5:7b-instruct > llama3.2:3b
    # Can be overridden via OLLAMA_MODEL or MODEL env var
    _default_model = os.getenv("OLLAMA_MODEL", "") or os.getenv("MODEL", "")
    MODEL: str = _default_model if _default_model else "qwen2.5:7b-instruct"
    
    # Preferred models in order of preference
    PREFERRED_MODELS: List[str] = [
        "qwen2.5:7b-instruct",
        "llama3.2:3b"
    ]
    
    # GPU configuration
    USE_GPU: bool = os.getenv("USE_GPU", "true").lower() == "true"
    GPU_DEVICE: str = os.getenv("GPU_DEVICE", "cuda")  # "cuda" or "cpu"
    
    # RAG configuration
    RAG_MAX_DISTANCE: float = float(os.getenv("RAG_MAX_DISTANCE", "0.8"))
    RAG_TOP_DOCS: int = int(os.getenv("RAG_TOP_DOCS", "3"))  # Reduced for faster responses
    RAG_CONTEXT_LENGTH: int = int(os.getenv("RAG_CONTEXT_LENGTH", "400"))  # Reduced for faster processing
    RAG_PREVIEW_LENGTH: int = int(os.getenv("RAG_PREVIEW_LENGTH", "200"))
    
    # Ollama generation options for well-structured responses
    OLLAMA_NUM_PREDICT: int = int(os.getenv("OLLAMA_NUM_PREDICT", "4096"))  # Allow longer, detailed responses (increased for complete answers)
    OLLAMA_TEMPERATURE: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.6"))  # Balanced for clarity and creativity
    OLLAMA_TOP_P: float = float(os.getenv("OLLAMA_TOP_P", "0.9"))  # Nucleus sampling
    OLLAMA_TOP_K: int = int(os.getenv("OLLAMA_TOP_K", "40"))  # Top-k sampling
    
    # Code detection thresholds
    MIN_TEXT_LENGTH_FOR_EXTRACTION: int = int(os.getenv("MIN_TEXT_LENGTH_FOR_EXTRACTION", "10"))
    MIN_CODE_LENGTH: int = int(os.getenv("MIN_CODE_LENGTH", "5"))
    MAX_WORDS_FOR_CODE: int = int(os.getenv("MAX_WORDS_FOR_CODE", "8"))
    MAX_WORDS_FOR_SENTENCE: int = int(os.getenv("MAX_WORDS_FOR_SENTENCE", "6"))
    
    # CORS origins - can be set via environment variable (comma-separated)
    ALLOWED_ORIGINS: List[str] = (
        [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]
        if os.getenv("ALLOWED_ORIGINS")
        else [os.getenv("FRONTEND_URL", "http://localhost:3000")]
    )
    
    # CORS origin regex pattern for dynamic subdomains
    CORS_ORIGIN_REGEX: str = os.getenv("CORS_ORIGIN_REGEX", r"https?://.*\.loca\.lt")
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # API configuration
    _default_api_url = f"http://{os.getenv('HOST', '0.0.0.0')}:{int(os.getenv('PORT', '8000'))}"
    API_BASE_URL: str = os.getenv("API_BASE_URL", _default_api_url)
    API_VERSION: str = os.getenv("API_VERSION", "v1")
    API_PREFIX: str = os.getenv("API_PREFIX", "/api")
    
    # Application metadata
    APP_TITLE: str = os.getenv("APP_TITLE", "Hybrid Chat API")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    APP_DESCRIPTION: str = os.getenv("APP_DESCRIPTION", "Hybrid chat system using RAG and LLM")
    
    # Project paths configuration
    PROJECT_ROOT: str = os.getenv("PROJECT_ROOT", "")  # If empty, will be calculated from __file__
    DATA_PROCESSING_PATH: str = os.getenv("DATA_PROCESSING_PATH", "")  # If empty, will be calculated relative to project root
    LOGS_DIRECTORY: str = os.getenv("LOGS_DIRECTORY", "logs")
    
    # Database configuration
    DB_DIRECTORY: str = os.getenv("DB_DIRECTORY", "databases")
    
    # Vector database path
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "")  # If empty, will be calculated relative to data-processing path
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "")  # If empty, will be calculated as {LOGS_DIRECTORY}/api.log
    
    # Security - hide model info in responses
    HIDE_MODEL_INFO: bool = os.getenv("HIDE_MODEL_INFO", "true").lower() == "true"
    
    # Embedding model configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "")  # Auto-detect if empty
    
    @classmethod
    def get_project_root(cls) -> Path:
        """
        Get the project root directory.
        Uses PROJECT_ROOT env var if set, otherwise calculates from backend location.
        """
        if cls.PROJECT_ROOT:
            return Path(cls.PROJECT_ROOT).resolve()
        # Default: assume backend/app/core/config.py structure, go up 4 levels to project root
        # Path: backend/app/core/config.py -> backend/app/core -> backend/app -> backend -> project_root
        config_file_path = Path(__file__).resolve()
        project_root = config_file_path.parent.parent.parent.parent
        return project_root.resolve()
    
    @classmethod
    def get_data_processing_path(cls) -> Path:
        """
        Get the data-processing directory path.
        Uses DATA_PROCESSING_PATH env var if set, otherwise calculates relative to project root.
        """
        if cls.DATA_PROCESSING_PATH:
            return Path(cls.DATA_PROCESSING_PATH).resolve()
        # Default: project_root / "data-processing"
        return cls.get_project_root() / "data-processing"
    
    @classmethod
    def get_vector_db_path(cls) -> Path:
        """
        Get the vector database path.
        Uses VECTOR_DB_PATH env var if set, otherwise calculates relative to data-processing path.
        """
        if cls.VECTOR_DB_PATH:
            return Path(cls.VECTOR_DB_PATH).resolve()
        # Default: data_processing_path / "vector_db"
        return cls.get_data_processing_path() / "vector_db"
    
    @classmethod
    def get_logs_directory(cls) -> Path:
        """
        Get the logs directory path.
        Uses LOGS_DIRECTORY env var if set, otherwise uses default "logs" relative to project root.
        """
        if cls.LOGS_DIRECTORY:
            logs_path = Path(cls.LOGS_DIRECTORY)
            if logs_path.is_absolute():
                return logs_path.resolve()
            # Relative path: resolve relative to project root
            return (cls.get_project_root() / logs_path).resolve()
        # Default: project_root / "logs"
        return (cls.get_project_root() / "logs").resolve()
    
    @classmethod
    def get_log_file(cls) -> Path:
        """
        Get the log file path.
        Uses LOG_FILE env var if set, otherwise calculates as {LOGS_DIRECTORY}/api.log.
        """
        if cls.LOG_FILE:
            log_file_path = Path(cls.LOG_FILE)
            if log_file_path.is_absolute():
                return log_file_path.resolve()
            # Relative path: resolve relative to project root
            return (cls.get_project_root() / log_file_path).resolve()
        return cls.get_logs_directory() / "api.log"
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration values."""
        from app.core.error_messages import (
            OLLAMA_MODEL_NOT_SET,
            INVALID_RAG_MAX_DISTANCE,
            INVALID_RAG_TOP_DOCS,
            INVALID_PORT
        )
        if not cls.MODEL:
            raise ValueError(OLLAMA_MODEL_NOT_SET)
        if cls.RAG_MAX_DISTANCE < 0 or cls.RAG_MAX_DISTANCE > 1:
            raise ValueError(INVALID_RAG_MAX_DISTANCE)
        if cls.RAG_TOP_DOCS < 1:
            raise ValueError(INVALID_RAG_TOP_DOCS)
        if cls.PORT < 1 or cls.PORT > 65535:
            raise ValueError(INVALID_PORT)

