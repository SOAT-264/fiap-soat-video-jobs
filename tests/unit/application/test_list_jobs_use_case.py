import pytest

from job_service.application.use_cases.list_jobs import ListJobsUseCase
from video_processor_shared.domain.value_objects import JobStatus


class RepoStub:
    def __init__(self, jobs):
        self.jobs = jobs

    async def find_by_user_id(self, user_id, skip, limit):
        return self.jobs[skip : skip + limit]

    async def count_by_user_id(self, user_id):
        return len(self.jobs)

    async def find_by_user_and_status(self, user_id, status, skip, limit):
        filtered = [job for job in self.jobs if job.status == status]
        return filtered[skip : skip + limit]

    async def count_by_user_and_status(self, user_id, status):
        return len([job for job in self.jobs if job.status == status])


@pytest.mark.asyncio
async def test_execute_without_filter_returns_paginated_jobs(make_job):
    jobs = [make_job() for _ in range(5)]
    repo = RepoStub(jobs)
    use_case = ListJobsUseCase(repo)

    result = await use_case.execute(user_id=jobs[0].user_id, page=1, limit=2)

    assert len(result.jobs) == 2
    assert result.total == 5
    assert result.pages == 3


@pytest.mark.asyncio
async def test_execute_with_status_filter(make_job):
    jobs = [
        make_job(status=JobStatus.PENDING),
        make_job(status=JobStatus.COMPLETED),
        make_job(status=JobStatus.COMPLETED),
    ]
    repo = RepoStub(jobs)
    use_case = ListJobsUseCase(repo)

    result = await use_case.execute(
        user_id=jobs[0].user_id,
        status_filter=JobStatus.COMPLETED.value,
        page=1,
        limit=10,
    )

    assert result.total == 2
    assert all(job.status == JobStatus.COMPLETED for job in result.jobs)


@pytest.mark.asyncio
async def test_execute_with_invalid_status_raises(make_job):
    jobs = [make_job()]
    repo = RepoStub(jobs)
    use_case = ListJobsUseCase(repo)

    with pytest.raises(ValueError):
        await use_case.execute(user_id=jobs[0].user_id, status_filter="INVALID")
