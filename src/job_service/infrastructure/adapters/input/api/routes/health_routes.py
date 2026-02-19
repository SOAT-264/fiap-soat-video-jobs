"""Health check routes."""
from datetime import UTC, datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from job_service.infrastructure.adapters.output.persistence.database import get_session
from job_service.infrastructure.adapters.output.cache.redis_client import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "job-service",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> Dict[str, Any]:
    """Readiness check - verifies all dependencies are available."""
    services = {}
    
    # Check database
    try:
        await db.execute("SELECT 1")
        services["database"] = {"status": "connected"}
    except Exception as e:
        services["database"] = {"status": "disconnected", "error": str(e)}
    
    # Check Redis
    try:
        await redis.ping()
        services["redis"] = {"status": "connected"}
    except Exception as e:
        services["redis"] = {"status": "disconnected", "error": str(e)}
    
    all_healthy = all(s.get("status") == "connected" for s in services.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "service": "job-service",
        "timestamp": datetime.now(UTC).isoformat(),
        "services": services,
    }
