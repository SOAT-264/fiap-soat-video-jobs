"""Cache adapters."""
from job_service.infrastructure.adapters.output.cache.redis_client import get_redis, close_redis

__all__ = ["get_redis", "close_redis"]
