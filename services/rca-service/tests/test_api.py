import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_rca_service
from app.config.state import service_state
from app.main import REQUEST_ID_HEADER, app


@pytest.fixture
def client() -> TestClient:
    # The context manager runs lifespan, which flips readiness on.
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_liveness_endpoint(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_reports_ready_when_serving(client: TestClient) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_fails_while_draining(client: TestClient) -> None:
    service_state.mark_draining()
    try:
        response = client.get("/health/ready")
    finally:
        service_state.mark_ready()

    assert response.status_code == 503
    assert response.json()["status"] == "draining"


def test_metrics_endpoint(client: TestClient) -> None:
    # Labelled series only appear once observed, so drive one request first.
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert 'http_requests_total{endpoint="/health"' in response.text
    assert 'http_request_latency_seconds_count{endpoint="/health"' in response.text


def test_metrics_use_route_templates_not_raw_paths(client: TestClient) -> None:
    client.get("/definitely/not/a/route")

    response = client.get("/metrics")

    assert "/definitely/not/a/route" not in response.text
    assert 'endpoint="unmatched"' in response.text


def test_rca_analysis_metrics_are_recorded(client: TestClient, sample_payload: dict) -> None:
    client.post("/api/v1/analyze", json=sample_payload)

    response = client.get("/metrics")

    assert 'rca_analysis_total{outcome="success",strategy="pearson"}' in response.text


def test_analyze_endpoint(client: TestClient, sample_payload: dict) -> None:
    response = client.post("/api/v1/analyze", json=sample_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["strategy"] == "pearson"
    assert body["analyzed_services"] == 3
    assert len(body["top_causes"]) == 3


def test_analyze_accepts_explicit_strategy(client: TestClient, sample_payload: dict) -> None:
    response = client.post("/api/v1/analyze", json={**sample_payload, "strategy": "spearman"})

    assert response.status_code == 200
    assert response.json()["strategy"] == "spearman"


def test_analyze_rejects_unknown_strategy(client: TestClient, sample_payload: dict) -> None:
    response = client.post("/api/v1/analyze", json={**sample_payload, "strategy": "nope"})

    assert response.status_code == 422
    assert "nope" in response.json()["detail"]


def test_analyze_rejects_single_service(client: TestClient) -> None:
    payload = {
        "metrics": [
            {"service_name": "solo", "error_rate": 0.1, "latency_ms": 10, "throughput_rps": 5}
        ]
    }

    response = client.post("/api/v1/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_constant_error_rates(client: TestClient) -> None:
    payload = {
        "metrics": [
            {"service_name": "a", "error_rate": 0.2, "latency_ms": 10, "throughput_rps": 5},
            {"service_name": "b", "error_rate": 0.2, "latency_ms": 90, "throughput_rps": 50},
        ]
    }

    response = client.post("/api/v1/analyze", json=payload)

    assert response.status_code == 422
    assert "vary" in response.text


def test_analyze_rejects_out_of_range_error_rate(client: TestClient) -> None:
    payload = {
        "metrics": [
            {"service_name": "a", "error_rate": 4.0, "latency_ms": 10, "throughput_rps": 5},
            {"service_name": "b", "error_rate": 0.2, "latency_ms": 90, "throughput_rps": 50},
        ]
    }

    response = client.post("/api/v1/analyze", json=payload)

    assert response.status_code == 422


def test_analyze_rejects_unknown_fields(client: TestClient, sample_payload: dict) -> None:
    response = client.post("/api/v1/analyze", json={**sample_payload, "injected": "value"})

    assert response.status_code == 422


def test_strategies_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/strategies")

    assert response.status_code == 200
    assert response.json() == {"strategies": ["pearson", "spearman"], "default": "pearson"}


def test_request_id_is_echoed_when_supplied(client: TestClient) -> None:
    response = client.get("/health", headers={REQUEST_ID_HEADER: "trace-123"})

    assert response.headers[REQUEST_ID_HEADER] == "trace-123"


def test_request_id_is_generated_when_absent(client: TestClient) -> None:
    response = client.get("/health")

    assert response.headers[REQUEST_ID_HEADER]


def test_dependency_override_replaces_service(client: TestClient, sample_payload: dict) -> None:
    class StubService:
        def analyze(self, payload: object) -> object:
            from app.models.rca import RCAResponse, RootCause

            return RCAResponse(
                top_causes=[
                    RootCause(service_name="overridden", correlation_score=9.0, confidence=1.0)
                ],
                strategy="stub",
                analyzed_services=0,
            )

    app.dependency_overrides[get_rca_service] = StubService
    try:
        response = client.post("/api/v1/analyze", json=sample_payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["top_causes"][0]["service_name"] == "overridden"
