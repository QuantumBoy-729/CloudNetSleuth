"""Pydantic models for RCA requests and responses."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_SERVICES_PER_REQUEST = 1000


class ServiceMetric(BaseModel):
    """A single service's observed metrics at analysis time."""

    model_config = ConfigDict(extra="forbid")

    service_name: str = Field(min_length=1, max_length=128)
    error_rate: float = Field(ge=0.0, le=1.0, description="Failed requests as a 0-1 fraction.")
    latency_ms: float = Field(ge=0.0, description="Observed latency in milliseconds.")
    throughput_rps: float = Field(ge=0.0, description="Observed throughput in requests/second.")


class RCARequest(BaseModel):
    """An analysis request covering two or more services."""

    model_config = ConfigDict(extra="forbid")

    metrics: list[ServiceMetric] = Field(
        min_length=2,
        max_length=MAX_SERVICES_PER_REQUEST,
    )
    strategy: str | None = Field(
        default=None,
        max_length=64,
        description="Analysis strategy name. Falls back to the configured default.",
    )

    @model_validator(mode="after")
    def validate_variance(self) -> "RCARequest":
        """Reject payloads whose error rates are constant.

        Correlation is undefined without variance in the target series, so the
        request is rejected up front rather than silently scoring every service
        identically.
        """
        error_rates = {item.error_rate for item in self.metrics}
        if len(error_rates) < 2:
            raise ValueError("error_rate must vary across services for correlation analysis")
        return self


class RootCause(BaseModel):
    """A single ranked suspect."""

    service_name: str
    correlation_score: float
    confidence: float = Field(ge=0.0, le=1.0)


class RCAResponse(BaseModel):
    """The ranked outcome of an analysis."""

    top_causes: list[RootCause]
    strategy: str = Field(description="Strategy that produced this ranking.")
    analyzed_services: int = Field(ge=0, description="Number of services considered.")


class StrategyListResponse(BaseModel):
    """The strategies this deployment permits."""

    strategies: list[str]
    default: str
