"""HTTP client for the log-ingestor (data access for summaries)."""

import httpx

from app.models.diagnosis import ServiceSummary


class IngestorUnavailableError(RuntimeError):
    """Raised when the log-ingestor cannot be reached or returns bad data."""


class IngestorClient:
    """Fetches per-service summaries from the log-ingestor."""

    def __init__(self, base_url: str, timeout_seconds: float, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._transport = transport

    async def fetch_summaries(self, window_seconds: int) -> list[ServiceSummary]:
        """Return summaries for the window; raises IngestorUnavailableError on failure."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as client:
                response = await client.get(
                    f"{self._base_url}/api/v1/summary", params={"window_seconds": window_seconds}
                )
                response.raise_for_status()
                payload = response.json()
            return [ServiceSummary(**item) for item in payload["services"]]
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
            raise IngestorUnavailableError(f"log-ingestor request failed: {exc}") from exc
