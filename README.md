# ML Sentiment App — Starter

A simple sentiment analysis microservice built with FastAPI and TextBlob.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m textblob.download_corpora
uvicorn src.inference:app --reload
```

## Endpoints

- `GET /health` — Health check
- `POST /predict` — Sentiment prediction (JSON body: `{"text": "..."}`)

## Running Tests

```bash
pytest
```

## Code Quality

```bash
ruff check src/ tests/
mypy src/
```
