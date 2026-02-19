from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest

from job_service.infrastructure.adapters.output.persistence import database


class DummySession:
    def __init__(self):
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.close = AsyncMock()


@asynccontextmanager
async def make_cm(session):
    yield session


@pytest.mark.asyncio
async def test_get_session_commits_and_closes(monkeypatch):
    session = DummySession()
    monkeypatch.setattr(database, "async_session_maker", lambda: make_cm(session))

    agen = database.get_session()
    yielded = await anext(agen)
    assert yielded is session

    with pytest.raises(StopAsyncIteration):
        await anext(agen)

    session.commit.assert_awaited_once()
    session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_rollbacks_on_error(monkeypatch):
    session = DummySession()
    monkeypatch.setattr(database, "async_session_maker", lambda: make_cm(session))

    agen = database.get_session()
    await anext(agen)

    with pytest.raises(RuntimeError):
        await agen.athrow(RuntimeError("x"))

    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_context_commits(monkeypatch):
    session = DummySession()
    monkeypatch.setattr(database, "async_session_maker", lambda: make_cm(session))

    async with database.get_session_context() as yielded:
        assert yielded is session

    session.commit.assert_awaited_once()
    session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_context_rollbacks_on_error(monkeypatch):
    session = DummySession()
    monkeypatch.setattr(database, "async_session_maker", lambda: make_cm(session))

    with pytest.raises(ValueError):
        async with database.get_session_context():
            raise ValueError("boom")

    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()
