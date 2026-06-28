"""
Motor de regras heurísticas.

Cobre os padrões de golpe mais comuns e bem documentados no Brasil
(golpe do PIX urgente, falso parente que trocou de número, falsa central
bancária, falsa renda extra, falso boleto/taxa de entrega, link de
"atualização do WhatsApp"). É o caminho rápido e barato do pipeline:
roda em microssegundos, sem custo de inferência, e cobre os casos óbvios
sem precisar do modelo de ML ou do LLM.

Isso é o ponto onde experiência de investigação de fraude real (não só
"chamar uma API de IA") faz diferença — as regras abaixo refletem padrões
documentados por Febraban/ADDP/TransUnion, não um chute genérico.
"""
import re
from dataclasses import dataclass, field

# Cada categoria: (nome_da_regra, padrões_regex, peso)
_RULES: list[tuple[str, list[str], float]] = [
    (
        "pix_urgente",
        [r"pix\s+urgente", r"preciso.*pix.*agora", r"manda.*pix.*r\$", r"transfer[êe]ncia.*urgente"],
        0.45,
    ),
    (
        "falso_parente_novo_numero",
        [r"troquei de n[uú]mero", r"perdi (meu|o) (celular|whats)", r"esse [eé] meu novo (n[uú]mero|whats)"],
        0.35,
    ),
    (
        "falsa_central_bancaria",
        [
            r"central de atendimento",
            r"sua conta ser[áa] bloqueada",
            r"c[óo]digo de verifica[çc][ãa]o",
            r"confirme seus dados",
            r"clique.*desbloquear",
        ],
        0.5,
    ),
    (
        "falsa_renda_extra",
        [r"renda extra", r"ganhe.*r\$\s*\d+.*por dia", r"trabalhe.*de casa.*poucas horas"],
        0.3,
    ),
    (
        "whatsapp_atualizacao_falsa",
        [r"atualizar.*whatsapp", r"whatsapp.*desatualizad", r"link.*atualiza[çc][ãa]o"],
        0.55,
    ),
    (
        "falso_boleto_taxa",
        [r"boleto.*pend[êe]ncia", r"taxa.*entrega.*urgente", r"pague.*para liberar.*encomenda"],
        0.4,
    ),
    (
        "link_suspeito",
        [r"https?://\S+\.(tk|xyz|top|click|info|gq)(/\S*)?\b"],
        0.45,
    ),
]

_URGENCY_BOOST = [r"urgente", r"agora mesmo", r"imediat", r"[úu]ltima chance", r"vai ser bloqueada"]

_COMPILED_RULES = [
    (name, [re.compile(p, re.IGNORECASE) for p in patterns], weight) for name, patterns, weight in _RULES
]
_COMPILED_URGENCY = [re.compile(p, re.IGNORECASE) for p in _URGENCY_BOOST]


@dataclass
class RulesResult:
    score: float
    triggered: list[str] = field(default_factory=list)


def evaluate(message: str) -> RulesResult:
    score = 0.0
    triggered: list[str] = []

    for name, patterns, weight in _COMPILED_RULES:
        if any(p.search(message) for p in patterns):
            triggered.append(name)
            score += weight

    # Urgência artificial combinada com qualquer outra regra já disparada
    # aumenta a confiança de que é golpe — engenharia social explora
    # justamente a pressão de tempo.
    if triggered and any(p.search(message) for p in _COMPILED_URGENCY):
        triggered.append("pressao_de_urgencia")
        score += 0.15

    return RulesResult(score=min(score, 1.0), triggered=triggered)
