import pytest

from job_service.application.use_cases.create_job import CreateJobUseCase
from video_processor_shared.domain.value_objects import JobStatus


class RepoStub:
    def __init__(self, existing=None):
        self.existing = existing
        self.saved = None

    async def find_by_video_id(self, video_id):
        return self.existing

    async def save(self, job):
        self.saved = job
        return job


@pytest.mark.asyncio
async def test_execute_returns_existing_job(make_job):
    existing = make_job(status=JobStatus.PROCESSING, progress=45)
    repo = RepoStub(existing=existing)
    use_case = CreateJobUseCase(repo)

    output = await use_case.execute(existing.video_id, existing.user_id)

    assert output.id == existing.id
    assert output.status == JobStatus.PROCESSING
    assert repo.saved is None


@pytest.mark.asyncio
async def test_execute_creates_new_job(make_job):
    sample = make_job()
    repo = RepoStub(existing=None)
    use_case = CreateJobUseCase(repo)

    output = await use_case.execute(sample.video_id, sample.user_id)

    assert repo.saved is not None
    assert output.video_id == sample.video_id
    assert output.user_id == sample.user_id
    assert output.status == JobStatus.PENDING
    assert output.progress == 0
