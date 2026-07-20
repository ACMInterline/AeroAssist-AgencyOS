#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import urllib.error
import urllib.request
from dataclasses import replace
from pathlib import Path
from typing import Any


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE
from config import get_settings, validate_config
from http_security import SecurityHttpMiddleware, unexpected_exception_handler
from observability import (
    COUNTER_LABELS,
    REDACTED,
    StructuredEventFormatter,
    operational_diagnostics_snapshot,
    redact_sensitive,
    reset_operational_diagnostics,
    structured_event,
)
from persistence_query import query_diagnostic_records, record_query_diagnostic
from phase_assertions import assert_application_phase_at_least
from starlette.requests import Request
from starlette.responses import JSONResponse


RELEASE_PHASE = "phase_56_5_7_observability_diagnostics_performance_telemetry_foundation"
MINIMUM_PHASE = RELEASE_PHASE
BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
PROTECTED_PUBLIC_READINESS_KEYS = {
    "operational_diagnostics",
    "counters",
    "timings",
    "startup_timestamp",
    "uptime_seconds",
    "recent_error_counters",
    "slow_operation_counters",
}


def protected_readiness_keys(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if key in PROTECTED_PUBLIC_READINESS_KEYS:
                found.add(key)
            found.update(protected_readiness_keys(nested_value))
    elif isinstance(value, list):
        for item in value:
            found.update(protected_readiness_keys(item))
    return found


class CapturingHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.events: list[dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        event = getattr(record, "aeroassist_event", None)
        if isinstance(event, dict):
            self.events.append(event)


def request(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any] | str, dict[str, str]]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        method=method,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        response = urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        raw = response.read().decode("utf-8")
        response_headers = {key.lower(): value for key, value in response.headers.items()}
        try:
            payload: dict[str, Any] | str = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = raw
        return response.status, payload, response_headers


def verify_event_and_formatting() -> None:
    event = structured_event(
        "http_request_completed",
        level="INFO",
        operation="/api/agencies/agency-secret/passengers/passenger-secret?token=unsafe",
        duration_ms=12.34567,
        outcome="success",
        metadata={
            "method": "GET",
            "status_code": 200,
            "password": "not-loggable",
            "route": "/api/agencies/{agency_id}/passengers",
        },
        request_id="observability-smoke-request",
        correlation_id="observability-smoke-correlation",
        tenant_scope="agency",
        agency_id="agency-secret",
    )
    required = {
        "timestamp",
        "level",
        "event_type",
        "service",
        "environment",
        "build_phase",
        "request_id",
        "correlation_id",
        "tenant_scope",
        "operation",
        "duration_ms",
        "outcome",
        "metadata",
    }
    if required - set(event):
        raise AssertionError(f"Structured event envelope is incomplete: {required - set(event)}")
    serialized = json.dumps(event, sort_keys=True)
    if "not-loggable" in serialized or "agency-secret" in serialized or "token=unsafe" in serialized:
        raise AssertionError(f"Structured event leaked a sensitive value: {serialized}")

    record = logging.LogRecord("smoke", logging.INFO, __file__, 1, "ignored", (), None)
    record.aeroassist_event = event
    json_output = StructuredEventFormatter(json_format=True, production=True).format(record)
    if json.loads(json_output).get("event_type") != "http_request_completed":
        raise AssertionError("Production JSON formatter did not preserve the canonical event.")
    human_output = StructuredEventFormatter(json_format=False, production=False).format(record)
    if "http_request_completed" not in human_output or "observability-smoke-request" not in human_output:
        raise AssertionError("Development human formatter omitted correlation context.")


def verify_redaction() -> None:
    source = {
        "password": "PlaintextPassword!",
        "authorization": "Bearer private-token",
        "mongodb_uri": "mongodb://user:pass@mongo:27017/private",
        "email": "person@example.test",
        "phone": "+359 88 123 4567",
        "passport_number": "AB1234567",
        "medical_profile": "private condition",
        "nested": {"payment_reference": "pay-123", "safe": "retained"},
    }
    redacted = redact_sensitive(source)
    serialized = json.dumps(redacted, sort_keys=True)
    for secret in (
        "PlaintextPassword!",
        "private-token",
        "user:pass",
        "person@example.test",
        "+359 88 123 4567",
        "AB1234567",
        "private condition",
        "pay-123",
    ):
        if secret in serialized:
            raise AssertionError(f"Redaction leaked {secret!r}: {serialized}")
    if any(redacted[key] != REDACTED for key in ("password", "authorization", "mongodb_uri", "email", "phone", "passport_number", "medical_profile")):
        raise AssertionError(f"Sensitive key redaction was incomplete: {redacted}")


async def verify_http_telemetry_and_counters() -> None:
    reset_operational_diagnostics()
    settings = replace(get_settings(), log_slow_request_threshold_ms=1)
    middleware = SecurityHttpMiddleware(lambda scope, receive, send: None, settings=settings)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/agencies/agency-private/passengers/passenger-private",
        "raw_path": b"/api/agencies/agency-private/passengers/passenger-private",
        "query_string": b"token=must-not-log",
        "headers": [
            (b"x-request-id", b"observability-request-0001"),
            (b"x-correlation-id", b"observability-correlation-0001"),
            (b"authorization", b"Bearer must-not-log"),
        ],
        "client": ("127.0.0.1", 50000),
        "server": ("127.0.0.1", 8000),
    }
    request_object = Request(scope)

    async def call_next(_request: Request) -> JSONResponse:
        await asyncio.sleep(0.003)
        record_query_diagnostic(
            collection_category="agency_owned",
            operation="find_many",
            duration_ms=300,
            returned_count=1,
            requested_limit=10,
            tenant_scoped=True,
            query_class="passenger_workspaces:updated_at:-1",
        )
        return JSONResponse({"ok": True})

    root = logging.getLogger()
    prior_level = root.level
    handler = CapturingHandler()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)
    try:
        response = await middleware.dispatch(request_object, call_next)
    finally:
        root.removeHandler(handler)
        root.setLevel(prior_level)

    if response.headers.get("X-Request-ID") != "observability-request-0001":
        raise AssertionError("Request ID was not propagated.")
    if response.headers.get("X-Correlation-ID") != "observability-correlation-0001":
        raise AssertionError("Correlation ID was not propagated independently.")
    http_events = [event for event in handler.events if event.get("event_type") == "http_request_completed"]
    query_events = [event for event in handler.events if event.get("event_type") == "database_query_completed"]
    if len(http_events) != 1 or http_events[0].get("duration_ms", 0) < 1:
        raise AssertionError(f"Canonical HTTP completion telemetry was not emitted once: {http_events}")
    if (http_events[0].get("metadata") or {}).get("slow_operation") is not True:
        raise AssertionError("Slow-request detection did not mark the delayed request.")
    if not query_events or query_events[-1].get("correlation_id") != "observability-correlation-0001":
        raise AssertionError("Phase 56.5.6 query telemetry did not reuse request correlation.")
    serialized_events = json.dumps(handler.events, sort_keys=True)
    if any(secret in serialized_events for secret in ("must-not-log", "agency-private", "passenger-private")):
        raise AssertionError(f"HTTP/query telemetry leaked request values: {serialized_events}")

    snapshot = operational_diagnostics_snapshot()
    if snapshot["counters"]["http_requests"]["2xx"] != 1:
        raise AssertionError(f"HTTP counters were not incremented deterministically: {snapshot}")
    if snapshot["counters"]["slow_requests"]["slow"] != 1 or snapshot["counters"]["slow_queries"]["slow"] < 1:
        raise AssertionError(f"Slow-operation counters were not incremented: {snapshot}")
    try:
        from observability import increment_counter

        increment_counter("http_requests", "path-/unbounded/value")
    except ValueError:
        pass
    else:
        raise AssertionError("Operational counters accepted an unbounded label.")
    if len(COUNTER_LABELS) > 16:
        raise AssertionError("Operational counter family cardinality is unexpectedly broad.")
    diagnostics = json.dumps(query_diagnostic_records(), sort_keys=True)
    if "must-not-log" in diagnostics or "agency-private" in diagnostics:
        raise AssertionError("Persistence diagnostics retained sensitive request values.")


async def verify_unhandled_error_safety() -> None:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/private-error",
        "raw_path": b"/api/private-error",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 50000),
        "server": ("127.0.0.1", 8000),
    }
    handler = CapturingHandler()
    logger = logging.getLogger()
    prior_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        response = await unexpected_exception_handler(
            Request(scope),
            RuntimeError("person@example.test passport AB1234567 must-not-log"),
        )
    finally:
        logger.removeHandler(handler)
        logger.setLevel(prior_level)
    serialized = response.body.decode("utf-8") + json.dumps(handler.events, sort_keys=True)
    if any(value in serialized for value in ("person@example.test", "AB1234567", "must-not-log")):
        raise AssertionError(f"Unhandled-error response or event leaked exception values: {serialized}")
    events = [item for item in handler.events if item.get("event_type") == "unhandled_exception"]
    if not events or (events[-1].get("metadata") or {}).get("exception_class") != "RuntimeError":
        raise AssertionError("Unhandled exception did not produce a safe class-only event.")


def verify_static_registration() -> None:
    assert_application_phase_at_least(
        CURRENT_BUILD_PHASE,
        MINIMUM_PHASE,
        source="canonical build phase",
    )
    settings = get_settings()
    config = validate_config(settings, include_storage=False)
    if not config.get("ok"):
        raise AssertionError(f"Observability configuration validation failed: {config}")
    server_text = (BACKEND / "server.py").read_text(encoding="utf-8")
    security_text = (BACKEND / "http_security.py").read_text(encoding="utf-8")
    router_text = (BACKEND / "routers" / "platform_observability.py").read_text(encoding="utf-8")
    production_readiness_text = (BACKEND / "scripts" / "check_production_readiness.py").read_text(encoding="utf-8")
    requirements_text = (BACKEND / "requirements.txt").read_text(encoding="utf-8").lower()
    for token in (
        "application_startup_initiated",
        "application_startup_completed",
        "application_shutdown_initiated",
        "application_shutdown_completed",
        "observability_diagnostics_performance_telemetry_foundation",
    ):
        if token not in server_text:
            raise AssertionError(f"Server lifecycle/readiness registration is missing {token!r}.")
    if "request.body" in security_text or "response.body" in security_text:
        raise AssertionError("HTTP telemetry accesses request or response bodies.")
    if "/api/platform/diagnostics/observability" not in router_text or "require_platform_role" not in router_text:
        raise AssertionError("Internal diagnostics are not protected by existing Platform authorization.")
    for token in (
        "backend_root = Path(__file__).resolve().parents[1]",
        "from routers import platform_observability",
        "app.include_router(platform_observability.router)",
    ):
        if token not in production_readiness_text:
            raise AssertionError(f"Packaged production diagnostics registration check is missing {token!r}.")
    if any(provider in requirements_text for provider in ("sentry", "datadog", "newrelic", "opentelemetry", "prometheus")):
        raise AssertionError("An external telemetry provider dependency was introduced.")


def verify_live_contracts() -> None:
    request_id = "observability-live-request-0001"
    correlation_id = "observability-live-correlation-0001"
    status_code, health, headers = request(
        "GET",
        "/api/health?token=must-not-log",
        headers={"X-Request-ID": request_id, "X-Correlation-ID": correlation_id},
    )
    if status_code != 200 or not isinstance(health, dict):
        raise AssertionError(f"Live health phase mismatch: {status_code} {health}")
    assert_application_phase_at_least(health.get("phase"), MINIMUM_PHASE, source="health")
    if headers.get("x-request-id") != request_id or headers.get("x-correlation-id") != correlation_id:
        raise AssertionError("Live request/correlation headers were not propagated.")

    validation_status, validation_body, _ = request("POST", "/api/auth/login", {})
    if validation_status != 422 or not isinstance(validation_body, dict):
        raise AssertionError(f"Safe validation error contract failed: {validation_body}")
    if (validation_body.get("error") or {}).get("code") != "validation_error" or "detail" not in validation_body:
        raise AssertionError(f"Validation error lost the backwards-compatible detail field: {validation_body}")

    auth_status, auth_body, _ = request(
        "GET",
        "/api/auth/me",
        headers={"Authorization": "Bearer observability-invalid-token"},
    )
    if auth_status != 401 or not isinstance(auth_body, dict) or (auth_body.get("error") or {}).get("code") != "authentication_required":
        raise AssertionError(f"Safe authentication error contract failed: {auth_body}")

    readiness_status, readiness, _ = request("GET", "/api/readiness")
    if readiness_status != 200 or not isinstance(readiness, dict):
        raise AssertionError(f"Public readiness failed: {readiness}")
    section = readiness.get("observability_diagnostics_performance_telemetry_foundation") or {}
    required_flags = (
        "structured_logging_enabled",
        "production_json_logging_supported",
        "development_human_logging_supported",
        "request_correlation_enabled",
        "http_duration_telemetry_enabled",
        "safe_error_telemetry_enabled",
        "query_telemetry_reused",
        "bounded_operational_counters_enabled",
        "sensitive_value_redaction_enabled",
    )
    if any(section.get(flag) is not True for flag in required_flags):
        raise AssertionError(f"Observability readiness metadata is incomplete: {section}")
    exposed_keys = protected_readiness_keys(readiness)
    if exposed_keys:
        raise AssertionError(
            "Public readiness exposed protected observability diagnostics: "
            + ", ".join(sorted(exposed_keys))
        )

    denied_status, _, _ = request(
        "GET",
        "/api/platform/diagnostics/observability",
        headers={"Authorization": "Bearer observability-invalid-token"},
    )
    if denied_status != 401:
        raise AssertionError("Platform observability diagnostics accepted invalid authorization.")

    diagnostic_status, diagnostic_body, _ = request(
        "GET",
        "/api/platform/diagnostics/observability",
        headers={"X-Demo-User-Email": "owner@aeroassist.dev"},
    )
    if diagnostic_status != 200 or not isinstance(diagnostic_body, dict):
        raise AssertionError(f"Authorized Platform diagnostics failed: {diagnostic_body}")
    diagnostics = diagnostic_body.get("diagnostics") or {}
    if not diagnostics.get("process_local") or diagnostics.get("durable") is not False:
        raise AssertionError(f"Platform diagnostics do not disclose their process-local limits: {diagnostics}")
    if diagnostic_body.get("raw_logs_exposed") is not False or diagnostic_body.get("environment_values_exposed") is not False:
        raise AssertionError(f"Platform diagnostics expose unsafe data classes: {diagnostic_body}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--static", action="store_true", help="Skip live disposable-backend HTTP checks.")
    args = parser.parse_args()
    verify_static_registration()
    verify_event_and_formatting()
    verify_redaction()
    asyncio.run(verify_http_telemetry_and_counters())
    asyncio.run(verify_unhandled_error_safety())
    if not args.static:
        verify_live_contracts()
    print("Phase 56.5.7 observability, diagnostics, and performance telemetry foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
