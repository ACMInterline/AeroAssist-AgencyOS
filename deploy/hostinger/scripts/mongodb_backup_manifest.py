#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASE_PATTERN = re.compile(r"^phase_\d+(?:_\d+)+_[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
COMMIT_PATTERN = re.compile(r"^(?:unknown|[0-9a-f]{7,40})$")
TIMESTAMP_PATTERN = re.compile(r"^\d{8}T\d{6}Z$")
FORBIDDEN_MANIFEST_KEYS = {"password", "token", "secret", "uri", "username"}


def artifact_paths(archive: Path) -> tuple[Path, Path]:
    suffix = ".archive.gz"
    if not archive.name.endswith(suffix):
        raise ValueError("MongoDB archive filename must end with .archive.gz")
    prefix = archive.name[: -len(suffix)]
    return archive.with_name(f"{archive.name}.sha256"), archive.with_name(f"{prefix}.manifest.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def load_counts(raw: str) -> dict[str, int]:
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError("Collection count metadata is not valid JSON") from exc
    if not isinstance(payload, dict) or any(
        not isinstance(key, str) or type(value) is not int or value < 0
        for key, value in payload.items()
    ):
        raise ValueError("Collection count metadata must be an object of non-negative integer counts")
    return dict(sorted(payload.items()))


def create_manifest(args: argparse.Namespace) -> int:
    archive = Path(args.archive).resolve()
    if not archive.is_file() or archive.stat().st_size <= 0:
        raise ValueError("Archive must exist and be non-empty")
    if not TIMESTAMP_PATTERN.fullmatch(args.timestamp):
        raise ValueError("Backup timestamp must use YYYYMMDDTHHMMSSZ format")
    if archive.name != f"mongodb-{args.timestamp}.archive.gz":
        raise ValueError("Archive filename must match the backup timestamp")
    if not PHASE_PATTERN.fullmatch(args.phase):
        raise ValueError("Build phase is not canonical")
    if not COMMIT_PATTERN.fullmatch(args.git_commit):
        raise ValueError("Git commit must be a hexadecimal revision or unknown")
    checksum_path, manifest_path = artifact_paths(archive)
    checksum = sha256_file(archive)
    counts = load_counts(args.collection_counts)
    checksum_path.write_text(f"{checksum}  {archive.name}\n", encoding="utf-8")
    os.chmod(checksum_path, 0o600)
    payload = {
        "schema_version": 1,
        "timestamp": args.timestamp,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "database_name": args.database,
        "archive_filename": archive.name,
        "archive_size_bytes": archive.stat().st_size,
        "sha256": checksum,
        "git_commit": args.git_commit,
        "current_build_phase": args.phase,
        "mongodb_version": args.mongodb_version.strip(),
        "backup_tool_version": args.tool_version.strip(),
        "environment_label": args.environment_label,
        "collection_count": len(counts),
        "document_count": sum(counts.values()),
        "collection_counts": counts,
        "document_export_backup_reference": args.document_export_reference or None,
        "verification_status": "checksum_verified",
        "verified_at": None,
        "restore_rehearsed_at": None,
    }
    write_json(manifest_path, payload)
    print(json.dumps({"archive": archive.name, "manifest": manifest_path.name, "status": "checksum_verified"}, sort_keys=True))
    return 0


def forbidden_keys(payload: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = key.lower()
            if any(part in lowered for part in FORBIDDEN_MANIFEST_KEYS):
                found.add(key)
            found.update(forbidden_keys(value))
    elif isinstance(payload, list):
        for value in payload:
            found.update(forbidden_keys(value))
    return found


def verify_manifest(archive: Path) -> tuple[dict[str, Any], Path]:
    archive = archive.resolve()
    checksum_path, manifest_path = artifact_paths(archive)
    if not archive.is_file() or archive.stat().st_size <= 0:
        raise ValueError("Archive is missing or empty")
    if not checksum_path.is_file() or not manifest_path.is_file():
        raise ValueError("Checksum or manifest is missing")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manifest root must be an object")
    forbidden = forbidden_keys(payload)
    if forbidden:
        raise ValueError("Manifest contains credential-like fields")
    expected_checksum = sha256_file(archive)
    checksum_parts = checksum_path.read_text(encoding="utf-8").strip().split()
    if len(checksum_parts) != 2 or checksum_parts[1] != archive.name:
        raise ValueError("Checksum file does not reference the archive basename")
    if checksum_parts[0] != expected_checksum or payload.get("sha256") != expected_checksum:
        raise ValueError("Archive checksum does not match")
    if payload.get("archive_filename") != archive.name:
        raise ValueError("Manifest references a different archive")
    timestamp = str(payload.get("timestamp") or "")
    if not TIMESTAMP_PATTERN.fullmatch(timestamp) or archive.name != f"mongodb-{timestamp}.archive.gz":
        raise ValueError("Manifest timestamp and archive filename are inconsistent")
    if payload.get("archive_size_bytes") != archive.stat().st_size:
        raise ValueError("Manifest archive size does not match")
    if not PHASE_PATTERN.fullmatch(str(payload.get("current_build_phase") or "")):
        raise ValueError("Manifest build phase is invalid")
    if not COMMIT_PATTERN.fullmatch(str(payload.get("git_commit") or "")):
        raise ValueError("Manifest Git revision is invalid")
    counts = payload.get("collection_counts") or {}
    if (
        not isinstance(counts, dict)
        or any(type(value) is not int or value < 0 for value in counts.values())
        or payload.get("collection_count") != len(counts)
        or payload.get("document_count") != sum(counts.values())
    ):
        raise ValueError("Manifest collection counts are inconsistent")
    if payload.get("verification_status") not in {"checksum_verified", "archive_inspected", "restore_rehearsed"}:
        raise ValueError("Manifest verification status is invalid")
    return payload, manifest_path


def verify_command(args: argparse.Namespace) -> int:
    archive = Path(args.archive)
    payload, manifest_path = verify_manifest(archive)
    print(
        json.dumps(
            {
                "archive": payload["archive_filename"],
                "manifest": manifest_path.name,
                "status": payload["verification_status"],
                "collection_count": payload["collection_count"],
                "document_count": payload["document_count"],
            },
            sort_keys=True,
        )
    )
    return 0


def mark_command(args: argparse.Namespace) -> int:
    archive = Path(args.archive)
    payload, manifest_path = verify_manifest(archive)
    now = datetime.now(timezone.utc).isoformat()
    if args.status == "archive_inspected":
        payload["verification_status"] = "archive_inspected"
        payload["verified_at"] = now
    else:
        payload["verification_status"] = "restore_rehearsed"
        payload["verified_at"] = payload.get("verified_at") or now
        payload["restore_rehearsed_at"] = now
    write_json(manifest_path, payload)
    print(json.dumps({"archive": payload["archive_filename"], "status": payload["verification_status"]}, sort_keys=True))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Create and verify credential-free MongoDB backup manifests.")
    subparsers = result.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--archive", required=True)
    create.add_argument("--timestamp", required=True)
    create.add_argument("--database", required=True)
    create.add_argument("--git-commit", required=True)
    create.add_argument("--phase", required=True)
    create.add_argument("--mongodb-version", required=True)
    create.add_argument("--tool-version", required=True)
    create.add_argument("--environment-label", required=True)
    create.add_argument("--collection-counts", default="{}")
    create.add_argument("--document-export-reference", default="")
    create.set_defaults(handler=create_manifest)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--archive", required=True)
    verify.set_defaults(handler=verify_command)
    mark = subparsers.add_parser("mark")
    mark.add_argument("--archive", required=True)
    mark.add_argument("--status", required=True, choices=("archive_inspected", "restore_rehearsed"))
    mark.set_defaults(handler=mark_command)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        return args.handler(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
