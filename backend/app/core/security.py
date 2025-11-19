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
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")
    
    # Sanitize: remove excessive whitespace and limit length
    sanitized = question.strip()
    
    # Remove control characters except newlines and tabs
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\t')
    
    # Limit length to prevent DoS
    if len(sanitized) > 5000:
        raise ValueError("Question is too long. Maximum length is 5000 characters.")
    
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

