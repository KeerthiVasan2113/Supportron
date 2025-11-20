"""
Main application entry point.
"""

import sys
from pathlib import Path

import ollama
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import set_rag_model
from app.api.v1 import routes as v1_routes
from app.core.config import Config
from app.core.logging_config import logger
from app.core.ollama_manager import start_ollama_if_needed
from app.core.preload_models import preload_all_models

# RAG model imports
project_root = Path(__file__).parent.parent.parent
data_processing_path = project_root / "data-processing"
sys.path.insert(0, str(data_processing_path))
from build_rag_model import SimpleRAGModel

# Initialize FastAPI app
app = FastAPI(
    title="Hybrid Chat API",
    version="1.0.0",
    description="Hybrid chat system using Qwen2.5B, Phi-2, and RAG"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers
app.include_router(v1_routes.router)

# Also include legacy routes for backward compatibility
from app.api.dependencies import get_rag_model
from app.api.v1.schemas import ChatRequest, ChatResponse
from app.services.chat_service import check_ollama_available

@app.get("/", tags=["health"])
async def root_legacy() -> dict:
    """Root endpoint (legacy)."""
    return {
        "status": "online",
        "service": "Hybrid Chat API",
        "models": {
            "qwen": Config.QWEN_MODEL,
            "phi": Config.PHI_MODEL
        },
        "rag_available": get_rag_model() is not None,
        "model_available": check_ollama_available()
    }


@app.get("/health", tags=["health"])
async def health_legacy() -> dict:
    """Health check endpoint (legacy)."""
    return {
        "status": "healthy",
        "models": {
            "qwen": Config.QWEN_MODEL,
            "phi": Config.PHI_MODEL
        },
        "rag_available": get_rag_model() is not None,
        "model_available": check_ollama_available()
    }


@app.post("/api/chat", tags=["chat"])
async def chat_legacy(request: ChatRequest) -> ChatResponse:
    """Chat endpoint (legacy - redirects to v1)."""
    from app.services.chat_service import process_chat_request
    
    # Convert Pydantic models to dicts for service layer
    history = None
    if request.conversation_history:
        history = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]
    
    answer, sources = process_chat_request(request.question, history)
    
    return ChatResponse(
        answer=answer,
        question=request.question,
        sources=sources
    )


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize Ollama and RAG on startup."""
    import asyncio
    
    # Attempt to start Ollama if it's not running
    try:
        logger.info("🚀 Starting Ollama service...")
        loop = asyncio.get_event_loop()
        ollama_started = await loop.run_in_executor(None, start_ollama_if_needed)
        if ollama_started:
            logger.info("✓ Ollama is running and ready!")
            
            # Preload models into memory to avoid cold-start delays
            logger.info("📦 Preloading models into memory...")
            models_to_load = [Config.PHI_MODEL, Config.QWEN_MODEL]
            await loop.run_in_executor(None, preload_all_models, models_to_load)
        else:
            logger.warning("⚠ Ollama not available. Chat may have limited functionality.")
    except Exception as e:
        logger.error(f"Error during Ollama startup: {e}", exc_info=True)
    
    # Initialize RAG model
    try:
        vector_db_path = project_root / "data-processing" / "vector_db"
        if not vector_db_path.exists():
            raise FileNotFoundError(f"Vector database path does not exist: {vector_db_path}")
        
        logger.info(f"Initializing RAG model from {vector_db_path}...")
        rag_model = SimpleRAGModel(
            str(vector_db_path),
            use_llm=False,  # We'll use Ollama models instead
            llm_model_name="Qwen/Qwen2.5-0.5B-Instruct",
            use_quantization=False
        )
        set_rag_model(rag_model)
        logger.info("✓ RAG model initialized successfully!")
    except FileNotFoundError as e:
        logger.error(f"Vector database not found: {e}")
        logger.warning("RAG will not be available. Chat will use Qwen2.5B directly.")
        set_rag_model(None)
    except Exception as e:
        logger.error(f"Failed to initialize RAG model: {e}", exc_info=True)
        logger.warning("RAG will not be available. Chat will use Qwen2.5B directly.")
        set_rag_model(None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=Config.HOST,
        port=Config.PORT,
        log_level="info",
        reload=False
    )

