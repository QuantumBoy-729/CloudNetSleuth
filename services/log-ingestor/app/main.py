"""Application entrypoint for the log-ingestor service."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.responses import Response

from app.api.routers.health import health_router
from app.api.routers.logs import logs_router
from app.config.logging import configure_logging
from app.config.metrics import ERROR_COUNT, REQUEST_COUNT, metrics_router
from app.config.settings import settings
from app.repository.event_store import EventStore
from app.service.ingest_service import IngestService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup wiring and graceful shutdown logging."""
    configure_logging()
    app.state.ingest_service = IngestService(EventStore(settings.max_events))
    logging.getLogger(__name__).info("Service startup")
    yield
    logging.getLogger(__name__).info("Service shutdown")


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(logs_router)


@app.middleware("http")
async def http_metrics_middleware(request: Request, call_next) -> Response:
    """Count requests and unhandled errors."""
    endpoint = request.url.path
    try:
        response = await call_next(request)
    except Exception:
        ERROR_COUNT.labels(endpoint=endpoint).inc()
        REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status="500").inc()
        raise
    REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=str(response.status_code)).inc()
    return response
