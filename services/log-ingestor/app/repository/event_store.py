"""In-memory sliding-window event store."""

import time
from collections import defaultdict, deque
from threading import Lock

from app.models.log import LogEvent, ServiceSummary

ERROR_LEVELS = {"ERROR", "FATAL", "CRITICAL"}


class EventStore:
    """Bounded, thread-safe store of recent events (O(1) append, O(n) summary)."""

    def __init__(self, max_events: int) -> None:
        self._events: deque[LogEvent] = deque(maxlen=max_events)
        self._lock = Lock()

    def add_many(self, events: list[LogEvent], now: float | None = None) -> None:
        """Append events, stamping their receive time."""
        stamp = time.time() if now is None else now
        with self._lock:
            for event in events:
                event.received_at = stamp
                self._events.append(event)

    def recent(self, limit: int, service: str | None = None) -> list[LogEvent]:
        """Newest-first events, optionally filtered by service."""
        with self._lock:
            items = [e for e in self._events if service is None or e.service == service]
        return items[-limit:][::-1]

    def summarize(self, window_seconds: int, now: float | None = None) -> list[ServiceSummary]:
        """Aggregate events received within the last window per service."""
        cutoff = (time.time() if now is None else now) - window_seconds
        with self._lock:
            window = [e for e in self._events if e.received_at >= cutoff]
        grouped: dict[str, list[LogEvent]] = defaultdict(list)
        for event in window:
            grouped[event.service].append(event)
        summaries = []
        for service, events in sorted(grouped.items()):
            errors = sum(1 for e in events if e.level in ERROR_LEVELS)
            latencies = [e.latency_ms for e in events if e.latency_ms is not None]
            categories: dict[str, int] = defaultdict(int)
            for event in events:
                if event.category != "other":
                    categories[event.category] += 1
            summaries.append(
                ServiceSummary(
                    service=service,
                    total=len(events),
                    errors=errors,
                    error_rate=round(errors / len(events), 4),
                    avg_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
                    throughput_rps=round(len(events) / window_seconds, 4),
                    by_category=dict(categories),
                )
            )
        return summaries
