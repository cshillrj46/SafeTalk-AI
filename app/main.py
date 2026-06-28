"""
Ponto de entrada da aplicação.

uvicorn app.main:app --reload
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.analyze import router as analyze_router
from app.audit.logger import AuditLogger
from app.config import get_settings
from app.detection.ml_model import classifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    classifier.load()
    app.state.audit_logger = AuditLogger(settings.audit_db_path)
    yield


app = FastAPI(
    title="SafeTalk B2B API",
    description=(
        "API de triagem de mensagens para detecção de golpes e engenharia social, "
        "para integração em sistemas de atendimento de bancos e fintechs."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(analyze_router)


@app.get("/health", tags=["infra"])
async def health() -> dict:
    return {"status": "ok", "ml_model_carregado": classifier.ready}
