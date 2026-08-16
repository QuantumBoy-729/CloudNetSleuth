# CloudNetSleuth

A cloud-native network observability and root-cause analysis platform, built as
Kubernetes-native Python microservices.

## Services

| Service | Status | Description |
|---|---|---|
| [rca-service](services/rca-service) | Active | Correlation-based root-cause analysis API |

## Repository Layout

```
.github/
  copilot-instructions.md   Engineering standards every service must meet
  workflows/                Per-service CI pipelines
services/
  <service-name>/
    app/
      api/                  Routers and DI wiring
      service/              Business logic
      repository/           Data access
      models/               Pydantic domain models
      config/               Settings, logging, metrics, lifecycle state
    tests/
    k8s/                    deployment.yaml + service.yaml
    Dockerfile
    requirements.txt        Runtime dependencies only
    requirements-dev.txt    Runtime + lint/test dependencies
```

Each service is independently buildable, deployable, and testable. The engineering
standards all services are held to live in
[.github/copilot-instructions.md](.github/copilot-instructions.md).

## Getting Started

Services target **Python 3.11**. Working on the RCA service:

```bash
cd services/rca-service && python3.11 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
```

```bash
cd services/rca-service && .venv/bin/pytest && .venv/bin/ruff check .
```

See [services/rca-service/README.md](services/rca-service/README.md) for run, Docker, and
Kubernetes instructions.

## Platform Conventions

Every service exposes `/health`, `/health/live`, `/health/ready`, and `/metrics`; logs
structured JSON with a propagated `X-Request-ID`; versions its API under `/api/v1`; reads
all configuration from prefixed environment variables; and ships a non-root, multi-stage
container image with a hardened pod spec.

Kubernetes objects carry both labels:

```yaml
app: <service-name>
platform: cloudnetsleuth
```

## Roadmap

Longer-term platform goals, in rough dependency order:

- Distributed tracing across services (OpenTelemetry)
- Time-series RCA input, replacing point-in-time cross-service correlation
- Event-driven anomaly detection pipeline
- Correlation graph engine
- Topology auto-discovery
- Adaptive thresholding
