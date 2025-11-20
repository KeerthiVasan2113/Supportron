"""
Ollama service manager for automatic startup and health checks.

This module handles:
- Checking if Ollama is running and accessible
- Automatically starting Ollama if configured
- Waiting for Ollama to become available
- Logging all operations
"""

import os
import shlex
import socket
import subprocess
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_HOST = os.getenv("OLLAMA_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
START_CMD = os.getenv("OLLAMA_START_CMD")
CHECK_INTERVAL = float(os.getenv("OLLAMA_CHECK_INTERVAL", "0.5"))
START_TIMEOUT = float(os.getenv("OLLAMA_START_TIMEOUT", "30.0"))


def _is_port_open(host: str, port: int) -> bool:
    """Check if a port is open and accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except Exception:
        return False


def _spawn_detached_process(cmd: str, log_path: Optional[str] = None) -> subprocess.Popen:
    """
    Spawn a detached process (runs independently from parent).
    
    Args:
        cmd: Shell command to execute
        log_path: Optional path to log output
        
    Returns:
        The Popen process object
    """
    parts = shlex.split(cmd)
    stdout = stderr = subprocess.DEVNULL
    
    if log_path:
        try:
            f = open(log_path, "a", encoding="utf-8")
            stdout = f
            stderr = f
        except Exception as e:
            logger.warning(f"Could not open log file {log_path}: {e}")
    
    # Platform-specific detachment
    kwargs = {}
    if os.name == "nt":
        # Windows: use process group flags
        kwargs["creationflags"] = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200) |
            getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        )
    else:
        # POSIX: use start_new_session
        kwargs["start_new_session"] = True
    
    proc = subprocess.Popen(
        parts,
        stdout=stdout,
        stderr=stderr,
        stdin=subprocess.DEVNULL,
        shell=False,
        **kwargs
    )
    logger.info(f"Spawned Ollama process (pid={proc.pid}) with cmd: {cmd}")
    return proc


def start_ollama_if_needed(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    start_cmd: Optional[str] = START_CMD
) -> bool:
    """
    Ensure Ollama is reachable; if not and start_cmd is provided, attempt to start it.
    
    Args:
        host: Ollama server host (default from OLLAMA_HOST env var or 127.0.0.1)
        port: Ollama server port (default from OLLAMA_PORT env var or 11434)
        start_cmd: Command to start Ollama (default from OLLAMA_START_CMD env var)
        
    Returns:
        True if Ollama is reachable after this call, False otherwise
    """
    # Check if already reachable
    if _is_port_open(host, port):
        logger.info(f"✓ Ollama already reachable at {host}:{port}")
        return True

    if not start_cmd:
        logger.warning(
            f"⚠ Ollama not reachable at {host}:{port} and OLLAMA_START_CMD not set. "
            "Set OLLAMA_START_CMD environment variable to auto-start Ollama."
        )
        return False

    # Prepare log directory and file
    log_dir = os.path.join(os.getcwd(), "logs")
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception as e:
        logger.warning(f"Could not create logs directory: {e}")
        log_dir = None

    log_path = os.path.join(log_dir, "ollama-start.log") if log_dir else None

    # Attempt to start Ollama
    try:
        _spawn_detached_process(start_cmd, log_path=log_path)
    except Exception as exc:
        logger.error(f"✗ Failed to spawn Ollama: {exc}", exc_info=True)
        return False

    # Wait for port to become available
    logger.info(f"⏳ Waiting for Ollama to start (timeout {START_TIMEOUT}s)...")
    deadline = time.time() + START_TIMEOUT
    
    while time.time() < deadline:
        if _is_port_open(host, port):
            logger.info(f"✓ Ollama is now reachable at {host}:{port}")
            return True
        time.sleep(CHECK_INTERVAL)

    elapsed = time.time() - (deadline - START_TIMEOUT)
    logger.error(
        f"✗ Ollama startup timed out after {elapsed:.1f}s. "
        f"Check if the command is correct: '{start_cmd}' "
        f"and see logs at: {log_path}"
    )
    return False
