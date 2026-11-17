from fastapi.testclient import TestClient

from app.main import app
from app.models.log import LogEvent
from app.repository.event_store import EventStore


def _event(service: str, level: str, category: str, latency: float | None = None) -> LogEvent:
    return LogEvent(
        timestamp="2026-01-01T00:00:00Z", service=service, level=level,
        message="m", category=category, latency_ms=latency,
    )


def test_summarize_window_and_aggregates() -> None:
    store = EventStore(100)
    store.add_many([_event("db", "ERROR", "network_timeout", 100), _event("db", "INFO", "other", 300)], now=1000)
    store.add_many([_event("old", "ERROR", "other")], now=100)
    result = store.summarize(60, now=1010)
    assert [s.service for s in result] == ["db"]
    assert result[0].error_rate == 0.5
    assert result[0].avg_latency_ms == 200.0
    assert result[0].by_category == {"network_timeout": 1}


def test_store_is_bounded() -> None:
    store = EventStore(2)
    store.add_many([_event("a", "INFO", "other") for _ in range(5)])
    assert len(store.recent(10)) == 2


def test_api_ingest_and_summary() -> None:
    with TestClient(app) as client:
        body = {"lines": ['{"level":"ERROR","service":"db","message":"timeout"}', "junk"]}
        resp = client.post("/api/v1/logs", json=body)
        assert resp.status_code == 202
        assert resp.json() == {"accepted": 1, "rejected": 1}
        summary = client.get("/api/v1/summary").json()
        assert summary["services"][0]["service"] == "db"
        assert client.get("/api/v1/events?service=db").json()[0]["category"] == "network_timeout"
        assert "cns_log_events_total" in client.get("/metrics").text
        assert client.get("/health").json() == {"status": "ok"}


def test_api_rejects_empty_batch() -> None:
    with TestClient(app) as client:
        assert client.post("/api/v1/logs", json={"lines": []}).status_code == 422
