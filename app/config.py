"""
Configuração central da aplicação.

Tudo que é segredo ou varia por ambiente (chaves de API, thresholds, limites)
vive aqui e é lido de variáveis de ambiente — nunca hardcoded no código.
"""
from functools import lru_cache
from typing import Dict

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Identidade do serviço ---
    app_name: str = "SafeTalk B2B API"
    environment: str = "development"  # development | staging | production

    # --- Autenticação ---
    # Formato: "chave1:cliente_a,chave2:cliente_b"
    api_keys_raw: str = "dev-key-local:cliente_demo"

    # --- Rate limiting ---
    rate_limit_per_minute: int = 60

    # --- Modelo de ML ---
    ml_model_dir: str = "models"
    ml_model_filename: str = "scam_detector.joblib"
    ml_vectorizer_filename: str = "vectorizer.joblib"

    # --- Pipeline de decisão ---
    # Confiança mínima do modelo de ML para aceitar o veredito sem
    # escalar para o LLM de segunda opinião.
    ml_confidence_threshold: float = 0.75
    # Pontuação mínima do motor de regras para classificar como "alto"
    # risco imediatamente, sem precisar rodar ML ou LLM (caminho rápido
    # e barato para os golpes mais óbvios).
    rules_high_risk_threshold: float = 0.8

    # --- LLM de segunda opinião (casos ambíguos) ---
    llm_fallback_enabled: bool = True
    anthropic_api_key: str = ""
    llm_model: str = "claude-haiku-4-5-20251001"  # modelo mais barato: volume alto, decisão simples

    # --- Auditoria / LGPD ---
    audit_db_path: str = "audit_log.db"
    # Mensagens nunca são logadas em texto puro — só a versão anonimizada.

    @property
    def api_keys(self) -> Dict[str, str]:
        """Mapa chave_de_api -> nome_do_cliente."""
        result: Dict[str, str] = {}
        for pair in self.api_keys_raw.split(","):
            pair = pair.strip()
            if not pair:
                continue
            key, _, client = pair.partition(":")
            result[key.strip()] = client.strip() or "desconhecido"
        return result


@lru_cache
def get_settings() -> Settings:
    return Settings()
