import csv
import json
import re
from io import StringIO
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import require_platform_role
from database import Database, get_database
from models import (
    GlobalReferenceRecord,
    PlatformReferenceRecordCreate,
    PlatformReferenceRecordUpdate,
    ReferenceDeactivationRequest,
    ReferenceEnrichmentPack,
    ReferenceEnrichmentPackCreate,
    ReferenceEnrichmentPackPreviewRequest,
    PlatformReferenceImportRequest,
    ReferenceImportApplyRequest,
    ReferenceImportPreviewRequest,
    ReferenceDomainMetadata,
    ReferenceDomainMetadataCreate,
    ReferenceDomainMetadataUpdate,
    ReferenceEnrichmentImportRequest,
    ReferenceSuggestionReview,
    now_utc,
)
from routers.reference import apply_suggestion_approval
from services.reference_enrichment_service import (
    ENRICHMENT_TEMPLATES,
    list_templates,
    read_template,
    run_reference_enrichment_import,
)
from services.reference_domain_usage_service import (
    get_domain_usage,
    list_domain_usage,
    reference_action_required,
    reference_health,
)
from services.reference_import_template_service import (
    apply_reference_import,
    get_import_template,
    list_import_templates,
    preview_reference_import,
)
from services.reference_data_service import (
    COUNTRY_METADATA_FIELDS,
    REFERENCE_DOMAINS,
    REFERENCE_DOMAIN_METADATA_SCHEMAS,
    audit_reference_event,
    country_enrichment_complete,
    create_reference_import_batch,
    normalize_reference_code,
    normalize_city_reference_code,
    normalize_city_reference_metadata,
    normalize_reference_metadata_for_domain,
    safe_reference_import_batch,
    safe_reference_record,
    safe_reference_suggestion,
    sort_records,
)
from services.canonical_reference_service import (
    find_active_scope_conflict,
    governed_deactivate_reference,
    normalize_domain_code as normalize_reference_value,
    reference_record_usage,
)

router = APIRouter(prefix="/api/platform/reference", tags=["platform-reference"])

PlatformReferenceOwner = Depends(require_platform_role(["platform_owner", "platform_admin"]))


def normalize_domain_code(domain: str) -> str:
    normalized = domain.strip().lower()
    if not re.fullmatch(r"[a-z0-9_]+", normalized):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Domain code must use lowercase letters, numbers, and underscores.")
    return normalized


async def is_supported_domain(db: Database, domain: str) -> bool:
    if domain in REFERENCE_DOMAINS:
        return True
    metadata = await db.collection("reference_domain_metadata").find_one({"domain": domain})
    return bool(metadata and metadata.get("is_active", True))


async def ensure_supported_domain(db: Database, domain: str) -> None:
    if not await is_supported_domain(db, domain):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported reference domain: {domain}")


def enriched_metadata(domain: str, metadata: dict[str, Any] | None, actor_user_id: str | None = None) -> dict[str, Any]:
    normalized, errors = normalize_reference_metadata_for_domain(domain, metadata or {})
    if errors:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors)
    if domain == "countries":
        normalized["updated_by_user_id"] = actor_user_id
        if normalized.get("data_quality_status") == "verified":
            normalized["reviewed_by_user_id"] = actor_user_id
            normalized["reviewed_at"] = now_utc().isoformat()
    return normalized


def enriched_record_metadata(domain: str, code: str, label: str, aliases: list[str] | None, metadata: dict[str, Any] | None, actor_user_id: str | None = None) -> dict[str, Any]:
    if domain == "cities":
        normalized, errors = normalize_city_reference_metadata(code, label, aliases or [], metadata or {})
        if errors:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors)
        return normalized
    return enriched_metadata(domain, metadata, actor_user_id)


async def platform_domains(db: Database) -> list[dict[str, Any]]:
    records = await db.collection("global_reference_records").find_many()
    metadata_records = {item["domain"]: item for item in await db.collection("reference_domain_metadata").find_many()}
    suggestions = await db.collection("reference_data_suggestions").find_many()
    import_batches = await db.collection("reference_import_batches").find_many()
    domain_codes = list(dict.fromkeys([*REFERENCE_DOMAINS.keys(), *metadata_records.keys()]))
    domains = []
    for index, domain in enumerate(domain_codes, start=1):
        metadata = metadata_records.get(domain, {})
        active_records = [item for item in records if item.get("domain") == domain and item.get("is_active", True)]
        inactive_records = [item for item in records if item.get("domain") == domain and not item.get("is_active", True)]
        domains.append(
            {
                "domain": domain,
                "label": metadata.get("label") or REFERENCE_DOMAINS.get(domain, domain.replace("_", " ").title()),
                "description": metadata.get("description"),
                "category": metadata.get("category", "reference"),
                "is_active": metadata.get("is_active", True),
                "sort_order": metadata.get("sort_order", index * 10),
                "metadata_schema_json": metadata.get("metadata_schema_json") or REFERENCE_DOMAIN_METADATA_SCHEMAS.get(domain, {}),
                "active_record_count": len(active_records),
                "inactive_record_count": len(inactive_records),
                "pending_suggestion_count": len([item for item in suggestions if item.get("domain") == domain and item.get("status") == "pending_review"]),
                "import_batch_count": len([item for item in import_batches if item.get("domain") == domain]),
                "platform_owned": True,
            }
        )
    return sorted(domains, key=lambda item: (item["sort_order"], item["label"]))


def matches_record_filters(
    record: dict[str, Any],
    query: str,
    data_quality_status: str | None,
    continent: str | None,
    missing_iso3: bool,
    missing_capital_iata: bool,
    missing_currency: bool,
    missing_major_airports: bool,
    missing_national_carrier: bool,
    capital_iata: str | None,
    currency: str | None,
    airport: str | None,
    national_carrier: str | None,
) -> bool:
    metadata = record.get("metadata_json") or {}
    if query:
        needle = query.lower()
        haystack = [
            record.get("code"),
            record.get("key"),
            record.get("label"),
            record.get("description"),
            *(record.get("aliases") or []),
            metadata.get("iso2_code"),
            metadata.get("iso3_code"),
            metadata.get("capital_city"),
            metadata.get("capital_iata_code"),
            metadata.get("currency_iso_code"),
        ]
        if not any(needle in str(value).lower() for value in haystack if value):
            return False
    if data_quality_status and metadata.get("data_quality_status") != data_quality_status:
        return False
    if continent and metadata.get("continent") != continent:
        return False
    if capital_iata and metadata.get("capital_iata_code") != capital_iata.upper():
        return False
    if currency and metadata.get("currency_iso_code") != currency.upper():
        return False
    if airport and airport.upper() not in (metadata.get("major_airports") or []):
        return False
    carrier = metadata.get("national_carrier") or {}
    if national_carrier and national_carrier.lower() not in str(carrier.get("name") or "").lower():
        return False
    if missing_iso3 and metadata.get("iso3_code"):
        return False
    if missing_capital_iata and metadata.get("capital_iata_code"):
        return False
    if missing_currency and metadata.get("currency_iso_code"):
        return False
    if missing_major_airports and metadata.get("major_airports"):
        return False
    if missing_national_carrier and metadata.get("national_carrier"):
        return False
    return True


def country_export_row(record: dict[str, Any]) -> dict[str, Any]:
    metadata = record.get("metadata_json") or {}
    row = {
        "domain": record.get("domain"),
        "code": record.get("code") or record.get("key"),
        "label": record.get("label"),
        "description": record.get("description") or "",
        "aliases": "|".join(record.get("aliases") or []),
        "sort_order": record.get("sort_order", 100),
        "is_active": record.get("is_active", True),
    }
    for field in COUNTRY_METADATA_FIELDS:
        value = metadata.get(field)
        row[field] = json.dumps(value, default=str) if isinstance(value, (dict, list)) else (value if value is not None else "")
    return row


def csv_content(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()), extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


@router.get("/domains")
async def list_platform_reference_domains(
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    return {"items": await platform_domains(db), "actor_user_id": user["id"]}


@router.get("/domain-usage")
async def list_reference_domain_usage(user: dict = PlatformReferenceOwner) -> dict:
    return {"items": list_domain_usage(), "actor_user_id": user["id"]}


@router.get("/domain-usage/{domain_key}")
async def get_reference_domain_usage(domain_key: str, user: dict = PlatformReferenceOwner) -> dict:
    usage = get_domain_usage(domain_key)
    if not usage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference domain usage definition not found.")
    return {"domain": usage, "actor_user_id": user["id"]}


@router.get("/health")
async def get_reference_health(
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    return {**await reference_health(db), "actor_user_id": user["id"]}


@router.get("/records/action-required")
async def list_reference_action_required(
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    return {"items": await reference_action_required(db), "actor_user_id": user["id"]}


@router.get("/import/templates")
async def list_reference_import_templates(user: dict = PlatformReferenceOwner) -> dict:
    return {"items": list_import_templates(), "actor_user_id": user["id"]}


@router.get("/import/templates/{domain_key}")
async def get_reference_import_template(domain_key: str, user: dict = PlatformReferenceOwner) -> dict:
    template = get_import_template(domain_key)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference import template not found.")
    return {"template": template, "actor_user_id": user["id"]}


@router.post("/import/preview")
async def preview_platform_reference_import(
    payload: ReferenceImportPreviewRequest,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    result = await preview_reference_import(db, payload.domain, payload.csv_text, payload.mode)
    return {**result, "actor_user_id": user["id"]}


@router.post("/import/apply")
async def apply_platform_reference_import(
    payload: ReferenceImportApplyRequest,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    result = await apply_reference_import(
        db,
        payload.domain,
        payload.filename or f"{payload.domain}.csv",
        payload.csv_text,
        payload.mode,
        user["id"],
    )
    return {**result, "actor_user_id": user["id"]}


@router.post("/domains", status_code=status.HTTP_201_CREATED)
async def create_platform_reference_domain(
    payload: ReferenceDomainMetadataCreate,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    domain = normalize_domain_code(payload.domain)
    existing = await db.collection("reference_domain_metadata").find_one({"domain": domain})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reference domain metadata already exists.")
    metadata = ReferenceDomainMetadata(
        **{
            **payload.model_dump(mode="json"),
            "domain": domain,
            "created_by_user_id": user["id"],
            "updated_by_user_id": user["id"],
        }
    )
    created = await db.collection("reference_domain_metadata").insert_one(metadata.model_dump(mode="json"))
    await audit_reference_event(db, "platform_reference_domain_created", "reference_domain_metadata", created["id"], f"Reference domain {domain} metadata created.", user["id"], {"domain": domain})
    return {"domain": created, "actor_user_id": user["id"]}


@router.put("/domains/{domain}")
async def update_platform_reference_domain(
    domain: str,
    payload: ReferenceDomainMetadataUpdate,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    domain = normalize_domain_code(domain)
    updates = {key: value for key, value in payload.model_dump(mode="json", exclude_unset=True).items() if value is not None}
    updates["updated_by_user_id"] = user["id"]
    existing = await db.collection("reference_domain_metadata").find_one({"domain": domain})
    if existing:
        updated = await db.collection("reference_domain_metadata").update_one({"id": existing["id"]}, updates)
    else:
        base = ReferenceDomainMetadata(
            domain=domain,
            label=updates.get("label") or REFERENCE_DOMAINS.get(domain, domain.replace("_", " ").title()),
            description=updates.get("description"),
            category=updates.get("category", "reference"),
            is_active=updates.get("is_active", True),
            sort_order=updates.get("sort_order", 100),
            metadata_schema_json=updates.get("metadata_schema_json") or REFERENCE_DOMAIN_METADATA_SCHEMAS.get(domain, {}),
            created_by_user_id=user["id"],
            updated_by_user_id=user["id"],
        )
        updated = await db.collection("reference_domain_metadata").insert_one(base.model_dump(mode="json"))
    await audit_reference_event(db, "platform_reference_domain_updated", "reference_domain_metadata", updated["id"], f"Reference domain {domain} metadata updated.", user["id"], {"domain": domain})
    return {"domain": updated, "actor_user_id": user["id"]}


@router.get("/records")
async def list_platform_reference_records(
    domain: str | None = Query(default=None),
    q: str = Query(default=""),
    include_inactive: bool = Query(default=True),
    data_quality_status: str | None = Query(default=None),
    continent: str | None = Query(default=None),
    missing_iso3: bool = Query(default=False),
    missing_capital_iata: bool = Query(default=False),
    missing_currency: bool = Query(default=False),
    missing_major_airports: bool = Query(default=False),
    missing_national_carrier: bool = Query(default=False),
    capital_iata: str | None = Query(default=None),
    currency: str | None = Query(default=None),
    airport: str | None = Query(default=None),
    national_carrier: str | None = Query(default=None),
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    filters = {"domain": domain} if domain else None
    if domain:
        await ensure_supported_domain(db, domain)
    records = [safe_reference_record(record) for record in await db.collection("global_reference_records").find_many(filters)]
    if not include_inactive:
        records = [record for record in records if record.get("is_active", True)]
    items = [
        record
        for record in records
        if matches_record_filters(
            record,
            q,
            data_quality_status,
            continent,
            missing_iso3,
            missing_capital_iata,
            missing_currency,
            missing_major_airports,
            missing_national_carrier,
            capital_iata,
            currency,
            airport,
            national_carrier,
        )
    ]
    return {"items": sort_records(items), "actor_user_id": user["id"]}


@router.post("/records", status_code=status.HTTP_201_CREATED)
async def create_platform_reference_record(
    payload: PlatformReferenceRecordCreate,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    domain = normalize_domain_code(payload.domain)
    await ensure_supported_domain(db, domain)
    code = normalize_city_reference_code(payload.code) if domain == "cities" else normalize_reference_value(domain, payload.code)
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reference code is required.")
    if await find_active_scope_conflict(
        db,
        domain=domain,
        code=code,
        key=code,
        scope="global",
        agency_id=None,
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An active reference code or key already exists in the effective scope.")
    metadata_json = enriched_record_metadata(domain, code, payload.label, payload.aliases, payload.metadata_json, user["id"])
    record = GlobalReferenceRecord(
        domain=domain,
        code=code,
        key=code,
        label=payload.label,
        description=payload.description,
        aliases=payload.aliases,
        sort_order=payload.sort_order,
        metadata_json=metadata_json,
        metadata=metadata_json,
        source_type="platform",
        is_active=payload.is_active,
        created_by_user_id=user["id"],
        updated_by_user_id=user["id"],
    )
    created = await db.collection("global_reference_records").insert_one(record.model_dump(mode="json"))
    await audit_reference_event(db, "platform_reference_record_created", "global_reference_record", created["id"], f"Platform reference record {domain}:{code} created.", user["id"], {"domain": domain, "code": code})
    if domain == "countries":
        await audit_reference_event(db, "platform_reference_country_enriched", "global_reference_record", created["id"], f"Country reference record {code} enriched.", user["id"], {"complete": country_enrichment_complete(metadata_json)})
    return {"record": safe_reference_record(created), "actor_user_id": user["id"]}


@router.get("/records/{record_id}")
async def get_platform_reference_record(
    record_id: str,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    record = await db.collection("global_reference_records").find_one({"id": record_id})
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference record not found.")
    await audit_reference_event(db, "platform_reference_record_card_viewed", "global_reference_record", record_id, "Platform reference record card viewed.", user["id"], {"domain": record.get("domain")})
    return {"record": safe_reference_record(record), "actor_user_id": user["id"]}


@router.get("/records/{record_id}/usage")
async def get_platform_reference_record_usage(
    record_id: str,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    record = await db.collection("global_reference_records").find_one({"id": record_id})
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference record not found.")
    return {
        "usage": await reference_record_usage(db, record),
        "actor_user_id": user["id"],
    }


@router.put("/records/{record_id}")
async def update_platform_reference_record(
    record_id: str,
    payload: PlatformReferenceRecordUpdate,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    existing = await db.collection("global_reference_records").find_one({"id": record_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference record not found.")
    domain = existing["domain"]
    updates = {key: value for key, value in payload.model_dump(mode="json", exclude_unset=True).items() if value is not None}
    if "domain" in updates:
        payload_domain = normalize_domain_code(updates.pop("domain"))
        if payload_domain != domain:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Reference record belongs to {domain}, not {payload_domain}.")
    if "is_active" in updates and bool(updates["is_active"]) != bool(existing.get("is_active", True)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the governed archive or reactivate action to change reference status.",
        )
    if "code" in updates:
        code = normalize_city_reference_code(updates["code"]) if domain == "cities" else normalize_reference_value(domain, updates["code"])
        if not code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reference code cannot be blank.")
        conflict = await find_active_scope_conflict(
            db,
            domain=domain,
            code=code,
            key=code,
            scope=str(existing.get("scope") or "global"),
            agency_id=existing.get("agency_id"),
            exclude_id=record_id,
        )
        if conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An active reference code or key already exists in the effective scope.")
        updates["code"] = code
        updates["key"] = code
    if "metadata_json" in updates:
        metadata_json = enriched_record_metadata(
            domain,
            updates.get("code") or existing.get("code") or existing.get("key"),
            updates.get("label") or existing.get("label"),
            updates.get("aliases") if "aliases" in updates else existing.get("aliases") or [],
            updates["metadata_json"],
            user["id"],
        )
        updates["metadata_json"] = metadata_json
        updates["metadata"] = metadata_json
    elif domain == "cities" and any(key in updates for key in {"code", "label", "aliases"}):
        metadata_json = enriched_record_metadata(
            domain,
            updates.get("code") or existing.get("code") or existing.get("key"),
            updates.get("label") or existing.get("label"),
            updates.get("aliases") if "aliases" in updates else existing.get("aliases") or [],
            existing.get("metadata_json") or {},
            user["id"],
        )
        updates["metadata_json"] = metadata_json
        updates["metadata"] = metadata_json
    updates["updated_by_user_id"] = user["id"]
    updated = await db.collection("global_reference_records").update_one({"id": record_id}, updates)
    await audit_reference_event(db, "platform_reference_record_updated", "global_reference_record", record_id, f"Platform reference record {domain}:{record_id} updated.", user["id"], {"domain": domain})
    if domain == "countries" and "metadata_json" in updates:
        await audit_reference_event(db, "platform_reference_country_enriched", "global_reference_record", record_id, "Country reference metadata updated.", user["id"], {"complete": country_enrichment_complete(updates["metadata_json"])})
    return {"record": safe_reference_record(updated or existing), "actor_user_id": user["id"]}


@router.post("/records/{record_id}/archive")
async def archive_platform_reference_record(
    record_id: str,
    payload: ReferenceDeactivationRequest | None = None,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    existing = await db.collection("global_reference_records").find_one({"id": record_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference record not found.")
    action = payload or ReferenceDeactivationRequest()
    updated, usage = await governed_deactivate_reference(
        db,
        existing,
        actor_user_id=user["id"],
        force=action.force,
        reason=action.reason,
    )
    await audit_reference_event(
        db,
        "platform_reference_record_archived",
        "global_reference_record",
        record_id,
        "Platform reference record archived.",
        user["id"],
        {
            "domain": updated.get("domain"),
            "forced": action.force,
            "reason": action.reason,
            "active_record_count": usage["active_record_count"],
        },
    )
    return {
        "record": safe_reference_record(updated),
        "usage": usage,
        "actor_user_id": user["id"],
    }


@router.post("/records/{record_id}/reactivate")
async def reactivate_platform_reference_record(
    record_id: str,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    existing = await db.collection("global_reference_records").find_one({"id": record_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference record not found.")
    conflict = await find_active_scope_conflict(
        db,
        domain=existing["domain"],
        code=existing.get("code") or existing.get("key") or "",
        key=existing.get("key") or existing.get("code") or "",
        scope=str(existing.get("scope") or "global"),
        agency_id=existing.get("agency_id"),
        exclude_id=record_id,
    )
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reference record cannot be reactivated because an active code or key conflicts in the effective scope.",
        )
    updated = await db.collection("global_reference_records").update_one(
        {"id": record_id},
        {"is_active": True, "updated_by_user_id": user["id"]},
    )
    await audit_reference_event(
        db,
        "platform_reference_record_reactivated",
        "global_reference_record",
        record_id,
        "Platform reference record reactivated.",
        user["id"],
        {"domain": existing.get("domain")},
    )
    return {"record": safe_reference_record(updated or existing), "actor_user_id": user["id"]}


@router.get("/suggestions")
async def list_platform_reference_suggestions(
    status_filter: str | None = Query(default=None, alias="status"),
    domain: str | None = Query(default=None),
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    filters: dict[str, Any] = {}
    if status_filter:
        filters["status"] = status_filter
    if domain:
        filters["domain"] = domain
    suggestions = [safe_reference_suggestion(item) for item in await db.collection("reference_data_suggestions").find_many(filters)]
    agencies = {item["id"]: item for item in await db.collection("agencies").find_many()}
    users = {item["id"]: item for item in await db.collection("platform_users").find_many()}
    items = []
    for suggestion in suggestions:
        items.append(
            {
                **suggestion,
                "agency_name": agencies.get(suggestion.get("submitting_agency_id"), {}).get("name"),
                "submitted_by_email": users.get(suggestion.get("submitted_by_user_id"), {}).get("email"),
            }
        )
    return {"items": sorted(items, key=lambda item: str(item.get("created_at")), reverse=True), "actor_user_id": user["id"]}


async def get_platform_suggestion(db: Database, suggestion_id: str) -> dict:
    suggestion = await db.collection("reference_data_suggestions").find_one({"id": suggestion_id})
    if not suggestion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference suggestion not found.")
    return suggestion


@router.post("/suggestions/{suggestion_id}/approve")
async def approve_platform_reference_suggestion(
    suggestion_id: str,
    payload: ReferenceSuggestionReview,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    suggestion = await get_platform_suggestion(db, suggestion_id)
    if suggestion.get("status") not in {"pending_review", "needs_more_information"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending suggestions can be approved.")
    if suggestion.get("domain") == "countries":
        _, metadata_errors = normalize_reference_metadata_for_domain("countries", suggestion.get("suggested_metadata_json") or {})
        if metadata_errors:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=metadata_errors)
    reviewed, record, final_status = await apply_suggestion_approval(db, suggestion, user["id"], payload.reviewer_note, payload.merge_into_reference_record_id)
    await audit_reference_event(db, "platform_reference_suggestion_approved", "reference_data_suggestion", suggestion_id, f"Platform approved reference suggestion for {suggestion['domain']}.", user["id"], {"status": final_status, "approved_reference_record_id": record["id"] if record else None})
    return {"suggestion": safe_reference_suggestion(reviewed), "record": safe_reference_record(record) if record else None, "actor_user_id": user["id"]}


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_platform_reference_suggestion(
    suggestion_id: str,
    payload: ReferenceSuggestionReview,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    suggestion = await get_platform_suggestion(db, suggestion_id)
    reviewed = await db.collection("reference_data_suggestions").update_one({"id": suggestion_id}, {"status": "rejected", "reviewer_user_id": user["id"], "reviewer_note": payload.reviewer_note, "reviewed_at": now_utc()})
    await audit_reference_event(db, "platform_reference_suggestion_rejected", "reference_data_suggestion", suggestion_id, f"Platform rejected reference suggestion for {suggestion['domain']}.", user["id"], {"domain": suggestion["domain"]})
    return {"suggestion": safe_reference_suggestion(reviewed or suggestion), "actor_user_id": user["id"]}


@router.post("/suggestions/{suggestion_id}/request-info")
async def request_info_platform_reference_suggestion(
    suggestion_id: str,
    payload: ReferenceSuggestionReview,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    suggestion = await get_platform_suggestion(db, suggestion_id)
    reviewed = await db.collection("reference_data_suggestions").update_one({"id": suggestion_id}, {"status": "needs_more_information", "reviewer_user_id": user["id"], "reviewer_note": payload.reviewer_note, "reviewed_at": now_utc()})
    await audit_reference_event(db, "platform_reference_suggestion_info_requested", "reference_data_suggestion", suggestion_id, f"Platform requested more information for {suggestion['domain']} suggestion.", user["id"], {"domain": suggestion["domain"]})
    return {"suggestion": safe_reference_suggestion(reviewed or suggestion), "actor_user_id": user["id"]}


@router.post("/suggestions/{suggestion_id}/archive")
async def archive_platform_reference_suggestion(
    suggestion_id: str,
    payload: ReferenceSuggestionReview,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    suggestion = await get_platform_suggestion(db, suggestion_id)
    reviewed = await db.collection("reference_data_suggestions").update_one({"id": suggestion_id}, {"status": "archived", "reviewer_user_id": user["id"], "reviewer_note": payload.reviewer_note, "reviewed_at": now_utc()})
    await audit_reference_event(db, "platform_reference_suggestion_archived", "reference_data_suggestion", suggestion_id, f"Platform archived reference suggestion for {suggestion['domain']}.", user["id"], {"domain": suggestion["domain"]})
    return {"suggestion": safe_reference_suggestion(reviewed or suggestion), "actor_user_id": user["id"]}


@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_platform_reference_csv(
    payload: PlatformReferenceImportRequest,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    await ensure_supported_domain(db, payload.domain)
    if payload.scope != "global":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Platform console imports must use global scope.")
    batch = await create_reference_import_batch(db, payload.domain, payload.filename, payload.csv_text, "global", user["id"], payload.dry_run)
    await audit_reference_event(
        db,
        "platform_reference_import_dry_run" if payload.dry_run else "platform_reference_import_committed",
        "reference_import_batch",
        batch["id"],
        f"Platform reference import {'dry run' if payload.dry_run else 'committed'} for {payload.domain}.",
        user["id"],
        {"domain": payload.domain, "valid_rows": batch.get("valid_rows"), "invalid_rows": batch.get("invalid_rows")},
    )
    return {"batch": batch, "actor_user_id": user["id"]}


@router.get("/import-batches")
async def list_platform_reference_import_batches(
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    items = [safe_reference_import_batch(item) for item in await db.collection("reference_import_batches").find_many()]
    return {"items": sorted(items, key=lambda item: str(item.get("created_at")), reverse=True), "actor_user_id": user["id"]}


@router.get("/enrichment/templates")
async def list_reference_enrichment_templates(
    user: dict = PlatformReferenceOwner,
) -> dict:
    return {"items": list_templates(), "actor_user_id": user["id"]}


@router.get("/enrichment/template/{template_name}")
async def get_reference_enrichment_template(
    template_name: str,
    user: dict = PlatformReferenceOwner,
) -> dict:
    if template_name not in ENRICHMENT_TEMPLATES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference enrichment template not found.")
    return {
        "template": {**ENRICHMENT_TEMPLATES[template_name], "template_name": template_name},
        "csv_text": read_template(template_name),
        "actor_user_id": user["id"],
    }


@router.post("/enrichment/dry-run")
async def dry_run_reference_enrichment_import(
    payload: ReferenceEnrichmentImportRequest,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    try:
        result = await run_reference_enrichment_import(
            db,
            payload.domain,
            payload.csv_text,
            user["id"],
            payload.update_mode,
            True,
            payload.source_label,
            payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {**result, "actor_user_id": user["id"]}


@router.post("/enrichment/import")
async def commit_reference_enrichment_import(
    payload: ReferenceEnrichmentImportRequest,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    try:
        result = await run_reference_enrichment_import(
            db,
            payload.domain,
            payload.csv_text,
            user["id"],
            payload.update_mode,
            False,
            payload.source_label,
            payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {**result, "actor_user_id": user["id"]}


@router.get("/enrichment/batches")
async def list_reference_enrichment_batches(
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    items = [
        safe_reference_import_batch(item)
        for item in await db.collection("reference_import_batches").find_many()
        if (item.get("error_report_json") or {}).get("enrichment")
    ]
    return {"items": sorted(items, key=lambda item: str(item.get("created_at")), reverse=True), "actor_user_id": user["id"]}


def default_enrichment_packs() -> list[dict[str, Any]]:
    return [
        {
            "id": "airport_timezone_city_country_pack",
            "pack_key": "airport_timezone_city_country_pack",
            "label": "Airport timezone, city, and country pack",
            "description": "Enriches airport records with city, country, timezone, and geospatial metadata used by route, offer, and readiness workflows.",
            "target_domain": "airports",
            "source_type": "csv_import",
            "status": "ready",
            "fields_added_or_updated": ["city_code", "country_code", "timezone", "latitude", "longitude"],
            "validation_rules_json": get_import_template("airports") or {},
            "preview_count": 0,
            "applied_count": 0,
            "warnings_json": [],
            "workflow_impact": ["request_segments", "trip_segments", "offer_routes", "booking_readiness"],
        },
        {
            "id": "airline_distribution_profile_pack",
            "pack_key": "airline_distribution_profile_pack",
            "label": "Airline distribution profile pack",
            "description": "Enriches airline records with identifiers and distribution metadata for airline intelligence, rules, and offers.",
            "target_domain": "airlines",
            "source_type": "csv_import",
            "status": "ready",
            "fields_added_or_updated": ["iata_code", "icao_code", "country_code", "distribution_profile"],
            "validation_rules_json": get_import_template("airlines") or {},
            "preview_count": 0,
            "applied_count": 0,
            "warnings_json": [],
            "workflow_impact": ["airline_intelligence", "rules_services", "offer_builder", "booking_readiness"],
        },
        {
            "id": "service_catalogue_ssr_emd_mapping_pack",
            "pack_key": "service_catalogue_ssr_emd_mapping_pack",
            "label": "Service catalogue SSR and EMD mapping pack",
            "description": "Adds service operational mapping for SSR/OSI previews, offer feasibility, booking readiness, EMD readiness, and documents.",
            "target_domain": "service_catalogue",
            "source_type": "csv_import",
            "status": "ready",
            "fields_added_or_updated": ["ssr_code", "rules_category", "emd_applicability", "required_documents_json"],
            "validation_rules_json": get_import_template("service_catalogue") or {},
            "preview_count": 0,
            "applied_count": 0,
            "warnings_json": [],
            "workflow_impact": ["request_builder", "rules_services", "offer_acceptance", "booking_readiness", "documents"],
        },
        {
            "id": "document_type_compliance_pack",
            "pack_key": "document_type_compliance_pack",
            "label": "Document type compliance pack",
            "description": "Enriches document type records with compliance and validity metadata.",
            "target_domain": "document_types",
            "source_type": "csv_import",
            "status": "ready",
            "fields_added_or_updated": ["validity_rules", "service_keys", "country_scope"],
            "validation_rules_json": get_import_template("document_types") or {},
            "preview_count": 0,
            "applied_count": 0,
            "warnings_json": [],
            "workflow_impact": ["request_compliance", "booking_readiness", "documents"],
        },
        {
            "id": "pet_species_breed_pack",
            "pack_key": "pet_species_breed_pack",
            "label": "Pet species and breed pack",
            "description": "Enriches pet species and breed records used by pet/service animal workflows.",
            "target_domain": "pet_species",
            "source_type": "csv_import",
            "status": "ready",
            "fields_added_or_updated": ["iata_live_animal_category", "default_documents"],
            "validation_rules_json": get_import_template("pet_species") or {},
            "preview_count": 0,
            "applied_count": 0,
            "warnings_json": [],
            "workflow_impact": ["request_pets", "offer_feasibility", "booking_readiness"],
        },
        {
            "id": "special_item_handling_pack",
            "pack_key": "special_item_handling_pack",
            "label": "Special item handling pack",
            "description": "Enriches special item categories with handling, fee, and readiness metadata.",
            "target_domain": "special_item_categories",
            "source_type": "csv_import",
            "status": "ready",
            "fields_added_or_updated": ["handling_notes", "fee_expected", "ssr_code"],
            "validation_rules_json": get_import_template("special_item_categories") or {},
            "preview_count": 0,
            "applied_count": 0,
            "warnings_json": [],
            "workflow_impact": ["request_special_items", "offer_fees", "booking_readiness", "future_emd_readiness"],
        },
    ]


async def enrichment_pack_or_default(db: Database, pack_id: str) -> dict[str, Any] | None:
    pack = await db.collection("reference_enrichment_packs").find_one({"id": pack_id})
    if pack:
        return pack
    pack = await db.collection("reference_enrichment_packs").find_one({"pack_key": pack_id})
    if pack:
        return pack
    return next((item for item in default_enrichment_packs() if item["id"] == pack_id or item["pack_key"] == pack_id), None)


@router.get("/enrichment-packs")
async def list_reference_enrichment_packs(
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    custom = await db.collection("reference_enrichment_packs").find_many()
    custom_keys = {item.get("pack_key") for item in custom}
    defaults = [item for item in default_enrichment_packs() if item["pack_key"] not in custom_keys]
    return {
        "items": sorted([*defaults, *custom], key=lambda item: item.get("label") or item.get("pack_key")),
        "description": "Enrichment Packs update selected reference domains with operational metadata used by requests, offers, rules, offer acceptance, booking readiness, and documents.",
        "actor_user_id": user["id"],
    }


@router.post("/enrichment-packs", status_code=status.HTTP_201_CREATED)
async def create_reference_enrichment_pack(
    payload: ReferenceEnrichmentPackCreate,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    if await db.collection("reference_enrichment_packs").find_one({"pack_key": payload.pack_key}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reference enrichment pack already exists.")
    pack = ReferenceEnrichmentPack(
        **payload.model_dump(mode="json"),
        created_by_user_id=user["id"],
    )
    created = await db.collection("reference_enrichment_packs").insert_one(pack.model_dump(mode="json"))
    await audit_reference_event(
        db,
        "reference_enrichment_pack_created",
        "reference_enrichment_pack",
        created["id"],
        f"Reference enrichment pack {created['pack_key']} created.",
        user["id"],
        {"target_domain": created.get("target_domain")},
    )
    return {"pack": created, "actor_user_id": user["id"]}


@router.get("/enrichment-packs/{pack_id}")
async def get_reference_enrichment_pack(
    pack_id: str,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    pack = await enrichment_pack_or_default(db, pack_id)
    if not pack:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference enrichment pack not found.")
    return {"pack": pack, "actor_user_id": user["id"]}


@router.post("/enrichment-packs/{pack_id}/preview")
async def preview_reference_enrichment_pack(
    pack_id: str,
    payload: ReferenceEnrichmentPackPreviewRequest,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    pack = await enrichment_pack_or_default(db, pack_id)
    if not pack:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference enrichment pack not found.")
    csv_text = payload.csv_text or ""
    target_domain = pack["target_domain"]
    if target_domain == "service_catalogue" or get_import_template(target_domain):
        preview = await preview_reference_import(db, target_domain, csv_text, "upsert")
        return {"pack": pack, "preview": preview, "actor_user_id": user["id"]}
    try:
        result = await run_reference_enrichment_import(
            db,
            target_domain,
            csv_text,
            user["id"],
            payload.update_mode,
            True,
            payload.source_label or pack.get("label"),
            payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"pack": pack, "preview": result, "actor_user_id": user["id"]}


@router.post("/enrichment-packs/{pack_id}/apply")
async def apply_reference_enrichment_pack(
    pack_id: str,
    payload: ReferenceEnrichmentPackPreviewRequest,
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    pack = await enrichment_pack_or_default(db, pack_id)
    if not pack:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference enrichment pack not found.")
    csv_text = payload.csv_text or ""
    target_domain = pack["target_domain"]
    if target_domain == "service_catalogue" or get_import_template(target_domain):
        result = await apply_reference_import(db, target_domain, f"{pack['pack_key']}.csv", csv_text, "upsert", user["id"])
        applied_count = result["summary"]["created"] + result["summary"]["updated"]
    else:
        try:
            result = await run_reference_enrichment_import(
                db,
                target_domain,
                csv_text,
                user["id"],
                payload.update_mode,
                False,
                payload.source_label or pack.get("label"),
                payload.notes,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        applied_count = (result.get("report") or {}).get("inserted", 0) + (result.get("report") or {}).get("updated", 0)
    existing = await db.collection("reference_enrichment_packs").find_one({"pack_key": pack["pack_key"]})
    updates = {
        "status": "applied",
        "preview_count": len((result.get("preview") or result.get("report") or {}).get("rows") or []),
        "applied_count": applied_count,
        "applied_by_user_id": user["id"],
        "applied_at": now_utc(),
    }
    if existing:
        pack = await db.collection("reference_enrichment_packs").update_one({"id": existing["id"]}, updates)
    else:
        created_pack = ReferenceEnrichmentPack(
            pack_key=pack["pack_key"],
            label=pack["label"],
            description=pack.get("description"),
            target_domain=target_domain,
            source_type=pack.get("source_type", "csv_import"),
            status="applied",
            fields_added_or_updated=pack.get("fields_added_or_updated") or [],
            validation_rules_json=pack.get("validation_rules_json") or {},
            preview_count=updates["preview_count"],
            applied_count=updates["applied_count"],
            warnings_json=pack.get("warnings_json") or [],
            created_by_user_id=user["id"],
            applied_by_user_id=user["id"],
            applied_at=updates["applied_at"],
        )
        pack = await db.collection("reference_enrichment_packs").insert_one(created_pack.model_dump(mode="json"))
    return {"pack": pack, "result": result, "actor_user_id": user["id"]}


@router.get("/export")
async def export_platform_reference_data(
    export_type: str = Query(default="domain"),
    domain: str = Query(default="countries"),
    format: str = Query(default="json"),
    user: dict = PlatformReferenceOwner,
    db: Database = Depends(get_database),
) -> dict:
    if format not in {"json", "csv"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export format must be json or csv.")
    if export_type == "domain":
        await ensure_supported_domain(db, domain)
        records = [safe_reference_record(item) for item in await db.collection("global_reference_records").find_many({"domain": domain})]
        if format == "csv":
            rows = [country_export_row(record) if domain == "countries" else {
                "domain": record.get("domain"),
                "code": record.get("code"),
                "label": record.get("label"),
                "description": record.get("description") or "",
                "aliases": "|".join(record.get("aliases") or []),
                "sort_order": record.get("sort_order", 100),
                "is_active": record.get("is_active", True),
                "metadata_json": json.dumps(record.get("metadata_json") or {}, default=str),
            } for record in records]
            content = csv_content(rows)
        else:
            content = json.dumps(records, indent=2, default=str)
        filename = f"{domain}_reference_export.{format}"
    elif export_type == "service_catalogue":
        items = await db.collection("service_catalogue").find_many()
        content = csv_content(items) if format == "csv" else json.dumps(items, indent=2, default=str)
        filename = f"service_catalogue_export.{format}"
    elif export_type == "suggestions":
        items = [safe_reference_suggestion(item) for item in await db.collection("reference_data_suggestions").find_many()]
        content = csv_content(items) if format == "csv" else json.dumps(items, indent=2, default=str)
        filename = f"reference_suggestions_export.{format}"
    elif export_type == "import_batches":
        items = [safe_reference_import_batch(item) for item in await db.collection("reference_import_batches").find_many()]
        content = csv_content(items) if format == "csv" else json.dumps(items, indent=2, default=str)
        filename = f"reference_import_batches_export.{format}"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported export type.")
    await audit_reference_event(db, "platform_reference_export_generated", "reference_export", export_type, f"Platform reference {export_type} export generated.", user["id"], {"export_type": export_type, "domain": domain, "format": format})
    return {"format": format, "filename": filename, "content": content, "actor_user_id": user["id"]}
