"""Message publisher for job events."""
import json
from typing import Any, Dict

from redis.asyncio import Redis

from job_service.infrastructure.adapters.output.cache import get_redis
from job_service.infrastructure.config import get_settings

settings = get_settings()


class EventPublisher:
    """Publishes domain events to message queue."""

    def __init__(self, redis: Redis):
        self._redis = redis

    async def publish_job_started(self, job_id: str, video_id: str, user_id: str) -> None:
        """Publish job started event."""
        await self._publish(
            "job.started",
            {
                "job_id": job_id,
                "video_id": video_id,
                "user_id": user_id,
                "event_type": "JOB_STARTED",
            },
        )

    async def publish_job_completed(
        self,
        job_id: str,
        video_id: str,
        user_id: str,
        frame_count: int,
        zip_path: str,
    ) -> None:
        """Publish job completed event."""
        await self._publish(
            "job.completed",
            {
                "job_id": job_id,
                "video_id": video_id,
                "user_id": user_id,
                "frame_count": frame_count,
                "zip_path": zip_path,
                "event_type": "JOB_COMPLETED",
            },
        )

    async def publish_job_failed(
        self, job_id: str, video_id: str, user_id: str, error_message: str
    ) -> None:
        """Publish job failed event."""
        await self._publish(
            "job.failed",
            {
                "job_id": job_id,
                "video_id": video_id,
                "user_id": user_id,
                "error_message": error_message,
                "event_type": "JOB_FAILED",
            },
        )

    async def _publish(self, channel: str, message: Dict[str, Any]) -> None:
        """Publish message to Redis pub/sub channel."""
        await self._redis.publish(channel, json.dumps(message))
