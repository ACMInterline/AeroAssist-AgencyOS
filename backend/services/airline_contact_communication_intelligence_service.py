from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from database import Database
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
    AuditEvent,
    OperationalTimelineCreate,
)
from services.timeline_workspace_service import OperationalTimelineService


PHASE_LABEL = "phase_56_3_journey_comparison_client_presentation_foundation"

AIRLINE_CONTACT_DIRECTORY_COLLECTION = "airline_contacts"
AIRLINE_CONTACT_CHANNELS_COLLECTION = "airline_contact_channels"
AIRLINE_CONTACT_SCOPES_COLLECTION = "airline_contact_scopes"
AIRLINE_CONTACT_AVAILABILITIES_COLLECTION = "airline_contact_availabilities"
AIRLINE_CONTACT_ESCALATION_PATHS_COLLECTION = "airline_contact_escalation_paths"
AIRLINE_COMMUNICATION_TEMPLATES_COLLECTION = "airline_communication_templates"
AIRLINE_COMMUNICATION_REQUIREMENTS_COLLECTION = "airline_communication_requirements"
AIRLINE_CONTACT_VERIFICATIONS_COLLECTION = "airline_contact_verifications"
AIRLINE_SUPPLIER_INTERACTIONS_COLLECTION = "airline_supplier_interactions"

CONTACT_INTELLIGENCE_COLLECTIONS = [
    AIRLINE_CONTACT_DIRECTORY_COLLECTION,
    AIRLINE_CONTACT_CHANNELS_COLLECTION,
    AIRLINE_CONTACT_SCOPES_COLLECTION,
    AIRLINE_CONTACT_AVAILABILITIES_COLLECTION,
    AIRLINE_CONTACT_ESCALATION_PATHS_COLLECTION,
    AIRLINE_COMMUNICATION_TEMPLATES_COLLECTION,
    AIRLINE_COMMUNICATION_REQUIREMENTS_COLLECTION,
    AIRLINE_CONTACT_VERIFICATIONS_COLLECTION,
    AIRLINE_SUPPLIER_INTERACTIONS_COLLECTION,
]

CONTACT_DESK_TYPES = [
    "general_agency_support",
    "trade_support",
    "ticketing_desk",
    "refunds_desk",
    "schedule_change_desk",
    "medical_desk",
    "special_assistance_desk",
    "umnr_desk",
    "pet_desk",
    "group_desk",
    "baggage_desk",
    "airport_station",
    "disruption_desk",
    "ndc_support",
    "gds_support",
    "emd_ancillary_desk",
    "accounting_adm_desk",
    "complaints_claims",
]

COMMUNICATION_TEMPLATE_TYPES = [
    "ssr_request",
    "medif_request",
    "poc_approval",
    "wheelchair_device_information",
    "petc_avih_request",
    "umnr_request",
    "extra_seat_cbbg",
    "schedule_change",
    "refund",
    "ticket_exchange",
    "emd_servicing",
    "baggage_special_item",
    "policy_clarification",
]

CONTACT_CHANNEL_TYPES = [
    "email",
    "phone",
    "web_form",
    "gds_queue",
    "ndc_portal",
    "chat",
    "airport_desk",
    "postal",
    "other",
]

PUBLICATION_STATUSES = ["draft", "under_review", "approved", "published", "archived"]
AGENCY_VISIBILITY_STATUSES = ["platform_only", "all_agencies", "selected_agencies"]
FRESHNESS_STATUSES = ["current", "review_due", "stale", "expired", "unknown"]
VERIFICATION_STATUSES = ["pending", "verified", "failed", "review_due", "stale", "superseded"]
ACCESS_CLASSIFICATIONS = ["public", "agency_visible", "restricted_internal", "platform_only"]
CONTACT_STATUSES = ["active", "inactive", "unverified", "superseded", "archived"]

ENTITY_CONFIG: dict[str, dict[str, Any]] = {
    "contacts": {"collection": AIRLINE_CONTACT_DIRECTORY_COLLECTION, "model": AirlineContactDirectoryEntry, "reference": "contact_reference", "prefix": "ACD"},
    "channels": {"collection": AIRLINE_CONTACT_CHANNELS_COLLECTION, "model": AirlineContactChannel, "reference": "channel_reference", "prefix": "ACC"},
    "scopes": {"collection": AIRLINE_CONTACT_SCOPES_COLLECTION, "model": AirlineContactScope, "reference": "scope_reference", "prefix": "ACS"},
    "availabilities": {"collection": AIRLINE_CONTACT_AVAILABILITIES_COLLECTION, "model": AirlineContactAvailability, "reference": "availability_reference", "prefix": "ACA"},
    "escalation-paths": {"collection": AIRLINE_CONTACT_ESCALATION_PATHS_COLLECTION, "model": AirlineContactEscalationPath, "reference": "escalation_reference", "prefix": "ACE"},
    "templates": {"collection": AIRLINE_COMMUNICATION_TEMPLATES_COLLECTION, "model": AirlineCommunicationTemplate, "reference": "communication_template_reference", "prefix": "ACT"},
    "requirements": {"collection": AIRLINE_COMMUNICATION_REQUIREMENTS_COLLECTION, "model": AirlineCommunicationRequirement, "reference": "communication_requirement_reference", "prefix": "ACR"},
    "verifications": {"collection": AIRLINE_CONTACT_VERIFICATIONS_COLLECTION, "model": AirlineContactVerification, "reference": "verification_reference", "prefix": "ACV"},
    "interactions": {"collection": AIRLINE_SUPPLIER_INTERACTIONS_COLLECTION, "model": AirlineSupplierInteractionRecord, "reference": "interaction_reference", "prefix": "ASI"},
}

AGENCY_DIRECTORY_ENTITIES = {
    "contacts",
    "channels",
    "scopes",
    "availabilities",
    "escalation-paths",
    "templates",
    "requirements",
    "interactions",
}

INTERNAL_FIELDS = {
    "internal_notes",
    "metadata",
    "visible_agency_ids",
    "evidence_link_ids",
    "source_reference_ids",
    "verification_notes",
    "verified_by",
    "review_decision",
}

FORBIDDEN_SECRET_KEYS = {
    "password",
    "passwd",
    "secret",
    "api_key",
    "access_key",
    "private_key",
    "bearer_token",
    "authorization_header",
    "credential_value",
}

INTEGRATION_COLLECTIONS = {
    "workflow_instance_id": "operational_workflow_instances",
    "passenger_service_workflow_id": "passenger_service_workflows",
    "after_sales_case_id": "after_sales_cases",
    "task_id": "request_tasks",
    "work_item_id": "operational_work_items",
    "deadline_id": "operational_deadlines",
    "communication_log_id": "after_sales_communication_records",
    "passenger_workspace_id": "passenger_workspaces",
    "travel_request_workspace_id": "travel_request_workspaces",
    "trip_workspace_id": "trip_workspaces",
    "booking_workspace_id": "booking_workspaces",
    "ticket_workspace_id": "ticket_workspaces",
    "emd_workspace_id": "emd_workspaces",
    "ssr_osi_workspace_id": "ssr_osi_operational_workspaces",
    "document_workspace_id": "document_workspaces",
}


class AirlineContactCommunicationIntelligenceError(ValueError):
    pass


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_none=True, exclude_unset=True)
    return {key: value for key, value in dict(payload or {}).items() if value is not None}


class _SafeTemplateValues(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


class AirlineContactCommunicationIntelligenceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "contact_intelligence_only": True,
            "canonical_airline_contacts_reused": True,
            "secret_storage_disabled": True,
            "private_credentials_disabled": True,
            "external_messaging_disabled": True,
            "email_sending_disabled": True,
            "sms_sending_disabled": True,
            "provider_connectivity_disabled": True,
            "automatic_escalation_disabled": True,
            "background_workers_disabled": True,
            "ai_disabled": True,
            "template_message_separation_enabled": True,
            "verification_and_freshness_enabled": True,
            "operational_timeline_integration_enabled": True,
            "workflow_after_sales_task_sla_linkage_enabled": True,
            "agency_isolation_enabled": True,
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "entity_types": list(ENTITY_CONFIG),
            "agency_directory_entities": sorted(AGENCY_DIRECTORY_ENTITIES),
            "desk_types": CONTACT_DESK_TYPES,
            "channel_types": CONTACT_CHANNEL_TYPES,
            "template_types": COMMUNICATION_TEMPLATE_TYPES,
            "contact_statuses": CONTACT_STATUSES,
            "verification_statuses": VERIFICATION_STATUSES,
            "freshness_statuses": FRESHNESS_STATUSES,
            "publication_statuses": PUBLICATION_STATUSES,
            "agency_visibility_statuses": AGENCY_VISIBILITY_STATUSES,
            "access_classifications": ACCESS_CLASSIFICATIONS,
        }

    async def coverage(self) -> dict[str, Any]:
        contacts = await self.list_records("contacts")
        channels = await self.list_records("channels")
        templates = await self.list_records("templates")
        interactions = await self.list_records("interactions")
        stale = self._stale_contacts(contacts)
        return {
            "contact_directory_entry_count": len(contacts),
            "contact_channel_count": len(channels),
            "contact_scope_count": await self.db.collection(AIRLINE_CONTACT_SCOPES_COLLECTION).count(),
            "contact_availability_count": await self.db.collection(AIRLINE_CONTACT_AVAILABILITIES_COLLECTION).count(),
            "contact_escalation_path_count": await self.db.collection(AIRLINE_CONTACT_ESCALATION_PATHS_COLLECTION).count(),
            "communication_template_count": len(templates),
            "communication_requirement_count": await self.db.collection(AIRLINE_COMMUNICATION_REQUIREMENTS_COLLECTION).count(),
            "contact_verification_count": await self.db.collection(AIRLINE_CONTACT_VERIFICATIONS_COLLECTION).count(),
            "supplier_interaction_count": len(interactions),
            "verified_contact_count": sum(item.get("verification_status") == "verified" for item in contacts),
            "stale_contact_count": len(stale),
            "published_contact_count": sum(item.get("publication_status") == "published" for item in contacts),
            "airline_count": len({self._airline(item.get("airline_code")) for item in contacts if item.get("airline_code")}),
        }

    async def create_record(self, entity_type: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        entity_type, config = self._config(entity_type)
        data = payload_dict(payload)
        self._reject_secrets(data)
        if entity_type == "interactions":
            return await self.log_interaction(data, user, agency_id=data.get("agency_id"))
        data.setdefault(config["reference"], self._reference(config["prefix"]))
        normalized = await self._normalize_and_validate(entity_type, data, user=user)
        record = config["model"](**normalized).model_dump(mode="json")
        created = await self.db.collection(config["collection"]).insert_one(record)
        if entity_type == "verifications":
            await self._apply_verification(created)
        await self._audit(f"airline_contact_intelligence.{entity_type}.created", created, user)
        return {"phase": PHASE_LABEL, "entity_type": entity_type, "item": created, **self.safety_flags()}

    async def update_record(self, entity_type: str, record_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        entity_type, config = self._config(entity_type)
        existing = await self._require(entity_type, record_id)
        updates = payload_dict(payload)
        self._reject_secrets(updates)
        normalized = await self._normalize_and_validate(entity_type, {**existing, **updates}, user=user, current_id=existing["id"])
        validated = config["model"](**normalized).model_dump(mode="json")
        immutable = {"id", "created_at", "agency_id", config["reference"]}
        changes = {key: value for key, value in validated.items() if key not in immutable}
        updated = await self.db.collection(config["collection"]).update_one({"id": existing["id"]}, changes)
        if not updated:
            raise AirlineContactCommunicationIntelligenceError("Contact intelligence metadata could not be updated.")
        if entity_type == "verifications":
            await self._apply_verification(updated)
        await self._audit(f"airline_contact_intelligence.{entity_type}.updated", updated, user)
        return {"phase": PHASE_LABEL, "entity_type": entity_type, "item": updated, **self.safety_flags()}

    async def get_record(self, entity_type: str, record_id: str) -> dict[str, Any]:
        entity_type, _ = self._config(entity_type)
        return {"phase": PHASE_LABEL, "entity_type": entity_type, "item": await self._require(entity_type, record_id), **self.safety_flags()}

    async def get_agency_record(self, entity_type: str, agency_id: str, record_id: str) -> dict[str, Any]:
        entity_type, _ = self._config(entity_type)
        if entity_type not in AGENCY_DIRECTORY_ENTITIES:
            raise AirlineContactCommunicationIntelligenceError("This contact intelligence entity is not agency-visible.")
        item = await self._require(entity_type, record_id)
        if entity_type == "interactions":
            if item.get("agency_id") != agency_id:
                raise AirlineContactCommunicationIntelligenceError("Interaction record was not found for this agency.")
        elif not self._agency_visible(entity_type, item, agency_id):
            raise AirlineContactCommunicationIntelligenceError("Published contact intelligence was not found for this agency.")
        return {"phase": PHASE_LABEL, "agency_id": agency_id, "entity_type": entity_type, "item": self._agency_projection(entity_type, item), "read_only": entity_type != "interactions", **self.safety_flags()}

    async def list_records(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
        entity_type, config = self._config(entity_type)
        items = await self.db.collection(config["collection"]).find_many()
        items = [item for item in items if self._matches_filters(item, filters)]
        items.sort(key=lambda item: (self._airline(item.get("airline_code")), self._sort_text(item.get("updated_at"))), reverse=False)
        return items

    async def list_agency_records(self, entity_type: str, agency_id: str, **filters: Any) -> list[dict[str, Any]]:
        entity_type, _ = self._config(entity_type)
        if entity_type not in AGENCY_DIRECTORY_ENTITIES:
            raise AirlineContactCommunicationIntelligenceError("This contact intelligence entity is not agency-visible.")
        items = await self.list_records(entity_type, **filters)
        if entity_type == "interactions":
            return [self._agency_projection(entity_type, item) for item in items if item.get("agency_id") == agency_id]
        return [self._agency_projection(entity_type, item) for item in items if self._agency_visible(entity_type, item, agency_id)]

    async def platform_dashboard(self, **filters: Any) -> dict[str, Any]:
        records = {entity_type: await self.list_records(entity_type, **filters) for entity_type in ENTITY_CONFIG}
        stale = self._stale_contacts(records["contacts"])
        return {
            "phase": PHASE_LABEL,
            "summary": self._summary(records, stale),
            "contacts": records["contacts"],
            "channels": records["channels"],
            "scopes": records["scopes"],
            "availabilities": records["availabilities"],
            "escalation_paths": records["escalation-paths"],
            "templates": records["templates"],
            "requirements": records["requirements"],
            "verifications": records["verifications"],
            "interactions": records["interactions"],
            "stale_contacts": stale,
            "filters": self.filter_metadata(),
            **self.safety_flags(),
        }

    async def agency_dashboard(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        records = {entity_type: await self.list_agency_records(entity_type, agency_id, **filters) for entity_type in AGENCY_DIRECTORY_ENTITIES}
        stale = self._stale_contacts(records["contacts"])
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self._summary(records, stale),
            "contacts": records["contacts"],
            "channels": records["channels"],
            "scopes": records["scopes"],
            "availabilities": records["availabilities"],
            "escalation_paths": records["escalation-paths"],
            "templates": records["templates"],
            "requirements": records["requirements"],
            "interactions": records["interactions"],
            "stale_contacts": stale,
            "filters": self.filter_metadata(),
            "read_only_directory": True,
            "interaction_logging_enabled": True,
            **self.safety_flags(),
        }

    async def find_desk(self, payload: Any, *, agency_id: str | None = None, agency_safe: bool = False) -> dict[str, Any]:
        context = payload_dict(payload)
        airline_code = self._airline(context.get("airline_code"))
        desk_type = self._normalize_token(context.get("desk_type"))
        if not airline_code or desk_type not in CONTACT_DESK_TYPES:
            raise AirlineContactCommunicationIntelligenceError("A valid airline code and desk type are required.")

        contacts = await self.list_records("contacts", airline_code=airline_code, desk_type=desk_type)
        if agency_safe:
            contacts = [item for item in contacts if self._agency_visible("contacts", item, agency_id)]
        contacts = [item for item in contacts if item.get("contact_status") == "active" and self._effective(item)]
        scored: list[tuple[int, dict[str, Any]]] = []
        for item in contacts:
            scopes = await self.list_records("scopes", contact_directory_entry_id=item["id"])
            if agency_safe:
                scopes = [scope for scope in scopes if self._agency_visible("scopes", scope, agency_id)]
            score = self._scope_score(item, context)
            matching_scopes = [scope for scope in scopes if self._scope_matches(scope, context)]
            if scopes and not matching_scopes:
                continue
            if matching_scopes:
                score += max(self._scope_score(scope, context) + max(0, 200 - int(scope.get("priority") or 100)) for scope in matching_scopes)
            scored.append((score, item))
        scored.sort(key=lambda pair: (pair[0], self._sort_text(pair[1].get("last_verified_at"))), reverse=True)

        matches = []
        for score, contact in scored:
            details = await self._contact_details(contact, agency_id=agency_id, agency_safe=agency_safe, at=context.get("at"))
            details["match_score"] = score
            matches.append(details)
        selected = matches[0] if matches else None
        warnings: list[str] = []
        if not selected:
            warnings.append("No governed contact matches this airline, desk, and operational scope.")
        elif selected["contact"].get("verification_status") != "verified":
            warnings.append("The selected contact is not currently verified.")
        if selected and selected.get("availability", {}).get("current_status") in {"closed", "unknown"}:
            warnings.append("The selected desk is closed or its current hours are unknown.")
        return {
            "phase": PHASE_LABEL,
            "airline_code": airline_code,
            "desk_type": desk_type,
            "selected": selected,
            "matches": matches,
            "warnings": warnings,
            "manual_review_required": bool(warnings),
            "advisory_only": True,
            **self.safety_flags(),
        }

    async def compose_message(self, payload: Any, *, agency_id: str | None = None, agency_safe: bool = False) -> dict[str, Any]:
        data = payload_dict(payload)
        self._reject_secrets(data)
        template_id = data.get("template_id")
        if template_id:
            template = await self._require("templates", str(template_id))
            if agency_safe and not self._agency_visible("templates", template, agency_id):
                raise AirlineContactCommunicationIntelligenceError("Published communication template was not found for this agency.")
        else:
            template_type = self._normalize_token(data.get("template_type"))
            if template_type not in COMMUNICATION_TEMPLATE_TYPES:
                raise AirlineContactCommunicationIntelligenceError("A valid communication template type is required.")
            candidates = await self.list_records("templates", template_type=template_type)
            if agency_safe:
                candidates = [item for item in candidates if self._agency_visible("templates", item, agency_id)]
            candidates = [item for item in candidates if self._template_matches(item, data)]
            candidates.sort(key=lambda item: self._template_score(item, data), reverse=True)
            template = candidates[0] if candidates else None
            if not template:
                raise AirlineContactCommunicationIntelligenceError("No governed communication template matches this context.")

        values = _SafeTemplateValues({key: str(value) for key, value in dict(data.get("values") or {}).items()})
        contact = None
        if data.get("contact_directory_entry_id"):
            contact = await self._require("contacts", str(data["contact_directory_entry_id"]))
        requirements = await self._matching_requirements(template, contact, agency_id, agency_safe)
        required_information = self._unique([
            *template.get("required_information", []),
            *(contact or {}).get("required_information", []),
            *[value for item in requirements for value in item.get("required_information", [])],
            *[value for item in requirements for value in item.get("required_identifiers", [])],
        ])
        required_documents = self._unique([value for item in requirements for value in item.get("required_document_types", [])])
        required_attachments = self._unique([
            *template.get("required_attachment_types", []),
            *(contact or {}).get("required_attachment_types", []),
            *[value for item in requirements for value in item.get("required_attachment_types", [])],
        ])
        provided = {self._normalize_token(value) for value in data.get("provided_information", [])}
        attached = {self._normalize_token(value) for value in data.get("provided_attachment_types", [])}
        missing_information = [value for value in required_information if self._normalize_token(value) not in provided and self._normalize_token(value) not in values]
        missing_attachments = [value for value in required_attachments if self._normalize_token(value) not in attached]
        messages = {
            "internal_instructions": self._format_template(template.get("internal_instructions"), values),
            "supplier_facing_message": self._format_template(template.get("supplier_message_template"), values),
            "client_facing_status_message": self._format_template(template.get("client_status_message_template"), values),
        }
        return {
            "phase": PHASE_LABEL,
            "template": self._agency_projection("templates", template) if agency_safe else template,
            "subject": self._format_template(template.get("subject_template"), values),
            "messages": messages,
            "required_information": required_information,
            "required_documents": required_documents,
            "required_attachments": required_attachments,
            "missing_information": missing_information,
            "missing_attachments": missing_attachments,
            "ready_for_manual_use": not missing_information and not missing_attachments,
            "manual_copy_only": True,
            "message_sent": False,
            **self.safety_flags(),
        }

    async def log_interaction(self, payload: Any, user: dict[str, Any], *, agency_id: str | None) -> dict[str, Any]:
        data = payload_dict(payload)
        self._reject_secrets(data)
        agency_id = agency_id or data.get("agency_id")
        if not agency_id:
            raise AirlineContactCommunicationIntelligenceError("Agency ID is required for supplier interaction history.")
        if data.get("sent_externally"):
            raise AirlineContactCommunicationIntelligenceError("This foundation cannot send or claim to send an external message.")
        data["agency_id"] = agency_id
        data.setdefault("interaction_reference", self._reference("ASI"))
        data.setdefault("created_by", user.get("id"))
        data["sent_externally"] = False
        data["provider_messaging_disabled"] = True
        data["secret_storage_disabled"] = True
        data["metadata_only"] = True

        contact = await self._optional_link("contacts", data.get("contact_directory_entry_id"), airline_code=data.get("airline_code"))
        channel = await self._optional_link("channels", data.get("contact_channel_id"), contact_id=data.get("contact_directory_entry_id"))
        template = await self._optional_link("templates", data.get("communication_template_id"), airline_code=data.get("airline_code"))
        if contact and contact.get("agency_id") not in {None, agency_id}:
            raise AirlineContactCommunicationIntelligenceError("Contact belongs to another agency.")
        if channel and channel.get("agency_id") not in {None, agency_id}:
            raise AirlineContactCommunicationIntelligenceError("Contact channel belongs to another agency.")
        if template and template.get("agency_id") not in {None, agency_id}:
            raise AirlineContactCommunicationIntelligenceError("Communication template belongs to another agency.")

        data.setdefault("airline_code", self._airline((contact or {}).get("airline_code")))
        data["airline_code"] = self._airline(data.get("airline_code"))
        if not data["airline_code"]:
            raise AirlineContactCommunicationIntelligenceError("Airline code is required for supplier interaction history.")
        data.setdefault("desk_type", (contact or template or {}).get("desk_type"))
        data.setdefault("channel_type", (channel or template or {}).get("channel_type"))
        if template:
            data.setdefault("internal_instruction_snapshot", template.get("internal_instructions"))
            data.setdefault("supplier_message_snapshot", template.get("supplier_message_template"))
            data.setdefault("client_status_message_snapshot", template.get("client_status_message_template"))
            data.setdefault("required_information_snapshot", template.get("required_information", []))
        occurred_at = self._parse_datetime(data.get("occurred_at")) or datetime.now(timezone.utc)
        data["occurred_at"] = occurred_at
        response_minutes = (channel or {}).get("expected_response_minutes") or (contact or {}).get("expected_response_minutes")
        if response_minutes and not data.get("response_due_at"):
            data["response_due_at"] = occurred_at + timedelta(minutes=int(response_minutes))
        integration = await self._integration_snapshot(data, agency_id)
        data["metadata"] = {**dict(data.get("metadata") or {}), "integration_snapshot": integration}

        validated = await self._normalize_and_validate("interactions", data, user=user)
        record = AirlineSupplierInteractionRecord(**validated).model_dump(mode="json")
        created = await self.db.collection(AIRLINE_SUPPLIER_INTERACTIONS_COLLECTION).insert_one(record)
        timeline = await self._create_timeline_entry(created, user)
        if timeline:
            created = await self.db.collection(AIRLINE_SUPPLIER_INTERACTIONS_COLLECTION).update_one(
                {"id": created["id"]},
                {"timeline_entry_id": timeline.get("id")},
            ) or created
        await self._audit("airline_contact_intelligence.interactions.logged", created, user)
        return {
            "phase": PHASE_LABEL,
            "entity_type": "interactions",
            "item": self._agency_projection("interactions", created),
            "integration": integration,
            "message_sent": False,
            **self.safety_flags(),
        }

    async def _normalize_and_validate(
        self,
        entity_type: str,
        data: dict[str, Any],
        *,
        user: dict[str, Any],
        current_id: str | None = None,
    ) -> dict[str, Any]:
        normalized = dict(data)
        if "airline_code" in normalized and normalized.get("airline_code"):
            normalized["airline_code"] = self._airline(normalized["airline_code"])
        for key in ("desk_type", "channel_type", "template_type", "target_type"):
            if normalized.get(key):
                normalized[key] = self._normalize_token(normalized[key])
        if normalized.get("desk_type") and normalized["desk_type"] not in CONTACT_DESK_TYPES:
            raise AirlineContactCommunicationIntelligenceError("Unsupported airline contact desk type.")
        if normalized.get("channel_type") and normalized["channel_type"] not in CONTACT_CHANNEL_TYPES:
            raise AirlineContactCommunicationIntelligenceError("Unsupported airline contact channel type.")
        if normalized.get("template_type") and normalized["template_type"] not in COMMUNICATION_TEMPLATE_TYPES:
            raise AirlineContactCommunicationIntelligenceError("Unsupported airline communication template type.")
        if entity_type == "contacts" and normalized.get("contact_status") not in CONTACT_STATUSES:
            raise AirlineContactCommunicationIntelligenceError("Unsupported airline contact status.")
        if entity_type == "channels":
            if normalized.get("access_classification") not in ACCESS_CLASSIFICATIONS:
                raise AirlineContactCommunicationIntelligenceError("Unsupported contact access classification.")
            if normalized.get("stores_credentials"):
                raise AirlineContactCommunicationIntelligenceError("Contact channels cannot store credentials or secrets.")
            await self._require_same_scope_link("contacts", normalized.get("contact_directory_entry_id"), normalized)
        if entity_type in {"scopes", "availabilities"}:
            await self._require_same_scope_link("contacts", normalized.get("contact_directory_entry_id"), normalized)
        if entity_type == "escalation-paths" and normalized.get("contact_directory_entry_id"):
            await self._require_same_scope_link("contacts", normalized.get("contact_directory_entry_id"), normalized)
        if entity_type == "templates":
            if not str(normalized.get("supplier_message_template") or "").strip():
                raise AirlineContactCommunicationIntelligenceError("Supplier-facing message template is required.")
            normalized["automatic_sending_disabled"] = True
        if entity_type == "requirements":
            if normalized.get("template_id"):
                await self._require_same_scope_link("templates", normalized.get("template_id"), normalized, allow_generic_airline=True)
            if normalized.get("contact_directory_entry_id"):
                await self._require_same_scope_link("contacts", normalized.get("contact_directory_entry_id"), normalized, allow_generic_airline=True)
        if entity_type == "verifications":
            if normalized.get("verification_status") not in VERIFICATION_STATUSES:
                raise AirlineContactCommunicationIntelligenceError("Unsupported verification status.")
            if normalized.get("target_type") not in ENTITY_CONFIG or normalized.get("target_type") in {"verifications", "interactions"}:
                raise AirlineContactCommunicationIntelligenceError("Verification target type is unsupported.")
            target = await self._require(normalized["target_type"], str(normalized.get("target_id") or ""))
            if self._airline(target.get("airline_code")) != self._airline(normalized.get("airline_code")):
                raise AirlineContactCommunicationIntelligenceError("Verification airline does not match its target.")
            normalized.setdefault("verified_by", user.get("id"))
            if normalized.get("verification_status") == "verified":
                normalized.setdefault("verified_at", datetime.now(timezone.utc))
        if entity_type == "interactions":
            if not str(normalized.get("interaction_summary") or "").strip():
                raise AirlineContactCommunicationIntelligenceError("Interaction summary is required.")
            normalized["sent_externally"] = False
        normalized["metadata_only"] = True
        self._reject_secrets(normalized)
        return normalized

    async def _apply_verification(self, verification: dict[str, Any]) -> None:
        target_type = verification.get("target_type")
        if target_type not in ENTITY_CONFIG:
            return
        config = ENTITY_CONFIG[target_type]
        updates: dict[str, Any] = {}
        status = verification.get("verification_status")
        if target_type in {"contacts", "channels"}:
            updates["verification_status"] = status
        if status == "verified":
            updates["last_verified_at"] = verification.get("verified_at") or datetime.now(timezone.utc)
            updates["freshness_status"] = "current"
        elif status in {"stale", "review_due"}:
            updates["freshness_status"] = status
        if verification.get("next_review_at"):
            updates["next_review_at"] = verification["next_review_at"]
        await self.db.collection(config["collection"]).update_one({"id": verification["target_id"]}, updates)

    async def _contact_details(
        self,
        contact: dict[str, Any],
        *,
        agency_id: str | None,
        agency_safe: bool,
        at: Any,
    ) -> dict[str, Any]:
        attached: dict[str, list[dict[str, Any]]] = {}
        for entity_type, foreign_key in (
            ("channels", "contact_directory_entry_id"),
            ("scopes", "contact_directory_entry_id"),
            ("availabilities", "contact_directory_entry_id"),
            ("escalation-paths", "contact_directory_entry_id"),
        ):
            items = await self.list_records(entity_type, **{foreign_key: contact["id"]})
            if agency_safe:
                items = [item for item in items if self._agency_visible(entity_type, item, agency_id)]
            attached[entity_type] = [self._agency_projection(entity_type, item) if agency_safe else item for item in items]
        availability_record = attached["availabilities"][0] if attached["availabilities"] else None
        availability = self._evaluate_availability(availability_record, at)
        escalations = sorted(attached["escalation-paths"], key=lambda item: int(item.get("trigger_after_minutes") or 999999))
        return {
            "contact": self._agency_projection("contacts", contact) if agency_safe else contact,
            "channels": attached["channels"],
            "scopes": attached["scopes"],
            "availability": availability,
            "escalation_paths": escalations,
            "escalation_recommendation": self._escalation_recommendation(escalations),
        }

    def _evaluate_availability(self, availability: dict[str, Any] | None, at: Any) -> dict[str, Any]:
        reference_time = self._parse_datetime(at) or datetime.now(timezone.utc)
        if not availability:
            return {"current_status": "unknown", "checked_at": reference_time.isoformat(), "reason": "No governed operating-hours record is available."}
        timezone_name = availability.get("timezone") or "UTC"
        try:
            local = reference_time.astimezone(ZoneInfo(timezone_name))
        except ZoneInfoNotFoundError:
            return {"current_status": "unknown", "timezone": timezone_name, "checked_at": reference_time.isoformat(), "reason": "Configured timezone is invalid."}
        result = {"current_status": "closed", "timezone": timezone_name, "checked_at": reference_time.isoformat(), "local_time": local.isoformat(), "after_hours_instruction": availability.get("after_hours_instruction")}
        if availability.get("availability_status") not in {"active", "open", "published"}:
            result["current_status"] = "unknown"
            result["reason"] = "Availability record is not active."
            return result
        if availability.get("is_24_hours"):
            result.update({"current_status": "open", "reason": "Desk is recorded as open 24 hours."})
            return result
        local_date = local.date().isoformat()
        if local_date in availability.get("holiday_dates", []):
            result["reason"] = "Desk is closed for a recorded holiday."
            return result
        schedule = availability.get("operating_hours", [])
        exceptions = [item for item in availability.get("exception_hours", []) if str(item.get("date")) == local_date]
        if exceptions:
            schedule = exceptions
        weekday = local.strftime("%A").lower()
        for period in schedule:
            days = [self._normalize_token(value) for value in period.get("days", [])]
            day = self._normalize_token(period.get("day"))
            if day and day != weekday or days and weekday not in days:
                continue
            if period.get("closed"):
                continue
            opens = self._parse_time(period.get("opens") or period.get("start"))
            closes = self._parse_time(period.get("closes") or period.get("end"))
            if opens is None or closes is None:
                continue
            local_clock = local.timetz().replace(tzinfo=None)
            in_period = opens <= local_clock < closes if opens <= closes else local_clock >= opens or local_clock < closes
            if in_period:
                result.update({"current_status": "open", "reason": "Current local time is within governed operating hours.", "opens": opens.isoformat(timespec="minutes"), "closes": closes.isoformat(timespec="minutes")})
                return result
        result["reason"] = "Current local time is outside governed operating hours."
        return result

    async def _matching_requirements(
        self,
        template: dict[str, Any],
        contact: dict[str, Any] | None,
        agency_id: str | None,
        agency_safe: bool,
    ) -> list[dict[str, Any]]:
        items = await self.list_records("requirements")
        matched = [
            item for item in items
            if item.get("requirement_status") == "active"
            and (not item.get("template_id") or item.get("template_id") == template.get("id"))
            and (not item.get("contact_directory_entry_id") or contact and item.get("contact_directory_entry_id") == contact.get("id"))
            and (not item.get("template_type") or item.get("template_type") == template.get("template_type"))
            and (not item.get("airline_code") or item.get("airline_code") == template.get("airline_code"))
        ]
        if agency_safe:
            matched = [item for item in matched if self._agency_visible("requirements", item, agency_id)]
        return matched

    async def _integration_snapshot(self, data: dict[str, Any], agency_id: str) -> dict[str, Any]:
        links: list[dict[str, Any]] = []
        warnings: list[str] = []
        for field, collection in INTEGRATION_COLLECTIONS.items():
            record_id = data.get(field)
            if not record_id:
                continue
            record = await self.db.collection(collection).find_one({"id": record_id})
            if not record:
                warnings.append(f"{field} could not be resolved and requires manual review.")
                links.append({"field": field, "id": record_id, "status": "unresolved"})
                continue
            if record.get("agency_id") not in {None, agency_id}:
                raise AirlineContactCommunicationIntelligenceError(f"{field} belongs to another agency.")
            links.append({"field": field, "id": record_id, "status": "linked"})
        return {"links": links, "warnings": warnings, "workflow_mutated": False, "task_mutated": False, "sla_mutated": False, "after_sales_mutated": False}

    async def _create_timeline_entry(self, interaction: dict[str, Any], user: dict[str, Any]) -> dict[str, Any] | None:
        payload = OperationalTimelineCreate(
            agency_id=interaction["agency_id"],
            created_by=user.get("id"),
            passenger_workspace_id=interaction.get("passenger_workspace_id"),
            travel_request_workspace_id=interaction.get("travel_request_workspace_id"),
            trip_workspace_id=interaction.get("trip_workspace_id"),
            booking_workspace_id=interaction.get("booking_workspace_id"),
            ticket_workspace_id=interaction.get("ticket_workspace_id"),
            emd_workspace_id=interaction.get("emd_workspace_id"),
            ssr_osi_workspace_id=interaction.get("ssr_osi_workspace_id"),
            document_workspace_id=interaction.get("document_workspace_id"),
            event_type="airline_contacted",
            event_category="supplier_communication",
            event_source="airline_contact_intelligence",
            event_status=interaction.get("interaction_status"),
            related_airline=interaction.get("airline_code"),
            communication_type="airline_message",
            communication_direction=interaction.get("direction"),
            communication_channel=interaction.get("channel_type"),
            subject=interaction.get("subject"),
            summary=interaction.get("interaction_summary"),
            attachment_ids=interaction.get("attachment_ids", []),
            internal_only=True,
            passenger_visible=False,
            airline_visible=False,
            operational_notes="Supplier interaction history only; no message was sent by AeroAssist.",
            metadata={"supplier_interaction_id": interaction["id"], "after_sales_case_id": interaction.get("after_sales_case_id"), "workflow_instance_id": interaction.get("workflow_instance_id"), "task_id": interaction.get("task_id"), "work_item_id": interaction.get("work_item_id"), "deadline_id": interaction.get("deadline_id"), "message_sent": False},
        )
        response = await OperationalTimelineService(self.db).create_entry(payload, user)
        return response.get("timeline_entry")

    async def _require_same_scope_link(self, entity_type: str, record_id: Any, data: dict[str, Any], *, allow_generic_airline: bool = False) -> dict[str, Any]:
        if not record_id:
            raise AirlineContactCommunicationIntelligenceError(f"{entity_type} relationship is required.")
        item = await self._require(entity_type, str(record_id))
        if item.get("agency_id") not in {None, data.get("agency_id")} and data.get("agency_id") is not None:
            raise AirlineContactCommunicationIntelligenceError("Linked contact intelligence belongs to another agency.")
        item_airline = self._airline(item.get("airline_code"))
        data_airline = self._airline(data.get("airline_code"))
        if item_airline and data_airline and item_airline != data_airline and not allow_generic_airline:
            raise AirlineContactCommunicationIntelligenceError("Linked contact intelligence belongs to another airline.")
        return item

    async def _optional_link(self, entity_type: str, record_id: Any, *, airline_code: Any = None, contact_id: Any = None) -> dict[str, Any] | None:
        if not record_id:
            return None
        item = await self._require(entity_type, str(record_id))
        if airline_code and item.get("airline_code") and self._airline(item.get("airline_code")) != self._airline(airline_code):
            raise AirlineContactCommunicationIntelligenceError("Linked contact intelligence belongs to another airline.")
        if contact_id and item.get("contact_directory_entry_id") != contact_id:
            raise AirlineContactCommunicationIntelligenceError("Linked channel does not belong to the selected contact.")
        return item

    def _agency_visible(self, entity_type: str, item: dict[str, Any], agency_id: str | None) -> bool:
        if item.get("agency_id") not in {None, agency_id}:
            return False
        if entity_type == "channels" and item.get("access_classification") in {"restricted_internal", "platform_only"}:
            return False
        if item.get("publication_status") != "published":
            return False
        visibility = item.get("agency_visibility_status")
        if visibility == "all_agencies":
            return True
        return visibility == "selected_agencies" and agency_id in item.get("visible_agency_ids", [])

    def _agency_projection(self, entity_type: str, item: dict[str, Any]) -> dict[str, Any]:
        projected = {key: value for key, value in item.items() if key not in INTERNAL_FIELDS}
        if entity_type == "channels":
            projected["stores_credentials"] = False
            projected["secret_storage_disabled"] = True
        return self._strip_secret_values(projected)

    def _strip_secret_values(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._strip_secret_values(item) for key, item in value.items() if self._normalize_token(key) not in FORBIDDEN_SECRET_KEYS}
        if isinstance(value, list):
            return [self._strip_secret_values(item) for item in value]
        return value

    def _reject_secrets(self, value: Any, path: str = "payload") -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                normalized = self._normalize_token(key)
                if normalized in FORBIDDEN_SECRET_KEYS or normalized.endswith("_password") or normalized.endswith("_secret") or normalized.endswith("_token") or normalized.endswith("_api_key"):
                    raise AirlineContactCommunicationIntelligenceError(f"Secrets and private credentials are not accepted ({path}.{key}).")
                self._reject_secrets(item, f"{path}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                self._reject_secrets(item, f"{path}[{index}]")

    def _scope_matches(self, record: dict[str, Any], context: dict[str, Any]) -> bool:
        for field, context_field in (
            ("market_scope", "market"),
            ("country_scope", "country"),
            ("airport_scope", "airport"),
            ("route_scope", "route"),
            ("service_scope", "service_code"),
            ("distribution_channel_scope", "distribution_channel"),
        ):
            allowed = {self._normalize_token(value) for value in record.get(field, [])}
            requested = self._normalize_token(context.get(context_field))
            if allowed and (not requested or requested not in allowed):
                return False
        return self._effective(record)

    def _scope_score(self, record: dict[str, Any], context: dict[str, Any]) -> int:
        score = 0
        for field, context_field, weight in (
            ("market_scope", "market", 25),
            ("country_scope", "country", 30),
            ("airport_scope", "airport", 45),
            ("route_scope", "route", 40),
            ("service_scope", "service_code", 35),
            ("distribution_channel_scope", "distribution_channel", 20),
        ):
            requested = self._normalize_token(context.get(context_field))
            allowed = {self._normalize_token(value) for value in record.get(field, [])}
            if requested and requested in allowed:
                score += weight
        return score

    def _template_matches(self, template: dict[str, Any], context: dict[str, Any]) -> bool:
        if template.get("template_status") not in {"active", "approved", "published"} or not self._effective(template):
            return False
        airline = self._airline(context.get("airline_code"))
        if template.get("airline_code") and self._airline(template.get("airline_code")) != airline:
            return False
        for field, context_field in (("desk_type", "desk_type"), ("channel_type", "channel_type"), ("language", "language")):
            configured = self._normalize_token(template.get(field))
            requested = self._normalize_token(context.get(context_field))
            if configured and requested and configured != requested:
                return False
        return True

    def _template_score(self, template: dict[str, Any], context: dict[str, Any]) -> int:
        score = 10 if template.get("airline_code") else 0
        for field in ("desk_type", "channel_type", "language"):
            if template.get(field) and self._normalize_token(template.get(field)) == self._normalize_token(context.get(field)):
                score += 5
        return score + self._scope_score(template, context)

    def _effective(self, item: dict[str, Any]) -> bool:
        today = date.today()
        start = self._parse_date(item.get("effective_from"))
        end = self._parse_date(item.get("effective_until"))
        return (not start or start <= today) and (not end or end >= today)

    def _stale_contacts(self, contacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        return [item for item in contacts if item.get("freshness_status") in {"stale", "expired", "review_due", "unknown"} or item.get("verification_status") != "verified" or (self._parse_datetime(item.get("next_review_at")) and self._parse_datetime(item.get("next_review_at")) <= now)]

    def _summary(self, records: dict[str, list[dict[str, Any]]], stale: list[dict[str, Any]]) -> dict[str, Any]:
        contacts = records.get("contacts", [])
        return {
            "airline_count": len({self._airline(item.get("airline_code")) for item in contacts if item.get("airline_code")}),
            "contact_count": len(contacts),
            "channel_count": len(records.get("channels", [])),
            "template_count": len(records.get("templates", [])),
            "escalation_path_count": len(records.get("escalation-paths", [])),
            "verified_contact_count": sum(item.get("verification_status") == "verified" for item in contacts),
            "stale_contact_count": len(stale),
            "interaction_count": len(records.get("interactions", [])),
        }

    def _matches_filters(self, item: dict[str, Any], filters: dict[str, Any]) -> bool:
        for key, value in filters.items():
            if value is None or value == "":
                continue
            expected = self._normalize_token(value)
            actual = item.get(key)
            if isinstance(actual, list):
                if expected not in {self._normalize_token(entry) for entry in actual}:
                    return False
            elif self._normalize_token(actual) != expected:
                return False
        return True

    async def _require(self, entity_type: str, record_id: str) -> dict[str, Any]:
        _, config = self._config(entity_type)
        item = await self.db.collection(config["collection"]).find_one({"id": record_id})
        if not item:
            item = await self.db.collection(config["collection"]).find_one({config["reference"]: record_id})
        if not item:
            raise AirlineContactCommunicationIntelligenceError("Contact intelligence metadata was not found.")
        return item

    def _config(self, entity_type: str) -> tuple[str, dict[str, Any]]:
        normalized = self._normalize_token(entity_type).replace("_", "-")
        if normalized not in ENTITY_CONFIG:
            raise AirlineContactCommunicationIntelligenceError("Unsupported contact intelligence entity type.")
        return normalized, ENTITY_CONFIG[normalized]

    async def _audit(self, event_type: str, item: dict[str, Any], user: dict[str, Any]) -> None:
        event = AuditEvent(
            agency_id=item.get("agency_id"),
            actor_user_id=user.get("id"),
            event_type=event_type,
            entity_type="airline_contact_communication_intelligence",
            entity_id=item["id"],
            summary=event_type.replace(".", " ").replace("_", " ").title(),
            metadata={"airline_code": item.get("airline_code"), "desk_type": item.get("desk_type"), "metadata_only": True, "message_sent": False},
        )
        await self.db.collection("audit_events").insert_one(event.model_dump(mode="json"))

    def _escalation_recommendation(self, paths: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not paths:
            return None
        path = paths[0]
        return {"path_id": path.get("id"), "path_name": path.get("path_name"), "trigger_after_minutes": path.get("trigger_after_minutes"), "steps": path.get("escalation_steps", []), "automatic_escalation": False}

    def _format_template(self, value: Any, values: _SafeTemplateValues) -> str | None:
        if value is None:
            return None
        try:
            return str(value).format_map(values)
        except (ValueError, KeyError):
            return str(value)

    def _parse_datetime(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if value:
            try:
                parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                return None
        return None

    def _parse_date(self, value: Any) -> date | None:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if value:
            try:
                return date.fromisoformat(str(value)[:10])
            except ValueError:
                return None
        return None

    def _parse_time(self, value: Any) -> time | None:
        if not value:
            return None
        try:
            return time.fromisoformat(str(value))
        except ValueError:
            return None

    def _reference(self, prefix: str) -> str:
        return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

    def _airline(self, value: Any) -> str:
        return str(value or "").strip().upper()

    def _normalize_token(self, value: Any) -> str:
        return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")

    def _sort_text(self, value: Any) -> str:
        return str(value or "")

    def _unique(self, values: list[Any]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            text = str(value).strip()
            key = self._normalize_token(text)
            if text and key not in seen:
                seen.add(key)
                result.append(text)
        return result
