#!/usr/bin/env python3
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import get_settings, validate_config
from services.pdf_rendering_service import pdf_capabilities
from services.secret_service import check_secret, mask_secret_ref


def status_line(level: str, message: str) -> str:
    return f"{level}: {message}"


def main() -> int:
    settings = get_settings()
    config = validate_config(settings, include_storage=True)
    errors = config["failure_count"] if settings.is_production else 0

    lines: list[str] = [
        status_line("INFO", f"APP_ENV={settings.app_env}"),
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

    for line in lines:
        print(line)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
