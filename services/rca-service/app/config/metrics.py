"""Prometheus metrics wiring."""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY_SECONDS = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
)
ERROR_COUNT = Counter(
    "http_error_total",
    "Total application errors",
    ["endpoint"],
)

metrics_router = APIRouter(tags=["metrics"])


@metrics_router.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

