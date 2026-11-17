"""Parsing of raw log lines (JSON or plain text) into LogEvent objects."""

import json
import re
from datetime import datetime, timezone

from app.models.log import LogEvent
from app.service.classifier import classify

PLAIN_RE = re.compile(r"^(?P<ts>\S+)\s+(?P<level>[A-Za-z]+)\s+(?P<service>[\w.\-]+)\s+(?P<msg>.+)$")
LATENCY_RE = re.compile(r"(\d+(?:\.\d+)?)\s?ms")
VALID_LEVELS = {"DEBUG", "INFO", "WARN", "WARNING", "ERROR", "FATAL", "CRITICAL"}


class ParseError(ValueError):
    """Raised when a line cannot be understood."""


def _parse_ts(value: object) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ParseError(f"invalid timestamp: {value}") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _build(ts: object, level: str, service: str, message: str, latency: float | None) -> LogEvent:
    level = level.upper()
    if level not in VALID_LEVELS:
        raise ParseError(f"unknown level: {level}")
    if not service or not message:
        raise ParseError("service and message are required")
    if latency is None:
        match = LATENCY_RE.search(message)
        latency = float(match.group(1)) if match else None
    return LogEvent(
        timestamp=_parse_ts(ts),
        service=service[:128],
        level="WARN" if level == "WARNING" else level,
        message=message,
        category=classify(message),
        latency_ms=latency,
    )


def parse_line(raw: str) -> LogEvent:
    """Parse one raw line: a JSON object or `<ts> <LEVEL> <service> <msg>`."""
    raw = raw.strip()
    if raw.startswith("{"):
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ParseError("malformed JSON") from exc
        if not isinstance(obj, dict):
            raise ParseError("JSON line must be an object")
        latency = obj.get("latency_ms")
        return _build(
            obj.get("ts") or obj.get("timestamp"),
            str(obj.get("level", "INFO")),
            str(obj.get("service", "")),
            str(obj.get("message") or obj.get("msg") or ""),
            float(latency) if isinstance(latency, (int, float)) else None,
        )
    match = PLAIN_RE.match(raw)
    if not match:
        raise ParseError("unrecognised line format")
    return _build(match["ts"], match["level"], match["service"], match["msg"], None)
