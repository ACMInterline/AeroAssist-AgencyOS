from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import require_platform_role
from database import Database, get_database
from models import ServiceCatalogueCreate, ServiceCatalogueReorderRequest, ServiceCatalogueUpdate
from services.reference_data_service import audit_reference_event
from services.service_catalogue_service import (
    insert_service_catalogue_record,
    normalize_service_catalogue_payload,
    normalize_service_key,
    safe_service_catalogue_record,
    update_service_catalogue_record,
)


router = APIRouter(prefix="/api/platform/service-catalogue", tags=["platform-service-catalogue"])

PlatformServiceCatalogueOwner = Depends(require_platform_role(["platform_owner", "platform_admin"]))


def matches_query(record: dict[str, Any], query: str) -> bool:
    if not query:
        return True
    needle = query.lower()
    safe = safe_service_catalogue_record(record)
    haystack = [
        safe.get("service_key"),
        safe.get("service_code"),
        safe.get("label"),
        safe.get("service_label"),
        safe.get("category"),
        safe.get("rules_category"),
        safe.get("ssr_code"),
    ]
    return any(needle in str(value or "").lower() for value in haystack)


def matches_status(record: dict[str, Any], status_filter: str | None) -> bool:
    if not status_filter:
        return True
    safe = safe_service_catalogue_record(record)
    return safe.get("status") == status_filter


async def get_service_or_404(db: Database, service_id: str) -> dict[str, Any]:
    service = await db.collection("service_catalogue").find_one({"id": service_id})
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service catalogue record not found.")
    return service


@router.get("")
async def list_platform_service_catalogue(
    q: str = Query(default=""),
    status_filter: str | None = Query(default=None, alias="status"),
    include_archived: bool = Query(default=True),
    user: dict = PlatformServiceCatalogueOwner,
    db: Database = Depends(get_database),
) -> dict:
    records = await db.collection("service_catalogue").find_many()
    items = [
        safe_service_catalogue_record(record)
        for record in records
        if matches_query(record, q)
        and matches_status(record, status_filter)
        and (include_archived or safe_service_catalogue_record(record).get("status") != "archived")
    ]
    return {
        "items": sorted(items, key=lambda item: (item.get("sort_order", 100), item.get("label") or "")),
        "actor_user_id": user["id"],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_service_catalogue_record(
    payload: ServiceCatalogueCreate,
    user: dict = PlatformServiceCatalogueOwner,
    db: Database = Depends(get_database),
) -> dict:
    payload_dict = normalize_service_catalogue_payload(payload.model_dump(mode="json"), user["id"])
    key = normalize_service_key(payload_dict.get("service_key"))
    existing = await db.collection("service_catalogue").find_one({"service_code": key})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service catalogue record already exists.")
    created = await insert_service_catalogue_record(db, payload_dict, user["id"])
    await audit_reference_event(
        db,
        "platform_service_catalogue_created",
        "service_catalogue",
        created["id"],
        f"Service catalogue record {key} created.",
        user["id"],
        {"service_key": key},
    )
    return {"service": safe_service_catalogue_record(created), "actor_user_id": user["id"]}


@router.get("/{service_id}")
async def get_platform_service_catalogue_record(
    service_id: str,
    user: dict = PlatformServiceCatalogueOwner,
    db: Database = Depends(get_database),
) -> dict:
    service = await get_service_or_404(db, service_id)
    return {"service": safe_service_catalogue_record(service), "actor_user_id": user["id"]}


@router.put("/{service_id}")
async def update_platform_service_catalogue_record(
    service_id: str,
    payload: ServiceCatalogueUpdate,
    user: dict = PlatformServiceCatalogueOwner,
    db: Database = Depends(get_database),
) -> dict:
    existing = await get_service_or_404(db, service_id)
    updates = {
        key: value
        for key, value in payload.model_dump(mode="json", exclude_unset=True).items()
        if value is not None
    }
    key = normalize_service_key(updates.get("service_key") or updates.get("service_code") or existing.get("service_key") or existing.get("service_code"))
    conflict = await db.collection("service_catalogue").find_one({"service_code": key})
    if conflict and conflict["id"] != service_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service catalogue key conflicts with another record.")
    updated = await update_service_catalogue_record(db, existing, updates, user["id"])
    await audit_reference_event(
        db,
        "platform_service_catalogue_updated",
        "service_catalogue",
        service_id,
        f"Service catalogue record {key} updated.",
        user["id"],
        {"service_key": key},
    )
    return {"service": safe_service_catalogue_record(updated), "actor_user_id": user["id"]}


@router.post("/{service_id}/archive")
async def archive_platform_service_catalogue_record(
    service_id: str,
    user: dict = PlatformServiceCatalogueOwner,
    db: Database = Depends(get_database),
) -> dict:
    existing = await get_service_or_404(db, service_id)
    updated = await update_service_catalogue_record(
        db,
        existing,
        {"status": "archived", "active": False, "is_active": False},
        user["id"],
    )
    await audit_reference_event(
        db,
        "platform_service_catalogue_archived",
        "service_catalogue",
        service_id,
        "Service catalogue record archived.",
        user["id"],
        {"service_key": normalize_service_key(existing.get("service_key") or existing.get("service_code"))},
    )
    return {"service": safe_service_catalogue_record(updated), "actor_user_id": user["id"]}


@router.post("/reorder")
async def reorder_platform_service_catalogue(
    payload: ServiceCatalogueReorderRequest,
    user: dict = PlatformServiceCatalogueOwner,
    db: Database = Depends(get_database),
) -> dict:
    updated = []
    for index, service_id in enumerate(payload.ordered_ids, start=1):
        service = await db.collection("service_catalogue").find_one({"id": service_id})
        if not service:
            continue
        result = await db.collection("service_catalogue").update_one(
            {"id": service_id},
            {"sort_order": index * 10, "updated_by_user_id": user["id"]},
        )
        if result:
            updated.append(safe_service_catalogue_record(result))
    await audit_reference_event(
        db,
        "platform_service_catalogue_reordered",
        "service_catalogue",
        "service_catalogue",
        "Service catalogue records reordered.",
        user["id"],
        {"count": len(updated)},
    )
    return {"items": updated, "actor_user_id": user["id"]}
