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
        "fetch-depth: 0",
        "python3 -m compileall -q backend",
        "validate_smoke_inventory.py",
        "validate_ci_foundation.py",
        "validate_persistence_query_foundation.py",
        "validate_observability_foundation.py",
        "validate_final_stabilization_pilot_release_gate.py",
        "smoke_persistence_scalability_tenant_query_hardening_foundation.py --static",
        "smoke_observability_diagnostics_performance_telemetry_foundation.py --static",
        "smoke_final_stabilization_pilot_release_gate.py --static",
        "smoke_pilot_operations_release_readiness.py --static",
        "assess_pilot_release_readiness.py",
        "smoke_mongodb_security_backup_disaster_recovery_foundation.py --static",
        "bash -n deploy/hostinger",
        "npm run build --prefix frontend",
        "import smoke_inventory, server",
    ),
    ".github/workflows/ci-docker.yml": (
        "pull_request:",
        "push:",
        "workflow_dispatch:",
        "application_commit:",
        "required: true",
        "github.workflow_sha",
        "fetch-depth: 0",
        "--file backend/Dockerfile",
        "--file frontend/Dockerfile",
        "org.opencontainers.image.revision=$APPLICATION_COMMIT",
        "CURRENT_BUILD_PHASE",
        "SMOKE_INVENTORY_SUMMARY",
        "/app/smoke_inventory.py",
        "/app/scripts/smoke_inventory.json",
        "import smoke_inventory, server",
        "/api/health",
        "/api/readiness",
        "/api/platform/diagnostics/observability",
        "final_stabilization_pilot_release_gate",
        "smoke_final_stabilization_pilot_release_gate.py --static",
        "smoke_pilot_operations_release_readiness.py --static",
        "assess_pilot_release_readiness.py",
        "run_pilot_release_validation.py",
        "--profile full",
        "--include-docker-config",
        "release-candidate-lineage.json",
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
        "application_commit:",
        "required: true",
        "schedule:",
        "mongo:7",
        "github.workflow_sha",
        "fetch-depth: 0",
        "npm audit --prefix frontend",
        "run_pilot_release_validation.py",
        "--profile full",
        "--include-docker-config",
        "pilot-release-validation.json",
        "full-regression-lineage.json",
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
    "avio.my": "CI foundation must not connect to the production domain.",
    "appleboy/": "CI foundation must not use SSH deployment actions.",
    "docker/login-action": "CI foundation must not authenticate to a registry.",
    "docker/build-push-action": "CI foundation must not publish images.",
    "contents: write": "Workflow permissions must remain read-only.",
    "packages: write": "Workflow permissions must not publish packages.",
    "deployments: write": "Workflow permissions must not deploy.",
    "pull-requests: write": "Workflow permissions must not mutate pull requests.",
}
APPROVED_APPLICATION_COMMIT = "de22b70c1ccdabf7bd6d28765addf63f79dd189d"
FULL_SHA_SHELL_PATTERN = r"^[0-9a-f]{40}$"
DOCUMENT_EXPORT_JOBS = {
    ".github/workflows/ci-fast.yml": ("validate",),
    ".github/workflows/ci-smoke-focused.yml": ("focused-smokes",),
    ".github/workflows/ci-regression-full.yml": ("complete-inventory",),
    ".github/workflows/ci-docker.yml": ("exact-release-validation",),
}
EXPRESSION_CONTEXT_RE = re.compile(r"\$\{\{\s*([A-Za-z_][A-Za-z0-9_-]*)")


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


def artifact_upload_blocks(text: str) -> list[str]:
    lines = text.splitlines()
    blocks: list[str] = []
    for index, line in enumerate(lines):
        if "uses: actions/upload-artifact@v4" not in line:
            continue
        block = [line]
        for following in lines[index + 1 :]:
            if following.startswith("      - name:"):
                break
            block.append(following)
        blocks.append("\n".join(block))
    return blocks


def workflow_job_block(text: str, job_name: str) -> str:
    marker = f"  {job_name}:\n"
    start = text.find(marker)
    if start < 0:
        return ""
    following = text[start + len(marker) :]
    next_job = re.search(r"(?m)^  [a-z0-9][a-z0-9-]*:\n", following)
    end = start + len(marker) + next_job.start() if next_job else len(text)
    return text[start:end]


def workflow_job_blocks(text: str) -> dict[str, str]:
    jobs_marker = "\njobs:\n"
    jobs_start = text.find(jobs_marker)
    if jobs_start < 0:
        return {}
    jobs_text = text[jobs_start + len(jobs_marker) :]
    matches = list(re.finditer(r"(?m)^  ([a-z0-9][a-z0-9-]*):\n", jobs_text))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(jobs_text)
        blocks[match.group(1)] = jobs_text[match.start() : end]
    return blocks


def indented_mapping_block(text: str, key: str, indent: int) -> str:
    lines = text.splitlines()
    marker = f"{' ' * indent}{key}:"
    for index, line in enumerate(lines):
        if line != marker:
            continue
        block = [line]
        for following in lines[index + 1 :]:
            if following.strip() and len(following) - len(following.lstrip(" ")) <= indent:
                break
            block.append(following)
        return "\n".join(block)
    return ""


def job_step_blocks(job_block: str) -> list[str]:
    steps_marker = "\n    steps:\n"
    start = job_block.find(steps_marker)
    if start < 0:
        return []
    steps_text = job_block[start + len(steps_marker) :]
    matches = list(re.finditer(r"(?m)^      - (?:name|uses|run):", steps_text))
    blocks: list[str] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(steps_text)
        blocks.append(steps_text[match.start() : end])
    return blocks


def expression_contexts(text: str) -> set[str]:
    return {match.group(1) for match in EXPRESSION_CONTEXT_RE.finditer(text)}


def audit_workflow_context_structure(relative: str, text: str) -> list[str]:
    errors: list[str] = []
    jobs = workflow_job_blocks(text)
    jobs_marker = "\njobs:\n"
    workflow_scope = text[: text.find(jobs_marker)] if jobs_marker in text else text
    workflow_contexts = expression_contexts(workflow_scope)
    invalid_workflow_contexts = workflow_contexts.intersection(
        {"runner", "job", "steps", "needs", "strategy", "matrix", "env", "hashFiles"}
    )
    for context in sorted(invalid_workflow_contexts):
        errors.append(f"{relative}: context {context!r} is not valid at workflow scope.")

    trigger_block = indented_mapping_block(text, "on", 0)
    has_non_dispatch_trigger = any(
        re.search(rf"(?m)^  {trigger}:", trigger_block)
        for trigger in ("pull_request", "push", "schedule")
    )
    if has_non_dispatch_trigger:
        for line in workflow_scope.splitlines():
            if "${{ inputs." in line and "||" not in line:
                errors.append(
                    f"{relative}: workflow-scope inputs context lacks a non-dispatch fallback: {line.strip()!r}."
                )

    for job_name, block in jobs.items():
        env_block = indented_mapping_block(block, "env", 4)
        env_contexts = expression_contexts(env_block)
        for context in sorted(env_contexts.intersection({"runner", "job", "steps", "env", "hashFiles"})):
            errors.append(
                f"{relative} job {job_name!r}: context {context!r} is not valid in jobs.<job_id>.env."
            )

        steps_marker = "\n    steps:\n"
        pre_steps = block[: block.find(steps_marker)] if steps_marker in block else block
        if "steps" in expression_contexts(pre_steps):
            errors.append(f"{relative} job {job_name!r}: steps context is used before job steps exist.")
        if "hashFiles" in expression_contexts(pre_steps):
            errors.append(f"{relative} job {job_name!r}: hashFiles is used outside a step expression.")

        if has_non_dispatch_trigger:
            dispatch_only = "if: github.event_name == 'workflow_dispatch'" in pre_steps
            for line in block.splitlines():
                if "${{ inputs." in line and "||" not in line and not dispatch_only:
                    errors.append(
                        f"{relative} job {job_name!r}: inputs context lacks a non-dispatch fallback: "
                        f"{line.strip()!r}."
                    )

    for job_name in DOCUMENT_EXPORT_JOBS.get(relative, ()):
        block = jobs.get(job_name)
        if not block:
            errors.append(f"{relative}: required document-export job {job_name!r} is missing.")
            continue
        env_block = indented_mapping_block(block, "env", 4)
        if "DOCUMENT_EXPORT_STORAGE_DIR" in env_block:
            errors.append(
                f"{relative} job {job_name!r}: DOCUMENT_EXPORT_STORAGE_DIR must not be initialized "
                "in job-level env."
            )
        steps = job_step_blocks(block)
        initializer_indexes = [
            index for index, step in enumerate(steps) if "- name: Initialize runner paths" in step
        ]
        if len(initializer_indexes) != 1:
            errors.append(
                f"{relative} job {job_name!r}: expected exactly one Initialize runner paths step."
            )
            continue
        initializer_index = initializer_indexes[0]
        initializer = steps[initializer_index]
        required_tokens = (
            'document_export_dir="$RUNNER_TEMP/document-exports"',
            'mkdir -p "$document_export_dir"',
            'echo "DOCUMENT_EXPORT_STORAGE_DIR=$document_export_dir" >> "$GITHUB_ENV"',
        )
        for token in required_tokens:
            if token not in initializer:
                errors.append(
                    f"{relative} job {job_name!r}: runner-path initializer omits {token!r}."
                )
        if "$GITHUB_WORKSPACE" in initializer or "./document-exports" in initializer:
            errors.append(
                f"{relative} job {job_name!r}: document exports must be initialized outside the repository."
            )
        consumer_indexes = [
            index for index, step in enumerate(steps) if "DOCUMENT_EXPORT_STORAGE_DIR" in step
        ]
        if not consumer_indexes or min(consumer_indexes) != initializer_index:
            errors.append(
                f"{relative} job {job_name!r}: DOCUMENT_EXPORT_STORAGE_DIR is used before initialization."
            )
    return errors


def validate_exact_commit_release_contract() -> list[str]:
    docker_path = ROOT / ".github/workflows/ci-docker.yml"
    regression_path = ROOT / ".github/workflows/ci-regression-full.yml"
    if not docker_path.is_file() or not regression_path.is_file():
        return []

    docker_text = docker_path.read_text(encoding="utf-8")
    regression_text = regression_path.read_text(encoding="utf-8")
    exact_source_job = workflow_job_block(docker_text, "exact-release-validation")
    docker_job = workflow_job_block(docker_text, "backend-image")
    summary_job = workflow_job_block(docker_text, "release-candidate-summary")
    regression_job = workflow_job_block(regression_text, "complete-inventory")
    errors: list[str] = []

    dispatch_contract = (
        "workflow_dispatch:\n"
        "    inputs:\n"
        "      application_commit:\n"
        "        description: Exact 40-character application commit to validate\n"
        "        required: true\n"
        "        type: string"
    )
    for relative, text in (
        (docker_path.relative_to(ROOT), docker_text),
        (regression_path.relative_to(ROOT), regression_text),
    ):
        if dispatch_contract not in text:
            errors.append(f"{relative}: exact-commit dispatch input is not required and typed.")
        if FULL_SHA_SHELL_PATTERN not in text:
            errors.append(f"{relative}: application commit is not validated as a full lowercase SHA.")
        if 'test "$checked_out_head" = "$APPLICATION_COMMIT"' not in text:
            errors.append(f"{relative}: checked-out HEAD is not compared with the requested application commit.")
        if "git cat-file -e \"${APPLICATION_COMMIT}^{commit}\"" not in text:
            errors.append(f"{relative}: requested application commit existence is not verified.")
        if "application_commit" not in text or "workflow_definition_commit" not in text:
            errors.append(f"{relative}: application and workflow-definition commit lineage are not distinct.")
        if "github_run_id" not in text or "checked_out_application_tree" not in text:
            errors.append(f"{relative}: hosted run and checked-out tree lineage are incomplete.")
        if APPROVED_APPLICATION_COMMIT in text:
            errors.append(f"{relative}: exact validation is pinned to one historical application commit.")

    exact_job_contracts = (
        ("ci-docker.yml exact-release-validation", exact_source_job),
        ("ci-docker.yml backend-image", docker_job),
        ("ci-regression-full.yml complete-inventory", regression_job),
    )
    for label, block in exact_job_contracts:
        if not block:
            errors.append(f"{label}: exact-tree job is missing.")
            continue
        if 'test "$checked_out_head" = "$APPLICATION_COMMIT"' not in block:
            errors.append(f"{label}: checked-out HEAD equality guard is missing.")
        if "git cat-file -e \"${APPLICATION_COMMIT}^{commit}\"" not in block:
            errors.append(f"{label}: requested commit existence guard is missing.")
        for field in (
            "application_commit",
            "workflow_definition_commit",
            "github_run_id",
            "checked_out_application_tree",
            "validation_result",
        ):
            if field not in block:
                errors.append(f"{label}: lineage field {field!r} is missing.")
    if not summary_job:
        errors.append("ci-docker.yml release-candidate-summary: composite evidence job is missing.")
    else:
        for field in (
            "application_commit",
            "workflow_definition_commit",
            "github_run_id",
            "checked_out_application_tree",
            "validation_result",
        ):
            if field not in summary_job:
                errors.append(f"ci-docker.yml release-candidate-summary: lineage field {field!r} is missing.")

    required_docker_commands = (
        'docker build --label "org.opencontainers.image.revision=$APPLICATION_COMMIT" --file backend/Dockerfile --tag "$BACKEND_IMAGE" .',
        'docker build --label "org.opencontainers.image.revision=$APPLICATION_COMMIT" --file frontend/Dockerfile --tag "$FRONTEND_IMAGE" frontend',
    )
    for command in required_docker_commands:
        if command not in docker_text:
            errors.append(f"ci-docker.yml: missing exact production image build command {command!r}.")
    if re.search(r"--file\s+backend/Dockerfile\s+--tag\s+[^\n]+\s+backend(?:\s|$)", docker_text):
        errors.append("ci-docker.yml: backend image uses backend/ instead of repository root as build context.")

    hardcoded_phases = sorted(set(re.findall(r"phase_\d+_[a-z0-9_]+", docker_text)))
    if hardcoded_phases:
        errors.append(
            "ci-docker.yml: runtime phase must come from packaged build metadata, not "
            + ", ".join(hardcoded_phases)
        )
    numeric_inventory_assertions = re.findall(
        r"inventoried_smoke_scripts[\"'\]]*\s*==\s*\d+",
        docker_text,
    )
    if numeric_inventory_assertions or re.search(r"\b(?:141|171)\b", docker_text):
        errors.append("ci-docker.yml: smoke inventory total is hardcoded instead of package-derived.")
    if "from build_phase import CURRENT_BUILD_PHASE" not in docker_text:
        errors.append("ci-docker.yml: packaged runtime phase is not derived from CURRENT_BUILD_PHASE.")
    if "SMOKE_INVENTORY_SUMMARY['inventoried_smoke_scripts']" not in docker_text:
        errors.append("ci-docker.yml: packaged smoke inventory total is not derived canonically.")
    if 'section["inventoried_smoke_scripts"] == expected_inventory' not in docker_text:
        errors.append("ci-docker.yml: readiness inventory is not compared with packaged inventory.")
    if 'health["phase"] == expected_phase' not in docker_text or 'readiness["phase"] == expected_phase' not in docker_text:
        errors.append("ci-docker.yml: health/readiness phase is not compared with packaged phase.")

    required_release_behaviors = (
        "validate_canonical_domain_ownership.py",
        "validate_canonical_identity_tenancy.py",
        "validate_canonical_lifecycle_integrity.py",
        "validate_product_experience_recovery.py",
        "validate_stabilization_accessibility.py",
        "validate_full_system_stabilization.py",
        "validate_observability_foundation.py",
        "validate_final_stabilization_pilot_release_gate.py",
        "run_pilot_release_validation.py --profile full --include-docker-config",
        "npm audit --prefix frontend",
        "final_stabilization_pilot_release_gate",
        'release_gate["assessment_status"] == "blocked"',
        'release_gate["production_evidence_supplied"] is False',
        'release_gate["production_deployment_verified"] is False',
        'release_gate["pilot_release_ready"] is False',
        "automatic_release_approval_disabled",
        "automatic_production_migration_disabled",
        "test_restore_mongodb_backup.sh",
        "verify_mongodb_backup.sh",
        "Anonymous production-shaped diagnostics access was accepted.",
        "docker network create aeroassist-ci-runtime",
        "--network-alias backend",
        "docker network rm aeroassist-ci-runtime",
        "docker builder prune --force",
        "down --volumes --remove-orphans --rmi local",
    )
    for behavior in required_release_behaviors:
        if behavior not in docker_text:
            errors.append(f"ci-docker.yml: exact release gate omits {behavior!r}.")

    if 'ref: ${{ inputs.application_commit }}' not in docker_text:
        errors.append("ci-docker.yml: manual full gate does not check out the requested application commit.")
    if 'ref: ${{ inputs.application_commit || github.sha }}' not in docker_text:
        errors.append("ci-docker.yml: Docker job does not bind checkout to dispatch input or event SHA.")
    if 'ref: ${{ github.workflow_sha }}' not in docker_text:
        errors.append("ci-docker.yml: reviewed workflow definition is not validated on its own commit.")
    expected_commit_delta_checks = (
        'git diff --check "${WORKFLOW_DEFINITION_COMMIT}^" "$WORKFLOW_DEFINITION_COMMIT"',
        'git diff --check "${APPLICATION_COMMIT}^" "$APPLICATION_COMMIT"',
    )
    for check in expected_commit_delta_checks:
        if check not in docker_text:
            errors.append(f"ci-docker.yml: exact-commit whitespace validation omits {check!r}.")
    if 'git diff --check "$(git hash-object -t tree /dev/null)" HEAD' in docker_text:
        errors.append(
            "ci-docker.yml: exact validation scans the entire historical tree instead of the requested commit delta."
        )
    fast_text = (ROOT / ".github/workflows/ci-fast.yml").read_text(encoding="utf-8")
    if 'git diff --check "$(git hash-object -t tree /dev/null)" HEAD' in fast_text:
        errors.append("ci-fast.yml: whitespace validation scans the entire historical tree.")
    for check in (
        'git diff --check "$EVENT_BEFORE" "$GITHUB_SHA"',
        'git diff --check "${GITHUB_SHA}^" "$GITHUB_SHA"',
    ):
        if check not in fast_text:
            errors.append(f"ci-fast.yml: commit-range whitespace validation omits {check!r}.")
    if 'ref: ${{ inputs.application_commit || github.sha }}' not in regression_text:
        errors.append("ci-regression-full.yml: full regression does not bind checkout to exact input or schedule SHA.")
    if "--include-docker-config" not in regression_text:
        errors.append("ci-regression-full.yml: full regression omits production Compose rendering.")

    unsafe_artifact_markers = (".log", ".env", "GITHUB_ENV", "MONGO_APP_PASSWORD", "AUTH_TOKEN_SECRET")
    for relative, text in (
        (docker_path.relative_to(ROOT), docker_text),
        (regression_path.relative_to(ROOT), regression_text),
    ):
        for block in artifact_upload_blocks(text):
            unsafe = [marker for marker in unsafe_artifact_markers if marker in block]
            if unsafe:
                errors.append(f"{relative}: artifact upload includes unsafe material: {', '.join(unsafe)}")

    command_forbidden = (
        (r"\bgit\s+push\b", "push commits"),
        (r"\bdocker\s+push\b", "publish images"),
        (r"\bkubectl\b", "operate a cluster"),
        (r"\bssh\b", "access an external host"),
        (r"\bdeploy_v1_release_candidate\.sh\b", "invoke production deployment"),
        (r"(?m)^\s*(?:python3?|bash|sh)\s+[^\n]*(?:migrate|migration)", "execute a migration"),
    )
    for pattern, action in command_forbidden:
        if re.search(pattern, docker_text, flags=re.IGNORECASE):
            errors.append(f"ci-docker.yml: hosted validation must not {action}.")
    return errors


def validate_ci_foundation() -> list[str]:
    errors: list[str] = []
    if not phase_is_at_least(CURRENT_BUILD_PHASE, MINIMUM_PHASE):
        errors.append(f"Current build phase is {CURRENT_BUILD_PHASE!r}, expected at least {MINIMUM_PHASE!r}")

    for relative, tokens in WORKFLOW_SPECS.items():
        path = ROOT / relative
        errors.extend(validate_workflow(path, tokens))
        if path.is_file():
            errors.extend(audit_workflow_context_structure(relative, path.read_text(encoding="utf-8")))
    errors.extend(validate_exact_commit_release_contract())

    summary, inventory_errors = validate_inventory()
    errors.extend(inventory_errors)
    inventory = load_smoke_inventory()
    entries = inventory.get("scripts") or []
    entry_by_path = {entry.get("script_path"): entry for entry in entries}
    allowlist = inventory.get("exact_current_allowlist") or []
    exact_path = "backend/scripts/smoke_product_experience_recovery.py"
    pilot_operations_path = "backend/scripts/smoke_pilot_operations_release_readiness.py"
    release_gate_path = "backend/scripts/smoke_final_stabilization_pilot_release_gate.py"
    observability_path = "backend/scripts/smoke_observability_diagnostics_performance_telemetry_foundation.py"
    persistence_path = "backend/scripts/smoke_persistence_scalability_tenant_query_hardening_foundation.py"
    mongodb_path = "backend/scripts/smoke_mongodb_security_backup_disaster_recovery_foundation.py"
    security_path = "backend/scripts/smoke_authentication_security_http_hardening_foundation.py"
    ci_path = "backend/scripts/smoke_github_actions_continuous_integration_foundation.py"
    legacy_path = "backend/scripts/smoke_legacy_regression_suite_migration.py"
    if len(allowlist) != 1 or allowlist[0].get("script_path") != exact_path:
        errors.append("The active phase-registration smoke must be the sole exact-current allowlist entry.")
    if entry_by_path.get(exact_path, {}).get("phase_assertion_mode") != "exact_current":
        errors.append("The active phase-registration smoke is not classified as exact_current.")
    if entry_by_path.get(pilot_operations_path, {}).get("phase_assertion_mode") != "minimum":
        errors.append("Phase 57.0 smoke did not migrate to minimum-phase semantics.")
    if entry_by_path.get(security_path, {}).get("phase_assertion_mode") != "minimum":
        errors.append("Phase 56.5.4 smoke did not migrate to minimum-phase semantics.")
    if entry_by_path.get(mongodb_path, {}).get("phase_assertion_mode") != "minimum":
        errors.append("Phase 56.5.5 smoke did not migrate to minimum-phase semantics.")
    if entry_by_path.get(persistence_path, {}).get("phase_assertion_mode") != "minimum":
        errors.append("Phase 56.5.6 smoke did not migrate to minimum-phase semantics.")
    if entry_by_path.get(observability_path, {}).get("phase_assertion_mode") != "minimum":
        errors.append("Phase 56.5.7 smoke did not migrate to minimum-phase semantics.")
    if entry_by_path.get(release_gate_path, {}).get("phase_assertion_mode") != "minimum":
        errors.append("Phase 56.5.8 smoke did not migrate to minimum-phase semantics.")
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
        release_gate_path,
        observability_path,
        persistence_path,
        mongodb_path,
        security_path,
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
    if '"mongodb_security_backup_disaster_recovery_foundation"' not in server_text:
        errors.append("Server readiness does not register the Phase 56.5.5 MongoDB security foundation.")
    if '"persistence_scalability_tenant_query_hardening_foundation"' not in server_text:
        errors.append("Server readiness does not register the Phase 56.5.6 persistence foundation.")
    if '"observability_diagnostics_performance_telemetry_foundation"' not in server_text:
        errors.append("Server readiness does not register the Phase 56.5.7 observability foundation.")
    if '"final_stabilization_pilot_release_gate"' not in server_text:
        errors.append("Server readiness does not register the Phase 56.5.8 final release gate.")
    if '"pilot_operations_release_readiness"' not in server_text:
        errors.append("Server readiness does not register the Phase 57.0 pilot operations foundation.")
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
