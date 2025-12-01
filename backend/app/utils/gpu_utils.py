"""
GPU detection and device management utilities.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def detect_gpu() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Detect GPU availability and return device information.
    
    Returns:
        Tuple of (has_gpu, device_name, device_type)
        - has_gpu: True if GPU is available
        - device_name: GPU name (e.g., "NVIDIA GeForce RTX 3060") or None
        - device_type: "cuda" or "cpu"
    """
    try:
        import torch
        
        # Check CUDA availability
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            if device_count > 0:
                device_name = torch.cuda.get_device_name(0)
                cuda_version = torch.version.cuda
                logger.info(f"✓ GPU detected: {device_name}")
                logger.info(f"  CUDA Version: {cuda_version}")
                logger.info(f"  Device Count: {device_count}")
                return True, device_name, "cuda"
        
        logger.info("No GPU detected, using CPU")
        return False, None, "cpu"
        
    except ImportError:
        logger.warning("PyTorch not installed, cannot detect GPU")
        return False, None, "cpu"
    except Exception as e:
        logger.warning(f"Error detecting GPU: {e}, falling back to CPU")
        return False, None, "cpu"


def get_device() -> str:
    """
    Get the appropriate device string for PyTorch operations.
    
    Returns:
        Device string: "cuda" or "cpu"
    """
    has_gpu, _, device_type = detect_gpu()
    return device_type or "cpu"


def get_device_for_model() -> str:
    """
    Get device string for model loading.
    
    Returns:
        Device string: "cuda" or "cpu"
    """
    return get_device()


def is_gpu_available() -> bool:
    """
    Check if GPU is available.
    
    Returns:
        True if GPU is available, False otherwise
    """
    has_gpu, _, _ = detect_gpu()
    return has_gpu

