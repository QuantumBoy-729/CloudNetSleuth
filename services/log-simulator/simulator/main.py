"""Entrypoint: periodically POST synthetic log batches to the log-ingestor."""

import logging
import os
import random
import time

import httpx

from simulator.generator import fault_active, generate_batch

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","message":"%(message)s"}')
log = logging.getLogger("simulator")


def main() -> None:
    """Run forever; configuration comes from SIM_* environment variables."""
    url = os.environ.get("SIM_INGESTOR_URL", "http://log-ingestor:8081").rstrip("/")
    interval = float(os.environ.get("SIM_INTERVAL_SECONDS", "1"))
    period = int(os.environ.get("SIM_FAULT_PERIOD_TICKS", "120"))
    duration = int(os.environ.get("SIM_FAULT_DURATION_TICKS", "50"))
    rng = random.Random(int(os.environ.get("SIM_SEED", "42")))
    tick = 0
    previous = False
    with httpx.Client(timeout=5.0) as client:
        while True:
            fault = fault_active(tick, period, duration)
            if fault != previous:
                log.info("fault on db: %s", "STARTED" if fault else "RESOLVED")
                previous = fault
            try:
                resp = client.post(f"{url}/api/v1/logs", json={"lines": generate_batch(rng, fault)})
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                log.warning("ingest failed: %s", exc)
            tick += 1
            time.sleep(interval)


if __name__ == "__main__":
    main()
