"""Background loop that publishes diagnosis results as Prometheus gauges."""

import asyncio
import logging

from app.config.metrics import ACTIVE_FINDINGS, DIAGNOSIS_RUNS, TOP_CAUSE_SCORE
from app.models.diagnosis import DiagnosisResponse
from app.repository.ingestor_client import IngestorClient, IngestorUnavailableError
from app.service.diagnosis_service import DiagnosisService

logger = logging.getLogger(__name__)


def publish(result: DiagnosisResponse) -> None:
    """Replace the finding/cause gauges with the latest diagnosis."""
    ACTIVE_FINDINGS.clear()
    TOP_CAUSE_SCORE.clear()
    for finding in result.findings:
        ACTIVE_FINDINGS.labels(
            rule=finding.rule, service=finding.service, severity=finding.severity
        ).set(finding.value)
    for cause in result.top_causes:
        TOP_CAUSE_SCORE.labels(service=cause.service_name).set(cause.correlation_score)


async def run_poller(
    client: IngestorClient, service: DiagnosisService, window_seconds: int, interval: float
) -> None:
    """Diagnose every ``interval`` seconds until cancelled."""
    while True:
        try:
            summaries = await client.fetch_summaries(window_seconds)
            publish(service.diagnose(summaries, window_seconds))
            DIAGNOSIS_RUNS.labels(outcome="ok").inc()
        except IngestorUnavailableError as exc:
            DIAGNOSIS_RUNS.labels(outcome="ingestor_unavailable").inc()
            logger.warning("diagnosis skipped: %s", exc)
        await asyncio.sleep(interval)
