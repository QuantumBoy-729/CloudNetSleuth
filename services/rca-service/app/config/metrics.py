"""Prometheus metrics wiring.

Endpoint labels always carry the *route template* (``/api/v1/analyze``) rather
than the raw request path, so metric cardinality stays bounded regardless of
how many distinct URLs are requested.
"""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.requests import Request

UNMATCHED_ROUTE = "unmatched"

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY_SECONDS = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)
ERROR_COUNT = Counter(
    "http_error_total",
    "Total HTTP responses that failed (5xx or unhandled exception)",
    ["endpoint"],
)
RCA_ANALYSIS_COUNT = Counter(
    "rca_analysis_total",
    "RCA analyses executed, by strategy and outcome",
    ["strategy", "outcome"],
)
RCA_ANALYSIS_DURATION_SECONDS = Histogram(
    "rca_analysis_duration_seconds",
    "Time spent inside an RCA strategy, excluding HTTP overhead",
    ["strategy"],
)

metrics_router = APIRouter(tags=["metrics"])


def route_template(request: Request) -> str:
    """Return the matched route template for ``request``.

    Falls back to :data:`UNMATCHED_ROUTE` for requests that never matched a
    route (404s and similar), which would otherwise create one label value per
    unique URL.
    """
    route = request.scope.get("route")
    path_format = getattr(route, "path_format", None) or getattr(route, "path", None)
    return path_format or UNMATCHED_ROUTE


@metrics_router.get("/metrics")
async def metrics() -> Response:
    """Expose the Prometheus exposition format."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
