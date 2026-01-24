"""API Routes for Job Service."""
from job_service.infrastructure.adapters.input.api.routes.job_routes import router as job_router
from job_service.infrastructure.adapters.input.api.routes.health_routes import router as health_router

__all__ = ["job_router", "health_router"]
