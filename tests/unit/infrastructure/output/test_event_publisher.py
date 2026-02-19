import json
from unittest.mock import AsyncMock

import pytest

from job_service.infrastructure.adapters.output.messaging.event_publisher import EventPublisher


class DummyClientContext:
    def __init__(self, client):
        self._client = client

    async def __aenter__(self):
        return self._client

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummySession:
    def __init__(self, client):
        self._client = client

    def client(self, *_args, **_kwargs):
        return DummyClientContext(self._client)


@pytest.mark.asyncio
async def test_publish_uses_redis_when_available():
    redis = AsyncMock()
    publisher = EventPublisher(redis=redis)

    await publisher._publish("job.completed", {"event_type": "job_completed", "job_id": "1"})

    redis.publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_publish_sends_to_sns_when_topic_configured(monkeypatch):
    sns = AsyncMock()
    publisher = EventPublisher(redis=None)
    publisher._session = DummySession(sns)

    from job_service.infrastructure.adapters.output.messaging import event_publisher as module

    monkeypatch.setattr(module.settings, "SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:topic")

    message = {"event_type": "job_failed", "error": "x"}
    await publisher._publish("job.failed", message)

    sns.publish.assert_awaited_once()
    kwargs = sns.publish.await_args.kwargs
    assert kwargs["TopicArn"]
    assert json.loads(kwargs["Message"]) == message


@pytest.mark.asyncio
async def test_helper_methods_build_expected_payload(monkeypatch):
    publisher = EventPublisher(redis=None)
    publisher._publish = AsyncMock()

    await publisher.publish_job_started("j", "v", "u")
    await publisher.publish_job_completed("j", "v", "u", 10, "x.zip")
    await publisher.publish_job_failed("j", "v", "u", "erro")

    assert publisher._publish.await_count == 3
