"""
Main application entry point.
"""

import asyncio
import sys
from pathlib import Path

# Load environment variables from .env file BEFORE importing Config
from dotenv import load_dotenv

# Find .env file in backend directory
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Fallback: try to load from current directory
    load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import set_rag_model
from app.api.v1 import routes as v1_routes
from app.core.config import Config
from app.core.logging_config import logger
from app.services.ollama_service import ensure_ollama_ready
from app.utils.gpu_utils import detect_gpu

# RAG model imports
data_processing_path = Config.get_data_processing_path()
sys.path.insert(0, str(data_processing_path))
from build_rag_model import SimpleRAGModel

# Initialize FastAPI app
app = FastAPI(
    title=Config.APP_TITLE,
    version=Config.APP_VERSION,
    description=Config.APP_DESCRIPTION
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_origin_regex=Config.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["Content-Type"],
    max_age=3600,
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
    response = {
        "status": "online",
        "service": Config.APP_TITLE,
        "rag_available": get_rag_model() is not None,
        "model_available": check_ollama_available()
    }
    if not Config.HIDE_MODEL_INFO:
        response["model"] = Config.MODEL
    return response

@app.get("/health", tags=["health"])
async def health_legacy() -> dict:
    """Health check endpoint (legacy - delegates to v1)."""
    response = {
        "status": "healthy",
        "rag_available": get_rag_model() is not None,
        "model_available": check_ollama_available()
    }
    if not Config.HIDE_MODEL_INFO:
        response["model"] = Config.MODEL
    return response

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
    # Detect GPU first
    has_gpu, gpu_name, device_type = detect_gpu()
    if has_gpu:
        logger.info(f"✓ GPU acceleration available: {gpu_name}")
        logger.info(f"  Using device: {device_type.upper()}")
    else:
        logger.info("ℹ Using CPU (GPU not available)")
    
    # Start RAG initialization and Ollama check in parallel
    async def init_rag_model() -> None:
        """Initialize RAG model asynchronously."""
        try:
            vector_db_path = Config.get_vector_db_path()
            if not vector_db_path.exists():
                raise FileNotFoundError(f"Vector database path does not exist: {vector_db_path}")
            
            logger.info(f"Initializing RAG model from {vector_db_path}...")
            rag_model = SimpleRAGModel(
                str(vector_db_path),
                use_llm=False,  # We use Ollama models instead
                llm_model_name=Config.MODEL,  # Not used when use_llm=False, but kept for reference
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
    
    async def init_ollama_model() -> None:
        """Initialize Ollama model asynchronously in background."""
        logger.info("Checking Ollama model availability...")
        is_ready, selected_model = await ensure_ollama_ready(max_wait_time=60)
        
        if is_ready and selected_model:
            logger.info(f"✓ Ollama model ready: {selected_model}")
            # Config.MODEL is already updated by ensure_ollama_ready
        else:
            logger.warning("Ollama model not ready. Make sure Ollama is running and at least one model is pulled:")
            logger.warning("  ollama pull qwen2.5:7b-instruct")
            logger.warning("  or")
            logger.warning("  ollama pull llama3.2:3b")
            logger.warning("Server will continue, but chat may have limited functionality.")
    
    # Run both initializations concurrently
    await asyncio.gather(
        init_rag_model(),
        init_ollama_model()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=Config.HOST,
        port=Config.PORT,
        log_level="info",
        reload=False
    )

