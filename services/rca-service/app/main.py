"""Application entrypoint for the RCA service."""

import logging
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.responses import Response

from app.api.routers.health import health_router
from app.api.routers.rca import rca_router
from app.config.logging import configure_logging, request_id_var
from app.config.metrics import (
    ERROR_COUNT,
    REQUEST_COUNT,
    REQUEST_LATENCY_SECONDS,
    metrics_router,
    route_template,
)
from app.config.settings import settings
from app.config.state import service_state

REQUEST_ID_HEADER = "X-Request-ID"

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage startup and shutdown.

    Readiness is only reported once startup completes, so a pod is never sent
    traffic mid-initialisation.

    Note that draining is *not* handled here. Uvicorn closes its listening
    socket before running lifespan shutdown, so by this point the readiness
    endpoint is already unreachable (connections are refused, not answered with
    503) and in-flight requests have finished under uvicorn's
    ``--timeout-graceful-shutdown`` budget. The window that actually lets
    Kubernetes stop routing traffic is the ``preStop`` hook in the deployment,
    which runs *before* SIGTERM while the app is still serving normally.
    """
    configure_logging()
    service_state.mark_ready()
    logger.info("Service startup", extra={"environment": settings.environment})

    try:
        yield
    finally:
        service_state.mark_draining()
        logger.info("Service shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(rca_router)


@app.middleware("http")
async def observability_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Attach a request id and record latency, throughput and error metrics.

    This is the single place HTTP-level metrics are recorded, so every route —
    including unhandled failures — is covered exactly once.
    """
    request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
    token = request_id_var.set(request_id)
    start = time.perf_counter()
    method = request.method

    try:
        response = await call_next(request)
    except Exception:
        elapsed = time.perf_counter() - start
        # The route is resolved during routing, so it is available even here.
        endpoint = route_template(request)
        REQUEST_LATENCY_SECONDS.labels(method=method, endpoint=endpoint).observe(elapsed)
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status="500").inc()
        ERROR_COUNT.labels(endpoint=endpoint).inc()
        logger.exception("Unhandled request failure", extra={"endpoint": endpoint})
        raise
    else:
        elapsed = time.perf_counter() - start
        endpoint = route_template(request)
        REQUEST_LATENCY_SECONDS.labels(method=method, endpoint=endpoint).observe(elapsed)
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status=str(response.status_code),
        ).inc()
        if response.status_code >= 500:
            ERROR_COUNT.labels(endpoint=endpoint).inc()
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
    finally:
        request_id_var.reset(token)
