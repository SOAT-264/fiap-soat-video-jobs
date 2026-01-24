"""Create Job Use Case."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from job_service.domain.entities.job import Job
from job_service.application.ports.output.repositories.job_repository import IJobRepository

from video_processor_shared.domain.value_objects import JobStatus


@dataclass
class JobOutput:
    id: UUID
    video_id: UUID
    user_id: UUID
    status: JobStatus
    progress: int
    created_at: datetime


class CreateJobUseCase:
    def __init__(self, job_repository: IJobRepository):
        self._job_repository = job_repository

    async def execute(self, video_id: UUID, user_id: UUID) -> JobOutput:
        existing = await self._job_repository.find_by_video_id(video_id)
        if existing:
            return JobOutput(
                id=existing.id,
                video_id=existing.video_id,
                user_id=existing.user_id,
                status=existing.status,
                progress=existing.progress,
                created_at=existing.created_at,
            )

        job = Job(
            id=uuid4(),
            video_id=video_id,
            user_id=user_id,
            status=JobStatus.PENDING,
        )

        saved = await self._job_repository.save(job)
        return JobOutput(
            id=saved.id,
            video_id=saved.video_id,
            user_id=saved.user_id,
            status=saved.status,
            progress=saved.progress,
            created_at=saved.created_at,
        )
