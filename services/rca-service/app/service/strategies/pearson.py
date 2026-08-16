"""Pearson-correlation RCA strategy."""

from app.service.strategies.base import CorrelationStrategy
from app.service.strategies.statistics import pearson_coefficient


class PearsonCorrelationStrategy(CorrelationStrategy):
    """Ranks services using linear correlation against error rate.

    Appropriate when the relationship between latency/throughput and errors is
    expected to be proportional. Sensitive to outliers — a single extreme
    service can dominate the coefficient.
    """

    name = "pearson"
    coefficient = staticmethod(pearson_coefficient)
