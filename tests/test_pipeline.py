from pathlib import Path

import pytest

from app.audit.logger import AuditLogger
from app.detection import llm_fallback, pipeline
from app.detection.ml_model import MLResult, classifier


@pytest.fixture
def audit_logger(tmp_path: Path) -> AuditLogger:
    return AuditLogger(str(tmp_path / "audit_test.db"))


def test_high_confidence_rule_short_circuits_pipeline(audit_logger):
    # Combina duas regras de peso alto para garantir score >= rules_high_risk_threshold
    msg = "Você precisa atualizar o whatsapp agora e também me manda um pix urgente, é urgente!"
    result = pipeline.analyze_message(msg, client_id="cliente_teste", audit_logger=audit_logger)

    assert result.risk == "alto"
    assert result.source == "regras"
    assert result.confidence >= 0.8


def test_falls_back_to_ml_when_rules_are_inconclusive(audit_logger, monkeypatch):
    monkeypatch.setattr(classifier, "predict", lambda message: MLResult(risk="alto", confidence=0.92))

    msg = "Cheguei bem em casa, obrigado pela carona hoje!"
    result = pipeline.analyze_message(msg, client_id="cliente_teste", audit_logger=audit_logger)

    assert result.source == "ml"
    assert result.risk == "alto"
    assert result.confidence == 0.92


def test_falls_back_to_llm_when_ml_confidence_is_low(audit_logger, monkeypatch):
    monkeypatch.setattr(classifier, "predict", lambda message: MLResult(risk="medio", confidence=0.4))
    monkeypatch.setattr(
        llm_fallback,
        "classify_with_llm",
        lambda message: llm_fallback.LLMResult(risk="alto", confidence=0.85, reason="padrão suspeito identificado"),
    )

    msg = "Mensagem ambígua qualquer"
    result = pipeline.analyze_message(msg, client_id="cliente_teste", audit_logger=audit_logger)

    assert result.source == "llm"
    assert result.risk == "alto"


def test_indeterminado_when_no_layer_is_confident(audit_logger, monkeypatch):
    monkeypatch.setattr(classifier, "predict", lambda message: None)
    monkeypatch.setattr(llm_fallback, "classify_with_llm", lambda message: None)

    msg = "Mensagem totalmente neutra sem nenhum padrão conhecido"
    result = pipeline.analyze_message(msg, client_id="cliente_teste", audit_logger=audit_logger)

    assert result.source == "indeterminado"
    assert result.risk in {"baixo", "medio"}


def test_audit_log_never_contains_raw_pii(audit_logger):
    msg = "Meu CPF é 123.456.789-00, me manda um pix urgente agora!"
    pipeline.analyze_message(msg, client_id="cliente_teste", audit_logger=audit_logger)

    stats = audit_logger.stats_summary("cliente_teste", window_hours=24)
    assert stats["total_analisadas"] == 1
