#!/usr/bin/env python3
import os
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.pdf_rendering_service import pdf_capabilities
from services.secret_service import check_secret, mask_secret_ref


def status_line(level: str, message: str) -> str:
    return f"{level}: {message}"


def main() -> int:
    lines: list[str] = []
    errors = 0

    db_mode = os.getenv("AEROASSIST_DB_MODE", "memory")
    if db_mode != "mongo":
        errors += 1
        lines.append(status_line("ERROR", "AEROASSIST_DB_MODE should be mongo for production."))
    else:
        lines.append(status_line("OK", "AEROASSIST_DB_MODE is mongo."))

    mongo_url = os.getenv("MONGODB_URL")
    if not mongo_url:
        errors += 1
        lines.append(status_line("ERROR", "MONGODB_URL is not configured."))
    else:
        lines.append(status_line("OK", "MONGODB_URL is configured."))

    demo_auth = os.getenv("DEMO_AUTH_ENABLED", "true").lower() in {"1", "true", "yes"}
    if demo_auth:
        errors += 1
        lines.append(status_line("ERROR", "DEMO_AUTH_ENABLED should be false for production."))
    else:
        lines.append(status_line("OK", "DEMO_AUTH_ENABLED is false."))

    auth_secret = os.getenv("AUTH_TOKEN_SECRET", "")
    if not auth_secret or auth_secret == "replace-with-a-long-random-secret":
        errors += 1
        lines.append(status_line("ERROR", "AUTH_TOKEN_SECRET must be set to a production secret."))
    else:
        lines.append(status_line("OK", "AUTH_TOKEN_SECRET is configured."))

    export_dir = os.getenv("DOCUMENT_EXPORT_STORAGE_DIR")
    if export_dir:
        lines.append(status_line("OK", "DOCUMENT_EXPORT_STORAGE_DIR is configured."))
    else:
        lines.append(status_line("WARN", "DOCUMENT_EXPORT_STORAGE_DIR is not set; local default .local/document_exports will be used."))

    caps = pdf_capabilities()
    if caps.get("available"):
        lines.append(status_line("OK", f"PDF renderer available: {caps.get('engine')} {caps.get('engine_version') or ''}".strip()))
    else:
        lines.append(status_line("WARN", caps.get("diagnostic") or "PDF renderer is unavailable."))

    cors_origins = [origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
    if "*" in cors_origins:
        errors += 1
        lines.append(status_line("ERROR", "CORS_ALLOWED_ORIGINS must not include wildcard '*' in production."))
    elif any("localhost" in origin or "127.0.0.1" in origin for origin in cors_origins):
        lines.append(status_line("WARN", "CORS_ALLOWED_ORIGINS includes local development origins."))
    else:
        lines.append(status_line("OK", "CORS_ALLOWED_ORIGINS does not include wildcard or local origins."))

    smtp_refs = [value.strip() for value in os.getenv("SMTP_SECRET_REFS", "").split(",") if value.strip()]
    if smtp_refs:
        for secret_ref in smtp_refs:
            result = check_secret(secret_ref)
            level = "OK" if result.ok else "ERROR"
            if not result.ok:
                errors += 1
            lines.append(status_line(level, f"SMTP secret reference {mask_secret_ref(secret_ref)}: {result.diagnostic}"))
    else:
        lines.append(status_line("WARN", "SMTP_SECRET_REFS is not set; agency SMTP secret refs must be checked through stored agency settings."))

    lines.append(status_line("WARN", "Seed endpoint and demo headers are development tooling; do not expose them in production without administrative controls."))
    lines.append(status_line("INFO", "No SMTP secret values were printed."))

    for line in lines:
        print(line)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
