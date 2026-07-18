#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE
from models import PilotReleaseProductionEvidence
from services.final_stabilization_pilot_release_gate_service import (
    RELEASE_PHASE,
    FinalStabilizationPilotReleaseGateService,
)
from smoke_inventory import SMOKE_INVENTORY_SUMMARY


MAX_EVIDENCE_FILE_BYTES = 64 * 1024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a read-only, evidence-aware AeroAssist pilot release assessment."
    )
    parser.add_argument("--production-evidence", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--environment-scope",
        choices=("repository", "ci", "disposable", "production"),
        default="repository",
    )
    parser.add_argument("--format", choices=("human", "json"), default="human")
    return parser.parse_args()


def git_output(*arguments: str) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return 127, ""
    return result.returncode, result.stdout.strip()


def collect_repository_evidence() -> tuple[dict[str, bool | None], str | None]:
    status_code, status_output = git_output("status", "--porcelain")
    revision_code, revision = git_output("rev-parse", "--short=12", "HEAD")
    required_files = (
        ROOT / "backend" / "build_phase.py",
        ROOT / "backend" / "observability.py",
        ROOT / "backend" / "persistence_query.py",
        ROOT / "backend" / "scripts" / "validate_smoke_inventory.py",
        ROOT / "backend" / "scripts" / "validate_ci_foundation.py",
        ROOT / "backend" / "scripts" / "validate_persistence_query_foundation.py",
        ROOT / "backend" / "scripts" / "validate_observability_foundation.py",
        ROOT / "backend" / "scripts" / "validate_final_stabilization_pilot_release_gate.py",
        ROOT / "docs" / "architecture" / "final-stabilization-pilot-release-gate.md",
        ROOT / "deploy" / "hostinger" / "PILOT_RELEASE_RUNBOOK.md",
    )
    inventory_valid = (
        SMOKE_INVENTORY_SUMMARY.get("unresolved_scripts") == 0
        and SMOKE_INVENTORY_SUMMARY.get("inventory_validation_ready") is True
    )
    evidence = {
        "source_integrity": status_code == 0 and not status_output,
        "build_integrity": CURRENT_BUILD_PHASE == RELEASE_PHASE and inventory_valid,
        "authentication_security": (BACKEND / "http_security.py").is_file(),
        "http_security": (BACKEND / "http_security.py").is_file(),
        "persistence_scalability": (BACKEND / "persistence_repository.py").is_file(),
        "query_governance": (BACKEND / "persistence_query.py").is_file(),
        "observability": (BACKEND / "observability.py").is_file(),
        "documentation_completeness": all(path.is_file() for path in required_files),
    }
    return evidence, revision if revision_code == 0 else None


def load_production_evidence(path: Path | None) -> PilotReleaseProductionEvidence | None:
    if path is None:
        return None
    if not path.is_file() or path.stat().st_size > MAX_EVIDENCE_FILE_BYTES:
        raise ValueError("Production evidence must be a JSON file no larger than 64 KiB.")
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Production evidence must be readable JSON metadata.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Production evidence must be a JSON object.")
    return PilotReleaseProductionEvidence.model_validate(payload)


def human_summary(payload: dict[str, Any]) -> str:
    dimensions = payload.get("dimensions") or []
    counts = {
        status: sum(1 for item in dimensions if item.get("status") == status)
        for status in ("passed", "warning", "blocked", "not_verified")
    }
    lines = [
        "AeroAssist Pilot Release Assessment",
        f"Phase: {payload['build_phase']}",
        f"Status: {payload['assessment_status']}",
        f"Assessment: {payload['assessment_id']}",
        "Dimensions: " + " ".join(f"{key}={value}" for key, value in counts.items()),
        f"Production evidence supplied: {str(payload['production_evidence_supplied']).lower()}",
        f"Production deployment verified: {str(payload['production_deployment_verified']).lower()}",
        f"Pilot release ready: {str(payload['pilot_release_ready']).lower()}",
    ]
    if payload.get("blocking_items"):
        lines.append("Blockers: " + ", ".join(payload["blocking_items"]))
    if payload.get("warnings"):
        lines.append("Warnings: " + ", ".join(payload["warnings"]))
    lines.append("Next action: " + payload["recommended_next_action"])
    lines.append("Human sign-off remains mandatory; this command never deploys or migrates production.")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        production_evidence = load_production_evidence(args.production_evidence)
        machine_evidence, revision = collect_repository_evidence()
        assessment = FinalStabilizationPilotReleaseGateService().build_assessment(
            environment_scope=args.environment_scope,
            machine_evidence=machine_evidence,
            production_evidence=production_evidence,
            git_commit=revision,
        )
    except (ValueError, TypeError):
        print("ERROR: invalid release evidence metadata.", file=sys.stderr)
        return 2

    payload = assessment.model_dump(mode="json")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.format == "json":
        print(json.dumps(payload, sort_keys=True))
    else:
        print(human_summary(payload))
    return 1 if assessment.assessment_status == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
