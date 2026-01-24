"""SQLAlchemy Models for Job Service."""
from datetime import datetime
from uuid import UUID as PyUUID

from sqlalchemy import Column, String, Integer, DateTime, Text, BigInteger, Enum
from sqlalchemy.dialects.postgresql import UUID

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
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
