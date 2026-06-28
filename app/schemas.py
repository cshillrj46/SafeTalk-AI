"""
Contratos de entrada e saída da API.

A resposta é o que diferencia uma API B2B de um bot fechado: o cliente
recebe um veredito estruturado e decide o que fazer com ele (bloquear,
escalar para um analista, alimentar um dashboard) — em vez de só receber
uma mensagem de alerta dentro do próprio WhatsApp.
"""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

RiskLevel = Literal["baixo", "medio", "alto"]
DecisionSource = Literal["regras", "ml", "llm", "indeterminado"]


class AnalyzeRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Conteúdo textual da mensagem a ser analisada (já transcrito, se era áudio).",
    )
    channel: Optional[str] = Field(
        default=None,
        description="Canal de origem opcional (ex: 'whatsapp', 'sms', 'chat_web'), para métricas por canal.",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadados não sensíveis e opcionais do cliente (ex: id interno do ticket). "
        "Nunca deve conter CPF, telefone ou outro dado pessoal em texto puro.",
    )


class AnalyzeResponse(BaseModel):
    request_id: str = Field(..., description="Identificador único desta análise, para auditoria.")
    risk: RiskLevel = Field(..., description="Classificação de risco da mensagem.")
    confidence: float = Field(..., ge=0, le=1, description="Confiança da decisão final, entre 0 e 1.")
    reason: str = Field(..., description="Explicação legível do motivo da classificação.")
    triggered_rules: List[str] = Field(
        default_factory=list, description="Nomes das regras heurísticas que dispararam, se houver."
    )
    source: DecisionSource = Field(..., description="Qual camada do pipeline produziu o veredito final.")


class StatsSummary(BaseModel):
    client: str
    window_hours: int
    total_analisadas: int
    total_alto_risco: int
    total_medio_risco: int
    total_baixo_risco: int
    por_fonte: Dict[str, int]
