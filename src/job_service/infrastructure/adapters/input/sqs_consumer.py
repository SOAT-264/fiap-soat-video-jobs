"""SQS Consumer for video processing jobs.

This module can be used in two ways:
1. As AWS Lambda handler (triggered by SQS)
2. As local poller for development with LocalStack
"""
import asyncio
import json
import os
from typing import Any, Dict

import aioboto3

from job_service.infrastructure.adapters.input.worker.video_processor_task import process_video_task


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
    
    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])
            
            # Handle SNS-wrapped messages (SQS subscribed to SNS)
            if "Message" in body:
                body = json.loads(body["Message"])
            
            job_id = body["job_id"]
            video_key = body["s3_key"]
            
            # Run async task
            asyncio.get_event_loop().run_until_complete(
                process_video_task(job_id=job_id, video_key=video_key)
            )
            
            processed_jobs.append(job_id)
            
        except Exception as e:
            failed_jobs.append({
                "message_id": record.get("messageId"),
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
        self._queue_url = queue_url or os.getenv("SQS_JOB_QUEUE_URL")
        self._endpoint_url = endpoint_url or os.getenv("AWS_ENDPOINT_URL")
        self._region = region
        self._session = aioboto3.Session()
        self._running = False
    
    async def start(self) -> None:
        """Start polling for messages."""
        self._running = True
        print(f"🚀 Starting SQS consumer for queue: {self._queue_url}")
        
        while self._running:
            await self._poll_and_process()
    
    async def stop(self) -> None:
        """Stop polling."""
        self._running = False
        print("⏹️ SQS consumer stopped")
    
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
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=20,  # Long polling
                    AttributeNames=["All"],
                )
                
                for message in response.get("Messages", []):
                    await self._process_message(sqs, message)
                    
            except Exception as e:
                print(f"❌ Error polling SQS: {e}")
                await asyncio.sleep(5)
    
    async def _process_message(self, sqs: Any, message: Dict[str, Any]) -> None:
        """Process a single message."""
        receipt_handle = message["ReceiptHandle"]
        
        try:
            body = json.loads(message["Body"])
            
            # Handle SNS-wrapped messages
            if "Message" in body:
                body = json.loads(body["Message"])
            
            job_id = body["job_id"]
            video_key = body["s3_key"]
            
            print(f"📹 Processing job: {job_id}")
            
            await process_video_task(job_id=job_id, video_key=video_key)
            
            # Delete message on success
            await sqs.delete_message(
                QueueUrl=self._queue_url,
                ReceiptHandle=receipt_handle,
            )
            
            print(f"✅ Job completed: {job_id}")
            
        except Exception as e:
            print(f"❌ Job failed: {e}")
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
