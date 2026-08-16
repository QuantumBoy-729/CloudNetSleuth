"""Configuration for the service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CloudNetSleuth RCA Service"
    environment: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="RCA_",
        env_file=".env",
        extra="ignore",
    )


settings = Settings()

