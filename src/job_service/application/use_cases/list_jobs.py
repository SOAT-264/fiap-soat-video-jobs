"""List Jobs Use Case."""
from dataclasses import dataclass
from typing import List
from uuid import UUID

from job_service.application.ports.output.repositories.job_repository import IJobRepository
from job_service.application.use_cases.create_job import JobOutput


@dataclass
class PaginatedJobsOutput:
    jobs: List[JobOutput]
    total: int
    page: int
    page_size: int


class ListJobsUseCase:
    def __init__(self, job_repository: IJobRepository):
        self._job_repository = job_repository

    async def execute(self, user_id: UUID, page: int = 1, page_size: int = 10) -> PaginatedJobsOutput:
        skip = (page - 1) * page_size
        jobs = await self._job_repository.find_by_user_id(user_id, skip, page_size)
        total = await self._job_repository.count_by_user_id(user_id)

        return PaginatedJobsOutput(
            jobs=[
                JobOutput(
                    id=j.id,
                    video_id=j.video_id,
                    user_id=j.user_id,
                    status=j.status,
                    progress=j.progress,
                    created_at=j.created_at,
                )
                for j in jobs
            ],
            total=total,
            page=page,
            page_size=page_size,
        )
