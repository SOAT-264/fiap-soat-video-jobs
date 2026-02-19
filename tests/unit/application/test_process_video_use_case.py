from unittest.mock import AsyncMock, patch

import pytest
from video_processor_shared.domain.events import JobCompletedEvent, JobFailedEvent
from video_processor_shared.domain.value_objects import JobStatus

from job_service.application.use_cases.process_video import ProcessVideoUseCase


@pytest.mark.asyncio
async def test_execute_returns_when_job_not_found():
    repo = AsyncMock()
    repo.find_by_id.return_value = None

    use_case = ProcessVideoUseCase(
        job_repository=repo,
        video_processor=AsyncMock(),
        storage_service=AsyncMock(),
        event_publisher=AsyncMock(),
    )

    await use_case.execute(job_id="x", video_path="path")

    repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_execute_happy_path(make_job):
    job = make_job()
    repo = AsyncMock()
    repo.find_by_id.return_value = job

    processor = AsyncMock()
    processor.extract_frames.return_value = (8, "/tmp/out.zip")
    storage = AsyncMock()
    storage.upload_file.return_value = "outputs/file.zip"
    publisher = AsyncMock()

    use_case = ProcessVideoUseCase(repo, processor, storage, publisher)

    with patch("os.path.getsize", return_value=222):
        await use_case.execute(job_id=job.id, video_path="video/key.mp4")

    assert repo.update.await_count >= 2
    assert storage.download_file.await_count == 1
    assert storage.upload_file.await_count == 1
    event = publisher.publish.await_args.args[0]
    assert isinstance(event, JobCompletedEvent)
    assert event.frame_count == 8


@pytest.mark.asyncio
async def test_execute_failure_publishes_failed_event(make_job):
    job = make_job()
    repo = AsyncMock()
    repo.find_by_id.return_value = job

    processor = AsyncMock()
    processor.extract_frames.side_effect = RuntimeError("ffmpeg failed")

    use_case = ProcessVideoUseCase(
        job_repository=repo,
        video_processor=processor,
        storage_service=AsyncMock(),
        event_publisher=AsyncMock(),
    )

    await use_case.execute(job_id=job.id, video_path="video/key.mp4")

    event = use_case._event_publisher.publish.await_args.args[0]
    assert isinstance(event, JobFailedEvent)
    assert "ffmpeg failed" in event.error_message


@pytest.mark.asyncio
async def test_update_progress_updates_job_and_repository(make_job):
    job = make_job(status=JobStatus.PROCESSING)
    repo = AsyncMock()
    use_case = ProcessVideoUseCase(repo, AsyncMock(), AsyncMock(), AsyncMock())

    await use_case._update_progress(job, 55)

    assert job.progress == 55
    repo.update.assert_awaited_once_with(job)
