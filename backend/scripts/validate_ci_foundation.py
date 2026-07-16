#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from build_phase import CURRENT_BUILD_PHASE, phase_is_at_least
from smoke_inventory import load_smoke_inventory
from validate_smoke_inventory import validate_inventory


MINIMUM_PHASE = "phase_56_5_3_github_actions_continuous_integration_foundation"
WORKFLOW_SPECS = {
    ".github/workflows/ci-fast.yml": (
        "pull_request:",
        "push:",
        "python3 -m compileall -q backend",
        "validate_smoke_inventory.py",
        "validate_ci_foundation.py",
        "npm run build --prefix frontend",
        "import smoke_inventory, server",
    ),
    ".github/workflows/ci-docker.yml": (
        "pull_request:",
        "push:",
        "workflow_dispatch:",
        "docker build --file backend/Dockerfile",
        "/app/smoke_inventory.py",
        "/app/scripts/smoke_inventory.json",
        "import smoke_inventory, server",
        "/api/health",
        "/api/readiness",
    ),
    ".github/workflows/ci-smoke-focused.yml": (
        "pull_request:",
        "push:",
        "workflow_dispatch:",
        "run_smoke_inventory.py",
        "--tier static",
        "--tier focused",
        "--result-json",
    ),
    ".github/workflows/ci-regression-full.yml": (
        "workflow_dispatch:",
        "schedule:",
        "mongo:7",
        "run_smoke_inventory.py",
        "--isolation none",
        "--isolation shared_backend",
        "--isolation fresh_backend",
        "--result-json",
    ),
}
ALLOWED_ACTIONS = {
    "actions/checkout@v4",
    "actions/setup-python@v5",
    "actions/setup-node@v4",
    "actions/upload-artifact@v4",
}
FORBIDDEN_WORKFLOW_PATTERNS = {
    "continue-on-error": "Required CI checks must not ignore failures.",
    "secrets.": "CI foundation must not consume repository secrets.",
    "hostinger": "CI foundation must not connect to production hosting.",
    "appleboy/": "CI foundation must not use SSH deployment actions.",
    "docker/login-action": "CI foundation must not authenticate to a registry.",
    "docker/build-push-action": "CI foundation must not publish images.",
    "contents: write": "Workflow permissions must remain read-only.",
    "packages: write": "Workflow permissions must not publish packages.",
    "deployments: write": "Workflow permissions must not deploy.",
    "pull-requests: write": "Workflow permissions must not mutate pull requests.",
}


def validate_workflow(path: Path, required_tokens: tuple[str, ...]) -> list[str]:
    relative = path.relative_to(ROOT)
    if not path.is_file():
        return [f"Missing workflow: {relative}"]
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if "\t" in text:
        errors.append(f"{relative}: tabs are not valid workflow indentation")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.strip() and (len(line) - len(line.lstrip(" "))) % 2:
            errors.append(f"{relative}:{line_number}: indentation must use two-space increments")
    for key in ("name:", "on:", "permissions:", "jobs:"):
        if not any(line.startswith(key) for line in text.splitlines()):
            errors.append(f"{relative}: missing top-level {key[:-1]}")
    if "contents: read" not in text:
        errors.append(f"{relative}: missing least-privilege contents: read permission")
    for token in required_tokens:
        if token not in text:
            errors.append(f"{relative}: missing required workflow behavior {token!r}")
    lower = text.lower()
    for pattern, message in FORBIDDEN_WORKFLOW_PATTERNS.items():
        if pattern in lower:
            errors.append(f"{relative}: {message}")
    for action in re.findall(r"uses:\s*([^\s#]+)", text):
        if action not in ALLOWED_ACTIONS:
            errors.append(f"{relative}: unsupported or unpinned action {action!r}")
    return errors


def validate_ci_foundation() -> list[str]:
    errors: list[str] = []
    if not phase_is_at_least(CURRENT_BUILD_PHASE, MINIMUM_PHASE):
        errors.append(f"Current build phase is {CURRENT_BUILD_PHASE!r}, expected at least {MINIMUM_PHASE!r}")

    for relative, tokens in WORKFLOW_SPECS.items():
        errors.extend(validate_workflow(ROOT / relative, tokens))

    summary, inventory_errors = validate_inventory()
    errors.extend(inventory_errors)
    inventory = load_smoke_inventory()
    entries = inventory.get("scripts") or []
    entry_by_path = {entry.get("script_path"): entry for entry in entries}
    allowlist = inventory.get("exact_current_allowlist") or []
    exact_path = "backend/scripts/smoke_authentication_security_http_hardening_foundation.py"
    ci_path = "backend/scripts/smoke_github_actions_continuous_integration_foundation.py"
    legacy_path = "backend/scripts/smoke_legacy_regression_suite_migration.py"
    if len(allowlist) != 1 or allowlist[0].get("script_path") != exact_path:
        errors.append("The active release-registration smoke must be the sole exact-current allowlist entry.")
    if entry_by_path.get(exact_path, {}).get("phase_assertion_mode") != "exact_current":
        errors.append("The active release-registration smoke is not classified as exact_current.")
    if entry_by_path.get(ci_path, {}).get("phase_assertion_mode") != "minimum":
        errors.append("Phase 56.5.3 smoke did not migrate to minimum-phase semantics.")
    if entry_by_path.get(legacy_path, {}).get("phase_assertion_mode") != "minimum":
        errors.append("Phase 56.5.2 smoke did not migrate to minimum-phase semantics.")
    if summary.get("unresolved_scripts") != 0:
        errors.append("Smoke inventory contains unresolved entries.")
    if not any(entry.get("ci_tier") == "focused" for entry in entries):
        errors.append("Smoke inventory has no focused CI tier.")
    if not any(entry.get("execution_isolation") == "fresh_backend" for entry in entries):
        errors.append("Smoke inventory does not identify any fresh-backend state-sensitive test.")

    focused_paths = {
        entry.get("script_path") for entry in entries if entry.get("ci_tier") == "focused"
    }
    required_focused = {
        exact_path,
        ci_path,
        legacy_path,
        "backend/scripts/smoke_phase_marker_regression_integrity_foundation.py",
        "backend/scripts/smoke_backend.py",
        "backend/scripts/smoke_platform_agency_ux_consolidation.py",
        "backend/scripts/smoke_operational_request_builder.py",
        "backend/scripts/smoke_trip_workspace_foundation.py",
        "backend/scripts/smoke_offer_workspace_foundation.py",
        "backend/scripts/smoke_booking_workspace_foundation.py",
        "backend/scripts/smoke_document_foundation.py",
        "backend/scripts/smoke_airline_operational_intelligence_engine_foundation.py",
        "backend/scripts/smoke_canonical_journey_itinerary_representation_foundation.py",
        "backend/scripts/smoke_offer_delivery_client_interaction_foundation.py",
    }
    missing_focused = sorted(required_focused - focused_paths)
    if missing_focused:
        errors.append("Focused CI tier is missing critical coverage: " + ", ".join(missing_focused))

    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "backend/smoke_inventory.py"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if tracked.returncode != 0:
        errors.append("backend/smoke_inventory.py is not tracked by Git.")

    required_paths = (
        BACKEND / "smoke_inventory.py",
        BACKEND / "scripts" / "smoke_inventory.json",
        BACKEND / "scripts" / "run_smoke_inventory.py",
        BACKEND / "scripts" / "validate_smoke_inventory.py",
        BACKEND / "Dockerfile",
        ROOT / "frontend" / "package-lock.json",
    )
    for path in required_paths:
        if not path.is_file():
            errors.append(f"Referenced CI path does not exist: {path.relative_to(ROOT)}")

    server_text = (BACKEND / "server.py").read_text(encoding="utf-8")
    if '"github_actions_continuous_integration_foundation"' not in server_text:
        errors.append("Server readiness does not register the Phase 56.5.3 CI foundation.")
    return errors


def main() -> int:
    errors = validate_ci_foundation()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("Phase 56.5.3 GitHub Actions CI foundation validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
