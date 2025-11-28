"""
Ollama service management for async startup and health checks.
"""

import asyncio
import platform
import subprocess
import time
from typing import Optional

import ollama
from app.core.config import Config
from app.core.logging_config import logger


def check_ollama_running() -> bool:
    """
    Check if Ollama service is currently running.
    
    Returns:
        True if Ollama is running and accessible, False otherwise
    """
    try:
        ollama.list()
        return True
    except Exception:
        return False


def check_model_available() -> bool:
    """
    Check if the configured model is available and ready.
    
    Returns:
        True if model is ready, False otherwise
    """
    try:
        # Quick test generation to verify model is loaded
        ollama.generate(model=Config.MODEL, prompt="test", options={"num_predict": 1})
        return True
    except Exception:
        return False


def start_ollama_service() -> Optional[subprocess.Popen]:
    """
    Start Ollama service as a background process.
    
    Returns:
        Process object if started successfully, None otherwise
    """
    try:
        system = platform.system().lower()
        
        if system == "windows":
            # On Windows, try to start Ollama service
            try:
                # Try to start Ollama via service or executable
                process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                )
                return process
            except FileNotFoundError:
                logger.warning("Ollama executable not found in PATH. Please ensure Ollama is installed.")
                return None
        else:
            # On Linux/macOS, try to start Ollama service
            try:
                process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )
                return process
            except FileNotFoundError:
                logger.warning("Ollama executable not found in PATH. Please ensure Ollama is installed.")
                return None
    except Exception as e:
        logger.error(f"Failed to start Ollama service: {e}")
        return None


async def ensure_ollama_ready(max_wait_time: int = 60) -> bool:
    """
    Ensure Ollama service is running and model is ready.
    Starts Ollama in background if not running.
    
    Args:
        max_wait_time: Maximum time to wait for Ollama to become ready (seconds)
        
    Returns:
        True if Ollama is ready, False otherwise
    """
    # Check if already running
    if check_ollama_running() and check_model_available():
        logger.info("✓ Ollama service is already running and model is ready!")
        return True
    
    # Try to start Ollama if not running
    if not check_ollama_running():
        logger.info("Ollama service not detected. Attempting to start in background...")
        process = start_ollama_service()
        
        if process is None:
            logger.warning("Could not start Ollama service automatically. Please start it manually.")
            return False
        
        # Wait for Ollama to start
        logger.info("Waiting for Ollama service to start...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            await asyncio.sleep(2)  # Check every 2 seconds
            
            if check_ollama_running():
                logger.info("✓ Ollama service started successfully!")
                break
        else:
            logger.error(f"Ollama service did not start within {max_wait_time} seconds")
            return False
    
    # Wait for model to be available
    logger.info(f"Waiting for model '{Config.MODEL}' to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        await asyncio.sleep(1)  # Check every second
        
        if check_model_available():
            logger.info("The model has initiated!!!")
            return True
    
    logger.warning(f"Model '{Config.MODEL}' did not become ready within {max_wait_time} seconds")
    return False

