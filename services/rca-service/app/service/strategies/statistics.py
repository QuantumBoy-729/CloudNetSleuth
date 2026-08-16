"""Pure statistical helpers shared by the analysis strategies."""

from math import sqrt


def pearson_coefficient(x_values: list[float], y_values: list[float]) -> float:
    """Return the Pearson product-moment correlation of two equal-length series.

    Measures the strength of a *linear* relationship. Runs in O(n) time and
    O(1) additional space.

    Args:
        x_values: First observation series.
        y_values: Second observation series.

    Returns:
        A coefficient in ``[-1.0, 1.0]``, or ``0.0`` when either series has
        zero variance and the correlation is therefore undefined.

    Raises:
        ValueError: If the series differ in length or hold fewer than two
            observations.
    """
    count = len(x_values)
    if count != len(y_values):
        raise ValueError("x and y values must have equal lengths")
    if count < 2:
        raise ValueError("at least two observations are required")

    x_mean = sum(x_values) / count
    y_mean = sum(y_values) / count

    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values, strict=True))
    denominator = sqrt(sum((x - x_mean) ** 2 for x in x_values)) * sqrt(
        sum((y - y_mean) ** 2 for y in y_values)
    )
    if denominator == 0:
        return 0.0
    return numerator / denominator


def rank(values: list[float]) -> list[float]:
    """Return fractional ranks for ``values``, averaging ties.

    Runs in O(n log n) time, dominated by the sort.

    Args:
        values: The observations to rank.

    Returns:
        Ranks in the original ordering, starting at 1.0. Tied observations
        share the mean of the ranks they span, which keeps rank-based
        correlations unbiased.
    """
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)

    position = 0
    while position < len(order):
        end = position
        while end + 1 < len(order) and values[order[end + 1]] == values[order[position]]:
            end += 1
        # Ranks are 1-based; average the span [position, end] across ties.
        shared_rank = (position + end) / 2.0 + 1.0
        for index in order[position : end + 1]:
            ranks[index] = shared_rank
        position = end + 1

    return ranks


def min_max_normalize(values: list[float]) -> list[float]:
    """Scale ``values`` onto ``[0.0, 1.0]``.

    Args:
        values: The observations to scale.

    Returns:
        The scaled series, or all ``0.5`` when every observation is identical
        and no ordering information exists to preserve.
    """
    if not values:
        return []
    lowest = min(values)
    highest = max(values)
    if highest == lowest:
        return [0.5] * len(values)
    span = highest - lowest
    return [(value - lowest) / span for value in values]
