"""FastAPI inference server for sentiment analysis."""

import time

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest

from src.model import predict_sentiment
from src.preprocess import validate_input


app = FastAPI(title="ML Sentiment Analyzer", version="0.1.0")


# -----------------------------
# Request / Response Schemas
# -----------------------------
class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    label: str
    confidence: float


# -----------------------------
# Prometheus Metrics
# -----------------------------
REQUEST_COUNT = Counter(
    "prediction_requests_total",
    "Total prediction requests",
    ["method", "endpoint", "status"],
)

PREDICTION_LABEL_COUNT = Counter(
    "predictions_per_label_total",
    "Total predictions per sentiment label",
    ["label"],
)

REQUEST_LATENCY = Histogram(
    "prediction_request_duration_seconds",
    "Prediction request latency",
    ["method", "endpoint"],
)


# -----------------------------
# API Endpoints
# -----------------------------
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    start = time.time()

    try:
        # Validate input
        if not validate_input(request.text):
            REQUEST_COUNT.labels(
                method="POST", endpoint="/predict", status="400"
            ).inc()
            raise HTTPException(status_code=400, detail="Invalid input text")

        # Model inference
        result = predict_sentiment(request.text)

        # Metrics
        REQUEST_COUNT.labels(
            method="POST", endpoint="/predict", status="200"
        ).inc()

        PREDICTION_LABEL_COUNT.labels(label=result["label"]).inc()

        return PredictResponse(
            label=result["label"],
            confidence=result["confidence"],
        )

    except Exception:
        REQUEST_COUNT.labels(
            method="POST", endpoint="/predict", status="500"
        ).inc()
        raise

    finally:
        REQUEST_LATENCY.labels(
            method="POST", endpoint="/predict"
        ).observe(time.time() - start)


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=generate_latest(), media_type="text/plain")
