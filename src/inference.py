"""FastAPI inference server for sentiment analysis."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.model import predict_sentiment
from src.preprocess import validate_input

app = FastAPI(title="ML Sentiment Analyzer", version="0.1.0")


class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    label: str
    confidence: float


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    if not validate_input(request.text):
        raise HTTPException(status_code=400, detail="Invalid input text")
    result = predict_sentiment(request.text)
    return PredictResponse(label=result["label"], confidence=result["confidence"])
