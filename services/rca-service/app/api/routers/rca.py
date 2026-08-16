"""RCA router."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_rca_service
from app.config.settings import settings
from app.models.rca import RCARequest, RCAResponse, StrategyListResponse
from app.service.rca_service import RCAService
from app.service.strategies.registry import UnknownStrategyError

rca_router = APIRouter(prefix=settings.api_prefix, tags=["rca"])


@rca_router.post("/analyze", response_model=RCAResponse)
async def analyze(
    payload: RCARequest,
    service: RCAService = Depends(get_rca_service),
) -> RCAResponse:
    """Rank the submitted services by likelihood of being the root cause.

    Raises:
        HTTPException: 422 if the requested strategy is unknown or disabled.
    """
    try:
        return service.analyze(payload=payload)
    except UnknownStrategyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@rca_router.get("/strategies", response_model=StrategyListResponse)
async def list_strategies(
    service: RCAService = Depends(get_rca_service),
) -> StrategyListResponse:
    """List the analysis strategies this deployment permits."""
    return service.list_strategies()
