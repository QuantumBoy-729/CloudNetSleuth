"""Log ingestion and query endpoints."""

import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.config.metrics import REQUEST_LATENCY_SECONDS
from app.config.settings import settings
from app.models.log import IngestRequest, IngestResponse, LogEvent, SummaryResponse
from app.service.ingest_service import IngestService

logs_router = APIRouter(prefix="/api/v1", tags=["logs"])


def get_ingest_service(request: Request) -> IngestService:
    """Dependency: the app-scoped service (holds the shared event store)."""
    return request.app.state.ingest_service


@logs_router.post("/logs", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_logs(
    payload: IngestRequest, service: IngestService = Depends(get_ingest_service)
) -> IngestResponse:
    """Ingest a batch of raw log lines."""
    start = time.perf_counter()
    try:
        if len(payload.lines) > settings.max_batch_lines:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "batch too large")
        if any(len(line) > settings.max_line_length for line in payload.lines):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "line too long")
        return service.ingest(payload.lines)
    finally:
        REQUEST_LATENCY_SECONDS.labels(endpoint="/api/v1/logs").observe(time.perf_counter() - start)


@logs_router.get("/summary", response_model=SummaryResponse)
async def summary(
    window_seconds: int = Query(60, ge=1, le=3600),
    service: IngestService = Depends(get_ingest_service),
) -> SummaryResponse:
    """Per-service aggregates over a sliding window."""
    return service.summary(window_seconds)


@logs_router.get("/events", response_model=list[LogEvent])
async def events(
    limit: int = Query(50, ge=1, le=500),
    service_name: str | None = Query(None, alias="service"),
    service: IngestService = Depends(get_ingest_service),
) -> list[LogEvent]:
    """Most recent events, newest first."""
    return service.recent(limit, service_name)
