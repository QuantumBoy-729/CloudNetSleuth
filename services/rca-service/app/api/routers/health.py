"""Health, liveness and readiness routers."""

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from app.config.settings import settings
from app.config.state import service_state

health_router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Basic health payload."""

    status: str
    service: str
    version: str


@health_router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report that the process is running."""
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
    )


@health_router.get("/health/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    """Liveness probe.

    Succeeds for as long as the event loop can serve a request. A failure here
    means the process is wedged and should be restarted.
    """
    return HealthResponse(
        status="alive",
        service=settings.app_name,
        version=settings.app_version,
    )


@health_router.get(
    "/health/ready",
    response_model=HealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
async def readiness(response: Response) -> HealthResponse:
    """Readiness probe.

    Fails during startup and as soon as shutdown begins, so Kubernetes stops
    routing new traffic to a pod that is about to go away. Unlike liveness, a
    failure here must not restart the process.
    """
    if not service_state.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="draining" if service_state.shutting_down else "starting",
            service=settings.app_name,
            version=settings.app_version,
        )
    return HealthResponse(
        status="ready",
        service=settings.app_name,
        version=settings.app_version,
    )
