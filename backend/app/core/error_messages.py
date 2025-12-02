"""
Standardized error messages for the application.
All error messages should be defined here for consistency.
"""

# Service availability errors
OLLAMA_SERVICE_UNAVAILABLE = "Ollama service is not available. Please ensure Ollama is running and at least one model is installed."
GENERATION_SERVICE_UNAVAILABLE = "Generation service is temporarily unavailable. Please try again later."
MODEL_NOT_AVAILABLE = "No suitable model is available. Please ensure at least one model is installed."

# Validation errors
INVALID_IDENTIFIER = "Invalid identifier. Only alphanumeric characters, underscores, and hyphens are allowed."
IDENTIFIER_REQUIRED = "Identifier must be a non-empty string."
TABLE_NOT_FOUND = "Table '{table_name}' does not exist in database '{db_name}'."
COLUMN_NOT_FOUND = "Column(s) {columns} do not exist in table '{table_name}'. Available columns: {available_columns}."
VALUES_REQUIRED_FOR_CREATE = "Values are required for POST (CREATE) operations."
VALUES_REQUIRED_FOR_UPDATE = "Values are required for PUT (UPDATE) operations."
FILTERS_REQUIRED_FOR_UPDATE = "Filters are required for PUT (UPDATE) operations."
FILTERS_REQUIRED_FOR_DELETE = "Filters are required for DELETE operations."
INVALID_METHOD = "Unsupported method: {method}. Supported methods: GET, POST, PUT, DELETE."
QUESTION_EMPTY = "Question cannot be empty."
QUESTION_TOO_LONG = "Question is too long. Maximum length is 5000 characters."

# Database errors
DATABASE_OPERATION_FAILED = "Database operation failed: {error}"
TABLE_INFO_FAILED = "Failed to retrieve table information: {error}"
DATABASE_INTEGRITY_ERROR = "Database integrity error: {error}"
NO_VALID_COLUMNS = "No valid columns provided."
NO_VALID_COLUMNS_FOR_UPDATE = "No valid columns provided for update."
INVALID_LIMIT = "Limit must be a non-negative integer."
INVALID_OFFSET = "Offset must be a non-negative integer."

# General errors
UNEXPECTED_ERROR = "An unexpected error occurred. Please try again."
UNEXPECTED_ERROR_PROCESSING_QUESTION = "An unexpected error occurred while processing your question."
COULD_NOT_GENERATE_RESPONSE = "I apologize, but I couldn't generate a response. Please try again."

# Configuration errors
OLLAMA_MODEL_NOT_SET = "OLLAMA_MODEL environment variable must be set. See .env.example for configuration."
INVALID_RAG_MAX_DISTANCE = "RAG_MAX_DISTANCE must be between 0 and 1."
INVALID_RAG_TOP_DOCS = "RAG_TOP_DOCS must be at least 1."
INVALID_PORT = "PORT must be between 1 and 65535."

