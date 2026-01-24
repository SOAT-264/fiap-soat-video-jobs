"""Redis client for caching."""
from typing import Optional
from redis.asyncio import Redis, from_url

from job_service.infrastructure.config import get_settings

settings = get_settings()

_redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    """Get Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
