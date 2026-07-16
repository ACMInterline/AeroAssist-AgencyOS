#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import InvalidPhaseIdentifier, parse_phase_identifier
from smoke_inventory import load_smoke_inventory, summarize_smoke_inventory


REQUIRED_FIELDS = {
    "script_path",
    "capability_name",
    "minimum_application_phase",
    "phase_assertion_mode",
    "requires_running_backend",
    "requires_mongodb",
    "mutates_disposable_test_data",
    "scope",
    "test_class",
    "suitable_for_future_ci",
    "ci_tier",
    "execution_isolation",
    "notes",
}
VALID_MODES = {"minimum", "exact_current", "none"}
VALID_TEST_CLASSES = {"focused", "integration", "broad"}
VALID_CI_TIERS = {"static", "focused", "integration", "full_only"}
VALID_EXECUTION_ISOLATION = {"none", "shared_backend", "fresh_backend"}
STALE_RUNTIME_PATTERNS = (
    re.compile(r"EXPECTED_PHASE\s*="),
    re.compile(r"(?:\.get\([\"']phase[\"']\)|PHASE_LABEL)\s*(?:==|!=)\s*[\"']phase_56_[34]_"),
    re.compile(r"(?:\.get\([\"']phase[\"']\)|PHASE_LABEL)\s*(?:==|!=)\s*MINIMUM_PHASE"),
)
EXACT_CURRENT_PATTERN = re.compile(
    r"phase_is_exact\(\s*(?:health|get\([^)]+\)|readiness|CURRENT_BUILD_PHASE).*CURRENT_BUILD_PHASE",
    re.DOTALL,
)


def validate_inventory() -> tuple[dict[str, int | bool], list[str]]:
    payload = load_smoke_inventory()
    entries = payload.get("scripts") or []
    allowlist = payload.get("exact_current_allowlist") or []
    errors: list[str] = []

    discovered = sorted(
        str(path.relative_to(ROOT))
        for path in (BACKEND / "scripts").glob("smoke_*.py")
        if path.is_file()
    )
    paths = [entry.get("script_path") for entry in entries if isinstance(entry, dict)]
    duplicates = sorted({path for path in paths if path and paths.count(path) > 1})
    if duplicates:
        errors.append(f"Duplicate inventory entries: {', '.join(duplicates)}")
    missing = sorted(set(discovered) - set(paths))
    extra = sorted(set(paths) - set(discovered))
    if missing:
        errors.append(f"Smoke scripts missing from inventory: {', '.join(missing)}")
    if extra:
        errors.append(f"Inventory paths that do not exist: {', '.join(extra)}")

    allowlist_by_path: dict[str, dict[str, Any]] = {}
    for item in allowlist:
        if not isinstance(item, dict) or not all(item.get(key) for key in ("script_path", "assertion_purpose", "exact_reason")):
            errors.append("Every exact-current allowlist entry requires script_path, assertion_purpose, and exact_reason.")
            continue
        path = str(item["script_path"])
        if path in allowlist_by_path:
            errors.append(f"Duplicate exact-current allowlist entry: {path}")
        allowlist_by_path[path] = item

    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("Every smoke inventory entry must be an object.")
            continue
        script_path = str(entry.get("script_path") or "<missing>")
        absent = sorted(REQUIRED_FIELDS - set(entry))
        if absent:
            errors.append(f"{script_path}: missing fields {', '.join(absent)}")
            continue
        mode = entry.get("phase_assertion_mode")
        if mode not in VALID_MODES:
            errors.append(f"{script_path}: unresolved or invalid phase_assertion_mode {mode!r}")
        if entry.get("test_class") not in VALID_TEST_CLASSES:
            errors.append(f"{script_path}: invalid test_class {entry.get('test_class')!r}")
        if entry.get("ci_tier") not in VALID_CI_TIERS:
            errors.append(f"{script_path}: invalid ci_tier {entry.get('ci_tier')!r}")
        if entry.get("execution_isolation") not in VALID_EXECUTION_ISOLATION:
            errors.append(f"{script_path}: invalid execution_isolation {entry.get('execution_isolation')!r}")
        if entry.get("execution_isolation") == "none" and entry.get("requires_running_backend"):
            errors.append(f"{script_path}: backend-dependent smoke cannot use none execution isolation")
        if entry.get("execution_isolation") != "none" and not entry.get("requires_running_backend"):
            errors.append(f"{script_path}: backend-free smoke must use none execution isolation")
        if not isinstance(entry.get("scope"), list) or not entry.get("scope"):
            errors.append(f"{script_path}: scope must be a non-empty array")
        for key in ("requires_running_backend", "requires_mongodb", "mutates_disposable_test_data", "suitable_for_future_ci"):
            if not isinstance(entry.get(key), bool):
                errors.append(f"{script_path}: {key} must be boolean")

        absolute = ROOT / script_path
        if not absolute.is_file():
            continue
        text = absolute.read_text(encoding="utf-8")
        minimum = entry.get("minimum_application_phase")
        if mode in {"minimum", "exact_current"}:
            if not isinstance(minimum, str):
                errors.append(f"{script_path}: {mode} mode requires minimum_application_phase")
            else:
                try:
                    parse_phase_identifier(minimum)
                except InvalidPhaseIdentifier as exc:
                    errors.append(f"{script_path}: invalid minimum phase {minimum!r}: {exc}")
        elif minimum is not None:
            errors.append(f"{script_path}: none mode must use null minimum_application_phase")

        if mode == "minimum":
            if "MINIMUM_PHASE" not in text or not re.search(
                r"(?:assert_application_phase_at_least|application_phase_is_at_least)", text
            ):
                errors.append(f"{script_path}: minimum mode does not use shared minimum-phase semantics")
            if EXACT_CURRENT_PATTERN.search(text):
                errors.append(f"{script_path}: minimum mode contains a current-build exact assertion")
        elif mode == "exact_current":
            if script_path not in allowlist_by_path:
                errors.append(f"{script_path}: exact-current mode is not allowlisted")
            if not EXACT_CURRENT_PATTERN.search(text):
                errors.append(f"{script_path}: exact-current mode lacks an exact current-build assertion")
        elif mode == "none" and re.search(r"(?:health|readiness).*\.get\([\"']phase[\"']\)", text):
            errors.append(f"{script_path}: none mode contains an application phase assertion")

        for pattern in STALE_RUNTIME_PATTERNS:
            if pattern.search(text):
                errors.append(f"{script_path}: contains a stale or disallowed exact runtime phase assertion")
                break

    entry_by_path = {entry.get("script_path"): entry for entry in entries if isinstance(entry, dict)}
    for script_path in allowlist_by_path:
        if entry_by_path.get(script_path, {}).get("phase_assertion_mode") != "exact_current":
            errors.append(f"{script_path}: allowlisted exact assertion is not exact_current in inventory")

    summary = summarize_smoke_inventory(payload)
    if len(discovered) != summary["inventoried_smoke_scripts"]:
        errors.append(
            f"Inventory count mismatch: discovered {len(discovered)}, inventoried {summary['inventoried_smoke_scripts']}"
        )
    if summary["unresolved_scripts"] != 0:
        errors.append(f"Inventory contains {summary['unresolved_scripts']} unresolved scripts")
    return summary, errors


def main() -> int:
    summary, errors = validate_inventory()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(
        "Smoke inventory validation passed: "
        f"{summary['inventoried_smoke_scripts']} scripts, "
        f"{summary['minimum_phase_scripts']} minimum, "
        f"{summary['intentional_exact_current_scripts']} exact-current, "
        f"{summary['no_phase_scripts']} no-phase, 0 unresolved."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
