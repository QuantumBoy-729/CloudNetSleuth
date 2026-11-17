"""Prometheus metrics for the log-ingestor."""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY_SECONDS = Histogram("http_request_latency_seconds", "HTTP request latency", ["endpoint"])
ERROR_COUNT = Counter("http_error_total", "Total application errors", ["endpoint"])

LOG_EVENTS_TOTAL = Counter(
    "cns_log_events_total",
    "Parsed log events by service, level and failure category",
    ["service", "level", "category"],
)
LOG_PARSE_FAILURES_TOTAL = Counter("cns_log_parse_failures_total", "Lines that could not be parsed")

metrics_router = APIRouter(tags=["metrics"])


@metrics_router.get("/metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
