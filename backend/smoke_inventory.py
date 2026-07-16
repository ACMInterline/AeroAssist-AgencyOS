from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


SMOKE_INVENTORY_PATH = Path(__file__).resolve().parent / "scripts" / "smoke_inventory.json"


@lru_cache(maxsize=1)
def load_smoke_inventory() -> dict[str, Any]:
    try:
        with SMOKE_INVENTORY_PATH.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Smoke inventory manifest is missing: {SMOKE_INVENTORY_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Smoke inventory manifest is malformed: {SMOKE_INVENTORY_PATH}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("scripts"), list):
        raise ValueError(f"Smoke inventory manifest must contain a scripts array: {SMOKE_INVENTORY_PATH}")
    return payload


def summarize_smoke_inventory(payload: dict[str, Any] | None = None) -> dict[str, int | bool]:
    inventory = load_smoke_inventory() if payload is None else payload
    scripts = inventory.get("scripts") or []
    mode_counts = {
        mode: sum(1 for item in scripts if item.get("phase_assertion_mode") == mode)
        for mode in ("minimum", "exact_current", "none")
    }
    unresolved = sum(1 for item in scripts if item.get("phase_assertion_mode") not in mode_counts)
    return {
        "total_smoke_scripts": len(scripts),
        "inventoried_smoke_scripts": len(scripts),
        "minimum_phase_scripts": mode_counts["minimum"],
        "intentional_exact_current_scripts": mode_counts["exact_current"],
        "no_phase_scripts": mode_counts["none"],
        "unresolved_scripts": unresolved,
        "inventory_validation_ready": unresolved == 0,
    }


SMOKE_INVENTORY_SUMMARY = summarize_smoke_inventory()
