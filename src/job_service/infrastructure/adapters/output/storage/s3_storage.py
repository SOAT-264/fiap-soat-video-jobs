"""S3 Storage adapter for video files."""
from typing import Optional, BinaryIO
import aioboto3

from job_service.infrastructure.config import get_settings

settings = get_settings()


class S3StorageAdapter:
    """S3/MinIO storage adapter for video and output files."""

    def __init__(self):
        self._session = aioboto3.Session()

    async def download_file(self, bucket: str, key: str, destination: str) -> str:
        """Download a file from S3."""
        async with self._session.client(
            "s3",
            endpoint_url=settings.AWS_ENDPOINT_URL or None,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION,
        ) as s3:
            await s3.download_file(bucket, key, destination)
        return destination

    async def upload_file(
        self, file_path: str, bucket: str, key: str, content_type: Optional[str] = None
    ) -> str:
        """Upload a file to S3."""
        extra_args = {"ContentType": content_type} if content_type else {}
        async with self._session.client(
            "s3",
            endpoint_url=settings.AWS_ENDPOINT_URL or None,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION,
        ) as s3:
            await s3.upload_file(file_path, bucket, key, ExtraArgs=extra_args)
        return key

    async def upload_fileobj(
        self, fileobj: BinaryIO, bucket: str, key: str, content_type: Optional[str] = None
    ) -> str:
        """Upload a file object to S3."""
        extra_args = {"ContentType": content_type} if content_type else {}
        async with self._session.client(
            "s3",
            endpoint_url=settings.AWS_ENDPOINT_URL or None,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION,
        ) as s3:
            await s3.upload_fileobj(fileobj, bucket, key, ExtraArgs=extra_args)
        return key

    async def generate_presigned_url(
        self, bucket: str, key: str, expires_in: int = 3600
    ) -> str:
        """Generate a presigned URL for download."""
        async with self._session.client(
            "s3",
            endpoint_url=settings.AWS_ENDPOINT_URL or None,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION,
        ) as s3:
            url = await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        return url

    async def delete_file(self, bucket: str, key: str) -> None:
        """Delete a file from S3."""
        async with self._session.client(
            "s3",
            endpoint_url=settings.AWS_ENDPOINT_URL or None,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION,
        ) as s3:
            await s3.delete_object(Bucket=bucket, Key=key)
