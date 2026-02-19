from datetime import UTC, datetime
from pathlib import Path
import sys
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from job_service.domain.entities.job import Job
from video_processor_shared.domain.value_objects import JobStatus


@pytest.fixture
def make_job():
    def _make_job(**overrides):
        now = datetime.now(UTC)
        data = {
            "id": uuid4(),
            "video_id": uuid4(),
            "user_id": uuid4(),
            "status": JobStatus.PENDING,
            "progress": 0,
            "created_at": now,
            "updated_at": now,
        }
        data.update(overrides)
        return Job(**data)

    return _make_job
