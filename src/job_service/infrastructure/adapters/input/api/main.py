"""FastAPI Main Application for Job Service."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from job_service.infrastructure.config import get_settings
from job_service.infrastructure.adapters.input.api.routes.job_routes import router as job_router
from job_service.infrastructure.adapters.input.api.routes.health_routes import router as health_router
from job_service.infrastructure.adapters.output.cache import close_redis

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    yield
    # Shutdown
    await close_redis()


app = FastAPI(
    title="Job Service",
    description="Video processing job management microservice",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(job_router)
app.mount("/metrics", make_asgi_app())


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "version": "0.1.0",
        "status": "running",
    }
