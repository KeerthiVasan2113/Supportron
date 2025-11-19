"""
Centralized logging utility for the project.
All modules should use this utility for consistent logging configuration.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Path is used in setup_logger function


def setup_logger(
    log_file: str,
    log_level: int = logging.INFO,
    console_output: bool = False,
    logger_name: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure a logger with file and optional console output.
    
    This function creates a centralized logging configuration that:
    - Creates log directories if they don't exist
    - Configures file logging with UTF-8 encoding
    - Optionally adds console output
    - Uses consistent formatting across all loggers
    
    Args:
        log_file: Path to the log file (e.g., "logs/app.log" or "logs/subdir/app.log")
        log_level: Logging level (default: logging.INFO)
        console_output: Whether to also output logs to console (default: False)
        logger_name: Name for the logger (default: None, uses calling module name)
    
    Returns:
        Configured Logger instance
    
    Example:
        ```python
        from logger_utils import setup_logger
        
        # Basic usage - file only
        logger = setup_logger("logs/my_app.log")
        
        # With console output
        logger = setup_logger("logs/my_app.log", console_output=True)
        
        # With custom log level
        logger = setup_logger("logs/debug.log", log_level=logging.DEBUG)
        
        # Use the logger
        logger.info("Application started")
        logger.error("An error occurred")
        ```
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get logger name (use calling module if not specified)
    if logger_name is None:
        import inspect
        frame = inspect.currentframe()
        try:
            # Get the frame that called this function
            caller_frame = frame.f_back
            logger_name = caller_frame.f_globals.get('__name__', 'root')
        finally:
            del frame
    
    # Create logger
    logger = logging.getLogger(logger_name)
    
    # Avoid adding handlers multiple times if logger already configured
    if logger.handlers:
        return logger
    
    # Set log level
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(log_file: str, **kwargs) -> logging.Logger:
    """
    Convenience function to get a logger with default settings.
    
    This is an alias for setup_logger with sensible defaults.
    Use this for quick logger setup.
    
    Args:
        log_file: Path to the log file
        **kwargs: Additional arguments passed to setup_logger
    
    Returns:
        Configured Logger instance
    
    Example:
        ```python
        from logger_utils import get_logger
        
        logger = get_logger("logs/app.log")
        logger.info("Hello, world!")
        ```
    """
    return setup_logger(log_file, **kwargs)

