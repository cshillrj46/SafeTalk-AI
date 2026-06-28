from app.core.anonymizer import anonymize, detect_pii_types


def test_anonymize_masks_cpf():
    text = "Meu CPF é 123.456.789-00, pode confirmar?"
    result = anonymize(text)
    assert "123.456.789-00" not in result
    assert "[CPF]" in result


def test_anonymize_masks_email():
    text = "Me chama em joao.silva@exemplo.com qualquer coisa"
    result = anonymize(text)
    assert "joao.silva@exemplo.com" not in result
    assert "[EMAIL]" in result


def test_anonymize_masks_phone():
    text = "Me liga no (11) 98765-4321 hoje"
    result = anonymize(text)
    assert "98765-4321" not in result
    assert "[TELEFONE]" in result


def test_anonymize_leaves_normal_text_untouched():
    text = "Vamos almoçar amanhã às 13h?"
    assert anonymize(text) == text


def test_detect_pii_types_returns_categories_found():
    text = "Meu e-mail é teste@teste.com e meu CPF é 111.222.333-44"
    found = detect_pii_types(text)
    assert "EMAIL" in found
    assert "CPF" in found
