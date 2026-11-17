"""Pydantic models for log ingestion."""

from datetime import datetime

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """A batch of raw log lines (JSON objects or plain text)."""

    lines: list[str] = Field(min_length=1)


class IngestResponse(BaseModel):
    accepted: int
    rejected: int


class LogEvent(BaseModel):
    """A parsed and classified log event."""

    timestamp: datetime
    service: str
    level: str
    message: str
    category: str
    latency_ms: float | None = None
    received_at: float = 0.0


class ServiceSummary(BaseModel):
    """Aggregated view of one service over a time window."""

    service: str
    total: int
    errors: int
    error_rate: float
    avg_latency_ms: float
    throughput_rps: float
    by_category: dict[str, int]


class SummaryResponse(BaseModel):
    window_seconds: int
    services: list[ServiceSummary]
