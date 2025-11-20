"""
Pydantic schemas for API v1.
"""

from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

from app.core.security import create_question_validator


class MessageHistory(BaseModel):
    """Message in conversation history."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str = Field(..., min_length=1, max_length=5000, description="User's question")
    show_sources: bool = Field(default=True, description="Whether to include source documents")
    include_history: bool = Field(default=False, description="Whether to include conversation history in the model prompt")
    conversation_history: Optional[List[MessageHistory]] = Field(
        default=None, 
        description="Previous messages in the conversation for context"
    )
    
    # Add validator
    _validate_question = create_question_validator()


class SourceDocument(BaseModel):
    """Source document model."""
    source_file: str = Field(..., description="Source file name")
    preview: str = Field(..., description="Preview of the document content")
    distance: Optional[float] = Field(None, description="Similarity distance (lower is better)")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str = Field(..., description="Generated answer")
    question: str = Field(..., description="Original question")
    sources: Optional[List[SourceDocument]] = Field(None, description="Source documents if available")


# Universal Database API Schemas

class UniversalDBRequest(BaseModel):
    """Request model for universal database operations."""
    db_name: str = Field(..., min_length=1, description="Name of the database")
    table_name: str = Field(..., min_length=1, description="Name of the table")
    method: str = Field(..., description="HTTP method: GET, POST, PUT, DELETE")
    
    # For POST (CREATE) and PUT (UPDATE)
    values: Optional[Dict[str, Any]] = Field(None, description="Column values for create/update")
    
    # For GET (READ), PUT (UPDATE), and DELETE
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter conditions (WHERE clause)")
    
    # For GET (READ) only
    columns: Optional[List[str]] = Field(None, description="Specific columns to retrieve (all if not specified)")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Maximum number of records to return")
    offset: Optional[int] = Field(None, ge=0, description="Number of records to skip")


class UniversalDBResponse(BaseModel):
    """Response model for universal database operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Operation result message")
    data: Optional[Any] = Field(None, description="Response data (records, rowid, affected_rows, etc.)")
    db_name: str = Field(..., description="Database name")
    table_name: str = Field(..., description="Table name")
    method: str = Field(..., description="HTTP method used")


class TableInfoRequest(BaseModel):
    """Request model for getting table information."""
    db_name: str = Field(..., min_length=1, description="Name of the database")
    table_name: str = Field(..., min_length=1, description="Name of the table")


class TableInfoResponse(BaseModel):
    """Response model for table information."""
    success: bool = Field(..., description="Whether the operation was successful")
    data: Dict[str, Any] = Field(..., description="Table schema and metadata")
