import json
import random

from simulator.generator import fault_active, generate_batch


def test_healthy_batch_has_only_info() -> None:
    lines = generate_batch(random.Random(1), fault=False)
    assert {json.loads(x)["level"] for x in lines} == {"INFO"}


def test_fault_batch_cascades_from_db() -> None:
    lines = [json.loads(x) for x in generate_batch(random.Random(1), fault=True)]
    errors = {x["service"] for x in lines if x["level"] == "ERROR"}
    assert errors == {"db", "orders", "gateway"}


def test_fault_schedule() -> None:
    assert not fault_active(5, period=10, duration=4)
    assert fault_active(10, period=10, duration=4)
    assert not fault_active(14, period=10, duration=4)
    assert not fault_active(3, period=0, duration=4)
