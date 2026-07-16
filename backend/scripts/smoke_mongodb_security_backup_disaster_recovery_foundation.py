#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from contextlib import contextmanager
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
SCRIPTS = ROOT / "deploy" / "hostinger" / "scripts"
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE
from config import get_settings, validate_config
from mongodb_security import mongodb_security_readiness_metadata, redact_mongodb_uri
from phase_assertions import assert_application_phase_at_least
from smoke_booking_pnr_foundation import BASE_URL


RELEASE_PHASE = "phase_56_5_5_mongodb_security_backup_disaster_recovery_foundation"
MINIMUM_PHASE = RELEASE_PHASE
REQUIRED_SCRIPTS = (
    "backup_mongo.sh",
    "verify_mongodb_backup.sh",
    "restore_mongodb_backup.sh",
    "test_restore_mongodb_backup.sh",
    "prune_backups.sh",
)


@contextmanager
def environment(overrides: dict[str, str]):
    original = os.environ.copy()
    os.environ.update(overrides)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(original)


def run(command: list[str], *, env: dict[str, str] | None = None, expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        env={**os.environ, **(env or {})},
        text=True,
        capture_output=True,
        check=False,
    )
    if expect_success and result.returncode != 0:
        raise AssertionError(f"Command failed: {' '.join(command)}\n{result.stdout}\n{result.stderr}")
    if not expect_success and result.returncode == 0:
        raise AssertionError(f"Unsafe command unexpectedly succeeded: {' '.join(command)}")
    return result


def verify_config() -> None:
    secure_env = {
        "APP_ENV": "production",
        "AEROASSIST_DB_MODE": "mongo",
        "MONGO_AUTHENTICATION_ENABLED": "true",
        "MONGO_INITDB_ROOT_USERNAME": "ci_root",
        "MONGO_INITDB_ROOT_PASSWORD": "6af42f8d495b4deab19c3eaa",
        "MONGO_APP_USERNAME": "ci_app",
        "MONGO_APP_PASSWORD": "b6523a376c5a4ebfab483945",
        "MONGO_AUTH_SOURCE": "admin",
        "MONGO_DATABASE": "aeroassist_ci",
        "MONGO_HOST": "mongo",
        "MONGO_PORT": "27017",
        "MONGODB_URL": "",
        "BACKUP_ROOT": "/tmp/aeroassist-ci-backups",
        "BACKUP_RETENTION_DAYS": "30",
        "BACKUP_MINIMUM_COUNT": "2",
        "BACKUP_ENVIRONMENT_LABEL": "ci",
        "DEMO_AUTH_ENABLED": "false",
        "SEED_ON_STARTUP": "false",
        "SEED_ENDPOINT_ENABLED": "false",
        "AUTH_TOKEN_SECRET": "f9281de513c24c3ca3e2161a7e02a1fe",
        "DOCUMENT_EXPORT_STORAGE_DIR": "/tmp/aeroassist-ci-documents",
        "CORS_ALLOWED_ORIGINS": "https://ci.example.test",
        "SECURITY_HEADERS_ENABLED": "true",
        "SECURITY_HSTS_ENABLED": "true",
        "READINESS_PUBLIC_MODE": "summary",
        "READINESS_INTERNAL_ENABLED": "false",
    }
    with environment(secure_env):
        settings = get_settings()
        validation = validate_config(settings, include_storage=False)
        if not validation["ok"] or not settings.mongodb_url.startswith("mongodb://ci_app:"):
            raise AssertionError(f"Authenticated production configuration was rejected: {validation}")
        if "b6523a" in json.dumps(validation):
            raise AssertionError("Configuration diagnostics exposed a MongoDB credential.")
        if "b6523a" in repr(settings) or "f9281d" in repr(settings):
            raise AssertionError("Application settings representation exposed a credential.")
        redacted = redact_mongodb_uri(settings.mongodb_url)
        if "ci_app" in redacted or "b6523a" in redacted or "[credentials-redacted]" not in redacted:
            raise AssertionError("MongoDB URI redaction did not remove credentials.")
    with environment({**secure_env, "MONGO_INITDB_ROOT_USERNAME": "", "MONGO_INITDB_ROOT_PASSWORD": ""}):
        if not validate_config(get_settings(), include_storage=False)["ok"]:
            raise AssertionError("Application runtime incorrectly requires administrative MongoDB credentials.")
    with environment({**secure_env, "MONGO_APP_PASSWORD": "replace-with-a-long-random-mongodb-app-password"}):
        if validate_config(get_settings(), include_storage=False)["ok"]:
            raise AssertionError("Placeholder production MongoDB credentials were accepted.")


def verify_compose_and_scripts() -> None:
    compose = (ROOT / "docker-compose.production.yml").read_text(encoding="utf-8")
    mongo_block = compose.split("  mongo:\n", 1)[1].split("\n  backend:\n", 1)[0]
    if re.search(r"^    ports:", mongo_block, re.MULTILINE):
        raise AssertionError("Production MongoDB publishes a host port.")
    for token in (
        "mongo_data:/data/db",
        "MONGO_INITDB_ROOT_USERNAME",
        "MONGO_APP_USERNAME",
        "MONGO_AUTH_SOURCE",
        "init-application-user.sh",
    ):
        if token not in mongo_block:
            raise AssertionError(f"Production MongoDB Compose support is missing {token!r}.")
    backend_block = compose.split("  backend:\n", 1)[1].split("\n  frontend:\n", 1)[0]
    for token in ('MONGO_INITDB_ROOT_USERNAME: ""', 'MONGO_INITDB_ROOT_PASSWORD: ""'):
        if token not in backend_block:
            raise AssertionError("Production backend does not mask MongoDB administrative credentials.")

    for name in REQUIRED_SCRIPTS:
        path = SCRIPTS / name
        text = path.read_text(encoding="utf-8")
        if not path.is_file() or "set -euo pipefail" not in text:
            raise AssertionError(f"Backup tooling is missing strict mode: {name}")
        run(["bash", "-n", str(path)])
    backup_text = (SCRIPTS / "backup_mongo.sh").read_text(encoding="utf-8")
    if not all(token in backup_text for token in ("mongodump", "mongodb-$TIMESTAMP.archive.gz", "mongodb_backup_manifest.py")):
        raise AssertionError("Backup tooling is missing timestamp, manifest, or mongodump behavior.")
    restore_text = (SCRIPTS / "restore_mongodb_backup.sh").read_text(encoding="utf-8")
    if not all(token in restore_text for token in ("DRY_RUN", "ALLOW_PRODUCTION_RESTORE", "PRODUCTION_RESTORE_CONFIRMATION", "--confirm-target")):
        raise AssertionError("Restore tooling is missing dry-run or multi-part production guards.")
    rehearsal_text = (SCRIPTS / "test_restore_mongodb_backup.sh").read_text(encoding="utf-8")
    if not all(token in rehearsal_text for token in ("ALLOW_DESTRUCTIVE_TEST_RESTORE", "RESTORE_TARGET_ENV", "docker volume", "collection_counts")):
        raise AssertionError("Disposable restore rehearsal guards are incomplete.")
    deploy_text = (SCRIPTS / "deploy.sh").read_text(encoding="utf-8")
    systemd_text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "deploy/hostinger/systemd").glob("*"))
    if "restore_mongodb_backup.sh" in deploy_text or "restore_mongodb_backup.sh" in systemd_text:
        raise AssertionError("Production restore was wired into deployment or scheduling.")


def create_test_manifest(directory: Path, stamp: str, status: str = "archive_inspected") -> Path:
    backup_dir = directory / stamp
    backup_dir.mkdir(parents=True)
    archive = backup_dir / f"mongodb-{stamp}.archive.gz"
    archive.write_bytes(f"disposable archive {stamp}".encode())
    run(
        [
            "python3", str(SCRIPTS / "mongodb_backup_manifest.py"), "create",
            "--archive", str(archive), "--timestamp", stamp,
            "--database", "aeroassist_source", "--git-commit", "unknown",
            "--phase", RELEASE_PHASE, "--mongodb-version", "test",
            "--tool-version", "test", "--environment-label", "test",
            "--collection-counts", '{"records": 2}',
        ]
    )
    run(["python3", str(SCRIPTS / "mongodb_backup_manifest.py"), "mark", "--archive", str(archive), "--status", status])
    return archive


def verify_manifest_retention_and_restore_guards() -> None:
    with tempfile.TemporaryDirectory(prefix="aeroassist-mongodb-smoke-") as temporary:
        root = Path(temporary)
        archives = [create_test_manifest(root, stamp) for stamp in ("20200101T000000Z", "20200102T000000Z", "20200103T000000Z")]
        verified = run(["python3", str(SCRIPTS / "mongodb_backup_manifest.py"), "verify", "--archive", str(archives[-1])])
        if '"document_count": 2' not in verified.stdout:
            raise AssertionError("Manifest verification did not preserve count metadata.")
        manifest_text = archives[-1].with_name(archives[-1].name.removesuffix(".archive.gz") + ".manifest.json").read_text(encoding="utf-8").lower()
        if any(token in manifest_text for token in ("password", "mongodb://", "token", "secret")):
            raise AssertionError("Backup manifest contains credential-like content.")

        retention = run(
            [str(SCRIPTS / "prune_backups.sh")],
            env={"BACKUP_ROOT": str(root), "BACKUP_ALLOW_TEST_ROOT": "true", "BACKUP_RETENTION_DAYS": "1", "BACKUP_MINIMUM_COUNT": "2"},
        )
        if "WOULD DELETE VERIFIED SET: 20200101T000000Z" not in retention.stdout or not all(path.exists() for path in archives):
            raise AssertionError(f"Retention dry-run did not protect files or minimum count: {retention.stdout}")

        env_file = root / "test.env"
        env_file.write_text(
            "APP_ENV=test\nMONGO_DATABASE=aeroassist_source\nMONGODB_DATABASE=aeroassist_source\n",
            encoding="utf-8",
        )
        production_env_file = root / "production.env"
        production_env_file.write_text(
            "APP_ENV=production\nMONGO_DATABASE=aeroassist_source\nMONGODB_DATABASE=aeroassist_source\n",
            encoding="utf-8",
        )
        dry_run = run(
            [str(SCRIPTS / "restore_mongodb_backup.sh"), "--archive", str(archives[-1]), "--target-database", "aeroassist_restore_preview"],
            env={"APP_DIR": str(ROOT), "ENV_FILE": str(env_file), "BACKUP_ROOT": str(root)},
        )
        if "validation-only" not in dry_run.stdout:
            raise AssertionError("Restore did not default to validation-only mode.")
        production_refusal = run(
            [str(SCRIPTS / "restore_mongodb_backup.sh"), "--archive", str(archives[-1]), "--target-database", "aeroassist_source", "--execute"],
            env={"APP_DIR": str(ROOT), "ENV_FILE": str(production_env_file), "BACKUP_ROOT": str(root), "RESTORE_TARGET_ENV": "production"},
            expect_success=False,
        )
        if "production restore is disabled" not in production_refusal.stderr:
            raise AssertionError("Production restore refusal did not reach the explicit authorization guard.")
        cluster_refusal = run(
            [str(SCRIPTS / "restore_mongodb_backup.sh"), "--archive", str(archives[-1]), "--target-database", "aeroassist_candidate", "--execute"],
            env={
                "APP_DIR": str(ROOT),
                "ENV_FILE": str(production_env_file),
                "BACKUP_ROOT": str(root),
                "RESTORE_TARGET_ENV": "test",
                "ALLOW_DESTRUCTIVE_TEST_RESTORE": "true",
            },
            expect_success=False,
        )
        if "production-configured MongoDB cluster" not in cluster_refusal.stderr:
            raise AssertionError("A test guard was accepted for a production-configured MongoDB cluster.")


def verify_readiness(static_only: bool) -> None:
    section = mongodb_security_readiness_metadata(get_settings())
    required_true = (
        "mongodb_authentication_supported",
        "unauthenticated_production_fallback_disabled",
        "mongodb_internal_network_only",
        "backup_tooling_enabled",
        "checksum_verification_enabled",
        "manifest_verification_enabled",
        "retention_controls_enabled",
        "dry_run_restore_enabled",
        "disposable_restore_rehearsal_enabled",
        "automatic_production_restore_disabled",
        "credential_redaction_enabled",
        "existing_volume_migration_documented",
        "document_storage_backup_documented",
        "scheduler_examples_documented",
    )
    if any(section.get(key) is not True for key in required_true) or section.get("production_secrets_exposed") is not False:
        raise AssertionError(f"MongoDB readiness metadata is incomplete: {section}")
    server_text = (BACKEND / "server.py").read_text(encoding="utf-8")
    if '"mongodb_security_backup_disaster_recovery_foundation"' not in server_text:
        raise AssertionError("Server readiness does not register Phase 56.5.5.")
    if static_only:
        return
    with urllib.request.urlopen(f"{BASE_URL}/api/readiness", timeout=30) as response:
        payload = json.load(response)
    assert_application_phase_at_least(payload.get("phase"), MINIMUM_PHASE, source="readiness")
    if (payload.get("mongodb_security_backup_disaster_recovery_foundation") or {}).get("production_secrets_exposed") is not False:
        raise AssertionError("Public readiness omitted or exposed unsafe MongoDB metadata.")


def verify_docs_and_secret_hygiene() -> None:
    required_docs = (
        ROOT / "docs/architecture/mongodb-security-backup-disaster-recovery-foundation.md",
        ROOT / "deploy/hostinger/MONGODB_DISASTER_RECOVERY_RUNBOOK.md",
    )
    if any(not path.is_file() for path in required_docs):
        raise AssertionError("MongoDB architecture or disaster-recovery runbook is missing.")
    example = (ROOT / ".env.production.example").read_text(encoding="utf-8")
    if "replace-with-a-long-random-mongodb-root-password" not in example or "replace-with-a-long-random-mongodb-app-password" not in example:
        raise AssertionError("Production example does not use explicit credential placeholders.")
    if re.search(r"mongodb://[^\s:]+:[^\s@]+@", example):
        raise AssertionError("Production example commits an authenticated MongoDB URI.")
    if "\n.env\n" not in "\n" + (ROOT / ".gitignore").read_text(encoding="utf-8"):
        raise AssertionError(".env is not ignored.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--static", action="store_true")
    args = parser.parse_args()
    assert_application_phase_at_least(CURRENT_BUILD_PHASE, MINIMUM_PHASE, source="canonical build phase")
    verify_config()
    verify_compose_and_scripts()
    verify_manifest_retention_and_restore_guards()
    verify_readiness(args.static)
    verify_docs_and_secret_hygiene()
    print("Phase 56.5.5 MongoDB security, backup, and disaster recovery foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
