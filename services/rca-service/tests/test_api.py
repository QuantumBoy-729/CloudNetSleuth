from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics_endpoint() -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_analyze_endpoint() -> None:
    payload = {
        "metrics": [
            {
                "service_name": "gateway",
                "error_rate": 0.40,
                "latency_ms": 250,
                "throughput_rps": 120,
            },
            {
                "service_name": "auth",
                "error_rate": 0.15,
                "latency_ms": 130,
                "throughput_rps": 180,
            },
            {
                "service_name": "db",
                "error_rate": 0.30,
                "latency_ms": 220,
                "throughput_rps": 90,
            },
        ]
    }
    response = client.post("/api/v1/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "top_causes" in body
    assert len(body["top_causes"]) > 0

