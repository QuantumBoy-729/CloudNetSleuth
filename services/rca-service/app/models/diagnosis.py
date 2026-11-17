"""Models for log-summary driven diagnosis."""

from pydantic import BaseModel, Field

from app.models.rca import RootCause


class ServiceSummary(BaseModel):
    """Per-service aggregates as produced by the log-ingestor."""

    service: str = Field(min_length=1, max_length=128)
    total: int = Field(ge=0)
    errors: int = Field(ge=0)
    error_rate: float = Field(ge=0.0)
    avg_latency_ms: float = Field(ge=0.0)
    throughput_rps: float = Field(ge=0.0)
    by_category: dict[str, int] = Field(default_factory=dict)


class DiagnoseRequest(BaseModel):
    """Summaries to evaluate (used by POST /diagnose)."""

    services: list[ServiceSummary] = Field(min_length=1)


class Finding(BaseModel):
    """A rule that fired for a service, with its recommendation."""

    rule: str
    title: str
    service: str
    severity: str
    value: float
    threshold: float
    recommendation: str


class DiagnosisResponse(BaseModel):
    window_seconds: int
    findings: list[Finding]
    top_causes: list[RootCause]
