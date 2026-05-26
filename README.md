# ml-sentiment-app

> **Evidence notice:** This GitHub repository is a mirror of the work originally developed and executed on a private **Gitea** instance running on a team virtual machine (`130.15.5.206`) as part of **CISC-814 (DevOps and MLOps) — Queen's University, Summer 2026**. All CI pipelines, Docker image builds, and registry pushes ran on that local infrastructure. This repo exists as a public record of the source code and CI workflow configuration.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Application Architecture](#application-architecture)
- [Repository Structure](#repository-structure)
- [Getting Started (Local)](#getting-started-local)
- [CI Pipeline](#ci-pipeline)
  - [Stage 1 — Dependency Installation & Health Check](#stage-1--dependency-installation--health-check)
  - [Stage 2 — Linting with Ruff](#stage-2--linting-with-ruff)
  - [Stage 3 — Type Checking with Mypy](#stage-3--type-checking-with-mypy)
  - [Stage 4 — Testing with Pytest](#stage-4--testing-with-pytest)
  - [Stage 5 — Docker Multi-Stage Build](#stage-5--docker-multi-stage-build)
  - [Stage 6 — Docker Push to Local Registry](#stage-6--docker-push-to-local-registry)
  - [Stage 7 — SBOM Generation (Syft / SPDX-JSON)](#stage-7--sbom-generation-syft--spdx-json)
- [Test Coverage Results](#test-coverage-results)
- [Docker Image](#docker-image)
- [API Endpoints](#api-endpoints)
- [Prometheus Metrics](#prometheus-metrics)
- [Team](#team)

---

## Project Overview

`ml-sentiment-app` is a machine learning microservice that performs sentiment analysis on free-text input. It is built with **FastAPI** and **TextBlob**, containerised with Docker, and shipped through a fully automated 7-stage CI pipeline running on **Gitea Actions**.

The CI pipeline enforces code quality (linting, type checking, test coverage) on every push and pull request to `main`, then builds a multi-stage Docker image, pushes it to a local registry, and generates a Software Bill of Materials (SBOM) — all without any manual intervention.

The produced image is consumed by the companion **GitOps repository** ([`team-gitops`](https://github.com/<org>/team-gitops)) which handles Kubernetes deployment via ArgoCD.

---

## Application Architecture

```
Developer
    │
    └─▶ git push to main
              │
              ▼
    ┌─────────────────────────────────────────────────┐
    │           Gitea Actions CI  (.gitea/workflows/ci.yml)       │
    │                                                             │
    │  [1] Install deps + health check                           │
    │  [2] ruff check src/ tests/          → ruff.txt artifact   │
    │  [3] mypy src/                        → mypy.txt artifact   │
    │  [4] pytest --cov=src                 → coverage artifact  │
    │  [5] docker build (multi-stage)                            │
    │  [6] docker push → localhost:5001/ml-sentiment-app:<sha>   │
    │  [7] syft → sbom.spdx.json            → SBOM artifact      │
    └─────────────────────────────────────────────────┘
              │
              ▼
    Local Docker Registry (localhost:5001 / registry.local:5000)
              │
              ▼
    GitOps repo picks up new SHA → ArgoCD deploys to k3d
```

---

## Repository Structure

```
ml-sentiment-app/
├── src/
│   ├── __init__.py
│   ├── model.py          # Sentiment classifier (TextBlob)
│   ├── preprocess.py     # Text preprocessing utilities
│   └── inference.py      # FastAPI app — /predict, /health, /metrics
├── tests/
│   ├── test_model.py
│   ├── test_preprocess.py
│   └── test_inference.py
├── .gitea/
│   └── workflows/
│       └── ci.yml        # 7-stage Gitea Actions CI pipeline
├── Dockerfile            # Multi-stage build (builder + runtime)
├── pyproject.toml        # ruff + mypy configuration
├── requirements.txt      # Pinned Python dependencies
└── .gitignore
```

---

## Getting Started (Local)

### Prerequisites

- Python 3.11+
- Docker

### Install dependencies

```bash
pip install -r requirements.txt
python -m textblob.download_corpora
```

### Run the application

```bash
uvicorn src.inference:app --reload --port 8000
```

### Run tests

```bash
pytest --cov=src --cov-report=term-missing
```

### Run code quality checks

```bash
ruff check src/ tests/
mypy src/
```

### Build Docker image locally

```bash
docker build -t ml-sentiment-app:local .
docker run -p 8000:8000 ml-sentiment-app:local
```

---

## CI Pipeline

The pipeline is defined in `.gitea/workflows/ci.yml` and is triggered on every **push** and **pull request** to `main`, as well as on version tags matching `v*` (e.g. `v1.0`, `v2.3.1`) to produce versioned images for deployment.

All quality-gate reports are consolidated into a single Gitea artifact named `ci-reports-${{ gitea.run_id }}`, uniquely tied to each CI run.

### Stage 1 — Dependency Installation & Health Check

Installs all Python dependencies from `requirements.txt`, downloads TextBlob corpora, starts the application via `uvicorn`, and confirms the `/health` endpoint is reachable before any quality gates run.

### Stage 2 — Linting with Ruff

```bash
ruff check src/ tests/
```

Enforces code style and detects common anti-patterns. The pipeline **fails immediately** if any violations are reported. Output is saved as `ruff.txt` and uploaded to the CI artifact.

### Stage 3 — Type Checking with Mypy

```bash
mypy src/
```

Runs strict static type checking with `disallow_untyped_defs = true` (configured in `pyproject.toml`). All functions — including test functions — carry return type annotations. `textblob` and `prometheus_client` are added to the mypy `ignore_missing_imports` override list to suppress third-party stub warnings. Output is saved as `mypy.txt` and uploaded to the CI artifact.

### Stage 4 — Testing with Pytest

```bash
pytest --cov=src --cov-report=term-missing
```

Executes the full test suite and generates an inline coverage report. The pipeline fails if any test fails or if coverage falls below **70%**. See [Test Coverage Results](#test-coverage-results) below. The coverage report is uploaded to the CI artifact.

### Stage 5 — Docker Multi-Stage Build

The `Dockerfile` uses a **two-stage build**:

| Stage | Base image | Purpose |
|-------|-----------|---------|
| `builder` | `python:3.11-slim` | Install all Python dependencies |
| `runtime` | `python:3.11-slim` | Copy only installed packages + app source; run as non-root `appuser` |

The multi-stage approach discards build tooling from the final image, reducing image size by ~40% compared to a single-stage build. The application runs as a **non-root user** (`appuser`) following container security best practices.

### Stage 6 — Docker Push to Local Registry

The built image is tagged with two labels and pushed to the local Docker registry:

```
localhost:5001/ml-sentiment-app:latest
localhost:5001/ml-sentiment-app:<git-sha>
```

The SHA tag is **immutable** — it permanently maps to the exact source revision that produced the image, enabling full traceability in the GitOps deployment workflow. Inside the k3d cluster, the same registry is accessible at `registry.local:5000`.

### Stage 7 — SBOM Generation (Syft / SPDX-JSON)

```bash
syft localhost:5001/ml-sentiment-app:<sha> -o spdx-json=sbom.spdx.json
```

Generates a Software Bill of Materials for the built image using [Syft](https://github.com/anchore/syft), capturing all software components, versions, and licence metadata in **SPDX JSON** format. The `sbom.spdx.json` file is uploaded to the CI artifact alongside lint and test reports.

---

## Test Coverage Results

The test suite comprises **14 test cases** covering model inference, text preprocessing, and the FastAPI HTTP layer.

| Module | Coverage | Tests |
|--------|----------|-------|
| `src/inference.py` | 92% | ✅ Passing |
| `src/model.py` | 100% | ✅ Passing |
| `src/preprocess.py` | 100% | ✅ Passing |
| **Overall** | **95%** | **14 / 14** |

> Exceeds the 70% threshold required by the assignment rubric.

---

## Docker Image

| Property | Value |
|----------|-------|
| Base image | `python:3.11-slim` |
| Build strategy | Multi-stage (builder + runtime) |
| Runtime user | `appuser` (non-root) |
| Registry (host) | `localhost:5001/ml-sentiment-app` |
| Registry (in-cluster) | `registry.local:5000/ml-sentiment-app` |
| Tags | `latest`, `<git-sha>` |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness/readiness check — returns `{"status": "ok"}` |
| `POST` | `/predict` | Sentiment prediction — accepts `{"text": "..."}`, returns label + score |
| `GET` | `/metrics` | Prometheus metrics in text exposition format |

**Example predict request:**

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a fantastic product!"}'
```

---

## Prometheus Metrics

The application exposes three custom Prometheus metrics via the `/metrics` endpoint:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `prediction_requests_total` | Counter | `method`, `endpoint`, `status` | Total prediction requests |
| `prediction_label_total` | Counter | `label` | Predictions per sentiment label |
| `prediction_request_duration_seconds` | Histogram | `method`, `endpoint` | End-to-end prediction latency |

These metrics are scraped by Prometheus via a `ServiceMonitor` CRD defined in the GitOps repository, and visualised in a Grafana dashboard with 4 panels (request rate, 5xx error rate, p50/p95/p99 latency, pod CPU/memory).

---

## Team

**Group 1 — CISC-814, Queen's University, Summer 2026**

| Member | Primary Responsibilities |
|--------|-------------------------|
| Mohamed Mahmoud | CI pipeline coordination, SBOM generation, ruff/mypy/pytest stages, Gitea Actions setup, architecture diagram |
| Ahmed Rayyan | Repository setup, branch protection, Kubernetes base manifests, kubectl validation, endpoint testing |
| Kerolos Zaka | CI/CD automation, ArgoCD manifest, GitOps sync loop validation, Argo Rollouts canary deployment |
| Kirollos Rasn | Dockerfile multi-stage build, Docker CI integration, Prometheus instrumentation, ServiceMonitor, Grafana dashboard |

---

*Part of CISC-814 Assignment 1 — see also the [GitOps repository](https://github.com/Kerolos129Yousef/ml-sentiment-app-gitops) for Kubernetes manifests, ArgoCD configuration, and monitoring.*
