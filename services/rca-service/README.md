# RCA Service

CloudNetSleuth RCA Service provides a FastAPI-based root-cause analysis API with Prometheus metrics and Kubernetes-ready deployment assets.

## Overview

- Clean architecture layout (`api`, `service`, `repository`, `models`, `config`, `tests`)
- Endpoints:
  - `GET /health`
  - `GET /metrics`
  - `POST /api/v1/analyze`
- Correlation-based RCA strategy (Pearson correlation, pluggable strategy contract)

## Local Run Instructions

```bash
cd services/rca-service
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## Run Tests

```bash
cd services/rca-service
pytest -q
```

## Docker Build Instructions

```bash
cd services/rca-service
docker build -t cloudnetsleuth/rca-service:latest .
docker run --rm -p 8080:8080 cloudnetsleuth/rca-service:latest
```

## Kubernetes Deployment Steps

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl get pods -l app=rca-service
kubectl get svc rca-service
```

## API Example Request

```bash
curl -X POST "http://localhost:8080/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": [
      {"service_name": "gateway", "error_rate": 0.4, "latency_ms": 250, "throughput_rps": 120},
      {"service_name": "auth", "error_rate": 0.15, "latency_ms": 130, "throughput_rps": 180},
      {"service_name": "db", "error_rate": 0.3, "latency_ms": 220, "throughput_rps": 90}
    ]
  }'
```

