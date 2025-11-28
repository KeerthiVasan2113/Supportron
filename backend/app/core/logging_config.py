"""
Logging configuration for the application.

This module provides centralized logging for the entire backend application.
All modules should import the logger from this module to ensure consistent
logging configuration across the application.
"""

import logging
import sys
from pathlib import Path

from app.core.config import Config

# Import logging utility from data-processing
# Calculate data-processing path and ensure it's in sys.path
data_processing_str = None
data_processing_path = None

try:
    data_processing_path = Config.get_data_processing_path()
    data_processing_path = data_processing_path.resolve()
    data_processing_str = str(data_processing_path)
except (AttributeError, Exception):
    # Fallback: try relative path calculation if Config method fails
    config_file_path = Path(__file__).resolve()
    # Go from backend/app/core/logging_config.py to project root
    # backend/app/core/logging_config.py -> backend/app/core -> backend/app -> backend -> project_root
    project_root = config_file_path.parent.parent.parent.parent
    data_processing_path = (project_root / "data-processing").resolve()
    data_processing_str = str(data_processing_path)

# Verify the path exists and contains logger_utils.py
if not data_processing_path or not data_processing_path.exists():
    raise ImportError(f"Data processing path does not exist: {data_processing_path}")

if not (data_processing_path / "logger_utils.py").exists():
    raise ImportError(f"logger_utils.py not found in: {data_processing_path}")

# Ensure the path is in sys.path before importing
if data_processing_str and data_processing_str not in sys.path:
    sys.path.insert(0, data_processing_str)

# Now import logger_utils
from logger_utils import setup_logger

# Setup logging with proper configuration
# This logger is shared across all backend modules
try:
    log_file_path = Config.get_log_file()
except AttributeError:
    # Fallback: use default log path
    config_file_path = Path(__file__).resolve()
    project_root = config_file_path.parent.parent.parent.parent
    log_file_path = project_root / "logs" / "api.log"
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

logger = setup_logger(str(log_file_path), console_output=True)


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

