import json
import logging

from app.config.logging import JsonFormatter, request_id_var


def _record(**extra: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_formatter_emits_valid_json_with_core_fields() -> None:
    payload = json.loads(JsonFormatter().format(_record()))

    assert payload["message"] == "hello world"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "test.logger"
    assert payload["timestamp"].endswith("+00:00")
    assert "service" in payload and "environment" in payload


def test_formatter_includes_extra_fields() -> None:
    payload = json.loads(JsonFormatter().format(_record(strategy="pearson", count=3)))

    assert payload["strategy"] == "pearson"
    assert payload["count"] == 3


def test_formatter_drops_uvicorn_ansi_duplicate() -> None:
    payload = json.loads(JsonFormatter().format(_record(color_message="[36mhello[0m")))

    assert "color_message" not in payload


def test_formatter_includes_request_id_when_set() -> None:
    token = request_id_var.set("abc-123")
    try:
        payload = json.loads(JsonFormatter().format(_record()))
    finally:
        request_id_var.reset(token)

    assert payload["request_id"] == "abc-123"


def test_formatter_omits_request_id_when_unset() -> None:
    assert "request_id" not in json.loads(JsonFormatter().format(_record()))


def test_formatter_preserves_tracebacks() -> None:
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        import sys

        record = _record()
        record.exc_info = sys.exc_info()
        payload = json.loads(JsonFormatter().format(record))

    assert "RuntimeError: boom" in payload["exception"]


def test_formatter_survives_non_serialisable_extras() -> None:
    payload = json.loads(JsonFormatter().format(_record(obj=object())))

    assert isinstance(payload["obj"], str)
