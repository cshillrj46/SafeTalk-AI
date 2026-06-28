"""
Anonimização de dados pessoais antes de log ou persistência.

Regra de design: a mensagem original é usada apenas em memória, durante a
análise da requisição, e nunca é gravada em disco ou banco de auditoria.
O que é persistido é sempre a versão anonimizada produzida aqui — esse é
o requisito mínimo de privacidade por padrão (LGPD, art. 6º, princípio da
necessidade) para um produto que processa conteúdo de conversas privadas.

Isto é um anonimizador baseado em regex — pega os padrões mais comuns
(CPF, telefone BR, e-mail, cartão de crédito). Não é infalível: nomes
próprios ou endereços em texto livre não são cobertos por regex e exigiriam
um modelo de NER (ex: spaCy pt_core_news ou um classificador dedicado) numa
v2. Documentado aqui como limitação conhecida, não escondido.
"""
import re

_PATTERNS = {
    "CPF": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    "CNPJ": re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"),
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "CARTAO": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "TELEFONE": re.compile(r"\b(?:\+?55\s?)?\(?\d{2}\)?\s?9?\d{4}-?\d{4}\b"),
}


def anonymize(text: str) -> str:
    """Substitui ocorrências de dados pessoais por marcadores ([CPF], [EMAIL] etc.)."""
    result = text
    for label, pattern in _PATTERNS.items():
        result = pattern.sub(f"[{label}]", result)
    return result


def detect_pii_types(text: str) -> list[str]:
    """Retorna quais categorias de PII foram encontradas (útil para métricas)."""
    found = []
    for label, pattern in _PATTERNS.items():
        if pattern.search(text):
            found.append(label)
    return found
