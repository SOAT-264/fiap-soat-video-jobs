"""SQS Consumer for video processing jobs.

This module can be used in two ways:
1. As AWS Lambda handler (triggered by SQS)
2. As local poller for development with LocalStack
"""
import asyncio
import json
import os
from typing import Any, Dict, Tuple
from uuid import UUID

import aioboto3

from job_service.infrastructure.adapters.input.worker.video_processor_task import process_video_task
from job_service.application.use_cases.create_job import CreateJobUseCase
from job_service.infrastructure.adapters.output.persistence import get_session_context
from job_service.infrastructure.adapters.output.persistence.repositories import SQLAlchemyJobRepository


async def _resolve_job_payload(body: Dict[str, Any]) -> Tuple[str, str]:
    """Resolve job_id and s3_key from either job or video upload events."""
    if "job_id" in body and "s3_key" in body:
        return body["job_id"], body["s3_key"]

    if "video_id" not in body or "user_id" not in body or "filename" not in body:
        raise ValueError("Message missing job_id/s3_key or video upload fields")

    video_id = str(body["video_id"])
    user_id = str(body["user_id"])
    filename = str(body["filename"])
    _, ext = os.path.splitext(filename)
    if not ext:
        raise ValueError("Filename missing extension to build S3 key")

    s3_key = f"videos/{user_id}/{video_id}{ext.lower()}"

    async with get_session_context() as session:
        repository = SQLAlchemyJobRepository(session)
        use_case = CreateJobUseCase(repository)
        created = await use_case.execute(UUID(video_id), UUID(user_id))
        await session.commit()

    return str(created.id), s3_key


# Lambda handler for AWS
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler triggered by SQS.
    
    Processes video jobs from the queue and extracts frames.
    
    Args:
        event: SQS event containing Records
        context: Lambda context
    
    Returns:
        Response with processed job IDs
    """
    processed_jobs = []
    failed_jobs = []
    
    resolved_jobs: list[tuple[str, str]] = []

    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])

            # Handle SNS-wrapped messages (SQS subscribed to SNS)
            if "Message" in body:
                body = json.loads(body["Message"])

            job_id, video_key = asyncio.get_event_loop().run_until_complete(
                _resolve_job_payload(body)
            )
            resolved_jobs.append((job_id, video_key))
        except Exception as e:
            failed_jobs.append({
                "message_id": record.get("messageId"),
                "error": str(e),
            })

    for job_id, video_key in resolved_jobs:
        try:
            asyncio.get_event_loop().run_until_complete(
                process_video_task(job_id=job_id, video_key=video_key)
            )
            processed_jobs.append(job_id)
        except Exception as e:
            failed_jobs.append({
                "message_id": job_id,
                "error": str(e),
            })
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "processed": processed_jobs,
            "failed": failed_jobs,
        }),
    }


# Local SQS poller for development
class SQSJobConsumer:
    """Polls SQS queue for video processing jobs (local development)."""
    
    def __init__(
        self,
        queue_url: str | None = None,
        endpoint_url: str | None = None,
        region: str = "us-east-1",
    ):
        self._queue_url = (
            queue_url
            or os.getenv("SQS_JOB_QUEUE_URL")
            or os.getenv("SQS_QUEUE_URL")
        )
        self._endpoint_url = endpoint_url or os.getenv("AWS_ENDPOINT_URL")
        self._region = region
        self._session = aioboto3.Session()
        self._running = False
    
    async def start(self) -> None:
        """Start polling for messages."""
        self._running = True
        print(f"🚀 Starting SQS consumer for queue: {self._queue_url}", flush=True)
        
        while self._running:
            await self._poll_and_process()
    
    async def stop(self) -> None:
        """Stop polling."""
        self._running = False
        print("⏹️ SQS consumer stopped", flush=True)
    
    async def _poll_and_process(self) -> None:
        """Poll queue and process messages."""
        async with self._session.client(
            "sqs",
            endpoint_url=self._endpoint_url,
            region_name=self._region,
        ) as sqs:
            try:
                response = await sqs.receive_message(
                    QueueUrl=self._queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20,  # Long polling
                    AttributeNames=["All"],
                    MessageAttributeNames=["All"],
                )
                
                messages = response.get("Messages", [])
                if not messages:
                    return

                resolved: list[tuple[str, str, str]] = []
                for message in messages:
                    job_id, video_key = await self._resolve_message(message)
                    if job_id and video_key:
                        resolved.append((job_id, video_key, message["ReceiptHandle"]))

                for job_id, video_key, receipt_handle in resolved:
                    await self._process_resolved_job(sqs, job_id, video_key, receipt_handle)
                    
            except Exception as e:
                print(f"❌ Error polling SQS: {e}", flush=True)
                await asyncio.sleep(5)
    
    async def _resolve_message(self, message: Dict[str, Any]) -> tuple[str | None, str | None]:
        """Resolve a message into a job id and S3 key, creating a pending job if needed."""
        try:
            print(f"📥 Received message: {message.get('MessageId')}", flush=True)
            body = json.loads(message["Body"])

            # Handle SNS-wrapped messages
            if "Message" in body:
                body = json.loads(body["Message"])

            job_id, video_key = await _resolve_job_payload(body)
            return job_id, video_key
        except Exception as e:
            print(f"❌ Job resolve failed: {e}", flush=True)
            return None, None

    async def _process_resolved_job(
        self, sqs: Any, job_id: str, video_key: str, receipt_handle: str
    ) -> None:
        """Process a resolved job and delete the message on success."""
        try:
            print(f"📹 Processing job: {job_id} key={video_key}", flush=True)

            await process_video_task(job_id=job_id, video_key=video_key)

            await sqs.delete_message(
                QueueUrl=self._queue_url,
                ReceiptHandle=receipt_handle,
            )

            print(f"✅ Job completed: {job_id}", flush=True)
        except Exception as e:
            print(f"❌ Job failed: {e}", flush=True)
            # Message will return to queue after visibility timeout


# CLI entry point for local development
async def main():
    consumer = SQSJobConsumer()
    try:
        await consumer.start()
    except KeyboardInterrupt:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
