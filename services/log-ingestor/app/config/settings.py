"""Configuration for the log-ingestor service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven settings (prefix ``INGEST_``)."""

    app_name: str = "CloudNetSleuth Log Ingestor"
    environment: str = "dev"
    log_level: str = "INFO"
    max_events: int = 50_000
    max_batch_lines: int = 1000
    max_line_length: int = 4096

    model_config = SettingsConfigDict(env_prefix="INGEST_", env_file=".env", extra="ignore")


settings = Settings()
