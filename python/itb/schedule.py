# impl: FR-002-06
"""Вікна лідера з getLeaderSchedule і snapshot версій з getClusterNodes."""

from __future__ import annotations


def windows(schedule: dict, validator_identity: str, epoch: int) -> list:
    """Згрупувати послідовні слоти валідатора у вікна."""
    slots = sorted(schedule.get(validator_identity, []))
    out = []
    if not slots:
        return out
    start = prev = slots[0]
    for s in slots[1:]:
        if s == prev + 1:
            prev = s
            continue
        out.append({"validator": validator_identity, "epoch": epoch,
                    "start_slot": start, "end_slot": prev})
        start = prev = s
    out.append({"validator": validator_identity, "epoch": epoch,
                "start_slot": start, "end_slot": prev})
    return out


def snapshot(nodes: list, source: str = "getClusterNodes") -> dict:
    """Знімок версій для validators_snapshot.json."""
    return {
        "source": source,
        "validators": [
            {"identity": n.get("pubkey"), "version": n.get("version"),
             "stake": n.get("stake")}
            for n in nodes
        ],
    }
