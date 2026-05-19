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
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    if not validate_input(request.text):
        raise HTTPException(status_code=400, detail="Invalid input text")

    result = predict_sentiment(request.text)

    return PredictResponse(
        label=result["label"],
        confidence=result["confidence"]
    )

from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# --- Prometheus metrics ---
REQUEST_COUNT = Counter(
    "prediction_requests_total",
    "Total prediction requests",
    ["method", "endpoint", "status"]
)
PREDICTION_LABEL_COUNT = Counter(
    "predictions_per_label_total",
    "Total predictions per sentiment label",
    ["label"]
)
REQUEST_LATENCY = Histogram(
    "prediction_request_duration_seconds",
    "Prediction request latency",
    ["method", "endpoint"]
)

@app.get("/metrics")
def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")
import time

@app.post("/predict")
def predict(request: PredictRequest) -> PredictResponse:
    start = time.time()
    try:
        result = model.predict(request.text)
        REQUEST_COUNT.labels(method="POST", endpoint="/predict", status="200").inc()
        PREDICTION_LABEL_COUNT.labels(label=result.label).inc()
        return result
    except Exception as e:
        REQUEST_COUNT.labels(method="POST", endpoint="/predict", status="500").inc()
        raise e
    finally:
        REQUEST_LATENCY.labels(method="POST", endpoint="/predict").observe(time.time() - start)
