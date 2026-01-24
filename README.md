# Job Service - fiap-soat-video-jobs

Microservice responsible for managing video processing jobs.

## Features

- **Job Management**: Create, list, and track video processing jobs
- **Video Processing**: Extract frames from videos using FFmpeg
- **Progress Tracking**: Real-time progress updates
- **Event Publishing**: Publishes job events (started, completed, failed)

## Architecture

```
src/job_service/
├── domain/            # Domain entities and exceptions
├── application/       # Use cases and ports
│   ├── ports/        # Input/Output interfaces
│   └── use_cases/    # Business logic
└── infrastructure/   # Adapters and config
    ├── adapters/
    │   ├── input/    # API routes, worker tasks
    │   └── output/   # Database, cache, storage
    └── config/       # Settings
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/health/ready` | Readiness check |
| GET | `/jobs` | List user jobs |
| GET | `/jobs/{job_id}` | Get job details |

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/2` |
| `AWS_ENDPOINT_URL` | S3/MinIO endpoint | - |
| `S3_INPUT_BUCKET` | Input videos bucket | `video-uploads` |
| `S3_OUTPUT_BUCKET` | Output frames bucket | `video-outputs` |

## Running Locally

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the service
uvicorn job_service.infrastructure.adapters.input.api.main:app --reload --port 8003

# Run with Docker
docker build -t job-service .
docker run -p 8003:8003 job-service
```

## Testing

```bash
pytest tests/ -v --cov=job_service
```

## Dependencies

- **Internal**: `video-processor-shared` (shared library)
- **External**: PostgreSQL, Redis, MinIO/S3
