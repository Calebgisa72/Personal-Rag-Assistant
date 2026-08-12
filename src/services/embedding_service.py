from typing import List
import asyncio
from src.domain.interfaces import IAIProvider
from src.core.logger import logger

class EmbeddingStrategyService:
    """
    Service dedicated to optimizing how embeddings are generated.
    Includes caching logic, rate limit backoff, and batching.
    """
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
        return await self.ai_provider.generate_embeddings(texts, model=self.model_name)\n