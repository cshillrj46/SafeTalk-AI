#backend/schemas.py
from pydantic import BaseModel, Field

class TextInput(BaseModel):
    message: str = Field(..., description="Texto da mensagem a ser analisada")

class TextOutput(BaseModel):
    risk: str = Field(..., description="Classificação da IA (ex: 'golpe', 'legítima')")
    confidence: float = Field(..., ge=0, le=1, description="Nível de confiança (0 a 1)")
    reason: str = Field(..., description="Motivo gerado pela IA para a classificação")
