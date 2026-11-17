"""Configuration for the service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven settings (prefix ``RCA_``)."""

    app_name: str = "CloudNetSleuth RCA Service"
    environment: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "INFO"
    ingestor_url: str = "http://log-ingestor:8081"
    ingestor_timeout_seconds: float = 3.0
    window_seconds: int = 60
    # Background diagnosis loop (feeds Prometheus/Grafana). 0 disables it.
    poll_interval_seconds: float = 0.0
    rules_path: str = ""

    model_config = SettingsConfigDict(
        env_prefix="RCA_",
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
