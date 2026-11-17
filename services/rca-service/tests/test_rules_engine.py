import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.routers.diagnose import get_ingestor_client
from app.main import app
from app.models.diagnosis import ServiceSummary
from app.repository.ingestor_client import IngestorClient, IngestorUnavailableError
from app.service.diagnosis_service import DiagnosisService
from app.service.rules.engine import RulesEngine, load_rules


def summary(service: str, **kw) -> ServiceSummary:
    base = dict(total=50, errors=0, error_rate=0.0, avg_latency_ms=50.0, throughput_rps=1.0, by_category={})
    base.update(kw)
    return ServiceSummary(service=service, **base)


def test_default_rules_load() -> None:
    names = {r.name for r in load_rules()}
    assert {"recurring_network_timeouts", "high_error_rate", "oom_kills"} <= names


def test_timeouts_rule_fires_with_recommendation() -> None:
    engine = RulesEngine(load_rules())
    findings = engine.evaluate([summary("db", by_category={"network_timeout": 12}), summary("auth")])
    assert [f.rule for f in findings] == ["recurring_network_timeouts"]
    assert findings[0].service == "db"
    assert findings[0].severity == "critical"
    assert "NetworkPolicies" in findings[0].recommendation


def test_rules_respect_min_events_and_threshold() -> None:
    engine = RulesEngine(load_rules())
    quiet = summary("x", total=3, error_rate=0.9, by_category={"network_timeout": 2})
    assert engine.evaluate([quiet]) == []


def test_findings_sorted_critical_first() -> None:
    engine = RulesEngine(load_rules())
    findings = engine.evaluate([summary("a", error_rate=0.5, by_category={"oom_killed": 1})])
    assert [f.severity for f in findings] == ["critical", "warning"]


def test_unknown_signal_rejected(tmp_path) -> None:
    bad = tmp_path / "r.yaml"
    bad.write_text(
        "rules:\n  - {name: n, title: t, signal: bogus, threshold: 1, recommendation: r}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_rules(bad)


def test_diagnosis_service_ranks_and_tolerates_no_variance() -> None:
    service = DiagnosisService(RulesEngine(load_rules()))
    varied = [
        summary("db", error_rate=0.6, avg_latency_ms=900, throughput_rps=2),
        summary("orders", error_rate=0.3, avg_latency_ms=400, throughput_rps=5),
        summary("auth", error_rate=0.0, avg_latency_ms=40, throughput_rps=9),
    ]
    assert service.diagnose(varied, 60).top_causes[0].service_name == "db"
    flat = [summary("a"), summary("b")]
    assert service.diagnose(flat, 60).top_causes == []


def _client_with(handler) -> IngestorClient:
    return IngestorClient("http://ingestor", 1.0, transport=httpx.MockTransport(handler))


def test_diagnose_post_endpoint() -> None:
    payload = {"services": [summary("db", by_category={"connection_refused": 4}).model_dump()]}
    body = TestClient(app).post("/api/v1/diagnose", json=payload).json()
    assert body["findings"][0]["rule"] == "connection_refused"


def test_diagnose_live_uses_ingestor_and_maps_failure_to_502() -> None:
    ok = {"window_seconds": 60, "services": [summary("db", by_category={"oom_killed": 2}).model_dump()]}
    app.dependency_overrides[get_ingestor_client] = lambda: _client_with(lambda r: httpx.Response(200, json=ok))
    try:
        resp = TestClient(app).get("/api/v1/diagnose")
        assert resp.status_code == 200
        assert resp.json()["findings"][0]["rule"] == "oom_kills"

        app.dependency_overrides[get_ingestor_client] = lambda: _client_with(lambda r: httpx.Response(500))
        assert TestClient(app).get("/api/v1/diagnose").status_code == 502
    finally:
        app.dependency_overrides.clear()


def test_client_raises_on_bad_payload() -> None:
    import asyncio

    client = _client_with(lambda r: httpx.Response(200, json={"nope": 1}))
    with pytest.raises(IngestorUnavailableError):
        asyncio.run(client.fetch_summaries(60))
