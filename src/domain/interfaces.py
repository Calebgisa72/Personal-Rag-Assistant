from domain.entities import DocumentChunk
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class IAIProvider(ABC):
    @abstractmethod
    async def generate_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        pass

    @abstractmethod
    async def generate_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        pass

class IVectorStore(ABC):
    @abstractmethod
    async def upsert(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        pass

    @abstractmethod
    async def similarity_search(self, query_embedding: List[float], k: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        pass

class ICache(ABC):
    @abstractmethod
    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        pass

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    async def clear(self) -> bool:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass

class IRepository(ABC):
    pass