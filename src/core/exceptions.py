from typing import Any, Dict, Optional

class BaseAppException(Exception):
    def __init__(self, message: str, code: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

class RAGPipelineException(BaseAppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "RAG_PIPELINE_ERROR", details)

class AIProviderException(BaseAppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AI_PROVIDER_ERROR", details)

class DocumentProcessingException(BaseAppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DOCUMENT_PROCESSING_ERROR", details)\n