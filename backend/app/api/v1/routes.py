"""
API v1 routes.
"""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import get_rag_model
from app.api.v1.schemas import (
    ChatRequest, ChatResponse,
    UniversalDBRequest, UniversalDBResponse,
    TableInfoRequest, TableInfoResponse
)
from app.core.config import Config
from app.core.logging_config import logger
from app.services.chat_service import check_ollama_available, process_chat_request
from app.services.database_service import DatabaseService
from app.db.session import db_manager

router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.get("/", tags=["health"])
async def root() -> dict:
    """Root endpoint with service information."""
    return {
        "status": "online",
        "service": "Hybrid Chat API",
        "version": "1.0.0",
        "model": Config.MODEL,
        "rag_available": get_rag_model() is not None,
        "model_available": check_ollama_available()
    }


@router.get("/health", tags=["health"])
async def health() -> dict:
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "model": Config.MODEL,
        "rag_available": get_rag_model() is not None,
        "model_available": check_ollama_available()
    }


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Hybrid chat endpoint with conversation context support.
    
    Pipeline:
    - If RAG has relevant docs: Use RAG → llama3.2:3b
    - If no RAG docs: Use llama3.2:3b directly
    - Conversation history is included in prompts for context awareness
    
    Args:
        request: Chat request with question, options, and conversation history
    
    Returns:
        Chat response with answer and sources
        
    Raises:
        HTTPException: If service is unavailable or error occurs
    """
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


# Universal Database API Routes

@router.post("/db/universal", response_model=UniversalDBResponse, tags=["database"])
async def universal_db_operation(request: UniversalDBRequest) -> UniversalDBResponse:
    """
    Universal database operation endpoint.
    
    Performs CRUD operations dynamically based on HTTP method:
    - GET (method="GET"): Read records
    - POST (method="POST"): Create new record
    - PUT (method="PUT"): Update records
    - DELETE (method="DELETE"): Delete records
    
    Args:
        request: Universal database request with db_name, table_name, method, and operation data
    
    Returns:
        Universal database response with operation results
        
    Raises:
        HTTPException: If operation fails or validation error occurs
    """
    try:
        method = request.method.upper()
        
        if method == "GET":
            # Read operation
            records = DatabaseService.read(
                db_name=request.db_name,
                table_name=request.table_name,
                columns=request.columns,
                filters=request.filters,
                limit=request.limit,
                offset=request.offset
            )
            return UniversalDBResponse(
                success=True,
                message=f"Retrieved {len(records)} record(s)",
                data=records,
                db_name=request.db_name,
                table_name=request.table_name,
                method=method
            )
        
        elif method == "POST":
            # Create operation
            if not request.values:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Values are required for POST (CREATE) operations"
                )
            result = DatabaseService.create(
                db_name=request.db_name,
                table_name=request.table_name,
                values=request.values
            )
            return UniversalDBResponse(
                success=True,
                message="Record created successfully",
                data=result,
                db_name=request.db_name,
                table_name=request.table_name,
                method=method
            )
        
        elif method == "PUT":
            # Update operation
            if not request.values:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Values are required for PUT (UPDATE) operations"
                )
            if not request.filters:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Filters are required for PUT (UPDATE) operations"
                )
            result = DatabaseService.update(
                db_name=request.db_name,
                table_name=request.table_name,
                values=request.values,
                filters=request.filters
            )
            return UniversalDBResponse(
                success=True,
                message=f"Updated {result['affected_rows']} record(s)",
                data=result,
                db_name=request.db_name,
                table_name=request.table_name,
                method=method
            )
        
        elif method == "DELETE":
            # Delete operation
            if not request.filters:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Filters are required for DELETE operations"
                )
            result = DatabaseService.delete(
                db_name=request.db_name,
                table_name=request.table_name,
                filters=request.filters
            )
            return UniversalDBResponse(
                success=True,
                message=f"Deleted {result['affected_rows']} record(s)",
                data=result,
                db_name=request.db_name,
                table_name=request.table_name,
                method=method
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported method: {method}. Supported methods: GET, POST, PUT, DELETE"
            )
    
    except ValueError as e:
        logger.error(f"Validation error in universal DB operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in universal DB operation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database operation failed: {str(e)}"
        )


@router.post("/db/table-info", response_model=TableInfoResponse, tags=["database"])
async def get_table_info(request: TableInfoRequest) -> TableInfoResponse:
    """
    Get table information including schema and metadata.
    
    Args:
        request: Table info request with db_name and table_name
    
    Returns:
        Table information response with schema and metadata
        
    Raises:
        HTTPException: If table doesn't exist or error occurs
    """
    try:
        info = DatabaseService.get_table_info(
            db_name=request.db_name,
            table_name=request.table_name
        )
        return TableInfoResponse(
            success=True,
            data=info
        )
    except ValueError as e:
        logger.error(f"Error getting table info: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting table info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get table info: {str(e)}"
        )


@router.get("/db/databases", tags=["database"])
async def list_databases() -> dict:
    """
    List all available databases.
    
    Returns:
        Dictionary with list of database names
    """
    try:
        databases = db_manager.get_all_databases()
        return {
            "success": True,
            "databases": databases,
            "count": len(databases)
        }
    except Exception as e:
        logger.error(f"Error listing databases: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list databases: {str(e)}"
        )


@router.get("/db/{db_name}/tables", tags=["database"])
async def list_tables(db_name: str) -> dict:
    """
    List all tables in a database.
    
    Args:
        db_name: Name of the database
    
    Returns:
        Dictionary with list of table names
    """
    try:
        tables = db_manager.get_all_tables(db_name)
        return {
            "success": True,
            "db_name": db_name,
            "tables": tables,
            "count": len(tables)
        }
    except Exception as e:
        logger.error(f"Error listing tables: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tables: {str(e)}"
        )

