"""
Model preloading utility for Ollama.

Ensures models are loaded into memory on startup to avoid cold-start delays.
"""

import requests
import logging

logger = logging.getLogger(__name__)

OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
REQUEST_TIMEOUT = 600  # 10 minutes - cold load can be slow


def preload_model(model: str, api_url: str = OLLAMA_API_URL) -> bool:
    """
    Preload a model into Ollama's memory.
    
    Args:
        model: Model name (e.g., "qwen2.5:0.5b")
        api_url: Ollama API endpoint
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"⏳ Preloading model: {model}...")
        response = requests.post(
            api_url,
            json={"model": model, "prompt": " "},
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        logger.info(f"✓ Model loaded: {model}")
        return True
    except requests.exceptions.Timeout:
        logger.error(f"✗ Timeout preloading {model} (>{REQUEST_TIMEOUT}s)")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"✗ Connection error preloading {model}: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Error preloading {model}: {e}", exc_info=True)
        return False


def preload_all_models(models: list, api_url: str = OLLAMA_API_URL) -> bool:
    """
    Preload all models sequentially.
    
    Args:
        models: List of model names
        api_url: Ollama API endpoint
        
    Returns:
        True if all models loaded successfully, False otherwise
    """
    logger.info(f"🚀 Preloading {len(models)} models...")
    all_success = True
    
    for model in models:
        success = preload_model(model, api_url)
        if not success:
            all_success = False
    
    if all_success:
        logger.info("✓ All models preloaded successfully!")
    else:
        logger.warning("⚠ Some models failed to preload")
    
    return all_success
