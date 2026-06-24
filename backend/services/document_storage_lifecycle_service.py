from pathlib import Path
from typing import Any

from config import get_settings
from database import Database
from models import DocumentStorageRecord, now_utc
from services.file_storage_service import resolve_storage_key, storage_root


def _safe_record(record: dict) -> dict:
    blocked = {"file_path", "absolute_path", "local_path"}
    return {key: value for key, value in record.items() if key not in blocked}


def _status_for_export(export: dict) -> str:
    status_value = export.get("status")
    if status_value == "archived":
        return "archived"
    if status_value == "failed":
        return "failed"
    if status_value == "generated":
        return "active"
    return "failed"


def _file_exists(export: dict) -> bool | None:
    if export.get("storage_mode") != "file_path" or not export.get("storage_key"):
        return None
    try:
        return resolve_storage_key(export["storage_key"]).is_file()
    except Exception:
        return False


async def register_export_storage_record(db: Database, export: dict, document: dict | None = None, actor_user: dict | None = None) -> dict:
    existing = await db.collection("document_storage_records").find_one(
        {"agency_id": export["agency_id"], "related_entity_type": "document_export", "related_entity_id": export["id"]}
    )
    file_exists = _file_exists(export)
    storage_status = "missing" if file_exists is False and export.get("status") == "generated" else _status_for_export(export)
    record_payload = {
        "agency_id": export["agency_id"],
        "workspace_id": document.get("workspace_id") if document else None,
        "related_entity_type": "document_export",
        "related_entity_id": export["id"],
        "document_type": export.get("export_type") or document.get("document_type") if document else export.get("export_type"),
        "filename_original": export.get("filename"),
        "filename_stored": Path(export.get("storage_key") or export.get("filename") or "").name or None,
        "storage_key": export.get("storage_key"),
        "storage_backend": "local_filesystem" if export.get("storage_mode") == "file_path" else "local_filesystem",
        "storage_status": storage_status,
        "content_type": export.get("content_type"),
        "size_bytes": export.get("file_size_bytes"),
        "checksum_sha256": export.get("checksum_sha256"),
        "created_by_user_id": export.get("generated_by_user_id") or (actor_user or {}).get("id"),
        "created_by_email": (actor_user or {}).get("email"),
        "archived_at": export.get("archived_at"),
        "retention_until": export.get("retention_expires_at"),
        "delivery_allowed": False,
        "public_access_allowed": False,
        "audit_metadata": {
            "rendered_document_id": export.get("rendered_document_id"),
            "storage_mode": export.get("storage_mode"),
            "retention_policy": export.get("retention_policy"),
        },
    }
    if existing:
        updated = await db.collection("document_storage_records").update_one({"id": existing["id"]}, record_payload)
        return _safe_record(updated)
    created = await db.collection("document_storage_records").insert_one(DocumentStorageRecord(**record_payload).model_dump(mode="json"))
    return _safe_record(created)


async def ensure_storage_records_for_exports(db: Database, agency_id: str | None = None) -> list[dict]:
    filters = {"agency_id": agency_id} if agency_id else None
    records = []
    for export in await db.collection("document_exports").find_many(filters):
        document = await db.collection("rendered_documents").find_one(
            {"agency_id": export["agency_id"], "id": export.get("rendered_document_id")}
        )
        records.append(await register_export_storage_record(db, export, document))
    return records


async def list_storage_records(db: Database, filters: dict[str, Any] | None = None) -> list[dict]:
    await ensure_storage_records_for_exports(db, filters.get("agency_id") if filters else None)
    records = await db.collection("document_storage_records").find_many(filters)
    records.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
    return [_safe_record(record) for record in records]


async def storage_summary(db: Database, agency_id: str | None = None) -> dict:
    records = await list_storage_records(db, {"agency_id": agency_id} if agency_id else None)
    counts = {
        "total": len(records),
        "by_status": {},
        "by_backend": {},
        "by_document_type": {},
        "delivery_allowed": {"true": 0, "false": 0},
        "public_access_allowed": {"true": 0, "false": 0},
    }
    for record in records:
        for key, bucket in [
            ("storage_status", "by_status"),
            ("storage_backend", "by_backend"),
            ("document_type", "by_document_type"),
        ]:
            value = record.get(key) or "unknown"
            counts[bucket][value] = counts[bucket].get(value, 0) + 1
        counts["delivery_allowed"]["true" if record.get("delivery_allowed") else "false"] += 1
        counts["public_access_allowed"]["true" if record.get("public_access_allowed") else "false"] += 1
    return counts


async def storage_health(db: Database, agency_id: str | None = None) -> dict:
    settings = get_settings()
    configured = bool(settings.document_export_storage_dir)
    exists = False
    writable = False
    total_files = 0
    total_bytes = 0
    if configured:
        try:
            root = storage_root()
            exists = root.exists() and root.is_dir()
            probe = root / ".aeroassist-storage-health"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            writable = True
            for item in root.rglob("*"):
                if item.is_file():
                    total_files += 1
                    total_bytes += item.stat().st_size
        except OSError:
            writable = False
    records = await list_storage_records(db, {"agency_id": agency_id} if agency_id else None)
    missing_metadata_count = sum(1 for record in records if record.get("storage_status") == "missing")
    return {
        "configured": configured,
        "backend": "local_filesystem",
        "directory_exists": exists,
        "directory_writable": writable,
        "total_file_count": total_files,
        "total_bytes": total_bytes,
        "missing_metadata_count": missing_metadata_count,
        "orphan_file_count": None,
        "checked_at": now_utc(),
    }


async def archive_storage_record(db: Database, record_id: str, actor_user_id: str | None = None) -> dict | None:
    return await db.collection("document_storage_records").update_one(
        {"id": record_id},
        {"storage_status": "archived", "archived_at": now_utc(), "delivery_allowed": False, "public_access_allowed": False},
    )


async def mark_storage_record_missing(db: Database, record_id: str) -> dict | None:
    return await db.collection("document_storage_records").update_one(
        {"id": record_id},
        {"storage_status": "missing", "delivery_allowed": False, "public_access_allowed": False},
    )
