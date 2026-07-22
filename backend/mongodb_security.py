from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit, urlunsplit

from config import AppSettings


def redact_mongodb_uri(value: str) -> str:
    if not value:
        return ""
    parsed = urlsplit(value)
    hostname = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    return urlunsplit((parsed.scheme, f"[credentials-redacted]@{hostname}{port}", parsed.path, parsed.query, ""))


def mongodb_security_readiness_metadata(settings: AppSettings) -> dict[str, Any]:
    return {
        "mongodb_authentication_supported": True,
        "mongodb_authentication_configured": settings.mongodb_authentication_enabled,
        "unauthenticated_production_fallback_disabled": True,
        "mongodb_internal_network_only": True,
        "backup_tooling_enabled": True,
        "checksum_verification_enabled": True,
        "manifest_verification_enabled": True,
        "retention_controls_enabled": True,
        "dry_run_restore_enabled": True,
        "disposable_restore_rehearsal_enabled": True,
        "disposable_restore_nofile_governed": True,
        "disposable_restore_nofile_minimum": 64000,
        "automatic_production_restore_disabled": True,
        "credential_redaction_enabled": True,
        "existing_volume_migration_documented": True,
        "document_storage_backup_documented": True,
        "scheduler_examples_documented": True,
        "production_secrets_exposed": False,
        "readiness_required": False,
        "diagnostic": (
            "Phase 56.5.5 provides authenticated MongoDB configuration, checksummed manifests, "
            "retention guards, dry-run restore planning, and disposable restore rehearsals. "
            "It never restores production automatically and exposes no credential values."
        ),
    }
