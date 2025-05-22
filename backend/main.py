# backend/main.py
from fastapi import FastAPI
from backend.schemas import TextInput, TextOutput
from backend.model import predict_message

app = FastAPI()

@app.post("/analyze-text", response_model=TextOutput)
def analyze_text(input_data: TextInput):
    result = predict_message(input_data.message)
    return result
