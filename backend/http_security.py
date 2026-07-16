from __future__ import annotations

import json
import logging
import re
import secrets
from typing import Any
from uuid import uuid4

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from config import AppSettings, get_settings


SECURITY_LOGGER = logging.getLogger("aeroassist.security")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$")
SAFE_SECURITY_EVENT_FIELDS = {
    "event",
    "outcome",
    "reason",
    "request_id",
    "identity_id",
    "session_id",
    "status_code",
    "route",
}


def correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", None) or uuid4().hex


def log_security_event(event: str, **metadata: Any) -> None:
    payload = {"event": event}
    for key, value in metadata.items():
        if key in SAFE_SECURITY_EVENT_FIELDS and value is not None:
            payload[key] = str(value)[:256]
    SECURITY_LOGGER.warning(json.dumps(payload, sort_keys=True, separators=(",", ":")))


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
        supplied = request.headers.get("x-request-id", "")
        request.state.correlation_id = supplied if REQUEST_ID_PATTERN.fullmatch(supplied) else uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.correlation_id
        for name, value in self.headers.items():
            response.headers[name] = value
        return response


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
