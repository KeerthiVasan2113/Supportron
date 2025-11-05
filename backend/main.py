"""
Supportron Backend API
FastAPI backend for IT tech support chatbot using Google Gemini AI
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Literal
import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env from backend directory or parent directory
env_path = Path(__file__).parent / '.env'
if not env_path.exists():
    env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize FastAPI app
app = FastAPI(
    title="Supportron API",
    version="1.0.0",
    description="IT Tech Support AI Assistant API"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

# System prompt to ensure only IT tech support questions are answered
SYSTEM_PROMPT = """You are Supportron, an advanced AI assistant specialized in IT technical support. 
Your primary role is to assist users with:
- Hardware troubleshooting (computers, printers, networks, etc.)
- Software issues (operating systems, applications, drivers)
- Network connectivity problems
- Security concerns (malware, firewalls, encryption)
- System configuration and optimization
- IT infrastructure questions
- Cloud services and deployment
- Database issues
- Development tools and environments

IMPORTANT: If a user asks about non-IT topics (such as cooking, travel, medical advice, legal advice, personal relationships, etc.), politely redirect them by saying:
"I'm Supportron, your IT tech support assistant. I specialize in helping with technical IT issues. Could you please rephrase your question related to IT support, or let me know what technical problem you're experiencing?"

Be professional, clear, and helpful. Provide step-by-step solutions when possible."""

# Pydantic models
class Message(BaseModel):
    role: Literal["user", "assistant"] = Field(..., description="Message role")
    content: str = Field(..., min_length=1, description="Message content")

class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., min_items=1, description="List of messages")

class ChatResponse(BaseModel):
    message: str = Field(..., description="AI response message")
    is_it_related: bool = Field(default=True, description="Whether the response is IT-related")

# Helper functions
def build_conversation_history(messages: List[Message]) -> List[dict]:
    """Build conversation history for Gemini API"""
    history = [
        {
            "role": "user",
            "parts": [SYSTEM_PROMPT]
        },
        {
            "role": "model",
            "parts": ["Understood. I'm Supportron, ready to assist with IT technical support issues."]
        }
    ]
    
    for msg in messages:
        if msg.role == "user":
            history.append({
                "role": "user",
                "parts": [msg.content]
            })
        elif msg.role == "assistant":
            history.append({
                "role": "model",
                "parts": [msg.content]
            })
    
    return history

def check_it_related(response_text: str) -> bool:
    """Check if response indicates non-IT question"""
    redirect_phrases = [
        "i specialize in helping with technical it issues",
        "could you please rephrase your question related to it support"
    ]
    return not any(phrase in response_text.lower() for phrase in redirect_phrases)

# API endpoints
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API information"""
    return {
        "message": "Supportron API is running",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Chat endpoint - Send messages and get AI responses
    
    Args:
        request: ChatRequest containing list of messages
        
    Returns:
        ChatResponse with AI message and IT-related flag
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        if not request.messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Messages list cannot be empty"
            )
        
        # Build conversation history
        conversation_history = build_conversation_history(request.messages)
        
        # Initialize model - use gemini-2.5-flash
        # Falls back to gemini-1.5-pro if unavailable
        model_name = "gemini-2.5-flash"
        
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
        except Exception as model_error:
            # Try fallback model
            logger.warning(f"Model {model_name} failed, trying gemini-1.5-pro: {str(model_error)}")
            model_name = "gemini-1.5-pro"
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
        
        logger.info(f"Using Gemini model: {model_name}")
        
        # Generate response
        last_message = request.messages[-1].content
        chat_session = model.start_chat(history=conversation_history)
        response = chat_session.send_message(last_message)
        
        # Extract response text
        response_text = response.text
        
        # Check if response is IT-related
        is_it_related = check_it_related(response_text)
        
        logger.info(f"Chat request processed successfully. IT-related: {is_it_related}")
        
        return ChatResponse(
            message=response_text,
            is_it_related=is_it_related
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
        )

