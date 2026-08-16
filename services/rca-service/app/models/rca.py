"""Pydantic models for RCA requests and responses."""

from pydantic import BaseModel, Field, model_validator


class ServiceMetric(BaseModel):
    service_name: str = Field(min_length=1, max_length=128)
    error_rate: float = Field(ge=0.0)
    latency_ms: float = Field(ge=0.0)
    throughput_rps: float = Field(ge=0.0)


class RCARequest(BaseModel):
    metrics: list[ServiceMetric] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_variance(self) -> "RCARequest":
        error_rates = [item.error_rate for item in self.metrics]
        if len(set(error_rates)) < 2:
            raise ValueError("error_rate must vary across services for correlation analysis")
        return self


class RootCause(BaseModel):
    service_name: str
    correlation_score: float
    confidence: float = Field(ge=0.0, le=1.0)


class RCAResponse(BaseModel):
    top_causes: list[RootCause]

