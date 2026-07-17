from __future__ import annotations

import re
import secrets
import time
from typing import Any
from uuid import uuid4

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from config import AppSettings, get_settings
from observability import (
    bind_request_context,
    emit_event,
    increment_counter,
    normalize_route,
    reset_request_context,
    tenant_context_for_path,
)


REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$")
SAFE_SECURITY_EVENT_FIELDS = {
    "event",
    "outcome",
    "reason",
    "request_id",
    "status_code",
    "route",
}


def correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", None) or uuid4().hex


def log_security_event(event: str, **metadata: Any) -> None:
    safe_metadata = {
        key: value
        for key, value in metadata.items()
        if key in SAFE_SECURITY_EVENT_FIELDS and value is not None
    }
    event_name = event.lower()
    if any(token in event_name for token in ("login", "token", "authentication", "lock")) and safe_metadata.get("outcome") != "success":
        label = "locked" if "lock" in event_name else "expired" if safe_metadata.get("reason") == "expired_token" else "malformed" if safe_metadata.get("reason") == "malformed_token" else "invalid"
        increment_counter("authentication_failures", label)
    if any(token in event_name for token in ("permission", "authorization", "tenant_scope")):
        increment_counter("authorization_failures", "denied")
    emit_event(
        event,
        level="WARNING" if safe_metadata.get("outcome") != "success" else "INFO",
        outcome="denied" if safe_metadata.get("outcome") in {"denied", "locked"} else "failure" if safe_metadata.get("outcome") == "error" else "success",
        operation=normalize_route(str(safe_metadata.get("route") or "")) or None,
        request_id=str(safe_metadata.get("request_id")) if safe_metadata.get("request_id") else None,
        metadata={
            "reason": safe_metadata.get("reason"),
            "status_code": safe_metadata.get("status_code"),
        },
        logger_name="aeroassist.security",
    )


def default_content_security_policy(settings: AppSettings) -> str:
    connect_sources = ["'self'", *settings.cors_allowed_origins]
    if not settings.is_production:
        for origin in settings.cors_allowed_origins:
            if origin.startswith("http://"):
                connect_sources.append("ws://" + origin.removeprefix("http://"))
            elif origin.startswith("https://"):
                connect_sources.append("wss://" + origin.removeprefix("https://"))
    return "; ".join(
        [
            "default-src 'self'",
            "base-uri 'self'",
            "object-src 'none'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "img-src 'self' data:",
            "font-src 'self' data: https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "connect-src " + " ".join(dict.fromkeys(connect_sources)),
        ]
    )


def security_headers(settings: AppSettings | None = None) -> dict[str, str]:
    settings = settings or get_settings()
    if not settings.security_headers_enabled:
        return {}
    hsts_max_age = settings.security_hsts_max_age_seconds if settings.security_hsts_enabled else 0
    hsts = f"max-age={hsts_max_age}"
    if settings.security_hsts_enabled and settings.security_hsts_include_subdomains:
        hsts += "; includeSubDomains"
    if settings.security_hsts_enabled and settings.security_hsts_preload:
        hsts += "; preload"
    return {
        "Content-Security-Policy": settings.security_content_security_policy
        or default_content_security_policy(settings),
        "Strict-Transport-Security": hsts,
        "X-Frame-Options": settings.security_frame_options,
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": settings.security_referrer_policy,
        "Permissions-Policy": settings.security_permissions_policy,
        "Cross-Origin-Resource-Policy": settings.security_cross_origin_resource_policy,
        "Cross-Origin-Opener-Policy": settings.security_cross_origin_opener_policy,
        "Cross-Origin-Embedder-Policy": settings.security_cross_origin_embedder_policy,
    }


class SecurityHttpMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, settings: AppSettings | None = None) -> None:
        super().__init__(app)
        self.settings = settings or get_settings()
        self.headers = security_headers(self.settings)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        supplied_request_id = request.headers.get("x-request-id", "")
        request_id = supplied_request_id if REQUEST_ID_PATTERN.fullmatch(supplied_request_id) else uuid4().hex
        supplied_correlation_id = request.headers.get("x-correlation-id", "")
        correlation = supplied_correlation_id if REQUEST_ID_PATTERN.fullmatch(supplied_correlation_id) else request_id
        tenant_scope, agency_id = tenant_context_for_path(request.url.path)
        request.state.request_id = request_id
        request.state.correlation_id = correlation
        request.state.tenant_scope = tenant_scope
        context_tokens = bind_request_context(
            request_id=request_id,
            correlation_id=correlation,
            tenant_scope=tenant_scope,
            agency_id=agency_id,
        )
        started = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        except Exception:
            duration_ms = (time.perf_counter() - started) * 1000
            increment_counter("http_requests", "5xx")
            increment_counter("unhandled_errors", "unexpected")
            if self.settings.log_request_telemetry_enabled:
                emit_event(
                    "http_request_completed",
                    level="ERROR",
                    outcome="failure",
                    operation=self._route_name(request),
                    duration_ms=duration_ms,
                    metadata={
                        "method": request.method,
                        "route": self._route_name(request),
                        "status_code": 500,
                        "status_class": "5xx",
                        "authenticated": self._authentication_state(request),
                        "slow_operation": duration_ms >= self.settings.log_slow_request_threshold_ms,
                    },
                )
            raise
        finally:
            if response is not None:
                duration_ms = (time.perf_counter() - started) * 1000
                status_class = f"{max(1, min(5, response.status_code // 100))}xx"
                increment_counter("http_requests", status_class)
                slow = duration_ms >= self.settings.log_slow_request_threshold_ms
                if slow:
                    increment_counter("slow_requests", "slow")
                if self.settings.log_request_telemetry_enabled:
                    health_probe = request.url.path in {"/api/health", "/api/readiness"}
                    emit_event(
                        "http_request_completed",
                        level="WARNING" if slow or response.status_code >= 500 else "DEBUG" if health_probe else "INFO",
                        outcome="denied" if response.status_code in {401, 403, 429} else "failure" if response.status_code >= 400 else "success",
                        operation=self._route_name(request),
                        duration_ms=duration_ms,
                        metadata={
                            "method": request.method,
                            "route": self._route_name(request),
                            "status_code": response.status_code,
                            "status_class": status_class,
                            "response_size_bytes": self._response_size(response),
                            "authenticated": self._authentication_state(request),
                            "slow_operation": slow,
                            "request_telemetry_sampled": not health_probe,
                        },
                    )
                origin = request.headers.get("origin")
                if origin and origin not in self.settings.cors_allowed_origins and "access-control-allow-origin" not in response.headers:
                    log_security_event(
                        "cors_origin_rejected",
                        outcome="denied",
                        reason="origin_not_allowlisted",
                        request_id=request_id,
                        status_code=response.status_code,
                        route=self._route_name(request),
                    )
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Correlation-ID"] = correlation
                for name, value in self.headers.items():
                    response.headers[name] = value
            reset_request_context(context_tokens)

    def _route_name(self, request: Request) -> str:
        if not self.settings.log_include_request_path:
            return "http_request"
        route = request.scope.get("route")
        template = getattr(route, "path", None)
        return normalize_route(template or request.url.path) or "http_request"

    @staticmethod
    def _authentication_state(request: Request) -> str:
        if request.headers.get("authorization"):
            return "bearer_present"
        if request.headers.get("x-demo-user-email"):
            return "demo_header_present"
        return "anonymous"

    @staticmethod
    def _response_size(response: Response) -> int | None:
        value = response.headers.get("content-length")
        try:
            return max(0, int(value)) if value is not None else None
        except ValueError:
            return None


def error_code(status_code: int) -> str:
    return {
        400: "bad_request",
        401: "authentication_required",
        403: "permission_denied",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "rate_limited",
    }.get(status_code, "request_failed")


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    request_id = correlation_id(request)
    detail = exc.detail if isinstance(exc.detail, (str, list, dict)) else "Request failed."
    message = detail if isinstance(detail, str) else "Request failed."
    if exc.status_code == 403:
        log_security_event(
            "permission_denied",
            outcome="denied",
            reason="forbidden_route",
            request_id=request_id,
            status_code=exc.status_code,
            route=request.url.path,
        )
    elif exc.status_code == 401:
        log_security_event(
            "authentication_denied",
            outcome="denied",
            reason="authentication_required",
            request_id=request_id,
            status_code=exc.status_code,
            route=request.url.path,
        )
    emit_event(
        "http_error_response",
        level="WARNING" if exc.status_code >= 400 else "INFO",
        outcome="denied" if exc.status_code in {401, 403, 429} else "failure",
        operation=normalize_route(request.url.path),
        metadata={
            "error_code": error_code(exc.status_code),
            "status_code": exc.status_code,
            "retryable": exc.status_code in {408, 429, 503, 504},
        },
    )
    body = {
        "detail": detail,
        "error": {"code": error_code(exc.status_code), "message": message, "request_id": request_id},
    }
    headers = dict(exc.headers or {})
    headers["X-Request-ID"] = request_id
    return JSONResponse(body, status_code=exc.status_code, headers=headers)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    settings = get_settings()
    request_id = correlation_id(request)
    body: dict[str, Any] = {
        "detail": "Request validation failed." if settings.is_production else exc.errors(),
        "error": {
            "code": "validation_error",
            "message": "Request validation failed.",
            "request_id": request_id,
        },
    }
    if not settings.is_production:
        body["validation_errors"] = exc.errors()
    emit_event(
        "validation_error",
        level="WARNING",
        outcome="failure",
        operation=normalize_route(request.url.path),
        metadata={"error_code": "validation_error", "status_code": 422, "retryable": False},
    )
    return JSONResponse(body, status_code=422, headers={"X-Request-ID": request_id})


async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    settings = get_settings()
    request_id = correlation_id(request)
    event = "unexpected_authentication_failure" if request.url.path.startswith("/api/auth") else "unexpected_request_failure"
    log_security_event(
        event,
        outcome="error",
        reason=exc.__class__.__name__,
        request_id=request_id,
        status_code=500,
        route=request.url.path,
    )
    emit_event(
        "unhandled_exception",
        level="ERROR",
        outcome="failure",
        operation=normalize_route(request.url.path),
        metadata={
            "error_code": "internal_error",
            "exception_class": exc.__class__.__name__,
            "status_code": 500,
            "retryable": False,
        },
    )
    message = "Internal server error."
    if not settings.is_production:
        message = f"Unhandled {exc.__class__.__name__}."
    body = {
        "detail": message,
        "error": {"code": "internal_error", "message": message, "request_id": request_id},
    }
    return JSONResponse(
        body,
        status_code=500,
        headers={**security_headers(settings), "X-Request-ID": request_id},
    )


def internal_readiness_authorized(supplied_key: str | None, settings: AppSettings | None = None) -> bool:
    settings = settings or get_settings()
    if not settings.readiness_internal_enabled:
        return False
    if not settings.is_production and not settings.readiness_internal_key:
        return True
    return bool(
        supplied_key
        and settings.readiness_internal_key
        and secrets.compare_digest(supplied_key, settings.readiness_internal_key)
    )


def security_readiness_metadata(settings: AppSettings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    return {
        "authentication_hardening": True,
        "http_security": settings.security_headers_enabled,
        "cors_validation": True,
        "security_logging": True,
        "request_correlation": True,
        "token_validation": True,
        "temporary_account_locking": settings.login_throttle_enabled,
        "exponential_backoff": settings.login_throttle_enabled,
        "permanent_account_locking": False,
        "token_refresh_execution": False,
        "public_readiness_mode": settings.readiness_public_mode,
        "authenticated_platform_readiness_mode": (
            "enabled" if settings.readiness_authenticated_detail_enabled else "disabled"
        ),
        "internal_readiness_mode": "enabled" if settings.readiness_internal_enabled else "disabled",
        "runtime_filesystem_scanning": False,
        "oauth_enabled": False,
        "sso_enabled": False,
        "readiness_required": False,
        "diagnostic": "Phase 56.5.4 hardens existing authentication, opaque sessions, HTTP responses, CORS, readiness projection, and security logging without changing product workflows or adding external identity providers.",
    }
