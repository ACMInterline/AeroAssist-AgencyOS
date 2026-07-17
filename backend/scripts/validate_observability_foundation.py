#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE
from observability import COUNTER_LABELS, SAFE_METADATA_FIELDS, SENSITIVE_KEY_FRAGMENTS, TIMING_LABELS


RELEASE_PHASE = "phase_56_5_7_observability_diagnostics_performance_telemetry_foundation"
PRODUCTION_SOURCE_ROOTS = (
    BACKEND,
    BACKEND / "routers",
    BACKEND / "services",
)
SENSITIVE_LOG_TOKENS = (
    "authorization",
    "cookie",
    "mongodb_url",
    "mongo_password",
    "passport_number",
    "medical_profile",
    "payment_reference",
    "password_hash",
    "request.body",
    "response.body",
)


def production_python_files() -> list[Path]:
    files: set[Path] = set()
    for root in PRODUCTION_SOURCE_ROOTS:
        iterator = root.glob("*.py") if root == BACKEND else root.rglob("*.py")
        files.update(iterator)
    return sorted(path for path in files if "scripts" not in path.parts and "__pycache__" not in path.parts)


def call_name(node: ast.Call) -> str:
    function = node.func
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return ""


def validate_source_file(path: Path) -> list[str]:
    relative = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(relative))
    except SyntaxError as exc:
        return [f"{relative}: cannot parse source: {exc}"]
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node)
        if name == "print":
            errors.append(f"{relative}:{node.lineno}: production backend path uses raw print()")
        if name == "exception":
            errors.append(f"{relative}:{node.lineno}: broad logger.exception is not governed")
        if name in {"debug", "info", "warning", "error", "critical", "log"}:
            expression = ast.unparse(node).lower()
            leaked = sorted(token for token in SENSITIVE_LOG_TOKENS if token in expression)
            if leaked:
                errors.append(
                    f"{relative}:{node.lineno}: logging call references sensitive names {leaked}"
                )
        expression = ast.unparse(node).lower()
        if "request.body(" in expression or "response.body(" in expression:
            errors.append(f"{relative}:{node.lineno}: request or response body logging/access is not governed")
    return errors


def validate_observability_foundation() -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    if CURRENT_BUILD_PHASE != RELEASE_PHASE:
        errors.append(f"Current build phase is {CURRENT_BUILD_PHASE!r}, expected {RELEASE_PHASE!r}")

    files = production_python_files()
    for path in files:
        errors.extend(validate_source_file(path))

    observability_text = (BACKEND / "observability.py").read_text(encoding="utf-8")
    security_text = (BACKEND / "http_security.py").read_text(encoding="utf-8")
    persistence_text = (BACKEND / "persistence_query.py").read_text(encoding="utf-8")
    server_text = (BACKEND / "server.py").read_text(encoding="utf-8")
    router_text = (BACKEND / "routers" / "platform_observability.py").read_text(encoding="utf-8")
    config_text = (BACKEND / "config.py").read_text(encoding="utf-8")
    requirements_text = (BACKEND / "requirements.txt").read_text(encoding="utf-8").lower()
    dockerfile_text = (BACKEND / "Dockerfile").read_text(encoding="utf-8")

    required_observability_tokens = (
        "StructuredEventFormatter",
        "structured_event",
        "redact_sensitive",
        "sanitize_string",
        "operational_diagnostics_snapshot",
        "increment_counter",
        "record_timing",
        "external_telemetry_provider_required",
    )
    for token in required_observability_tokens:
        if token not in observability_text:
            errors.append(f"Central observability module is missing {token!r}")

    if security_text.count("class SecurityHttpMiddleware") != 1:
        errors.append("HTTP timing must use exactly one canonical security/telemetry middleware class.")
    if "http_request_completed" not in security_text or "request.body" in security_text or "response.body" in security_text:
        errors.append("HTTP completion telemetry or body-logging prohibition is incomplete.")
    if "database_query_completed" not in persistence_text or "current_correlation_id" not in persistence_text:
        errors.append("Phase 56.5.6 query diagnostics are not reused with request correlation.")

    public_start = server_text.find("async def public_readiness_payload")
    internal_start = server_text.find("async def bounded_internal_readiness_payload")
    public_source = server_text[public_start:internal_start]
    if "operational_diagnostics_snapshot" in public_source:
        errors.append("Public readiness exposes internal operational counters.")
    if '"observability_diagnostics_performance_telemetry_foundation"' not in public_source:
        errors.append("Public readiness is missing non-sensitive observability metadata.")
    if "operational_diagnostics_snapshot" in server_text[internal_start:]:
        errors.append("Readiness routes expose diagnostics reserved for the protected Platform endpoint.")
    if (
        "/api/platform/diagnostics/observability" not in router_text
        or "require_platform_role" not in router_text
        or "operational_diagnostics_snapshot" not in router_text
        or "raw_logs_exposed" not in router_text
    ):
        errors.append("Platform diagnostics route is missing protection or safe aggregate policy.")

    smoke_text = (
        BACKEND / "scripts" / "smoke_observability_diagnostics_performance_telemetry_foundation.py"
    ).read_text(encoding="utf-8")
    protected_readiness_keys = (
        "operational_diagnostics",
        "counters",
        "timings",
        "startup_timestamp",
        "uptime_seconds",
        "recent_error_counters",
        "slow_operation_counters",
    )
    if "def protected_readiness_keys" not in smoke_text or any(
        f'"{key}"' not in smoke_text for key in protected_readiness_keys
    ):
        errors.append("Public readiness smoke lacks recursive protected-diagnostics regression coverage.")

    required_config_tokens = (
        "LOG_FORMAT",
        "LOG_SERVICE_NAME",
        "LOG_SLOW_REQUEST_THRESHOLD_MS",
        "LOG_ERROR_STACKTRACES",
        "LOG_HASH_TENANT_IDENTIFIERS",
        "LOG_REQUEST_TELEMETRY_ENABLED",
        "LOG_REDACTION_ENABLED",
        "APP_GIT_COMMIT",
        "APP_DEPLOYMENT_ID",
    )
    for token in required_config_tokens:
        if token not in config_text:
            errors.append(f"Observability configuration is missing {token}")

    if len(COUNTER_LABELS) > 16 or any(len(labels) > 16 for labels in COUNTER_LABELS.values()):
        errors.append("Operational counter label cardinality is not statically bounded.")
    if len(TIMING_LABELS) > 16:
        errors.append("Operational timing label cardinality is not statically bounded.")
    if any(fragment in SAFE_METADATA_FIELDS for fragment in SENSITIVE_KEY_FRAGMENTS):
        errors.append("Structured metadata allowlist includes a sensitive field.")

    forbidden_dependencies = ("opentelemetry", "sentry", "datadog", "newrelic", "prometheus")
    if any(dependency in requirements_text for dependency in forbidden_dependencies):
        errors.append("An external telemetry dependency was introduced.")
    if "FileHandler" in observability_text or "RotatingFileHandler" in observability_text:
        errors.append("Application-managed container log files or rotation were introduced.")
    if "--no-access-log" not in dockerfile_text:
        errors.append("Uvicorn access logging is not disabled despite canonical HTTP telemetry.")

    summary = {
        "production_python_files_scanned": len(files),
        "bounded_counter_families": len(COUNTER_LABELS),
        "bounded_counter_labels": sum(len(labels) for labels in COUNTER_LABELS.values()),
        "bounded_timing_labels": len(TIMING_LABELS),
    }
    return errors, summary


def main() -> int:
    errors, summary = validate_observability_foundation()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("Observability foundation validation passed: " + json.dumps(summary, sort_keys=True))
    print("Static validation is a guardrail and does not prove complete privacy or runtime telemetry coverage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
