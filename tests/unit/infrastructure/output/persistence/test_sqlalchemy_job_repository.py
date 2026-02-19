from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from job_service.infrastructure.adapters.output.persistence.models import JobModel
from job_service.infrastructure.adapters.output.persistence.repositories.sqlalchemy_job_repository import (
    SQLAlchemyJobRepository,
)
from video_processor_shared.domain.value_objects import JobStatus


class ScalarWrapper:
    def __init__(self, one=None, many=None):
        self._one = one
        self._many = many or []

    def scalar_one_or_none(self):
        return self._one

    def scalar(self):
        return self._one

    def scalars(self):
        class Items:
            def __init__(self, values):
                self._values = values

            def all(self):
                return self._values

        return Items(self._many)


def make_model(**overrides):
    now = datetime.now(UTC)
    data = {
        "id": uuid4(),
        "video_id": uuid4(),
        "user_id": uuid4(),
        "status": JobStatus.PENDING,
        "progress": 0,
        "frame_count": None,
        "zip_path": None,
        "zip_size": None,
        "error_message": None,
        "started_at": None,
        "completed_at": None,
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return JobModel(**data)


def make_session_stub():
    session = Mock()
    session.add = Mock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_save_adds_and_flushes(make_job):
    session = make_session_stub()
    repo = SQLAlchemyJobRepository(session)
    job = make_job()

    saved = await repo.save(job)

    assert saved == job
    session.add.assert_called_once()
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_find_by_id_returns_entity():
    session = make_session_stub()
    model = make_model()
    session.execute.return_value = ScalarWrapper(one=model)
    repo = SQLAlchemyJobRepository(session)

    result = await repo.find_by_id(model.id)

    assert result is not None
    assert result.id == model.id


@pytest.mark.asyncio
async def test_find_by_user_and_video_and_count():
    session = make_session_stub()
    models = [make_model(), make_model()]
    session.execute.side_effect = [
        ScalarWrapper(many=models),
        ScalarWrapper(one=models[0]),
        ScalarWrapper(one=2),
        ScalarWrapper(many=[models[1]]),
        ScalarWrapper(one=1),
    ]
    repo = SQLAlchemyJobRepository(session)

    by_user = await repo.find_by_user_id(models[0].user_id, 0, 10)
    by_video = await repo.find_by_video_id(models[0].video_id)
    count_user = await repo.count_by_user_id(models[0].user_id)
    by_status = await repo.find_by_user_and_status(models[0].user_id, JobStatus.PENDING, 0, 10)
    count_status = await repo.count_by_user_and_status(models[0].user_id, JobStatus.PENDING)

    assert len(by_user) == 2
    assert by_video is not None
    assert count_user == 2
    assert len(by_status) == 1
    assert count_status == 1


@pytest.mark.asyncio
async def test_update_updates_model_fields(make_job):
    session = make_session_stub()
    model = make_model(progress=10)
    session.execute.return_value = ScalarWrapper(one=model)
    repo = SQLAlchemyJobRepository(session)

    job = make_job(id=model.id, status=JobStatus.PROCESSING, progress=55, zip_path="k", zip_size=9)
    updated = await repo.update(job)

    assert updated == job
    assert model.progress == 55
    assert model.status == JobStatus.PROCESSING
    assert model.zip_path == "k"
    session.flush.assert_awaited_once()
