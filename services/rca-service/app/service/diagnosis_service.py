"""Combines the rules engine with correlation-based ranking."""

from app.models.diagnosis import DiagnosisResponse, ServiceSummary
from app.models.rca import RCARequest, RootCause, ServiceMetric
from app.service.rca_service import RCAService
from app.service.rules.engine import RulesEngine


class DiagnosisService:
    """Evaluates rules and, when the data allows, ranks suspects statistically."""

    def __init__(self, engine: RulesEngine, rca_service: RCAService | None = None) -> None:
        self._engine = engine
        self._rca = rca_service or RCAService()

    def diagnose(self, summaries: list[ServiceSummary], window_seconds: int) -> DiagnosisResponse:
        """Return rule findings plus correlation-ranked top causes."""
        return DiagnosisResponse(
            window_seconds=window_seconds,
            findings=self._engine.evaluate(summaries),
            top_causes=self._rank(summaries),
        )

    def _rank(self, summaries: list[ServiceSummary]) -> list[RootCause]:
        if len(summaries) < 2:
            return []
        request_metrics = [
            ServiceMetric(
                service_name=s.service,
                error_rate=s.error_rate,
                latency_ms=s.avg_latency_ms,
                throughput_rps=s.throughput_rps,
            )
            for s in summaries
        ]
        try:
            return self._rca.analyze(RCARequest(metrics=request_metrics)).top_causes
        except ValueError:
            # Not enough variance across services for a meaningful correlation.
            return []
