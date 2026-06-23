import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}
VALID_APP_ENVS = {"development", "test", "production"}
VALID_DB_MODES = {"memory", "mongo"}
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
PLACEHOLDER_AUTH_SECRETS = {
    "",
    "replace-with-a-long-random-secret",
    "replace-with-a-long-random-production-secret",
    "local-dev-auth-token-secret-change-me",
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


def env_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def configured_storage_root() -> Path:
    configured = os.getenv("DOCUMENT_EXPORT_STORAGE_DIR")
    root = Path(configured).expanduser() if configured else Path(__file__).resolve().parents[1] / ".local" / "document_exports"
    return root.resolve()


@dataclass(frozen=True)
class AppSettings:
    app_env: str
    demo_auth_enabled: bool
    seed_on_startup: bool
    seed_endpoint_enabled: bool
    db_mode: str
    mongodb_url: str
    mongodb_database: str
    cors_allowed_origins: list[str]
    document_export_storage_dir: Path
    log_level: str
    frontend_url: str | None
    public_app_url: str | None
    auth_token_secret: str
    token_expiry_minutes: int
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
        mongodb_url=os.getenv("MONGODB_URL", "" if production else "mongodb://localhost:27017").strip(),
        mongodb_database=os.getenv("MONGODB_DATABASE", "aeroassist_agencyos").strip() or "aeroassist_agencyos",
        cors_allowed_origins=env_list("CORS_ALLOWED_ORIGINS", DEFAULT_CORS_ORIGINS),
        document_export_storage_dir=configured_storage_root(),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
        frontend_url=os.getenv("FRONTEND_URL") or None,
        public_app_url=os.getenv("PUBLIC_APP_URL") or None,
        auth_token_secret=os.getenv("AUTH_TOKEN_SECRET", ""),
        token_expiry_minutes=env_int("TOKEN_EXPIRY_MINUTES", 720),
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

    if not settings.cors_allowed_origins:
        add("fail", "CORS_ALLOWED_ORIGINS", "At least one CORS origin is required.")
    elif "*" in settings.cors_allowed_origins and settings.is_production:
        add("fail", "CORS_ALLOWED_ORIGINS", "Production CORS must not include wildcard '*'.")
    elif settings.is_production and any("localhost" in origin or "127.0.0.1" in origin for origin in settings.cors_allowed_origins):
        add("fail", "CORS_ALLOWED_ORIGINS", "Production CORS must not include local development origins.")
    elif any(origin == "*" for origin in settings.cors_allowed_origins):
        add("warn", "CORS_ALLOWED_ORIGINS", "Wildcard CORS is development-only.")
    else:
        add("pass", "CORS_ALLOWED_ORIGINS", "CORS origins are configured.")

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
    level = logging._nameToLevel.get(settings.log_level, logging.INFO)
    logging.basicConfig(level=level, format="%(levelname)s:%(name)s:%(message)s")


def assert_startup_safe(settings: AppSettings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    result = validate_config(settings, include_storage=True)
    if settings.is_production and not result["ok"]:
        messages = "; ".join(check["message"] for check in result["checks"] if check["level"] == "fail")
        raise RuntimeError(f"Unsafe production configuration: {messages}")
    return result
