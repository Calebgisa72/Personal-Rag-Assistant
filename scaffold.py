import os
import textwrap

BASE_DIR = r"c:\Users\user\Desktop\Backend PRO\RAG systems\Personal-Rag-Assistant"

FILES = {
    "requirements.txt": """
fastapi==0.111.0
uvicorn==0.30.1
pydantic==2.7.4
pydantic-settings==2.3.4
sqlalchemy==2.0.30
asyncpg==0.29.0
alembic==1.13.1
redis==5.0.6
httpx==0.27.0
structlog==24.2.0
langchain==0.2.5
langchain-community==0.2.5
sentence-transformers==3.0.1
chromadb==0.5.3
pytest==8.2.2
pytest-asyncio==0.23.7
    """,
    "pyproject.toml": """
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "rag-saas-platform"
version = "0.1.0"
description = "Enterprise AI-powered Retrieval-Augmented Generation (RAG) SaaS platform"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn>=0.30.1",
    "pydantic>=2.7.4",
    "pydantic-settings>=2.3.4",
    "sqlalchemy>=2.0.30",
    "asyncpg>=0.29.0",
    "alembic>=1.13.1",
    "redis>=5.0.6",
    "httpx>=0.27.0",
    "structlog>=24.2.0",
    "langchain>=0.2.5",
    "langchain-community>=0.2.5",
    "sentence-transformers>=3.0.1",
    "chromadb>=0.5.3",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.2",
    "pytest-asyncio>=0.23.7",
    "black",
    "isort",
    "mypy"
]
    """,
    "src/__init__.py": "",
    "src/core/__init__.py": "",
    "src/core/config.py": """
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "RAG SaaS Platform"
    VERSION: str = "0.1.0"
    
    # Environment
    ENV: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_db"
    
    # Redis Cache & Rate Limiting
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Vector Store
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"
    
    # AI Provider (Amali AI)
    AMALI_API_URL: str = "https://ai-api.amalitech.org/api/v2/public/v1"
    AMALI_API_KEY: str = "dummy_key"
    AMALI_PROVIDER_NAME: str = "openai"  # or anthropic
    
    # Embedding config
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Chunking config
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
    """,
    "src/core/exceptions.py": """
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
        super().__init__(message, "DOCUMENT_PROCESSING_ERROR", details)
    """,
    "src/core/logger.py": """
import structlog
import logging

def setup_logger():
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=logging.INFO)

logger = structlog.get_logger()
    """,
    "src/core/middleware.py": """
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.core.logger import logger

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        # Attach request id to context or request state
        request.state.request_id = request_id
        
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            "request_completed",
            method=request.method,
            url=str(request.url),
            request_id=request_id,
            process_time_ms=round(process_time * 1000, 2),
            status_code=response.status_code
        )
        response.headers["X-Request-ID"] = request_id
        return response
    """,
    "src/domain/__init__.py": "",
    "src/domain/entities.py": """
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

@dataclass
class DocumentChunk:
    content: str
    document_id: uuid.UUID
    chunk_index: int
    metadata: Dict[str, Any]
    chunk_id: uuid.UUID = field(default_factory=uuid.uuid4)
    page_number: Optional[int] = None
    source: Optional[str] = None

@dataclass
class DocumentEntity:
    title: str
    content: str
    mime_type: str
    document_id: uuid.UUID = field(default_factory=uuid.uuid4)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class MessageEntity:
    role: str
    content: str
    message_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ConversationEntity:
    user_id: uuid.UUID
    conversation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    messages: List[MessageEntity] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    """,
    "src/domain/interfaces.py": """
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.domain.entities import DocumentChunk, ConversationEntity, MessageEntity

class IAIProvider(ABC):
    @abstractmethod
    async def generate_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        pass

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        pass

class IVectorStore(ABC):
    @abstractmethod
    async def upsert(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        pass

    @abstractmethod
    async def similarity_search(self, query_embedding: List[float], k: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        pass

class IRepository(ABC):
    pass
    """,
    "src/infrastructure/__init__.py": "",
    "src/infrastructure/ai/amali_provider.py": """
import httpx
import asyncio
from typing import List, Dict, Any
from src.domain.interfaces import IAIProvider
from src.core.config import settings
from src.core.exceptions import AIProviderException
from src.core.logger import logger

class AmaliAIProvider(IAIProvider):
    def __init__(self):
        self.base_url = settings.AMALI_API_URL
        self.api_key = settings.AMALI_API_KEY
        self.provider = settings.AMALI_PROVIDER_NAME
        
        # We do NOT use 'Authorization: Bearer <token>'
        self.headers = {
            "X-Api-Key": self.api_key,
            "Provider": self.provider,
            "Content-Type": "application/json"
        }
        
    async def _make_request(self, method: str, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{self.base_url}{endpoint}"
            try:
                response = await client.request(method, url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error("amali_api_status_error", status_code=e.response.status_code, response=e.response.text)
                raise AIProviderException(f"API Error: {e.response.status_code}", details={"response": e.response.text})
            except httpx.RequestError as e:
                logger.error("amali_api_request_error", error=str(e))
                raise AIProviderException(f"Request failed: {str(e)}")

    async def generate_completion(self, messages: List[Dict[str, str]], model: str = "gpt-4o-mini", **kwargs) -> str:
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        res = await self._make_request("POST", "/chat/completions", payload)
        try:
            return res["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise AIProviderException("Unexpected response format from Chat Completions", details={"raw": res})

    async def _generate_single_embedding(self, text: str, model: str) -> List[float]:
        payload = {
            "input": text,
            "model": model
        }
        res = await self._make_request("POST", "/embeddings", payload)
        try:
            return res["data"][0]["embedding"]
        except (KeyError, IndexError) as e:
            raise AIProviderException("Unexpected response format from Embeddings", details={"raw": res})

    async def generate_embeddings(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        # The gateway may support single-string inputs only.
        # We embed them concurrently and use asyncio.gather to preserve original order.
        tasks = [self._generate_single_embedding(text, model) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        final_embeddings = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error("embedding_generation_failed_for_chunk", index=i, error=str(res))
                raise res
            final_embeddings.append(res)
            
        return final_embeddings
    """,
    "src/infrastructure/vector_store/chroma_adapter.py": """
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from src.domain.interfaces import IVectorStore
from src.domain.entities import DocumentChunk
from src.core.config import settings

class ChromaDBVectorStore(IVectorStore):
    def __init__(self, collection_name: str = "rag_collection"):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(name=collection_name)

    async def upsert(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        ids = [str(chunk.chunk_id) for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = []
        for chunk in chunks:
            # Flatten metadata to string/int/float for Chroma
            meta = chunk.metadata.copy()
            meta["document_id"] = str(chunk.document_id)
            meta["chunk_index"] = chunk.chunk_index
            if chunk.page_number is not None:
                meta["page_number"] = chunk.page_number
            if chunk.source:
                meta["source"] = chunk.source
            metadatas.append(meta)

        # Chroma doesn't natively support async yet, but we wrap it in a pseudo-async interface
        # for architectural consistency. Real implementations could offload this to a threadpool.
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    async def similarity_search(self, query_embedding: List[float], k: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_dict
        )
        
        chunks = []
        if not results["ids"] or not results["ids"][0]:
            return chunks
            
        for i in range(len(results["ids"][0])):
            chunk_id_str = results["ids"][0][i]
            content = results["documents"][0][i]
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            
            import uuid
            chunk = DocumentChunk(
                chunk_id=uuid.UUID(chunk_id_str),
                content=content,
                document_id=uuid.UUID(meta.get("document_id", str(uuid.uuid4()))),
                chunk_index=meta.get("chunk_index", 0),
                page_number=meta.get("page_number"),
                source=meta.get("source"),
                metadata=meta
            )
            chunks.append(chunk)
            
        return chunks
    """,
    "src/infrastructure/cache/redis_client.py": """
import redis.asyncio as redis
from src.core.config import settings

class RedisClientManager:
    _pool = None

    @classmethod
    def get_pool(cls):
        if cls._pool is None:
            cls._pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL, decode_responses=True
            )
        return cls._pool

    @classmethod
    def get_client(cls):
        return redis.Redis(connection_pool=cls.get_pool())

async def get_redis_client():
    client = RedisClientManager.get_client()
    try:
        yield client
    finally:
        await client.aclose()
    """,
    "src/infrastructure/document/chunking.py": """
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Any, Optional
from src.domain.entities import DocumentEntity, DocumentChunk
from src.core.config import settings

class ChunkingService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\\n\\n", "\\n", ". ", " ", ""]
        )

    def chunk_document(self, document: DocumentEntity) -> List[DocumentChunk]:
        # Using LangChain to split
        texts = self.text_splitter.split_text(document.content)
        
        chunks = []
        for index, text in enumerate(texts):
            chunk = DocumentChunk(
                content=text,
                document_id=document.document_id,
                chunk_index=index,
                metadata={
                    "title": document.title,
                    "mime_type": document.mime_type,
                    **document.metadata
                },
                source=document.metadata.get("source", "unknown"),
                page_number=document.metadata.get("page_number", None)
            )
            chunks.append(chunk)
        return chunks
    """,
    "src/services/__init__.py": "",
    "src/services/embedding_service.py": """
from typing import List
import asyncio
from src.domain.interfaces import IAIProvider
from src.core.logger import logger

class EmbeddingStrategyService:
    \"\"\"
    Service dedicated to optimizing how embeddings are generated.
    Includes caching logic, rate limit backoff, and batching.
    \"\"\"
    def __init__(self, ai_provider: IAIProvider, redis_client=None):
        self.ai_provider = ai_provider
        self.redis_client = redis_client
        self.model_name = "text-embedding-3-small"

    async def get_embedding(self, text: str) -> List[float]:
        # Placeholder for caching logic:
        # cache_key = f"emb:{hash(text)}"
        # if cached := await self.redis_client.get(cache_key): return cached
        
        embeddings = await self.ai_provider.generate_embeddings([text], model=self.model_name)
        return embeddings[0]
        
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        # This calls the AmaliProvider which already handles concurrency.
        # But we could wrap this to enforce specific batch sizes (e.g. 50 at a time)
        # to respect rate limits.
        logger.info("embedding_batch_requested", num_texts=len(texts))
        return await self.ai_provider.generate_embeddings(texts, model=self.model_name)
    """,
    "src/services/rag_service.py": """
from typing import List
from src.domain.interfaces import IAIProvider, IVectorStore
from src.services.embedding_service import EmbeddingStrategyService
from src.core.logger import logger

class RAGService:
    def __init__(self, embedding_service: EmbeddingStrategyService, ai_provider: IAIProvider, vector_store: IVectorStore):
        self.embedding_service = embedding_service
        self.ai_provider = ai_provider
        self.vector_store = vector_store

    async def ask_question(self, question: str) -> str:
        # 1. Embed question
        query_embedding = await self.embedding_service.get_embedding(question)
        
        # 2. Retrieve context
        chunks = await self.vector_store.similarity_search(query_embedding, k=5)
        
        context_text = "\\n\\n---\\n\\n".join([c.content for c in chunks])
        
        # 3. Formulate Prompt
        system_prompt = (
            "You are a helpful AI assistant. Use the following pieces of retrieved context to answer the question. "
            "If you don't know the answer, just say that you don't know.\\n\\n"
            f"Context: {context_text}"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        # 4. Generate Answer
        logger.info("generating_rag_answer", num_chunks_retrieved=len(chunks))
        answer = await self.ai_provider.generate_completion(messages)
        return answer
    """,
    "src/services/cost_service.py": """
class CostService:
    \"\"\"
    Tracks tokens and calculates estimated costs based on provider pricing.
    \"\"\"
    
    # Example rates per 1k tokens
    PRICING = {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
    }

    def __init__(self):
        pass

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = self.PRICING.get(model)
        if not pricing:
            return 0.0
            
        input_cost = (input_tokens / 1000.0) * pricing["input"]
        output_cost = (output_tokens / 1000.0) * pricing["output"]
        return input_cost + output_cost
    """,
    "src/persistence/__init__.py": "",
    "src/persistence/database.py": """
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from src.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
    """,
    "src/persistence/uow.py": """
from src.persistence.database import AsyncSessionLocal

class UnitOfWork:
    def __init__(self):
        self.session_factory = AsyncSessionLocal
        self.session = None

    async def __aenter__(self):
        self.session = self.session_factory()
        # Initialize repositories here, injecting self.session
        # self.users = UserRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, traceback):
        if exc_type is not None:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()
    """,
    "src/api/__init__.py": "",
    "src/api/dependencies.py": """
from fastapi import Depends
from src.infrastructure.ai.amali_provider import AmaliAIProvider
from src.infrastructure.vector_store.chroma_adapter import ChromaDBVectorStore
from src.services.embedding_service import EmbeddingStrategyService
from src.services.rag_service import RAGService

def get_ai_provider():
    return AmaliAIProvider()

def get_vector_store():
    return ChromaDBVectorStore()

def get_embedding_service(ai_provider = Depends(get_ai_provider)):
    return EmbeddingStrategyService(ai_provider=ai_provider)

def get_rag_service(
    embedding_service = Depends(get_embedding_service),
    ai_provider = Depends(get_ai_provider),
    vector_store = Depends(get_vector_store)
):
    return RAGService(embedding_service, ai_provider, vector_store)
    """,
    "src/api/routers/chat.py": """
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api.dependencies import get_rag_service
from src.services.rag_service import RAGService

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    question: str
    conversation_id: str = None

class ChatResponse(BaseModel):
    answer: str

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, rag_service: RAGService = Depends(get_rag_service)):
    answer = await rag_service.ask_question(request.question)
    return ChatResponse(answer=answer)
    """,
    "src/api/routers/system.py": """
from fastapi import APIRouter
from src.core.config import settings

router = APIRouter(tags=["System"])

@router.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}
    """,
    "src/api/main.py": """
from fastapi import FastAPI
from src.core.logger import setup_logger
from src.core.middleware import RequestIDMiddleware
from src.api.routers import chat, system

setup_logger()

app = FastAPI(
    title="RAG SaaS Platform API",
    description="Enterprise AI-powered Retrieval-Augmented Generation",
    version="0.1.0"
)

app.add_middleware(RequestIDMiddleware)

app.include_router(system.router)
app.include_router(chat.router)
    """
}

def create_files():
    for rel_path, content in FILES.items():
        full_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\\n")
    print("Scaffolding complete.")

if __name__ == "__main__":
    create_files()
