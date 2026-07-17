import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse


TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}
VALID_APP_ENVS = {"development", "test", "production"}
VALID_DB_MODES = {"memory", "mongo"}
VALID_READINESS_PUBLIC_MODES = {"detailed", "summary"}
VALID_TOKEN_REFRESH_POLICIES = {"disabled", "manual_metadata"}
VALID_FRAME_OPTIONS = {"DENY", "SAMEORIGIN"}
VALID_CORP_POLICIES = {"same-origin", "same-site", "cross-origin"}
VALID_COOP_POLICIES = {"same-origin", "same-origin-allow-popups", "unsafe-none"}
VALID_COEP_POLICIES = {"unsafe-none", "require-corp", "credentialless"}
VALID_LOG_FORMATS = {"human", "json"}
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
DEFAULT_QUERY_LIMIT = 50
MAXIMUM_QUERY_LIMIT = 250
DEFAULT_QUERY_SLOW_THRESHOLD_MS = 250
DEFAULT_READINESS_DATABASE_TIMEOUT_SECONDS = 5.0
DEFAULT_LOG_SLOW_REQUEST_THRESHOLD_MS = 1000
DEFAULT_LOG_SLOW_READINESS_THRESHOLD_MS = 1000
DEFAULT_LOG_SLOW_STARTUP_THRESHOLD_MS = 5000
DEFAULT_LOG_SLOW_DOCUMENT_RENDER_THRESHOLD_MS = 2000
DEPLOYMENT_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
PLACEHOLDER_AUTH_SECRETS = {
    "",
    "replace-with-a-long-random-secret",
    "replace-with-a-long-random-production-secret",
    "local-dev-auth-token-secret-change-me",
}
PLACEHOLDER_MONGO_SECRETS = {
    "",
    "changeme",
    "change-me",
    "password",
    "replace-with-a-long-random-mongodb-root-password",
    "replace-with-a-long-random-mongodb-app-password",
}


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return default


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def env_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def configured_storage_root() -> Path:
    configured = os.getenv("DOCUMENT_EXPORT_STORAGE_DIR")
    root = Path(configured).expanduser() if configured else Path(__file__).resolve().parents[1] / ".local" / "document_exports"
    return root.resolve()


def insecure_production_secret(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        len(value) < 16
        or normalized in PLACEHOLDER_MONGO_SECRETS
        or normalized.startswith("replace-with-")
    )


def configured_mongodb_url(production: bool) -> str:
    explicit = os.getenv("MONGODB_URL", "").strip()
    if explicit:
        return explicit
    if not env_bool("MONGO_AUTHENTICATION_ENABLED", False):
        return "" if production else "mongodb://localhost:27017"
    username = os.getenv("MONGO_APP_USERNAME", "").strip()
    password = os.getenv("MONGO_APP_PASSWORD", "")
    host = os.getenv("MONGO_HOST", "mongo").strip() or "mongo"
    port = env_int("MONGO_PORT", 27017)
    auth_source = os.getenv("MONGO_AUTH_SOURCE", "admin").strip() or "admin"
    return (
        f"mongodb://{quote(username, safe='')}:{quote(password, safe='')}@{host}:{port}"
        f"/?authSource={quote(auth_source, safe='')}"
    )


@dataclass(frozen=True)
class AppSettings:
    app_env: str
    demo_auth_enabled: bool
    seed_on_startup: bool
    seed_endpoint_enabled: bool
    db_mode: str
    mongodb_url: str = field(repr=False)
    mongodb_database: str
    mongodb_authentication_enabled: bool
    mongo_root_username: str
    mongo_root_password: str = field(repr=False)
    mongo_app_username: str
    mongo_app_password: str = field(repr=False)
    mongo_auth_source: str
    mongo_host: str
    mongo_port: int
    backup_root: Path
    backup_retention_days: int
    backup_minimum_count: int
    backup_environment_label: str
    cors_allowed_origins: list[str]
    document_export_storage_dir: Path
    log_level: str
    log_format: str
    log_service_name: str
    log_include_request_path: bool
    log_include_query_names: bool
    log_slow_request_threshold_ms: int
    log_slow_readiness_threshold_ms: int
    log_slow_startup_threshold_ms: int
    log_slow_document_render_threshold_ms: int
    log_error_stacktraces: bool
    log_hash_tenant_identifiers: bool
    log_request_telemetry_enabled: bool
    log_redaction_enabled: bool
    app_git_commit: str | None
    app_deployment_id: str | None
    frontend_url: str | None
    public_app_url: str | None
    auth_token_secret: str = field(repr=False)
    token_expiry_minutes: int
    token_clock_skew_seconds: int
    token_refresh_policy: str
    token_refresh_window_minutes: int
    login_throttle_enabled: bool
    login_max_attempts: int
    login_lock_duration_seconds: int
    login_failure_reset_seconds: int
    login_backoff_base_seconds: float
    login_backoff_max_seconds: float
    security_headers_enabled: bool
    security_content_security_policy: str | None
    security_hsts_enabled: bool
    security_hsts_max_age_seconds: int
    security_hsts_include_subdomains: bool
    security_hsts_preload: bool
    security_frame_options: str
    security_referrer_policy: str
    security_permissions_policy: str
    security_cross_origin_resource_policy: str
    security_cross_origin_opener_policy: str
    security_cross_origin_embedder_policy: str
    readiness_public_mode: str
    readiness_authenticated_detail_enabled: bool
    readiness_internal_enabled: bool
    readiness_internal_key: str = field(repr=False)
    query_default_limit: int
    query_maximum_limit: int
    query_slow_threshold_ms: int
    query_diagnostics_enabled: bool
    readiness_database_timeout_seconds: float
    invitation_expiry_hours: int
    password_reset_expiry_hours: int
    smtp_secret_refs: list[str]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


def get_settings() -> AppSettings:
    app_env = os.getenv("APP_ENV", "development").strip().lower() or "development"
    production = app_env == "production"
    return AppSettings(
        app_env=app_env,
        demo_auth_enabled=env_bool("DEMO_AUTH_ENABLED", not production),
        seed_on_startup=env_bool("SEED_ON_STARTUP", not production),
        seed_endpoint_enabled=env_bool("SEED_ENDPOINT_ENABLED", not production),
        db_mode=os.getenv("AEROASSIST_DB_MODE", "memory").strip().lower() or "memory",
        mongodb_url=configured_mongodb_url(production),
        mongodb_database=(
            os.getenv("MONGO_DATABASE") or os.getenv("MONGODB_DATABASE", "aeroassist_agencyos")
        ).strip() or "aeroassist_agencyos",
        mongodb_authentication_enabled=env_bool("MONGO_AUTHENTICATION_ENABLED", False),
        mongo_root_username=os.getenv("MONGO_INITDB_ROOT_USERNAME", "").strip(),
        mongo_root_password=os.getenv("MONGO_INITDB_ROOT_PASSWORD", ""),
        mongo_app_username=os.getenv("MONGO_APP_USERNAME", "").strip(),
        mongo_app_password=os.getenv("MONGO_APP_PASSWORD", ""),
        mongo_auth_source=os.getenv("MONGO_AUTH_SOURCE", "admin").strip() or "admin",
        mongo_host=os.getenv("MONGO_HOST", "mongo" if production else "localhost").strip(),
        mongo_port=env_int("MONGO_PORT", 27017),
        backup_root=Path(os.getenv("BACKUP_ROOT", "/var/backups/aeroassist")).expanduser(),
        backup_retention_days=env_int("BACKUP_RETENTION_DAYS", 30),
        backup_minimum_count=env_int("BACKUP_MINIMUM_COUNT", 7),
        backup_environment_label=os.getenv(
            "BACKUP_ENVIRONMENT_LABEL", "production" if production else "development"
        ).strip(),
        cors_allowed_origins=env_list("CORS_ALLOWED_ORIGINS", DEFAULT_CORS_ORIGINS),
        document_export_storage_dir=configured_storage_root(),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
        log_format=os.getenv("LOG_FORMAT", "json" if production else "human").strip().lower(),
        log_service_name=os.getenv("LOG_SERVICE_NAME", "aeroassist-agencyos-api").strip(),
        log_include_request_path=env_bool("LOG_INCLUDE_REQUEST_PATH", True),
        log_include_query_names=env_bool("LOG_INCLUDE_QUERY_NAMES", True),
        log_slow_request_threshold_ms=env_int(
            "LOG_SLOW_REQUEST_THRESHOLD_MS", DEFAULT_LOG_SLOW_REQUEST_THRESHOLD_MS
        ),
        log_slow_readiness_threshold_ms=env_int(
            "LOG_SLOW_READINESS_THRESHOLD_MS", DEFAULT_LOG_SLOW_READINESS_THRESHOLD_MS
        ),
        log_slow_startup_threshold_ms=env_int(
            "LOG_SLOW_STARTUP_THRESHOLD_MS", DEFAULT_LOG_SLOW_STARTUP_THRESHOLD_MS
        ),
        log_slow_document_render_threshold_ms=env_int(
            "LOG_SLOW_DOCUMENT_RENDER_THRESHOLD_MS", DEFAULT_LOG_SLOW_DOCUMENT_RENDER_THRESHOLD_MS
        ),
        log_error_stacktraces=env_bool("LOG_ERROR_STACKTRACES", not production),
        log_hash_tenant_identifiers=env_bool("LOG_HASH_TENANT_IDENTIFIERS", True),
        log_request_telemetry_enabled=env_bool("LOG_REQUEST_TELEMETRY_ENABLED", True),
        log_redaction_enabled=env_bool("LOG_REDACTION_ENABLED", True),
        app_git_commit=os.getenv("APP_GIT_COMMIT", "").strip() or None,
        app_deployment_id=os.getenv("APP_DEPLOYMENT_ID", "").strip() or None,
        frontend_url=os.getenv("FRONTEND_URL") or None,
        public_app_url=os.getenv("PUBLIC_APP_URL") or None,
        auth_token_secret=os.getenv("AUTH_TOKEN_SECRET", ""),
        token_expiry_minutes=env_int("TOKEN_EXPIRY_MINUTES", 720),
        token_clock_skew_seconds=env_int("TOKEN_CLOCK_SKEW_SECONDS", 30),
        token_refresh_policy=os.getenv("TOKEN_REFRESH_POLICY", "disabled").strip().lower() or "disabled",
        token_refresh_window_minutes=env_int("TOKEN_REFRESH_WINDOW_MINUTES", 60),
        login_throttle_enabled=env_bool("LOGIN_THROTTLE_ENABLED", True),
        login_max_attempts=env_int("LOGIN_MAX_ATTEMPTS", 5),
        login_lock_duration_seconds=env_int("LOGIN_LOCK_DURATION_SECONDS", 900),
        login_failure_reset_seconds=env_int("LOGIN_FAILURE_RESET_SECONDS", 900),
        login_backoff_base_seconds=env_float("LOGIN_BACKOFF_BASE_SECONDS", 0.1),
        login_backoff_max_seconds=env_float("LOGIN_BACKOFF_MAX_SECONDS", 2.0),
        security_headers_enabled=env_bool("SECURITY_HEADERS_ENABLED", True),
        security_content_security_policy=os.getenv("SECURITY_CONTENT_SECURITY_POLICY") or None,
        security_hsts_enabled=env_bool("SECURITY_HSTS_ENABLED", production),
        security_hsts_max_age_seconds=env_int("SECURITY_HSTS_MAX_AGE_SECONDS", 31_536_000),
        security_hsts_include_subdomains=env_bool("SECURITY_HSTS_INCLUDE_SUBDOMAINS", True),
        security_hsts_preload=env_bool("SECURITY_HSTS_PRELOAD", False),
        security_frame_options=os.getenv("SECURITY_FRAME_OPTIONS", "DENY").strip() or "DENY",
        security_referrer_policy=os.getenv("SECURITY_REFERRER_POLICY", "no-referrer").strip() or "no-referrer",
        security_permissions_policy=os.getenv(
            "SECURITY_PERMISSIONS_POLICY",
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
        ).strip(),
        security_cross_origin_resource_policy=os.getenv(
            "SECURITY_CROSS_ORIGIN_RESOURCE_POLICY", "same-site"
        ).strip() or "same-site",
        security_cross_origin_opener_policy=os.getenv(
            "SECURITY_CROSS_ORIGIN_OPENER_POLICY", "same-origin"
        ).strip() or "same-origin",
        security_cross_origin_embedder_policy=os.getenv(
            "SECURITY_CROSS_ORIGIN_EMBEDDER_POLICY", "unsafe-none"
        ).strip() or "unsafe-none",
        readiness_public_mode=os.getenv(
            "READINESS_PUBLIC_MODE", "summary" if production else "detailed"
        ).strip().lower(),
        readiness_authenticated_detail_enabled=env_bool("READINESS_AUTHENTICATED_DETAIL_ENABLED", True),
        readiness_internal_enabled=env_bool("READINESS_INTERNAL_ENABLED", not production),
        readiness_internal_key=os.getenv("READINESS_INTERNAL_KEY", ""),
        query_default_limit=env_int("QUERY_DEFAULT_LIMIT", DEFAULT_QUERY_LIMIT),
        query_maximum_limit=env_int("QUERY_MAXIMUM_LIMIT", MAXIMUM_QUERY_LIMIT),
        query_slow_threshold_ms=env_int("QUERY_SLOW_THRESHOLD_MS", DEFAULT_QUERY_SLOW_THRESHOLD_MS),
        query_diagnostics_enabled=env_bool("QUERY_DIAGNOSTICS_ENABLED", True),
        readiness_database_timeout_seconds=env_float(
            "READINESS_DATABASE_TIMEOUT_SECONDS",
            DEFAULT_READINESS_DATABASE_TIMEOUT_SECONDS,
        ),
        invitation_expiry_hours=env_int("INVITATION_EXPIRY_HOURS", 72),
        password_reset_expiry_hours=env_int("PASSWORD_RESET_EXPIRY_HOURS", 2),
        smtp_secret_refs=env_list("SMTP_SECRET_REFS"),
    )


def validate_config(settings: AppSettings | None = None, include_storage: bool = True) -> dict[str, Any]:
    settings = settings or get_settings()
    checks: list[dict[str, str]] = []

    def add(level: str, key: str, message: str) -> None:
        checks.append({"level": level, "key": key, "message": message})

    if settings.app_env not in VALID_APP_ENVS:
        add("fail", "APP_ENV", "APP_ENV must be development, test, or production.")
    else:
        add("pass", "APP_ENV", f"APP_ENV is {settings.app_env}.")

    if settings.db_mode not in VALID_DB_MODES:
        add("fail", "AEROASSIST_DB_MODE", "AEROASSIST_DB_MODE must be memory or mongo.")
    elif settings.is_production and settings.db_mode != "mongo":
        add("fail", "AEROASSIST_DB_MODE", "Production requires AEROASSIST_DB_MODE=mongo.")
    elif settings.db_mode == "memory":
        add("warn", "AEROASSIST_DB_MODE", "Memory database mode is for local development only.")
    else:
        add("pass", "AEROASSIST_DB_MODE", "MongoDB mode is configured.")

    if settings.is_production and not settings.mongodb_url:
        add("fail", "MONGODB_URL", "Production requires MONGODB_URL.")
    elif settings.db_mode == "mongo" and not settings.mongodb_url:
        add("fail", "MONGODB_URL", "MongoDB mode requires MONGODB_URL.")
    else:
        add("pass", "MONGODB_URL", "MongoDB URL is configured." if settings.mongodb_url else "MongoDB URL is not required for memory mode.")

    if not settings.mongodb_database:
        add("fail", "MONGODB_DATABASE", "MONGODB_DATABASE is required.")
    else:
        add("pass", "MONGODB_DATABASE", "MongoDB database name is configured.")

    auth_flag_explicit = "MONGO_AUTHENTICATION_ENABLED" in os.environ
    if settings.is_production and not auth_flag_explicit:
        add(
            "fail",
            "MONGO_AUTHENTICATION_ENABLED",
            "Production must explicitly enable authenticated MongoDB after completing the existing-volume migration runbook.",
        )
    elif settings.is_production and not settings.mongodb_authentication_enabled:
        add(
            "fail",
            "MONGO_AUTHENTICATION_ENABLED",
            "Production MongoDB authentication must be enabled; unauthenticated fallback is not allowed.",
        )
    elif settings.mongodb_authentication_enabled:
        missing_credentials = [
            name
            for name, value in (
                ("MONGO_APP_USERNAME", settings.mongo_app_username),
                ("MONGO_APP_PASSWORD", settings.mongo_app_password),
            )
            if not value
        ]
        if missing_credentials:
            add(
                "fail",
                "MONGO_AUTHENTICATION_CREDENTIALS",
                "Authenticated MongoDB is missing required application credentials.",
            )
        elif bool(settings.mongo_root_username) != bool(settings.mongo_root_password):
            add(
                "fail",
                "MONGO_AUTHENTICATION_CREDENTIALS",
                "MongoDB administrative credentials must be supplied as a complete pair when present.",
            )
        elif settings.is_production and insecure_production_secret(settings.mongo_app_password):
            add(
                "fail",
                "MONGO_AUTHENTICATION_CREDENTIALS",
                "The production MongoDB application password must be a non-placeholder value of at least 16 characters.",
            )
        elif (
            settings.is_production
            and settings.mongo_root_password
            and insecure_production_secret(settings.mongo_root_password)
        ):
            add(
                "fail",
                "MONGO_AUTHENTICATION_CREDENTIALS",
                "The production MongoDB administrative password must be a non-placeholder value of at least 16 characters when present.",
            )
        elif not settings.mongo_host or not settings.mongo_auth_source or settings.mongo_port < 1 or settings.mongo_port > 65535:
            add("fail", "MONGO_AUTHENTICATION_CONFIGURATION", "MongoDB auth source and port must be valid.")
        elif not urlparse(settings.mongodb_url).username:
            add(
                "fail",
                "MONGODB_URL",
                "Authenticated MongoDB mode requires an authenticated application URI.",
            )
        else:
            add(
                "pass",
                "MONGO_AUTHENTICATION_ENABLED",
                "Authenticated MongoDB uses dedicated application credentials; administrative credentials are optional at application runtime and values are not reported.",
            )
    else:
        add("warn", "MONGO_AUTHENTICATION_ENABLED", "MongoDB authentication is disabled for explicit non-production use.")

    if settings.backup_retention_days < 1:
        add("fail", "BACKUP_RETENTION_DAYS", "Backup retention days must be at least 1.")
    elif settings.backup_minimum_count < 1:
        add("fail", "BACKUP_MINIMUM_COUNT", "Backup minimum count must be at least 1.")
    elif not settings.backup_environment_label:
        add("fail", "BACKUP_ENVIRONMENT_LABEL", "Backup environment label must not be empty.")
    else:
        add("pass", "BACKUP_RETENTION", "Backup retention and minimum-count controls are configured.")

    if settings.is_production and settings.demo_auth_enabled:
        add("fail", "DEMO_AUTH_ENABLED", "Production must disable demo header auth.")
    elif settings.demo_auth_enabled:
        add("warn", "DEMO_AUTH_ENABLED", "Demo header auth is enabled for local development.")
    else:
        add("pass", "DEMO_AUTH_ENABLED", "Demo header auth is disabled.")

    if settings.is_production and settings.seed_on_startup:
        add("fail", "SEED_ON_STARTUP", "Production must not seed demo data on startup.")
    elif settings.seed_on_startup:
        add("warn", "SEED_ON_STARTUP", "Startup seed is enabled for local development.")
    else:
        add("pass", "SEED_ON_STARTUP", "Startup seed is disabled.")

    if settings.is_production and settings.seed_endpoint_enabled:
        add("fail", "SEED_ENDPOINT_ENABLED", "Production seed endpoint must be disabled unless running a controlled maintenance task.")
    elif settings.seed_endpoint_enabled:
        add("warn", "SEED_ENDPOINT_ENABLED", "Seed endpoint is enabled for local development.")
    else:
        add("pass", "SEED_ENDPOINT_ENABLED", "Seed endpoint is disabled.")

    if settings.is_production and settings.auth_token_secret in PLACEHOLDER_AUTH_SECRETS:
        add("fail", "AUTH_TOKEN_SECRET", "Production requires a non-placeholder AUTH_TOKEN_SECRET.")
    elif settings.auth_token_secret in PLACEHOLDER_AUTH_SECRETS:
        add("warn", "AUTH_TOKEN_SECRET", "AUTH_TOKEN_SECRET is using a local placeholder.")
    else:
        add("pass", "AUTH_TOKEN_SECRET", "AUTH_TOKEN_SECRET is configured.")

    if settings.token_expiry_minutes <= 0:
        add("fail", "TOKEN_EXPIRY_MINUTES", "TOKEN_EXPIRY_MINUTES must be greater than zero.")
    else:
        add("pass", "TOKEN_EXPIRY_MINUTES", "Token lifetime is configured.")

    if not 0 <= settings.token_clock_skew_seconds <= 300:
        add("fail", "TOKEN_CLOCK_SKEW_SECONDS", "TOKEN_CLOCK_SKEW_SECONDS must be between 0 and 300.")
    else:
        add("pass", "TOKEN_CLOCK_SKEW_SECONDS", "Token clock-skew tolerance is bounded.")

    if settings.token_refresh_policy not in VALID_TOKEN_REFRESH_POLICIES:
        add("fail", "TOKEN_REFRESH_POLICY", "TOKEN_REFRESH_POLICY must be disabled or manual_metadata.")
    elif settings.token_refresh_window_minutes < 0:
        add("fail", "TOKEN_REFRESH_WINDOW_MINUTES", "TOKEN_REFRESH_WINDOW_MINUTES must not be negative.")
    else:
        add("pass", "TOKEN_REFRESH_POLICY", "Token refresh policy metadata is configured; no refresh execution is enabled.")

    if settings.login_max_attempts < 2:
        add("fail", "LOGIN_MAX_ATTEMPTS", "LOGIN_MAX_ATTEMPTS must be at least 2.")
    elif settings.login_lock_duration_seconds <= 0 or settings.login_failure_reset_seconds <= 0:
        add("fail", "LOGIN_THROTTLE_WINDOWS", "Login lock and failure reset intervals must be greater than zero.")
    elif settings.login_backoff_base_seconds < 0 or settings.login_backoff_max_seconds < settings.login_backoff_base_seconds:
        add("fail", "LOGIN_BACKOFF", "Login backoff must be non-negative and its maximum must not be below its base.")
    else:
        add("pass", "LOGIN_THROTTLE", "Temporary login throttling and reset windows are configured.")

    if not settings.cors_allowed_origins:
        add("fail", "CORS_ALLOWED_ORIGINS", "At least one CORS origin is required.")
    elif "*" in settings.cors_allowed_origins and settings.is_production:
        add("fail", "CORS_ALLOWED_ORIGINS", "Production CORS must not include wildcard '*'.")
    elif settings.is_production and any("localhost" in origin or "127.0.0.1" in origin for origin in settings.cors_allowed_origins):
        add("fail", "CORS_ALLOWED_ORIGINS", "Production CORS must not include local development origins.")
    elif any(origin == "*" for origin in settings.cors_allowed_origins):
        add("warn", "CORS_ALLOWED_ORIGINS", "Wildcard CORS is development-only.")
    elif any(
        urlparse(origin).scheme not in {"http", "https"}
        or not urlparse(origin).netloc
        or urlparse(origin).path != ""
        or bool(urlparse(origin).params or urlparse(origin).query or urlparse(origin).fragment)
        or bool(urlparse(origin).username or urlparse(origin).password)
        for origin in settings.cors_allowed_origins
    ):
        add("fail", "CORS_ALLOWED_ORIGINS", "CORS origins must be absolute HTTP(S) origins without paths.")
    else:
        add("pass", "CORS_ALLOWED_ORIGINS", "CORS origins are configured.")

    if settings.readiness_public_mode not in VALID_READINESS_PUBLIC_MODES:
        add("fail", "READINESS_PUBLIC_MODE", "READINESS_PUBLIC_MODE must be summary or detailed.")
    elif settings.is_production and settings.readiness_public_mode != "summary":
        add("fail", "READINESS_PUBLIC_MODE", "Production public readiness must use summary mode.")
    else:
        add("pass", "READINESS_PUBLIC_MODE", f"Public readiness mode is {settings.readiness_public_mode}.")

    if settings.is_production and settings.readiness_internal_enabled and len(settings.readiness_internal_key) < 24:
        add("fail", "READINESS_INTERNAL_KEY", "Enabled production internal readiness requires a key of at least 24 characters.")
    elif settings.readiness_internal_enabled:
        add("pass", "READINESS_INTERNAL_ENABLED", "Internal readiness is enabled with environment-appropriate access control.")
    else:
        add("pass", "READINESS_INTERNAL_ENABLED", "Internal readiness is disabled.")

    if settings.readiness_authenticated_detail_enabled:
        add("pass", "READINESS_AUTHENTICATED_DETAIL_ENABLED", "Detailed readiness is available to active Platform users.")
    else:
        add("pass", "READINESS_AUTHENTICATED_DETAIL_ENABLED", "Authenticated detailed readiness is disabled.")

    if settings.query_default_limit <= 0:
        add("fail", "QUERY_DEFAULT_LIMIT", "QUERY_DEFAULT_LIMIT must be greater than zero.")
    elif settings.query_maximum_limit < settings.query_default_limit or settings.query_maximum_limit > 1000:
        add("fail", "QUERY_MAXIMUM_LIMIT", "QUERY_MAXIMUM_LIMIT must be at least the default and no greater than 1000.")
    else:
        add("pass", "QUERY_LIMITS", "Persistence query limits are bounded and ordered.")

    if settings.query_slow_threshold_ms <= 0:
        add("fail", "QUERY_SLOW_THRESHOLD_MS", "QUERY_SLOW_THRESHOLD_MS must be greater than zero.")
    elif settings.readiness_database_timeout_seconds <= 0 or settings.readiness_database_timeout_seconds > 60:
        add("fail", "READINESS_DATABASE_TIMEOUT_SECONDS", "Readiness database timeout must be greater than zero and no more than 60 seconds.")
    else:
        add("pass", "QUERY_DIAGNOSTICS", "Query diagnostics and readiness timeout controls are configured.")

    if settings.security_hsts_max_age_seconds < 0:
        add("fail", "SECURITY_HSTS_MAX_AGE_SECONDS", "HSTS max age must not be negative.")
    elif settings.is_production and not settings.security_headers_enabled:
        add("fail", "SECURITY_HEADERS_ENABLED", "Production must enable HTTP security headers.")
    elif settings.is_production and not settings.security_hsts_enabled:
        add("fail", "SECURITY_HSTS_ENABLED", "Production must enable HSTS.")
    else:
        add("pass", "SECURITY_HEADERS", "HTTP security header policy is configured.")

    configured_header_values = [
        settings.security_content_security_policy or "",
        settings.security_frame_options,
        settings.security_referrer_policy,
        settings.security_permissions_policy,
        settings.security_cross_origin_resource_policy,
        settings.security_cross_origin_opener_policy,
        settings.security_cross_origin_embedder_policy,
    ]
    if any("\r" in value or "\n" in value for value in configured_header_values):
        add("fail", "SECURITY_HEADER_VALUES", "HTTP security header values must not contain line breaks.")
    elif settings.security_frame_options.upper() not in VALID_FRAME_OPTIONS:
        add("fail", "SECURITY_FRAME_OPTIONS", "SECURITY_FRAME_OPTIONS must be DENY or SAMEORIGIN.")
    elif settings.security_cross_origin_resource_policy not in VALID_CORP_POLICIES:
        add("fail", "SECURITY_CROSS_ORIGIN_RESOURCE_POLICY", "Invalid Cross-Origin-Resource-Policy value.")
    elif settings.security_cross_origin_opener_policy not in VALID_COOP_POLICIES:
        add("fail", "SECURITY_CROSS_ORIGIN_OPENER_POLICY", "Invalid Cross-Origin-Opener-Policy value.")
    elif settings.security_cross_origin_embedder_policy not in VALID_COEP_POLICIES:
        add("fail", "SECURITY_CROSS_ORIGIN_EMBEDDER_POLICY", "Invalid Cross-Origin-Embedder-Policy value.")
    elif not settings.security_referrer_policy or not settings.security_permissions_policy:
        add("fail", "SECURITY_HEADER_VALUES", "Referrer and Permissions policies must not be empty.")
    else:
        add("pass", "SECURITY_HEADER_VALUES", "HTTP security header values are valid and injection-safe.")

    if include_storage:
        if settings.is_production and not os.getenv("DOCUMENT_EXPORT_STORAGE_DIR"):
            add("fail", "DOCUMENT_EXPORT_STORAGE_DIR", "Production requires an explicit DOCUMENT_EXPORT_STORAGE_DIR.")
        try:
            settings.document_export_storage_dir.mkdir(parents=True, exist_ok=True)
            probe = settings.document_export_storage_dir / ".aeroassist-write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            if os.getenv("DOCUMENT_EXPORT_STORAGE_DIR") or not settings.is_production:
                add("pass", "DOCUMENT_EXPORT_STORAGE_DIR", "Document export storage directory is writable.")
        except OSError:
            add("fail", "DOCUMENT_EXPORT_STORAGE_DIR", "Document export storage directory is not writable.")
    elif settings.is_production and not os.getenv("DOCUMENT_EXPORT_STORAGE_DIR"):
        add("fail", "DOCUMENT_EXPORT_STORAGE_DIR", "Production requires an explicit DOCUMENT_EXPORT_STORAGE_DIR.")
    elif not os.getenv("DOCUMENT_EXPORT_STORAGE_DIR"):
        add("warn", "DOCUMENT_EXPORT_STORAGE_DIR", "Using local default .local/document_exports.")
    else:
        add("pass", "DOCUMENT_EXPORT_STORAGE_DIR", "Document export storage directory is configured.")

    if settings.log_level not in logging._nameToLevel:
        add("warn", "LOG_LEVEL", "LOG_LEVEL is not a standard Python logging level; INFO will be used by logging setup.")
    else:
        add("pass", "LOG_LEVEL", f"LOG_LEVEL is {settings.log_level}.")

    if settings.log_format not in VALID_LOG_FORMATS:
        add("fail", "LOG_FORMAT", "LOG_FORMAT must be human or json.")
    elif settings.is_production and settings.log_format != "json":
        add("fail", "LOG_FORMAT", "Production requires JSON structured logging.")
    elif not settings.log_service_name or len(settings.log_service_name) > 80:
        add("fail", "LOG_SERVICE_NAME", "LOG_SERVICE_NAME must contain between 1 and 80 characters.")
    else:
        add("pass", "LOG_FORMAT", f"Logging format {settings.log_format} is configured for stdout collection.")

    threshold_values = (
        settings.log_slow_request_threshold_ms,
        settings.log_slow_readiness_threshold_ms,
        settings.log_slow_startup_threshold_ms,
        settings.log_slow_document_render_threshold_ms,
    )
    if any(value <= 0 or value > 3_600_000 for value in threshold_values):
        add("fail", "LOG_SLOW_THRESHOLDS", "Observability thresholds must be greater than zero and no more than one hour in milliseconds.")
    else:
        add("pass", "LOG_SLOW_THRESHOLDS", "HTTP, readiness, startup, and document-render warning thresholds are bounded.")

    if settings.is_production and settings.log_level in {"DEBUG", "NOTSET"}:
        add("fail", "LOG_LEVEL", "Production logging must not use DEBUG or NOTSET.")
    elif settings.is_production and settings.log_error_stacktraces:
        add("fail", "LOG_ERROR_STACKTRACES", "Production stacktrace logging must be disabled.")
    elif settings.is_production and not settings.log_request_telemetry_enabled:
        add("fail", "LOG_REQUEST_TELEMETRY_ENABLED", "Production request telemetry must be enabled.")
    elif settings.is_production and not settings.log_redaction_enabled:
        add("fail", "LOG_REDACTION_ENABLED", "Production structured logging redaction must be enabled.")
    elif settings.is_production and not settings.log_hash_tenant_identifiers:
        add("fail", "LOG_HASH_TENANT_IDENTIFIERS", "Production tenant identifiers must be hashed when included in telemetry.")
    else:
        add("pass", "LOG_PRIVACY", "Request telemetry, redaction, tenant hashing, and stacktrace policy are environment-safe.")

    invalid_deployment_identifiers = [
        name
        for name, value in (
            ("APP_GIT_COMMIT", settings.app_git_commit),
            ("APP_DEPLOYMENT_ID", settings.app_deployment_id),
        )
        if value and DEPLOYMENT_IDENTIFIER_PATTERN.fullmatch(value) is None
    ]
    if invalid_deployment_identifiers:
        add("fail", "DEPLOYMENT_IDENTIFIERS", "Deployment identifiers must use 1-64 alphanumeric, dot, underscore, or hyphen characters.")
    else:
        add("pass", "DEPLOYMENT_IDENTIFIERS", "Optional deployment correlation identifiers are syntactically safe.")

    failures = [check for check in checks if check["level"] == "fail"]
    warnings = [check for check in checks if check["level"] == "warn"]
    return {
        "ok": not failures,
        "checks": checks,
        "failure_count": len(failures),
        "warning_count": len(warnings),
    }


def configure_logging(settings: AppSettings | None = None) -> None:
    settings = settings or get_settings()
    from observability import configure_observability_logging

    configure_observability_logging(settings)


def assert_startup_safe(settings: AppSettings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    result = validate_config(settings, include_storage=True)
    if settings.is_production and not result["ok"]:
        messages = "; ".join(check["message"] for check in result["checks"] if check["level"] == "fail")
        raise RuntimeError(f"Unsafe production configuration: {messages}")
    return result
