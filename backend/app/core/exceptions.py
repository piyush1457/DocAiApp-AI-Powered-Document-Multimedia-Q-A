"""
Custom exceptions for the DocAiApp backend.
"""


class DocAiError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self, message: str, code: str = "INTERNAL_ERROR", details: dict = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class IngestionError(DocAiError):
    """Raised when file ingestion fails."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="INGESTION_ERROR", details=details)


class TranscriptionError(DocAiError):
    """Raised when audio/video transcription fails."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="TRANSCRIPTION_ERROR", details=details)


class LLMError(DocAiError):
    """Raised when there is an error with LLM operations (OpenAI)."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="LLM_ERROR", details=details)


class VectorStoreError(DocAiError):
    """Raised when vector store operations fail."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="VECTOR_STORE_ERROR", details=details)
