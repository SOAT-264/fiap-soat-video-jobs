import asyncio
import json
from unittest.mock import AsyncMock
from uuid import uuid4
from contextlib import asynccontextmanager

import pytest

from job_service.infrastructure.adapters.input import sqs_consumer


@pytest.mark.asyncio
async def test_resolve_job_payload_direct_job_fields():
    body = {"job_id": "job-1", "s3_key": "videos/a.mp4"}

    job_id, s3_key = await sqs_consumer._resolve_job_payload(body)

    assert job_id == "job-1"
    assert s3_key == "videos/a.mp4"


@pytest.mark.asyncio
async def test_resolve_job_payload_raises_on_missing_fields():
    with pytest.raises(ValueError):
        await sqs_consumer._resolve_job_payload({"video_id": "x"})


@pytest.mark.asyncio
async def test_resolve_job_payload_creates_job_when_video_event(monkeypatch):
    video_id = uuid4()
    user_id = uuid4()

    class Created:
        id = uuid4()

    class UseCaseStub:
        def __init__(self, *_args, **_kwargs):
            pass

        async def execute(self, *_args, **_kwargs):
            return Created()

    session = AsyncMock()

    @asynccontextmanager
    async def fake_session_context():
        yield session

    monkeypatch.setattr(sqs_consumer, "CreateJobUseCase", UseCaseStub)
    monkeypatch.setattr(sqs_consumer, "get_session_context", fake_session_context)

    body = {
        "video_id": str(video_id),
        "user_id": str(user_id),
        "filename": "movie.MP4",
    }

    job_id, s3_key = await sqs_consumer._resolve_job_payload(body)

    assert job_id == str(Created.id)
    assert s3_key.endswith(f"{video_id}.mp4")
    session.commit.assert_awaited_once()


def test_lambda_handler_processes_records(monkeypatch):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        resolved = [("job-1", "videos/a.mp4")]
        monkeypatch.setattr(sqs_consumer, "_resolve_job_payload", AsyncMock(return_value=resolved[0]))
        monkeypatch.setattr(sqs_consumer, "process_video_task", AsyncMock())

        event = {
            "Records": [
                {"messageId": "1", "body": json.dumps({"job_id": "job-1", "s3_key": "videos/a.mp4"})}
            ]
        }

        result = sqs_consumer.lambda_handler(event, None)
        body = json.loads(result["body"])

        assert result["statusCode"] == 200
        assert body["processed"] == ["job-1"]
        assert body["failed"] == []
    finally:
        loop.close()


@pytest.mark.asyncio
async def test_resolve_message_returns_none_on_invalid_body():
    consumer = sqs_consumer.SQSJobConsumer(queue_url="q")
    job_id, video_key = await consumer._resolve_message({"Body": "not-json", "MessageId": "1"})
    assert job_id is None
    assert video_key is None


@pytest.mark.asyncio
async def test_process_resolved_job_deletes_message(monkeypatch):
    consumer = sqs_consumer.SQSJobConsumer(queue_url="q")
    sqs = AsyncMock()
    monkeypatch.setattr(sqs_consumer, "process_video_task", AsyncMock())

    await consumer._process_resolved_job(sqs, str(uuid4()), "videos/x.mp4", "rh")

    sqs.delete_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_resolved_job_keeps_message_when_processing_fails(monkeypatch):
    consumer = sqs_consumer.SQSJobConsumer(queue_url="q")
    sqs = AsyncMock()
    monkeypatch.setattr(sqs_consumer, "process_video_task", AsyncMock(side_effect=RuntimeError("x")))

    await consumer._process_resolved_job(sqs, str(uuid4()), "videos/x.mp4", "rh")

    sqs.delete_message.assert_not_called()


@pytest.mark.asyncio
async def test_poll_and_process_no_messages(monkeypatch):
    consumer = sqs_consumer.SQSJobConsumer(queue_url="q")
    sqs = AsyncMock()
    sqs.receive_message.return_value = {}

    class DummyCtx:
        async def __aenter__(self):
            return sqs

        async def __aexit__(self, exc_type, exc, tb):
            return False

    consumer._session = type("S", (), {"client": lambda *_args, **_kwargs: DummyCtx()})()
    consumer._process_resolved_job = AsyncMock()

    await consumer._poll_and_process()

    consumer._process_resolved_job.assert_not_called()
