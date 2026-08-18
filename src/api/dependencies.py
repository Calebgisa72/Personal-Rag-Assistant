from functools import lru_cache
from fastapi import Depends

from infrastructure.ai.amali_provider import AmaliAIProvider
from infrastructure.vector_store.chroma_adapter import ChromaDBVectorStore
from services.embedding_service import EmbeddingStrategyService
from services.rag_service import RAGService
from infrastructure.document.chunking import ChunkingService

# ==============================================================================
# 1. Core Clients (Application-scoped singletons)
# We use @lru_cache here because initializing these providers can be "heavy" 
# (e.g., opening network connection pools, loading heavy client libraries).
# Caching them ensures we reuse the same instance across all API requests.
# ==============================================================================

@lru_cache(maxsize=1)
def get_ai_provider():
    return AmaliAIProvider()

@lru_cache(maxsize=1)
def get_vector_store():
    return ChromaDBVectorStore()

# ==============================================================================
# 2. Application Services (Instantiated per-request)
# We do NOT use @lru_cache here. Instantiating these classes is extremely cheap
# (just variable assignment). FastAPI will pass the cached singleton clients 
# into these services automatically.
# ==============================================================================

def get_embedding_service(ai_provider = Depends(get_ai_provider)):
    return EmbeddingStrategyService(ai_provider=ai_provider)

def get_chunking_service():
    """Currently available in the app, used for document processing."""
    return ChunkingService()

def get_rag_service(
    embedding_service = Depends(get_embedding_service),
    ai_provider = Depends(get_ai_provider),
    vector_store = Depends(get_vector_store)
):
    return RAGService(embedding_service, ai_provider, vector_store)

# ==============================================================================
# 3. Future Roadmap Dependencies (Stubs)
# These are place-holders based on the project_roadmap.md. You can implement
# them as you progress through the branches.
# ==============================================================================

# def get_db_session():
#     """Provides an async SQLAlchemy database session."""
#     # yield session
#     pass

# def get_document_repository(session = Depends(get_db_session)):
#     """Handles database operations for document metadata."""
#     # return DocumentRepository(session)
#     pass

# def get_conversation_repository(session = Depends(get_db_session)):
#     """Handles saving and retrieving chat history."""
#     # return ConversationRepository(session)
#     pass

# def get_current_user(token: str = Depends(oauth2_scheme)):
#     \"\"\"Authenticates the user via JWT and returns the User entity.\"\"\"
#     # return user
#     pass

from persistence.uow import UnitOfWork

async def get_uow():
    async with UnitOfWork() as uow:
        yield uow
