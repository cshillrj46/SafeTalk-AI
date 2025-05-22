# backend/model.py
import joblib
import numpy as np

# Carga dos componentes treinados
try:
    model = joblib.load("model/scam_detector.joblib")
    vectorizer = joblib.load("model/vectorizer.joblib")
except Exception as e:
    raise RuntimeError(f"❌ Falha ao carregar modelo ou vetorizador: {e}")

# Mapeamento de rótulos (caso use 'golpe', 'fraude', 'legitima' etc.)
LABELS = {
    "high": "Mensagem identificada com padrão de golpe",
    "golpe": "Mensagem identificada com padrão de golpe",
    "fraude": "Mensagem identificada com padrão de golpe",
    "low": "Mensagem sem sinais evidentes de golpe",
    "legitima": "Mensagem sem sinais evidentes de golpe",
    "mensagem_legitima": "Mensagem sem sinais evidentes de golpe"
}

def predict_message(message: str):
    vectorized = vectorizer.transform([message])
    prediction = model.predict(vectorized)[0]
    proba = np.max(model.predict_proba(vectorized))  # maior score entre as classes

    # Definir motivo baseado no rótulo retornado
    reason = LABELS.get(prediction.lower(), "Resultado indefinido pela IA")

    return {
        "risk": prediction,
        "confidence": round(proba, 2),
        "reason": reason
    }
