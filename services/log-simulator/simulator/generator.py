"""Synthetic Kubernetes-style log generation with an injectable cascading fault."""

import json
import random
from datetime import datetime, timezone

SERVICES = ["gateway", "auth", "orders", "db"]
FAULT_SERVICE = "db"


def _line(service: str, level: str, message: str, latency_ms: float, now: datetime) -> str:
    return json.dumps(
        {
            "ts": now.isoformat(),
            "level": level,
            "service": service,
            "message": message,
            "latency_ms": round(latency_ms, 1),
        }
    )


def fault_active(tick: int, period: int, duration: int) -> bool:
    """The fault is on for the first `duration` ticks of every `period`-tick cycle (after one healthy cycle)."""
    if period <= 0 or tick < period:
        return False
    return (tick % period) < duration


def generate_batch(rng: random.Random, fault: bool, per_service: int = 6, now: datetime | None = None) -> list[str]:
    """Generate one batch of log lines for all services.

    When `fault` is set, `db` suffers network timeouts and the failure cascades:
    `orders` reports upstream timeouts and `gateway` returns 5xx/503.
    """
    stamp = now or datetime.now(timezone.utc)
    lines: list[str] = []
    for service in SERVICES:
        for _ in range(per_service):
            lines.append(_line(service, "INFO", "request handled ok", rng.uniform(15, 80), stamp))
    if not fault:
        return lines
    for _ in range(per_service * 2):
        lines.append(_line("db", "ERROR", "query timed out after 5000ms, i/o timeout to storage", rng.uniform(4500, 5500), stamp))
    for _ in range(per_service):
        lines.append(_line("orders", "ERROR", "upstream timeout calling db: context deadline exceeded", rng.uniform(2500, 3500), stamp))
    for _ in range(per_service // 2):
        lines.append(_line("gateway", "ERROR", "upstream returned 503 service unavailable", rng.uniform(900, 1500), stamp))
    return lines
