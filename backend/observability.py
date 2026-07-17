from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import sys
import threading
import time
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from build_phase import CURRENT_BUILD_PHASE


DEFAULT_SERVICE_NAME = "aeroassist-agencyos-api"
REDACTED = "[REDACTED]"
SAFE_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
SENSITIVE_KEY_FRAGMENTS = (
    "password",
    "token",
    "authorization",
    "cookie",
    "secret",
    "mongodb_uri",
    "mongo_password",
    "passport",
    "document_number",
    "medical",
    "health",
    "payment",
    "card",
    "email",
    "phone",
    "date_of_birth",
)
SAFE_METADATA_FIELDS = frozenset(
    {
        "authenticated",
        "collection_category",
        "completed",
        "count",
        "database_classification",
        "degraded",
        "error_code",
        "exception_class",
        "index_classification",
        "logger",
        "method",
        "outcome_class",
        "query_class",
        "reason",
        "readiness_section",
        "request_telemetry_sampled",
        "requested_limit",
        "response_size_bytes",
        "retryable",
        "returned_count",
        "route",
        "slow_operation",
        "startup_step",
        "status_class",
        "status_code",
        "storage_classification",
        "tenant_scoped",
        "timeout",
    }
)
COUNTER_LABELS: dict[str, frozenset[str]] = {
    "http_requests": frozenset({"1xx", "2xx", "3xx", "4xx", "5xx"}),
    "authentication_failures": frozenset({"invalid", "locked", "expired", "malformed"}),
    "authorization_failures": frozenset({"denied"}),
    "unhandled_errors": frozenset({"unexpected"}),
    "database_errors": frozenset({"connectivity", "timeout", "query"}),
    "slow_requests": frozenset({"slow"}),
    "slow_queries": frozenset({"slow"}),
    "readiness_degradations": frozenset({"timeout", "database", "storage", "configuration"}),
}
TIMING_LABELS = frozenset(
    {
        "public_readiness",
        "internal_readiness",
        "startup",
        "shutdown",
        "document_render",
    }
)

_request_id: ContextVar[str | None] = ContextVar("observability_request_id", default=None)
_correlation_id: ContextVar[str | None] = ContextVar("observability_correlation_id", default=None)
_tenant_scope: ContextVar[str] = ContextVar("observability_tenant_scope", default="none")
_agency_id: ContextVar[str | None] = ContextVar("observability_agency_id", default=None)

_runtime: dict[str, Any] = {
    "environment": "development",
    "service_name": DEFAULT_SERVICE_NAME,
    "git_commit": None,
    "deployment_id": None,
    "hash_tenants": True,
    "hash_secret": "aeroassist-observability-development-key",
    "production": False,
}
_started_monotonic = time.monotonic()
_startup_timestamp = datetime.now(timezone.utc)
_counter_lock = threading.Lock()
_counters = {
    counter: {label: 0 for label in labels}
    for counter, labels in COUNTER_LABELS.items()
}
_timings = {
    label: {"count": 0, "last_duration_ms": 0.0, "maximum_duration_ms": 0.0, "degraded_count": 0}
    for label in TIMING_LABELS
}

for _logger_name in (
    "aeroassist.observability",
    "aeroassist.security",
    "aeroassist.persistence",
):
    logging.getLogger(_logger_name).addHandler(logging.NullHandler())

_MONGODB_URI_PATTERN = re.compile(r"mongodb(?:\+srv)?://[^\s\"']+", re.IGNORECASE)
_BEARER_PATTERN = re.compile(r"\bbearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"\b(token|password|secret|authorization|cookie)=([^\s&]+)", re.IGNORECASE
)
_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_PATTERN = re.compile(r"(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)")
_PATH_IDENTIFIER_PATTERN = re.compile(r"^(?:\d+|[0-9a-f]{8,}|[A-Za-z0-9_-]{24,})$", re.IGNORECASE)
_RESOURCE_IDENTIFIER_PARENTS = frozenset(
    {
        "agencies",
        "bookings",
        "clients",
        "documents",
        "emds",
        "offers",
        "passengers",
        "requests",
        "tickets",
        "trips",
        "workspaces",
    }
)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sensitive_key(key: object) -> bool:
    normalized = str(key).strip().lower()
    return any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS)


def sanitize_string(value: str, *, maximum_length: int = 512) -> str:
    clean = _MONGODB_URI_PATTERN.sub("mongodb://[REDACTED]", value)
    clean = _BEARER_PATTERN.sub("Bearer [REDACTED]", clean)
    clean = _SECRET_ASSIGNMENT_PATTERN.sub(lambda match: f"{match.group(1)}={REDACTED}", clean)
    clean = _EMAIL_PATTERN.sub(REDACTED, clean)
    clean = _PHONE_PATTERN.sub(REDACTED, clean)
    return clean[:maximum_length]


def redact_sensitive(value: Any, *, key: str | None = None) -> Any:
    if key is not None and sensitive_key(key):
        return REDACTED
    if isinstance(value, Mapping):
        return {str(item_key): redact_sensitive(item_value, key=str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, str):
        return sanitize_string(value)
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    return sanitize_string(value.__class__.__name__)


def normalize_route(path: str | None) -> str | None:
    if not path:
        return None
    clean_path = path.split("?", 1)[0]
    segments = []
    previous = ""
    for segment in clean_path.split("/"):
        if segment and (
            _PATH_IDENTIFIER_PATTERN.fullmatch(segment)
            or previous in _RESOURCE_IDENTIFIER_PARENTS
        ):
            segments.append("{id}")
        else:
            segments.append(segment[:80])
        previous = segment
    return "/".join(segments)[:256]


def tenant_context_for_path(path: str) -> tuple[str, str | None]:
    clean = path.split("?", 1)[0]
    segments = [segment for segment in clean.split("/") if segment]
    if len(segments) >= 2 and segments[:2] == ["api", "platform"]:
        return "platform", None
    if len(segments) >= 3 and segments[:2] == ["api", "agencies"]:
        return "agency", segments[2]
    if len(segments) >= 2 and segments[:2] in (["api", "agency"], ["api", "portal"]):
        return "agency" if segments[1] == "agency" else "public", None
    if clean.startswith("/api/"):
        return "public", None
    return "none", None


def bind_request_context(
    *,
    request_id: str,
    correlation_id: str,
    tenant_scope: str,
    agency_id: str | None,
) -> tuple[Token[Any], Token[Any], Token[Any], Token[Any]]:
    return (
        _request_id.set(request_id),
        _correlation_id.set(correlation_id),
        _tenant_scope.set(tenant_scope),
        _agency_id.set(agency_id),
    )


def reset_request_context(tokens: Iterable[Token[Any]]) -> None:
    request_token, correlation_token, tenant_token, agency_token = tuple(tokens)
    _request_id.reset(request_token)
    _correlation_id.reset(correlation_token)
    _tenant_scope.reset(tenant_token)
    _agency_id.reset(agency_token)


def current_request_id() -> str | None:
    return _request_id.get()


def current_correlation_id() -> str | None:
    return _correlation_id.get()


def hash_tenant_identifier(value: str | None) -> str | None:
    if not value or not _runtime["hash_tenants"]:
        return None
    digest = hmac.new(
        str(_runtime["hash_secret"]).encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest[:16]


def _safe_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key not in SAFE_METADATA_FIELDS or value is None:
            continue
        clean[key] = redact_sensitive(value, key=key)
    return clean


def structured_event(
    event_type: str,
    *,
    level: str = "INFO",
    outcome: str = "success",
    operation: str | None = None,
    duration_ms: float | None = None,
    metadata: Mapping[str, Any] | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    tenant_scope: str | None = None,
    agency_id: str | None = None,
) -> dict[str, Any]:
    normalized_level = level.upper() if level.upper() in SAFE_LEVELS else "INFO"
    scope = tenant_scope or _tenant_scope.get()
    tenant_identifier = agency_id if agency_id is not None else _agency_id.get()
    event: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "level": normalized_level,
        "event_type": re.sub(r"[^a-z0-9_]+", "_", event_type.lower())[:96],
        "service": _runtime["service_name"],
        "environment": _runtime["environment"],
        "build_phase": CURRENT_BUILD_PHASE,
        "request_id": request_id if request_id is not None else _request_id.get(),
        "correlation_id": correlation_id if correlation_id is not None else _correlation_id.get(),
        "tenant_scope": scope if scope in {"agency", "platform", "public", "none"} else "none",
        "operation": normalize_route(operation) if operation and operation.startswith("/") else sanitize_string(operation, maximum_length=256) if operation else None,
        "duration_ms": round(max(0.0, duration_ms), 3) if duration_ms is not None else None,
        "outcome": outcome if outcome in {"success", "failure", "degraded", "denied"} else "failure",
        "metadata": _safe_metadata(metadata),
    }
    agency_hash = hash_tenant_identifier(tenant_identifier)
    if agency_hash:
        event["agency_id_hash"] = agency_hash
    if _runtime.get("git_commit"):
        event["git_commit"] = _runtime["git_commit"]
    if _runtime.get("deployment_id"):
        event["deployment_id"] = _runtime["deployment_id"]
    return {key: value for key, value in event.items() if value is not None}


class StructuredEventFormatter(logging.Formatter):
    def __init__(self, *, json_format: bool, production: bool) -> None:
        super().__init__()
        self.json_format = json_format
        self.production = production

    def format(self, record: logging.LogRecord) -> str:
        event = getattr(record, "aeroassist_event", None)
        if not isinstance(event, dict):
            event = structured_event(
                "application_log",
                level=record.levelname,
                outcome="failure" if record.levelno >= logging.ERROR else "success",
                operation=record.name,
                metadata={
                    "logger": record.name,
                    "reason": "unstructured_message_suppressed",
                },
            )
        event = redact_sensitive(event)
        if self.json_format:
            return json.dumps(event, sort_keys=True, separators=(",", ":"), default=str)
        prefix = " ".join(
            str(event.get(key, "-"))
            for key in ("timestamp", "level", "event_type")
        )
        context = {
            key: event.get(key)
            for key in ("request_id", "correlation_id", "tenant_scope", "operation", "duration_ms", "outcome")
            if event.get(key) is not None
        }
        if event.get("metadata"):
            context["metadata"] = event["metadata"]
        return f"{prefix} {json.dumps(context, sort_keys=True, separators=(',', ':'), default=str)}"


def configure_observability_logging(settings: Any) -> None:
    _runtime.update(
        {
            "environment": settings.app_env,
            "service_name": settings.log_service_name,
            "git_commit": settings.app_git_commit,
            "deployment_id": settings.app_deployment_id,
            "hash_tenants": settings.log_hash_tenant_identifiers,
            "hash_secret": settings.auth_token_secret or "aeroassist-observability-development-key",
            "production": settings.is_production,
        }
    )
    level = logging._nameToLevel.get(settings.log_level, logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        StructuredEventFormatter(
            json_format=settings.log_format == "json",
            production=settings.is_production,
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    logging.getLogger("uvicorn.access").disabled = True
    logging.captureWarnings(True)


def emit_event(
    event_type: str,
    *,
    level: str = "INFO",
    outcome: str = "success",
    operation: str | None = None,
    duration_ms: float | None = None,
    metadata: Mapping[str, Any] | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    tenant_scope: str | None = None,
    agency_id: str | None = None,
    logger_name: str = "aeroassist.observability",
) -> dict[str, Any]:
    event = structured_event(
        event_type,
        level=level,
        outcome=outcome,
        operation=operation,
        duration_ms=duration_ms,
        metadata=metadata,
        request_id=request_id,
        correlation_id=correlation_id,
        tenant_scope=tenant_scope,
        agency_id=agency_id,
    )
    logging.getLogger(logger_name).log(
        logging._nameToLevel.get(event["level"], logging.INFO),
        event["event_type"],
        extra={"aeroassist_event": event},
    )
    return event


def increment_counter(counter: str, label: str) -> None:
    if counter not in COUNTER_LABELS or label not in COUNTER_LABELS[counter]:
        raise ValueError("Operational counter labels are fixed and bounded.")
    with _counter_lock:
        _counters[counter][label] += 1


def record_timing(label: str, duration_ms: float, *, degraded: bool = False) -> None:
    if label not in TIMING_LABELS:
        raise ValueError("Operational timing labels are fixed and bounded.")
    duration = round(max(0.0, duration_ms), 3)
    with _counter_lock:
        item = _timings[label]
        item["count"] += 1
        item["last_duration_ms"] = duration
        item["maximum_duration_ms"] = max(item["maximum_duration_ms"], duration)
        if degraded:
            item["degraded_count"] += 1


def reset_operational_diagnostics() -> None:
    with _counter_lock:
        for counter, labels in _counters.items():
            _counters[counter] = {label: 0 for label in labels}
        for label in _timings:
            _timings[label] = {
                "count": 0,
                "last_duration_ms": 0.0,
                "maximum_duration_ms": 0.0,
                "degraded_count": 0,
            }


def operational_diagnostics_snapshot() -> dict[str, Any]:
    with _counter_lock:
        counters = {name: dict(values) for name, values in _counters.items()}
        timings = {name: dict(values) for name, values in _timings.items()}
    return {
        "process_local": True,
        "durable": False,
        "reset_on_restart": True,
        "startup_timestamp": _startup_timestamp.isoformat().replace("+00:00", "Z"),
        "uptime_seconds": round(max(0.0, time.monotonic() - _started_monotonic), 3),
        "build_phase": CURRENT_BUILD_PHASE,
        "deployment": {
            "git_commit": _runtime.get("git_commit"),
            "deployment_id": _runtime.get("deployment_id"),
        },
        "counters": counters,
        "timings": timings,
    }


def observability_readiness_metadata(settings: Any) -> dict[str, Any]:
    return {
        "structured_logging_enabled": True,
        "production_json_logging_supported": True,
        "development_human_logging_supported": True,
        "request_correlation_enabled": True,
        "http_duration_telemetry_enabled": settings.log_request_telemetry_enabled,
        "safe_error_telemetry_enabled": True,
        "security_event_integration_enabled": True,
        "query_telemetry_reused": True,
        "slow_request_detection_enabled": True,
        "slow_query_detection_enabled": settings.query_diagnostics_enabled,
        "readiness_timing_enabled": True,
        "bounded_operational_counters_enabled": True,
        "sensitive_value_redaction_enabled": settings.log_redaction_enabled,
        "request_body_logging_disabled": True,
        "response_body_logging_disabled": True,
        "credential_logging_disabled": True,
        "protected_internal_diagnostics_enabled": settings.readiness_authenticated_detail_enabled,
        "external_telemetry_provider_required": False,
        "background_worker_telemetry_placeholder_only": True,
        "log_format": settings.log_format,
        "readiness_required": False,
    }
