from io import BytesIO
from unittest.mock import AsyncMock

import pytest

from job_service.infrastructure.adapters.output.storage.s3_storage import S3StorageAdapter


class DummyClientContext:
    def __init__(self, client):
        self._client = client

    async def __aenter__(self):
        return self._client

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummySession:
    def __init__(self, client):
        self._client = client

    def client(self, *_args, **_kwargs):
        return DummyClientContext(self._client)


@pytest.mark.asyncio
async def test_download_upload_delete_and_presigned(monkeypatch):
    s3 = AsyncMock()
    s3.generate_presigned_url.return_value = "http://internal:4566/bucket/key?sig=1"

    adapter = S3StorageAdapter()
    adapter._session = DummySession(s3)

    from job_service.infrastructure.adapters.output.storage import s3_storage as module

    monkeypatch.setattr(module.settings, "PUBLIC_S3_ENDPOINT_URL", "https://cdn.example.com")

    destination = await adapter.download_file("b", "k", "dest.mp4")
    uploaded_key = await adapter.upload_file("f", "b", "k", "video/mp4")
    uploaded_obj_key = await adapter.upload_fileobj(BytesIO(b"x"), "b", "k2", None)
    signed_url = await adapter.generate_presigned_url("b", "k", 90)
    await adapter.delete_file("b", "k")

    assert destination == "dest.mp4"
    assert uploaded_key == "k"
    assert uploaded_obj_key == "k2"
    assert signed_url.startswith("https://cdn.example.com")
    s3.download_file.assert_awaited_once()
    s3.upload_file.assert_awaited_once()
    s3.upload_fileobj.assert_awaited_once()
    s3.delete_object.assert_awaited_once()
