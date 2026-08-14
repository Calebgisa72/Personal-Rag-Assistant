from typing import List
from domain.interfaces import IAIProvider, IVectorStore
from services.embedding_service import EmbeddingStrategyService
from core.logger import logger
from core.exceptions import VectorStoreError, AIProviderError

class RAGService:
    def __init__(self, embedding_service: EmbeddingStrategyService, ai_provider: IAIProvider, vector_store: IVectorStore):
        self.embedding_service = embedding_service
        self.ai_provider = ai_provider
        self.vector_store = vector_store

    async def ask_question(self, question: str) -> str:
        # 1. Embed question
        query_embedding = await self.embedding_service.get_embedding(question)
        
        # 2. Retrieve context
        try:
            chunks = await self.vector_store.similarity_search(query_embedding, k=5)
        except Exception as e:
            logger.error("vector_store.search_failed", detail=str(e))
            raise VectorStoreError(f"Failed to retrieve context: {str(e)}")
        
        context_text = "\n\n---\n\n".join([c.content for c in chunks])
        
        # 3. Formulate Prompt
        system_prompt = (
            "You are a helpful AI assistant. Use the following pieces of retrieved context to answer the question. "
            "If you don't know the answer, just say that you don't know.\n\n"
            f"Context: {context_text}"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        # 4. Generate Answer
        logger.info("generating_rag_answer", num_chunks_retrieved=len(chunks))
        try:
            answer = await self.ai_provider.generate_completion(messages)
        except Exception as e:
            logger.error("ai_provider.completion_failed", detail=str(e))
            raise AIProviderError(f"Failed to generate answer: {str(e)}")
            
        return answer