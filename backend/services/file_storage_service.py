import base64
import binascii
import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status

from config import get_settings


def storage_root() -> Path:
    root = get_settings().document_export_storage_dir
    root.mkdir(parents=True, exist_ok=True)
    return root


def safe_storage_segment(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value).strip("-") or "item"


def compute_checksum(data_bytes: bytes) -> str:
    return hashlib.sha256(data_bytes).hexdigest()


def resolve_storage_key(storage_key: str) -> Path:
    root = storage_root()
    candidate = (root / storage_key).resolve()
    if root not in candidate.parents and candidate != root:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export storage key is invalid.")
    return candidate


def save_export_bytes(agency_id: str, export_id: str, filename: str, content_type: str, data_bytes: bytes) -> dict:
    extension = Path(filename).suffix or ".bin"
    agency_segment = safe_storage_segment(agency_id)
    export_segment = safe_storage_segment(export_id)
    storage_key = f"{agency_segment}/{export_segment}/{uuid4().hex}{extension}"
    target = resolve_storage_key(storage_key)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data_bytes)
    return {
        "storage_mode": "file_path",
        "storage_key": storage_key,
        "storage_bucket": "local",
        "file_path": str(target),
        "file_size_bytes": len(data_bytes),
        "checksum_sha256": compute_checksum(data_bytes),
        "content_type": content_type,
    }


def get_export_bytes(export_record: dict) -> bytes:
    storage_mode = export_record.get("storage_mode")
    if storage_mode == "file_path":
        storage_key = export_record.get("storage_key")
        if not storage_key:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export storage key is missing.")
        path = resolve_storage_key(storage_key)
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export file is not available.")
        data = path.read_bytes()
    elif storage_mode == "inline_base64":
        raw = export_record.get("file_data_base64")
        if not raw:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export file is not available.")
        try:
            data = base64.b64decode(raw.encode("ascii"), validate=True)
        except (binascii.Error, UnicodeEncodeError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export file data is invalid.")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export file is not available.")

    checksum = export_record.get("checksum_sha256")
    if checksum and compute_checksum(data) != checksum:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export file checksum verification failed.")
    expected_size = export_record.get("file_size_bytes")
    if expected_size is not None and len(data) != int(expected_size):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export file size verification failed.")
    return data


def delete_or_archive_export(export_record: dict) -> None:
    if export_record.get("storage_mode") != "file_path" or not export_record.get("storage_key"):
        return
    path = resolve_storage_key(export_record["storage_key"])
    if path.exists() and path.is_file():
        path.unlink()
