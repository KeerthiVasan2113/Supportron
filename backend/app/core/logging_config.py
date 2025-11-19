"""
Logging configuration for the application.

This module provides centralized logging for the entire backend application.
All modules should import the logger from this module to ensure consistent
logging configuration across the application.
"""

import logging
import sys
from pathlib import Path

# Import logging utility from data-processing
project_root = Path(__file__).parent.parent.parent.parent
data_processing_path = project_root / "data-processing"
sys.path.insert(0, str(data_processing_path))
from logger_utils import setup_logger

# Setup logging with proper configuration
# This logger is shared across all backend modules
logger = setup_logger("logs/api.log", console_output=True)


def get_logger() -> logging.Logger:
    """
    Get the application logger.
    
    This function returns the centralized logger instance that is configured
    to log to both file and console. All backend modules should use this
    logger for consistent logging.
    
    Returns:
        Configured logger instance
        
    Example:
        ```python
        from app.core.logging_config import logger
        
        logger.info("Application started")
        logger.error("An error occurred")
        ```
    """
    return logger

