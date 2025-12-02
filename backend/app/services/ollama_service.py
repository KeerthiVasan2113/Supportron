"""
Ollama service management for async startup and health checks.
"""

import asyncio
import platform
import subprocess
import time
from typing import Optional, List

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
    except ConnectionError as e:
        logger.debug(f"Ollama connection error: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking Ollama status: {e}")
        return False


def check_model_available(model_name: Optional[str] = None) -> bool:
    """
    Check if a specific model is available and ready.
    
    Args:
        model_name: Name of the model to check (defaults to Config.MODEL)
    
    Returns:
        True if model is ready, False otherwise
    """
    model = model_name or Config.MODEL
    try:
        # Quick test generation to verify model is loaded
        ollama.generate(model=model, prompt="test", options={"num_predict": 1})
        return True
    except ConnectionError as e:
        logger.debug(f"Connection error checking model '{model}': {e}")
        return False
    except ValueError as e:
        logger.warning(f"Model '{model}' not found or invalid: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking model '{model}': {e}")
        return False


def get_available_models() -> List[str]:
    """
    Get list of available Ollama models.
    
    Returns:
        List of available model names
    """
    try:
        models = ollama.list()
        return [model['name'] for model in models.get('models', [])]
    except Exception as e:
        logger.debug(f"Error getting available models: {e}")
        return []


def select_best_available_model() -> Optional[str]:
    """
    Select the best available model from preferred models.
    Checks availability in order of preference.
    
    Returns:
        Name of the best available model, or None if none are available
    """
    if not check_ollama_running():
        logger.warning("Ollama is not running, cannot check model availability")
        return None
    
    available_models = get_available_models()
    logger.info(f"Available Ollama models: {available_models}")
    
    # Check preferred models in order - optimize by checking exact match first
    for preferred_model in Config.PREFERRED_MODELS:
        # First try exact match (faster)
        if preferred_model in available_models:
            if check_model_available(preferred_model):
                logger.info(f"✓ Selected model: {preferred_model}")
                return preferred_model
        
        # Then check for partial matches (name with different tags)
        preferred_base = preferred_model.split(':')[0]
        for available_model in available_models:
            if available_model.startswith(preferred_base):
                if check_model_available(available_model):
                    logger.info(f"✓ Selected model: {available_model}")
                    return available_model
    
    # If no preferred model is available, try the configured model
    if Config.MODEL and check_model_available(Config.MODEL):
        logger.info(f"✓ Using configured model: {Config.MODEL}")
        return Config.MODEL
    
    # If still no model, try any available model
    for model in available_models:
        if check_model_available(model):
            logger.warning(f"Using fallback model: {model}")
            return model
    
    logger.error("No available models found!")
    return None


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


async def ensure_ollama_ready(max_wait_time: int = 60) -> tuple:
    """
    Ensure Ollama service is running and select the best available model.
    Starts Ollama in background if not running.
    
    Args:
        max_wait_time: Maximum time to wait for Ollama to become ready (seconds)
        
    Returns:
        Tuple of (is_ready, selected_model_name)
    """
    # Check if already running
    if check_ollama_running():
        selected_model = select_best_available_model()
        if selected_model and check_model_available(selected_model):
            logger.info(f"✓ Ollama service is already running with model: {selected_model}")
            # Update Config.MODEL to the selected model
            Config.MODEL = selected_model
            return True, selected_model
    
    # Try to start Ollama if not running
    if not check_ollama_running():
        logger.info("Ollama service not detected. Attempting to start in background...")
        process = start_ollama_service()
        
        if process is None:
            logger.warning("Could not start Ollama service automatically. Please start it manually.")
            return False, None
        
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
            return False, None
    
    # Select and wait for model to be available
    logger.info("Selecting best available model...")
    selected_model = select_best_available_model()
    
    if not selected_model:
        logger.warning("No suitable model found. Please ensure at least one model is pulled:")
        logger.warning("  ollama pull qwen2.5:7b-instruct")
        logger.warning("  or")
        logger.warning("  ollama pull llama3.2:3b")
        return False, None
    
    # Update Config.MODEL to the selected model
    Config.MODEL = selected_model
    
    # Wait for model to be ready
    logger.info(f"Waiting for model '{selected_model}' to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        await asyncio.sleep(1)  # Check every second
        
        if check_model_available(selected_model):
            logger.info(f"✓ Model '{selected_model}' is ready!")
            return True, selected_model
    
    logger.warning(f"Model '{selected_model}' did not become ready within {max_wait_time} seconds")
    return False, selected_model

