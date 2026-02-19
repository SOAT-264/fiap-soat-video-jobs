from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from job_service.infrastructure.adapters.input.api.main import app
from job_service.infrastructure.adapters.input.api.routes import job_routes, health_routes
from video_processor_shared.domain.exceptions import JobNotFoundError
from video_processor_shared.domain.value_objects import JobStatus


def test_root_endpoint():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "job-service"


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness_endpoint_connected_services():
    class DbStub:
        async def execute(self, _):
            return 1

    class RedisStub:
        async def ping(self):
            return True

    app.dependency_overrides[health_routes.get_session] = lambda: DbStub()
    app.dependency_overrides[health_routes.get_redis] = lambda: RedisStub()

    client = TestClient(app)
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"

    app.dependency_overrides.clear()


def test_get_job_endpoint_404(monkeypatch):
    class FakeUseCase:
        def __init__(self, _):
            pass

        async def execute(self, *_args, **_kwargs):
            raise JobNotFoundError("x")

    monkeypatch.setattr(job_routes, "GetJobUseCase", FakeUseCase)

    user_id = uuid4()
    job_id = uuid4()
    client = TestClient(app)
    response = client.get(f"/jobs/{job_id}?user_id={user_id}")

    assert response.status_code == 404


def test_list_jobs_endpoint_success(monkeypatch):
    class Result:
        def __init__(self, user_id):
            self.jobs = [
                type("J", (), {
                    "id": uuid4(),
                    "video_id": uuid4(),
                    "user_id": user_id,
                    "status": JobStatus.COMPLETED,
                    "progress": 100,
                    "frame_count": 10,
                    "zip_path": "outputs/x.zip",
                    "zip_size": 99,
                    "error_message": None,
                    "started_at": None,
                    "completed_at": datetime.now(UTC),
                    "created_at": datetime.now(UTC),
                })
            ]
            self.page = 1
            self.limit = 20
            self.total = 1
            self.pages = 1

    class FakeUseCase:
        def __init__(self, _):
            pass

        async def execute(self, user_id, status_filter=None, page=1, limit=20):
            return Result(user_id)

    class FakeStorage:
        async def generate_presigned_url(self, bucket, key):
            return f"https://cdn/{bucket}/{key}"

    monkeypatch.setattr(job_routes, "ListJobsUseCase", FakeUseCase)
    monkeypatch.setattr(job_routes, "S3StorageAdapter", lambda: FakeStorage())

    user_id = uuid4()
    client = TestClient(app)
    response = client.get(f"/jobs?user_id={user_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total"] == 1
    assert body["jobs"][0]["download_url"].startswith("https://cdn/")


def test_list_jobs_endpoint_invalid_status_returns_400(monkeypatch):
    class FakeUseCase:
        def __init__(self, _):
            pass

        async def execute(self, **_kwargs):
            raise ValueError("Invalid status")

    monkeypatch.setattr(job_routes, "ListJobsUseCase", FakeUseCase)

    user_id = uuid4()
    client = TestClient(app)
    response = client.get(f"/jobs?user_id={user_id}&status=BAD")

    assert response.status_code == 400
