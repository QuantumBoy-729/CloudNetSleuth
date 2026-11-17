# Log Ingestor

Receives raw log lines from Kubernetes workloads (JSON or `<ts> <LEVEL> <service> <message>`), parses them,
classifies each into a failure category (`network_timeout`, `connection_refused`, `dns_failure`,
`service_unavailable`, `http_5xx`, `oom_killed`, `crash_loop`, `other`), exports Prometheus metrics and keeps a
bounded in-memory sliding window that the RCA service queries.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/logs` | Ingest `{"lines": [...]}` (returns accepted/rejected counts) |
| GET | `/api/v1/summary?window_seconds=60` | Per-service error rate, latency, throughput, category counts |
| GET | `/api/v1/events?limit=50&service=db` | Recent parsed events |
| GET | `/health`, `/metrics` | Probes and Prometheus metrics (`cns_log_events_total`, ...) |

## Configuration (env, prefix `INGEST_`)

`LOG_LEVEL`, `MAX_EVENTS` (default 50000), `MAX_BATCH_LINES` (1000), `MAX_LINE_LENGTH` (4096).

## Run locally

```bash
cd services/log-ingestor
python -m venv .venv && . .venv/Scripts/activate   # PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --port 8081
pytest -q
```

## Docker

```bash
docker build -t cloudnetsleuth/log-ingestor:latest .
docker run --rm -p 8081:8081 cloudnetsleuth/log-ingestor:latest
```

## Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
```

## Example

```bash
curl -X POST localhost:8081/api/v1/logs -H "Content-Type: application/json" -d '{
  "lines": [
    "{\"level\":\"ERROR\",\"service\":\"db\",\"message\":\"query timed out\",\"latency_ms\":5000}",
    "2026-01-01T00:00:00Z WARN orders slow response 1200ms"
  ]}'
curl "localhost:8081/api/v1/summary?window_seconds=60"
```
