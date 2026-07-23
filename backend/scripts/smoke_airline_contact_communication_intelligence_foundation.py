#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from database import AGENCY_OWNED_COLLECTIONS, Database
from models import (
    AirlineCommunicationRequirement,
    AirlineCommunicationTemplate,
    AirlineContactAvailability,
    AirlineContactChannel,
    AirlineContactDirectoryEntry,
    AirlineContactEscalationPath,
    AirlineContactScope,
    AirlineContactVerification,
    AirlineSupplierInteractionRecord,
)
from services.airline_contact_communication_intelligence_service import (
    CAPABILITY_PHASE,
    COMMUNICATION_TEMPLATE_TYPES,
    CONTACT_CHANNEL_TYPES,
    CONTACT_DESK_TYPES,
    CONTACT_INTELLIGENCE_COLLECTIONS,
    ENTITY_CONFIG,
    PHASE_LABEL,
    AirlineContactCommunicationIntelligenceError,
    AirlineContactCommunicationIntelligenceService,
)
from phase_assertions import assert_application_phase_at_least
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


MINIMUM_PHASE = "phase_55_8_airline_contact_communication_intelligence_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/airline-contact-intelligence"
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def require_text(path: Path, value: str) -> None:
    if value not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {value}")


def reject_text(path: Path, value: str) -> None:
    if value.lower() in path.read_text(encoding="utf-8").lower():
        raise AssertionError(f"{path.relative_to(ROOT)} contains prohibited execution text: {value}")


def assert_agency_safe(value: object) -> None:
    restricted = {
        "internal_notes",
        "visible_agency_ids",
        "evidence_link_ids",
        "source_reference_ids",
        "verification_notes",
        "verified_by",
        "review_decision",
        "password",
        "secret",
        "api_key",
        "private_key",
        "access_token",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if key in restricted:
                raise AssertionError(f"Agency contact response leaked restricted field {key}")
            assert_agency_safe(child)
    elif isinstance(value, list):
        for child in value:
            assert_agency_safe(child)


def verify_models_collections_indexes_and_taxonomies() -> None:
    service_text = (ROOT / "backend/services/airline_contact_communication_intelligence_service.py").read_text(encoding="utf-8")
    if '"ssr_osi_workspace_id": "ssr_osi_operational_workspaces"' in service_text:
        raise AssertionError("Airline contact integration uses the stale SSR/OSI collection name.")
    if '"ssr_osi_workspace_id": "ssr_osi_workspaces"' not in service_text:
        raise AssertionError("Airline contact integration is not mapped to the canonical SSR/OSI collection.")
    if CAPABILITY_PHASE != MINIMUM_PHASE:
        raise AssertionError(f"Unexpected Phase 55.8 capability provenance: {CAPABILITY_PHASE}")
    assert_application_phase_at_least(PHASE_LABEL, MINIMUM_PHASE, source="Phase 55.8 service")
    expected_collections = {
        "airline_contacts",
        "airline_contact_channels",
        "airline_contact_scopes",
        "airline_contact_availabilities",
        "airline_contact_escalation_paths",
        "airline_communication_templates",
        "airline_communication_requirements",
        "airline_contact_verifications",
        "airline_supplier_interactions",
    }
    if set(CONTACT_INTELLIGENCE_COLLECTIONS) != expected_collections:
        raise AssertionError("Phase 55.8 collection constants are incomplete.")
    if not expected_collections.issubset(set(AGENCY_OWNED_COLLECTIONS)):
        raise AssertionError("Phase 55.8 agency-aware collection registration is incomplete.")
    if len(ENTITY_CONFIG) != 9:
        raise AssertionError("All governed contact intelligence entity families are not registered.")
    required_desks = {
        "general_agency_support", "trade_support", "ticketing_desk", "refunds_desk",
        "schedule_change_desk", "medical_desk", "special_assistance_desk", "umnr_desk",
        "pet_desk", "group_desk", "baggage_desk", "airport_station", "disruption_desk",
        "ndc_support", "gds_support", "emd_ancillary_desk", "accounting_adm_desk", "complaints_claims",
    }
    required_templates = {
        "ssr_request", "medif_request", "poc_approval", "wheelchair_device_information",
        "petc_avih_request", "umnr_request", "extra_seat_cbbg", "schedule_change", "refund",
        "ticket_exchange", "emd_servicing", "baggage_special_item", "policy_clarification",
    }
    if set(CONTACT_DESK_TYPES) != required_desks or set(COMMUNICATION_TEMPLATE_TYPES) != required_templates:
        raise AssertionError("Contact desk or communication-template taxonomy is incomplete.")
    if not {"email", "phone", "gds_queue", "ndc_portal"}.issubset(set(CONTACT_CHANNEL_TYPES)):
        raise AssertionError("Contact channel taxonomy is incomplete.")

    contact = AirlineContactDirectoryEntry(contact_reference="ACD-MODEL", airline_code="LH", desk_type="medical_desk", contact_name="Medical desk")
    channel = AirlineContactChannel(channel_reference="ACC-MODEL", airline_code="LH", contact_directory_entry_id=contact.id, channel_type="email", channel_label="Email")
    scope = AirlineContactScope(scope_reference="ACS-MODEL", airline_code="LH", contact_directory_entry_id=contact.id, scope_name="Germany")
    availability = AirlineContactAvailability(availability_reference="ACA-MODEL", airline_code="LH", contact_directory_entry_id=contact.id)
    escalation = AirlineContactEscalationPath(escalation_reference="ACE-MODEL", airline_code="LH", desk_type="medical_desk", path_name="Medical escalation")
    template = AirlineCommunicationTemplate(communication_template_reference="ACT-MODEL", template_type="medif_request", template_name="MEDIF", supplier_message_template="Please review")
    requirement = AirlineCommunicationRequirement(communication_requirement_reference="ACR-MODEL", requirement_name="MEDIF information")
    verification = AirlineContactVerification(verification_reference="ACV-MODEL", airline_code="LH", target_type="contacts", target_id=contact.id)
    interaction = AirlineSupplierInteractionRecord(agency_id="agency-model", interaction_reference="ASI-MODEL", airline_code="LH", interaction_summary="Recorded outside AeroAssist")
    if not all(item.id and item.metadata_only for item in [contact, channel, scope, availability, escalation, template, requirement, verification, interaction]):
        raise AssertionError("Phase 55.8 model defaults are incomplete.")
    if channel.stores_credentials or not channel.secret_storage_disabled or interaction.sent_externally:
        raise AssertionError("Contact and interaction model safety defaults are incomplete.")

    database_text = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "airline_contacts_agency_airline_desk_lookup",
        "airline_contact_channels_access_lookup",
        "airline_contact_scopes_service_route_lookup",
        "airline_contact_availabilities_timezone_status_lookup",
        "airline_contact_escalation_paths_desk_lookup",
        "airline_communication_templates_airline_type_lookup",
        "airline_communication_requirements_target_lookup",
        "airline_contact_verifications_review_due_lookup",
        "airline_supplier_interactions_operational_links_lookup",
    ]:
        if index_name not in database_text:
            raise AssertionError(f"Mongo index registration missing {index_name}")


async def verify_service_behavior() -> None:
    db = Database()
    service = AirlineContactCommunicationIntelligenceService(db)
    agency_id = "agency-contact-smoke"
    other_agency_id = "agency-contact-other"
    user = {"id": "platform-owner", "email": "owner@aeroassist.dev"}
    visible = {
        "publication_status": "published",
        "agency_visibility_status": "selected_agencies",
        "visible_agency_ids": [agency_id],
    }
    contact = (await service.create_record("contacts", {
        "airline_code": "LH",
        "desk_type": "medical_desk",
        "contact_name": "Germany medical desk",
        "contact_status": "active",
        "country_scope": ["DE"],
        "airport_scope": ["FRA"],
        "service_scope": ["MEDIF"],
        "required_information": ["passenger_name", "booking_reference", "medical_summary"],
        "required_attachment_types": ["medif"],
        "expected_response_minutes": 120,
        "verification_status": "verified",
        "freshness_status": "current",
        "evidence_link_ids": ["evidence-medical-desk"],
        **visible,
    }, user))["item"]
    generic = (await service.create_record("contacts", {
        "airline_code": "LH",
        "desk_type": "medical_desk",
        "contact_name": "Global medical desk",
        "contact_status": "active",
        "verification_status": "verified",
        "freshness_status": "current",
        **visible,
    }, user))["item"]
    channel = (await service.create_record("channels", {
        "airline_code": "LH",
        "contact_directory_entry_id": contact["id"],
        "channel_type": "email",
        "channel_label": "Medical email",
        "contact_value": "medical@example.test",
        "language_codes": ["en", "de"],
        "agency_identifier_required": True,
        "access_classification": "agency_visible",
        "channel_status": "active",
        **visible,
    }, user))["item"]
    await service.create_record("channels", {
        "airline_code": "LH",
        "contact_directory_entry_id": contact["id"],
        "channel_type": "gds_queue",
        "channel_label": "Restricted queue",
        "channel_reference_value": "Q-PRIVATE",
        "access_classification": "restricted_internal",
        "channel_status": "active",
        **visible,
    }, user)
    await service.create_record("scopes", {
        "airline_code": "LH",
        "contact_directory_entry_id": contact["id"],
        "scope_name": "Frankfurt MEDIF",
        "country_scope": ["DE"],
        "airport_scope": ["FRA"],
        "service_scope": ["MEDIF"],
        "scope_status": "active",
        "priority": 10,
        **visible,
    }, user)
    await service.create_record("availabilities", {
        "airline_code": "LH",
        "contact_directory_entry_id": contact["id"],
        "timezone": "Europe/Berlin",
        "availability_status": "active",
        "operating_hours": [{"days": ["monday", "tuesday", "wednesday", "thursday", "friday"], "opens": "08:00", "closes": "18:00"}],
        "after_hours_instruction": "Use the published disruption desk for urgent travel within 24 hours.",
        **visible,
    }, user)
    escalation = (await service.create_record("escalation-paths", {
        "airline_code": "LH",
        "desk_type": "medical_desk",
        "contact_directory_entry_id": contact["id"],
        "path_name": "Medical response escalation",
        "trigger_after_minutes": 120,
        "escalation_steps": [{"order": 1, "instruction": "Call the medical desk and quote the interaction reference."}],
        "path_status": "active",
        **visible,
    }, user))["item"]
    template = (await service.create_record("templates", {
        "airline_code": "LH",
        "template_type": "medif_request",
        "template_name": "LH MEDIF request",
        "desk_type": "medical_desk",
        "channel_type": "email",
        "language": "en",
        "subject_template": "MEDIF review for {passenger_name}",
        "internal_instructions": "Confirm the passenger consent and use the approved document record.",
        "supplier_message_template": "Please review MEDIF for {passenger_name}, booking {booking_reference}.",
        "client_status_message_template": "We have prepared your medical-assistance request for airline review.",
        "required_information": ["passenger_name", "booking_reference"],
        "required_attachment_types": ["medif"],
        "template_status": "active",
        "freshness_status": "current",
        **visible,
    }, user))["item"]
    await service.create_record("requirements", {
        "airline_code": "LH",
        "template_id": template["id"],
        "contact_directory_entry_id": contact["id"],
        "requirement_name": "LH MEDIF submission",
        "desk_type": "medical_desk",
        "template_type": "medif_request",
        "required_information": ["medical_summary"],
        "required_document_types": ["medical_certificate"],
        "required_attachment_types": ["medif"],
        "required_identifiers": ["ticket_number"],
        "requirement_status": "active",
        **visible,
    }, user)
    verification = (await service.create_record("verifications", {
        "airline_code": "LH",
        "target_type": "contacts",
        "target_id": contact["id"],
        "verification_status": "verified",
        "verification_method": "airline_email_confirmation",
        "verified_at": "2026-07-01T09:00:00Z",
        "next_review_at": "2027-01-01T09:00:00Z",
        "source_reference_ids": ["source-email-confirmation"],
    }, user))["item"]
    refreshed = (await service.get_record("contacts", contact["id"]))["item"]
    if refreshed.get("freshness_status") != "current" or not refreshed.get("last_verified_at") or verification.get("target_id") != contact["id"]:
        raise AssertionError("Contact verification did not update governed freshness metadata.")

    open_result = await service.find_desk({"airline_code": "LH", "desk_type": "medical_desk", "country": "DE", "airport": "FRA", "service_code": "MEDIF", "at": "2026-07-13T08:00:00Z"}, agency_id=agency_id, agency_safe=True)
    if open_result.get("selected", {}).get("contact", {}).get("id") != contact["id"]:
        raise AssertionError("Specific scoped contact did not outrank the generic desk.")
    if open_result.get("selected", {}).get("availability", {}).get("current_status") != "open":
        raise AssertionError("Business-hours evaluation did not recognize open Europe/Berlin hours.")
    if not any(item.get("contact", {}).get("id") == generic["id"] for item in open_result.get("matches", [])):
        raise AssertionError("Generic desk fallback was not retained behind the scoped match.")
    if open_result.get("selected", {}).get("escalation_recommendation", {}).get("path_id") != escalation["id"]:
        raise AssertionError("Desk finder omitted its manual escalation recommendation.")
    assert_agency_safe(open_result)
    closed_result = await service.find_desk({"airline_code": "LH", "desk_type": "medical_desk", "country": "DE", "airport": "FRA", "service_code": "MEDIF", "at": "2026-07-12T08:00:00Z"}, agency_id=agency_id, agency_safe=True)
    if closed_result.get("selected", {}).get("availability", {}).get("current_status") != "closed" or not closed_result.get("warnings"):
        raise AssertionError("Closed operating-hours state did not produce an agency warning.")

    composed = await service.compose_message({
        "airline_code": "LH",
        "template_type": "medif_request",
        "desk_type": "medical_desk",
        "channel_type": "email",
        "contact_directory_entry_id": contact["id"],
        "values": {"passenger_name": "Ada Example", "booking_reference": "ABC123"},
        "provided_information": ["passenger_name", "booking_reference", "medical_summary"],
        "provided_attachment_types": ["medif"],
    }, agency_id=agency_id, agency_safe=True)
    messages = composed.get("messages") or {}
    if len({messages.get("internal_instructions"), messages.get("supplier_facing_message"), messages.get("client_facing_status_message")}) != 3:
        raise AssertionError("Internal, supplier, and client template content was not kept separate.")
    if "medical_certificate" not in composed.get("required_documents", []) or "ticket_number" not in composed.get("missing_information", []):
        raise AssertionError("Communication requirement checklist was not merged into the composed metadata.")
    if composed.get("message_sent") is not False or composed.get("manual_copy_only") is not True:
        raise AssertionError("Template composition implied external message execution.")
    assert_agency_safe(composed)

    for collection, record_id in [("operational_work_items", "work-contact-1"), ("operational_deadlines", "deadline-contact-1"), ("after_sales_cases", "case-contact-1")]:
        await db.collection(collection).insert_one({"id": record_id, "agency_id": agency_id})
    interaction = await service.log_interaction({
        "airline_code": "LH",
        "contact_directory_entry_id": contact["id"],
        "contact_channel_id": channel["id"],
        "communication_template_id": template["id"],
        "desk_type": "medical_desk",
        "channel_type": "email",
        "interaction_summary": "Agency agent sent MEDIF to the airline outside AeroAssist.",
        "work_item_id": "work-contact-1",
        "deadline_id": "deadline-contact-1",
        "after_sales_case_id": "case-contact-1",
        "supplier_message_snapshot": messages.get("supplier_facing_message"),
        "client_status_message_snapshot": messages.get("client_facing_status_message"),
        "sent_externally": False,
    }, user, agency_id=agency_id)
    item = interaction.get("item") or {}
    if item.get("sent_externally") is not False or not item.get("timeline_entry_id"):
        raise AssertionError("Interaction history did not preserve no-send state and timeline linkage.")
    if interaction.get("integration", {}).get("warnings"):
        raise AssertionError("Existing workflow/task/SLA/after-sales integration links were not resolved.")
    timeline = await db.collection("operational_timelines").find_one({"id": item["timeline_entry_id"]})
    if not timeline or timeline.get("event_type") != "airline_contacted" or timeline.get("metadata", {}).get("message_sent") is not False:
        raise AssertionError("Interaction history did not create the expected internal operational timeline entry.")

    agency = await service.agency_dashboard(agency_id, airline_code="LH")
    if len(agency.get("channels") or []) != 1 or agency["channels"][0].get("access_classification") != "agency_visible":
        raise AssertionError("Restricted channel leaked into the agency directory.")
    if (await service.agency_dashboard(other_agency_id, airline_code="LH")).get("contacts"):
        raise AssertionError("Selected-agency contact intelligence leaked across agencies.")
    assert_agency_safe(agency)
    try:
        await service.create_record("channels", {"airline_code": "LH", "contact_directory_entry_id": contact["id"], "channel_type": "email", "channel_label": "Unsafe", "api_key": "not-allowed"}, user)
    except AirlineContactCommunicationIntelligenceError:
        pass
    else:
        raise AssertionError("Secret-like contact payload was accepted.")


def verify_routes_ui_docs_and_readiness(paths: dict) -> None:
    expected = {
        "/api/platform/airline-contact-intelligence": {"get"},
        "/api/platform/airline-contact-intelligence/summary": {"get"},
        "/api/platform/airline-contact-intelligence/filters": {"get"},
        "/api/platform/airline-contact-intelligence/find-desk": {"post"},
        "/api/platform/airline-contact-intelligence/compose": {"post"},
        "/api/platform/airline-contact-intelligence/{entity_type}": {"get", "post"},
        "/api/platform/airline-contact-intelligence/{entity_type}/{record_id}": {"get", "put"},
        "/api/agencies/{agency_id}/airline-contact-directory": {"get"},
        "/api/agencies/{agency_id}/airline-contact-directory/summary": {"get"},
        "/api/agencies/{agency_id}/airline-contact-directory/filters": {"get"},
        "/api/agencies/{agency_id}/airline-contact-directory/find-desk": {"post"},
        "/api/agencies/{agency_id}/airline-contact-directory/compose": {"post"},
        "/api/agencies/{agency_id}/airline-contact-directory/interactions": {"get", "post"},
        "/api/agencies/{agency_id}/airline-contact-directory/interactions/{record_id}": {"get"},
        "/api/agencies/{agency_id}/airline-contact-directory/{entity_type}": {"get"},
        "/api/agencies/{agency_id}/airline-contact-directory/{entity_type}/{record_id}": {"get"},
    }
    for path, methods in expected.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    agency_directory_path = "/api/agencies/{agency_id}/airline-contact-directory/{entity_type}"
    if set(paths.get(agency_directory_path, {})) & {"post", "put", "patch", "delete"}:
        raise AssertionError("Agency contact directory records expose mutation.")

    checks = [
        ("frontend/src/App.jsx", "/platform/airline-contact-intelligence"),
        ("frontend/src/App.jsx", "/agency/airline-contact-directory"),
        ("frontend/src/lib/moduleCatalog.js", "Airline Contact Directory"),
        ("frontend/src/pages/platform/AirlineContactIntelligencePage.jsx", "Separated communication templates"),
        ("frontend/src/pages/agency/AirlineContactDirectoryPage.jsx", "AeroAssist did not send a message"),
        ("docs/architecture/airline-contact-communication-intelligence-foundation.md", "does not send the supplier-facing or client-facing text"),
        ("BUILD_PHASES.md", "Implemented Phase 55.8"),
        ("README.md", "Phase 55.8 Airline Contact and Communication Intelligence"),
        ("docs/architecture/current-model-inventory.md", "airline_supplier_interactions"),
        ("docs/architecture/canonical-route-policy.md", "/api/platform/airline-contact-intelligence"),
        ("docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Phase 55.8 Alignment"),
        ("docs/architecture/supplementary-blueprint-adoption-map.md", "Phase 55.8 Airline Contact and Communication Intelligence"),
        ("backend/services/blueprint_adoption_service.py", "Airline Contact And Communication Intelligence"),
        ("backend/services/airline_policy_evidence_governance_service.py", '"communication_template": "airline_communication_templates"'),
        ("backend/services/airline_knowledge_versioning_service.py", '"contact_availability": "airline_contact_availabilities"'),
    ]
    for relative, value in checks:
        require_text(ROOT / relative, value)

    health = get("/api/health")
    readiness = get("/api/readiness")
    assert_application_phase_at_least(health.get("phase"), MINIMUM_PHASE, source="health")
    assert_application_phase_at_least(readiness.get("phase"), MINIMUM_PHASE, source="readiness")
    section = readiness.get("airline_contact_communication_intelligence_foundation") or {}
    for key in [
        "airline_contact_communication_intelligence_enabled",
        "canonical_airline_contacts_collection_reused",
        "desk_and_scope_matching_enabled",
        "timezone_operating_hours_enabled",
        "governed_template_separation_enabled",
        "required_information_checklists_enabled",
        "verification_and_freshness_enabled",
        "manual_interaction_logging_enabled",
        "operational_timeline_integration_enabled",
        "workflow_after_sales_task_sla_linkage_enabled",
        "agency_published_directory_enabled",
        "restricted_contact_protection_enabled",
        "private_credentials_disabled",
        "secret_storage_disabled",
        "external_messaging_disabled",
        "automatic_escalation_disabled",
        "metadata_only",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Readiness missing Phase 55.8 flag {key}: {section}")
    for key in ["contact_directory_entry_count", "contact_channel_count", "contact_availability_count", "communication_template_count", "supplier_interaction_count", "stale_contact_count"]:
        if key not in section:
            raise AssertionError(f"Readiness missing Phase 55.8 counter {key}")


def verify_live_routes() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Phase 55.8 smoke requires a seeded agency.")
    agency_id = agencies[0]["id"]
    token = uuid4().hex[:8].upper()
    airline_code = f"C{token[:1]}"
    visible = {
        "agency_id": agency_id,
        "publication_status": "published",
        "agency_visibility_status": "selected_agencies",
        "visible_agency_ids": [agency_id],
    }
    contact = post(f"{PLATFORM_BASE}/contacts", {
        "airline_code": airline_code,
        "desk_type": "pet_desk",
        "contact_name": "Smoke pet desk",
        "contact_status": "active",
        "country_scope": ["BG"],
        "service_scope": ["PETC"],
        "verification_status": "verified",
        "freshness_status": "current",
        "required_information": ["booking_reference", "pet_dimensions"],
        **visible,
    }, OWNER_HEADERS, 201)["item"]
    channel = post(f"{PLATFORM_BASE}/channels", {
        "airline_code": airline_code,
        "contact_directory_entry_id": contact["id"],
        "channel_type": "email",
        "channel_label": "Pet email",
        "contact_value": "pet@example.test",
        "access_classification": "agency_visible",
        "channel_status": "active",
        **visible,
    }, OWNER_HEADERS, 201)["item"]
    post(f"{PLATFORM_BASE}/availabilities", {
        "airline_code": airline_code,
        "contact_directory_entry_id": contact["id"],
        "timezone": "Europe/Sofia",
        "is_24_hours": True,
        "availability_status": "active",
        **visible,
    }, OWNER_HEADERS, 201)
    template = post(f"{PLATFORM_BASE}/templates", {
        "airline_code": airline_code,
        "template_type": "petc_avih_request",
        "template_name": "Smoke PETC request",
        "desk_type": "pet_desk",
        "channel_type": "email",
        "internal_instructions": "Confirm carrier dimensions.",
        "supplier_message_template": "Please review PETC for {booking_reference}.",
        "client_status_message_template": "We prepared your pet request.",
        "required_information": ["booking_reference", "pet_dimensions"],
        "template_status": "active",
        "freshness_status": "current",
        **visible,
    }, OWNER_HEADERS, 201)["item"]
    updated = put(f"{PLATFORM_BASE}/contacts/{contact['id']}", {"expected_response_minutes": 90}, OWNER_HEADERS)["item"]
    if updated.get("expected_response_minutes") != 90:
        raise AssertionError("Live platform contact update failed.")
    dashboard = get(f"{PLATFORM_BASE}?airline_code={airline_code}", OWNER_HEADERS)
    if dashboard.get("summary", {}).get("contact_count") != 1:
        raise AssertionError("Platform contact dashboard omitted the live record.")
    agency = get(f"/api/agencies/{agency_id}/airline-contact-directory?airline_code={airline_code}", OWNER_HEADERS)
    if len(agency.get("contacts") or []) != 1 or len(agency.get("channels") or []) != 1:
        raise AssertionError("Agency contact directory omitted published contact metadata.")
    assert_agency_safe(agency)
    found = post(f"/api/agencies/{agency_id}/airline-contact-directory/find-desk", {"airline_code": airline_code, "desk_type": "pet_desk", "country": "BG", "service_code": "PETC"}, OWNER_HEADERS)
    if found.get("selected", {}).get("contact", {}).get("id") != contact["id"] or found.get("selected", {}).get("availability", {}).get("current_status") != "open":
        raise AssertionError("Agency live desk finder failed.")
    composed = post(f"/api/agencies/{agency_id}/airline-contact-directory/compose", {"airline_code": airline_code, "template_type": "petc_avih_request", "desk_type": "pet_desk", "channel_type": "email", "contact_directory_entry_id": contact["id"], "values": {"booking_reference": "LIVE123"}}, OWNER_HEADERS)
    if composed.get("message_sent") is not False or not composed.get("messages", {}).get("supplier_facing_message"):
        raise AssertionError("Agency live template composition failed or implied sending.")
    interaction = post(f"/api/agencies/{agency_id}/airline-contact-directory/interactions", {
        "airline_code": airline_code,
        "contact_directory_entry_id": contact["id"],
        "contact_channel_id": channel["id"],
        "communication_template_id": template["id"],
        "interaction_summary": "Agent contacted the pet desk outside AeroAssist.",
        "sent_externally": False,
    }, OWNER_HEADERS, 201)["item"]
    if interaction.get("sent_externally") is not False or not interaction.get("timeline_entry_id"):
        raise AssertionError("Agency live interaction logging failed.")
    request("POST", f"/api/agencies/{agency_id}/airline-contact-directory/contacts", {}, OWNER_HEADERS, 405)
    request("POST", f"{PLATFORM_BASE}/channels", {"airline_code": airline_code, "contact_directory_entry_id": contact["id"], "channel_type": "email", "channel_label": "Unsafe", "api_key": "secret-value"}, OWNER_HEADERS, 400)
    request("GET", PLATFORM_BASE, None, AGENCY_AGENT_HEADERS, 403)
    if len(agencies) > 1:
        request(
            "GET",
            f"/api/agencies/{agencies[1]['id']}/airline-contact-directory?airline_code={airline_code}",
            None,
            OWNER_HEADERS,
            403,
        )


def verify_safety() -> None:
    flags = AirlineContactCommunicationIntelligenceService(None).safety_flags()  # type: ignore[arg-type]
    if any(value is not True for value in flags.values()):
        raise AssertionError(f"Contact intelligence safety flag is disabled: {flags}")
    service_path = ROOT / "backend/services/airline_contact_communication_intelligence_service.py"
    for forbidden in [
        "requests.get(",
        "requests.post(",
        "httpx.",
        "openai",
        "backgroundtasks",
        "asyncio.create_task",
        ".delete_one(",
        ".delete_many(",
        "send_email(",
        "send_sms(",
        "provider.send(",
        "execute_escalation(",
    ]:
        reject_text(service_path, forbidden)


def main() -> int:
    verify_models_collections_indexes_and_taxonomies()
    verify_safety()
    asyncio.run(verify_service_behavior())
    paths = get("/openapi.json").get("paths") or {}
    verify_routes_ui_docs_and_readiness(paths)
    verify_live_routes()
    print("Phase 55.8 airline contact and communication intelligence foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
