from app.detection import rules_engine


def test_pix_urgente_message_triggers_rule():
    msg = "Preciso que você me manda um PIX urgente agora, é emergência!"
    result = rules_engine.evaluate(msg)
    assert "pix_urgente" in result.triggered
    assert result.score > 0


def test_fake_bank_central_triggers_rule():
    msg = "Aqui é a central de atendimento do banco, confirme seus dados e o código de verificação."
    result = rules_engine.evaluate(msg)
    assert "falsa_central_bancaria" in result.triggered


def test_normal_message_does_not_trigger_rules():
    msg = "Vamos almoçar amanhã? Marquei aquele restaurante novo."
    result = rules_engine.evaluate(msg)
    assert result.triggered == []
    assert result.score == 0.0


def test_urgency_boost_increases_score_when_combined_with_other_rule():
    msg = "Sua conta será bloqueada, é urgente, confirme seus dados agora mesmo!"
    result = rules_engine.evaluate(msg)
    assert "pressao_de_urgencia" in result.triggered
    assert result.score > 0.5


def test_score_is_capped_at_one():
    msg = (
        "PIX urgente agora! Troquei de número. Central de atendimento, "
        "confirme seus dados, código de verificação, renda extra, "
        "atualizar whatsapp, boleto com pendência, taxa de entrega urgente, "
        "é urgente, agora mesmo, imediatamente, última chance!"
    )
    result = rules_engine.evaluate(msg)
    assert result.score <= 1.0
