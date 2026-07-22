#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build_phase import CURRENT_BUILD_PHASE, phase_is_at_least
from config import get_settings, validate_config
from services.pdf_rendering_service import pdf_capabilities
from services.secret_service import check_secret, mask_secret_ref
from services.final_stabilization_pilot_release_gate_service import release_gate_readiness_metadata


def status_line(level: str, message: str) -> str:
    return f"{level}: {message}"


def mongo_compose_block(compose_text: str) -> str:
    marker = "  mongo:\n"
    if marker not in compose_text:
        return ""
    remainder = compose_text.split(marker, 1)[1]
    next_service = remainder.find("\n  ", 1)
    return remainder if next_service < 0 else remainder[:next_service]


def main() -> int:
    settings = get_settings()
    config = validate_config(settings, include_storage=True)
    errors = config["failure_count"] if settings.is_production else 0

    lines: list[str] = [
        status_line("INFO", f"APP_ENV={settings.app_env}"),
        status_line("INFO", f"Build phase={CURRENT_BUILD_PHASE}"),
        status_line("INFO", "Secrets are checked by reference only; secret values are never printed."),
    ]

    for check in config["checks"]:
        level = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}[check["level"]]
        lines.append(status_line(level, check["message"]))

    caps = pdf_capabilities()
    if caps.get("available"):
        renderer = f"{caps.get('engine')} {caps.get('engine_version') or ''}".strip()
        lines.append(status_line("PASS", f"PDF renderer available: {renderer}."))
    else:
        lines.append(status_line("WARN", caps.get("diagnostic") or "PDF renderer is unavailable."))

    if settings.smtp_secret_refs:
        for secret_ref in settings.smtp_secret_refs:
            result = check_secret(secret_ref)
            if result.ok:
                lines.append(status_line("PASS", f"SMTP secret reference {mask_secret_ref(secret_ref)}: {result.diagnostic}"))
            else:
                level = "FAIL" if settings.is_production else "WARN"
                if settings.is_production:
                    errors += 1
                lines.append(status_line(level, f"SMTP secret reference {mask_secret_ref(secret_ref)}: {result.diagnostic}"))
    else:
        lines.append(status_line("WARN", "SMTP_SECRET_REFS is not set; stored agency SMTP references must be checked separately."))

    if settings.public_app_url:
        lines.append(status_line("PASS", "PUBLIC_APP_URL is configured."))
    else:
        lines.append(status_line("WARN", "PUBLIC_APP_URL is not configured; set it before public deployment."))

    if settings.frontend_url:
        lines.append(status_line("PASS", "FRONTEND_URL is configured."))
    else:
        lines.append(status_line("WARN", "FRONTEND_URL is not configured; CORS must still list the deployed frontend origin."))

    if settings.is_production and not settings.seed_endpoint_enabled and not settings.seed_on_startup:
        lines.append(status_line("PASS", "Production seed paths are disabled by default."))
    elif not settings.is_production:
        lines.append(status_line("WARN", "Demo seed paths may be enabled in non-production for local setup."))

    lines.append(status_line("INFO", "Frontend production builds should set VITE_API_BASE_URL or serve the API from the same origin."))

    backend_root = Path(__file__).resolve().parents[1]
    root = backend_root.parent
    compose_path = root / "docker-compose.production.yml"
    compose_text = compose_path.read_text(encoding="utf-8") if compose_path.is_file() else ""
    mongo_block = mongo_compose_block(compose_text)
    packaged_inventory_path = Path(__file__).with_name("mongodb_backup_tooling_inventory.json")
    packaged_inventory = (
        json.loads(packaged_inventory_path.read_text(encoding="utf-8"))
        if packaged_inventory_path.is_file()
        else {}
    )
    if mongo_block:
        if "\n    ports:" in "\n" + mongo_block:
            errors += 1
            lines.append(status_line("FAIL", "Production MongoDB must not publish a host port."))
        else:
            lines.append(status_line("PASS", "Production MongoDB is internal-network only with no host port binding."))
    elif packaged_inventory.get("mongodb_internal_network_only") is True:
        lines.append(status_line("PASS", "Packaged deployment inventory records internal-only production MongoDB networking."))
    else:
        errors += 1
        lines.append(status_line("FAIL", "Production MongoDB network isolation is not represented."))

    required_backup_scripts = (
        "backup_mongo.sh",
        "verify_mongodb_backup.sh",
        "restore_mongodb_backup.sh",
        "test_restore_mongodb_backup.sh",
        "prune_backups.sh",
    )
    scripts_root = root / "deploy" / "hostinger" / "scripts"
    if scripts_root.is_dir():
        if not settings.mongo_root_username or not settings.mongo_root_password:
            if settings.is_production:
                errors += 1
                lines.append(status_line("FAIL", "Host deployment checks require MongoDB administrative credentials for initialization and guarded recovery."))
            else:
                lines.append(status_line("WARN", "Host-only MongoDB administrative credentials are not required for non-production validation."))
        else:
            lines.append(status_line("PASS", "Host deployment has protected MongoDB administrative credentials available to operator tooling."))
    elif packaged_inventory.get("application_root_credentials_excluded") is True:
        lines.append(status_line("PASS", "MongoDB administrative credentials are intentionally excluded from the application container."))
    else:
        errors += 1
        lines.append(status_line("FAIL", "MongoDB administrative credential isolation is not represented."))

    if scripts_root.is_dir():
        missing_scripts = [name for name in required_backup_scripts if not (scripts_root / name).is_file()]
        structurally_unsafe = [
            name
            for name in required_backup_scripts
            if (scripts_root / name).is_file()
            and "set -euo pipefail" not in (scripts_root / name).read_text(encoding="utf-8")
        ]
        if missing_scripts or structurally_unsafe:
            errors += 1
            lines.append(status_line("FAIL", "MongoDB backup or restore tooling is missing required strict-mode safety."))
        else:
            lines.append(status_line("PASS", "MongoDB backup, verification, guarded restore, rehearsal, and retention tooling is present."))
    elif set(required_backup_scripts) == set(packaged_inventory.get("backup_tooling") or []) and packaged_inventory.get("strict_shell_mode_required") is True:
        lines.append(status_line("PASS", "Packaged deployment inventory represents the validated backup and restore tooling."))
    else:
        errors += 1
        lines.append(status_line("FAIL", "MongoDB backup and restore tooling inventory is incomplete."))

    rehearsal_path = scripts_root / "test_restore_mongodb_backup.sh"
    rehearsal_text = rehearsal_path.read_text(encoding="utf-8") if rehearsal_path.is_file() else ""
    rehearsal_nofile_governed = (
        'MINIMUM_RESTORE_MONGO_NOFILE=64000' in rehearsal_text
        and '--ulimit "nofile=${RESTORE_MONGO_NOFILE_SOFT}:${RESTORE_MONGO_NOFILE_HARD}"' in rehearsal_text
        and "ulimit -Sn" in rehearsal_text
        and "ulimit -Hn" in rehearsal_text
    )
    packaged_nofile_minimum = packaged_inventory.get("disposable_restore_nofile_minimum")
    if rehearsal_nofile_governed or (
        type(packaged_nofile_minimum) is int and packaged_nofile_minimum >= 64000
    ):
        lines.append(status_line("PASS", "Disposable MongoDB restore rehearsals enforce and verify safe file-descriptor limits."))
    else:
        errors += 1
        lines.append(status_line("FAIL", "Disposable MongoDB restore rehearsal file-descriptor limits are not governed."))

    restore_path = scripts_root / "restore_mongodb_backup.sh"
    restore_text = restore_path.read_text(encoding="utf-8") if restore_path.is_file() else ""
    required_restore_guards = (
        "ALLOW_PRODUCTION_RESTORE",
        "PRODUCTION_RESTORE_CONFIRMATION",
        "RESTORE_TARGET_ENV",
        "DRY_RUN",
    )
    packaged_restore_guards = (
        packaged_inventory.get("dry_run_restore_default") is True
        and packaged_inventory.get("production_confirmation_required") is True
        and packaged_inventory.get("automatic_production_restore_disabled") is True
    )
    if restore_text and not all(token in restore_text for token in required_restore_guards):
        errors += 1
        lines.append(status_line("FAIL", "Production restore tooling is missing explicit dry-run or confirmation guards."))
    elif restore_text or packaged_restore_guards:
        lines.append(status_line("PASS", "Production restore defaults to dry-run and requires multi-part confirmation."))
    else:
        errors += 1
        lines.append(status_line("FAIL", "Production restore safety guards are not represented."))

    if not phase_is_at_least(
        CURRENT_BUILD_PHASE,
        "phase_56_5_8_final_stabilization_pilot_release_gate",
    ):
        errors += 1
        lines.append(status_line("FAIL", "Build phase does not include the final stabilization and pilot release gate."))
    else:
        lines.append(status_line("PASS", "Final stabilization and pilot release-gate phase marker is current."))

    if settings.log_format == "json" or not settings.is_production:
        lines.append(status_line("PASS", "Structured logging format is environment-appropriate."))
    else:
        errors += 1
        lines.append(status_line("FAIL", "Production requires LOG_FORMAT=json."))

    if settings.log_request_telemetry_enabled and settings.log_redaction_enabled:
        lines.append(status_line("PASS", "Request telemetry and centralized sensitive-value redaction are enabled."))
    else:
        errors += 1
        lines.append(status_line("FAIL", "Request telemetry and redaction must be enabled for production diagnostics."))

    if settings.is_production and settings.log_error_stacktraces:
        errors += 1
        lines.append(status_line("FAIL", "Production stacktrace logging must remain disabled."))
    else:
        lines.append(status_line("PASS", "Stacktrace exposure follows the environment-safe policy."))

    if 'max-size: "10m"' in compose_text and 'max-file: "5"' in compose_text:
        lines.append(status_line("PASS", "Container logs have bounded Docker rotation settings."))
    elif compose_path.is_file():
        errors += 1
        lines.append(status_line("FAIL", "Production Compose is missing bounded container log rotation settings."))

    server_path = backend_root / "server.py"
    server_text = server_path.read_text(encoding="utf-8") if server_path.is_file() else ""
    router_path = backend_root / "routers" / "platform_observability.py"
    router_text = router_path.read_text(encoding="utf-8") if router_path.is_file() else ""
    if (
        '"observability_diagnostics_performance_telemetry_foundation"' in server_text
        and "from routers import platform_observability" in server_text
        and "app.include_router(platform_observability.router)" in server_text
        and "require_platform_role" in router_text
        and "/api/platform/diagnostics/observability" in router_text
    ):
        lines.append(status_line("PASS", "Internal observability diagnostics use an existing protected Platform route."))
    else:
        errors += 1
        lines.append(status_line("FAIL", "Protected observability diagnostics registration is incomplete."))

    frontend_binding = os.getenv("FRONTEND_HTTP_PORT", "")
    if settings.is_production and compose_path.is_file() and not frontend_binding.startswith("127.0.0.1:"):
        errors += 1
        lines.append(status_line("FAIL", "Production frontend must bind to loopback when host nginx terminates TLS."))
    elif frontend_binding.startswith("127.0.0.1:") or packaged_inventory.get("frontend_loopback_binding_required") is True:
        lines.append(status_line("PASS", "Production frontend loopback binding is represented."))
    else:
        lines.append(status_line("WARN", "Frontend loopback binding must be verified on the deployment host."))

    release_gate = release_gate_readiness_metadata()
    if (
        release_gate.get("repository_gate_available") is True
        and release_gate.get("production_evidence_supplied") is False
        and release_gate.get("production_deployment_verified") is False
        and release_gate.get("pilot_release_ready") is False
        and release_gate.get("human_sign_off_required") is True
    ):
        lines.append(status_line("PASS", "Pilot release gate defaults production evidence to unverified and requires human sign-off."))
    else:
        errors += 1
        lines.append(status_line("FAIL", "Pilot release gate does not fail closed without production evidence."))

    pilot_runbook = root / "deploy" / "hostinger" / "PILOT_RELEASE_RUNBOOK.md"
    if pilot_runbook.is_file() or packaged_inventory.get("pilot_release_runbook_packaged") is True:
        lines.append(status_line("PASS", "Pilot release and rollback procedure is represented."))
    else:
        errors += 1
        lines.append(status_line("FAIL", "Pilot release runbook is missing."))

    for line in lines:
        print(line)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
