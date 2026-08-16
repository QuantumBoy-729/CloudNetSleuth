# CloudNetSleuth – Copilot Instructions

## Project Overview

CloudNetSleuth is a cloud-native Network Observability and Root Cause Analysis (RCA) platform.

Architecture:

- Microservices-based
- Python 3.11
- FastAPI
- Kubernetes-native
- Dockerized services
- Clean Architecture (layered design)

The goal is production-grade, resume-level quality code.

---

## Engineering Principles

1. Follow Clean Architecture:
   - api/ (controllers, routers)
   - service/ (business logic)
   - repository/ (data access)
   - models/ (pydantic/domain models)
   - config/
   - tests/

2. Code must be:
   - Modular
   - Testable
   - Dependency-injected
   - Typed (Python typing required)
   - Lint-compliant (PEP8)

3. No monolithic files.
4. No hardcoded values — use environment variables.
5. Structured logging (JSON format).
6. Proper error handling with HTTP status codes.

---

## Microservice Requirements

Every service must include:

- /health endpoint
- /metrics endpoint (Prometheus compatible)
- Graceful shutdown handling
- requirements.txt
- Dockerfile
- Kubernetes deployment.yaml
- Kubernetes service.yaml
- README.md

---

## Observability Requirements

- Expose Prometheus metrics using prometheus_client.
- Use OpenTelemetry hooks where applicable.
- Log in structured JSON format.
- Track request latency metrics.
- Track error count metrics.

---

## API Standards

- Use FastAPI.
- Use Pydantic models.
- Explicit request and response models.
- OpenAPI auto-generation enabled.
- Version APIs under /api/v1.

---

## Testing Standards

- Use pytest.
- Minimum:
  - Unit tests for service layer.
  - API endpoint test using TestClient.
- Mock external dependencies.
- No external network calls in tests.

---

## Docker Standards

- Use python:3.11-slim.
- Multi-stage build preferred.
- Non-root user inside container.
- Expose correct port.
- Use uvicorn production server.

---

## Kubernetes Standards

- Liveness probe
- Readiness probe
- Resource limits (CPU + memory)
- Environment variables defined in deployment
- Labels must include:
  app: <service-name>
  platform: cloudnetsleuth

---

## RCA Engine Design Rules

- RCA must not use naive if-else logic.
- Use statistical or correlation-based reasoning.
- Implement pluggable analysis strategies.
- Ensure algorithmic complexity is considered.

---

## Code Generation Rules for Copilot

When generating new features:

1. Respect folder structure.
2. Do not collapse architecture layers.
3. Add unit tests automatically.
4. Include type hints.
5. Add docstrings.
6. Follow SOLID principles.
7. Avoid global state.

---

## Performance Expectations

- Async endpoints preferred.
- Avoid blocking I/O.
- Use connection pooling if applicable.
- Cache only when justified.

---

## Security Requirements

- Input validation mandatory.
- No unsafe deserialization.
- No plain-text secrets.
- Assume services may run in multi-tenant cluster.

---

## Documentation Requirements

Each microservice must contain:

- README.md
  - Overview
  - Local run instructions
  - Docker build instructions
  - Kubernetes deployment steps
  - API example request

---

## Long-Term Architecture Goals

- Distributed tracing
- Event-driven anomaly pipeline
- Correlation graph engine
- Topology auto-discovery
- Adaptive thresholding
