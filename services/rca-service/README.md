# RCA Service

CloudNetSleuth's root-cause analysis API: a FastAPI service that ranks suspect services
using correlation-based reasoning, with Prometheus metrics and Kubernetes-ready assets.

## Overview

- Clean architecture (`api` → `service` → `repository`, with `models` and `config` as shared layers)
- Pluggable analysis strategies selectable per request and gated by deployment config
- Structured JSON logging with request-id propagation
- Prometheus metrics on bounded, route-template labels
- Readiness-gated startup and ordered graceful shutdown

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Basic health payload |
| `GET` | `/health/live` | Liveness probe — failure means restart the pod |
| `GET` | `/health/ready` | Readiness probe — 503 while starting or draining |
| `GET` | `/metrics` | Prometheus exposition format |
| `POST` | `/api/v1/analyze` | Rank suspected root causes |
| `GET` | `/api/v1/strategies` | List enabled analysis strategies |

### Analysis strategies

| Name | Coefficient | When to prefer it |
|---|---|---|
| `pearson` | Linear product-moment | Errors scale proportionally with latency/throughput |
| `spearman` | Monotonic rank correlation | One service is a severe outlier, or the relationship is directional but not proportional |

Both share the scoring in `CorrelationStrategy`: two population coefficients (latency vs.
error rate, throughput vs. error rate) weight per-service features that are min-max
normalised first, so neither term silently dominates. Complexity is **O(n log n)** in the
number of services, dominated by the final sort and by rank transforms in `spearman`.

Adding a strategy means creating a `CorrelationStrategy` subclass, registering it in
`app/service/strategies/registry.py`, and adding its name to `RCA_ENABLED_STRATEGIES`.

> **Scope note.** The correlation is computed *across services at one instant*, not across
> time. With a handful of services the coefficient rests on very few points and should be
> read as a heuristic ranking, not a statistical claim. Time-series input is the natural
> next step and would change the request schema.

## Configuration

Every setting is read from a `RCA_`-prefixed environment variable — see
[`.env.example`](.env.example) for the full list and defaults.

| Variable | Default | Purpose |
|---|---|---|
| `RCA_ENVIRONMENT` | `dev` | Deployment environment, echoed into every log line |
| `RCA_LOG_LEVEL` | `INFO` | Root log level |
| `RCA_DEFAULT_STRATEGY` | `pearson` | Strategy used when a request does not name one |
| `RCA_ENABLED_STRATEGIES` | `pearson,spearman` | Allowlist of selectable strategies |
| `RCA_TOP_K_CAUSES` | `3` | Number of ranked causes returned |

## Local Run Instructions

```bash
cd services/rca-service && python3.11 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
```

```bash
cd services/rca-service && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Interactive API docs are then at `http://localhost:8080/docs`.

## Run Tests and Lint

```bash
cd services/rca-service && .venv/bin/pytest && .venv/bin/ruff check . && .venv/bin/ruff format --check .
```

## Docker Build Instructions

```bash
cd services/rca-service && docker build -t cloudnetsleuth/rca-service:latest .
```

```bash
docker run --rm -p 8080:8080 -e RCA_ENVIRONMENT=dev cloudnetsleuth/rca-service:latest
```

The build is multi-stage: wheels are compiled in a builder stage so the runtime image
carries no toolchain, test dependencies, or test code. It runs as UID 1001.

## Kubernetes Deployment Steps

```bash
kubectl apply -f services/rca-service/k8s/deployment.yaml -f services/rca-service/k8s/service.yaml
```

```bash
kubectl rollout status deployment/rca-service && kubectl get pods -l app=rca-service
```

The pod spec drops all capabilities, runs with a read-only root filesystem as a non-root
user, and declares `RuntimeDefault` seccomp.

### Verify in a local cluster

`kind` runs a throwaway cluster against the local Docker daemon:

```bash
kind create cluster --name cloudnetsleuth && kind load docker-image cloudnetsleuth/rca-service:latest --name cloudnetsleuth
```

Then apply the manifests above. To prove a rollout is zero-downtime, drive continuous
traffic at `/health/ready` from an in-cluster pod while running:

```bash
kubectl rollout restart deployment/rca-service && kubectl rollout status deployment/rca-service
```

```bash
kind delete cluster --name cloudnetsleuth
```

### Shutdown ordering

1. **`preStop` hook (5s)** — runs *before* SIGTERM. The app keeps serving normally while
   Kubernetes propagates the endpoint removal. This is the window that actually drains
   traffic.
2. **SIGTERM** — uvicorn closes the listening socket and finishes in-flight requests
   within its 20s `--timeout-graceful-shutdown` budget.
3. **Lifespan shutdown** — readiness state flips and the process exits cleanly.

All of it fits inside the 30s `terminationGracePeriodSeconds`. Verified in a `kind`
cluster: pod deletion completes in ~6.2s (5s `preStop` plus shutdown), and a rolling
restart under continuous load served 20,193 requests with zero failures.

> Once SIGTERM lands the listening socket is already closed, so `/health/ready` refuses
> connections rather than answering `503`. Kubernetes treats both as probe failure, but it
> means a post-SIGTERM sleep inside the app would drain nothing — the `preStop` hook is
> load-bearing, not decorative.

## API Example Request

```bash
curl -X POST "http://localhost:8080/api/v1/analyze" -H "Content-Type: application/json" -d '{"strategy":"spearman","metrics":[{"service_name":"gateway","error_rate":0.4,"latency_ms":250,"throughput_rps":120},{"service_name":"auth","error_rate":0.15,"latency_ms":130,"throughput_rps":180},{"service_name":"db","error_rate":0.3,"latency_ms":220,"throughput_rps":90}]}'
```

```json
{
  "top_causes": [
    {"service_name": "gateway", "correlation_score": 1.3333, "confidence": 0.85},
    {"service_name": "db", "correlation_score": 1.1, "confidence": 0.85},
    {"service_name": "auth", "correlation_score": 0.0, "confidence": 0.85}
  ],
  "strategy": "spearman",
  "analyzed_services": 3
}
```

`strategy` is optional and defaults to `RCA_DEFAULT_STRATEGY`. Requests are rejected with
`422` when fewer than two services are supplied, when error rates are constant (correlation
is undefined without variance), or when the requested strategy is unknown or disabled.

## Metrics

| Metric | Type | Labels |
|---|---|---|
| `http_requests_total` | Counter | `method`, `endpoint`, `status` |
| `http_request_latency_seconds` | Histogram | `method`, `endpoint` |
| `http_error_total` | Counter | `endpoint` |
| `rca_analysis_total` | Counter | `strategy`, `outcome` |
| `rca_analysis_duration_seconds` | Histogram | `strategy` |

`endpoint` is always the matched route template (`/api/v1/analyze`), never the raw request
path, so cardinality stays bounded; unmatched requests collapse to `unmatched`.
