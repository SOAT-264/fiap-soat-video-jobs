"""Input adapters."""
from job_service.infrastructure.adapters.input.api import app
from job_service.infrastructure.adapters.input.worker import process_video_task

__all__ = ["app", "process_video_task"]
