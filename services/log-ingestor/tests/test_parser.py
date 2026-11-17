import pytest

from app.service.classifier import classify
from app.service.parser import ParseError, parse_line


@pytest.mark.parametrize(
    "message,category",
    [
        ("upstream request timed out after 5000ms", "network_timeout"),
        ("dial tcp 10.0.0.1:5432: connection refused", "connection_refused"),
        ("lookup db: no such host", "dns_failure"),
        ("container OOMKilled", "oom_killed"),
        ("returned 502 bad gateway", "http_5xx"),
        ("request ok", "other"),
    ],
)
def test_classify(message: str, category: str) -> None:
    assert classify(message) == category


def test_parse_json_line() -> None:
    raw = '{"ts":"2026-01-01T00:00:00Z","level":"error","service":"db","message":"query timeout","latency_ms":900}'
    event = parse_line(raw)
    assert (event.service, event.level, event.category, event.latency_ms) == (
        "db", "ERROR", "network_timeout", 900,
    )


def test_parse_plain_line_extracts_latency() -> None:
    event = parse_line("2026-01-01T00:00:00Z WARN orders slow response 1200ms")
    assert event.service == "orders"
    assert event.latency_ms == 1200.0


@pytest.mark.parametrize("raw", ["garbage", "{bad json", "[1,2]", "2026-01-01T00:00:00Z NOPE svc msg"])
def test_parse_rejects_bad_lines(raw: str) -> None:
    with pytest.raises(ParseError):
        parse_line(raw)
