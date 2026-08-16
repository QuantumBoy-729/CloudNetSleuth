import pytest

from app.service.strategies.spearman import spearman_coefficient
from app.service.strategies.statistics import min_max_normalize, pearson_coefficient, rank


def test_pearson_detects_perfect_positive_correlation() -> None:
    assert pearson_coefficient([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == pytest.approx(1.0)


def test_pearson_detects_perfect_negative_correlation() -> None:
    assert pearson_coefficient([1.0, 2.0, 3.0], [6.0, 4.0, 2.0]) == pytest.approx(-1.0)


def test_pearson_matches_known_value() -> None:
    # Hand-computed reference: cov = 4.0, sd_x = sd_y = sqrt(5), so r = 4/5 = 0.8.
    result = pearson_coefficient([1.0, 2.0, 3.0, 4.0], [1.0, 3.0, 2.0, 4.0])
    assert result == pytest.approx(0.8)


def test_pearson_returns_zero_without_variance() -> None:
    assert pearson_coefficient([5.0, 5.0, 5.0], [1.0, 2.0, 3.0]) == 0.0


def test_pearson_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="equal lengths"):
        pearson_coefficient([1.0, 2.0], [1.0])


def test_pearson_rejects_single_observation() -> None:
    with pytest.raises(ValueError, match="at least two observations"):
        pearson_coefficient([1.0], [1.0])


def test_rank_orders_values_from_one() -> None:
    assert rank([30.0, 10.0, 20.0]) == [3.0, 1.0, 2.0]


def test_rank_averages_ties() -> None:
    # Two values tie for ranks 2 and 3, so both receive 2.5.
    assert rank([10.0, 20.0, 20.0, 40.0]) == [1.0, 2.5, 2.5, 4.0]


def test_spearman_is_one_for_monotonic_but_nonlinear_data() -> None:
    # Pearson is dragged below 1.0 by the curvature; Spearman is not.
    x_values = [1.0, 2.0, 3.0, 4.0]
    y_values = [1.0, 4.0, 9.0, 1000.0]
    assert spearman_coefficient(x_values, y_values) == pytest.approx(1.0)
    assert pearson_coefficient(x_values, y_values) < 0.9


def test_min_max_normalize_scales_to_unit_range() -> None:
    assert min_max_normalize([10.0, 20.0, 30.0]) == [0.0, 0.5, 1.0]


def test_min_max_normalize_handles_constant_series() -> None:
    assert min_max_normalize([7.0, 7.0]) == [0.5, 0.5]


def test_min_max_normalize_handles_empty_series() -> None:
    assert min_max_normalize([]) == []
