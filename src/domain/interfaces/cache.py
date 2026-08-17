from abc import ABC, abstractmethod
from typing import Optional

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
