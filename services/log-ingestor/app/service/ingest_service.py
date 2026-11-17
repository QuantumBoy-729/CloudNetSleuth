"""Business logic for log ingestion."""

from app.config.metrics import LOG_EVENTS_TOTAL, LOG_PARSE_FAILURES_TOTAL
from app.models.log import IngestResponse, LogEvent, SummaryResponse
from app.repository.event_store import EventStore
from app.service.parser import ParseError, parse_line


class IngestService:
    """Parses raw lines, records metrics and stores events."""

    def __init__(self, store: EventStore) -> None:
        self._store = store

    def ingest(self, lines: list[str]) -> IngestResponse:
        """Parse and store a batch; unparseable lines are counted as rejected."""
        events: list[LogEvent] = []
        rejected = 0
        for line in lines:
            try:
                events.append(parse_line(line))
            except ParseError:
                rejected += 1
                LOG_PARSE_FAILURES_TOTAL.inc()
        for event in events:
            LOG_EVENTS_TOTAL.labels(
                service=event.service, level=event.level, category=event.category
            ).inc()
        self._store.add_many(events)
        return IngestResponse(accepted=len(events), rejected=rejected)

    def summary(self, window_seconds: int) -> SummaryResponse:
        """Per-service aggregates for the window."""
        return SummaryResponse(
            window_seconds=window_seconds, services=self._store.summarize(window_seconds)
        )

    def recent(self, limit: int, service: str | None) -> list[LogEvent]:
        """Most recent events."""
        return self._store.recent(limit, service)
