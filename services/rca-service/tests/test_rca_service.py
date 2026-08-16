import pytest

from app.models.rca import RCARequest, RootCause, ServiceMetric
from app.repository.strategy_repository import StrategyConfigRepository
from app.service.rca_service import RCAService
from app.service.strategies.base import AnalysisStrategy
from app.service.strategies.registry import StrategyRegistry, UnknownStrategyError


class RecordingStrategy(AnalysisStrategy):
    """Test double that records what the service handed it."""

    name = "recording"

    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def analyze(self, metrics: list[ServiceMetric], top_k: int) -> list[RootCause]:
        self.calls.append((len(metrics), top_k))
        return [RootCause(service_name="stub", correlation_score=1.0, confidence=0.5)]


class FailingStrategy(AnalysisStrategy):
    name = "failing"

    def analyze(self, metrics: list[ServiceMetric], top_k: int) -> list[RootCause]:
        raise RuntimeError("strategy exploded")


def _service_with(strategy: AnalysisStrategy, top_k: int = 3) -> RCAService:
    class StubRepository(StrategyConfigRepository):
        def get_default_strategy_name(self) -> str:
            return strategy.name

        def list_enabled_strategy_names(self) -> tuple[str, ...]:
            return (strategy.name,)

        def get_top_k_causes(self) -> int:
            return top_k

    return RCAService(repository=StubRepository(), registry=StrategyRegistry([strategy]))


def test_rca_service_returns_ranked_causes(sample_request: RCARequest) -> None:
    response = RCAService().analyze(payload=sample_request)

    assert response.top_causes
    assert response.strategy == "pearson"
    assert response.analyzed_services == 3
    scores = [cause.correlation_score for cause in response.top_causes]
    assert scores == sorted(scores, reverse=True)


def test_rca_service_honours_requested_strategy(sample_metrics: list[ServiceMetric]) -> None:
    payload = RCARequest(metrics=sample_metrics, strategy="spearman")

    response = RCAService().analyze(payload=payload)

    assert response.strategy == "spearman"


def test_rca_service_delegates_to_injected_strategy(sample_request: RCARequest) -> None:
    strategy = RecordingStrategy()
    service = _service_with(strategy, top_k=2)

    response = service.analyze(payload=sample_request)

    assert strategy.calls == [(3, 2)]
    assert response.strategy == "recording"
    assert response.top_causes[0].service_name == "stub"


def test_rca_service_truncates_to_configured_top_k(sample_request: RCARequest) -> None:
    service = RCAService(repository=_TopKRepository(2))

    response = service.analyze(payload=sample_request)

    assert len(response.top_causes) == 2


class _TopKRepository(StrategyConfigRepository):
    def __init__(self, top_k: int) -> None:
        super().__init__()
        self._top_k = top_k

    def get_top_k_causes(self) -> int:
        return self._top_k


def test_rca_service_rejects_unknown_strategy(sample_metrics: list[ServiceMetric]) -> None:
    payload = RCARequest(metrics=sample_metrics, strategy="does-not-exist")

    with pytest.raises(UnknownStrategyError):
        RCAService().analyze(payload=payload)


def test_rca_service_rejects_disabled_strategy(sample_metrics: list[ServiceMetric]) -> None:
    payload = RCARequest(metrics=sample_metrics, strategy="spearman")
    service = _service_with(RecordingStrategy())

    with pytest.raises(UnknownStrategyError, match="not enabled"):
        service.analyze(payload=payload)


def test_rca_service_propagates_strategy_failure(sample_request: RCARequest) -> None:
    service = _service_with(FailingStrategy())

    with pytest.raises(RuntimeError, match="strategy exploded"):
        service.analyze(payload=sample_request)


def test_list_strategies_reports_registered_and_enabled() -> None:
    result = RCAService().list_strategies()

    assert result.default == "pearson"
    assert result.strategies == ["pearson", "spearman"]
