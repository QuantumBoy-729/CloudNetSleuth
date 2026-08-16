"""RCA router."""

import time

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.rca import RCARequest, RCAResponse
from app.service.rca_service import RCAService

rca_router = APIRouter(prefix="/api/v1", tags=["rca"])


def get_rca_service() -> RCAService:
    return RCAService()


@rca_router.post("/analyze", response_model=RCAResponse)
async def analyze(
    payload: RCARequest,
    service: RCAService = Depends(get_rca_service),
) -> RCAResponse:
    start = time.perf_counter()
    try:
        result = service.analyze(payload=payload)
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    finally:
        from app.config.metrics import REQUEST_LATENCY_SECONDS

        REQUEST_LATENCY_SECONDS.labels(endpoint="/api/v1/analyze").observe(
            time.perf_counter() - start
        )

