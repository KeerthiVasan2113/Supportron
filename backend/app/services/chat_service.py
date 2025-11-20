"""
Chat service for handling chat requests and generating responses.
"""

from typing import List, Optional, Tuple

import ollama
from fastapi import HTTPException, status

from app.api.dependencies import get_rag_model
from app.api.v1.schemas import SourceDocument
from app.core.config import Config
from app.core.logging_config import logger
from app.utils.helpers import format_code_blocks


def check_ollama_available() -> bool:
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


def retrieve_rag_documents(question: str) -> List[dict]:
    """
    Retrieve relevant documents from RAG model.
    
    Args:
        question: User's question
        
    Returns:
        List of relevant documents, empty if none found or RAG unavailable
    """
    rag_model = get_rag_model()
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


def format_conversation_history(history: Optional[List[dict]], include_all: bool = False) -> str:
    """
    Format conversation history for inclusion in prompts.
    
    Args:
        history: List of previous messages with 'role' and 'content'
        include_all: If True, include all messages. If False, limit to last 30 messages.
        
    Returns:
        Formatted conversation history string
    """
    if not history or len(history) == 0:
        return ""
    
    # Use all history if requested, otherwise limit to last 30 messages for token management
    messages_to_format = history if include_all else history[-30:]
    
    formatted = []
    for idx, msg in enumerate(messages_to_format, 1):
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role == 'user':
            formatted.append(f"[Message {idx}] User: {content}")
        elif role == 'assistant':
            formatted.append(f"[Message {idx}] Assistant: {content}")
    
    # Add summary if we truncated
    if not include_all and len(history) > 30:
        formatted.insert(0, f"[Note: This is a conversation with {len(history)} total messages. Showing the last 30 messages below. The first message was: \"{history[0].get('content', '')[:100]}...\"]")
    
    return "\n".join(formatted)


def generate_with_rag_pipeline(
    question: str,
    rag_docs: List[dict],
    conversation_history: Optional[List[dict]] = None,
    include_history: bool = False
) -> Tuple[str, Optional[List[SourceDocument]]]:
    """
    Generate answer using RAG → Phi-2 → Qwen2.5B pipeline.
    
    Args:
        question: User's question
        rag_docs: Relevant RAG documents
        conversation_history: Previous messages in the conversation
        
    Returns:
        Tuple of (answer, sources)
        
    Raises:
        HTTPException: If generation fails
    """
    logger.info("Using RAG + Phi-2 + Qwen2.5B pipeline")
    
    # Determine whether to include conversation history in the prompts
    question_lower = question.lower()
    is_about_conversation = False
    if include_history:
        is_about_conversation = any(keyword in question_lower for keyword in [
            'first question', 'first message', 'earlier', 'previous', 'before', 
            'what did i ask', 'what did you say', 'conversation', 'chat history',
            'earlier in', 'mentioned', 'discussed', 'talked about'
        ])
    
    # Prepare context from RAG documents
    context_text = "\n\n".join([
        f"Source: {doc.get('source_file', 'unknown')}\n"
        f"{doc.get('text', '')[:Config.RAG_CONTEXT_LENGTH]}"
        for doc in rag_docs
    ])
    
    # Format conversation history - include all if question is about the conversation
    history_text = ""
    history_context = ""
    if include_history and conversation_history:
        history_text = format_conversation_history(conversation_history, include_all=is_about_conversation)
    if history_text:
        history_context = f"""

=== COMPLETE CONVERSATION HISTORY ===
This is the full conversation history up to this point. Use this to answer questions about what was discussed, asked, or mentioned earlier in the conversation.

{history_text}

=== END OF CONVERSATION HISTORY ===
"""
    
    # Step 1: Use Phi-2 for reasoning on the context
    phi_prompt = f"""You are analyzing a user's question in the context of technical documentation.

Technical Documentation:
{context_text}{history_context}

Current User Question: {question}

IMPORTANT INSTRUCTIONS:
1. If the question asks about the conversation itself (e.g., "what was the first question", "what did I ask earlier", "what did you say before"), you MUST use the conversation history above to answer.
2. The conversation history shows numbered messages - you can reference specific messages by their numbers.
3. For questions about the conversation, look through ALL the messages in the conversation history.
4. For technical questions, use both the documentation and conversation context.
5. Maintain continuity with previous messages in the conversation.

Please analyze and provide a reasoned answer based on the documentation and conversation history."""
    
    # Add brief instruction to use layman's terms and be concise
    phi_prompt = phi_prompt + "\n\nNOTE: Answer in simple, layman's terms. Be concise and give a direct solution or steps. Only use the conversation history if it was explicitly requested by the user."

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
    # Reuse the formatted history from step 1
    history_context_for_qwen = ""
    if history_text:
        history_context_for_qwen = f"""

=== CONVERSATION HISTORY ===
{history_text}
=== END OF CONVERSATION HISTORY ===
"""
    
    qwen_prompt = f"""Based on the reasoned analysis below, provide a clear, well-structured answer to the user's question.

Reasoned Analysis:
{phi_reasoning}{history_context_for_qwen}

Current User Question: {question}

INSTRUCTIONS:
1. If the question is about the conversation (e.g., "first question", "what I asked", "earlier message"), use the conversation history above to find and reference the specific messages.
2. Reference message numbers from the conversation history when answering questions about the conversation.
3. Provide a clear, structured answer with proper formatting.
4. Use code blocks for any code examples.
5. Maintain continuity and context from the conversation history.

Provide your answer now:"""
    
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


def generate_direct_answer(
    question: str,
    conversation_history: Optional[List[dict]] = None,
    include_history: bool = False
) -> str:
    """
    Generate answer directly using Qwen2.5B.
    
    Args:
        question: User's question
        conversation_history: Previous messages in the conversation
        
    Returns:
        Generated answer
        
    Raises:
        HTTPException: If generation fails
    """
    logger.info("No relevant RAG documents, using Qwen2.5B directly")
    
    history_text = ""
    if include_history and conversation_history:
        # include full history when explicitly requested
        history_text = format_conversation_history(conversation_history, include_all=True)

    if history_text:
        prompt = f"""You are a helpful assistant having a conversation with a user. Below is the conversation history provided by the user.

=== PROVIDED CONVERSATION HISTORY ===
{history_text}
=== END OF PROVIDED CONVERSATION HISTORY ===

Current User Question: {question}

NOTE: Answer in simple, layman's terms. Be concise and give direct steps or the solution. Only use the conversation history because the user explicitly requested it.

Provide a helpful, clear answer based on the conversation history and your knowledge."""
    else:
        prompt = f"Please respond in simple, layman's terms, concisely: {question}"
    
    try:
        response = ollama.generate(
            model=Config.QWEN_MODEL,
            prompt=prompt,
            stream=False
        )
        return response.get("response", "").strip()
    except Exception as e:
        logger.error(f"Qwen2.5B generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Generation service temporarily unavailable. Make sure Ollama is running."
        )


def process_chat_request(
    question: str,
    conversation_history: Optional[List[dict]] = None
) -> Tuple[str, Optional[List[SourceDocument]]]:
    """
    Process a chat request and generate a response.
    
    Args:
        question: User's question
        conversation_history: Previous messages in the conversation for context
        
    Returns:
        Tuple of (answer, sources)
        
    Raises:
        HTTPException: If processing fails
    """
    logger.info(f"Received question: {question}")
    if conversation_history:
        logger.info(f"Conversation history: {len(conversation_history)} previous messages")
        # Log first and last message for debugging
        if len(conversation_history) > 0:
            logger.debug(f"First message in history: {conversation_history[0].get('role', 'unknown')} - {conversation_history[0].get('content', '')[:100]}")
            logger.debug(f"Last message in history: {conversation_history[-1].get('role', 'unknown')} - {conversation_history[-1].get('content', '')[:100]}")
    
    try:
        # Step 1: Check if RAG has relevant documents
        rag_docs = retrieve_rag_documents(question)
        
        # Step 2: Process based on whether we have RAG docs
        if rag_docs:
            answer, sources = generate_with_rag_pipeline(
                question,
                rag_docs,
                conversation_history,
                include_history=(conversation_history is not None)
            )
        else:
            answer = generate_direct_answer(
                question,
                conversation_history,
                include_history=(conversation_history is not None)
            )
            sources = None
        
        if not answer:
            answer = "I apologize, but I couldn't generate a response. Please try again."
        
        # Post-process answer to format code blocks and clean punctuation
        answer = format_code_blocks(answer)
        
        logger.info(
            f"Generated answer (length: {len(answer)} chars, "
            f"sources: {len(sources) if sources else 0})"
        )
        
        return answer, sources
    
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

