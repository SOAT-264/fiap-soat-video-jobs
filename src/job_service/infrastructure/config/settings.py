"""Application Settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVICE_NAME: str = "job-service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5434/job_db"
    REDIS_URL: str = "redis://localhost:6379/2"

    AWS_ENDPOINT_URL: str = ""
    PUBLIC_S3_ENDPOINT_URL: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_DEFAULT_REGION: str = "us-east-1"

    S3_INPUT_BUCKET: str = "video-uploads"
    S3_OUTPUT_BUCKET: str = "video-outputs"
    SQS_QUEUE_URL: str = ""
    SNS_TOPIC_ARN: str = ""

    AUTH_SERVICE_URL: str = "http://localhost:8001"
    VIDEO_SERVICE_URL: str = "http://localhost:8002"

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
