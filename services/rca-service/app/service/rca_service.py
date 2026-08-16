"""Service layer for RCA execution."""

import logging
import time

from app.config.metrics import RCA_ANALYSIS_COUNT, RCA_ANALYSIS_DURATION_SECONDS
from app.models.rca import RCARequest, RCAResponse, StrategyListResponse
from app.repository.strategy_repository import StrategyConfigRepository
from app.service.strategies.registry import StrategyRegistry, UnknownStrategyError

logger = logging.getLogger(__name__)


class RCAService:
    """Coordinates strategy selection and execution."""

    def __init__(
        self,
        repository: StrategyConfigRepository | None = None,
        registry: StrategyRegistry | None = None,
    ) -> None:
        """Initialise the service.

        Args:
            repository: Source of strategy selection policy.
            registry: Source of strategy implementations.
        """
        self._repository = repository or StrategyConfigRepository()
        self._registry = registry or StrategyRegistry()

    def analyze(self, payload: RCARequest) -> RCAResponse:
        """Run an analysis over ``payload``.

        Args:
            payload: The validated request.

        Returns:
            The ranked causes together with the strategy that produced them.

        Raises:
            UnknownStrategyError: If the requested strategy is unregistered or
                disabled in this deployment.
        """
        name = payload.strategy or self._repository.get_default_strategy_name()
        if not self._repository.is_enabled(name):
            enabled = ", ".join(self._repository.list_enabled_strategy_names())
            raise UnknownStrategyError(f"strategy '{name}' is not enabled; enabled: {enabled}")

        strategy = self._registry.get(name)
        start = time.perf_counter()
        try:
            causes = strategy.analyze(
                metrics=payload.metrics,
                top_k=self._repository.get_top_k_causes(),
            )
        except Exception:
            RCA_ANALYSIS_COUNT.labels(strategy=strategy.name, outcome="failure").inc()
            logger.exception("RCA analysis failed", extra={"strategy": strategy.name})
            raise
        finally:
            RCA_ANALYSIS_DURATION_SECONDS.labels(strategy=strategy.name).observe(
                time.perf_counter() - start
            )

        RCA_ANALYSIS_COUNT.labels(strategy=strategy.name, outcome="success").inc()
        logger.info(
            "RCA analysis completed",
            extra={"strategy": strategy.name, "analyzed_services": len(payload.metrics)},
        )
        return RCAResponse(
            top_causes=causes,
            strategy=strategy.name,
            analyzed_services=len(payload.metrics),
        )

    def list_strategies(self) -> StrategyListResponse:
        """Return the strategies that are both registered and enabled."""
        registered = set(self._registry.names())
        enabled = [
            name for name in self._repository.list_enabled_strategy_names() if name in registered
        ]
        return StrategyListResponse(
            strategies=sorted(enabled),
            default=self._repository.get_default_strategy_name(),
        )
