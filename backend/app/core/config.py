"""
Application configuration constants.
"""

from typing import List


class Config:
    """Application configuration constants."""
    # Model names
    QWEN_MODEL: str = "qwen2.5:0.5b"
    PHI_MODEL: str = "phi:latest"
    
    # RAG configuration
    RAG_MAX_DISTANCE: float = 0.8
    RAG_TOP_DOCS: int = 5
    RAG_CONTEXT_LENGTH: int = 500
    RAG_PREVIEW_LENGTH: int = 200
    
    # Code detection thresholds
    MIN_TEXT_LENGTH_FOR_EXTRACTION: int = 10
    MIN_CODE_LENGTH: int = 5
    MAX_WORDS_FOR_CODE: int = 8
    MAX_WORDS_FOR_SENTENCE: int = 6
    
    # CORS origins
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://supportron-demo.loca.lt",
        "https://*.loca.lt",  # Allow all localtunnel HTTPS subdomains
        "http://*.loca.lt",   # Allow all localtunnel HTTP subdomains
    ]
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

