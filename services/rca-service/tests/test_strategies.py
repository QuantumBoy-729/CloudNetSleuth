import pytest

from app.models.rca import ServiceMetric
from app.service.strategies.pearson import PearsonCorrelationStrategy
from app.service.strategies.registry import (
    StrategyRegistry,
    UnknownStrategyError,
)
from app.service.strategies.spearman import SpearmanCorrelationStrategy


@pytest.mark.parametrize(
    "strategy",
    [PearsonCorrelationStrategy(), SpearmanCorrelationStrategy()],
    ids=["pearson", "spearman"],
)
def test_strategy_ranks_worst_offender_first(strategy: PearsonCorrelationStrategy) -> None:
    metrics = [
        ServiceMetric(service_name="healthy", error_rate=0.01, latency_ms=20, throughput_rps=500),
        ServiceMetric(service_name="degraded", error_rate=0.50, latency_ms=900, throughput_rps=10),
        ServiceMetric(service_name="middling", error_rate=0.10, latency_ms=120, throughput_rps=200),
    ]

    causes = strategy.analyze(metrics=metrics, top_k=3)

    assert causes[0].service_name == "degraded"
    assert causes[-1].service_name == "healthy"


@pytest.mark.parametrize(
    "strategy",
    [PearsonCorrelationStrategy(), SpearmanCorrelationStrategy()],
    ids=["pearson", "spearman"],
)
def test_strategy_respects_top_k(strategy: PearsonCorrelationStrategy) -> None:
    metrics = [
        ServiceMetric(
            service_name=f"svc-{index}",
            error_rate=index / 10,
            latency_ms=index * 10,
            throughput_rps=index,
        )
        for index in range(1, 6)
    ]

    causes = strategy.analyze(metrics=metrics, top_k=2)

    assert len(causes) == 2


def test_confidence_stays_within_unit_range() -> None:
    metrics = [
        ServiceMetric(service_name="a", error_rate=0.9, latency_ms=1000, throughput_rps=1),
        ServiceMetric(service_name="b", error_rate=0.1, latency_ms=10, throughput_rps=1000),
    ]

    causes = PearsonCorrelationStrategy().analyze(metrics=metrics, top_k=2)

    assert all(0.0 <= cause.confidence <= 1.0 for cause in causes)


def test_throughput_term_is_not_dwarfed_by_error_term() -> None:
    """Both signals are normalised, so throughput still moves the ranking.

    With raw units the ``1/(1+rps)`` throughput term collapsed to ~0.008 against
    an error term near 0.4, making it decorative. Here two services share an
    error rate and only throughput separates them.
    """
    metrics = [
        ServiceMetric(service_name="starved", error_rate=0.3, latency_ms=200, throughput_rps=5),
        ServiceMetric(service_name="busy", error_rate=0.3, latency_ms=200, throughput_rps=900),
        ServiceMetric(service_name="calm", error_rate=0.01, latency_ms=15, throughput_rps=400),
    ]

    causes = PearsonCorrelationStrategy().analyze(metrics=metrics, top_k=3)
    ranking = [cause.service_name for cause in causes]

    assert ranking.index("starved") < ranking.index("busy")


def test_registry_resolves_case_insensitively() -> None:
    assert StrategyRegistry().get("PEARSON").name == "pearson"


def test_registry_raises_for_unknown_name() -> None:
    with pytest.raises(UnknownStrategyError, match="available: pearson, spearman"):
        StrategyRegistry().get("bogus")


def test_registry_lists_sorted_names() -> None:
    assert StrategyRegistry().names() == ("pearson", "spearman")
