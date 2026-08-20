import redis.asyncio as redis
from core.config import settings


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
