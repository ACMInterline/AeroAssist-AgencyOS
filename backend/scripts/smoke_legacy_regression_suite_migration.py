#!/usr/bin/env python3
from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from build_phase import CURRENT_BUILD_PHASE
from phase_assertions import assert_application_phase_at_least
from smoke_booking_pnr_foundation import get
from smoke_inventory import (
    SMOKE_INVENTORY_PATH,
    SMOKE_INVENTORY_SUMMARY,
    load_smoke_inventory,
    summarize_smoke_inventory,
)
from validate_smoke_inventory import validate_inventory


MINIMUM_PHASE = "phase_56_5_2_legacy_regression_suite_migration"


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
    if len(allowlist) != 1 or allowlist[0].get("script_path") != "backend/scripts/smoke_authentication_security_http_hardening_foundation.py":
        raise AssertionError(f"Exact-current assertion allowlist is invalid: {allowlist}")
    return summary


def verify_runtime_inventory_module(summary: dict[str, int | bool]) -> None:
    expected_manifest = BACKEND / "scripts" / "smoke_inventory.json"
    if SMOKE_INVENTORY_PATH != expected_manifest:
        raise AssertionError(
            f"Runtime inventory path is not module-relative: {SMOKE_INVENTORY_PATH} != {expected_manifest}"
        )
    if not SMOKE_INVENTORY_PATH.is_file():
        raise AssertionError(f"Runtime inventory manifest is missing: {SMOKE_INVENTORY_PATH}")
    if SMOKE_INVENTORY_SUMMARY != summary:
        raise AssertionError(
            f"Runtime inventory summary differs from validator counts: {SMOKE_INVENTORY_SUMMARY} != {summary}"
        )

    loader_path = BACKEND / "smoke_inventory.py"
    loader_text = loader_path.read_text(encoding="utf-8")
    server_text = (BACKEND / "server.py").read_text(encoding="utf-8")
    for text in [
        "SMOKE_INVENTORY_PATH = Path(__file__).resolve().parent",
        "@lru_cache(maxsize=1)",
        "SMOKE_INVENTORY_SUMMARY = summarize_smoke_inventory()",
    ]:
        if text not in loader_text:
            raise AssertionError(f"Runtime inventory loader is missing production-safe behavior: {text}")
    for forbidden in (".glob(", ".rglob(", "os.walk("):
        if forbidden in loader_text:
            raise AssertionError(f"Runtime inventory loader scans the repository filesystem: {forbidden}")
    if "from smoke_inventory import SMOKE_INVENTORY_SUMMARY" not in server_text:
        raise AssertionError("Server does not import the canonical runtime inventory summary module.")
    if "**SMOKE_INVENTORY_SUMMARY" not in server_text:
        raise AssertionError("Readiness does not expose the cached runtime inventory summary.")

    server_module = import_module("server")
    if server_module.SMOKE_INVENTORY_SUMMARY != summary:
        raise AssertionError("Direct server import did not expose the canonical inventory summary.")


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
    assert_application_phase_at_least(health.get("phase"), MINIMUM_PHASE, source="health")
    assert_application_phase_at_least(readiness.get("phase"), MINIMUM_PHASE, source="readiness")
    assert_application_phase_at_least(CURRENT_BUILD_PHASE, MINIMUM_PHASE, source="canonical build marker")
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
    verify_runtime_inventory_module(summary)
    verify_historical_provenance()
    verify_runtime(summary)
    print("Phase 56.5.2 legacy regression suite migration smoke passed.")


if __name__ == "__main__":
    main()
