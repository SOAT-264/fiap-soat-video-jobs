"""Get Job Use Case."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from job_service.application.ports.output.repositories.job_repository import IJobRepository

from video_processor_shared.domain.value_objects import JobStatus
from video_processor_shared.domain.exceptions import JobNotFoundError


@dataclass
class JobDetailOutput:
    id: UUID
    video_id: UUID
    user_id: UUID
    status: JobStatus
    progress: int
    frame_count: Optional[int]
    zip_path: Optional[str]
    zip_size: Optional[int]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


class GetJobUseCase:
    def __init__(self, job_repository: IJobRepository):
        self._job_repository = job_repository

    async def execute(self, job_id: UUID, user_id: UUID) -> JobDetailOutput:
        job = await self._job_repository.find_by_id(job_id)
        if not job or job.user_id != user_id:
            raise JobNotFoundError(f"Job {job_id} not found")

        return JobDetailOutput(
            id=job.id,
            video_id=job.video_id,
            user_id=job.user_id,
            status=job.status,
            progress=job.progress,
            frame_count=job.frame_count,
            zip_path=job.zip_path,
            zip_size=job.zip_size,
            error_message=job.error_message,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
        )
