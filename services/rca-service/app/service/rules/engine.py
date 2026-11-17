"""Declarative, data-driven rules engine.

Rules are loaded from YAML and evaluated against per-service summaries. Signal extraction is a
lookup table (no if/else chains), and evaluation is O(services x rules).
"""

from collections.abc import Callable
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from app.models.diagnosis import Finding, ServiceSummary

DEFAULT_RULES_PATH = Path(__file__).with_name("default_rules.yaml")
SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


class Rule(BaseModel):
    """A single detection rule."""

    name: str
    title: str
    signal: str
    threshold: float
    min_events: int = Field(default=1, ge=0)
    severity: str = "warning"
    recommendation: str


def _category_signal(summary: ServiceSummary, arg: str) -> float:
    return float(summary.by_category.get(arg, 0))


def _error_rate_signal(summary: ServiceSummary, _: str) -> float:
    return summary.error_rate


def _latency_signal(summary: ServiceSummary, _: str) -> float:
    return summary.avg_latency_ms


SIGNALS: dict[str, Callable[[ServiceSummary, str], float]] = {
    "category": _category_signal,
    "error_rate": _error_rate_signal,
    "avg_latency_ms": _latency_signal,
}


def load_rules(path: str | Path | None = None) -> list[Rule]:
    """Load and validate rules from a YAML file (safe_load only)."""
    source = Path(path) if path else DEFAULT_RULES_PATH
    data = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    rules = [Rule(**item) for item in data.get("rules", [])]
    for rule in rules:
        kind = rule.signal.split(":", 1)[0]
        if kind not in SIGNALS:
            raise ValueError(f"rule {rule.name}: unknown signal {rule.signal}")
    return rules


class RulesEngine:
    """Evaluates rules against service summaries."""

    def __init__(self, rules: list[Rule]) -> None:
        self._rules = rules

    def evaluate(self, summaries: list[ServiceSummary]) -> list[Finding]:
        """Return findings sorted by severity, then by how far the value exceeds the threshold."""
        findings: list[Finding] = []
        for summary in summaries:
            for rule in self._rules:
                kind, _, arg = rule.signal.partition(":")
                value = SIGNALS[kind](summary, arg)
                if summary.total >= rule.min_events and value >= rule.threshold:
                    findings.append(
                        Finding(
                            rule=rule.name,
                            title=rule.title,
                            service=summary.service,
                            severity=rule.severity,
                            value=round(value, 4),
                            threshold=rule.threshold,
                            recommendation=" ".join(rule.recommendation.split()),
                        )
                    )
        findings.sort(
            key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), -(f.value / f.threshold if f.threshold else f.value))
        )
        return findings
