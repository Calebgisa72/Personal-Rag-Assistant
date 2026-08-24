from functools import lru_cache
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import uuid

from infrastructure.ai.amali_provider import AmaliAIProvider
from infrastructure.vector_store.chroma_adapter import ChromaDBVectorStore
from services.embedding_service import EmbeddingStrategyService
from services.rag_service import RAGService
from infrastructure.document.chunking import ChunkingService
from services.storage_service import StorageService
from services.url_scraper_service import URLScraperService
from services.document_service import DocumentService
from services.conversation_service import ConversationService
from services.admin_service import AdminService
from services.auth_service import AuthService
from persistence.uow import UnitOfWork
from core.config import settings

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


def get_conversation_service(uow=Depends(get_uow)):
    return ConversationService(uow)


def get_auth_service(uow=Depends(get_uow)):
    return AuthService(uow)

# ==============================================================================
# 3. Auth & RBAC Dependencies
# ==============================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user_entity(
    token: str = Depends(oauth2_scheme),
    uow: UnitOfWork = Depends(get_uow)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_id = uuid.UUID(user_id_str)
    user = await uow.users.get_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user(current_user = Depends(get_current_user_entity)) -> uuid.UUID:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user.user_id


async def get_current_superuser(current_user = Depends(get_current_user_entity)) -> uuid.UUID:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
        )
    return current_user.user_id
