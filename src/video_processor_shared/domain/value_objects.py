from enum import Enum


class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    def can_transition_to(self, new_status: "JobStatus") -> bool:
        transitions = {
            JobStatus.PENDING: {JobStatus.PROCESSING, JobStatus.CANCELLED},
            JobStatus.PROCESSING: {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED},
            JobStatus.COMPLETED: set(),
            JobStatus.FAILED: set(),
            JobStatus.CANCELLED: set(),
        }
        return new_status in transitions[self]

    @property
    def is_terminal(self) -> bool:
        return self in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
