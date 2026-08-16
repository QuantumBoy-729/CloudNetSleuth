import pytest

from app.models.rca import RCARequest, ServiceMetric


@pytest.fixture
def sample_metrics() -> list[ServiceMetric]:
    return [
        ServiceMetric(
            service_name="gateway",
            error_rate=0.40,
            latency_ms=250.0,
            throughput_rps=120.0,
        ),
        ServiceMetric(
            service_name="auth",
            error_rate=0.15,
            latency_ms=130.0,
            throughput_rps=180.0,
        ),
        ServiceMetric(
            service_name="db",
            error_rate=0.30,
            latency_ms=220.0,
            throughput_rps=90.0,
        ),
    ]


@pytest.fixture
def sample_request(sample_metrics: list[ServiceMetric]) -> RCARequest:
    return RCARequest(metrics=sample_metrics)


@pytest.fixture
def sample_payload() -> dict:
    return {
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
