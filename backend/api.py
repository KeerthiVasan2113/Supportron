"""
FastAPI backend server for Chat API.
Hybrid system using:
- Qwen2.5-0.5B for chat & speed
- Phi-2 for reasoning
- RAG with tech docs for retrieval
"""

from __future__ import annotations

import re
import sys
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple

import ollama
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# RAG model and logging imports
project_root = Path(__file__).parent.parent
data_processing_path = project_root / "data-processing"
sys.path.insert(0, str(data_processing_path))
from build_rag_model import SimpleRAGModel
from logger_utils import setup_logger

# Setup logging with proper configuration
logger = setup_logger("logs/api.log", console_output=True)

# Constants
class Config:
    """Application configuration constants."""
    # Model names
    QWEN_MODEL: str = "qwen2.5:0.5b"
    PHI_MODEL: str = "phi:latest"
    
    # RAG configuration
    RAG_MAX_DISTANCE: float = 0.8
    RAG_TOP_DOCS: int = 5
    RAG_CONTEXT_LENGTH: int = 500
    RAG_PREVIEW_LENGTH: int = 200
    
    # Code detection thresholds
    MIN_TEXT_LENGTH_FOR_EXTRACTION: int = 10
    MIN_CODE_LENGTH: int = 5
    MAX_WORDS_FOR_CODE: int = 8
    MAX_WORDS_FOR_SENTENCE: int = 6
    
    # CORS origins
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

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

# Global state
rag_model: Optional[SimpleRAGModel] = None


class CodeLanguage(str, Enum):
    """Supported code languages for syntax highlighting."""
    PHP = "php"
    PYTHON = "python"
    APACHE = "apache"
    SQL = "sql"
    BASH = "bash"
    HTML = "html"
    NONE = ""


@lru_cache(maxsize=128)
def _compile_regex_patterns() -> Tuple[re.Pattern, ...]:
    """Compile regex patterns once for better performance."""
    return tuple(re.compile(pattern, re.IGNORECASE) for pattern in [
        r'^\s*\$',
        r'^\s*#\s*[a-zA-Z]',
        r'^\s*<\?php',
        r'^\s*<\?',
        r'^\s*<IfModule',
        r'^\s*</IfModule',
        r'^\s*AuthType\s+',
        r'^\s*AuthName\s+',
        r'^\s*AuthUserFile\s+',
        r'^\s*Require\s+',
        r'^\s*import\s+[a-zA-Z]',
        r'^\s*from\s+[a-zA-Z]',
        r'^\s*def\s+[a-zA-Z_]',
        r'^\s*class\s+[a-zA-Z_]',
        r'^\s*if\s+[\(a-zA-Z_]',
        r'^\s*for\s+[\(a-zA-Z_]',
        r'^\s*while\s+[\(a-zA-Z_]',
        r'^\s*return\s+',
        r'^\s*SELECT\s+',
        r'^\s*INSERT\s+',
        r'^\s*UPDATE\s+',
        r'^\s*DELETE\s+',
        r'^\s*CREATE\s+',
        r'^\s*ALTER\s+',
        r'^\s*DROP\s+',
        r'^\s*curl\s+',
        r'^\s*npm\s+',
        r'^\s*pip\s+',
        r'^\s*sudo\s+',
        r'^\s*postconf\s+',
        r'^\s*git\s+',
        r'^\s*#!/',
    ])


def _detect_language(code: str) -> CodeLanguage:
    """
    Detect programming language from code snippet.
    
    Args:
        code: Code snippet to analyze
        
    Returns:
        Detected language enum
    """
    code_lower = code.lower()
    
    # PHP detection
    if any(keyword in code_lower for keyword in ['php', '<?php', '<?', '$_session', 'echo']):
        return CodeLanguage.PHP
    
    # Python detection
    if any(keyword in code_lower for keyword in ['python', 'import', 'def ', 'class ', 'print(']):
        return CodeLanguage.PYTHON
    
    # Apache detection
    if any(keyword in code_lower for keyword in ['<ifmodule', 'authtype', 'require', 'authname', 'authuserfile', '</ifmodule']):
        return CodeLanguage.APACHE
    
    # SQL detection
    if any(keyword in code_lower for keyword in ['select', 'insert', 'update', 'delete', 'create', 'alter', 'drop']):
        return CodeLanguage.SQL
    
    # Bash/Shell detection
    if any(keyword in code_lower for keyword in ['$', 'npm', 'pip', 'curl', 'bash', 'shell', 'sudo', 'postconf', 'git', '#!/']):
        return CodeLanguage.BASH
    
    # HTML detection
    if any(keyword in code_lower for keyword in ['<html', '<div', '<script', '</html', '<', '>', 'html', 'xml']):
        return CodeLanguage.HTML
    
    return CodeLanguage.NONE


def _clean_markdown_heading(line: str) -> str:
    """
    Clean markdown heading by removing markdown syntax.
    
    Removes:
    - `**` (bold markers)
    - `###`, `##`, `#` (heading markers)
    - Leading/trailing whitespace
    
    Args:
        line: Line that may be a markdown heading
        
    Returns:
        Cleaned heading text
    """
    cleaned = line.strip()
    
    # Remove markdown heading markers (###, ##, #)
    cleaned = re.sub(r'^#{1,6}\s+', '', cleaned)
    
    # Remove bold markers (**text**)
    cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
    
    # Remove single asterisks (*text*)
    cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
    
    # Remove any remaining leading/trailing asterisks
    cleaned = cleaned.strip('*').strip()
    
    return cleaned


def _is_markdown_heading(line: str) -> bool:
    """
    Check if a line is a markdown heading.
    
    Args:
        line: Line to check
        
    Returns:
        True if line is a markdown heading
    """
    stripped = line.strip()
    
    # Check for markdown heading syntax (#, ##, ###, etc.)
    if re.match(r'^#{1,6}\s+', stripped):
        return True
    
    # Check for bold heading (**text**)
    if re.match(r'^\*\*.*\*\*$', stripped) and not re.search(r'[{}();=<>\[\]]', stripped):
        return True
    
    # Check for numbered heading with bold (e.g., "4. **Heading**")
    if re.match(r'^\d+\.\s+\*\*.*\*\*$', stripped):
        return True
    
    return False


def format_code_blocks(text: str) -> str:
    """
    Post-process text to ensure code blocks are properly formatted.
    
    Detects code patterns and wraps them in markdown code blocks.
    Only wraps pure code/commands/queries on their own lines.
    Also cleans up excessive punctuation and markdown headings.
    
    Args:
        text: Input text to format
        
    Returns:
        Formatted text with code blocks properly wrapped
    """
    if not text or not text.strip():
        return text
    
    lines = text.split('\n')
    formatted_lines: List[str] = []
    in_code_block = False
    code_block_lines: List[str] = []
    i = 0
    
    # Get compiled regex patterns for better performance
    code_indicators = _compile_regex_patterns()
    
    # Compile command patterns once for better performance
    _command_patterns = [
        re.compile(r'(sudo\s+[^\s]+(?:\s+(?:[^\s]+|[\'"][^\'"]*[\'"]))*?)', re.IGNORECASE),
        re.compile(r'(postconf\s+[^\s]+(?:\s+(?:[^\s]+|[\'"][^\'"]*[\'"]))*?)', re.IGNORECASE),
        re.compile(r'(curl\s+[^\s]+(?:\s+[^\s]+)*)', re.IGNORECASE),
        re.compile(r'(npm\s+[^\s]+(?:\s+[^\s]+)*)', re.IGNORECASE),
        re.compile(r'(pip\s+[^\s]+(?:\s+[^\s]+)*)', re.IGNORECASE),
        re.compile(r'(git\s+[^\s]+(?:\s+[^\s]+)*)', re.IGNORECASE),
        re.compile(r'(\$\s+[^\s]+(?:\s+[^\s]+)*)', re.IGNORECASE),
        re.compile(r'(SELECT\s+.*?;)', re.IGNORECASE),
        re.compile(r'(INSERT\s+.*?;)', re.IGNORECASE),
        re.compile(r'(UPDATE\s+.*?;)', re.IGNORECASE),
        re.compile(r'(DELETE\s+.*?;)', re.IGNORECASE),
        re.compile(r'(CREATE\s+.*?;)', re.IGNORECASE),
    ]
    _trailing_words_pattern = re.compile(r'\s+(using|with|by|via|through)\s*$', re.IGNORECASE)
    
    def extract_code_from_line(line: str) -> Tuple[str, str]:
        """
        Extract code from a line that might contain descriptive text.
        
        Args:
            line: Line that may contain both text and code
            
        Returns:
            Tuple of (text_part, code_part). If no code found, returns (line, '')
        """
        stripped = line.strip()
        if not stripped:
            return (line, '')
        
        # Look for common command patterns in the line
        for pattern in _command_patterns:
            match = pattern.search(stripped)
            if match:
                code_part = match.group(1).strip()
                code_start = match.start()
                text_part = stripped[:code_start].strip()
                
                # Only extract if there's substantial text before the code
                # and the code part is substantial (not just a word)
                if (len(text_part) > Config.MIN_TEXT_LENGTH_FOR_EXTRACTION and 
                    len(code_part) > Config.MIN_CODE_LENGTH):
                    # Clean up text part - remove trailing words like "using", "with", "by"
                    text_part = _trailing_words_pattern.sub('', text_part)
                    return (text_part, code_part)
        
        return (line, '')
    
    # Check if a line is PURELY code (no descriptive text mixed in)
    def is_pure_code_line(line: str) -> bool:
        """
        Check if a line is purely code with no descriptive text.
        A line is pure code if it:
        - Starts with a code indicator
        - Has code structure and minimal words
        - Doesn't look like a sentence
        
        Headings are NEVER considered code.
        """
        stripped = line.strip()
        if not stripped:
            return False
        
        # Already in a code block marker
        if stripped.startswith('```'):
            return True
        
        # NEVER treat markdown headings as code
        if _is_markdown_heading(line):
            return False
        
        # Exclude numbered lists, bullet points, and regular text
        # Numbered lists: "1. ", "2. ", etc.
        if re.match(r'^\d+\.\s+', stripped):
            return False
        
        # Bullet points: "- ", "* ", etc. (but not code comments or commands)
        if re.match(r'^[-*]\s+[A-Z][a-z]', stripped):  # Bullet with capital letter (likely text)
            return False
        
        # Exclude lines that start with descriptive text (capital letter, many words)
        # If line starts with capital and has many words, it's likely descriptive text
        if re.match(r'^[A-Z][a-z]+', stripped):
            word_count = len(stripped.split())
            # If it has many words and looks like a sentence, it's not pure code
            if word_count > 8:
                return False
            # If it ends with punctuation and has many words, it's descriptive text
            if word_count > 5 and stripped.rstrip().endswith(('.', '!', '?', ':', ',')):
                return False
        
        # Check against strict code patterns (must match at the START)
        for pattern in code_indicators:
            if pattern.match(stripped):
                return True
        
        # Check for code-like content with strict criteria
        # Must have multiple code indicators to be considered code
        code_chars = ['{', '}', '(', ')', ';', '=', '[', ']']
        code_char_count = sum(1 for char in stripped if char in code_chars)
        
        # Must have at least 2 code characters AND not look like a sentence
        if code_char_count >= 2:
            word_count = len(stripped.split())
            ends_with_punct = stripped.rstrip().endswith(('.', '!', '?', ':', ','))
            
            # If it has many words and ends with punctuation, it's likely text
            if word_count > 6 and ends_with_punct:
                return False
            
            # Must have code structure (brackets, braces, or function calls)
            has_code_structure = (
                '{' in stripped or 
                '}' in stripped or 
                ('(' in stripped and ')' in stripped) or
                ('[' in stripped and ']' in stripped) or
                ('=' in stripped and '==' not in stripped)  # Assignment, not comparison
            )
            
            # Also check that it doesn't start with descriptive text
            # If it starts with a capital letter and has many words, it's likely mixed
            if has_code_structure and not re.match(r'^[A-Z][a-z]+\s+[a-z]+', stripped):
                return True
        
        # Check for HTML/XML tags (strict - must be actual tags, not in sentences)
        html_tag_match = re.search(r'<[A-Za-z][A-Za-z0-9]*[^>]*>', stripped)
        if html_tag_match:
            # Exclude if it's part of a sentence (many words)
            if len(stripped.split()) > 8:
                return False
            # Exclude if it starts with descriptive text
            if re.match(r'^[A-Z][a-z]+\s+', stripped):
                return False
            return True
        
        return False
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Handle markdown headings - clean them and never wrap in code blocks
        if _is_markdown_heading(line):
            cleaned_heading = _clean_markdown_heading(line)
            formatted_lines.append(cleaned_heading)
            i += 1
            continue
        
        # Handle existing code block markers
        if stripped.startswith('```'):
            if in_code_block:
                # End code block
                if code_block_lines:
                    formatted_lines.append('```')
                    formatted_lines.extend(code_block_lines)
                    formatted_lines.append('```')
                    code_block_lines = []
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
                code_block_lines = []
            formatted_lines.append(line)
            i += 1
            continue
        
        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue
        
        # Check if line has code mixed with text
        text_part, code_part = extract_code_from_line(line)
        
        if code_part:
            # Line has both text and code - separate them
            if text_part:
                # Add the descriptive text as regular text
                formatted_lines.append(text_part)
            # Add the code in its own code block
            lang = _detect_language(code_part)
            formatted_lines.append(f'```{lang.value if lang != CodeLanguage.NONE else ""}')
            formatted_lines.append(code_part)
            formatted_lines.append('```')
            i += 1
        elif is_pure_code_line(line):
            # Pure code line - collect consecutive code lines
            code_lines = [line]
            i += 1
            
            # Look ahead for more code lines
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                
                # Stop if we hit a blank line followed by non-code
                if not next_stripped:
                    # Check the line after the blank
                    if i + 1 < len(lines):
                        if not is_pure_code_line(lines[i + 1]):
                            break
                    else:
                        break
                elif not is_pure_code_line(next_line):
                    break
                
                code_lines.append(next_line)
                i += 1
            
            # Wrap code lines in code block
            all_code = ' '.join(code_lines)
            lang = _detect_language(all_code)
            formatted_lines.append(f'```{lang.value if lang != CodeLanguage.NONE else ""}')
            formatted_lines.extend(code_lines)
            formatted_lines.append('```')
        else:
            # Regular text line - clean up excessive punctuation and markdown artifacts
            cleaned_line = line
            
            # Remove markdown bold markers from regular text (**text**)
            cleaned_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_line)
            
            # Remove markdown heading markers if they appear in text
            cleaned_line = re.sub(r'^#{1,6}\s+', '', cleaned_line)
            
            # Remove multiple consecutive punctuation marks
            cleaned_line = re.sub(r'([.!?])\1{2,}', r'\1\1', cleaned_line)  # Multiple periods/exclamations
            cleaned_line = re.sub(r'([,;:])\1+', r'\1', cleaned_line)  # Multiple commas/semicolons/colons
            
            # Remove trailing multiple punctuation (keep only one)
            cleaned_line = re.sub(r'([.!?])+$', r'\1', cleaned_line)
            
            formatted_lines.append(cleaned_line)
            i += 1
    
    # Handle any remaining code block
    if in_code_block and code_block_lines:
        formatted_lines.append('```')
        formatted_lines.extend(code_block_lines)
        formatted_lines.append('```')
    
    result = '\n'.join(formatted_lines)
    
    # Final cleanup: remove excessive punctuation in the entire text
    # Remove multiple spaces
    result = re.sub(r' +', ' ', result)
    # Remove multiple newlines (more than 2)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str = Field(..., min_length=1, max_length=5000, description="User's question")
    show_sources: bool = Field(default=True, description="Whether to include source documents")
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        """
        Validate and sanitize question input.
        
        Args:
            v: Input question string
            
        Returns:
            Sanitized question string
            
        Raises:
            ValueError: If question is empty or invalid
        """
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        
        # Sanitize: remove excessive whitespace and limit length
        sanitized = v.strip()
        
        # Remove control characters except newlines and tabs
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\t')
        
        # Limit length to prevent DoS
        if len(sanitized) > 5000:
            raise ValueError("Question is too long. Maximum length is 5000 characters.")
        
        return sanitized


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


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize Ollama models and RAG on startup."""
    global rag_model
    
    # Verify Ollama models are available
    try:
        logger.info("Checking Ollama models availability...")
        # Test Qwen
        ollama.generate(model=Config.QWEN_MODEL, prompt="test")
        logger.info(f"✓ Qwen model '{Config.QWEN_MODEL}' is ready!")
        
        # Test Phi-2
        ollama.generate(model=Config.PHI_MODEL, prompt="test")
        logger.info(f"✓ Phi-2 model '{Config.PHI_MODEL}' is ready!")
    except Exception as e:
        logger.error(f"Failed to connect to Ollama or model not found: {e}", exc_info=True)
        logger.warning("Make sure Ollama is running and models are pulled:")
        logger.warning("  ollama pull qwen2.5:0.5b")
        logger.warning("  ollama pull phi:latest")
        # Don't raise - allow server to start, but chat will fail gracefully
    
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
        logger.info("✓ RAG model initialized successfully!")
    except FileNotFoundError as e:
        logger.error(f"Vector database not found: {e}")
        logger.warning("RAG will not be available. Chat will use Qwen2.5B directly.")
        rag_model = None
    except Exception as e:
        logger.error(f"Failed to initialize RAG model: {e}", exc_info=True)
        logger.warning("RAG will not be available. Chat will use Qwen2.5B directly.")
        rag_model = None


def _check_ollama_available() -> bool:
    """
    Check if Ollama service is available.
    
    Returns:
        True if Ollama is available, False otherwise
    """
    try:
        ollama.list()
        return True
    except Exception as e:
        logger.debug(f"Ollama check failed: {e}")
        return False


@app.get("/", tags=["health"])
async def root() -> dict:
    """Root endpoint with service information."""
    return {
        "status": "online",
        "service": "Hybrid Chat API",
        "models": {
            "qwen": Config.QWEN_MODEL,
            "phi": Config.PHI_MODEL
        },
        "rag_available": rag_model is not None,
        "model_available": _check_ollama_available()
    }


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "models": {
            "qwen": Config.QWEN_MODEL,
            "phi": Config.PHI_MODEL
        },
        "rag_available": rag_model is not None,
        "model_available": _check_ollama_available()
    }


def _retrieve_rag_documents(question: str) -> List[dict]:
    """
    Retrieve relevant documents from RAG model.
    
    Args:
        question: User's question
        
    Returns:
        List of relevant documents, empty if none found or RAG unavailable
    """
    if rag_model is None:
        return []
    
    try:
        rag_docs = rag_model.retrieve(question)
        if not rag_docs:
            return []
        
        # Filter by distance threshold (lower is better)
        relevant_docs = [
            doc for doc in rag_docs 
            if doc.get('distance', 1.0) < Config.RAG_MAX_DISTANCE
        ]
        
        if relevant_docs:
            logger.info(f"Found {len(relevant_docs)} relevant RAG documents")
            return relevant_docs[:Config.RAG_TOP_DOCS]
        
        logger.info("RAG documents found but distance too high, using direct Qwen")
        return []
    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}, falling back to direct Qwen")
        return []


def _generate_with_rag_pipeline(question: str, rag_docs: List[dict]) -> Tuple[str, Optional[List[SourceDocument]]]:
    """
    Generate answer using RAG → Phi-2 → Qwen2.5B pipeline.
    
    Args:
        question: User's question
        rag_docs: Relevant RAG documents
        
    Returns:
        Tuple of (answer, sources)
    """
    logger.info("Using RAG + Phi-2 + Qwen2.5B pipeline")
    
    # Prepare context from RAG documents
    context_text = "\n\n".join([
        f"Source: {doc.get('source_file', 'unknown')}\n"
        f"{doc.get('text', '')[:Config.RAG_CONTEXT_LENGTH]}"
        for doc in rag_docs
    ])
    
    # Step 1: Use Phi-2 for reasoning on the context
    phi_prompt = f"""Based on the following technical documentation, analyze and reason about the user's question.

Technical Documentation:
{context_text}

User Question: {question}

Please analyze the documentation and provide a reasoned answer. Focus on accuracy and technical details."""
    
    try:
        phi_response = ollama.generate(
            model=Config.PHI_MODEL,
            prompt=phi_prompt,
            stream=False
        )
        phi_reasoning = phi_response.get("response", "").strip()
    except Exception as e:
        logger.error(f"Phi-2 reasoning failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reasoning service temporarily unavailable"
        )
    
    # Step 2: Use Qwen2.5B to structure the reasoned answer
    qwen_prompt = f"""Based on the following reasoned analysis, provide a clear, well-structured answer to the user's question.

Reasoned Analysis:
{phi_reasoning}

User Question: {question}

Provide a clear, structured answer with proper formatting. Use code blocks for any code examples."""
    
    try:
        qwen_response = ollama.generate(
            model=Config.QWEN_MODEL,
            prompt=qwen_prompt,
            stream=False
        )
        answer = qwen_response.get("response", "").strip()
    except Exception as e:
        logger.error(f"Qwen2.5B generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Generation service temporarily unavailable"
        )
    
    # Format sources
    sources = [
        SourceDocument(
            source_file=doc.get("source_file", "unknown"),
            preview=doc.get("text", "")[:Config.RAG_PREVIEW_LENGTH] + "...",
            distance=doc.get("distance")
        )
        for doc in rag_docs
    ] if rag_docs else None
    
    return answer, sources


def _generate_direct_answer(question: str) -> str:
    """
    Generate answer directly using Qwen2.5B.
    
    Args:
        question: User's question
        
    Returns:
        Generated answer
    """
    logger.info("No relevant RAG documents, using Qwen2.5B directly")
    
    try:
        response = ollama.generate(
            model=Config.QWEN_MODEL,
            prompt=question,
            stream=False
        )
        return response.get("response", "").strip()
    except Exception as e:
        logger.error(f"Qwen2.5B generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Generation service temporarily unavailable. Make sure Ollama is running."
        )


@app.post("/api/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Hybrid chat endpoint.
    
    Pipeline:
    - If RAG has relevant docs: Use RAG → Phi-2 reasoning → Qwen2.5B structuring
    - If no RAG docs: Use Qwen2.5B directly
    
    Args:
        request: Chat request with question and options
    
    Returns:
        Chat response with answer and sources
        
    Raises:
        HTTPException: If service is unavailable or error occurs
    """
    logger.info(f"Received question: {request.question}")
    
    try:
        # Step 1: Check if RAG has relevant documents
        rag_docs = _retrieve_rag_documents(request.question)
        
        # Step 2: Process based on whether we have RAG docs
        if rag_docs:
            answer, sources = _generate_with_rag_pipeline(request.question, rag_docs)
        else:
            answer = _generate_direct_answer(request.question)
            sources = None
        
        if not answer:
            answer = "I apologize, but I couldn't generate a response. Please try again."
        
        # Post-process answer to format code blocks and clean punctuation
        answer = format_code_blocks(answer)
        
        # Format response
        chat_response = ChatResponse(
            answer=answer,
            question=request.question,
            sources=sources
        )
        
        logger.info(
            f"Generated answer (length: {len(answer)} chars, "
            f"sources: {len(sources) if sources else 0})"
        )
        return chat_response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}", exc_info=True)
        error_msg = str(e).lower()
        if "connection" in error_msg or "refused" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Ollama service is not available. Make sure Ollama is running."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your question."
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        log_level="info"
    )

