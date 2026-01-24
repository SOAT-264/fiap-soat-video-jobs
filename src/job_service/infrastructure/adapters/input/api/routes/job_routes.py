"""Job routes for the API."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from job_service.application.use_cases.get_job import GetJobUseCase
from job_service.application.use_cases.list_jobs import ListJobsUseCase
from job_service.infrastructure.adapters.input.api.schemas.job_schemas import (
    JobResponse,
    JobListResponse,
    PaginationMeta,
)
from job_service.infrastructure.adapters.output.persistence.repositories.sqlalchemy_job_repository import (
    SQLAlchemyJobRepository,
)
from job_service.infrastructure.adapters.output.persistence.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession

from video_processor_shared.domain.exceptions import JobNotFoundError

router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_repository(session: AsyncSession = Depends(get_session)) -> SQLAlchemyJobRepository:
    return SQLAlchemyJobRepository(session)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    user_id: UUID = Query(..., description="User ID from auth token"),
    repository: SQLAlchemyJobRepository = Depends(get_job_repository),
) -> JobResponse:
    """Get job details by ID."""
    use_case = GetJobUseCase(repository)
    try:
        result = await use_case.execute(job_id, user_id)
        return JobResponse(
            id=result.id,
            video_id=result.video_id,
            user_id=result.user_id,
            status=result.status.value,
            progress=result.progress,
            frame_count=result.frame_count,
            zip_path=result.zip_path,
            zip_size=result.zip_size,
            error_message=result.error_message,
            started_at=result.started_at,
            completed_at=result.completed_at,
            created_at=result.created_at,
        )
    except JobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")


@router.get("", response_model=JobListResponse)
async def list_jobs(
    user_id: UUID = Query(..., description="User ID from auth token"),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    repository: SQLAlchemyJobRepository = Depends(get_job_repository),
) -> JobListResponse:
    """List jobs for a user with pagination."""
    use_case = ListJobsUseCase(repository)
    result = await use_case.execute(
        user_id=user_id,
        status_filter=status_filter,
        page=page,
        limit=limit,
    )
    
    jobs = [
        JobResponse(
            id=job.id,
            video_id=job.video_id,
            user_id=job.user_id,
            status=job.status.value,
            progress=job.progress,
            frame_count=job.frame_count,
            zip_path=job.zip_path,
            zip_size=job.zip_size,
            error_message=job.error_message,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
        )
        for job in result.jobs
    ]
    
    return JobListResponse(
        jobs=jobs,
        pagination=PaginationMeta(
            page=result.page,
            limit=result.limit,
            total=result.total,
            pages=result.pages,
        ),
    )
