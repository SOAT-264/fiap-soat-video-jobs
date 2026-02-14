"""List Jobs Use Case."""
from dataclasses import dataclass
from math import ceil
from typing import List, Optional
from uuid import UUID

from job_service.application.ports.output.repositories.job_repository import IJobRepository
from job_service.application.use_cases.create_job import JobOutput

from video_processor_shared.domain.value_objects import JobStatus


@dataclass
class PaginatedJobsOutput:
    jobs: List[JobOutput]
    total: int
    page: int
    limit: int
    pages: int


class ListJobsUseCase:
    def __init__(self, job_repository: IJobRepository):
        self._job_repository = job_repository

    async def execute(
        self,
        user_id: UUID,
        status_filter: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> PaginatedJobsOutput:
        skip = (page - 1) * limit

        if status_filter:
            try:
                status = JobStatus(status_filter)
            except ValueError as exc:
                raise ValueError(f"Invalid status: {status_filter}") from exc
            jobs = await self._job_repository.find_by_user_and_status(user_id, status, skip, limit)
            total = await self._job_repository.count_by_user_and_status(user_id, status)
        else:
            jobs = await self._job_repository.find_by_user_id(user_id, skip, limit)
            total = await self._job_repository.count_by_user_id(user_id)

        pages = ceil(total / limit) if total else 0

        return PaginatedJobsOutput(
            jobs=[
                JobOutput(
                    id=j.id,
                    video_id=j.video_id,
                    user_id=j.user_id,
                    status=j.status,
                    progress=j.progress,
                    created_at=j.created_at,
                    frame_count=j.frame_count,
                    zip_path=j.zip_path,
                    zip_size=j.zip_size,
                    error_message=j.error_message,
                    started_at=j.started_at,
                    completed_at=j.completed_at,
                )
                for j in jobs
            ],
            total=total,
            page=page,
            limit=limit,
            pages=pages,
        )
