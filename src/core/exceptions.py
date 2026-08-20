from typing import Any


class BaseAppError(Exception):
    default_message: str = "An internal error occurred."

    def __init__(
        self, message: str | None = None, *, detail: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message or self.default_message)
        self.detail: dict[str, Any] = detail or {}


class ValidationError(BaseAppError):
    default_message = "Invalid input data."


class InvalidRequestError(BaseAppError):
    default_message = "Invalid request parameters."


class AuthenticationError(BaseAppError):
    default_message = "Authentication failed or missing credentials."


class AuthorizationError(BaseAppError):
    default_message = "You do not have permission to perform this action."


class NotFoundError(BaseAppError):
    default_message = "Resource not found."


class DatabaseError(BaseAppError):
    default_message = "A database error occurred."


class RateLimitExceededError(BaseAppError):
    default_message = "Rate limit exceeded. Slow down."


class RAGPipelineError(BaseAppError):
    default_message = "Internal RAG pipeline error."


class AIProviderError(BaseAppError):
    default_message = "AI provider request failed."


class ProviderUnavailableError(AIProviderError):
    default_message = "AI provider is unavailable."


class DocumentProcessingError(BaseAppError):
    default_message = "Error processing document."


class VectorStoreError(BaseAppError):
    default_message = "Vector store error."


class CacheError(BaseAppError):
    default_message = "Cache operation failed."
