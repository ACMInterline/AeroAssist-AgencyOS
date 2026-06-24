from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user, require_platform_role
from config import get_settings
from database import Database, get_database
from models import GlobalReferenceCreate, GlobalReferenceRecord, GlobalReferenceUpdate
from services.reference_data_service import (
    REFERENCE_DOMAINS,
    SERVICE_FAMILIES,
    audit_reference_event,
    bootstrap_reference_data,
    normalize_reference_code,
    safe_reference_record,
    sort_records,
)
from services.seed_service import seed_core_data

router = APIRouter(prefix="/api/reference", tags=["reference"])


def ensure_domain(domain: str) -> None:
    if domain not in REFERENCE_DOMAINS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported reference domain: {domain}")


def filter_active(records: list[dict[str, Any]], include_inactive: bool) -> list[dict[str, Any]]:
    return records if include_inactive else [record for record in records if record.get("is_active", True)]


def matches_query(record: dict[str, Any], query: str) -> bool:
    needle = query.strip().lower()
    if not needle:
        return True
    haystack = [
        record.get("code"),
        record.get("key"),
        record.get("label"),
        record.get("description"),
        *(record.get("aliases") or []),
    ]
    return any(needle in str(value).lower() for value in haystack if value)


def matches_service_query(record: dict[str, Any], query: str) -> bool:
    needle = query.strip().lower()
    if not needle:
        return True
    haystack = [
        record.get("service_code"),
        record.get("service_label"),
        record.get("service_family_code"),
        record.get("default_ssr_code"),
    ]
    return any(needle in str(value).lower() for value in haystack if value)


async def require_reference_manager(user: dict, payload_scope: str | None = None) -> None:
    if payload_scope == "agency":
        if user.get("global_role") in {"platform_owner", "platform_admin"}:
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agency-scoped reference overrides are reserved for a future agency settings phase.")
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform owner or admin role is required.")


@router.get("/domains")
async def list_reference_domains(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    records = await db.collection("global_reference_records").find_many()
    active_records = [safe_reference_record(record) for record in records if record.get("is_active", True)]
    domain_counts = {
        domain: len([record for record in active_records if record.get("domain") == domain])
        for domain in REFERENCE_DOMAINS
    }
    return {
        "domains": [
            {
                "domain": domain,
                "label": label,
                "active_record_count": domain_counts.get(domain, 0),
            }
            for domain, label in REFERENCE_DOMAINS.items()
        ],
        "service_catalogue": {
            "domain": "service_catalogue",
            "label": "Service catalogue",
            "active_record_count": await db.collection("service_catalogue").count({"is_active": True}),
        },
        "actor_user_id": user["id"],
    }


@router.get("/service-catalogue/families")
async def list_service_catalogue_families(user: dict = Depends(get_current_user)) -> dict:
    return {"families": SERVICE_FAMILIES, "actor_user_id": user["id"]}


@router.get("/service-catalogue/search")
async def search_service_catalogue(
    q: str = Query(default=""),
    include_inactive: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    records = filter_active(await db.collection("service_catalogue").find_many(), include_inactive)
    items = [record for record in records if matches_service_query(record, q)]
    return {"items": sort_records(items, "service_code", "service_label"), "query": q, "actor_user_id": user["id"]}


@router.get("/service-catalogue")
async def list_service_catalogue(
    include_inactive: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    records = filter_active(await db.collection("service_catalogue").find_many(), include_inactive)
    grouped = []
    for family in SERVICE_FAMILIES:
        family_records = [record for record in records if record.get("service_family_code") == family["code"]]
        grouped.append({**family, "items": sort_records(family_records, "service_code", "service_label")})
    return {
        "items": sort_records(records, "service_code", "service_label"),
        "families": grouped,
        "actor_user_id": user["id"],
    }


@router.post("/bootstrap")
async def bootstrap_reference_catalogue(
    user: dict = Depends(require_platform_role(["platform_owner", "platform_admin"])),
    db: Database = Depends(get_database),
) -> dict:
    result = await bootstrap_reference_data(db, user["id"])
    await audit_reference_event(
        db,
        "reference_data.bootstrap",
        "reference_data",
        "phase_33_bootstrap",
        "Reference data and service catalogue bootstrap executed.",
        user["id"],
        result,
    )
    return {"ok": True, "bootstrap": result, "actor_user_id": user["id"]}


@router.post("/seed")
async def seed_reference(
    user: dict = Depends(require_platform_role(["platform_owner", "platform_admin"])),
    db: Database = Depends(get_database),
) -> dict:
    if not get_settings().seed_endpoint_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seed endpoint is disabled.")
    result = await seed_core_data(db)
    reference_result = await bootstrap_reference_data(db, user["id"])
    return {"ok": True, "seed": result, "reference_bootstrap": reference_result, "actor_user_id": user["id"]}


@router.get("/{domain}/search")
async def search_reference_domain(
    domain: str,
    q: str = Query(default=""),
    include_inactive: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    ensure_domain(domain)
    records = [safe_reference_record(record) for record in await db.collection("global_reference_records").find_many({"domain": domain})]
    items = [record for record in filter_active(records, include_inactive) if matches_query(record, q)]
    return {"domain": domain, "items": sort_records(items), "query": q, "actor_user_id": user["id"]}


@router.get("/{domain}")
async def list_reference_domain(
    domain: str,
    include_inactive: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    ensure_domain(domain)
    records = [safe_reference_record(record) for record in await db.collection("global_reference_records").find_many({"domain": domain})]
    return {
        "domain": domain,
        "label": REFERENCE_DOMAINS[domain],
        "items": sort_records(filter_active(records, include_inactive)),
        "actor_user_id": user["id"],
    }


@router.get("")
async def list_reference(
    include_inactive: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    records = [safe_reference_record(record) for record in await db.collection("global_reference_records").find_many()]
    return {"items": sort_records(filter_active(records, include_inactive)), "actor_user_id": user["id"]}


@router.post("/{domain}", status_code=status.HTTP_201_CREATED)
async def create_reference_record_for_domain(
    domain: str,
    payload: GlobalReferenceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    ensure_domain(domain)
    await require_reference_manager(user, payload.scope.value if hasattr(payload.scope, "value") else payload.scope)
    code = normalize_reference_code(payload.code or payload.key or "")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reference code is required.")
    existing = await db.collection("global_reference_records").find_one({"domain": domain, "key": code})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reference record already exists.")
    payload_dict = payload.model_dump(mode="json")
    metadata_json = payload_dict.get("metadata_json") or payload_dict.get("metadata") or {}
    record = GlobalReferenceRecord(
        **{
            **payload_dict,
            "domain": domain,
            "code": code,
            "key": code,
            "metadata_json": metadata_json,
            "metadata": metadata_json,
            "created_by_user_id": user["id"],
            "updated_by_user_id": user["id"],
        }
    )
    created = await db.collection("global_reference_records").insert_one(record.model_dump(mode="json"))
    await audit_reference_event(db, "reference_data.created", "global_reference_record", created["id"], f"Reference record {domain}:{code} created.", user["id"], {"domain": domain, "code": code})
    return {"record": safe_reference_record(created), "created": True, "actor_user_id": user["id"]}


@router.post("")
async def create_reference_record(
    payload: GlobalReferenceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    if not payload.domain:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reference domain is required.")
    return await create_reference_record_for_domain(payload.domain, payload, user, db)


@router.put("/{domain}/{record_id}")
async def update_reference_record(
    domain: str,
    record_id: str,
    payload: GlobalReferenceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    ensure_domain(domain)
    existing = await db.collection("global_reference_records").find_one({"domain": domain, "id": record_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference record not found.")
    await require_reference_manager(user, payload.scope.value if payload.scope and hasattr(payload.scope, "value") else payload.scope)
    updates = {key: value for key, value in payload.model_dump(mode="json", exclude_unset=True).items() if value is not None}
    if "code" in updates or "key" in updates:
        code = normalize_reference_code(updates.get("code") or updates.get("key") or "")
        if not code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reference code cannot be blank.")
        conflict = await db.collection("global_reference_records").find_one({"domain": domain, "key": code})
        if conflict and conflict["id"] != record_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reference code already exists.")
        updates["code"] = code
        updates["key"] = code
    if "metadata_json" in updates:
        updates["metadata"] = updates["metadata_json"]
    updates["updated_by_user_id"] = user["id"]
    updated = await db.collection("global_reference_records").update_one({"id": record_id}, updates)
    await audit_reference_event(db, "reference_data.updated", "global_reference_record", record_id, f"Reference record {domain}:{record_id} updated.", user["id"], {"domain": domain})
    return {"record": safe_reference_record(updated), "actor_user_id": user["id"]}


@router.patch("/{domain}/{record_id}/activate")
async def activate_reference_record(
    domain: str,
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    ensure_domain(domain)
    await require_reference_manager(user)
    updated = await db.collection("global_reference_records").update_one({"domain": domain, "id": record_id}, {"is_active": True, "updated_by_user_id": user["id"]})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference record not found.")
    await audit_reference_event(db, "reference_data.activated", "global_reference_record", record_id, f"Reference record {domain}:{record_id} activated.", user["id"], {"domain": domain})
    return {"record": safe_reference_record(updated), "actor_user_id": user["id"]}


@router.patch("/{domain}/{record_id}/deactivate")
async def deactivate_reference_record(
    domain: str,
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    ensure_domain(domain)
    await require_reference_manager(user)
    updated = await db.collection("global_reference_records").update_one({"domain": domain, "id": record_id}, {"is_active": False, "updated_by_user_id": user["id"]})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference record not found.")
    await audit_reference_event(db, "reference_data.deactivated", "global_reference_record", record_id, f"Reference record {domain}:{record_id} deactivated.", user["id"], {"domain": domain})
    return {"record": safe_reference_record(updated), "actor_user_id": user["id"]}
