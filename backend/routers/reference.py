from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user, require_platform_role
from config import get_settings
from database import Database, get_database
from models import (
    GlobalReferenceCreate,
    GlobalReferenceRecord,
    GlobalReferenceUpdate,
    ReferenceDataSuggestion,
    ReferenceDataSuggestionCreate,
    ReferenceImportBatchCreate,
    ReferenceSuggestionReview,
    now_utc,
)
from services.reference_data_service import (
    REFERENCE_DOMAINS,
    SERVICE_FAMILIES,
    audit_reference_event,
    bootstrap_reference_data,
    create_reference_import_batch,
    normalize_city_reference_code,
    normalize_city_reference_metadata,
    normalize_reference_code,
    normalize_reference_metadata_for_domain,
    safe_reference_import_batch,
    safe_reference_record,
    safe_reference_suggestion,
    sort_records,
)
from services.seed_service import seed_core_data
from services.tenant_service import assert_agency_access

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


def normalize_metadata_or_raise(domain: str, metadata: dict[str, Any] | None) -> dict[str, Any]:
    normalized, errors = normalize_reference_metadata_for_domain(domain, metadata or {})
    if errors:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors)
    return normalized


def normalize_record_metadata_or_raise(domain: str, code: str, label: str, aliases: list[str] | None, metadata: dict[str, Any] | None) -> dict[str, Any]:
    if domain == "cities":
        normalized, errors = normalize_city_reference_metadata(code, label, aliases or [], metadata or {})
        if errors:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors)
        return normalized
    return normalize_metadata_or_raise(domain, metadata)


async def require_reference_manager(user: dict, payload_scope: str | None = None) -> None:
    if payload_scope == "agency":
        if user.get("global_role") in {"platform_owner", "platform_admin"}:
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agency-scoped reference overrides are reserved for a future agency settings phase.")
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform owner or admin role is required.")


def is_platform_owner(user: dict) -> bool:
    return user.get("global_role") in {"platform_owner", "platform_admin"}


async def require_platform_reference_owner(user: dict) -> None:
    if not is_platform_owner(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform owner or admin role is required.")


async def enforce_approved_reference_read(user: dict, include_inactive: bool) -> None:
    if include_inactive and not is_platform_owner(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive reference records are restricted to platform owners.")


async def get_suggestion_for_actor(db: Database, suggestion_id: str, user: dict) -> dict:
    suggestion = await db.collection("reference_data_suggestions").find_one({"id": suggestion_id})
    if not suggestion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference suggestion not found.")
    if is_platform_owner(user):
        return suggestion
    await assert_agency_access(db, suggestion["submitting_agency_id"], user)
    if suggestion.get("submitted_by_user_id") != user["id"]:
        membership = await db.collection("agency_staff_memberships").find_one({"agency_id": suggestion["submitting_agency_id"], "user_id": user["id"], "status": "active"})
        if not membership or membership.get("agency_role") not in {"agency_owner", "agency_admin"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the submitting agency or platform owner can view this suggestion.")
    return suggestion


async def apply_suggestion_approval(db: Database, suggestion: dict, reviewer_user_id: str, reviewer_note: str | None = None, merge_into_reference_record_id: str | None = None) -> tuple[dict, dict | None, str]:
    suggestion_type = suggestion.get("suggestion_type")
    domain = suggestion["domain"]
    target_id = merge_into_reference_record_id or suggestion.get("target_reference_record_id")
    approved_record: dict | None = None
    final_status = "approved"

    if suggestion_type in {"correction", "deactivation_request", "merge_request"} and not target_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target reference record is required for this suggestion type.")

    if suggestion_type in {"new_record", "missing_domain_value"}:
        code = normalize_reference_code(suggestion.get("suggested_code") or "")
        if not code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Suggested code is required for approval.")
        existing = await db.collection("global_reference_records").find_one({"domain": domain, "key": code})
        metadata_json = normalize_metadata_or_raise(domain, suggestion.get("suggested_metadata_json") or {})
        payload = {
            "domain": domain,
            "code": code,
            "key": code,
            "label": suggestion["suggested_label"],
            "description": suggestion.get("suggested_description"),
            "aliases": suggestion.get("suggested_aliases") or [],
            "metadata_json": metadata_json,
            "metadata": metadata_json,
            "source_type": "platform",
            "is_active": True,
            "updated_by_user_id": reviewer_user_id,
        }
        if existing:
            approved_record = await db.collection("global_reference_records").update_one({"id": existing["id"]}, payload)
        else:
            approved_record = await db.collection("global_reference_records").insert_one(GlobalReferenceRecord(**{**payload, "created_by_user_id": reviewer_user_id}).model_dump(mode="json"))
    elif suggestion_type == "correction":
        metadata_json = normalize_metadata_or_raise(domain, suggestion.get("suggested_metadata_json") or {})
        updates = {
            "label": suggestion.get("suggested_label"),
            "description": suggestion.get("suggested_description"),
            "aliases": suggestion.get("suggested_aliases") or [],
            "metadata_json": metadata_json,
            "metadata": metadata_json,
            "updated_by_user_id": reviewer_user_id,
        }
        if suggestion.get("suggested_code"):
            code = normalize_reference_code(suggestion["suggested_code"])
            conflict = await db.collection("global_reference_records").find_one({"domain": domain, "key": code})
            if conflict and conflict["id"] != target_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Suggested code conflicts with another global record.")
            updates.update({"code": code, "key": code})
        approved_record = await db.collection("global_reference_records").update_one({"domain": domain, "id": target_id}, updates)
    elif suggestion_type == "deactivation_request":
        approved_record = await db.collection("global_reference_records").update_one({"domain": domain, "id": target_id}, {"is_active": False, "updated_by_user_id": reviewer_user_id})
    elif suggestion_type == "merge_request":
        approved_record = await db.collection("global_reference_records").find_one({"domain": domain, "id": target_id})
        final_status = "merged"

    if suggestion_type in {"correction", "deactivation_request", "merge_request"} and not approved_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target reference record not found.")

    reviewed = await db.collection("reference_data_suggestions").update_one(
        {"id": suggestion["id"]},
        {
            "status": final_status,
            "reviewer_user_id": reviewer_user_id,
            "reviewer_note": reviewer_note,
            "approved_reference_record_id": approved_record["id"] if approved_record else None,
            "reviewed_at": now_utc(),
        },
    )
    return reviewed or suggestion, approved_record, final_status


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
    await enforce_approved_reference_read(user, include_inactive)
    records = filter_active(await db.collection("service_catalogue").find_many(), include_inactive)
    items = [record for record in records if matches_service_query(record, q)]
    return {"items": sort_records(items, "service_code", "service_label"), "query": q, "actor_user_id": user["id"]}


@router.get("/service-catalogue")
async def list_service_catalogue(
    include_inactive: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await enforce_approved_reference_read(user, include_inactive)
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


@router.post("/import-batches", status_code=status.HTTP_201_CREATED)
async def create_import_batch(
    payload: ReferenceImportBatchCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    ensure_domain(payload.domain)
    await require_platform_reference_owner(user)
    if payload.scope != "global":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency suggestion batch imports are reserved for a future import UI phase.")
    batch = await create_reference_import_batch(db, payload.domain, payload.filename, payload.csv_text, payload.scope.value if hasattr(payload.scope, "value") else payload.scope, user["id"], payload.dry_run)
    return {"batch": batch, "actor_user_id": user["id"]}


@router.get("/import-batches")
async def list_import_batches(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_reference_owner(user)
    items = [safe_reference_import_batch(item) for item in await db.collection("reference_import_batches").find_many()]
    return {"items": sorted(items, key=lambda item: str(item.get("created_at")), reverse=True), "actor_user_id": user["id"]}


@router.get("/import-batches/{batch_id}")
async def get_import_batch(
    batch_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_reference_owner(user)
    batch = await db.collection("reference_import_batches").find_one({"id": batch_id})
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference import batch not found.")
    return {"batch": safe_reference_import_batch(batch), "actor_user_id": user["id"]}


@router.post("/suggestions", status_code=status.HTTP_201_CREATED)
async def create_reference_suggestion(
    payload: ReferenceDataSuggestionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    ensure_domain(payload.domain)
    await assert_agency_access(db, payload.submitting_agency_id, user)
    code = normalize_reference_code(payload.suggested_code or "") or None
    if payload.target_reference_record_id:
        target = await db.collection("global_reference_records").find_one({"domain": payload.domain, "id": payload.target_reference_record_id})
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target reference record not found.")
    suggestion = ReferenceDataSuggestion(
        **{
            **payload.model_dump(mode="json"),
            "suggested_code": code,
            "submitted_by_user_id": user["id"],
            "status": "pending_review",
        }
    )
    created = await db.collection("reference_data_suggestions").insert_one(suggestion.model_dump(mode="json"))
    await audit_reference_event(db, "reference_suggestion_created", "reference_data_suggestion", created["id"], f"Reference suggestion submitted for {payload.domain}.", user["id"], {"domain": payload.domain, "suggestion_type": payload.suggestion_type.value if hasattr(payload.suggestion_type, "value") else payload.suggestion_type, "submitting_agency_id": payload.submitting_agency_id})
    return {"suggestion": safe_reference_suggestion(created), "actor_user_id": user["id"]}


@router.get("/suggestions")
async def list_reference_suggestions(
    status_filter: str | None = Query(default=None, alias="status"),
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    filters: dict[str, Any] = {}
    if status_filter:
        filters["status"] = status_filter
    if is_platform_owner(user):
        if agency_id:
            filters["submitting_agency_id"] = agency_id
    else:
        if agency_id:
            await assert_agency_access(db, agency_id, user)
            filters["submitting_agency_id"] = agency_id
        else:
            memberships = await db.collection("agency_staff_memberships").find_many({"user_id": user["id"], "status": "active"})
            agency_ids = {item["agency_id"] for item in memberships}
            items = [safe_reference_suggestion(item) for item in await db.collection("reference_data_suggestions").find_many(filters) if item.get("submitting_agency_id") in agency_ids]
            return {"items": sorted(items, key=lambda item: str(item.get("created_at")), reverse=True), "actor_user_id": user["id"]}
    items = [safe_reference_suggestion(item) for item in await db.collection("reference_data_suggestions").find_many(filters)]
    return {"items": sorted(items, key=lambda item: str(item.get("created_at")), reverse=True), "actor_user_id": user["id"]}


@router.get("/suggestions/{suggestion_id}")
async def get_reference_suggestion(
    suggestion_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    suggestion = await get_suggestion_for_actor(db, suggestion_id, user)
    return {"suggestion": safe_reference_suggestion(suggestion), "actor_user_id": user["id"]}


@router.patch("/suggestions/{suggestion_id}/approve")
async def approve_reference_suggestion(
    suggestion_id: str,
    payload: ReferenceSuggestionReview,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_reference_owner(user)
    suggestion = await get_suggestion_for_actor(db, suggestion_id, user)
    if suggestion.get("status") not in {"pending_review", "needs_more_information"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending suggestions can be approved.")
    reviewed, record, final_status = await apply_suggestion_approval(db, suggestion, user["id"], payload.reviewer_note, payload.merge_into_reference_record_id)
    await audit_reference_event(db, "reference_suggestion_reviewed", "reference_data_suggestion", suggestion_id, f"Reference suggestion {final_status}.", user["id"], {"status": final_status})
    await audit_reference_event(db, "reference_suggestion_approved", "reference_data_suggestion", suggestion_id, f"Reference suggestion approved for {suggestion['domain']}.", user["id"], {"approved_reference_record_id": record["id"] if record else None})
    if record:
        await audit_reference_event(db, "reference_record_promoted_from_suggestion", "global_reference_record", record["id"], f"Global reference record promoted from suggestion {suggestion_id}.", user["id"], {"suggestion_id": suggestion_id, "domain": suggestion["domain"]})
    return {"suggestion": safe_reference_suggestion(reviewed), "record": safe_reference_record(record) if record else None, "actor_user_id": user["id"]}


@router.patch("/suggestions/{suggestion_id}/reject")
async def reject_reference_suggestion(
    suggestion_id: str,
    payload: ReferenceSuggestionReview,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_reference_owner(user)
    suggestion = await get_suggestion_for_actor(db, suggestion_id, user)
    reviewed = await db.collection("reference_data_suggestions").update_one({"id": suggestion_id}, {"status": "rejected", "reviewer_user_id": user["id"], "reviewer_note": payload.reviewer_note, "reviewed_at": now_utc()})
    await audit_reference_event(db, "reference_suggestion_reviewed", "reference_data_suggestion", suggestion_id, "Reference suggestion reviewed.", user["id"], {"status": "rejected"})
    await audit_reference_event(db, "reference_suggestion_rejected", "reference_data_suggestion", suggestion_id, f"Reference suggestion rejected for {suggestion['domain']}.", user["id"], {"domain": suggestion["domain"]})
    return {"suggestion": safe_reference_suggestion(reviewed or suggestion), "actor_user_id": user["id"]}


@router.patch("/suggestions/{suggestion_id}/needs-more-information")
async def request_reference_suggestion_information(
    suggestion_id: str,
    payload: ReferenceSuggestionReview,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_reference_owner(user)
    suggestion = await get_suggestion_for_actor(db, suggestion_id, user)
    reviewed = await db.collection("reference_data_suggestions").update_one({"id": suggestion_id}, {"status": "needs_more_information", "reviewer_user_id": user["id"], "reviewer_note": payload.reviewer_note, "reviewed_at": now_utc()})
    await audit_reference_event(db, "reference_suggestion_reviewed", "reference_data_suggestion", suggestion_id, "Reference suggestion marked needs more information.", user["id"], {"status": "needs_more_information"})
    return {"suggestion": safe_reference_suggestion(reviewed or suggestion), "actor_user_id": user["id"]}


@router.patch("/suggestions/{suggestion_id}/archive")
async def archive_reference_suggestion(
    suggestion_id: str,
    payload: ReferenceSuggestionReview,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_reference_owner(user)
    suggestion = await get_suggestion_for_actor(db, suggestion_id, user)
    reviewed = await db.collection("reference_data_suggestions").update_one({"id": suggestion_id}, {"status": "archived", "reviewer_user_id": user["id"], "reviewer_note": payload.reviewer_note, "reviewed_at": now_utc()})
    await audit_reference_event(db, "reference_suggestion_reviewed", "reference_data_suggestion", suggestion_id, "Reference suggestion archived.", user["id"], {"status": "archived"})
    return {"suggestion": safe_reference_suggestion(reviewed or suggestion), "actor_user_id": user["id"]}


@router.get("/{domain}/search")
async def search_reference_domain(
    domain: str,
    q: str = Query(default=""),
    include_inactive: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    ensure_domain(domain)
    await enforce_approved_reference_read(user, include_inactive)
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
    await enforce_approved_reference_read(user, include_inactive)
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
    await enforce_approved_reference_read(user, include_inactive)
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
    code = normalize_city_reference_code(payload.code or payload.key or "") if domain == "cities" else normalize_reference_code(payload.code or payload.key or "")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reference code is required.")
    existing = await db.collection("global_reference_records").find_one({"domain": domain, "key": code})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reference record already exists.")
    payload_dict = payload.model_dump(mode="json")
    metadata_json = normalize_record_metadata_or_raise(domain, code, payload.label, payload.aliases, payload_dict.get("metadata_json") or payload_dict.get("metadata") or {})
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
        code = normalize_city_reference_code(updates.get("code") or updates.get("key") or "") if domain == "cities" else normalize_reference_code(updates.get("code") or updates.get("key") or "")
        if not code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reference code cannot be blank.")
        conflict = await db.collection("global_reference_records").find_one({"domain": domain, "key": code})
        if conflict and conflict["id"] != record_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reference code already exists.")
        updates["code"] = code
        updates["key"] = code
    if "metadata_json" in updates or "metadata" in updates:
        metadata_json = normalize_record_metadata_or_raise(
            domain,
            updates.get("code") or existing.get("code") or existing.get("key"),
            updates.get("label") or existing.get("label"),
            updates.get("aliases") if "aliases" in updates else existing.get("aliases") or [],
            updates.get("metadata_json") or updates.get("metadata") or {},
        )
        updates["metadata_json"] = metadata_json
        updates["metadata"] = metadata_json
    elif domain == "cities" and any(key in updates for key in {"code", "key", "label", "aliases"}):
        metadata_json = normalize_record_metadata_or_raise(
            domain,
            updates.get("code") or existing.get("code") or existing.get("key"),
            updates.get("label") or existing.get("label"),
            updates.get("aliases") if "aliases" in updates else existing.get("aliases") or [],
            existing.get("metadata_json") or {},
        )
        updates["metadata_json"] = metadata_json
        updates["metadata"] = metadata_json
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
