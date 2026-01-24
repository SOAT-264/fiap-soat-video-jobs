"""Process Video Use Case - Worker."""
from abc import ABC, abstractmethod
from typing import Callable, Optional
from uuid import UUID

from job_service.application.ports.output.repositories.job_repository import IJobRepository

from video_processor_shared.domain.events import JobCompletedEvent, JobFailedEvent


class IVideoProcessor(ABC):
    @abstractmethod
    async def extract_frames(
        self,
        input_path: str,
        output_dir: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> tuple[int, str]:
        """Extract frames from video. Returns (frame_count, zip_path)."""
        pass


class IStorageService(ABC):
    @abstractmethod
    async def download_file(self, key: str, local_path: str) -> None:
        pass

    @abstractmethod
    async def upload_file(self, local_path: str, key: str) -> str:
        pass


class IEventPublisher(ABC):
    @abstractmethod
    async def publish(self, event) -> None:
        pass


class ProcessVideoUseCase:
    def __init__(
        self,
        job_repository: IJobRepository,
        video_processor: IVideoProcessor,
        storage_service: IStorageService,
        event_publisher: IEventPublisher,
    ):
        self._job_repository = job_repository
        self._video_processor = video_processor
        self._storage_service = storage_service
        self._event_publisher = event_publisher

    async def execute(self, job_id: UUID, video_path: str) -> None:
        job = await self._job_repository.find_by_id(job_id)
        if not job:
            return

        try:
            job.start()
            await self._job_repository.update(job)

            # Download video from S3
            local_input = f"/tmp/{job_id}_input.mp4"
            await self._storage_service.download_file(video_path, local_input)

            # Extract frames
            output_dir = f"/tmp/{job_id}_frames"
            frame_count, local_zip = await self._video_processor.extract_frames(
                local_input,
                output_dir,
                progress_callback=lambda p: self._update_progress(job, p),
            )

            # Upload zip to S3
            output_key = f"outputs/{job.user_id}/{job_id}/frames.zip"
            zip_path = await self._storage_service.upload_file(local_zip, output_key)

            import os
            zip_size = os.path.getsize(local_zip)

            job.complete(frame_count, zip_path, zip_size)
            await self._job_repository.update(job)

            await self._event_publisher.publish(
                JobCompletedEvent(
                    job_id=job.id,
                    video_id=job.video_id,
                    user_id=job.user_id,
                    frame_count=frame_count,
                    zip_path=zip_path,
                )
            )

        except Exception as e:
            job.fail(str(e))
            await self._job_repository.update(job)

            await self._event_publisher.publish(
                JobFailedEvent(
                    job_id=job.id,
                    video_id=job.video_id,
                    user_id=job.user_id,
                    error_message=str(e),
                )
            )

    async def _update_progress(self, job, progress: int) -> None:
        job.update_progress(progress)
        await self._job_repository.update(job)
