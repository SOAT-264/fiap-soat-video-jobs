"""SQLAlchemy Job Repository implementation."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from job_service.domain.entities.job import Job
from job_service.application.ports.output.repositories.job_repository import IJobRepository
from job_service.infrastructure.adapters.output.persistence.models import JobModel

from video_processor_shared.domain.value_objects import JobStatus


class SQLAlchemyJobRepository(IJobRepository):
    """SQLAlchemy implementation of IJobRepository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, job: Job) -> Job:
        """Save a new job."""
        model = JobModel(
            id=job.id,
            video_id=job.video_id,
            user_id=job.user_id,
            status=job.status,
            progress=job.progress,
            frame_count=job.frame_count,
            zip_path=job.zip_path,
            zip_size=job.zip_size,
            error_message=job.error_message,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return job

    async def find_by_id(self, job_id: UUID) -> Optional[Job]:
        """Find a job by ID."""
        result = await self._session.execute(
            select(JobModel).where(JobModel.id == job_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_user_id(
        self, user_id: UUID, skip: int = 0, limit: int = 10
    ) -> List[Job]:
        """Find jobs by user ID with pagination."""
        result = await self._session.execute(
            select(JobModel)
            .where(JobModel.user_id == user_id)
            .order_by(JobModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def find_by_video_id(self, video_id: UUID) -> Optional[Job]:
        """Find a job by video ID."""
        result = await self._session.execute(
            select(JobModel).where(JobModel.video_id == video_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, job: Job) -> Job:
        """Update an existing job."""
        result = await self._session.execute(
            select(JobModel).where(JobModel.id == job.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.status = job.status
            model.progress = job.progress
            model.frame_count = job.frame_count
            model.zip_path = job.zip_path
            model.zip_size = job.zip_size
            model.error_message = job.error_message
            model.started_at = job.started_at
            model.completed_at = job.completed_at
            model.updated_at = job.updated_at
            await self._session.flush()
        return job

    async def count_by_user_id(self, user_id: UUID) -> int:
        """Count jobs for a user."""
        result = await self._session.execute(
            select(func.count(JobModel.id)).where(JobModel.user_id == user_id)
        )
        return result.scalar() or 0

    async def find_by_user_and_status(
        self, user_id: UUID, status: JobStatus, skip: int = 0, limit: int = 10
    ) -> List[Job]:
        """Find jobs by user ID and status with pagination."""
        result = await self._session.execute(
            select(JobModel)
            .where(JobModel.user_id == user_id, JobModel.status == status)
            .order_by(JobModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def count_by_user_and_status(self, user_id: UUID, status: JobStatus) -> int:
        """Count jobs for a user with specific status."""
        result = await self._session.execute(
            select(func.count(JobModel.id)).where(
                JobModel.user_id == user_id, JobModel.status == status
            )
        )
        return result.scalar() or 0

    def _to_entity(self, model: JobModel) -> Job:
        """Convert SQLAlchemy model to domain entity."""
        return Job(
            id=model.id,
            video_id=model.video_id,
            user_id=model.user_id,
            status=model.status,
            progress=model.progress,
            frame_count=model.frame_count,
            zip_path=model.zip_path,
            zip_size=model.zip_size,
            error_message=model.error_message,
            started_at=model.started_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
