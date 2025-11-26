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
# Use allow_origin_regex to support localtunnel subdomains
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_origin_regex=r"https?://.*\.loca\.lt",  # Allow all localtunnel subdomains
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Explicitly allow only needed methods
    allow_headers=["Content-Type", "Authorization", "Accept"],  # Explicit headers only
    expose_headers=["Content-Type"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Include routers
app.include_router(v1_routes.router)

# Legacy routes for backward compatibility - delegate to v1 router
from app.api.dependencies import get_rag_model
from app.api.v1.schemas import ChatRequest, ChatResponse
from app.services.chat_service import check_ollama_available, process_chat_request

@app.get("/", tags=["health"])
async def root_legacy() -> dict:
    """Root endpoint (legacy - delegates to v1)."""
    return {
        "status": "online",
        "service": "Hybrid Chat API",
        "model": Config.MODEL,
        "rag_available": get_rag_model() is not None,
        "model_available": check_ollama_available()
    }

@app.get("/health", tags=["health"])
async def health_legacy() -> dict:
    """Health check endpoint (legacy - delegates to v1)."""
    return {
        "status": "healthy",
        "model": Config.MODEL,
        "rag_available": get_rag_model() is not None,
        "model_available": check_ollama_available()
    }

@app.post("/api/chat", response_model=ChatResponse, tags=["chat"])
async def chat_legacy(request: ChatRequest) -> ChatResponse:
    """Chat endpoint (legacy - delegates to v1)."""
    history = [
        {"role": msg.role, "content": msg.content} 
        for msg in request.conversation_history
    ] if request.conversation_history else None
    
    answer, sources = process_chat_request(request.question, history)
    
    return ChatResponse(
        answer=answer,
        question=request.question,
        sources=sources
    )


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize Ollama models and RAG on startup."""
    # Verify Ollama model is available
    try:
        logger.info("Checking Ollama model availability...")
        # Test model
        ollama.generate(model=Config.MODEL, prompt="test")
        logger.info(f"✓ Model '{Config.MODEL}' is ready!")
    except Exception as e:
        logger.error(f"Failed to connect to Ollama or model not found: {e}", exc_info=True)
        logger.warning("Make sure Ollama is running and model is pulled:")
        logger.warning(f"  ollama pull {Config.MODEL}")
        # Don't raise - allow server to start, but chat will fail gracefully
    
    # Initialize RAG model
    try:
        vector_db_path = project_root / "data-processing" / "vector_db"
        if not vector_db_path.exists():
            raise FileNotFoundError(f"Vector database path does not exist: {vector_db_path}")
        
        logger.info(f"Initializing RAG model from {vector_db_path}...")
        rag_model = SimpleRAGModel(
            str(vector_db_path),
            use_llm=False,  # We use Ollama models instead
            llm_model_name="Qwen/Qwen2.5-0.5B-Instruct",  # Not used when use_llm=False
            use_quantization=False
        )
        set_rag_model(rag_model)
        logger.info("✓ RAG model initialized successfully!")
    except FileNotFoundError as e:
        logger.error(f"Vector database not found: {e}")
        logger.warning("RAG will not be available. Chat will use model directly.")
        set_rag_model(None)
    except Exception as e:
        logger.error(f"Failed to initialize RAG model: {e}", exc_info=True)
        logger.warning("RAG will not be available. Chat will use model directly.")
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

