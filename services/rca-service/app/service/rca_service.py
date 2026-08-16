"""Service layer for RCA execution."""

from app.config.metrics import ERROR_COUNT
from app.models.rca import RCARequest, RCAResponse
from app.repository.strategy_repository import StrategyRepository


class RCAService:
    def __init__(self, repository: StrategyRepository | None = None) -> None:
        self._repository = repository or StrategyRepository()

    def analyze(self, payload: RCARequest) -> RCAResponse:
        strategy = self._repository.get_default_strategy()
        try:
            return strategy.analyze(payload)
        except Exception:
            ERROR_COUNT.labels(endpoint="/api/v1/analyze").inc()
            raise

