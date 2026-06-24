from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user, require_platform_role
from database import Database, get_database
from models import (
    AgencyFormFieldSettingsUpdate,
    AgencyFormProfile,
    AgencyFormProfileCreate,
    AgencyFormProfileUpdate,
    GlobalFieldDefinition,
    GlobalFieldDefinitionCreate,
    GlobalFieldDefinitionUpdate,
)
from services.form_profile_service import (
    ADMIN_CONTEXTS,
    PORTAL_CONTEXTS,
    PUBLIC_CONTEXTS,
    audit_form_profile_event,
    bootstrap_global_field_definitions,
    ensure_default_form_profiles,
    get_profile_or_404,
    replace_form_field_settings,
    resolve_effective_form_profile,
    safe_form_profile,
    safe_global_field_definition,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/form-profiles", tags=["form-profiles"])
agency_router = APIRouter(prefix="/api/agencies/{agency_id}/form-profiles", tags=["agency-form-profiles"])
public_router = APIRouter(prefix="/api/public/form-profiles", tags=["public-form-profiles"])

READ_ROLES = {"agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"}
WRITE_ROLES = {"agency_owner", "agency_admin"}


async def require_form_profile_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_form_profile_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


async def workspace_for_agency(db: Database, agency_id: str) -> dict | None:
    return await db.collection("agency_workspaces").find_one({"agency_id": agency_id})


async def ensure_profile_key_available(db: Database, agency_id: str, profile_key: str, profile_id: str | None = None) -> None:
    existing = await db.collection("agency_form_profiles").find_one({"agency_id": agency_id, "profile_key": profile_key})
    if existing and existing["id"] != profile_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Form profile key already exists.")


async def clear_default_for_context(db: Database, agency_id: str, form_context: str, except_profile_id: str | None = None) -> None:
    for profile in await db.collection("agency_form_profiles").find_many({"agency_id": agency_id, "form_context": form_context, "is_default": True}):
        if profile["id"] != except_profile_id:
            await db.collection("agency_form_profiles").update_one({"id": profile["id"]}, {"is_default": False})


@router.get("/field-definitions")
async def list_field_definitions(
    include_inactive: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    records = await db.collection("global_field_definitions").find_many()
    items = [safe_global_field_definition(item) for item in records if include_inactive or item.get("is_active", True)]
    items = sorted(items, key=lambda item: (item.get("field_family", ""), item.get("default_display_order", 100), item.get("field_key", "")))
    return {"items": items, "actor_user_id": user["id"]}


@router.post("/field-definitions/bootstrap")
async def bootstrap_field_definitions(
    user: dict = Depends(require_platform_role(["platform_owner", "platform_admin"])),
    db: Database = Depends(get_database),
) -> dict:
    result = await bootstrap_global_field_definitions(db, user["id"])
    await audit_form_profile_event(db, "global_field_definition_updated", "global_field_definition", "phase_34_1_bootstrap", "Global field definitions bootstrap executed.", user["id"], metadata=result)
    return {"ok": True, "bootstrap": result, "actor_user_id": user["id"]}


@router.post("/field-definitions", status_code=status.HTTP_201_CREATED)
async def create_field_definition(
    payload: GlobalFieldDefinitionCreate,
    user: dict = Depends(require_platform_role(["platform_owner", "platform_admin"])),
    db: Database = Depends(get_database),
) -> dict:
    existing = await db.collection("global_field_definitions").find_one({"field_key": payload.field_key})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Global field definition already exists.")
    created = await db.collection("global_field_definitions").insert_one(GlobalFieldDefinition(**payload.model_dump(mode="json")).model_dump(mode="json"))
    await audit_form_profile_event(db, "global_field_definition_created", "global_field_definition", created["id"], f"Global field definition {created['field_key']} created.", user["id"], metadata={"field_key": created["field_key"]})
    return {"field": safe_global_field_definition(created), "actor_user_id": user["id"]}


@router.put("/field-definitions/{field_id}")
async def update_field_definition(
    field_id: str,
    payload: GlobalFieldDefinitionUpdate,
    user: dict = Depends(require_platform_role(["platform_owner", "platform_admin"])),
    db: Database = Depends(get_database),
) -> dict:
    existing = await db.collection("global_field_definitions").find_one({"id": field_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Global field definition not found.")
    updates = {key: value for key, value in payload.model_dump(mode="json", exclude_unset=True).items() if value is not None}
    updated = await db.collection("global_field_definitions").update_one({"id": field_id}, updates)
    await audit_form_profile_event(db, "global_field_definition_updated", "global_field_definition", field_id, f"Global field definition {existing['field_key']} updated.", user["id"], metadata={"fields": sorted(updates.keys())})
    return {"field": safe_global_field_definition(updated), "actor_user_id": user["id"]}


@agency_router.get("")
async def list_agency_form_profiles(
    agency_id: str,
    ensure_defaults: bool = Query(default=True),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_form_profile_read(db, agency_id, user)
    if ensure_defaults:
        workspace = await workspace_for_agency(db, agency_id)
        await ensure_default_form_profiles(db, agency_id, workspace.get("id") if workspace else None, user["id"])
    profiles = await db.collection("agency_form_profiles").find_many({"agency_id": agency_id})
    return {"items": sorted([safe_form_profile(item) for item in profiles], key=lambda item: (item.get("form_context", ""), item.get("name", ""))), "actor_user_id": user["id"]}


@agency_router.post("", status_code=status.HTTP_201_CREATED)
async def create_agency_form_profile(
    agency_id: str,
    payload: AgencyFormProfileCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_form_profile_write(db, agency_id, user)
    await ensure_profile_key_available(db, agency_id, payload.profile_key)
    data = payload.model_dump(mode="json")
    if data.get("is_default"):
        await clear_default_for_context(db, agency_id, data["form_context"])
    created = await db.collection("agency_form_profiles").insert_one(AgencyFormProfile(agency_id=agency_id, created_by_user_id=user["id"], **data).model_dump(mode="json"))
    await audit_form_profile_event(db, "agency_form_profile_created", "agency_form_profile", created["id"], f"Agency form profile {created['profile_key']} created.", user["id"], agency_id, {"form_context": created["form_context"]})
    return {"profile": safe_form_profile(created), "actor_user_id": user["id"]}


@agency_router.get("/{profile_id}")
async def get_agency_form_profile(
    agency_id: str,
    profile_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_form_profile_read(db, agency_id, user)
    profile = await get_profile_or_404(db, agency_id, profile_id)
    fields = await db.collection("agency_form_field_settings").find_many({"agency_id": agency_id, "form_profile_id": profile_id})
    return {"profile": safe_form_profile(profile), "field_settings": fields, "actor_user_id": user["id"]}


@agency_router.put("/{profile_id}")
async def update_agency_form_profile(
    agency_id: str,
    profile_id: str,
    payload: AgencyFormProfileUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_form_profile_write(db, agency_id, user)
    existing = await get_profile_or_404(db, agency_id, profile_id)
    updates = {key: value for key, value in payload.model_dump(mode="json", exclude_unset=True).items() if value is not None}
    if "profile_key" in updates:
        await ensure_profile_key_available(db, agency_id, updates["profile_key"], profile_id)
    context = updates.get("form_context") or existing["form_context"]
    if updates.get("is_default") is True:
        await clear_default_for_context(db, agency_id, context, profile_id)
    updated = await db.collection("agency_form_profiles").update_one({"id": profile_id}, updates)
    await audit_form_profile_event(db, "agency_form_profile_updated", "agency_form_profile", profile_id, f"Agency form profile {existing['profile_key']} updated.", user["id"], agency_id, {"fields": sorted(updates.keys())})
    return {"profile": safe_form_profile(updated), "actor_user_id": user["id"]}


@agency_router.get("/{profile_id}/effective")
async def get_effective_agency_form_profile(
    agency_id: str,
    profile_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_form_profile_read(db, agency_id, user)
    result = await resolve_effective_form_profile(db, agency_id, profile_id=profile_id)
    return {**result, "actor_user_id": user["id"]}


@agency_router.put("/{profile_id}/fields")
async def update_agency_form_fields(
    agency_id: str,
    profile_id: str,
    payload: AgencyFormFieldSettingsUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_form_profile_write(db, agency_id, user)
    profile = await get_profile_or_404(db, agency_id, profile_id)
    result = await replace_form_field_settings(db, agency_id, profile, payload.fields, user["id"])
    effective = await resolve_effective_form_profile(db, agency_id, profile_id=profile_id)
    return {**result, "effective": effective, "actor_user_id": user["id"]}


@public_router.get("/effective")
async def public_effective_form_profile(
    agency_id: str = Query(...),
    form_context: str = Query(default="public_request"),
    db: Database = Depends(get_database),
) -> dict:
    if form_context not in PUBLIC_CONTEXTS and form_context not in PORTAL_CONTEXTS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only public-safe or portal-safe effective profiles are available publicly.")
    result = await resolve_effective_form_profile(db, agency_id, form_context=form_context)
    safe_fields = [field for field in result.get("fields", []) if field.get("visible") and (field.get("public_safe") or field.get("portal_safe"))]
    sections = []
    for field in safe_fields:
        section = next((item for item in sections if item["section_key"] == field["section_key"]), None)
        if not section:
            section = {"section_key": field["section_key"], "section_label": field.get("section_label"), "fields": []}
            sections.append(section)
        section["fields"].append(field)
    return {"profile": result.get("profile"), "fields": safe_fields, "sections": sections, "fallback": result.get("fallback", False)}
