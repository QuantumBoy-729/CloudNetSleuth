"""Spearman rank-correlation RCA strategy."""

from app.service.strategies.base import CorrelationStrategy
from app.service.strategies.statistics import pearson_coefficient, rank


def spearman_coefficient(x_values: list[float], y_values: list[float]) -> float:
    """Return the Spearman rank correlation of two equal-length series.

    Equivalent to the Pearson coefficient computed over fractional ranks, which
    captures any *monotonic* relationship rather than only a linear one and is
    far less sensitive to outliers. Runs in O(n log n) time.

    Args:
        x_values: First observation series.
        y_values: Second observation series.

    Returns:
        A coefficient in ``[-1.0, 1.0]``.

    Raises:
        ValueError: If the series differ in length or hold fewer than two
            observations.
    """
    if len(x_values) != len(y_values):
        raise ValueError("x and y values must have equal lengths")
    return pearson_coefficient(rank(x_values), rank(y_values))


class SpearmanCorrelationStrategy(CorrelationStrategy):
    """Ranks services using monotonic rank correlation against error rate.

    Preferred over :class:`~app.service.strategies.pearson.PearsonCorrelationStrategy`
    when one service is a severe outlier, or when the relationship is
    consistently directional but not proportional.
    """

    name = "spearman"
    coefficient = staticmethod(spearman_coefficient)
