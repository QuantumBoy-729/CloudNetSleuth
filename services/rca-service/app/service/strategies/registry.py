"""Registry of available analysis strategies."""

from app.service.strategies.base import AnalysisStrategy
from app.service.strategies.pearson import PearsonCorrelationStrategy
from app.service.strategies.spearman import SpearmanCorrelationStrategy


class UnknownStrategyError(LookupError):
    """Raised when a requested strategy is not registered or not enabled."""


class StrategyRegistry:
    """Resolves strategy names to strategy instances.

    Strategies are stateless, so a single instance per name is shared. New
    algorithms are added by registering them here; nothing else in the service
    needs to change.
    """

    def __init__(self, strategies: list[AnalysisStrategy] | None = None) -> None:
        """Initialise the registry.

        Args:
            strategies: Strategy instances to register. Defaults to every
                strategy shipped with the service.
        """
        default: list[AnalysisStrategy] = [
            PearsonCorrelationStrategy(),
            SpearmanCorrelationStrategy(),
        ]
        chosen = default if strategies is None else strategies
        self._strategies: dict[str, AnalysisStrategy] = {item.name: item for item in chosen}

    def get(self, name: str) -> AnalysisStrategy:
        """Return the strategy registered under ``name``.

        Args:
            name: Strategy identifier, matched case-insensitively.

        Returns:
            The matching strategy instance.

        Raises:
            UnknownStrategyError: If no strategy is registered under ``name``.
        """
        try:
            return self._strategies[name.strip().lower()]
        except KeyError as exc:
            available = ", ".join(sorted(self._strategies))
            raise UnknownStrategyError(
                f"unknown analysis strategy '{name}'; available: {available}"
            ) from exc

    def names(self) -> tuple[str, ...]:
        """Return every registered strategy name, sorted."""
        return tuple(sorted(self._strategies))
