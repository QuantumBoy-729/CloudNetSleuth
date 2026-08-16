"""JSON logging configuration."""

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from app.config.settings import settings

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

_RESERVED_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "asctime",
    "message",
    "taskName",
    # uvicorn attaches an ANSI-escaped duplicate of the message; dropping it
    # keeps escape sequences out of structured log sinks.
    "color_message",
}


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialise ``record`` to a JSON string.

        Includes the active request id and any custom ``extra`` fields, and
        preserves exception tracebacks so failures remain diagnosable.
        """
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.app_name,
            "environment": settings.environment,
        }

        request_id = request_id_var.get()
        if request_id:
            payload["request_id"] = request_id

        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Install the JSON formatter on the root logger and align uvicorn loggers."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())

    # Stop uvicorn from emitting a second, plain-text copy of every record.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True
