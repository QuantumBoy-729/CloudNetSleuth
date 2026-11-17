"""Failure-category classification for log messages."""

import re

# Ordered: first match wins. Declarative table instead of branching logic.
CATEGORY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("oom_killed", re.compile(r"oomkilled|out of memory", re.I)),
    ("crash_loop", re.compile(r"crashloopbackoff|back-off restarting", re.I)),
    ("dns_failure", re.compile(r"name resolution|nxdomain|no such host|dns", re.I)),
    ("connection_refused", re.compile(r"connection refused|econnrefused", re.I)),
    ("network_timeout", re.compile(r"timed? ?out|timeout|deadline exceeded", re.I)),
    ("service_unavailable", re.compile(r"\b503\b|unavailable|circuit (breaker )?open", re.I)),
    ("http_5xx", re.compile(r"\b5\d\d\b")),
]
DEFAULT_CATEGORY = "other"


def classify(message: str) -> str:
    """Return the failure category of the message (``other`` if none match)."""
    for category, pattern in CATEGORY_PATTERNS:
        if pattern.search(message):
            return category
    return DEFAULT_CATEGORY
