from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from job_service.infrastructure.adapters.input.worker import video_processor_task as task


class SessionStub:
    def __init__(self):
        self.commit = AsyncMock()


@pytest.mark.asyncio
async def test_process_video_task_happy_path(monkeypatch, make_job, tmp_path):
    job = make_job()
    session = SessionStub()

    class RepoStub:
        def __init__(self, _session):
            self._session = _session

        async def find_by_id(self, _id):
            return job

        async def update(self, _job):
            return _job

    storage = AsyncMock()
    processor = AsyncMock()
    processor.extract_frames.return_value = 5
    processor.create_zip_archive.return_value = 100
    publisher = AsyncMock()

    @asynccontextmanager
    async def session_ctx():
        yield session

    monkeypatch.setattr(task, "get_session_context", session_ctx)
    monkeypatch.setattr(task, "SQLAlchemyJobRepository", RepoStub)
    monkeypatch.setattr(task, "S3StorageAdapter", lambda: storage)
    monkeypatch.setattr(task, "FFmpegVideoProcessor", lambda: processor)
    monkeypatch.setattr(task, "EventPublisher", lambda *_args, **_kwargs: publisher)
    monkeypatch.setattr(task, "get_redis", AsyncMock(return_value=None))
    monkeypatch.setattr(task.tempfile, "mkdtemp", lambda: str(tmp_path))

    await task.process_video_task(str(job.id), "videos/in.mp4")

    assert session.commit.await_count >= 4
    storage.download_file.assert_awaited_once()
    storage.upload_file.assert_awaited_once()
    publisher.publish_job_completed.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_video_task_marks_failed_and_raises(monkeypatch, make_job, tmp_path):
    job = make_job()

    class RepoStub:
        def __init__(self, _session):
            pass

        async def find_by_id(self, _id):
            return job

        async def update(self, _job):
            return _job

    session = SessionStub()

    @asynccontextmanager
    async def session_ctx():
        yield session

    processor = AsyncMock()
    processor.extract_frames.side_effect = RuntimeError("erro de processamento")
    publisher = AsyncMock()

    monkeypatch.setattr(task, "get_session_context", session_ctx)
    monkeypatch.setattr(task, "SQLAlchemyJobRepository", RepoStub)
    monkeypatch.setattr(task, "S3StorageAdapter", lambda: AsyncMock())
    monkeypatch.setattr(task, "FFmpegVideoProcessor", lambda: processor)
    monkeypatch.setattr(task, "EventPublisher", lambda *_args, **_kwargs: publisher)
    monkeypatch.setattr(task, "get_redis", AsyncMock(return_value=None))
    monkeypatch.setattr(task.tempfile, "mkdtemp", lambda: str(tmp_path / "work"))

    with pytest.raises(RuntimeError):
        await task.process_video_task(str(job.id), "videos/in.mp4")

    publisher.publish_job_failed.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_video_task_raises_when_job_not_found(monkeypatch, tmp_path):
    class RepoStub:
        def __init__(self, _session):
            pass

        async def find_by_id(self, _id):
            return None

        async def update(self, _job):
            return _job

    session = SessionStub()

    @asynccontextmanager
    async def session_ctx():
        yield session

    monkeypatch.setattr(task, "get_session_context", session_ctx)
    monkeypatch.setattr(task, "SQLAlchemyJobRepository", RepoStub)
    monkeypatch.setattr(task, "S3StorageAdapter", lambda: AsyncMock())
    monkeypatch.setattr(task, "FFmpegVideoProcessor", lambda: AsyncMock())
    monkeypatch.setattr(task, "EventPublisher", lambda *_args, **_kwargs: AsyncMock())
    monkeypatch.setattr(task, "get_redis", AsyncMock(return_value=None))
    monkeypatch.setattr(task.tempfile, "mkdtemp", lambda: str(tmp_path / "work2"))

    with pytest.raises(ValueError):
        await task.process_video_task(str(uuid4()), "videos/in.mp4")
