"""Diagnosis endpoints (rules engine + correlation)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config.settings import settings
from app.models.diagnosis import DiagnoseRequest, DiagnosisResponse
from app.repository.ingestor_client import IngestorClient, IngestorUnavailableError
from app.service.diagnosis_service import DiagnosisService
from app.service.rules.engine import RulesEngine, load_rules

diagnose_router = APIRouter(prefix="/api/v1", tags=["diagnosis"])


def get_diagnosis_service() -> DiagnosisService:
    """Dependency: build the service from the configured rules file."""
    return DiagnosisService(RulesEngine(load_rules(settings.rules_path or None)))


def get_ingestor_client() -> IngestorClient:
    """Dependency: client for the log-ingestor."""
    return IngestorClient(settings.ingestor_url, settings.ingestor_timeout_seconds)


@diagnose_router.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose(
    payload: DiagnoseRequest,
    service: DiagnosisService = Depends(get_diagnosis_service),
) -> DiagnosisResponse:
    """Diagnose from caller-supplied per-service summaries."""
    return service.diagnose(payload.services, settings.window_seconds)


@diagnose_router.get("/diagnose", response_model=DiagnosisResponse)
async def diagnose_live(
    window_seconds: int = Query(settings.window_seconds, ge=1, le=3600),
    service: DiagnosisService = Depends(get_diagnosis_service),
    client: IngestorClient = Depends(get_ingestor_client),
) -> DiagnosisResponse:
    """Pull the latest window from the log-ingestor and diagnose it."""
    try:
        summaries = await client.fetch_summaries(window_seconds)
    except IngestorUnavailableError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return service.diagnose(summaries, window_seconds)
