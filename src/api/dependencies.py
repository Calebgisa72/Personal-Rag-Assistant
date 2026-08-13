from fastapi import Depends

from infrastructure.ai.amali_provider import AmaliAIProvider
from infrastructure.vector_store.chroma_adapter import ChromaDBVectorStore
from services.embedding_service import EmbeddingStrategyService
from services.rag_service import RAGService


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