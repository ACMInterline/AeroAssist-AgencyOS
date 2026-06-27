from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AirlineRulesCore,
    AirlineRulesCorePayload,
    AuditEvent,
    RulesServicesSimulationRequest,
    UnifiedExceptionRule,
    UnifiedExceptionRuleCreate,
    UnifiedExceptionRuleUpdate,
)
from services.exception_engine_service import ExceptionEngineService
from services.rules_and_services_registry import RulesAndServicesRegistry, normalize_code
from services.ssr_osi_generator_service import SsrOsiGeneratorService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/rules-services", tags=["platform-rules-services"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def clean_updates(payload: Any) -> dict[str, Any]:
    return payload.model_dump(mode="json", exclude_unset=True)


def empty_rules_payload(airline_id: str | None, iata_code: str | None = None) -> dict[str, Any]:
    return {
        "airline_id": airline_id,
        "iata_code": iata_code,
        "umnr_rules_json": {},
        "prm_rules_json": {},
        "medical_rules_json": {},
        "pets_service_animals_rules_json": {},
        "pos_rules_json": {},
        "musical_instruments_rules_json": {},
        "weapons_regulated_items_rules_json": {},
        "cargo_oversized_rules_json": {},
        "vip_protocol_rules_json": {},
        "baggage_rules_json": {},
        "seating_rules_json": {},
        "meal_rules_json": {},
        "general_notes": None,
        "source_metadata_json": {},
        "governance_status": "draft",
    }


async def write_rules_audit(
    db: Database,
    actor_user_id: str | None,
    event_type: str,
    entity_type: str,
    entity_id: str,
    summary: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    event = AuditEvent(
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata=metadata or {},
    )
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


@router.get("/airlines/{airline_id}/rules")
async def get_airline_rules(
    airline_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    registry = RulesAndServicesRegistry(db)
    resolved = await registry.resolve_airline(airline_id)
    rules_payload = await registry.get_airline_rules(airline_id)
    rules = rules_payload.get("rules") or empty_rules_payload(resolved.get("airline_id") or airline_id, resolved.get("iata_code"))
    return {"rules": rules, "airline": resolved, "warnings": rules_payload.get("warnings") or [], "actor_user_id": user["id"]}


@router.put("/airlines/{airline_id}/rules")
async def put_airline_rules(
    airline_id: str,
    payload: AirlineRulesCorePayload,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    registry = RulesAndServicesRegistry(db)
    resolved = await registry.resolve_airline(airline_id)
    data = payload.model_dump(mode="json")
    canonical_airline_id = data.get("airline_id") or resolved.get("airline_id") or airline_id
    data["airline_id"] = canonical_airline_id
    data["iata_code"] = normalize_code(data.get("iata_code") or resolved.get("iata_code"))
    existing = await db.collection("airline_rules_core").find_one({"airline_id": canonical_airline_id})
    if existing is None and data.get("iata_code"):
        existing = await db.collection("airline_rules_core").find_one({"iata_code": data["iata_code"]})
    if existing:
        updates = {**data, "updated_by_user_id": user["id"]}
        updated = await db.collection("airline_rules_core").update_one({"id": existing["id"]}, updates)
        event_type = "airline_rules_core.updated"
        rules = updated
    else:
        rules_model = AirlineRulesCore(**data, created_by_user_id=user["id"], updated_by_user_id=user["id"])
        rules = await db.collection("airline_rules_core").insert_one(rules_model.model_dump(mode="json"))
        event_type = "airline_rules_core.created"
    await write_rules_audit(db, user["id"], event_type, "airline_rules_core", rules["id"], f"Saved airline rules for {data.get('iata_code') or canonical_airline_id}.")
    return {"rules": rules, "airline": resolved, "actor_user_id": user["id"]}


@router.get("/exception-rules")
async def list_exception_rules(
    category: Optional[str] = Query(default=None),
    airline_id: Optional[str] = Query(default=None),
    active: Optional[bool] = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    filters: dict[str, Any] = {}
    if category:
        filters["category"] = normalize_code(category)
    if active is not None:
        filters["active"] = active
    items = await db.collection("unified_exception_rules").find_many(filters or None)
    if airline_id:
        resolved = await RulesAndServicesRegistry(db).resolve_airline(airline_id)
        airline_ids = {airline_id, resolved.get("airline_id")}
        iata_codes = {normalize_code(airline_id), resolved.get("iata_code")}
        items = [
            item
            for item in items
            if not item.get("airline_id") and not item.get("iata_code")
            or item.get("airline_id") in airline_ids
            or normalize_code(item.get("iata_code")) in iata_codes
        ]
    items.sort(key=lambda item: (item.get("category") or "", item.get("priority", 100)))
    return {"items": items, "actor_user_id": user["id"]}


@router.post("/exception-rules", status_code=status.HTTP_201_CREATED)
async def create_exception_rule(
    payload: UnifiedExceptionRuleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    data = payload.model_dump(mode="json")
    data["iata_code"] = normalize_code(data.get("iata_code"))
    data["route_origin"] = normalize_code(data.get("route_origin"))
    data["route_destination"] = normalize_code(data.get("route_destination"))
    data["airport_code"] = normalize_code(data.get("airport_code"))
    data["aircraft_type"] = normalize_code(data.get("aircraft_type"))
    rule = UnifiedExceptionRule(**data)
    created = await db.collection("unified_exception_rules").insert_one(rule.model_dump(mode="json"))
    await write_rules_audit(db, user["id"], "unified_exception_rule.created", "unified_exception_rule", created["id"], "Created unified exception rule.")
    return {"rule": created, "actor_user_id": user["id"]}


@router.put("/exception-rules/{rule_id}")
async def update_exception_rule(
    rule_id: str,
    payload: UnifiedExceptionRuleUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    existing = await db.collection("unified_exception_rules").find_one({"id": rule_id})
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exception rule not found.")
    updates = clean_updates(payload)
    for key in ["iata_code", "route_origin", "route_destination", "airport_code", "aircraft_type"]:
        if key in updates:
            updates[key] = normalize_code(updates.get(key))
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    updated = await db.collection("unified_exception_rules").update_one({"id": rule_id}, updates)
    await write_rules_audit(db, user["id"], "unified_exception_rule.updated", "unified_exception_rule", rule_id, "Updated unified exception rule.", {"fields": sorted(updates.keys())})
    return {"rule": updated, "actor_user_id": user["id"]}


@router.post("/simulate")
async def simulate_rules_services(
    payload: RulesServicesSimulationRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    context = payload.model_dump(mode="json")
    context["iata_code"] = normalize_code(context.get("iata_code"))
    context["route_origin"] = normalize_code(context.get("route_origin"))
    context["route_destination"] = normalize_code(context.get("route_destination"))
    context["aircraft_type"] = normalize_code(context.get("aircraft_type"))
    evaluation = await ExceptionEngineService(db).evaluate(context)
    preview = await SsrOsiGeneratorService(db).generate(context, evaluation)
    return {
        "allowed": evaluation.get("allowed"),
        "actions": evaluation.get("actions"),
        "warnings": evaluation.get("warnings"),
        "required_documents": preview.get("required_documents"),
        "policy_violations": evaluation.get("policy_violations"),
        "rules_fired": evaluation.get("rules_fired"),
        "confidence": evaluation.get("confidence"),
        "fallback_used": evaluation.get("fallback_used"),
        "ssr_preview": preview.get("ssr"),
        "osi_preview": preview.get("osi"),
        "blocked": preview.get("blocked"),
        "rules_context": evaluation.get("rules_context"),
        "actor_user_id": user["id"],
    }
