from typing import List
from domain.interfaces import IAIProvider, IVectorStore
from services.embedding_service import EmbeddingStrategyService
from core.logger import logger

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
        answer = await self.ai_provider.generate_completion(messages)
        return answer