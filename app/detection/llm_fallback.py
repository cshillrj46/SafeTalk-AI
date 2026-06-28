"""
Segunda opinião via LLM para mensagens ambíguas.

Só é chamado quando o motor de regras não disparou um risco "alto" óbvio
E o modelo de ML não atingiu o limiar de confiança configurado
(ml_confidence_threshold). Isso é deliberado: chamar um LLM em toda
mensagem seria caro e lento em alto volume — aqui ele entra só nos casos
realmente ambíguos, que são a minoria.

Usa claude-haiku por padrão (configurável): é o ponto certo do trade-off
custo/qualidade para uma tarefa de classificação binária com poucos
exemplos, não uma tarefa que precise do modelo mais caro da linha.

Se ANTHROPIC_API_KEY não estiver configurada, ou a chamada falhar, o
sistema não trava — retorna "indeterminado" e deixa o veredito do ML
(ou das regras) prevalecer. Falha de um componente opcional nunca deve
derrubar a resposta da API.
"""
import json
import logging
from dataclasses import dataclass
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Você é um classificador especialista em fraude e engenharia social em \
mensagens de WhatsApp no Brasil. Você já viu milhares de exemplos reais de golpes (PIX \
urgente, falso parente, falsa central bancária, falsa renda extra, falso boleto, phishing \
de atualização de app) e de mensagens legítimas.

Responda SOMENTE com um JSON válido, sem texto antes ou depois, no formato:
{"risk": "baixo" | "medio" | "alto", "confidence": 0.0 a 1.0, "reason": "explicação curta em português"}
"""


@dataclass
class LLMResult:
    risk: str
    confidence: float
    reason: str


def classify_with_llm(message: str) -> Optional[LLMResult]:
    settings = get_settings()
    if not settings.llm_fallback_enabled or not settings.anthropic_api_key:
        logger.info("Fallback de LLM desabilitado ou sem chave configurada — pulando etapa.")
        return None

    try:
        import anthropic  # import local: dependência opcional, só carregada se usada
    except ImportError:
        logger.warning("Pacote 'anthropic' não instalado — pulando fallback de LLM.")
        return None

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.llm_model,
            max_tokens=200,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Mensagem para classificar:\n\n{message}"}],
        )
        raw_text = "".join(block.text for block in response.content if block.type == "text")
        parsed = json.loads(raw_text)
        return LLMResult(
            risk=parsed["risk"],
            confidence=float(parsed["confidence"]),
            reason=parsed["reason"],
        )
    except Exception:
        logger.exception("Falha ao consultar LLM de segunda opinião — seguindo sem ele.")
        return None
