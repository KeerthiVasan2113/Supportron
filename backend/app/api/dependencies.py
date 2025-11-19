"""
Shared dependencies for API endpoints.
"""

import sys
from pathlib import Path
from typing import Optional

from app.core.logging_config import logger

# RAG model imports
project_root = Path(__file__).parent.parent.parent.parent
data_processing_path = project_root / "data-processing"
sys.path.insert(0, str(data_processing_path))
from build_rag_model import SimpleRAGModel

# Global state for RAG model
rag_model: Optional[SimpleRAGModel] = None


def get_rag_model() -> Optional[SimpleRAGModel]:
    """
    Get the global RAG model instance.
    
    Returns:
        RAG model instance or None if not initialized
    """
    return rag_model


def set_rag_model(model: Optional[SimpleRAGModel]) -> None:
    """
    Set the global RAG model instance.
    
    Args:
        model: RAG model instance to set
    """
    global rag_model
    rag_model = model
    if model is not None:
        logger.info("RAG model set successfully")
    else:
        logger.info("RAG model cleared")

