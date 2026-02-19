"""Job Entity."""
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from video_processor_shared.domain.value_objects import JobStatus
from video_processor_shared.domain.exceptions import InvalidJobTransitionError


class Job:
    """Job Entity - Represents a video processing job."""

    def __init__(
        self,
        id: UUID,
        video_id: UUID,
        user_id: UUID,
        status: JobStatus = JobStatus.PENDING,
        progress: int = 0,
        frame_count: Optional[int] = None,
        zip_path: Optional[str] = None,
        zip_size: Optional[int] = None,
        error_message: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.video_id = video_id
        self.user_id = user_id
        self.status = status
        self.progress = progress
        self.frame_count = frame_count
        self.zip_path = zip_path
        self.zip_size = zip_size
        self.error_message = error_message
        self.started_at = started_at
        self.completed_at = completed_at
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)

    def start(self) -> None:
        self._transition_to(JobStatus.PROCESSING)
        self.started_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def complete(self, frame_count: int, zip_path: str, zip_size: int) -> None:
        self._transition_to(JobStatus.COMPLETED)
        self.frame_count = frame_count
        self.zip_path = zip_path
        self.zip_size = zip_size
        self.progress = 100
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def fail(self, error_message: str) -> None:
        self._transition_to(JobStatus.FAILED)
        self.error_message = error_message
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def cancel(self) -> None:
        self._transition_to(JobStatus.CANCELLED)
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def update_progress(self, progress: int) -> None:
        if not 0 <= progress <= 100:
            raise ValueError("Progress must be between 0 and 100")
        self.progress = progress
        self.updated_at = datetime.now(UTC)

    def _transition_to(self, new_status: JobStatus) -> None:
        if not self.status.can_transition_to(new_status):
            raise InvalidJobTransitionError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status

    @property
    def is_terminal(self) -> bool:
        return self.status.is_terminal

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Job):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
