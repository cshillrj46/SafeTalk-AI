"""
Pipeline de decisão: orquestra regras -> ML -> LLM.

Fluxo:
1. Motor de regras roda sempre (barato, rápido). Se a pontuação passa do
   limiar de alto risco, retorna na hora — sem gastar inferência de ML
   nem chamar o LLM.
2. Se as regras não foram conclusivas, roda o modelo de ML. Se a confiança
   dele está acima do limiar configurado, esse é o veredito final.
3. Se nem as regras nem o ML deram um veredito confiante, escala para o
   LLM como segunda opinião. Se o LLM também falhar/estiver desabilitado,
   o sistema ainda responde — com o melhor palpite disponível e
   confidence mais baixa, nunca com erro 500.

Cada análise gera um registro de auditoria com a mensagem ANONIMIZADA,
nunca o texto original.
"""
import uuid
from dataclasses import dataclass

from app.audit.logger import AuditLogger
from app.core.anonymizer import anonymize
from app.detection import llm_fallback, rules_engine
from app.detection.ml_model import classifier
from app.config import get_settings
from app.schemas import AnalyzeResponse


@dataclass
class PipelineDependencies:
    audit_logger: AuditLogger


def analyze_message(message: str, client_id: str, audit_logger: AuditLogger) -> AnalyzeResponse:
    settings = get_settings()
    request_id = str(uuid.uuid4())

    rules_result = rules_engine.evaluate(message)

    # Caminho 1: regra de alto risco disparou com confiança suficiente.
    if rules_result.score >= settings.rules_high_risk_threshold:
        response = AnalyzeResponse(
            request_id=request_id,
            risk="alto",
            confidence=round(rules_result.score, 4),
            reason="Padrões de golpe conhecidos detectados: " + ", ".join(rules_result.triggered),
            triggered_rules=rules_result.triggered,
            source="regras",
        )
        _log(audit_logger, request_id, client_id, message, response)
        return response

    # Caminho 2: modelo de ML, se disponível e confiante.
    ml_result = classifier.predict(message)
    if ml_result is not None and ml_result.confidence >= settings.ml_confidence_threshold:
        response = AnalyzeResponse(
            request_id=request_id,
            risk=ml_result.risk,
            confidence=ml_result.confidence,
            reason="Classificação pelo modelo de machine learning treinado.",
            triggered_rules=rules_result.triggered,
            source="ml",
        )
        _log(audit_logger, request_id, client_id, message, response)
        return response

    # Caminho 3: caso ambíguo — segunda opinião do LLM.
    llm_result = llm_fallback.classify_with_llm(message)
    if llm_result is not None:
        response = AnalyzeResponse(
            request_id=request_id,
            risk=llm_result.risk,
            confidence=llm_result.confidence,
            reason=llm_result.reason,
            triggered_rules=rules_result.triggered,
            source="llm",
        )
        _log(audit_logger, request_id, client_id, message, response)
        return response

    # Nenhuma camada teve confiança suficiente — devolve o melhor palpite
    # disponível (ML de baixa confiança ou, na ausência total, as regras)
    # em vez de travar a resposta.
    if ml_result is not None:
        response = AnalyzeResponse(
            request_id=request_id,
            risk=ml_result.risk,
            confidence=ml_result.confidence,
            reason="Classificação de baixa confiança — nenhuma camada teve certeza suficiente.",
            triggered_rules=rules_result.triggered,
            source="ml",
        )
    else:
        fallback_risk = "medio" if rules_result.triggered else "baixo"
        response = AnalyzeResponse(
            request_id=request_id,
            risk=fallback_risk,
            confidence=round(max(rules_result.score, 0.3), 4),
            reason="Sem modelo de ML disponível e sem segunda opinião de LLM — veredito baseado só em regras.",
            triggered_rules=rules_result.triggered,
            source="indeterminado",
        )

    _log(audit_logger, request_id, client_id, message, response)
    return response


def _log(audit_logger: AuditLogger, request_id: str, client_id: str, message: str, response: AnalyzeResponse) -> None:
    audit_logger.record(
        request_id=request_id,
        client_id=client_id,
        anonymized_message=anonymize(message),
        risk=response.risk,
        confidence=response.confidence,
        source=response.source,
        triggered_rules=response.triggered_rules,
    )
