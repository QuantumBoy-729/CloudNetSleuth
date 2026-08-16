"""Configuration for the service.

All values are overridable through ``RCA_``-prefixed environment variables so
that nothing operational is hardcoded in the image.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from the environment.

    Attributes:
        app_name: Human readable service name, surfaced in OpenAPI metadata.
        app_version: Version reported by OpenAPI and the readiness endpoint.
        environment: Deployment environment identifier (``dev``, ``production``).
        host: Bind address used by the local uvicorn entrypoint.
        port: Bind port used by the local uvicorn entrypoint.
        log_level: Root log level.
        api_prefix: Prefix applied to all versioned API routes.
        default_strategy: Name of the analysis strategy used when a request
            does not select one explicitly.
        enabled_strategies: Comma-separated allowlist of selectable strategies.
        top_k_causes: Number of ranked causes returned by an analysis.
    """

    app_name: str = "CloudNetSleuth RCA Service"
    app_version: str = "1.1.0"
    environment: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    default_strategy: str = "pearson"
    enabled_strategies: str = "pearson,spearman"
    top_k_causes: int = Field(default=3, ge=1, le=100)

    model_config = SettingsConfigDict(
        env_prefix="RCA_",
        env_file=".env",
        extra="ignore",
    )

    @property
    def enabled_strategy_names(self) -> tuple[str, ...]:
        """Return the enabled strategy names as a normalised tuple."""
        names = (name.strip().lower() for name in self.enabled_strategies.split(","))
        return tuple(name for name in names if name)


settings = Settings()
