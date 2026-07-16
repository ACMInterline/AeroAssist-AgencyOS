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
from smoke_inventory import SMOKE_INVENTORY_PATH, SMOKE_INVENTORY_SUMMARY, load_smoke_inventory
from validate_ci_foundation import EXPECTED_PHASE, validate_ci_foundation


def main() -> None:
    errors = validate_ci_foundation()
    if errors:
        raise AssertionError("CI foundation validation failed: " + "; ".join(errors))
    if not phase_is_exact(CURRENT_BUILD_PHASE, EXPECTED_PHASE):
        raise AssertionError(f"Canonical current build phase mismatch: {CURRENT_BUILD_PHASE}")

    expected_manifest = BACKEND / "scripts" / "smoke_inventory.json"
    if SMOKE_INVENTORY_PATH != expected_manifest or not SMOKE_INVENTORY_PATH.is_file():
        raise AssertionError(f"Production inventory path is invalid: {SMOKE_INVENTORY_PATH}")
    inventory = load_smoke_inventory()
    if SMOKE_INVENTORY_SUMMARY["inventoried_smoke_scripts"] != len(inventory["scripts"]):
        raise AssertionError("Runtime smoke inventory summary does not match the manifest.")

    health = get("/api/health")
    readiness = get("/api/readiness")
    if not phase_is_exact(health.get("phase"), CURRENT_BUILD_PHASE):
        raise AssertionError(f"Health phase mismatch: {health.get('phase')}")
    if not phase_is_exact(readiness.get("phase"), CURRENT_BUILD_PHASE):
        raise AssertionError(f"Readiness phase mismatch: {readiness.get('phase')}")

    section = readiness.get("github_actions_continuous_integration_foundation") or {}
    required_true = (
        "fast_ci_workflow_enabled",
        "docker_ci_workflow_enabled",
        "focused_smoke_ci_workflow_enabled",
        "full_regression_workflow_enabled",
        "inventory_driven_ci_enabled",
        "production_import_validation_enabled",
        "frontend_build_validation_enabled",
        "backend_compile_validation_enabled",
        "current_phase_validation_enabled",
        "production_deployment_disabled",
    )
    for key in required_true:
        if section.get(key) is not True:
            raise AssertionError(f"CI readiness flag is not enabled: {key}")
    if section.get("production_secrets_required") is not False:
        raise AssertionError("CI foundation must not require production secrets.")
    if section.get("workflow_count") != 4:
        raise AssertionError(f"Unexpected CI workflow count: {section.get('workflow_count')}")
    if section.get("inventoried_smoke_scripts") != len(inventory["scripts"]):
        raise AssertionError("CI readiness inventory count does not match the manifest.")
    if section.get("unresolved_scripts") != 0:
        raise AssertionError("CI readiness reports unresolved smoke inventory entries.")

    print("Phase 56.5.3 GitHub Actions continuous integration foundation smoke passed.")


if __name__ == "__main__":
    main()
