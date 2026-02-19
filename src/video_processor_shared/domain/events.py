from dataclasses import dataclass
from uuid import UUID


@dataclass
class JobCompletedEvent:
    job_id: UUID
    video_id: UUID
    user_id: UUID
    frame_count: int
    zip_path: str


@dataclass
class JobFailedEvent:
    job_id: UUID
    video_id: UUID
    user_id: UUID
    error_message: str
