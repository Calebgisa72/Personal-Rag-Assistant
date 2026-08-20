from abc import ABC, abstractmethod
from typing import List, Dict


class IAIProvider(ABC):
    @abstractmethod
    async def generate_completion(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        pass

    @abstractmethod
    async def generate_embeddings(
        self, texts: List[str], **kwargs
    ) -> List[List[float]]:
        pass
