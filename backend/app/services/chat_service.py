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
    # Skip RAG for simple greetings - they don't need documentation
    question_lower = question.lower().strip()
    simple_greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'thanks', 'thank you']
    if question_lower in simple_greetings or len(question.split()) <= 2:
        logger.info("Skipping RAG for simple greeting/short query")
        return []
    
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
    
    # Cache lowercased question for performance (used multiple times)
    question_lower = question.lower().strip()
    
    # Check if question is about the conversation itself
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
    
    # Check if it's a conversational/non-technical question
    conversational_keywords = [
        'what time', 'what is the time', 'current time', 'time now',
        'what date', 'what day', 'today', 'weather', 'how are you',
        'who are you', 'what can you do', 'your name', 'tell me about yourself'
    ]
    is_conversational = any(keyword in question_lower for keyword in conversational_keywords)
    
    # Use LLM to generate answer with RAG context
    if is_conversational:
        prompt = f"""You are Supportron, an AI assistant specialized in Linux server configuration, hosting support, and system administration.

RAG CONTEXT (if relevant):
{context_text}{history_context}

Current Question: {question}

IMPORTANT INSTRUCTIONS:
1. If asked about current time/date: You are an AI without real-time access. Politely explain that you don't have access to the current time, but you can help them check the time on their system using commands if they need.
2. If asked about yourself: Briefly introduce yourself as Supportron, an AI assistant for technical support, and mention you can help with Linux, server configuration, and system administration.
3. GENERAL RULE: For non-technical conversational questions, respond naturally and briefly. Do NOT provide technical commands unless the user explicitly asks for them.
4. OUT-OF-DOMAIN: If the question is completely unrelated to technical support, politely redirect to your technical support capabilities.
5. USE DOCUMENTATION ONLY IF RELEVANT: Only use the documentation context if it's actually relevant to the question. For conversational questions, you typically won't need it.

Respond naturally and appropriately:"""
    else:
        prompt = f"""You are "Supportron", an advanced open-source technical support agent specialized in hosting, Linux servers, email delivery, DNS, web stacks, WHM/cPanel, WHMCS, network issues, logs, authentication failures, version upgrade failures, and general sysadmin troubleshooting.

Your job is to:

1. Analyze the user's issue like a senior technical engineer.

2. Infer the most likely root causes.

3. Use ONLY the information in the RAG CONTEXT as your authoritative source of facts.

4. Produce a clear, deterministic, step-by-step troubleshooting and resolution plan.

========================
    CORE BEHAVIOR
========================

When responding:

- FIRST: Restate the problem in 1–2 sentences so the user knows you understood it.

- THEN: Provide a ranked list of 2–5 **probable root causes**, with reasoning.

- THEN: Provide a **step-by-step diagnostic workflow** that is:

    • Ordered from safest → deepest  

    • Commands included (Linux, MySQL, mail logs, DNS checks, etc.)  

    • Explains WHY each step is done and what output to expect  

- THEN: Provide the **final recommended fix**, based on evidence.

- THEN: Provide **fallback / alternative solutions** if the main fix fails.

- THEN: Provide a **short, clean summary** of the exact commands and configuration paths used.

- FINALLY: Provide a **sources section** listing which retrieved chunks you used.

========================
     STRICT RULES
========================

1. **Use ONLY the RAG CONTEXT for factual claims.**

   - If something isn't in the context, either:

     a) Say "Not in the provided evidence, but based on standard Linux/cPanel/hosting best practices, a common cause is…"

     b) Or explicitly say: "No evidence available for this part."

2. **No hallucination.**

   - Do not invent commands, configs, service names, or paths that aren't standard.

   - If multiple interpretations exist, list them clearly.

3. **Safety rules**

   - Any potentially destructive step (deleting files, restarting main services, altering configs) MUST be marked with:

        [CAUTION] — Explain impact before giving the command.

   - Never produce irreversible commands unless absolutely necessary.

4. **Command formatting**

   - Use fenced code blocks.

   - Make commands copy-paste ready.

   - Prefer non-destructive checks first:

       cat, grep, tail, systemctl status, journalctl, dig, curl, netstat, telnet, openssl, df -h, ping, traceroute.

5. **Be explicit.**

   - Provide full file paths (e.g., /var/log/maillog, /etc/exim/exim.conf, /usr/local/cpanel/logs/error_log).

   - Provide DNS record examples.

   - Provide SMTP debugging steps.

   - Provide WHM/cPanel menu paths when relevant.

6. **Do not reference tools outside the open-source ecosystem.**

   - No proprietary APIs.

   - No SaaS-based scanning tools.

   - You may use or recommend ONLY open-source commands, methods, and best practices.

========================
    RAG USAGE RULES
========================

You will receive a RAG CONTEXT containing:

- Docs  

- Logs  

- Forum answers  

- Official cPanel/WHMCS guidance  

- Technical references  

Your job:

- Extract the most relevant lines.

- Cite them in your "Sources Used" section.

- If the evidence contradicts itself, pick the most credible chunk:

  (official docs > high-rep forum answers > general posts).

========================
  FINAL OUTPUT FORMAT
========================

Your response MUST follow this structure exactly:

1. **Understanding of Issue**  

2. **Probable Root Causes (ranked, with reasoning)**  

3. **Step-by-Step Diagnostics (with commands + expected output)**  

4. **Recommended Fix (based on evidence)**  

5. **Fallback / Alternatives**  

6. **Command Summary**  

7. **Sources Used (from RAG context)**

Make the tone professional, concise, and engineer-friendly.

CRITICAL: You MUST complete your entire response. Do not stop mid-sentence or cut off your answer. Ensure all sections are fully written out, especially the "Recommended Fix", "Fallback / Alternatives", "Command Summary", and "Sources Used" sections.

========================

RAG CONTEXT:

{context_text}{history_context}

========================

Now answer the user query below, following all rules above. Remember to complete ALL sections fully.

User Query: {question}"""
    
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
        
        # Check if response seems incomplete (ends mid-sentence or missing expected sections)
        if answer:
            # Check for incomplete responses: ends without punctuation or ends mid-word
            last_char = answer[-1] if answer else ""
            ends_with_punctuation = last_char in '.!?'
            # Check if response mentions sections that should be present
            expected_sections = ["Recommended Fix", "Fallback", "Command Summary", "Sources Used"]
            has_expected_sections = any(section.lower() in answer.lower() for section in expected_sections)
            
            # If response is long but doesn't end properly, it might be incomplete
            if len(answer) > 500 and not ends_with_punctuation and has_expected_sections:
                logger.warning(f"Response may be incomplete (length: {len(answer)}, ends with: '{last_char}')")
    except Exception as e:
        logger.error(f"Model generation failed: {e}")
        from app.core.error_messages import GENERATION_SERVICE_UNAVAILABLE
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=GENERATION_SERVICE_UNAVAILABLE
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
    
    # Cache lowercased question for performance (used multiple times)
    question_lower = question.lower().strip()
    
    # Check if question is about the conversation itself
    is_about_conversation = any(keyword in question_lower for keyword in [
        'first question', 'first message', 'earlier', 'previous', 'before', 
        'what did i ask', 'what did you say', 'conversation', 'chat history',
        'earlier in', 'mentioned', 'discussed', 'talked about'
    ])
    
    # Format conversation history - include all if question is about the conversation
    history_text = format_conversation_history(conversation_history, include_all=is_about_conversation)
    
    if history_text:
        # Check if it's a conversational question
        conversational_keywords = [
            'what time', 'what is the time', 'current time', 'time now',
            'what date', 'what day', 'today', 'weather', 'how are you',
            'who are you', 'what can you do', 'your name', 'tell me about yourself'
        ]
        is_conversational = any(keyword in question_lower for keyword in conversational_keywords)
        
        if is_conversational:
            prompt = f"""You are Supportron, an AI assistant specialized in Linux server configuration, hosting support, and system administration.

Conversation History:
{history_text}

Current Question: {question}

IMPORTANT INSTRUCTIONS:
1. If asked about current time/date: You are an AI without real-time access. Politely explain that you don't have access to the current time, but you can help them check the time on their system using commands if they need.
2. If asked about yourself: Briefly introduce yourself as Supportron, an AI assistant for technical support, and mention you can help with Linux, server configuration, and system administration.
3. GENERAL RULE: For non-technical conversational questions, respond naturally and briefly. Do NOT provide technical commands unless the user explicitly asks for them.
4. OUT-OF-DOMAIN: If the question is completely unrelated to technical support, politely redirect to your technical support capabilities.
5. USE HISTORY CAREFULLY: Only reference conversation history if it's actually relevant to the current question.

Respond naturally and appropriately:"""
        else:
            prompt = f"""You are "Supportron", an advanced open-source technical support agent specialized in hosting, Linux servers, email delivery, DNS, web stacks, WHM/cPanel, WHMCS, network issues, logs, authentication failures, version upgrade failures, and general sysadmin troubleshooting.

Your job is to:

1. Analyze the user's issue like a senior technical engineer.

2. Infer the most likely root causes.

3. Use ONLY information from conversation history or standard best practices (no RAG context available).

4. Produce a clear, deterministic, step-by-step troubleshooting and resolution plan.

========================
    CORE BEHAVIOR
========================

When responding:

- FIRST: Restate the problem in 1–2 sentences so the user knows you understood it.

- THEN: Provide a ranked list of 2–5 **probable root causes**, with reasoning.

- THEN: Provide a **step-by-step diagnostic workflow** that is:

    • Ordered from safest → deepest  

    • Commands included (Linux, MySQL, mail logs, DNS checks, etc.)  

    • Explains WHY each step is done and what output to expect  

- THEN: Provide the **final recommended fix**, based on standard best practices.

- THEN: Provide **fallback / alternative solutions** if the main fix fails.

- THEN: Provide a **short, clean summary** of the exact commands and configuration paths used.

CRITICAL: You MUST complete your entire response. Do not stop mid-sentence or cut off your answer. Ensure all sections are fully written out, especially the "Recommended Fix", "Fallback / Alternatives", and "Command Summary" sections.

========================
     STRICT RULES
========================

1. **Use standard best practices and conversation history only.**

   - If something isn't in the conversation history, say "Based on standard Linux/cPanel/hosting best practices, a common cause is…"

   - Be explicit when information is not available.

2. **No hallucination.**

   - Do not invent commands, configs, service names, or paths that aren't standard.

   - If multiple interpretations exist, list them clearly.

3. **Safety rules**

   - Any potentially destructive step (deleting files, restarting main services, altering configs) MUST be marked with:

        [CAUTION] — Explain impact before giving the command.

   - Never produce irreversible commands unless absolutely necessary.

4. **Command formatting**

   - Use fenced code blocks.

   - Make commands copy-paste ready.

   - Prefer non-destructive checks first:

       cat, grep, tail, systemctl status, journalctl, dig, curl, netstat, telnet, openssl, df -h, ping, traceroute.

5. **Be explicit.**

   - Provide full file paths (e.g., /var/log/maillog, /etc/exim/exim.conf, /usr/local/cpanel/logs/error_log).

   - Provide DNS record examples.

   - Provide SMTP debugging steps.

   - Provide WHM/cPanel menu paths when relevant.

6. **Do not reference tools outside the open-source ecosystem.**

   - No proprietary APIs.

   - No SaaS-based scanning tools.

   - You may use or recommend ONLY open-source commands, methods, and best practices.

========================
  FINAL OUTPUT FORMAT
========================

Your response MUST follow this structure exactly:

1. **Understanding of Issue**  

2. **Probable Root Causes (ranked, with reasoning)**  

3. **Step-by-Step Diagnostics (with commands + expected output)**  

4. **Recommended Fix (based on best practices)**  

5. **Fallback / Alternatives**  

6. **Command Summary**  

Make the tone professional, concise, and engineer-friendly.

CRITICAL: You MUST complete your entire response. Do not stop mid-sentence or cut off your answer. Ensure all sections are fully written out, especially the "Recommended Fix", "Fallback / Alternatives", and "Command Summary" sections.

========================

CONVERSATION HISTORY:

{history_text}

========================

Now answer the user query below, following all rules above. Remember to complete ALL sections fully.

User Query: {question}"""
    else:
        # Check if it's a simple greeting or conversational question
        question_lower = question.lower().strip()
        is_greeting = question_lower in ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        
        # Check for conversational/non-technical questions
        conversational_keywords = [
            'what time', 'what is the time', 'current time', 'time now',
            'what date', 'what day', 'today', 'weather', 'how are you',
            'who are you', 'what can you do', 'your name', 'tell me about yourself'
        ]
        is_conversational = any(keyword in question_lower for keyword in conversational_keywords)
        
        if is_greeting:
            prompt = f"""You are Supportron, a friendly AI assistant for Linux server configuration, hosting support, and system administration.

The user just said: "{question}"

Respond with a friendly greeting and ask how you can help them. Keep it brief and welcoming. Do NOT provide troubleshooting steps or assume any problems."""
        elif is_conversational:
            prompt = f"""You are Supportron, an AI assistant specialized in Linux server configuration, hosting support, and system administration.

The user asked: "{question}"

IMPORTANT INSTRUCTIONS:
1. If asked about current time/date: You are an AI without real-time access. Politely explain that you don't have access to the current time, but you can help them check the time on their system using commands if they need.
2. If asked about yourself: Briefly introduce yourself as Supportron, an AI assistant for technical support, and mention you can help with Linux, server configuration, and system administration.
3. GENERAL RULE: For non-technical conversational questions, respond naturally and briefly. Do NOT provide technical commands unless the user explicitly asks for them.
4. OUT-OF-DOMAIN: If the question is completely unrelated to technical support (like weather, general knowledge, etc.), politely redirect to your technical support capabilities.

Respond naturally and appropriately:"""
        else:
            prompt = f"""You are "Supportron", an advanced open-source technical support agent specialized in hosting, Linux servers, email delivery, DNS, web stacks, WHM/cPanel, WHMCS, network issues, logs, authentication failures, version upgrade failures, and general sysadmin troubleshooting.

Your job is to:

1. Analyze the user's issue like a senior technical engineer.

2. Infer the most likely root causes.

3. Use standard Linux/cPanel/hosting best practices (no RAG context or conversation history available).

4. Produce a clear, deterministic, step-by-step troubleshooting and resolution plan.

========================
    CORE BEHAVIOR
========================

When responding:

- FIRST: Restate the problem in 1–2 sentences so the user knows you understood it.

- THEN: Provide a ranked list of 2–5 **probable root causes**, with reasoning.

- THEN: Provide a **step-by-step diagnostic workflow** that is:

    • Ordered from safest → deepest  

    • Commands included (Linux, MySQL, mail logs, DNS checks, etc.)  

    • Explains WHY each step is done and what output to expect  

- THEN: Provide the **final recommended fix**, based on standard best practices.

- THEN: Provide **fallback / alternative solutions** if the main fix fails.

- THEN: Provide a **short, clean summary** of the exact commands and configuration paths used.

========================
     STRICT RULES
========================

1. **Use standard best practices only.**

   - Say "Based on standard Linux/cPanel/hosting best practices, a common cause is…"

   - Be explicit when information is not available.

2. **No hallucination.**

   - Do not invent commands, configs, service names, or paths that aren't standard.

   - If multiple interpretations exist, list them clearly.

3. **Safety rules**

   - Any potentially destructive step (deleting files, restarting main services, altering configs) MUST be marked with:

        [CAUTION] — Explain impact before giving the command.

   - Never produce irreversible commands unless absolutely necessary.

4. **Command formatting**

   - Use fenced code blocks.

   - Make commands copy-paste ready.

   - Prefer non-destructive checks first:

       cat, grep, tail, systemctl status, journalctl, dig, curl, netstat, telnet, openssl, df -h, ping, traceroute.

5. **Be explicit.**

   - Provide full file paths (e.g., /var/log/maillog, /etc/exim/exim.conf, /usr/local/cpanel/logs/error_log).

   - Provide DNS record examples.

   - Provide SMTP debugging steps.

   - Provide WHM/cPanel menu paths when relevant.

6. **Do not reference tools outside the open-source ecosystem.**

   - No proprietary APIs.

   - No SaaS-based scanning tools.

   - You may use or recommend ONLY open-source commands, methods, and best practices.

========================
  FINAL OUTPUT FORMAT
========================

Your response MUST follow this structure exactly:

1. **Understanding of Issue**  

2. **Probable Root Causes (ranked, with reasoning)**  

3. **Step-by-Step Diagnostics (with commands + expected output)**  

4. **Recommended Fix (based on best practices)**  

5. **Fallback / Alternatives**  

6. **Command Summary**  

Make the tone professional, concise, and engineer-friendly.

CRITICAL: You MUST complete your entire response. Do not stop mid-sentence or cut off your answer. Ensure all sections are fully written out, especially the "Recommended Fix", "Fallback / Alternatives", and "Command Summary" sections.

========================

Now answer the user query below, following all rules above. Remember to complete ALL sections fully.

User Query: {question}"""
    
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
        
        # Check if response seems incomplete
        if answer:
            last_char = answer[-1] if answer else ""
            ends_with_punctuation = last_char in '.!?'
            expected_sections = ["Recommended Fix", "Fallback", "Command Summary"]
            has_expected_sections = any(section.lower() in answer.lower() for section in expected_sections)
            
            if len(answer) > 500 and not ends_with_punctuation and has_expected_sections:
                logger.warning(f"Response may be incomplete (length: {len(answer)}, ends with: '{last_char}')")
        
        return answer
    except Exception as e:
        logger.error(f"Model generation failed: {e}")
        from app.core.error_messages import GENERATION_SERVICE_UNAVAILABLE
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=GENERATION_SERVICE_UNAVAILABLE
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
            from app.core.error_messages import COULD_NOT_GENERATE_RESPONSE
            answer = COULD_NOT_GENERATE_RESPONSE
        
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
        from app.core.error_messages import OLLAMA_SERVICE_UNAVAILABLE, UNEXPECTED_ERROR_PROCESSING_QUESTION
        error_msg = str(e).lower()
        if "connection" in error_msg or "refused" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=OLLAMA_SERVICE_UNAVAILABLE
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=UNEXPECTED_ERROR_PROCESSING_QUESTION
        )

