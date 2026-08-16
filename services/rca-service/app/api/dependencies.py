"""Dependency-injection wiring for the API layer.

The service and its collaborators are stateless and safe to share, so they are
constructed once at import time and handed out by reference. Tests override
:func:`get_rca_service` through ``app.dependency_overrides``.
"""

from functools import lru_cache

from app.repository.strategy_repository import StrategyConfigRepository
from app.service.rca_service import RCAService
from app.service.strategies.registry import StrategyRegistry


@lru_cache(maxsize=1)
def _build_rca_service() -> RCAService:
    return RCAService(
        repository=StrategyConfigRepository(),
        registry=StrategyRegistry(),
    )


def get_rca_service() -> RCAService:
    """Return the shared :class:`RCAService` instance."""
    return _build_rca_service()
