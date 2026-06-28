"""
Endpoints da API v1.
"""
from fastapi import APIRouter, Depends, Request

from app.core.auth import AuthenticatedClient
from app.core.rate_limit import enforce_rate_limit
from app.detection.pipeline import analyze_message
from app.schemas import AnalyzeRequest, AnalyzeResponse, StatsSummary

router = APIRouter(prefix="/v1", tags=["análise"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    payload: AnalyzeRequest,
    request: Request,
    client: AuthenticatedClient = Depends(enforce_rate_limit),
) -> AnalyzeResponse:
    """
    Analisa uma mensagem e retorna um veredito estruturado de risco de golpe.

    O cliente decide o que fazer com o resultado: bloquear, escalar para
    um analista humano, ou só registrar no próprio painel de fraude.
    """
    audit_logger = request.app.state.audit_logger
    return analyze_message(payload.message, client_id=client.client_id, audit_logger=audit_logger)


@router.get("/stats/summary", response_model=StatsSummary)
async def stats_summary(
    request: Request,
    window_hours: int = 24,
    client: AuthenticatedClient = Depends(enforce_rate_limit),
) -> StatsSummary:
    """Resumo agregado das análises do cliente nas últimas N horas (fonte para dashboard)."""
    audit_logger = request.app.state.audit_logger
    return StatsSummary(**audit_logger.stats_summary(client.client_id, window_hours))
