import pytest

from job_service.application.use_cases.get_job import GetJobUseCase
from video_processor_shared.domain.exceptions import JobNotFoundError


class RepoStub:
    def __init__(self, job):
        self.job = job

    async def find_by_id(self, job_id):
        return self.job


@pytest.mark.asyncio
async def test_execute_returns_job_details(make_job):
    job = make_job(progress=70)
    repo = RepoStub(job)
    use_case = GetJobUseCase(repo)

    result = await use_case.execute(job.id, job.user_id)

    assert result.id == job.id
    assert result.progress == 70


@pytest.mark.asyncio
async def test_execute_raises_when_not_found(make_job):
    job = make_job()
    repo = RepoStub(None)
    use_case = GetJobUseCase(repo)

    with pytest.raises(JobNotFoundError):
        await use_case.execute(job.id, job.user_id)


@pytest.mark.asyncio
async def test_execute_raises_when_user_differs(make_job):
    job = make_job()
    other = make_job()
    repo = RepoStub(job)
    use_case = GetJobUseCase(repo)

    with pytest.raises(JobNotFoundError):
        await use_case.execute(job.id, other.user_id)
