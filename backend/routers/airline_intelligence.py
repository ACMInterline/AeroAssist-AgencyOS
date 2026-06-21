from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AgencyAirlineOverride,
    AgencyAirlineOverrideCreate,
    AgencyAirlineOverrideUpdate,
    AirlineEmdRuleNote,
    AirlineEmdRuleNoteCreate,
    AirlineEmdRuleNoteUpdate,
    AirlineKnowledgeItem,
    AirlineKnowledgeItemCreate,
    AirlineKnowledgeItemUpdate,
    AirlineKnowledgeSource,
    AirlineKnowledgeSourceCreate,
    AirlineKnowledgeUsageEvent,
    AirlineKnowledgeUsageEventCreate,
    AirlineProcedure,
    AirlineProcedureCreate,
    AirlineProcedureUpdate,
    AirlineProfile,
    AirlineProfileCreate,
    AirlineProfileUpdate,
    AuditEvent,
)
from services.tenant_service import assert_agency_access, require_any_agency_role, require_any_platform_role

router = APIRouter(tags=["airline-intelligence"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]
AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
AGENCY_OVERRIDE_ROLES = ["agency_owner", "agency_admin"]
PUBLISHED_STATUSES = {"verified", "published"}


def clean_updates(payload: Any) -> dict:
    return payload.model_dump(exclude_unset=True, mode="json")


def contains(value: Any, needle: str) -> bool:
    if value is None:
        return False
    if isinstance(value, list):
        return any(contains(item, needle) for item in value)
    return needle in str(value).lower()


async def write_audit(db: Database, actor_user_id: str, event_type: str, entity_type: str, entity_id: str, summary: str, agency_id: str | None = None, metadata: dict | None = None) -> None:
    event = AuditEvent(
        agency_id=agency_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata=metadata or {},
    )
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


async def require_agency_override_write(db: Database, agency_id: str, user: dict) -> None:
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_OVERRIDE_ROLES)


async def get_airline_or_404(db: Database, airline_id: str) -> dict:
    airline = await db.collection("airline_profiles").find_one({"id": airline_id})
    if airline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Airline profile not found.")
    return airline


async def get_knowledge_or_404(db: Database, knowledge_id: str) -> dict:
    item = await db.collection("airline_knowledge_items").find_one({"id": knowledge_id})
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Airline knowledge item not found.")
    return item


async def get_target_or_404(db: Database, target_type: str, target_id: str) -> dict:
    collection_by_type = {
        "airline_profile": "airline_profiles",
        "knowledge_item": "airline_knowledge_items",
        "procedure": "airline_procedures",
        "emd_rule_note": "airline_emd_rule_notes",
        "source": "airline_knowledge_sources",
    }
    collection = collection_by_type.get(target_type)
    if not collection:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported override target type.")
    target = await db.collection(collection).find_one({"id": target_id})
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Override target not found.")
    return target


def is_agency_visible(record: dict) -> bool:
    return record.get("review_status") in PUBLISHED_STATUSES


def matches_airline(record: dict, airline: dict, query: Optional[str]) -> bool:
    if not query:
        return True
    needle = query.lower()
    return any(contains(record.get(field), needle) for field in ["title", "summary", "detailed_text", "service_code", "tags", "category"]) or any(
        contains(airline.get(field), needle) for field in ["airline_code", "icao_code", "airline_name", "country", "alliance"]
    )


async def source_map(db: Database, source_ids: list[str]) -> dict:
    if not source_ids:
        return {}
    sources = await db.collection("airline_knowledge_sources").find_many()
    return {source["id"]: source for source in sources if source["id"] in set(source_ids)}


async def active_overrides(db: Database, agency_id: str, airline_id: str, target_type: str | None = None, target_id: str | None = None) -> list[dict]:
    filters = {"agency_id": agency_id, "airline_id": airline_id, "status": "active"}
    if target_type:
        filters["target_type"] = target_type
    if target_id:
        filters["target_id"] = target_id
    return await db.collection("agency_airline_overrides").find_many(filters)


def merge_override_text(base_text: str, overrides: list[dict]) -> dict:
    active = [override for override in overrides if override.get("status") == "active"]
    replacement = next((override for override in active if override.get("override_mode") == "replace"), None)
    augmentations = [override for override in active if override.get("override_mode") == "augment"]
    annotations = [override for override in active if override.get("override_mode") == "annotate"]
    if replacement:
        merged_text = replacement.get("override_text") or base_text
        mode = "replace"
    else:
        extras = [override.get("override_text") for override in augmentations if override.get("override_text")]
        merged_text = "\n\n".join([part for part in [base_text, *extras] if part])
        mode = "augment" if augmentations else "global"
    return {
        "merged_text": merged_text,
        "override_mode_applied": mode,
        "annotations": annotations,
        "has_internal_warning": any(override.get("internal_warning") for override in active),
        "overrides": active,
    }


async def enrich_knowledge_for_agency(db: Database, agency_id: str, item: dict, airline: dict | None = None) -> dict:
    overrides = await active_overrides(db, agency_id, item["airline_id"], "knowledge_item", item["id"])
    source_lookup = await source_map(db, item.get("source_ids", []))
    merged = merge_override_text(item.get("detailed_text") or "", overrides)
    return {
        **item,
        "airline": airline or await get_airline_or_404(db, item["airline_id"]),
        "sources": [source_lookup[source_id] for source_id in item.get("source_ids", []) if source_id in source_lookup],
        "agency_override": merged,
        "decision_support_notice": "Decision support, verify before action.",
    }


@router.get("/api/platform/airlines")
async def list_platform_airlines(
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    items = await db.collection("airline_profiles").find_many({"status": status_filter} if status_filter else None)
    if search:
        needle = search.lower()
        items = [item for item in items if any(contains(item.get(field), needle) for field in ["airline_code", "icao_code", "airline_name", "country", "alliance", "notes"])]
    items.sort(key=lambda item: item.get("airline_code", ""))
    return {"items": items}


@router.post("/api/platform/airlines", status_code=status.HTTP_201_CREATED)
async def create_platform_airline(payload: AirlineProfileCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_write(user)
    code = payload.airline_code.upper()
    existing = await db.collection("airline_profiles").find_one({"airline_code": code})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Airline code already exists.")
    airline = AirlineProfile(**{**payload.model_dump(mode="json"), "airline_code": code})
    created = await db.collection("airline_profiles").insert_one(airline.model_dump(mode="json"))
    await write_audit(db, user["id"], "airline.created", "airline_profile", airline.id, f"Created airline {code}.")
    return {"airline": created}


@router.get("/api/platform/airlines/{airline_id}")
async def get_platform_airline(airline_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_read(user)
    airline = await get_airline_or_404(db, airline_id)
    return {
        "airline": airline,
        "knowledge": await db.collection("airline_knowledge_items").find_many({"airline_id": airline_id}),
        "procedures": await db.collection("airline_procedures").find_many({"airline_id": airline_id}),
        "emd_notes": await db.collection("airline_emd_rule_notes").find_many({"airline_id": airline_id}),
        "sources": await db.collection("airline_knowledge_sources").find_many({"airline_id": airline_id}),
    }


@router.put("/api/platform/airlines/{airline_id}")
async def update_platform_airline(airline_id: str, payload: AirlineProfileUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_write(user)
    await get_airline_or_404(db, airline_id)
    updates = clean_updates(payload)
    if "airline_code" in updates:
        updates["airline_code"] = updates["airline_code"].upper()
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    updated = await db.collection("airline_profiles").update_one({"id": airline_id}, updates)
    await write_audit(db, user["id"], "airline.updated", "airline_profile", airline_id, "Updated airline profile.", metadata={"fields": sorted(updates.keys())})
    return {"airline": updated}


@router.get("/api/platform/airlines/{airline_id}/knowledge")
async def list_platform_knowledge(airline_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_read(user)
    await get_airline_or_404(db, airline_id)
    return {"items": await db.collection("airline_knowledge_items").find_many({"airline_id": airline_id})}


@router.post("/api/platform/airlines/{airline_id}/knowledge", status_code=status.HTTP_201_CREATED)
async def create_platform_knowledge(airline_id: str, payload: AirlineKnowledgeItemCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_write(user)
    await get_airline_or_404(db, airline_id)
    item = AirlineKnowledgeItem(airline_id=airline_id, created_by_user_id=user["id"], **payload.model_dump(mode="json"))
    created = await db.collection("airline_knowledge_items").insert_one(item.model_dump(mode="json"))
    await write_audit(db, user["id"], "airline_knowledge.created", "airline_knowledge_item", item.id, f"Created knowledge item {item.title}.")
    return {"knowledge": created}


@router.get("/api/platform/airline-knowledge/{knowledge_id}")
async def get_platform_knowledge(knowledge_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_read(user)
    item = await get_knowledge_or_404(db, knowledge_id)
    airline = await get_airline_or_404(db, item["airline_id"])
    sources = await source_map(db, item.get("source_ids", []))
    return {"knowledge": item, "airline": airline, "sources": [sources[source_id] for source_id in item.get("source_ids", []) if source_id in sources]}


@router.put("/api/platform/airline-knowledge/{knowledge_id}")
async def update_platform_knowledge(knowledge_id: str, payload: AirlineKnowledgeItemUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_write(user)
    await get_knowledge_or_404(db, knowledge_id)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    updated = await db.collection("airline_knowledge_items").update_one({"id": knowledge_id}, updates)
    await write_audit(db, user["id"], "airline_knowledge.updated", "airline_knowledge_item", knowledge_id, "Updated knowledge item.", metadata={"fields": sorted(updates.keys())})
    return {"knowledge": updated}


@router.post("/api/platform/airline-knowledge/{knowledge_id}/publish")
async def publish_platform_knowledge(knowledge_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_write(user)
    await get_knowledge_or_404(db, knowledge_id)
    updated = await db.collection("airline_knowledge_items").update_one({"id": knowledge_id}, {"review_status": "published", "reviewed_by_user_id": user["id"], "published_at": datetime.now(timezone.utc)})
    await write_audit(db, user["id"], "airline_knowledge.published", "airline_knowledge_item", knowledge_id, "Published knowledge item.")
    return {"knowledge": updated}


@router.post("/api/platform/airline-knowledge/{knowledge_id}/archive")
async def archive_platform_knowledge(knowledge_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_write(user)
    await get_knowledge_or_404(db, knowledge_id)
    updated = await db.collection("airline_knowledge_items").update_one({"id": knowledge_id}, {"review_status": "archived"})
    await write_audit(db, user["id"], "airline_knowledge.archived", "airline_knowledge_item", knowledge_id, "Archived knowledge item.")
    return {"knowledge": updated}


@router.get("/api/platform/airlines/{airline_id}/procedures")
async def list_platform_procedures(airline_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_read(user)
    await get_airline_or_404(db, airline_id)
    return {"items": await db.collection("airline_procedures").find_many({"airline_id": airline_id})}


@router.post("/api/platform/airlines/{airline_id}/procedures", status_code=status.HTTP_201_CREATED)
async def create_platform_procedure(airline_id: str, payload: AirlineProcedureCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_write(user)
    await get_airline_or_404(db, airline_id)
    procedure = AirlineProcedure(airline_id=airline_id, **payload.model_dump(mode="json"))
    created = await db.collection("airline_procedures").insert_one(procedure.model_dump(mode="json"))
    await write_audit(db, user["id"], "airline_procedure.created", "airline_procedure", procedure.id, f"Created procedure {procedure.title}.")
    return {"procedure": created}


@router.put("/api/platform/airline-procedures/{procedure_id}")
async def update_platform_procedure(procedure_id: str, payload: AirlineProcedureUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_write(user)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    updated = await db.collection("airline_procedures").update_one({"id": procedure_id}, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Airline procedure not found.")
    await write_audit(db, user["id"], "airline_procedure.updated", "airline_procedure", procedure_id, "Updated procedure.")
    return {"procedure": updated}


@router.get("/api/platform/airlines/{airline_id}/emd-notes")
async def list_platform_emd_notes(airline_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_read(user)
    await get_airline_or_404(db, airline_id)
    return {"items": await db.collection("airline_emd_rule_notes").find_many({"airline_id": airline_id})}


@router.post("/api/platform/airlines/{airline_id}/emd-notes", status_code=status.HTTP_201_CREATED)
async def create_platform_emd_note(airline_id: str, payload: AirlineEmdRuleNoteCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_write(user)
    await get_airline_or_404(db, airline_id)
    note = AirlineEmdRuleNote(airline_id=airline_id, **payload.model_dump(mode="json"))
    created = await db.collection("airline_emd_rule_notes").insert_one(note.model_dump(mode="json"))
    await write_audit(db, user["id"], "airline_emd_note.created", "airline_emd_rule_note", note.id, f"Created EMD note {note.service_code}.")
    return {"emd_note": created}


@router.put("/api/platform/airline-emd-notes/{emd_note_id}")
async def update_platform_emd_note(emd_note_id: str, payload: AirlineEmdRuleNoteUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_write(user)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    updated = await db.collection("airline_emd_rule_notes").update_one({"id": emd_note_id}, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Airline EMD note not found.")
    await write_audit(db, user["id"], "airline_emd_note.updated", "airline_emd_rule_note", emd_note_id, "Updated EMD note.")
    return {"emd_note": updated}


@router.get("/api/platform/airline-sources")
async def list_platform_sources(airline_id: Optional[str] = None, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_read(user)
    return {"items": await db.collection("airline_knowledge_sources").find_many({"airline_id": airline_id} if airline_id else None)}


@router.post("/api/platform/airline-sources", status_code=status.HTTP_201_CREATED)
async def create_platform_source(payload: AirlineKnowledgeSourceCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_platform_write(user)
    if payload.airline_id:
        await get_airline_or_404(db, payload.airline_id)
    source = AirlineKnowledgeSource(captured_by_user_id=user["id"], **payload.model_dump(mode="json"))
    created = await db.collection("airline_knowledge_sources").insert_one(source.model_dump(mode="json"))
    await write_audit(db, user["id"], "airline_source.created", "airline_knowledge_source", source.id, f"Created source {source.title}.")
    return {"source": created}


@router.get("/api/agencies/{agency_id}/airline-intelligence/search")
async def agency_airline_search(
    agency_id: str,
    q: Optional[str] = Query(default=None),
    airline: Optional[str] = None,
    airline_id: Optional[str] = None,
    category: Optional[str] = None,
    service_code: Optional[str] = None,
    confidence: Optional[str] = None,
    tag: Optional[str] = None,
    review_status: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    airlines = await db.collection("airline_profiles").find_many()
    airline_by_id = {item["id"]: item for item in airlines}
    visible = []
    for item in await db.collection("airline_knowledge_items").find_many():
        airline_record = airline_by_id.get(item["airline_id"])
        if not airline_record or not is_agency_visible(item):
            continue
        if airline_id and item["airline_id"] != airline_id:
            continue
        if airline:
            needle = airline.lower()
            if not (contains(airline_record.get("airline_code"), needle) or contains(airline_record.get("airline_name"), needle)):
                continue
        if category and item.get("category") != category:
            continue
        if service_code and (item.get("service_code") or "").lower() != service_code.lower():
            continue
        if confidence and item.get("confidence") != confidence:
            continue
        if tag and tag.lower() not in [str(value).lower() for value in item.get("tags", [])]:
            continue
        if review_status and item.get("review_status") != review_status:
            continue
        if not matches_airline(item, airline_record, q):
            continue
        overrides = await active_overrides(db, agency_id, item["airline_id"], "knowledge_item", item["id"])
        visible.append({**item, "airline": airline_record, "has_agency_override": bool(overrides), "agency_override_modes": [override["override_mode"] for override in overrides]})
    visible.sort(key=lambda item: (item.get("airline", {}).get("airline_code", ""), item.get("category", ""), item.get("title", "")))
    return {"items": visible, "decision_support_notice": "Decision support, verify before action."}


@router.get("/api/agencies/{agency_id}/airlines/{airline_id}/intelligence")
async def agency_airline_detail(agency_id: str, airline_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_agency_read(db, agency_id, user)
    airline = await get_airline_or_404(db, airline_id)
    knowledge = [await enrich_knowledge_for_agency(db, agency_id, item, airline) for item in await db.collection("airline_knowledge_items").find_many({"airline_id": airline_id}) if is_agency_visible(item)]
    procedures = [item for item in await db.collection("airline_procedures").find_many({"airline_id": airline_id}) if is_agency_visible(item)]
    emd_notes = [item for item in await db.collection("airline_emd_rule_notes").find_many({"airline_id": airline_id}) if is_agency_visible(item)]
    overrides = await active_overrides(db, agency_id, airline_id)
    return {
        "airline": airline,
        "knowledge": knowledge,
        "procedures": procedures,
        "emd_notes": emd_notes,
        "sources": await db.collection("airline_knowledge_sources").find_many({"airline_id": airline_id}),
        "overrides": overrides,
        "decision_support_notice": "Decision support, verify before action.",
    }


@router.get("/api/agencies/{agency_id}/airline-knowledge/{knowledge_id}")
async def agency_knowledge_detail(agency_id: str, knowledge_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_agency_read(db, agency_id, user)
    item = await get_knowledge_or_404(db, knowledge_id)
    if not is_agency_visible(item):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published airline knowledge item not found.")
    return {"knowledge": await enrich_knowledge_for_agency(db, agency_id, item)}


@router.get("/api/agencies/{agency_id}/airlines/{airline_id}/overrides")
async def list_agency_overrides(agency_id: str, airline_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_agency_read(db, agency_id, user)
    await get_airline_or_404(db, airline_id)
    return {"items": await db.collection("agency_airline_overrides").find_many({"agency_id": agency_id, "airline_id": airline_id})}


@router.post("/api/agencies/{agency_id}/airlines/{airline_id}/overrides", status_code=status.HTTP_201_CREATED)
async def create_agency_override(agency_id: str, airline_id: str, payload: AgencyAirlineOverrideCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_agency_override_write(db, agency_id, user)
    await get_airline_or_404(db, airline_id)
    target = await get_target_or_404(db, payload.target_type, payload.target_id)
    if target.get("airline_id", airline_id) != airline_id and payload.target_type != "source":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Override target must belong to the airline.")
    override = AgencyAirlineOverride(agency_id=agency_id, airline_id=airline_id, created_by_user_id=user["id"], **payload.model_dump(mode="json"))
    created = await db.collection("agency_airline_overrides").insert_one(override.model_dump(mode="json"))
    await write_audit(db, user["id"], "agency_airline_override.created", "agency_airline_override", override.id, "Created agency airline override.", agency_id=agency_id)
    return {"override": created}


@router.put("/api/agencies/{agency_id}/airline-overrides/{override_id}")
async def update_agency_override(agency_id: str, override_id: str, payload: AgencyAirlineOverrideUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_agency_override_write(db, agency_id, user)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    updated = await db.collection("agency_airline_overrides").update_one({"agency_id": agency_id, "id": override_id}, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency override not found.")
    await write_audit(db, user["id"], "agency_airline_override.updated", "agency_airline_override", override_id, "Updated agency airline override.", agency_id=agency_id)
    return {"override": updated}


@router.post("/api/agencies/{agency_id}/airline-overrides/{override_id}/archive")
async def archive_agency_override(agency_id: str, override_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_agency_override_write(db, agency_id, user)
    updated = await db.collection("agency_airline_overrides").update_one({"agency_id": agency_id, "id": override_id}, {"status": "archived"})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency override not found.")
    await write_audit(db, user["id"], "agency_airline_override.archived", "agency_airline_override", override_id, "Archived agency airline override.", agency_id=agency_id)
    return {"override": updated}


@router.post("/api/agencies/{agency_id}/airline-knowledge/{knowledge_id}/usage", status_code=status.HTTP_201_CREATED)
async def record_agency_knowledge_usage(agency_id: str, knowledge_id: str, payload: AirlineKnowledgeUsageEventCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_agency_read(db, agency_id, user)
    item = await get_knowledge_or_404(db, knowledge_id)
    if not is_agency_visible(item):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published airline knowledge item not found.")
    event = AirlineKnowledgeUsageEvent(
        agency_id=agency_id,
        airline_id=item["airline_id"],
        target_type="knowledge_item",
        target_id=knowledge_id,
        actor_user_id=user["id"],
        **payload.model_dump(mode="json"),
    )
    created = await db.collection("airline_knowledge_usage_events").insert_one(event.model_dump(mode="json"))
    await write_audit(db, user["id"], "airline_knowledge.used", "airline_knowledge_item", knowledge_id, "Recorded airline knowledge usage.", agency_id=agency_id, metadata={"usage_event_id": event.id})
    return {"usage_event": created}
