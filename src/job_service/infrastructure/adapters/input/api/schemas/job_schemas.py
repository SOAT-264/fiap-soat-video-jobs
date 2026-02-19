"""Job API Schemas."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class JobResponse(BaseModel):
    """Job response schema."""
    id: UUID
    video_id: UUID
    user_id: UUID
    status: str
    progress: int = Field(ge=0, le=100)
    frame_count: Optional[int] = None
    zip_path: Optional[str] = None
    zip_size: Optional[int] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobProgressUpdate(BaseModel):
    """Job progress update schema."""
    progress: int = Field(ge=0, le=100)


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int
    limit: int
    total: int
    pages: int


class JobListResponse(BaseModel):
    """Paginated job list response."""
    jobs: List[JobResponse]
    pagination: PaginationMeta
