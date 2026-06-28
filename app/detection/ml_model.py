"""
Wrapper do modelo de ML (TF-IDF + LogisticRegression).

Diferença deliberada em relação ao protótipo original: aqui o carregamento
do modelo é lazy e tolerante a falha. Se os arquivos .joblib não existirem
(ex: antes de rodar o script de treino), o serviço sobe normalmente e o
pipeline simplesmente pula a etapa de ML — em vez de derrubar a API inteira
com uma RuntimeError no import, como acontecia no protótipo original.
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import joblib

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class MLResult:
    risk: str  # "baixo" | "medio" | "alto"
    confidence: float


class ScamClassifier:
    def __init__(self) -> None:
        self._model = None
        self._vectorizer = None
        self.ready = False

    def load(self) -> None:
        settings = get_settings()
        model_path = Path(settings.ml_model_dir) / settings.ml_model_filename
        vectorizer_path = Path(settings.ml_model_dir) / settings.ml_vectorizer_filename

        if not model_path.exists() or not vectorizer_path.exists():
            logger.warning(
                "Modelo de ML não encontrado em %s — etapa de ML será pulada até o treino ser executado "
                "(veja training/train_model.py).",
                settings.ml_model_dir,
            )
            self.ready = False
            return

        self._model = joblib.load(model_path)
        self._vectorizer = joblib.load(vectorizer_path)
        self.ready = True
        logger.info("Modelo de ML carregado com sucesso (%s).", model_path)

    def predict(self, message: str) -> Optional[MLResult]:
        if not self.ready or self._model is None or self._vectorizer is None:
            return None

        vector = self._vectorizer.transform([message])
        proba = self._model.predict_proba(vector)[0]
        classes = list(self._model.classes_)
        golpe_idx = classes.index("golpe") if "golpe" in classes else None

        if golpe_idx is None:
            # Defensivo: se o modelo foi treinado com rótulos diferentes,
            # não inventamos um resultado — melhor sinalizar indisponível.
            return None

        p_golpe = float(proba[golpe_idx])
        confidence = max(p_golpe, 1 - p_golpe)

        if p_golpe >= 0.66:
            risk = "alto"
        elif p_golpe >= 0.4:
            risk = "medio"
        else:
            risk = "baixo"

        return MLResult(risk=risk, confidence=round(confidence, 4))


# Singleton simples para o processo da aplicação — carregado no startup do FastAPI.
classifier = ScamClassifier()
