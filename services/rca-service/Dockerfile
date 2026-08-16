# syntax=docker/dockerfile:1

# ---- build stage: compile wheels so the runtime image carries no toolchain ----
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY requirements.txt ./
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# ---- runtime stage ----
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# UID/GID are pinned so the Kubernetes securityContext can assert runAsUser 1001.
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --ingroup appgroup --no-create-home appuser

COPY --from=builder /wheels /wheels
COPY requirements.txt ./
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels requirements.txt

COPY --chown=appuser:appgroup app ./app

USER 1001
EXPOSE 8080

# Matches the k8s terminationGracePeriodSeconds budget minus the preStop drain.
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--timeout-graceful-shutdown", "20"]
