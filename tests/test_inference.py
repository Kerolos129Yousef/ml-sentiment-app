"""Tests for the FastAPI inference server."""

from fastapi.testclient import TestClient

from src.inference import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_predict_positive():
    response = client.post("/predict", json={"text": "I love this product!"})
    assert response.status_code == 200
    data = response.json()
    assert data["label"] in ("positive", "negative", "neutral")
    assert "confidence" in data


def test_predict_empty_text():
    response = client.post("/predict", json={"text": ""})
    assert response.status_code == 400


def test_predict_missing_field():
    response = client.post("/predict", json={})
    assert response.status_code == 422
