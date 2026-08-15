from core.exceptions import CacheError
import redis.asyncio as redis

from domain.interfaces import ICache

class Cache(ICache):
    def __init__(self, client: redis.Redis):
        self.client = client

    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        try:
            return await self.client.set(key, value, ex=ttl)
        except redis.exceptions.RedisError as e:
            raise CacheError("Failed to set in cache.") from e

    async def get(self, key: str) -> str | None:
        try:
            return await self.client.get(key)
        except redis.exceptions.RedisError as e:
            raise CacheError("Failed to get from cache.") from e

    async def delete(self, key: str) -> bool:
        try:
            return await self.client.delete(key)
        except redis.exceptions.RedisError as e:
            raise CacheError("Failed to delete from cache.") from e

    async def clear(self) -> bool:
        try:
            return await self.client.flushdb()
        except redis.exceptions.RedisError as e:
            raise CacheError("Failed to clear cache.") from e

    async def exists(self, key: str) -> bool:
        try:
            return await self.client.exists(key)
        except redis.exceptions.RedisError as e:
            raise CacheError("Failed to check existence in cache.") from e
