from unittest.mock import AsyncMock

import pytest

from job_service.infrastructure.adapters.output.cache import redis_client


@pytest.mark.asyncio
async def test_get_redis_creates_singleton(monkeypatch):
    fake = AsyncMock()
    redis_client._redis_client = None
    monkeypatch.setattr(redis_client, "from_url", lambda *args, **kwargs: fake)

    one = await redis_client.get_redis()
    two = await redis_client.get_redis()

    assert one is fake
    assert two is fake


@pytest.mark.asyncio
async def test_close_redis_closes_and_resets():
    fake = AsyncMock()
    redis_client._redis_client = fake

    await redis_client.close_redis()

    fake.close.assert_awaited_once()
    assert redis_client._redis_client is None
