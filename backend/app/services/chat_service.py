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
        
        logger.info("RAG documents found but distance too high, using direct Ollama")
        return []
    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}, falling back to direct Ollama")
        return []


def format_conversation_history(history: Optional[List[dict]], include_all: bool = False) -> str:
    """
    Format conversation history for inclusion in prompts.
    
    Args:
        history: List of previous messages with 'role' and 'content'
        include_all: If True, include all messages. If False, limit to last 10 messages for faster processing.
        
    Returns:
        Formatted conversation history string
    """
    if not history or len(history) == 0:
        return ""
    
    # Use all history if requested, otherwise limit to last 10 messages for faster processing
    messages_to_format = history if include_all else history[-10:]
    
    formatted = []
    for idx, msg in enumerate(messages_to_format, 1):
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role == 'user':
            formatted.append(f"[Message {idx}] User: {content}")
        elif role == 'assistant':
            formatted.append(f"[Message {idx}] Assistant: {content}")
    
    # Add summary if we truncated
    if not include_all and len(history) > 10:
        formatted.insert(0, f"[Note: This is a conversation with {len(history)} total messages. Showing the last 10 messages below. The first message was: \"{history[0].get('content', '')[:100]}...\"]")
    
    return "\n".join(formatted)


def generate_with_rag_pipeline(
    question: str, 
    rag_docs: List[dict],
    conversation_history: Optional[List[dict]] = None
) -> Tuple[str, Optional[List[SourceDocument]]]:
    """
    Generate answer using RAG with LLM model.
    
    Args:
        question: User's question
        rag_docs: Relevant RAG documents
        conversation_history: Previous messages in the conversation
        
    Returns:
        Tuple of (answer, sources)
        
    Raises:
        HTTPException: If generation fails
    """
    logger.info("Using RAG + LLM pipeline")
    
    # Check if question is about the conversation itself
    question_lower = question.lower()
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
    history_text = format_conversation_history(conversation_history, include_all=is_about_conversation)
    history_context = ""
    if history_text:
        history_context = f"""

=== COMPLETE CONVERSATION HISTORY ===
This is the full conversation history up to this point. Use this to answer questions about what was discussed, asked, or mentioned earlier in the conversation.

{history_text}

=== END OF CONVERSATION HISTORY ===
"""
    
    # Use LLM to generate answer with RAG context
    prompt = f"""You are an expert technical support AI assistant. Your role is to provide direct, actionable solutions to technical problems.

Documentation:
{context_text}{history_context}

Current Question: {question}

CRITICAL INSTRUCTIONS:
1. FOCUS ON THE ACTUAL PROBLEM: Identify what the user is actually trying to solve. If they say "Unable to connect to server IP: 199.43.207.194", focus on connection troubleshooting for that specific IP, not generic server setup.
2. NO ASSUMPTIONS: Do NOT assume operating system, environment, or setup. If the user mentions "Outlook" and "email accounts", they're likely on Windows. If they mention a server IP, address server/client connectivity issues.
3. DIRECT SOLUTIONS FIRST: Provide step-by-step solutions that directly address the problem. Only ask clarifying questions if absolutely necessary to solve the issue.
4. USE CONTEXT: The conversation history shows the full context. Read it carefully and address the specific issues mentioned.
5. RELEVANCE: Only provide information directly related to solving the problem. Do not suggest unrelated commands, tools, or steps.
6. COMPLETE COMMANDS: All commands must be complete and executable. Never truncate or leave commands incomplete.
7. PLATFORM AWARENESS: Support all platforms but choose solutions based on the problem context (Outlook = Windows, server IP = network/connectivity).

EXAMPLE OF GOOD RESPONSE:
User: "Unable to connect to server IP: 199.43.207.194"
Good Response: "To troubleshoot the connection issue with server 199.43.207.194, try these steps:
1. Test connectivity: ping 199.43.207.194
2. Check if the port is open: telnet 199.43.207.194 443 (or the specific port)
3. Verify firewall settings aren't blocking the connection
4. Check if the server is running and accessible from your network"

Now answer the current question with a direct, actionable solution:"""
    
    try:
        response = ollama.generate(
            model=Config.MODEL,
            prompt=prompt,
            stream=False,
            options={
                "num_predict": Config.OLLAMA_NUM_PREDICT,
                "temperature": Config.OLLAMA_TEMPERATURE,
                "top_p": Config.OLLAMA_TOP_P,
                "top_k": Config.OLLAMA_TOP_K,
            }
        )
        answer = response.get("response", "").strip()
    except Exception as e:
        logger.error(f"Model generation failed: {e}")
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
    conversation_history: Optional[List[dict]] = None
) -> str:
    """
    Generate answer directly using LLM.
    
    Args:
        question: User's question
        conversation_history: Previous messages in the conversation
        
    Returns:
        Generated answer
        
    Raises:
        HTTPException: If generation fails
    """
    logger.info("No relevant RAG documents, using LLM directly")
    
    # Check if question is about the conversation itself
    question_lower = question.lower()
    is_about_conversation = any(keyword in question_lower for keyword in [
        'first question', 'first message', 'earlier', 'previous', 'before', 
        'what did i ask', 'what did you say', 'conversation', 'chat history',
        'earlier in', 'mentioned', 'discussed', 'talked about'
    ])
    
    # Format conversation history - include all if question is about the conversation
    history_text = format_conversation_history(conversation_history, include_all=is_about_conversation)
    
    if history_text:
        prompt = f"""You are an expert technical support AI assistant. Your role is to provide direct, actionable solutions to technical problems.

Conversation History:
{history_text}

Current Question: {question}

CRITICAL INSTRUCTIONS:
1. FOCUS ON THE ACTUAL PROBLEM: Read the conversation history and current question carefully. Identify what the user is actually trying to solve. If they mention "Outlook email not connecting after SSL update" and then "Unable to connect to server IP: 199.43.207.194", focus on Outlook email server connection issues, not generic Linux server commands.
2. NO ASSUMPTIONS: Do NOT assume operating system or environment. If the user mentions "Outlook", they're on Windows. If they mention a server IP, address connectivity issues. Do not suggest Linux commands for Windows Outlook problems.
3. DIRECT SOLUTIONS FIRST: Provide step-by-step solutions that directly address the problem. If the user says "Unable to connect to server IP: X", provide connection troubleshooting steps for that specific IP and the application (Outlook email).
4. USE FULL CONTEXT: The conversation history contains important context. If the user mentioned "SSL update" and "Outlook", focus on SSL/TLS configuration for Outlook email accounts connecting to the server IP.
5. RELEVANCE: Only provide information directly related to solving the problem. Do not suggest unrelated commands, tools, or generic troubleshooting steps.
6. COMPLETE COMMANDS: All commands must be complete and executable. Never truncate commands.
7. PLATFORM AWARENESS: Choose solutions based on context (Outlook = Windows email client, server IP = network/email server connectivity).

EXAMPLE OF GOOD RESPONSE:
User (after mentioning Outlook email issues): "Unable to connect to server IP: 199.43.207.194"
Good Response: "For Outlook email connection issues with server 199.43.207.194, check:
1. Outlook Account Settings: File > Account Settings > Server Settings - verify the incoming/outgoing server matches 199.43.207.194
2. Port Settings: Ensure correct ports (IMAP: 993, POP3: 995, SMTP: 465/587) with SSL/TLS enabled
3. Test Connection: Use Outlook's Test Account Settings feature
4. Firewall: Ensure Windows Firewall allows Outlook to connect to 199.43.207.194
5. SSL Certificate: After SSL update, you may need to re-enter password or accept new certificate"

Now answer the current question with a direct, actionable solution:"""
    else:
        prompt = f"""You are an expert technical support AI assistant. Analyze the user's problem and provide direct, actionable solutions.

Question: {question}

CRITICAL INSTRUCTIONS:
1. UNDERSTAND THE ACTUAL PROBLEM: Read the question carefully. What is the user actually trying to solve? Focus on that specific issue.
2. NO ASSUMPTIONS: Do NOT assume the user's operating system, environment, or setup unless explicitly stated. If unclear, provide solutions for the most likely scenario based on the problem description.
3. DIRECT SOLUTIONS: Provide step-by-step solutions that directly address the stated problem. Avoid generic troubleshooting steps that don't relate to the specific issue.
4. RELEVANT RESPONSES: Only provide information relevant to solving the user's problem. Do not suggest unrelated commands or steps.
5. COMPLETE COMMANDS: When providing commands, ensure they are complete and executable. Never truncate commands.
6. PLATFORM SUPPORT: Support Windows, Linux, macOS, and cloud services. Choose the appropriate solution based on the problem context.

Answer the question directly and provide a concrete solution:"""
    
    try:
        response = ollama.generate(
            model=Config.MODEL,
            prompt=prompt,
            stream=False,
            options={
                "num_predict": Config.OLLAMA_NUM_PREDICT,
                "temperature": Config.OLLAMA_TEMPERATURE,
                "top_p": Config.OLLAMA_TOP_P,
                "top_k": Config.OLLAMA_TOP_K,
            }
        )
        return response.get("response", "").strip()
    except Exception as e:
        logger.error(f"Model generation failed: {e}")
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
            answer, sources = generate_with_rag_pipeline(question, rag_docs, conversation_history)
        else:
            answer = generate_direct_answer(question, conversation_history)
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

