"""Data access for analysis-strategy configuration.

This layer owns *which* strategies the deployment permits and which one is the
default. It deliberately knows nothing about strategy implementations, keeping
the dependency direction service -> repository. Backing this with a database or
config service later means changing only this class.
"""

from app.config.settings import Settings
from app.config.settings import settings as default_settings


class StrategyConfigRepository:
    """Reads strategy selection policy from configuration."""

    def __init__(self, config: Settings | None = None) -> None:
        """Initialise the repository.

        Args:
            config: Settings source. Defaults to the process-wide settings.
        """
        self._config = config or default_settings

    def get_default_strategy_name(self) -> str:
        """Return the strategy name to use when a request does not specify one."""
        return self._config.default_strategy.strip().lower()

    def list_enabled_strategy_names(self) -> tuple[str, ...]:
        """Return the strategy names this deployment permits."""
        return self._config.enabled_strategy_names

    def is_enabled(self, name: str) -> bool:
        """Return whether ``name`` is permitted by the current configuration.

        Args:
            name: Strategy identifier, matched case-insensitively.
        """
        return name.strip().lower() in self.list_enabled_strategy_names()

    def get_top_k_causes(self) -> int:
        """Return how many ranked causes an analysis should return."""
        return self._config.top_k_causes
