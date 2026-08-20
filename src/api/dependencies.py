from functools import lru_cache
from fastapi import Depends
import uuid

from infrastructure.ai.amali_provider import AmaliAIProvider
from infrastructure.vector_store.chroma_adapter import ChromaDBVectorStore
from services.embedding_service import EmbeddingStrategyService
from services.rag_service import RAGService
from infrastructure.document.chunking import ChunkingService
from services.storage_service import StorageService
from services.url_scraper_service import URLScraperService
from services.document_service import DocumentService
from persistence.uow import UnitOfWork

# ==============================================================================
# 1. Core Clients (Application-scoped singletons)
# ==============================================================================


@lru_cache(maxsize=1)
def get_ai_provider():
    return AmaliAIProvider()


@lru_cache(maxsize=1)
def get_vector_store():
    return ChromaDBVectorStore()


# ==============================================================================
# 2. Application Services (Instantiated per-request)
# ==============================================================================


def get_embedding_service(ai_provider=Depends(get_ai_provider)):
    return EmbeddingStrategyService(ai_provider=ai_provider)


def get_chunking_service():
    """Currently available in the app, used for document processing."""
    return ChunkingService()


async def get_uow():
    async with UnitOfWork() as uow:
        yield uow


def get_rag_service(
    embedding_service=Depends(get_embedding_service),
    ai_provider=Depends(get_ai_provider),
    vector_store=Depends(get_vector_store),
    uow=Depends(get_uow),
):
    return RAGService(embedding_service, ai_provider, vector_store, uow)


def get_storage_service():
    return StorageService()


def get_url_scraper_service():
    return URLScraperService()


def get_document_service(
    uow=Depends(get_uow),
    storage_service=Depends(get_storage_service),
    url_scraper_service=Depends(get_url_scraper_service),
    vector_store=Depends(get_vector_store),
):
    return DocumentService(uow, storage_service, url_scraper_service, vector_store)


# ==============================================================================
# 3. Future Roadmap Dependencies (Stubs)
# ==============================================================================


def get_current_user() -> uuid.UUID:
    """Mock user dependency until proper auth is implemented."""
    return uuid.UUID(int=1)
