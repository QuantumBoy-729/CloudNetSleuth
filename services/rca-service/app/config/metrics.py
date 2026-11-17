"""Prometheus metrics wiring."""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

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

ACTIVE_FINDINGS = Gauge(
    "cns_rca_finding_active",
    "Rules-engine findings currently active (value = signal value)",
    ["rule", "service", "severity"],
)
TOP_CAUSE_SCORE = Gauge(
    "cns_rca_top_cause_score",
    "Correlation-based root-cause score per suspected service",
    ["service"],
)
DIAGNOSIS_RUNS = Counter("cns_rca_diagnosis_runs_total", "Background diagnosis runs", ["outcome"])

metrics_router = APIRouter(tags=["metrics"])


@metrics_router.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

