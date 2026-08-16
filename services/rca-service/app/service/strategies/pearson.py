"""Pearson-correlation RCA strategy."""

from math import sqrt

from app.models.rca import RCARequest, RCAResponse, RootCause
from app.service.strategies.base import AnalysisStrategy


class PearsonCorrelationStrategy(AnalysisStrategy):
    """Ranks services by correlation between latency and error rate."""

    def analyze(self, payload: RCARequest) -> RCAResponse:
        items = payload.metrics
        latency = [item.latency_ms for item in items]
        error = [item.error_rate for item in items]
        throughput = [item.throughput_rps for item in items]

        latency_corr = self._pearson(latency, error)
        throughput_corr = self._pearson(throughput, error)

        causes: list[RootCause] = []
        for item in items:
            score = (item.error_rate * abs(latency_corr)) + (
                (1.0 / (1.0 + item.throughput_rps)) * abs(throughput_corr)
            )
            confidence = min(1.0, abs(latency_corr) * 0.7 + abs(throughput_corr) * 0.3)
            causes.append(
                RootCause(
                    service_name=item.service_name,
                    correlation_score=round(score, 4),
                    confidence=round(confidence, 4),
                )
            )

        causes.sort(key=lambda cause: cause.correlation_score, reverse=True)
        return RCAResponse(top_causes=causes[:3])

    def _pearson(self, x_values: list[float], y_values: list[float]) -> float:
        count = len(x_values)
        if count != len(y_values):
            raise ValueError("x and y values must have equal lengths")
        if count < 2:
            raise ValueError("at least two observations are required")

        x_mean = sum(x_values) / count
        y_mean = sum(y_values) / count

        num = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        den_x = sqrt(sum((x - x_mean) ** 2 for x in x_values))
        den_y = sqrt(sum((y - y_mean) ** 2 for y in y_values))
        den = den_x * den_y
        if den == 0:
            return 0.0
        return num / den

