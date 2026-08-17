from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from domain.entities import DocumentChunk

class IVectorStore(ABC):
    @abstractmethod
    async def upsert(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        pass

    @abstractmethod
    async def similarity_search(self, query_embedding: List[float], k: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        pass
