"""Application entrypoint for the RCA service."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.responses import Response

from app.api.routers.health import health_router
from app.api.routers.rca import rca_router
from app.config.logging import configure_logging
from app.config.metrics import ERROR_COUNT, REQUEST_COUNT, metrics_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    logging.getLogger(__name__).info("Service startup")
    yield
    logging.getLogger(__name__).info("Service shutdown")


app = FastAPI(
    title="CloudNetSleuth RCA Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(rca_router)


@app.middleware("http")
async def http_metrics_middleware(request: Request, call_next) -> Response:
    endpoint = request.url.path
    method = request.method
    try:
        response = await call_next(request)
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status=str(response.status_code),
        ).inc()
        return response
    except Exception:
        ERROR_COUNT.labels(endpoint=endpoint).inc()
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status="500").inc()
        raise
