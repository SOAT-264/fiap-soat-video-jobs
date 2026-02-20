"""SQLAlchemy Models for Job Service."""
from uuid import UUID

from sqlalchemy import Column, String, Integer, Text, BigInteger, Enum
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from job_service.infrastructure.adapters.output.persistence.database import Base
from video_processor_shared.domain.value_objects import JobStatus


class JobModel(Base):
    """SQLAlchemy model for jobs table."""
    
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    video_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    status = Column(
        Enum(JobStatus, name="job_status", create_type=False),
        nullable=False,
        default=JobStatus.PENDING,
        index=True,
    )
    progress = Column(Integer, nullable=False, default=0)
    frame_count = Column(Integer, nullable=True)
    zip_path = Column(String(500), nullable=True)
    zip_size = Column(BigInteger, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
