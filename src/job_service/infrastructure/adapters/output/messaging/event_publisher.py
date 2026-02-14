"""Message publisher for job events."""
import json
from typing import Any, Dict, Optional

import aioboto3
from redis.asyncio import Redis

from job_service.infrastructure.config import get_settings

settings = get_settings()


class EventPublisher:
    """Publishes domain events to message queue."""

    def __init__(self, redis: Optional[Redis] = None):
        self._redis = redis
        self._session = aioboto3.Session()

    async def publish_job_started(self, job_id: str, video_id: str, user_id: str) -> None:
        """Publish job started event."""
        await self._publish(
            "job.started",
            {
                "job_id": job_id,
                "video_id": video_id,
                "user_id": user_id,
                "event_type": "job_started",
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
                "event_type": "job_completed",
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
                "event_type": "job_failed",
            },
        )

    async def _publish(self, channel: str, message: Dict[str, Any]) -> None:
        """Publish message to SNS and optionally Redis pub/sub."""
        if settings.SNS_TOPIC_ARN:
            async with self._session.client(
                "sns",
                endpoint_url=settings.AWS_ENDPOINT_URL or None,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_DEFAULT_REGION,
            ) as sns:
                await sns.publish(
                    TopicArn=settings.SNS_TOPIC_ARN,
                    Message=json.dumps(message),
                    MessageAttributes={
                        "event_type": {
                            "DataType": "String",
                            "StringValue": message.get("event_type", channel),
                        }
                    },
                )

        if self._redis:
            await self._redis.publish(channel, json.dumps(message))
