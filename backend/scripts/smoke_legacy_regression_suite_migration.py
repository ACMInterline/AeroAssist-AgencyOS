#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from build_phase import CURRENT_BUILD_PHASE, phase_is_exact
from smoke_booking_pnr_foundation import get
from smoke_inventory import load_smoke_inventory, summarize_smoke_inventory
from validate_smoke_inventory import validate_inventory


EXPECTED_CURRENT_PHASE = "phase_56_5_2_legacy_regression_suite_migration"


def verify_inventory() -> dict[str, int | bool]:
    inventory = load_smoke_inventory()
    summary, errors = validate_inventory()
    if errors:
        raise AssertionError("Smoke inventory validation failed: " + "; ".join(errors))
    if summary["unresolved_scripts"] != 0 or not summary["inventory_validation_ready"]:
        raise AssertionError(f"Smoke inventory contains unresolved entries: {summary}")
    if summary != summarize_smoke_inventory(inventory):
        raise AssertionError("Smoke inventory summary is nondeterministic.")
    allowlist = inventory.get("exact_current_allowlist") or []
    if len(allowlist) != 1 or allowlist[0].get("script_path") != "backend/scripts/smoke_legacy_regression_suite_migration.py":
        raise AssertionError(f"Exact-current assertion allowlist is invalid: {allowlist}")
    return summary


def verify_historical_provenance() -> None:
    preserved = {
        ROOT / "backend/models.py": 'introduced_phase: str = "phase_40_1_capability_catalog_foundation"',
        ROOT / "backend/services/knowledge_import_template_service.py": 'FOUNDATION_PHASE_LABEL = "phase_52_2_knowledge_import_templates_foundation"',
        ROOT / "backend/services/offer_delivery_client_interaction_service.py": 'event_source="phase_56_4"',
    }
    for path, text in preserved.items():
        if text not in path.read_text(encoding="utf-8"):
            raise AssertionError(f"Historical provenance changed unexpectedly in {path.relative_to(ROOT)}: {text}")


def verify_runtime(summary: dict[str, int | bool]) -> None:
    health = get("/api/health")
    readiness = get("/api/readiness")
    if not phase_is_exact(health.get("phase"), CURRENT_BUILD_PHASE):
        raise AssertionError(f"Health current phase mismatch: {health.get('phase')}")
    if not phase_is_exact(readiness.get("phase"), CURRENT_BUILD_PHASE):
        raise AssertionError(f"Readiness current phase mismatch: {readiness.get('phase')}")
    if not phase_is_exact(CURRENT_BUILD_PHASE, EXPECTED_CURRENT_PHASE):
        raise AssertionError(f"Canonical current build phase mismatch: {CURRENT_BUILD_PHASE}")
    section = readiness.get("legacy_regression_suite_migration") or {}
    for key in (
        "total_smoke_scripts",
        "inventoried_smoke_scripts",
        "minimum_phase_scripts",
        "intentional_exact_current_scripts",
        "no_phase_scripts",
        "unresolved_scripts",
    ):
        if section.get(key) != summary[key]:
            raise AssertionError(f"Readiness inventory count mismatch for {key}: {section.get(key)} != {summary[key]}")
    if section.get("inventory_validation_ready") is not True:
        raise AssertionError("Legacy regression inventory is not readiness-valid.")


def main() -> None:
    summary = verify_inventory()
    verify_historical_provenance()
    verify_runtime(summary)
    print("Phase 56.5.2 legacy regression suite migration smoke passed.")


if __name__ == "__main__":
    main()
