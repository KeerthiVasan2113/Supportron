"""
Security and input validation utilities.
"""

from pydantic import field_validator


def validate_question(question: str) -> str:
    """
    Validate and sanitize question input.
    
    Args:
        question: Input question string
        
    Returns:
        Sanitized question string
        
    Raises:
        ValueError: If question is empty or invalid
    """
    from app.core.error_messages import QUESTION_EMPTY
    if not question or not question.strip():
        raise ValueError(QUESTION_EMPTY)
    
    # Sanitize: remove excessive whitespace and limit length
    sanitized = question.strip()
    
    # Remove control characters except newlines and tabs
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\t')
    
    # Limit length to prevent DoS
    from app.core.error_messages import QUESTION_TOO_LONG
    if len(sanitized) > 5000:
        raise ValueError(QUESTION_TOO_LONG)
    
    return sanitized


def create_question_validator():
    """
    Create a Pydantic field validator for question fields.
    
    Returns:
        Field validator function
    """
    @field_validator('question')
    @classmethod
    def validate_question_field(cls, v: str) -> str:
        """Validate and sanitize question input."""
        return validate_question(v)
    
    return validate_question_field

