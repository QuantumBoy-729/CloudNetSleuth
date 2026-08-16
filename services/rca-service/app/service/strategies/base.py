"""Strategy contracts for RCA analysis."""

from abc import ABC, abstractmethod
from collections.abc import Callable

from app.models.rca import RootCause, ServiceMetric
from app.service.strategies.statistics import min_max_normalize

LATENCY_WEIGHT = 0.7
THROUGHPUT_WEIGHT = 0.3


class AnalysisStrategy(ABC):
    """A pluggable ranking algorithm for suspected root causes."""

    name: str

    @abstractmethod
    def analyze(self, metrics: list[ServiceMetric], top_k: int) -> list[RootCause]:
        """Rank ``metrics`` by likelihood of being the root cause.

        Args:
            metrics: Observed per-service metrics, at least two entries.
            top_k: Maximum number of causes to return.

        Returns:
            Causes sorted by descending correlation score, truncated to
            ``top_k``.
        """
        raise NotImplementedError


class CorrelationStrategy(AnalysisStrategy):
    """Shared scoring for strategies that differ only in their coefficient.

    Two population-level coefficients are computed across the submitted
    services: latency against error rate, and throughput against error rate.
    Those coefficients weight per-service features that have been min-max
    normalised first, so the latency and throughput terms stay on a comparable
    scale instead of one silently dominating the sum.

    Overall complexity is O(n log n) for ``n`` services, dominated by the final
    sort (and by rank transforms in rank-based subclasses).
    """

    #: Coefficient function applied to each (feature, error_rate) pair.
    coefficient: Callable[[list[float], list[float]], float]

    def analyze(self, metrics: list[ServiceMetric], top_k: int) -> list[RootCause]:
        """Rank ``metrics`` using this strategy's correlation coefficient."""
        error_rates = [item.error_rate for item in metrics]
        latencies = [item.latency_ms for item in metrics]
        throughputs = [item.throughput_rps for item in metrics]

        latency_corr = self.coefficient(latencies, error_rates)
        throughput_corr = self.coefficient(throughputs, error_rates)

        # A service is more suspicious when it carries a high error rate and a
        # low share of traffic, so the throughput signal is inverted.
        error_signal = min_max_normalize(error_rates)
        starvation_signal = [1.0 - value for value in min_max_normalize(throughputs)]

        confidence = round(
            min(
                1.0,
                abs(latency_corr) * LATENCY_WEIGHT + abs(throughput_corr) * THROUGHPUT_WEIGHT,
            ),
            4,
        )

        causes = [
            RootCause(
                service_name=item.service_name,
                correlation_score=round(
                    error_signal[index] * abs(latency_corr)
                    + starvation_signal[index] * abs(throughput_corr),
                    4,
                ),
                confidence=confidence,
            )
            for index, item in enumerate(metrics)
        ]

        causes.sort(key=lambda cause: cause.correlation_score, reverse=True)
        return causes[:top_k]
