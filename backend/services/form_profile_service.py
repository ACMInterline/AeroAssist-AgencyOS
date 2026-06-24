from typing import Any

from fastapi import HTTPException, status

from database import Database
from models import (
    AgencyFormFieldSetting,
    AgencyFormFieldSettingInput,
    AgencyFormProfile,
    AuditEvent,
    GlobalFieldDefinition,
    now_utc,
)


PUBLIC_CONTEXTS = {"public_request", "offer_client_view", "offer_pdf"}
PORTAL_CONTEXTS = {"portal_request"}
ADMIN_CONTEXTS = {"admin_request", "trip_intake", "service_specific"}

FIELD_FAMILY_LABELS = {
    "contact": "Contact",
    "client_context": "Client context",
    "passenger": "Passengers",
    "itinerary_segment": "Trip / Itinerary",
    "service": "Services",
    "pet": "Pets",
    "special_item": "Special Items",
    "document": "Documents",
    "pricing": "Pricing",
    "offer_display": "Offer Display",
    "consent": "Consent",
    "internal_admin": "Internal",
}

DEFAULT_FORM_PROFILES = [
    {"profile_key": "public_request_default", "name": "Public Request", "form_context": "public_request", "is_default": True},
    {"profile_key": "portal_request_default", "name": "Portal Request", "form_context": "portal_request", "is_default": True},
    {"profile_key": "admin_request_default", "name": "Admin Request", "form_context": "admin_request", "is_default": True},
    {"profile_key": "offer_client_view_default", "name": "Offer Client View", "form_context": "offer_client_view", "is_default": True},
    {"profile_key": "offer_pdf_default", "name": "Offer PDF", "form_context": "offer_pdf", "is_default": True},
]

DEFAULT_FIELD_DEFINITIONS = [
    {"field_key": "contact.first_name", "canonical_path": "contact.first_name", "field_family": "contact", "field_type": "text", "label": "First name", "required_level": "system_required", "public_safe": True, "portal_safe": True, "can_be_hidden_by_agency": False, "default_display_order": 10},
    {"field_key": "contact.last_name", "canonical_path": "contact.last_name", "field_family": "contact", "field_type": "text", "label": "Last name", "required_level": "recommended", "public_safe": True, "portal_safe": True, "default_display_order": 20},
    {"field_key": "contact.email", "canonical_path": "contact.email", "field_family": "contact", "field_type": "email", "label": "Email", "help_text": "At least one contact method is required.", "required_level": "system_required", "public_safe": True, "portal_safe": True, "can_be_hidden_by_agency": False, "default_display_order": 30},
    {"field_key": "contact.phone", "canonical_path": "contact.phone", "field_family": "contact", "field_type": "phone", "label": "Phone", "help_text": "At least one contact method is required.", "required_level": "system_required", "public_safe": True, "portal_safe": True, "can_be_hidden_by_agency": False, "default_display_order": 40},
    {"field_key": "contact.preferred_contact_channel", "canonical_path": "contact.preferred_contact_channel", "field_family": "contact", "field_type": "reference_select", "label": "Preferred contact channel", "reference_domain": "contact_channels", "required_level": "optional", "public_safe": True, "portal_safe": True, "default_display_order": 50},
    {"field_key": "contact.consent_to_store_data", "canonical_path": "contact.data_processing_consent", "field_family": "consent", "field_type": "boolean", "label": "Data storage consent", "required_level": "system_required", "public_safe": True, "portal_safe": True, "can_be_hidden_by_agency": False, "can_label_be_overridden": False, "default_display_order": 900},
    {"field_key": "contact.consent_to_contact", "canonical_path": "contact.privacy_policy_accepted", "field_family": "consent", "field_type": "boolean", "label": "Contact consent", "required_level": "system_required", "public_safe": True, "portal_safe": True, "can_be_hidden_by_agency": False, "can_label_be_overridden": False, "default_display_order": 910},
    {"field_key": "client_context.client_id", "canonical_path": "client.client_id", "field_family": "client_context", "field_type": "text", "label": "Existing client", "required_level": "optional", "public_safe": False, "portal_safe": False, "admin_safe": True, "default_display_order": 100},
    {"field_key": "client_context.portal_access_expected", "canonical_path": "client_context.portal_access_expected", "field_family": "client_context", "field_type": "boolean", "label": "Portal access expected", "required_level": "optional", "public_safe": False, "portal_safe": False, "admin_safe": True, "default_display_order": 110},
    {"field_key": "itinerary_segments.origin", "canonical_path": "travel.origin", "field_family": "itinerary_segment", "field_type": "text", "label": "Origin", "required_level": "system_required", "public_safe": True, "portal_safe": True, "can_be_hidden_by_agency": False, "default_display_order": 200},
    {"field_key": "itinerary_segments.destination", "canonical_path": "travel.destination", "field_family": "itinerary_segment", "field_type": "text", "label": "Destination", "required_level": "system_required", "public_safe": True, "portal_safe": True, "can_be_hidden_by_agency": False, "default_display_order": 210},
    {"field_key": "itinerary_segments.departure_date", "canonical_path": "travel.departure_date", "field_family": "itinerary_segment", "field_type": "date", "label": "Departure date", "required_level": "system_required", "public_safe": True, "portal_safe": True, "can_be_hidden_by_agency": False, "default_display_order": 220},
    {"field_key": "itinerary_segments.arrival_date", "canonical_path": "segments[].arrival_date", "field_family": "itinerary_segment", "field_type": "date", "label": "Arrival date", "required_level": "optional", "public_safe": True, "portal_safe": True, "default_display_order": 230},
    {"field_key": "itinerary_segments.preferred_airline", "canonical_path": "segments[].marketing_airline", "field_family": "itinerary_segment", "field_type": "reference_select", "label": "Preferred airline", "reference_domain": "airlines", "required_level": "optional", "public_safe": True, "portal_safe": True, "default_display_order": 240},
    {"field_key": "itinerary_segments.cabin_class", "canonical_path": "segments[].cabin_preference", "field_family": "itinerary_segment", "field_type": "reference_select", "label": "Cabin class", "reference_domain": "cabin_classes", "required_level": "optional", "public_safe": True, "portal_safe": True, "default_display_order": 250},
    {"field_key": "itinerary_segments.notes", "canonical_path": "travel.itinerary_notes", "field_family": "itinerary_segment", "field_type": "textarea", "label": "Trip notes", "required_level": "recommended", "public_safe": True, "portal_safe": True, "default_display_order": 260},
    {"field_key": "passengers.first_name", "canonical_path": "passengers[].first_name", "field_family": "passenger", "field_type": "text", "label": "Passenger first name", "required_level": "system_required", "public_safe": True, "portal_safe": True, "can_be_hidden_by_agency": False, "default_display_order": 300},
    {"field_key": "passengers.last_name", "canonical_path": "passengers[].last_name", "field_family": "passenger", "field_type": "text", "label": "Passenger last name", "required_level": "recommended", "public_safe": True, "portal_safe": True, "default_display_order": 310},
    {"field_key": "passengers.date_of_birth", "canonical_path": "passengers[].date_of_birth", "field_family": "passenger", "field_type": "date", "label": "Date of birth", "required_level": "optional", "public_safe": True, "portal_safe": True, "default_display_order": 320},
    {"field_key": "passengers.passenger_type", "canonical_path": "passengers[].passenger_type", "field_family": "passenger", "field_type": "reference_select", "label": "Passenger type", "reference_domain": "passenger_types", "required_level": "recommended", "public_safe": True, "portal_safe": True, "default_display_order": 330},
    {"field_key": "passengers.nationality", "canonical_path": "passengers[].nationality", "field_family": "passenger", "field_type": "reference_select", "label": "Nationality", "reference_domain": "countries", "required_level": "optional", "public_safe": True, "portal_safe": True, "default_display_order": 340},
    {"field_key": "passengers.documents.passport_number", "canonical_path": "passengers[].documents.passport_number", "field_family": "document", "field_type": "text", "label": "Passport number", "required_level": "optional", "public_safe": False, "portal_safe": True, "default_display_order": 350},
    {"field_key": "passengers.documents.passport_expiry", "canonical_path": "passengers[].documents.passport_expiry", "field_family": "document", "field_type": "date", "label": "Passport expiry", "required_level": "optional", "public_safe": False, "portal_safe": True, "default_display_order": 360},
    {"field_key": "passengers.notes", "canonical_path": "passengers[].notes", "field_family": "passenger", "field_type": "textarea", "label": "Passenger notes", "required_level": "optional", "public_safe": True, "portal_safe": True, "default_display_order": 370},
    {"field_key": "services.service_family", "canonical_path": "services[].service_family_code", "field_family": "service", "field_type": "select", "label": "Service family", "required_level": "system_required", "public_safe": True, "portal_safe": True, "can_be_hidden_by_agency": False, "default_display_order": 400},
    {"field_key": "services.ssr_code", "canonical_path": "services[].ssr_code", "field_family": "service", "field_type": "text", "label": "SSR code", "required_level": "policy_required", "public_safe": False, "portal_safe": False, "admin_safe": True, "default_display_order": 410},
    {"field_key": "services.segment_scope", "canonical_path": "services[].segment_ids", "field_family": "service", "field_type": "multiselect", "label": "Segment scope", "required_level": "system_required", "public_safe": False, "portal_safe": False, "admin_safe": True, "can_be_hidden_by_agency": False, "default_display_order": 420},
    {"field_key": "services.service_details_json", "canonical_path": "services[].details", "field_family": "service", "field_type": "json", "label": "Service details", "required_level": "recommended", "public_safe": False, "portal_safe": False, "admin_safe": True, "default_display_order": 430},
    {"field_key": "pets.species", "canonical_path": "pets[].species", "field_family": "pet", "field_type": "reference_select", "label": "Pet species", "reference_domain": "pet_species", "required_level": "recommended", "public_safe": True, "portal_safe": True, "default_display_order": 500},
    {"field_key": "pets.breed", "canonical_path": "pets[].breed_free_text", "field_family": "pet", "field_type": "text", "label": "Breed", "required_level": "optional", "public_safe": True, "portal_safe": True, "default_display_order": 510},
    {"field_key": "pets.weight", "canonical_path": "pets[].combined_weight_kg", "field_family": "pet", "field_type": "number", "label": "Pet + carrier weight", "required_level": "recommended", "public_safe": True, "portal_safe": True, "default_display_order": 520},
    {"field_key": "pets.carrier_dimensions", "canonical_path": "pets[].container_dimensions_cm", "field_family": "pet", "field_type": "json", "label": "Carrier dimensions", "required_level": "optional", "public_safe": True, "portal_safe": True, "default_display_order": 530},
    {"field_key": "pets.transport_mode", "canonical_path": "pets[].requested_transport_mode", "field_family": "pet", "field_type": "select", "label": "Transport mode", "required_level": "recommended", "public_safe": True, "portal_safe": True, "default_display_order": 540},
    {"field_key": "pets.documentation_status", "canonical_path": "pets[].documentation_status", "field_family": "pet", "field_type": "select", "label": "Pet documents", "required_level": "recommended", "public_safe": False, "portal_safe": True, "default_display_order": 550},
    {"field_key": "special_items.item_category", "canonical_path": "special_items[].item_category_code", "field_family": "special_item", "field_type": "reference_select", "label": "Special item category", "reference_domain": "special_item_categories", "required_level": "recommended", "public_safe": True, "portal_safe": True, "default_display_order": 600},
    {"field_key": "special_items.weight", "canonical_path": "special_items[].weight_kg", "field_family": "special_item", "field_type": "number", "label": "Item weight", "required_level": "optional", "public_safe": True, "portal_safe": True, "default_display_order": 610},
    {"field_key": "special_items.dimensions", "canonical_path": "special_items[].dimensions_cm", "field_family": "special_item", "field_type": "json", "label": "Item dimensions", "required_level": "optional", "public_safe": True, "portal_safe": True, "default_display_order": 620},
    {"field_key": "special_items.transport_location", "canonical_path": "special_items[].transport_location", "field_family": "special_item", "field_type": "select", "label": "Transport location", "required_level": "recommended", "public_safe": True, "portal_safe": True, "default_display_order": 630},
    {"field_key": "special_items.documentation_status", "canonical_path": "special_items[].documentation_status", "field_family": "special_item", "field_type": "select", "label": "Special item documents", "required_level": "recommended", "public_safe": False, "portal_safe": True, "default_display_order": 640},
    {"field_key": "internal.admin_notes", "canonical_path": "internal_notes", "field_family": "internal_admin", "field_type": "textarea", "label": "Internal admin notes", "required_level": "internal_only", "public_safe": False, "portal_safe": False, "admin_safe": True, "can_be_hidden_by_agency": False, "default_display_order": 1000},
]


def safe_global_field_definition(record: dict[str, Any]) -> dict[str, Any]:
    return {**record, "validation_schema_json": record.get("validation_schema_json") or {}}


def safe_form_profile(record: dict[str, Any]) -> dict[str, Any]:
    return record


def safe_field_setting(record: dict[str, Any]) -> dict[str, Any]:
    return {
        **record,
        "custom_field_schema_json": record.get("custom_field_schema_json") or {},
        "visibility_condition_json": record.get("visibility_condition_json") or {},
        "validation_override_json": record.get("validation_override_json") or {},
    }


async def audit_form_profile_event(db: Database, event_type: str, entity_type: str, entity_id: str, summary: str, actor_user_id: str | None, agency_id: str | None = None, metadata: dict[str, Any] | None = None) -> None:
    event = AuditEvent(agency_id=agency_id, actor_user_id=actor_user_id, event_type=event_type, entity_type=entity_type, entity_id=entity_id, summary=summary, metadata=metadata or {})
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


async def bootstrap_global_field_definitions(db: Database, actor_user_id: str | None = None) -> dict[str, int]:
    counts = {"inserted": 0, "updated": 0}
    for payload in DEFAULT_FIELD_DEFINITIONS:
        existing = await db.collection("global_field_definitions").find_one({"field_key": payload["field_key"]})
        record_payload = {**payload, "updated_at": now_utc()}
        if existing:
            await db.collection("global_field_definitions").update_one({"id": existing["id"]}, record_payload)
            counts["updated"] += 1
        else:
            created = await db.collection("global_field_definitions").insert_one(GlobalFieldDefinition(**record_payload).model_dump(mode="json"))
            counts["inserted"] += 1
            await audit_form_profile_event(db, "global_field_definition_created", "global_field_definition", created["id"], f"Global field definition {created['field_key']} created.", actor_user_id, metadata={"field_key": created["field_key"]})
    return counts


async def ensure_default_form_profiles(db: Database, agency_id: str, workspace_id: str | None = None, actor_user_id: str | None = None) -> dict[str, int]:
    counts = {"inserted": 0, "existing": 0}
    for payload in DEFAULT_FORM_PROFILES:
        existing = await db.collection("agency_form_profiles").find_one({"agency_id": agency_id, "profile_key": payload["profile_key"]})
        if existing:
            counts["existing"] += 1
            continue
        profile = AgencyFormProfile(agency_id=agency_id, workspace_id=workspace_id, created_by_user_id=actor_user_id, **payload)
        created = await db.collection("agency_form_profiles").insert_one(profile.model_dump(mode="json"))
        counts["inserted"] += 1
        await audit_form_profile_event(db, "agency_form_profile_created", "agency_form_profile", created["id"], f"Agency form profile {created['profile_key']} created.", actor_user_id, agency_id, {"form_context": created["form_context"]})
    return counts


def field_safe_for_context(definition: dict[str, Any], form_context: str) -> bool:
    if definition.get("required_level") == "internal_only":
        return form_context in ADMIN_CONTEXTS
    if form_context in PUBLIC_CONTEXTS:
        return bool(definition.get("public_safe"))
    if form_context in PORTAL_CONTEXTS:
        return bool(definition.get("portal_safe"))
    return bool(definition.get("admin_safe", True))


def setting_section_key(definition: dict[str, Any], setting: dict[str, Any] | None = None) -> str:
    return (setting or {}).get("section_key") or definition.get("field_family") or "general"


def locked_reason(definition: dict[str, Any], form_context: str) -> str | None:
    if definition.get("required_level") == "system_required":
        return "system_required"
    if not field_safe_for_context(definition, form_context):
        return "unsafe_for_context"
    if not definition.get("can_be_hidden_by_agency", True):
        return "not_hideable"
    return None


async def get_profile_or_404(db: Database, agency_id: str, profile_id: str) -> dict[str, Any]:
    profile = await db.collection("agency_form_profiles").find_one({"agency_id": agency_id, "id": profile_id})
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form profile not found.")
    return profile


async def default_profile_for_context(db: Database, agency_id: str, form_context: str) -> dict[str, Any] | None:
    profile = await db.collection("agency_form_profiles").find_one({"agency_id": agency_id, "form_context": form_context, "is_default": True, "is_active": True})
    if profile:
        return profile
    profiles = await db.collection("agency_form_profiles").find_many({"agency_id": agency_id, "form_context": form_context, "is_active": True})
    return profiles[0] if profiles else None


def effective_field(definition: dict[str, Any], setting: dict[str, Any] | None, form_context: str) -> dict[str, Any]:
    safe = field_safe_for_context(definition, form_context)
    visible = safe
    enabled = True
    if setting:
        enabled = bool(setting.get("enabled", True))
        requested_visible = bool(setting.get("visible", True))
        visible = safe and requested_visible
    if definition.get("required_level") == "system_required":
        enabled = True
        visible = safe
    if not safe:
        visible = False
    required = definition.get("required_level") in {"system_required", "policy_required"}
    if setting and definition.get("can_be_required_by_agency", True) and setting.get("required_override") is not None:
        required = bool(setting.get("required_override"))
    label = definition.get("label")
    if setting and definition.get("can_label_be_overridden", True) and setting.get("label_override"):
        label = setting["label_override"]
    help_text = definition.get("help_text")
    if setting and definition.get("can_label_be_overridden", True) and setting.get("help_text_override"):
        help_text = setting["help_text_override"]
    return {
        **safe_global_field_definition(definition),
        "enabled": enabled,
        "visible": visible,
        "required": required,
        "effective_label": label,
        "effective_help_text": help_text,
        "placeholder": setting.get("placeholder_override") if setting else None,
        "display_order": setting.get("display_order") if setting else definition.get("default_display_order", 100),
        "section_key": setting_section_key(definition, setting),
        "section_label": (setting or {}).get("section_label_override") or FIELD_FAMILY_LABELS.get(definition.get("field_family"), definition.get("field_family", "General").replace("_", " ").title()),
        "locked": locked_reason(definition, form_context) is not None,
        "locked_reason": locked_reason(definition, form_context),
        "setting": safe_field_setting(setting) if setting else None,
    }


def effective_custom_field(setting: dict[str, Any], form_context: str) -> dict[str, Any]:
    schema = setting.get("custom_field_schema_json") or {}
    field_type = schema.get("field_type") or "text"
    label = setting.get("label_override") or schema.get("label") or setting.get("field_key")
    section_key = setting.get("section_key") or "agency_custom"
    return {
        "id": setting.get("id"),
        "field_key": setting.get("field_key"),
        "canonical_path": f"agency_custom_fields.{setting.get('field_key')}",
        "field_family": "agency_custom",
        "field_type": field_type,
        "label": label,
        "effective_label": label,
        "effective_help_text": setting.get("help_text_override") or schema.get("help_text"),
        "required_level": "optional",
        "public_safe": form_context in PUBLIC_CONTEXTS,
        "portal_safe": form_context in PORTAL_CONTEXTS,
        "admin_safe": True,
        "enabled": bool(setting.get("enabled", True)),
        "visible": bool(setting.get("visible", True)),
        "required": bool(setting.get("required_override", False)),
        "display_order": setting.get("display_order", 1000),
        "section_key": section_key,
        "section_label": setting.get("section_label_override") or "Agency Custom",
        "custom_field": True,
        "custom_field_schema_json": schema,
        "locked": False,
    }


async def resolve_effective_form_profile(db: Database, agency_id: str, profile_id: str | None = None, form_context: str | None = None) -> dict[str, Any]:
    profile = await get_profile_or_404(db, agency_id, profile_id) if profile_id else await default_profile_for_context(db, agency_id, form_context or "public_request")
    if not profile:
        return {"profile": None, "fields": [], "sections": [], "fallback": True}
    definitions = [safe_global_field_definition(item) for item in await db.collection("global_field_definitions").find_many({"is_active": True})]
    settings = [safe_field_setting(item) for item in await db.collection("agency_form_field_settings").find_many({"agency_id": agency_id, "form_profile_id": profile["id"]})]
    settings_by_key = {item["field_key"]: item for item in settings if not item.get("custom_field")}
    context = profile["form_context"]
    fields = [effective_field(definition, settings_by_key.get(definition["field_key"]), context) for definition in definitions]
    fields.extend(effective_custom_field(setting, context) for setting in settings if setting.get("custom_field"))
    fields = sorted(fields, key=lambda item: (str(item.get("section_key")), int(item.get("display_order") or 100), str(item.get("effective_label") or item.get("label"))))
    sections = []
    for field in fields:
        section = next((item for item in sections if item["section_key"] == field["section_key"]), None)
        if not section:
            section = {"section_key": field["section_key"], "section_label": field.get("section_label") or field["section_key"].replace("_", " ").title(), "fields": []}
            sections.append(section)
        section["fields"].append(field)
    return {"profile": safe_form_profile(profile), "fields": fields, "sections": sections, "fallback": False}


async def validate_field_setting(db: Database, profile: dict[str, Any], payload: AgencyFormFieldSettingInput) -> dict[str, Any]:
    if payload.custom_field:
        if not payload.custom_field_schema_json:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Custom field schema is required.")
        field_type = payload.custom_field_schema_json.get("field_type")
        if field_type not in {"text", "textarea", "select", "boolean", "number", "date"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported custom field type.")
        return {}
    definition = None
    if payload.global_field_definition_id:
        definition = await db.collection("global_field_definitions").find_one({"id": payload.global_field_definition_id})
    if not definition:
        definition = await db.collection("global_field_definitions").find_one({"field_key": payload.field_key})
    if not definition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Global field definition not found: {payload.field_key}")
    if definition.get("required_level") == "system_required" and (payload.enabled is False or payload.visible is False):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="System-required fields cannot be hidden.")
    if not field_safe_for_context(definition, profile["form_context"]) and payload.visible:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsafe or internal-only fields cannot be exposed in this form context.")
    if payload.required_override is not None and not definition.get("can_be_required_by_agency", True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This field cannot have its required setting overridden.")
    if (payload.label_override or payload.help_text_override) and not definition.get("can_label_be_overridden", True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This field label/help text cannot be overridden.")
    return definition


async def replace_form_field_settings(db: Database, agency_id: str, profile: dict[str, Any], fields: list[AgencyFormFieldSettingInput], actor_user_id: str | None = None) -> dict[str, Any]:
    existing = await db.collection("agency_form_field_settings").find_many({"agency_id": agency_id, "form_profile_id": profile["id"]})
    existing_by_key = {item["field_key"]: item for item in existing}
    updated_items = []
    custom_added = 0
    for payload in fields:
        definition = await validate_field_setting(db, profile, payload)
        record_payload = payload.model_dump(mode="json")
        if not record_payload.get("id"):
            record_payload.pop("id", None)
        record_payload["agency_id"] = agency_id
        record_payload["workspace_id"] = record_payload.get("workspace_id") or profile.get("workspace_id")
        record_payload["form_profile_id"] = profile["id"]
        if definition:
            record_payload["global_field_definition_id"] = definition["id"]
            record_payload["field_key"] = definition["field_key"]
        existing_record = existing_by_key.get(record_payload["field_key"])
        if existing_record:
            updated = await db.collection("agency_form_field_settings").update_one({"id": existing_record["id"]}, record_payload)
            updated_items.append(updated)
        else:
            created = await db.collection("agency_form_field_settings").insert_one(AgencyFormFieldSetting(**record_payload).model_dump(mode="json"))
            updated_items.append(created)
            if created.get("custom_field"):
                custom_added += 1
                await audit_form_profile_event(db, "agency_custom_field_added", "agency_form_field_setting", created["id"], f"Agency custom field {created['field_key']} added.", actor_user_id, agency_id, {"form_profile_id": profile["id"]})
    await audit_form_profile_event(db, "agency_form_field_settings_updated", "agency_form_profile", profile["id"], "Agency form field settings updated.", actor_user_id, agency_id, {"field_count": len(updated_items)})
    return {"items": [safe_field_setting(item) for item in updated_items], "custom_added": custom_added}
