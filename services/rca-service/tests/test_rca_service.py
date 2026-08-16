from app.models.rca import RCARequest, ServiceMetric
from app.service.rca_service import RCAService


def test_rca_service_returns_ranked_causes() -> None:
    payload = RCARequest(
        metrics=[
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
    )
    service = RCAService()

    response = service.analyze(payload=payload)

    assert len(response.top_causes) > 0
    assert response.top_causes[0].correlation_score >= response.top_causes[-1].correlation_score

