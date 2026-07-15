from __future__ import annotations

import json
from datetime import date, datetime, timezone
from hashlib import sha256
from typing import Any

from database import Database
from models import (
    AuditEvent,
    DocumentPackageCreate,
    JourneyOfferAcceptanceHandoff,
    JourneyOfferClientDecision,
    JourneyOfferClientInteraction,
    JourneyOfferClientQuestion,
    JourneyOfferDelivery,
    JourneyOfferDeliveryAuditEvent,
    JourneyOfferDeliveryRecipient,
    JourneyOfferDeliveryVersion,
    JourneyOfferDocumentPackageLink,
    JourneyOfferWarningAcknowledgement,
    OfferAcceptanceCreate,
    OperationalTimeline,
    new_id,
)
from services.document_render_service import DocumentRenderService
from services.journey_comparison_client_presentation_service import (
    JourneyComparisonClientPresentationService,
)
from services.offer_acceptance_service import OfferAcceptanceService


PHASE_LABEL = "phase_56_4_offer_delivery_client_interaction_foundation"

DELIVERY_COLLECTION = "journey_offer_deliveries"
VERSION_COLLECTION = "journey_offer_delivery_versions"
RECIPIENT_COLLECTION = "journey_offer_delivery_recipients"
INTERACTION_COLLECTION = "journey_offer_client_interactions"
DECISION_COLLECTION = "journey_offer_client_decisions"
QUESTION_COLLECTION = "journey_offer_client_questions"
ACKNOWLEDGEMENT_COLLECTION = "journey_offer_warning_acknowledgements"
DOCUMENT_LINK_COLLECTION = "journey_offer_document_package_links"
ACCEPTANCE_HANDOFF_COLLECTION = "journey_offer_acceptance_handoffs"
AUDIT_COLLECTION = "journey_offer_delivery_audit_events"

DELIVERY_COLLECTIONS = [
    DELIVERY_COLLECTION,
    VERSION_COLLECTION,
    RECIPIENT_COLLECTION,
    INTERACTION_COLLECTION,
    DECISION_COLLECTION,
    QUESTION_COLLECTION,
    ACKNOWLEDGEMENT_COLLECTION,
    DOCUMENT_LINK_COLLECTION,
    ACCEPTANCE_HANDOFF_COLLECTION,
    AUDIT_COLLECTION,
]

DELIVERY_STATUSES = [
    "draft", "preparing", "review_required", "ready_for_release", "released", "viewed",
    "client_action_received", "accepted", "declined", "change_requested", "expired", "revoked",
    "superseded", "archived",
]
VERSION_STATUSES = ["draft", "ready_for_release", "released", "expired", "revoked", "superseded", "archived"]
RECIPIENT_STATUSES = ["authorized", "revoked", "expired"]
RECIPIENT_ROLES = ["client", "passenger", "travel_coordinator", "authorized_representative"]
INTERACTION_TYPES = [
    "opened", "option_expanded", "fare_brand_expanded", "baggage_expanded", "conditions_expanded",
    "service_suitability_expanded", "warning_acknowledged", "document_requested", "document_downloaded",
    "question_submitted", "preferred_option_selected", "preferred_fare_brand_selected", "acceptance_started",
    "decision_submitted",
]
DECISION_TYPES = ["accept", "decline", "request_changes", "ask_question", "save_for_later"]
AUDIT_EVENT_TYPES = [
    "created", "updated", "reviewed", "released", "opened", "version_superseded", "expired", "revoked",
    "decision_received", "handoff_previewed", "handoff_applied", "document_requested", "document_generated",
    "document_downloaded",
]

VALIDATION_CODES = [
    "DELIVERY_SOURCE_REQUIRED", "PRESENTATION_NOT_FOUND", "PRESENTATION_AGENCY_MISMATCH",
    "PRESENTATION_NOT_CLIENT_READY", "PRESENTATION_SNAPSHOT_REQUIRED",
    "PRESENTATION_SNAPSHOT_NOT_FINALIZED", "PRESENTATION_SNAPSHOT_HASH_MISMATCH", "OFFER_NOT_FOUND",
    "OFFER_PRESENTATION_MISMATCH",
    "OFFER_AGENCY_MISMATCH", "CLIENT_REQUIRED", "RECIPIENT_REQUIRED", "RECIPIENT_NOT_AUTHORIZED",
    "RECIPIENT_REVOKED", "CLIENT_PAYLOAD_EMPTY", "CLIENT_PAYLOAD_INTERNAL_FIELD_DETECTED",
    "DELIVERY_VERSION_IMMUTABLE", "DELIVERY_VERSION_NOT_RELEASED", "DELIVERY_VERSION_SUPERSEDED",
    "DELIVERY_EXPIRED", "DELIVERY_REVOKED", "DELIVERY_ALREADY_RELEASED", "OPTION_SELECTION_REQUIRED",
    "OPTION_NOT_IN_RELEASED_VERSION", "FARE_BRAND_SELECTION_REQUIRED", "FARE_BRAND_NOT_IN_SELECTED_OPTION",
    "MANDATORY_WARNING_NOT_ACKNOWLEDGED", "CLIENT_BLOCKING_WARNING_PRESENT", "DECISION_ALREADY_SUBMITTED",
    "DECISION_VERSION_MISMATCH", "ACCEPTANCE_HANDOFF_NOT_READY", "CANONICAL_OFFER_REQUIRED_FOR_ACCEPTANCE",
    "DOCUMENT_HANDOFF_NOT_READY", "UNKNOWN_VALUE_PRESERVED", "AGENCY_ISOLATION_VIOLATION",
]

CLIENT_RESTRICTED_FIELDS = {
    "agency_id", "internal_title", "internal_notes", "internal_summary", "internal_operational_text",
    "internal_connection_text", "internal_operational_summary", "internal_text", "internal_payload",
    "snapshot_payload", "source_provenance", "source_references", "calculation_trace", "evidence_refs",
    "knowledge_version_refs", "restricted_contacts", "source_urls", "source_locations", "supplier_cost",
    "supplier_amount", "margin", "markup_amount", "commission", "internal_cost", "created_by",
    "updated_by", "metadata",
}


class JourneyOfferDeliveryError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class ImmutableJourneyOfferDeliveryVersionError(JourneyOfferDeliveryError):
    pass


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_none=True, exclude_unset=True)
    return {key: value for key, value in dict(payload or {}).items() if value is not None}


class OfferDeliveryClientInteractionService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.presentations = JourneyComparisonClientPresentationService(db)
        self.acceptance = OfferAcceptanceService(db)
        self.documents = DocumentRenderService(db)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "offer_delivery_enabled": True,
            "immutable_delivery_versions_enabled": True,
            "authenticated_client_access_enabled": True,
            "recipient_authorization_enabled": True,
            "agency_isolation_enabled": True,
            "client_safe_payload_enabled": True,
            "internal_payload_exposure_disabled": True,
            "interactive_option_review_enabled": True,
            "interactive_fare_brand_review_enabled": True,
            "itinerary_timeline_enabled": True,
            "connection_detail_presentation_enabled": True,
            "baggage_comparison_enabled": True,
            "flexibility_comparison_enabled": True,
            "special_service_suitability_enabled": True,
            "explicit_unknown_state_enabled": True,
            "warning_acknowledgement_enabled": True,
            "client_questions_enabled": True,
            "explicit_client_decisions_enabled": True,
            "acceptance_handoff_preview_enabled": True,
            "canonical_offer_acceptance_handoff_enabled": True,
            "automatic_booking_disabled": True,
            "immutable_document_source_enabled": True,
            "document_package_handoff_enabled": True,
            "expiry_control_enabled": True,
            "revocation_enabled": True,
            "supersession_enabled": True,
            "audit_history_enabled": True,
            "public_share_links_disabled": True,
            "anonymous_access_disabled": True,
            "live_availability_disabled": True,
            "live_pricing_disabled": True,
            "provider_connectivity_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "scraping_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_publication_disabled": True,
            "automatic_production_seeding_disabled": True,
            "metadata_only": True,
        }

    def filters(self) -> dict[str, Any]:
        return {
            "delivery_statuses": DELIVERY_STATUSES,
            "version_statuses": VERSION_STATUSES,
            "recipient_statuses": RECIPIENT_STATUSES,
            "recipient_roles": RECIPIENT_ROLES,
            "interaction_types": INTERACTION_TYPES,
            "decision_types": DECISION_TYPES,
            "validation_codes": VALIDATION_CODES,
            "audit_event_types": AUDIT_EVENT_TYPES,
        }

    async def create_from_presentation(
        self, agency_id: str, presentation_id: str, payload: Any, user: dict[str, Any]
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        presentation = await self.db.collection("journey_comparison_presentations").find_one(
            {"agency_id": agency_id, "id": presentation_id}
        )
        if not presentation:
            raise JourneyOfferDeliveryError("PRESENTATION_NOT_FOUND", "Offer comparison was not found for this agency.")
        if presentation.get("archived_at") or presentation.get("status") not in {"client_ready", "approved", "handed_off"}:
            raise JourneyOfferDeliveryError("PRESENTATION_NOT_CLIENT_READY", "The source presentation must be finalized or approved before delivery preparation.")
        snapshot = await self._select_presentation_snapshot(agency_id, presentation_id, data.get("presentation_snapshot_id"))
        presentation_offer_id = str(presentation.get("offer_id") or "")
        requested_offer_id = str(data.get("offer_id") or "")
        if presentation_offer_id and requested_offer_id and presentation_offer_id != requested_offer_id:
            raise JourneyOfferDeliveryError(
                "OFFER_PRESENTATION_MISMATCH",
                "The approved Offer Comparison belongs to a different Offer Workspace.",
            )
        offer_id = presentation_offer_id or requested_offer_id
        if not offer_id:
            raise JourneyOfferDeliveryError("OFFER_NOT_FOUND", "A canonical Offer Workspace is required for delivery.")
        canonical_offer = await self.db.collection("offer_workspaces").find_one({"agency_id": agency_id, "id": offer_id})
        if not canonical_offer:
            raise JourneyOfferDeliveryError("OFFER_NOT_FOUND", "The canonical Offer Workspace was not found for this agency.")
        client_id = str(data.get("client_id") or (presentation.get("metadata") or {}).get("client_id") or "")
        if not client_id:
            raise JourneyOfferDeliveryError("CLIENT_REQUIRED", "A canonical client is required for controlled delivery.")
        client = await self.db.collection("client_profiles").find_one({"agency_id": agency_id, "id": client_id})
        if not client or client.get("status") == "archived":
            raise JourneyOfferDeliveryError("CLIENT_REQUIRED", "The selected client was not found for this agency.")
        passenger_ids = self._tokens(data.get("passenger_ids") or [])
        await self._validate_passengers(agency_id, client_id, passenger_ids)

        existing = await self.db.collection(DELIVERY_COLLECTION).find_one({
            "agency_id": agency_id,
            "offer_id": offer_id,
            "presentation_snapshot_id": snapshot["id"],
            "client_id": client_id,
            "archived_at": None,
        })
        if existing:
            return {**await self.get_delivery(agency_id, existing["id"]), "created": False, "idempotent": True}

        expires_at = self._dt(data.get("expires_at"))
        values = {
            "agency_id": agency_id,
            "delivery_code": data.get("delivery_code") or f"OD-{new_id()[:8].upper()}",
            "presentation_id": presentation_id,
            "presentation_snapshot_id": snapshot["id"],
            "journey_id": presentation["journey_id"],
            "composition_id": presentation["composition_id"],
            "offer_id": offer_id,
            "trip_id": data.get("trip_id") or presentation.get("trip_id"),
            "client_id": client_id,
            "passenger_ids": passenger_ids,
            "status": "draft",
            "audience_type": data.get("audience_type") or presentation.get("audience_type") or "client",
            "language_code": data.get("language_code") or presentation.get("language_code") or "en",
            "currency_code": data.get("currency_code") or presentation.get("currency_code") or "EUR",
            "title": data.get("title") or presentation.get("client_title") or presentation.get("title"),
            "client_intro": data.get("client_intro") or presentation.get("client_intro_text"),
            "client_footer": data.get("client_footer"),
            "expires_at": expires_at,
            "created_by": self._actor(user),
            "updated_by": self._actor(user),
            "metadata": {"source_presentation_status": presentation.get("status")},
        }
        delivery = await self.db.collection(DELIVERY_COLLECTION).insert_one(
            JourneyOfferDelivery(**values).model_dump(mode="json")
        )
        version = await self._create_version(delivery, snapshot, data, user)
        await self._audit("created", delivery, user, version_id=version["id"], summary="Offer delivery created from an approved comparison version.")
        return {**await self.get_delivery(agency_id, delivery["id"]), "created": True}

    async def create_from_offer(
        self, agency_id: str, offer_id: str, payload: Any, user: dict[str, Any]
    ) -> dict[str, Any]:
        offer = await self.db.collection("offer_workspaces").find_one({"agency_id": agency_id, "id": offer_id})
        if not offer:
            raise JourneyOfferDeliveryError("OFFER_NOT_FOUND", "Offer Workspace was not found for this agency.")
        presentations = await self.presentations.list_presentations(agency_id, offer_id=offer_id, include_archived=False)
        ready = [item for item in presentations if item.get("status") in {"client_ready", "approved", "handed_off"}]
        if not ready:
            raise JourneyOfferDeliveryError("PRESENTATION_NOT_CLIENT_READY", "An approved Offer Comparison linked to this Offer is required.")
        return await self.create_from_presentation(
            agency_id, ready[0]["id"], {**payload_dict(payload), "offer_id": offer_id}, user
        )

    async def list_deliveries(self, agency_id: str | None = None, **filters: Any) -> list[dict[str, Any]]:
        rows = await self.db.collection(DELIVERY_COLLECTION).find_many({"agency_id": agency_id} if agency_id else None)
        if not filters.get("include_archived"):
            rows = [item for item in rows if not item.get("archived_at")]
        for field in ["status", "client_id", "journey_id", "offer_id", "presentation_id"]:
            if filters.get(field):
                rows = [item for item in rows if item.get(field) == filters[field]]
        if filters.get("passenger_id"):
            rows = [item for item in rows if filters["passenger_id"] in (item.get("passenger_ids") or [])]
        if filters.get("expiry") == "expired":
            rows = [item for item in rows if self._expired(item)]
        if filters.get("expiry") == "active":
            rows = [item for item in rows if not self._expired(item)]
        return sorted(rows, key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)

    async def get_delivery(self, agency_id: str, delivery_id: str) -> dict[str, Any]:
        delivery = await self._require_delivery(agency_id, delivery_id)
        related: dict[str, list[dict[str, Any]]] = {}
        for key, collection in {
            "versions": VERSION_COLLECTION,
            "recipients": RECIPIENT_COLLECTION,
            "interactions": INTERACTION_COLLECTION,
            "decisions": DECISION_COLLECTION,
            "questions": QUESTION_COLLECTION,
            "warning_acknowledgements": ACKNOWLEDGEMENT_COLLECTION,
            "documents": DOCUMENT_LINK_COLLECTION,
            "acceptance_handoffs": ACCEPTANCE_HANDOFF_COLLECTION,
            "audit_events": AUDIT_COLLECTION,
        }.items():
            related[key] = await self.db.collection(collection).find_many({"agency_id": agency_id, "delivery_id": delivery_id})
        related["versions"] = sorted(related["versions"], key=lambda item: int(item.get("version_number") or 0), reverse=True)
        for key in ["interactions", "decisions", "questions", "audit_events"]:
            related[key] = sorted(related[key], key=lambda item: str(item.get("occurred_at") or item.get("submitted_at") or item.get("created_at") or ""), reverse=True)
        return {"phase": PHASE_LABEL, "delivery": delivery, **related, **self.safety_flags()}

    async def update_delivery(
        self, agency_id: str, delivery_id: str, payload: Any, user: dict[str, Any]
    ) -> dict[str, Any]:
        delivery = await self._require_delivery(agency_id, delivery_id)
        data = payload_dict(payload)
        allowed = {"title", "client_intro", "client_footer", "language_code", "currency_code", "audience_type", "expires_at", "passenger_ids"}
        updates = {key: value for key, value in data.items() if key in allowed}
        released = await self.db.collection(VERSION_COLLECTION).find_one({"agency_id": agency_id, "delivery_id": delivery_id, "status": "released"})
        if released and any(key in updates for key in {"expires_at", "language_code", "currency_code", "audience_type", "passenger_ids"}):
            raise JourneyOfferDeliveryError("DELIVERY_VERSION_IMMUTABLE", "Released delivery terms are immutable; create a new version instead.")
        if "expires_at" in updates:
            updates["expires_at"] = self._dt(updates["expires_at"])
        if "passenger_ids" in updates:
            updates["passenger_ids"] = self._tokens(updates["passenger_ids"])
            await self._validate_passengers(agency_id, delivery["client_id"], updates["passenger_ids"])
        updates["updated_by"] = self._actor(user)
        stored = await self.db.collection(DELIVERY_COLLECTION).update_one({"agency_id": agency_id, "id": delivery_id}, updates)
        await self._audit("updated", stored or delivery, user, summary="Offer delivery preparation metadata updated.")
        return {"phase": PHASE_LABEL, "delivery": stored or delivery, **self.safety_flags()}

    async def archive_delivery(self, agency_id: str, delivery_id: str, user: dict[str, Any]) -> dict[str, Any]:
        delivery = await self._require_delivery(agency_id, delivery_id)
        stored = await self.db.collection(DELIVERY_COLLECTION).update_one(
            {"agency_id": agency_id, "id": delivery_id},
            {"status": "archived", "archived_at": self._now(), "updated_by": self._actor(user)},
        )
        await self._audit("updated", stored or delivery, user, summary="Offer delivery archived non-destructively.")
        return {"phase": PHASE_LABEL, "delivery": stored or delivery, "physical_deletion_performed": False, **self.safety_flags()}

    async def revoke_delivery(self, agency_id: str, delivery_id: str, user: dict[str, Any]) -> dict[str, Any]:
        delivery = await self._require_delivery(agency_id, delivery_id)
        now = self._now()
        stored = await self.db.collection(DELIVERY_COLLECTION).update_one(
            {"agency_id": agency_id, "id": delivery_id},
            {"status": "revoked", "revoked_at": now, "updated_by": self._actor(user)},
        )
        for version in await self.list_versions(agency_id, delivery_id):
            if version.get("status") == "released":
                await self.db.collection(VERSION_COLLECTION).update_one({"agency_id": agency_id, "id": version["id"]}, {"status": "revoked"})
        for recipient in await self.list_recipients(agency_id, delivery_id):
            if recipient.get("access_status") == "authorized":
                await self.db.collection(RECIPIENT_COLLECTION).update_one({"agency_id": agency_id, "id": recipient["id"]}, {"access_status": "revoked", "revoked_at": now})
        await self._audit("revoked", stored or delivery, user, summary="Offer delivery access revoked.")
        return {"phase": PHASE_LABEL, "delivery": stored or delivery, **self.safety_flags()}

    async def preview_client(self, agency_id: str, delivery_id: str) -> dict[str, Any]:
        delivery = await self._require_delivery(agency_id, delivery_id)
        version = await self._latest_version(agency_id, delivery_id)
        return {
            "phase": PHASE_LABEL,
            "delivery": self._client_delivery(delivery),
            "version": self._client_version(version) if version else None,
            "client_safe_payload": (version or {}).get("client_payload") or {},
            "restricted_content_removed": True,
            **self.safety_flags(),
        }

    async def preview_internal(self, agency_id: str, delivery_id: str) -> dict[str, Any]:
        return {**await self.get_delivery(agency_id, delivery_id), "agency_authorized_internal_view": True}

    async def create_recipient(
        self, agency_id: str, delivery_id: str, payload: Any, user: dict[str, Any]
    ) -> dict[str, Any]:
        delivery = await self._require_delivery(agency_id, delivery_id)
        data = payload_dict(payload)
        client_id = str(data.get("client_id") or delivery["client_id"])
        if client_id != delivery["client_id"]:
            raise JourneyOfferDeliveryError("RECIPIENT_NOT_AUTHORIZED", "Recipient client must match the delivery client.")
        mapping = None
        portal_user_id = data.get("portal_user_id")
        if portal_user_id:
            mapping = await self.db.collection("portal_access_mappings").find_one({"agency_id": agency_id, "id": portal_user_id, "client_id": client_id})
        elif data.get("email_reference"):
            mapping = await self.db.collection("portal_access_mappings").find_one({"agency_id": agency_id, "client_id": client_id, "user_email": data["email_reference"]})
        if (portal_user_id or data.get("email_reference")) and not mapping:
            raise JourneyOfferDeliveryError("RECIPIENT_NOT_AUTHORIZED", "Recipient must resolve to an existing portal identity for this client and agency.")
        if mapping and mapping.get("portal_status") != "active":
            raise JourneyOfferDeliveryError("RECIPIENT_NOT_AUTHORIZED", "Recipient portal access is not active.")
        passenger_id = data.get("passenger_id")
        if passenger_id:
            await self._validate_passengers(agency_id, client_id, [passenger_id])
        role = data.get("recipient_role") or ("passenger" if passenger_id else "client")
        self._choice(role, RECIPIENT_ROLES, "recipient role")
        existing = await self.db.collection(RECIPIENT_COLLECTION).find_one({
            "agency_id": agency_id,
            "delivery_id": delivery_id,
            "client_id": client_id,
            "passenger_id": passenger_id,
            "portal_user_id": (mapping or {}).get("id") or portal_user_id,
        })
        if existing:
            return {"phase": PHASE_LABEL, "recipient": existing, "created": False, "idempotent": True, **self.safety_flags()}
        values = {
            **data,
            "agency_id": agency_id,
            "delivery_id": delivery_id,
            "client_id": client_id,
            "portal_user_id": (mapping or {}).get("id") or portal_user_id,
            "recipient_role": role,
            "display_name": data.get("display_name") or (mapping or {}).get("display_name") or "Authorized recipient",
            "email_reference": data.get("email_reference") or (mapping or {}).get("user_email"),
            "access_status": "authorized",
            "invited_at": self._now(),
        }
        recipient = await self.db.collection(RECIPIENT_COLLECTION).insert_one(
            JourneyOfferDeliveryRecipient(**values).model_dump(mode="json")
        )
        await self._audit("updated", delivery, user, recipient_id=recipient["id"], summary="Authorized delivery recipient added.")
        return {"phase": PHASE_LABEL, "recipient": recipient, "created": True, **self.safety_flags()}

    async def list_recipients(self, agency_id: str, delivery_id: str) -> list[dict[str, Any]]:
        await self._require_delivery(agency_id, delivery_id)
        return await self.db.collection(RECIPIENT_COLLECTION).find_many({"agency_id": agency_id, "delivery_id": delivery_id})

    async def update_recipient(
        self, agency_id: str, delivery_id: str, recipient_id: str, payload: Any, user: dict[str, Any]
    ) -> dict[str, Any]:
        recipient = await self._require_recipient(agency_id, delivery_id, recipient_id)
        allowed = {"recipient_role", "display_name", "locale", "timezone", "access_status"}
        updates = {key: value for key, value in payload_dict(payload).items() if key in allowed}
        if "recipient_role" in updates:
            self._choice(updates["recipient_role"], RECIPIENT_ROLES, "recipient role")
        if "access_status" in updates:
            self._choice(updates["access_status"], RECIPIENT_STATUSES, "recipient status")
        stored = await self.db.collection(RECIPIENT_COLLECTION).update_one({"agency_id": agency_id, "id": recipient_id}, updates)
        delivery = await self._require_delivery(agency_id, delivery_id)
        await self._audit("updated", delivery, user, recipient_id=recipient_id, summary="Authorized recipient metadata updated.")
        return {"phase": PHASE_LABEL, "recipient": stored or recipient, **self.safety_flags()}

    async def revoke_recipient(
        self, agency_id: str, delivery_id: str, recipient_id: str, user: dict[str, Any]
    ) -> dict[str, Any]:
        recipient = await self._require_recipient(agency_id, delivery_id, recipient_id)
        stored = await self.db.collection(RECIPIENT_COLLECTION).update_one(
            {"agency_id": agency_id, "id": recipient_id}, {"access_status": "revoked", "revoked_at": self._now()}
        )
        delivery = await self._require_delivery(agency_id, delivery_id)
        await self._audit("revoked", delivery, user, recipient_id=recipient_id, summary="Recipient access revoked.")
        return {"phase": PHASE_LABEL, "recipient": stored or recipient, **self.safety_flags()}

    async def list_versions(self, agency_id: str, delivery_id: str) -> list[dict[str, Any]]:
        await self._require_delivery(agency_id, delivery_id)
        rows = await self.db.collection(VERSION_COLLECTION).find_many({"agency_id": agency_id, "delivery_id": delivery_id})
        return sorted(rows, key=lambda item: int(item.get("version_number") or 0), reverse=True)

    async def create_version(
        self, agency_id: str, delivery_id: str, payload: Any, user: dict[str, Any]
    ) -> dict[str, Any]:
        delivery = await self._require_delivery(agency_id, delivery_id)
        data = payload_dict(payload)
        snapshot = await self._select_presentation_snapshot(
            agency_id, delivery["presentation_id"], data.get("presentation_snapshot_id") or delivery["presentation_snapshot_id"]
        )
        version = await self._create_version(delivery, snapshot, data, user)
        await self._audit("updated", delivery, user, version_id=version["id"], summary="Draft delivery version created from immutable presentation snapshot.")
        return {"phase": PHASE_LABEL, "version": version, **self.safety_flags()}

    async def get_version(self, agency_id: str, delivery_id: str, version_id: str) -> dict[str, Any]:
        version = await self._require_version(agency_id, delivery_id, version_id)
        return {"phase": PHASE_LABEL, "version": version, **self.safety_flags()}

    async def validate_version(self, agency_id: str, delivery_id: str, version_id: str) -> dict[str, Any]:
        delivery = await self._require_delivery(agency_id, delivery_id)
        version = await self._require_version(agency_id, delivery_id, version_id)
        findings: list[dict[str, Any]] = []
        payload = version.get("client_payload") or {}
        if not payload:
            findings.append(self._finding("CLIENT_PAYLOAD_EMPTY", "blocking", "The released client payload cannot be empty."))
        leaked = sorted(self._restricted_keys(payload))
        if leaked:
            findings.append(self._finding("CLIENT_PAYLOAD_INTERNAL_FIELD_DETECTED", "blocking", f"Restricted client fields detected: {', '.join(leaked)}."))
        snapshot = await self.db.collection("journey_presentation_snapshots").find_one({
            "agency_id": agency_id, "id": version["source_presentation_snapshot_id"], "presentation_id": delivery["presentation_id"]
        })
        if not snapshot:
            findings.append(self._finding("PRESENTATION_SNAPSHOT_REQUIRED", "blocking", "The source snapshot no longer resolves."))
        elif not snapshot.get("finalized"):
            findings.append(self._finding("PRESENTATION_SNAPSHOT_NOT_FINALIZED", "blocking", "Only finalized presentation snapshots can be released."))
        elif snapshot.get("source_hash") != version.get("source_snapshot_hash"):
            findings.append(self._finding("PRESENTATION_SNAPSHOT_HASH_MISMATCH", "blocking", "The preserved source snapshot hash does not match."))
        if version.get("payload_hash") != self._hash(payload):
            findings.append(self._finding("PRESENTATION_SNAPSHOT_HASH_MISMATCH", "blocking", "The deterministic delivery payload hash does not match."))
        recipients = await self.list_recipients(agency_id, delivery_id)
        if not any(item.get("access_status") == "authorized" for item in recipients):
            findings.append(self._finding("RECIPIENT_REQUIRED", "blocking", "At least one authorized recipient is required before release."))
        for warning in payload.get("warnings") or []:
            if warning.get("client_blocking"):
                findings.append(self._finding("CLIENT_BLOCKING_WARNING_PRESENT", "blocking", warning.get("message") or "A client-blocking warning remains unresolved."))
        unknown_count = self._unknown_count(payload)
        if unknown_count:
            findings.append(self._finding("UNKNOWN_VALUE_PRESERVED", "unknown", f"{unknown_count} unknown values remain explicit for client review."))
        blocking = [item for item in findings if item["severity"] == "blocking"]
        return {
            "phase": PHASE_LABEL,
            "delivery_id": delivery_id,
            "version_id": version_id,
            "findings": findings,
            "blocking_count": len(blocking),
            "unknown_count": unknown_count,
            "can_release": not blocking,
            **self.safety_flags(),
        }

    async def release_version(
        self, agency_id: str, delivery_id: str, version_id: str, payload: Any, user: dict[str, Any]
    ) -> dict[str, Any]:
        delivery = await self._require_delivery(agency_id, delivery_id)
        version = await self._require_version(agency_id, delivery_id, version_id)
        if version.get("immutable") or version.get("status") == "released":
            raise ImmutableJourneyOfferDeliveryVersionError("DELIVERY_ALREADY_RELEASED", "Released delivery versions are immutable and cannot be released again.")
        validation = await self.validate_version(agency_id, delivery_id, version_id)
        if not validation["can_release"]:
            raise JourneyOfferDeliveryError("PRESENTATION_NOT_CLIENT_READY", "Delivery release is blocked by deterministic validation findings.")
        now = self._now()
        stored = await self.db.collection(VERSION_COLLECTION).update_one(
            {"agency_id": agency_id, "id": version_id},
            {
                "status": "released", "immutable": True, "released_by": self._actor(user), "released_at": now,
                "finalized_at": now, "release_notes": payload_dict(payload).get("release_notes") or version.get("release_notes"),
            },
        )
        await self.db.collection(DELIVERY_COLLECTION).update_one(
            {"agency_id": agency_id, "id": delivery_id},
            {"status": "released", "released_at": now, "updated_by": self._actor(user)},
        )
        for recipient in await self.list_recipients(agency_id, delivery_id):
            if recipient.get("access_status") == "authorized":
                await self.db.collection(RECIPIENT_COLLECTION).update_one(
                    {"agency_id": agency_id, "id": recipient["id"]}, {"delivery_version_id": version_id}
                )
        await self._audit("released", delivery, user, version_id=version_id, summary="Immutable offer delivery version explicitly released.")
        await self._timeline(delivery, "offer_created", "Offer delivery released", user)
        return {"phase": PHASE_LABEL, "version": stored or version, "validation": validation, "notification_sent": False, **self.safety_flags()}

    async def supersede_version(
        self, agency_id: str, delivery_id: str, version_id: str, payload: Any, user: dict[str, Any]
    ) -> dict[str, Any]:
        delivery = await self._require_delivery(agency_id, delivery_id)
        version = await self._require_version(agency_id, delivery_id, version_id)
        next_id = payload_dict(payload).get("superseded_by_version_id")
        if not next_id:
            candidates = [item for item in await self.list_versions(agency_id, delivery_id) if item["id"] != version_id]
            next_version = candidates[0] if candidates else None
        else:
            next_version = await self._require_version(agency_id, delivery_id, str(next_id))
        if not next_version:
            raise JourneyOfferDeliveryError("DELIVERY_SOURCE_REQUIRED", "Create a replacement delivery version before superseding this version.")
        stored = await self.db.collection(VERSION_COLLECTION).update_one(
            {"agency_id": agency_id, "id": version_id},
            {"status": "superseded", "superseded_by_version_id": next_version["id"]},
        )
        await self.db.collection(VERSION_COLLECTION).update_one(
            {"agency_id": agency_id, "id": next_version["id"]}, {"supersedes_version_id": version_id}
        )
        await self.db.collection(DELIVERY_COLLECTION).update_one(
            {"agency_id": agency_id, "id": delivery_id}, {"status": "superseded", "superseded_at": self._now()}
        )
        await self._audit("version_superseded", delivery, user, version_id=version_id, summary="Delivery version superseded without deleting history.")
        return {"phase": PHASE_LABEL, "version": stored or version, "replacement_version": next_version, **self.safety_flags()}

    async def list_interactions(self, agency_id: str, delivery_id: str) -> list[dict[str, Any]]:
        await self._require_delivery(agency_id, delivery_id)
        rows = await self.db.collection(INTERACTION_COLLECTION).find_many({"agency_id": agency_id, "delivery_id": delivery_id})
        return sorted(rows, key=lambda item: str(item.get("occurred_at") or ""), reverse=True)

    async def list_decisions(self, agency_id: str, delivery_id: str) -> list[dict[str, Any]]:
        await self._require_delivery(agency_id, delivery_id)
        rows = await self.db.collection(DECISION_COLLECTION).find_many({"agency_id": agency_id, "delivery_id": delivery_id})
        return sorted(rows, key=lambda item: str(item.get("submitted_at") or ""), reverse=True)

    async def list_questions(self, agency_id: str, delivery_id: str) -> list[dict[str, Any]]:
        await self._require_delivery(agency_id, delivery_id)
        rows = await self.db.collection(QUESTION_COLLECTION).find_many({"agency_id": agency_id, "delivery_id": delivery_id})
        return sorted(rows, key=lambda item: str(item.get("created_at") or ""))

    async def reply_question(
        self, agency_id: str, delivery_id: str, question_id: str, payload: Any, user: dict[str, Any]
    ) -> dict[str, Any]:
        parent = await self.db.collection(QUESTION_COLLECTION).find_one({"agency_id": agency_id, "delivery_id": delivery_id, "id": question_id})
        if not parent:
            raise JourneyOfferDeliveryError("DELIVERY_SOURCE_REQUIRED", "Client question was not found.")
        message = str(payload_dict(payload).get("message_text") or "").strip()
        if not message:
            raise JourneyOfferDeliveryError("DELIVERY_SOURCE_REQUIRED", "A reply message is required.")
        reply = await self.db.collection(QUESTION_COLLECTION).insert_one(JourneyOfferClientQuestion(
            agency_id=agency_id,
            delivery_id=delivery_id,
            delivery_version_id=parent["delivery_version_id"],
            recipient_id=parent["recipient_id"],
            parent_question_id=question_id,
            audience="client",
            message_text=message,
            status="answered",
            created_by_type="agency_user",
            created_by_id=self._actor(user),
            answered_at=self._now(),
        ).model_dump(mode="json"))
        await self.db.collection(QUESTION_COLLECTION).update_one({"agency_id": agency_id, "id": question_id}, {"status": "answered", "answered_at": self._now()})
        return {"phase": PHASE_LABEL, "question": reply, "message_sent": False, **self.safety_flags()}

    async def acceptance_handoff_preview(
        self, agency_id: str, delivery_id: str, payload: Any, user: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        delivery = await self._require_delivery(agency_id, delivery_id)
        data = payload_dict(payload)
        decision = await self._select_accept_decision(agency_id, delivery_id, data.get("decision_id"))
        version = await self._require_actionable_version(agency_id, delivery, decision["delivery_version_id"])
        findings = await self._decision_findings(delivery, version, decision, decision["recipient_id"])
        offer_id = delivery.get("offer_id")
        offer_option_id = await self._resolve_offer_option(agency_id, delivery, version, decision)
        canonical_offer = await self.db.collection("offer_workspaces").find_one(
            {"agency_id": agency_id, "id": offer_id}
        ) if offer_id else None
        if not canonical_offer:
            findings.append(self._finding("CANONICAL_OFFER_REQUIRED_FOR_ACCEPTANCE", "blocking", "A canonical Offer Workspace is required for acceptance."))
        if not offer_option_id:
            findings.append(self._finding("ACCEPTANCE_HANDOFF_NOT_READY", "blocking", "The selected itinerary is not mapped to a canonical Offer option."))
        preview_payload = {
            "delivery_id": delivery_id,
            "delivery_version_id": version["id"],
            "decision_id": decision["id"],
            "offer_id": offer_id,
            "offer_option_id": offer_option_id,
            "selected_option_id": decision.get("selected_option_id"),
            "selected_fare_brand_id": decision.get("selected_fare_brand_id"),
            "source_payload_hash": version.get("payload_hash"),
            "canonical_acceptance_created": False,
            "automatic_booking": False,
        }
        blocking = [item for item in findings if item["severity"] == "blocking"]
        existing = await self.db.collection(ACCEPTANCE_HANDOFF_COLLECTION).find_one({"agency_id": agency_id, "decision_id": decision["id"]})
        if existing:
            handoff = existing
        else:
            handoff = await self.db.collection(ACCEPTANCE_HANDOFF_COLLECTION).insert_one(JourneyOfferAcceptanceHandoff(
                agency_id=agency_id,
                delivery_id=delivery_id,
                delivery_version_id=version["id"],
                decision_id=decision["id"],
                offer_id=offer_id or "unresolved",
                selected_option_id=decision.get("selected_option_id") or "unresolved",
                selected_fare_brand_id=decision.get("selected_fare_brand_id"),
                preview_payload=preview_payload,
                validation_results=findings,
                status="previewed" if not blocking else "blocked",
            ).model_dump(mode="json"))
        await self._audit("handoff_previewed", delivery, user, version_id=version["id"], recipient_id=decision["recipient_id"], summary="Canonical Offer Acceptance handoff previewed.")
        return {"phase": PHASE_LABEL, "handoff": handoff, "preview": preview_payload, "findings": findings, "can_apply": not blocking, **self.safety_flags()}

    async def acceptance_handoff_apply(
        self, agency_id: str, delivery_id: str, payload: Any, user: dict[str, Any]
    ) -> dict[str, Any]:
        preview = await self.acceptance_handoff_preview(agency_id, delivery_id, payload, user)
        handoff = preview["handoff"]
        if handoff.get("canonical_acceptance_id"):
            return {**preview, "created": False, "idempotent": True}
        if not preview["can_apply"]:
            raise JourneyOfferDeliveryError("ACCEPTANCE_HANDOFF_NOT_READY", "Acceptance handoff is blocked by deterministic validation findings.")
        result = await self.acceptance.accept_offer_option(
            agency_id,
            preview["preview"]["offer_id"],
            preview["preview"]["offer_option_id"],
            user,
            OfferAcceptanceCreate(
                acceptance_source="client_preview",
                provider_target="manual",
                client_visible_summary_json={
                    "delivery_id": delivery_id,
                    "delivery_version_id": preview["preview"]["delivery_version_id"],
                    "selected_option_id": preview["preview"]["selected_option_id"],
                    "selected_fare_brand_id": preview["preview"]["selected_fare_brand_id"],
                },
            ),
        )
        if not result or not result.get("acceptance"):
            await self.db.collection(ACCEPTANCE_HANDOFF_COLLECTION).update_one(
                {"agency_id": agency_id, "id": handoff["id"]},
                {"status": "failed", "failure_code": "CANONICAL_ACCEPTANCE_FAILED", "failure_message": "Canonical Offer Acceptance did not return an acceptance."},
            )
            raise JourneyOfferDeliveryError("ACCEPTANCE_HANDOFF_NOT_READY", "Canonical Offer Acceptance could not be applied.")
        acceptance_id = result["acceptance"]["id"]
        stored = await self.db.collection(ACCEPTANCE_HANDOFF_COLLECTION).update_one(
            {"agency_id": agency_id, "id": handoff["id"]},
            {"status": "applied", "canonical_acceptance_id": acceptance_id, "applied_by": self._actor(user), "applied_at": self._now()},
        )
        await self.db.collection(DECISION_COLLECTION).update_one(
            {"agency_id": agency_id, "id": handoff["decision_id"]},
            {"canonical_acceptance_id": acceptance_id, "handoff_status": "applied"},
        )
        delivery = await self._require_delivery(agency_id, delivery_id)
        await self.db.collection(DELIVERY_COLLECTION).update_one({"agency_id": agency_id, "id": delivery_id}, {"status": "accepted"})
        await self._audit("handoff_applied", delivery, user, version_id=handoff["delivery_version_id"], summary="Client decision explicitly handed to canonical Offer Acceptance.")
        await self._timeline(delivery, "offer_accepted", "Client selection handed to Offer Acceptance", user)
        return {"phase": PHASE_LABEL, "handoff": stored or handoff, "canonical_acceptance": result, "booking_created": False, **self.safety_flags()}

    async def document_handoff_preview(
        self, agency_id: str, delivery_id: str, payload: Any
    ) -> dict[str, Any]:
        delivery = await self._require_delivery(agency_id, delivery_id)
        version_id = payload_dict(payload).get("delivery_version_id")
        version = await self._require_actionable_version(agency_id, delivery, version_id) if version_id else await self._latest_released_version(agency_id, delivery_id)
        if not version:
            raise JourneyOfferDeliveryError("DOCUMENT_HANDOFF_NOT_READY", "A released immutable delivery version is required for document preparation.")
        preview = {
            "delivery_id": delivery_id,
            "delivery_version_id": version["id"],
            "source_payload_hash": version["payload_hash"],
            "package_type": "offer_package",
            "document_type": "journey_comparison_offer",
            "formats": ["portal_html", "deterministic_text", "pdf_handoff"],
            "source_is_immutable": bool(version.get("immutable")),
            "rendered": False,
            "sent": False,
            "published": False,
        }
        return {"phase": PHASE_LABEL, "preview": preview, "can_apply": bool(version.get("immutable")), **self.safety_flags()}

    async def document_handoff_apply(
        self, agency_id: str, delivery_id: str, payload: Any, user: dict[str, Any]
    ) -> dict[str, Any]:
        preview = await self.document_handoff_preview(agency_id, delivery_id, payload)
        data = preview["preview"]
        document_links = await self.db.collection(DOCUMENT_LINK_COLLECTION).find_many({
            "agency_id": agency_id, "delivery_version_id": data["delivery_version_id"]
        })
        existing = next((item for item in document_links if item.get("status") != "archived"), None)
        if existing:
            return {"phase": PHASE_LABEL, "document_link": existing, "created": False, "idempotent": True, **self.safety_flags()}
        package_result = await self.documents.create_document_package(
            agency_id,
            DocumentPackageCreate(
                package_type="offer_package",
                title=f"Offer delivery {delivery_id}",
                source_context_type="mixed_context",
                source_context_id=delivery_id,
                source_context_ids_json={
                    "offer_delivery_id": delivery_id,
                    "offer_delivery_version_id": data["delivery_version_id"],
                    "source_payload_hash": data["source_payload_hash"],
                },
                document_render_job_ids=[],
            ),
            user,
        )
        package = package_result["package"]
        delivery = await self._require_delivery(agency_id, delivery_id)
        link = await self.db.collection(DOCUMENT_LINK_COLLECTION).insert_one(JourneyOfferDocumentPackageLink(
            agency_id=agency_id,
            delivery_id=delivery_id,
            delivery_version_id=data["delivery_version_id"],
            document_package_id=package["id"],
            language_code=delivery.get("language_code") or "en",
            status="prepared",
            generated_at=self._now(),
            available_at=self._now(),
            checksum=data["source_payload_hash"],
        ).model_dump(mode="json"))
        await self._audit("document_generated", delivery, user, version_id=data["delivery_version_id"], summary="Document package metadata linked to immutable delivery version.")
        return {"phase": PHASE_LABEL, "document_link": link, "document_package": package, "rendered": False, "sent": False, **self.safety_flags()}

    async def list_documents(self, agency_id: str, delivery_id: str) -> list[dict[str, Any]]:
        await self._require_delivery(agency_id, delivery_id)
        return await self.db.collection(DOCUMENT_LINK_COLLECTION).find_many({"agency_id": agency_id, "delivery_id": delivery_id})

    async def list_audit_events(self, agency_id: str, delivery_id: str) -> list[dict[str, Any]]:
        await self._require_delivery(agency_id, delivery_id)
        rows = await self.db.collection(AUDIT_COLLECTION).find_many({"agency_id": agency_id, "delivery_id": delivery_id})
        return sorted(rows, key=lambda item: str(item.get("occurred_at") or item.get("created_at") or ""), reverse=True)

    async def portal_list(self, context: dict[str, Any]) -> dict[str, Any]:
        agency_id = context["account"]["agency_id"]
        client_id = context["account"]["client_id"]
        deliveries = await self.list_deliveries(agency_id, client_id=client_id, include_archived=True)
        items = []
        for delivery in deliveries:
            recipient = await self._portal_recipient(context, delivery["id"], required=False)
            if not recipient:
                continue
            version = await self._latest_client_visible_version(agency_id, delivery["id"])
            if version:
                items.append({**self._client_delivery(delivery), "version": self._client_version(version)})
        return {"phase": PHASE_LABEL, "items": items, "count": len(items), "authenticated": True, **self._portal_safety_flags()}

    async def portal_detail(
        self, context: dict[str, Any], delivery_id: str, *, record_open: bool = False
    ) -> dict[str, Any]:
        recipient = await self._portal_recipient(context, delivery_id)
        agency_id = context["account"]["agency_id"]
        delivery = await self._require_delivery(agency_id, delivery_id)
        version = await self._latest_client_visible_version(agency_id, delivery_id)
        if not version:
            raise JourneyOfferDeliveryError("DELIVERY_VERSION_NOT_RELEASED", "No released delivery version is available.")
        await self._require_actionable_version(agency_id, delivery, version["id"], historical_ok=True)
        if record_open:
            await self._record_interaction(delivery, version, recipient, "opened")
            now = self._now()
            recipient_updates = {"last_opened_at": now}
            if not recipient.get("first_opened_at"):
                recipient_updates["first_opened_at"] = now
            await self.db.collection(RECIPIENT_COLLECTION).update_one({"agency_id": agency_id, "id": recipient["id"]}, recipient_updates)
            if delivery.get("status") == "released":
                await self.db.collection(DELIVERY_COLLECTION).update_one({"agency_id": agency_id, "id": delivery_id}, {"status": "viewed"})
            await self._audit("opened", delivery, {"id": recipient["id"]}, version_id=version["id"], recipient_id=recipient["id"], actor_type="portal_recipient", summary="Authorized recipient opened the released offer.")
        questions = await self.db.collection(QUESTION_COLLECTION).find_many({"agency_id": agency_id, "delivery_id": delivery_id, "recipient_id": recipient["id"]})
        decisions = await self.db.collection(DECISION_COLLECTION).find_many({"agency_id": agency_id, "delivery_id": delivery_id, "recipient_id": recipient["id"]})
        acknowledgements = await self.db.collection(ACKNOWLEDGEMENT_COLLECTION).find_many({"agency_id": agency_id, "delivery_version_id": version["id"], "recipient_id": recipient["id"]})
        documents = await self.db.collection(DOCUMENT_LINK_COLLECTION).find_many({"agency_id": agency_id, "delivery_version_id": version["id"]})
        portal_payload = {
            "phase": PHASE_LABEL,
            "delivery": self._client_delivery(delivery),
            "version": self._client_version(version),
            "recipient": self._client_recipient(recipient),
            "client_safe_payload": version.get("client_payload") or {},
            "questions": [self._client_question(item) for item in questions],
            "decisions": [self._client_decision(item) for item in decisions],
            "warning_acknowledgements": [self._client_acknowledgement(item) for item in acknowledgements],
            "documents": [self._client_document(item) for item in documents],
        }
        if self._restricted_keys(portal_payload):
            raise JourneyOfferDeliveryError("CLIENT_PAYLOAD_INTERNAL_FIELD_DETECTED", "Client portal projection contains a restricted field.")
        return {**portal_payload, **self._portal_safety_flags()}

    async def portal_record_interaction(
        self, context: dict[str, Any], delivery_id: str, payload: Any
    ) -> dict[str, Any]:
        recipient = await self._portal_recipient(context, delivery_id)
        agency_id = context["account"]["agency_id"]
        delivery = await self._require_delivery(agency_id, delivery_id)
        version = await self._latest_client_visible_version(agency_id, delivery_id)
        if not version:
            raise JourneyOfferDeliveryError("DELIVERY_VERSION_NOT_RELEASED", "No released delivery version is available.")
        data = payload_dict(payload)
        interaction_type = str(data.get("interaction_type") or "")
        self._choice(interaction_type, INTERACTION_TYPES, "interaction type")
        interaction = await self._record_interaction(
            delivery, version, recipient, interaction_type,
            option_id=data.get("option_id"), fare_brand_id=data.get("fare_brand_id"), warning_code=data.get("warning_code"),
            interaction_metadata=data.get("interaction_metadata") or {},
        )
        return {"phase": PHASE_LABEL, "interaction": self._client_interaction(interaction), **self._portal_safety_flags()}

    async def portal_acknowledge_warning(
        self, context: dict[str, Any], delivery_id: str, payload: Any
    ) -> dict[str, Any]:
        recipient = await self._portal_recipient(context, delivery_id)
        agency_id = context["account"]["agency_id"]
        delivery = await self._require_delivery(agency_id, delivery_id)
        version = await self._latest_client_visible_version(agency_id, delivery_id)
        if not version:
            raise JourneyOfferDeliveryError("DELIVERY_VERSION_NOT_RELEASED", "No released delivery version is available.")
        data = payload_dict(payload)
        code = str(data.get("warning_code") or "")
        warning = next((item for item in version.get("client_payload", {}).get("warnings", []) if item.get("code") == code), None)
        if not warning:
            raise JourneyOfferDeliveryError("MANDATORY_WARNING_NOT_ACKNOWLEDGED", "The warning does not belong to this released version.")
        existing = await self.db.collection(ACKNOWLEDGEMENT_COLLECTION).find_one({
            "agency_id": agency_id, "delivery_version_id": version["id"], "recipient_id": recipient["id"], "warning_code": code
        })
        if existing:
            acknowledgement = existing
        else:
            acknowledgement = await self.db.collection(ACKNOWLEDGEMENT_COLLECTION).insert_one(JourneyOfferWarningAcknowledgement(
                agency_id=agency_id,
                delivery_id=delivery_id,
                delivery_version_id=version["id"],
                recipient_id=recipient["id"],
                warning_code=code,
                warning_snapshot=self._sanitize_client(warning),
                acknowledgement_text=data.get("acknowledgement_text"),
                required=bool(warning.get("required")),
                source_type=warning.get("source_type"),
                source_id=warning.get("source_id"),
            ).model_dump(mode="json"))
            await self._record_interaction(delivery, version, recipient, "warning_acknowledged", warning_code=code)
        return {"phase": PHASE_LABEL, "acknowledgement": self._client_acknowledgement(acknowledgement), **self._portal_safety_flags()}

    async def portal_submit_question(
        self, context: dict[str, Any], delivery_id: str, payload: Any
    ) -> dict[str, Any]:
        recipient = await self._portal_recipient(context, delivery_id)
        agency_id = context["account"]["agency_id"]
        delivery = await self._require_delivery(agency_id, delivery_id)
        version = await self._latest_client_visible_version(agency_id, delivery_id)
        if not version:
            raise JourneyOfferDeliveryError("DELIVERY_VERSION_NOT_RELEASED", "No released delivery version is available.")
        message = str(payload_dict(payload).get("message_text") or "").strip()
        if not message:
            raise JourneyOfferDeliveryError("DELIVERY_SOURCE_REQUIRED", "A question is required.")
        question = await self.db.collection(QUESTION_COLLECTION).insert_one(JourneyOfferClientQuestion(
            agency_id=agency_id,
            delivery_id=delivery_id,
            delivery_version_id=version["id"],
            recipient_id=recipient["id"],
            parent_question_id=payload_dict(payload).get("parent_question_id"),
            audience="agency",
            message_text=message,
            created_by_type="client",
            created_by_id=recipient["id"],
        ).model_dump(mode="json"))
        await self._record_interaction(delivery, version, recipient, "question_submitted")
        await self._timeline(delivery, "customer_contacted", "Client submitted an offer question", {"id": recipient["id"]})
        return {"phase": PHASE_LABEL, "question": self._client_question(question), "external_message_sent": False, **self._portal_safety_flags()}

    async def portal_decision_preview(
        self, context: dict[str, Any], delivery_id: str, payload: Any
    ) -> dict[str, Any]:
        recipient = await self._portal_recipient(context, delivery_id)
        agency_id = context["account"]["agency_id"]
        delivery = await self._require_delivery(agency_id, delivery_id)
        version = await self._latest_client_visible_version(agency_id, delivery_id)
        if not version:
            raise JourneyOfferDeliveryError("DELIVERY_VERSION_NOT_RELEASED", "No released delivery version is available.")
        data = payload_dict(payload)
        decision = {**data, "delivery_version_id": version["id"], "recipient_id": recipient["id"]}
        findings = await self._decision_findings(delivery, version, decision, recipient["id"])
        return {
            "phase": PHASE_LABEL,
            "preview": self._sanitize_client(decision),
            "findings": findings,
            "can_submit": not any(item["severity"] == "blocking" for item in findings),
            "canonical_acceptance_created": False,
            **self._portal_safety_flags(),
        }

    async def portal_submit_decision(
        self, context: dict[str, Any], delivery_id: str, payload: Any
    ) -> dict[str, Any]:
        preview = await self.portal_decision_preview(context, delivery_id, payload)
        if not preview["can_submit"]:
            raise JourneyOfferDeliveryError("ACCEPTANCE_HANDOFF_NOT_READY", "Decision submission is blocked by deterministic validation findings.")
        recipient = await self._portal_recipient(context, delivery_id)
        agency_id = context["account"]["agency_id"]
        delivery = await self._require_delivery(agency_id, delivery_id)
        version = await self._latest_client_visible_version(agency_id, delivery_id)
        data = payload_dict(payload)
        decision_type = str(data.get("decision_type") or "")
        self._choice(decision_type, DECISION_TYPES, "decision type")
        if decision_type in {"accept", "decline", "request_changes"}:
            submitted_decisions = await self.db.collection(DECISION_COLLECTION).find_many({
                "agency_id": agency_id,
                "delivery_version_id": version["id"],
                "recipient_id": recipient["id"],
                "status": "submitted",
            })
            existing = next(
                (item for item in submitted_decisions if item.get("decision_type") in {"accept", "decline", "request_changes"}),
                None,
            )
            if existing:
                raise JourneyOfferDeliveryError("DECISION_ALREADY_SUBMITTED", "A final decision has already been submitted for this released version.")
        decision = await self.db.collection(DECISION_COLLECTION).insert_one(JourneyOfferClientDecision(
            agency_id=agency_id,
            delivery_id=delivery_id,
            delivery_version_id=version["id"],
            recipient_id=recipient["id"],
            decision_type=decision_type,
            selected_option_id=data.get("selected_option_id"),
            selected_fare_brand_id=data.get("selected_fare_brand_id"),
            client_comment=data.get("client_comment"),
            acknowledged_warning_codes=self._tokens(data.get("acknowledged_warning_codes") or []),
            terms_acknowledged=bool(data.get("terms_acknowledged")),
            status="submitted",
            handoff_status="pending_agency_action" if decision_type == "accept" else "not_required",
        ).model_dump(mode="json"))
        status_by_decision = {"accept": "client_action_received", "decline": "declined", "request_changes": "change_requested"}
        if decision_type in status_by_decision:
            await self.db.collection(DELIVERY_COLLECTION).update_one({"agency_id": agency_id, "id": delivery_id}, {"status": status_by_decision[decision_type]})
        await self._record_interaction(delivery, version, recipient, "decision_submitted", option_id=data.get("selected_option_id"), fare_brand_id=data.get("selected_fare_brand_id"))
        await self._audit("decision_received", delivery, {"id": recipient["id"]}, version_id=version["id"], recipient_id=recipient["id"], actor_type="portal_recipient", summary=f"Client decision recorded: {decision_type}.")
        return {"phase": PHASE_LABEL, "decision": self._client_decision(decision), "canonical_acceptance_created": False, "booking_created": False, **self._portal_safety_flags()}

    async def portal_documents(self, context: dict[str, Any], delivery_id: str) -> dict[str, Any]:
        recipient = await self._portal_recipient(context, delivery_id)
        agency_id = context["account"]["agency_id"]
        version = await self._latest_client_visible_version(agency_id, delivery_id)
        if not version:
            raise JourneyOfferDeliveryError("DELIVERY_VERSION_NOT_RELEASED", "No released delivery version is available.")
        rows = await self.db.collection(DOCUMENT_LINK_COLLECTION).find_many({"agency_id": agency_id, "delivery_version_id": version["id"]})
        return {"phase": PHASE_LABEL, "recipient_id": recipient["id"], "items": [self._client_document(item) for item in rows], **self._portal_safety_flags()}

    async def portal_record_document_download(
        self, context: dict[str, Any], delivery_id: str, document_link_id: str
    ) -> dict[str, Any]:
        recipient = await self._portal_recipient(context, delivery_id)
        agency_id = context["account"]["agency_id"]
        delivery = await self._require_delivery(agency_id, delivery_id)
        link = await self.db.collection(DOCUMENT_LINK_COLLECTION).find_one({"agency_id": agency_id, "delivery_id": delivery_id, "id": document_link_id})
        if not link:
            raise JourneyOfferDeliveryError("DOCUMENT_HANDOFF_NOT_READY", "Delivery document was not found.")
        version = await self._require_version(agency_id, delivery_id, link["delivery_version_id"])
        stored = await self.db.collection(DOCUMENT_LINK_COLLECTION).update_one({"agency_id": agency_id, "id": document_link_id}, {"downloaded_at": self._now()})
        await self._record_interaction(delivery, version, recipient, "document_downloaded", interaction_metadata={"document_link_id": document_link_id})
        await self._audit("document_downloaded", delivery, {"id": recipient["id"]}, version_id=version["id"], recipient_id=recipient["id"], actor_type="portal_recipient", summary="Document download metadata recorded.")
        return {"phase": PHASE_LABEL, "document": self._client_document(stored or link), "file_transfer_performed": False, **self._portal_safety_flags()}

    async def summarize_readiness(self, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        deliveries = await self.db.collection(DELIVERY_COLLECTION).find_many(filters)
        versions = await self.db.collection(VERSION_COLLECTION).find_many(filters)
        recipients = await self.db.collection(RECIPIENT_COLLECTION).find_many(filters)
        interactions = await self.db.collection(INTERACTION_COLLECTION).find_many(filters)
        questions = await self.db.collection(QUESTION_COLLECTION).find_many(filters)
        decisions = await self.db.collection(DECISION_COLLECTION).find_many(filters)
        acknowledgements = await self.db.collection(ACKNOWLEDGEMENT_COLLECTION).find_many(filters)
        handoffs = await self.db.collection(ACCEPTANCE_HANDOFF_COLLECTION).find_many(filters)
        documents = await self.db.collection(DOCUMENT_LINK_COLLECTION).find_many(filters)
        audit_events = await self.db.collection(AUDIT_COLLECTION).find_many(filters)
        status_counts = {status: len([item for item in deliveries if item.get("status") == status]) for status in DELIVERY_STATUSES}
        decision_counts = {kind: len([item for item in decisions if item.get("decision_type") == kind]) for kind in DECISION_TYPES}
        agency_counts: dict[str, int] = {}
        for item in deliveries:
            key = item.get("agency_id") or "unknown"
            agency_counts[key] = agency_counts.get(key, 0) + 1
        blocking_validation_count = 0
        unknown_value_count = 0
        for version in versions:
            unknown_value_count += self._unknown_count(version.get("client_payload") or {})
            blocking_validation_count += len([item for item in (version.get("client_payload") or {}).get("warnings", []) if item.get("client_blocking")])
        return {
            "delivery_count": len(deliveries),
            "draft_delivery_count": len([item for item in deliveries if item.get("status") == "draft"]),
            "released_delivery_count": len([item for item in deliveries if item.get("released_at")]),
            "viewed_delivery_count": len([item for item in deliveries if item.get("status") == "viewed"]),
            "expired_delivery_count": len([item for item in deliveries if item.get("status") == "expired" or self._expired(item)]),
            "revoked_delivery_count": len([item for item in deliveries if item.get("status") == "revoked"]),
            "delivery_version_count": len(versions),
            "version_count": len(versions),
            "immutable_version_count": len([item for item in versions if item.get("immutable")]),
            "released_version_count": len([item for item in versions if item.get("status") == "released"]),
            "recipient_count": len(recipients),
            "authorized_recipient_count": len([item for item in recipients if item.get("access_status") == "authorized"]),
            "client_interaction_count": len(interactions),
            "interaction_count": len(interactions),
            "question_count": len(questions),
            "decision_count": len(decisions),
            "accepted_decision_count": decision_counts["accept"],
            "declined_decision_count": decision_counts["decline"],
            "change_requested_count": decision_counts["request_changes"],
            "warning_acknowledgement_count": len(acknowledgements),
            "acknowledgement_count": len(acknowledgements),
            "acceptance_handoff_count": len(handoffs),
            "completed_acceptance_handoff_count": len([item for item in handoffs if item.get("status") == "applied"]),
            "document_package_link_count": len(documents),
            "document_count": len(documents),
            "audit_event_count": len(audit_events),
            "blocking_validation_count": blocking_validation_count,
            "blocking_warning_count": blocking_validation_count,
            "unknown_value_count": unknown_value_count,
            "expired_count": len([item for item in deliveries if item.get("status") == "expired" or self._expired(item)]),
            "revoked_count": len([item for item in deliveries if item.get("status") == "revoked"]),
            "superseded_count": len([item for item in versions if item.get("status") == "superseded"]),
            "agency_counts": agency_counts,
            "status_counts": status_counts,
            "decision_type_counts": decision_counts,
        }

    async def dashboard(self) -> dict[str, Any]:
        deliveries = await self.list_deliveries(include_archived=True)
        return {
            "phase": PHASE_LABEL,
            "summary": await self.summarize_readiness(),
            "items": [self._platform_delivery(item) for item in deliveries[:30]],
            "filters": self.filters(),
            "read_only": True,
            "platform_diagnostics_read_only": True,
            "diagnostic": "Phase 56.4 enables controlled authenticated delivery, immutable client versions, recipient-bound interactions, explicit decisions, and guarded handoffs. It does not retrieve live fares, connect to providers, publish anonymously, process payment, create bookings, issue tickets, or send uncontrolled external messages.",
            **self.safety_flags(),
        }

    async def platform_detail(self, delivery_id: str) -> dict[str, Any]:
        delivery = await self.db.collection(DELIVERY_COLLECTION).find_one({"id": delivery_id})
        if not delivery:
            raise JourneyOfferDeliveryError("DELIVERY_SOURCE_REQUIRED", "Offer delivery was not found.")
        agency_id = delivery["agency_id"]
        detail = await self.get_delivery(agency_id, delivery_id)
        return {
            "phase": PHASE_LABEL,
            "delivery": self._platform_delivery(delivery),
            "version_count": len(detail["versions"]),
            "recipient_count": len(detail["recipients"]),
            "interaction_count": len(detail["interactions"]),
            "decision_count": len(detail["decisions"]),
            "question_count": len(detail["questions"]),
            "document_count": len(detail["documents"]),
            "handoff_count": len(detail["acceptance_handoffs"]),
            "source_integrity": [
                {"version_id": item["id"], "source_hash_present": bool(item.get("source_snapshot_hash")), "payload_hash_present": bool(item.get("payload_hash")), "immutable": bool(item.get("immutable"))}
                for item in detail["versions"]
            ],
            "read_only": True,
            **self.safety_flags(),
        }

    async def _create_version(
        self, delivery: dict[str, Any], snapshot: dict[str, Any], data: dict[str, Any], user: dict[str, Any]
    ) -> dict[str, Any]:
        versions = await self.list_versions(delivery["agency_id"], delivery["id"])
        client_payload = self._build_client_payload(delivery, snapshot)
        if self._restricted_keys(client_payload):
            raise JourneyOfferDeliveryError("CLIENT_PAYLOAD_INTERNAL_FIELD_DETECTED", "Client payload sanitization did not remove all restricted fields.")
        values = {
            "agency_id": delivery["agency_id"],
            "delivery_id": delivery["id"],
            "version_number": max([int(item.get("version_number") or 0) for item in versions], default=0) + 1,
            "source_presentation_snapshot_id": snapshot["id"],
            "source_snapshot_hash": snapshot["source_hash"],
            "payload_hash": self._hash(client_payload),
            "client_payload": client_payload,
            "release_notes": data.get("release_notes"),
            "expires_at": self._dt(data.get("expires_at")) or delivery.get("expires_at"),
            "status": "draft",
            "immutable": False,
        }
        return await self.db.collection(VERSION_COLLECTION).insert_one(
            JourneyOfferDeliveryVersion(**values).model_dump(mode="json")
        )

    def _build_client_payload(self, delivery: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
        source = self._sanitize_client(snapshot.get("client_safe_payload") or {})
        options = source.get("options") or []
        fares = source.get("fare_brands") or []
        segments = source.get("segments") or []
        connections = source.get("connections") or []
        services = source.get("service_suitability") or []
        warnings: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item, source_type in [
            *[(item, "option") for item in options],
            *[(item, "connection") for item in connections],
            *[(item, "fare_brand") for item in fares],
            *[(item, "service_suitability") for item in services],
        ]:
            codes = list(item.get("warning_codes") or [])
            if item.get("blocking_indicator") or int(item.get("blocking_warning_count") or 0) > 0:
                codes.append("client_blocking_review")
            for code in codes:
                key = f"{source_type}:{item.get('id')}:{code}"
                if key in seen:
                    continue
                seen.add(key)
                blocking = code == "client_blocking_review"
                warnings.append({
                    "code": code,
                    "message": self._plain_warning(code),
                    "severity": "blocking" if blocking else "important",
                    "required": True,
                    "client_blocking": blocking,
                    "source_type": source_type,
                    "source_id": item.get("id"),
                })
        return self._sanitize_client({
            "delivery": {
                "id": delivery["id"],
                "delivery_code": delivery["delivery_code"],
                "title": delivery["title"],
                "client_intro": delivery.get("client_intro"),
                "client_footer": delivery.get("client_footer"),
                "language_code": delivery.get("language_code"),
                "currency_code": delivery.get("currency_code"),
                "audience_type": delivery.get("audience_type"),
                "expires_at": delivery.get("expires_at"),
            },
            "presentation": source.get("presentation") or {},
            "configuration": source.get("configuration") or {},
            "options": options,
            "segments": segments,
            "connections": connections,
            "fare_brands": fares,
            "service_suitability": services,
            "comparison": source.get("comparison"),
            "content_blocks": source.get("content_blocks") or [],
            "warnings": warnings,
            "terms": {
                "acceptance_is_a_request_for_agency_processing": True,
                "booking_is_not_created_automatically": True,
                "airline_approvals_remain_conditional_unless_explicitly_confirmed": True,
                "local_times": True,
            },
        })

    async def _decision_findings(
        self, delivery: dict[str, Any], version: dict[str, Any], decision: dict[str, Any], recipient_id: str
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        try:
            await self._require_actionable_version(delivery["agency_id"], delivery, version["id"])
        except JourneyOfferDeliveryError as exc:
            findings.append(self._finding(exc.code, "blocking", str(exc)))
        decision_type = str(decision.get("decision_type") or "")
        if decision_type not in DECISION_TYPES:
            findings.append(self._finding("DELIVERY_SOURCE_REQUIRED", "blocking", "A supported decision type is required."))
            return findings
        if decision_type != "accept":
            return findings
        options = version.get("client_payload", {}).get("options") or []
        fares = version.get("client_payload", {}).get("fare_brands") or []
        selected_option_id = decision.get("selected_option_id")
        selected_fare_id = decision.get("selected_fare_brand_id")
        selected_option = next((item for item in options if item.get("id") == selected_option_id), None)
        if not selected_option_id:
            findings.append(self._finding("OPTION_SELECTION_REQUIRED", "blocking", "Select an itinerary option before accepting."))
        elif not selected_option:
            findings.append(self._finding("OPTION_NOT_IN_RELEASED_VERSION", "blocking", "The selected itinerary does not belong to this released version."))
        option_fares = [item for item in fares if item.get("option_projection_id") == selected_option_id]
        if option_fares and not selected_fare_id:
            findings.append(self._finding("FARE_BRAND_SELECTION_REQUIRED", "blocking", "Select a fare brand before accepting."))
        elif selected_fare_id and not any(item.get("id") == selected_fare_id for item in option_fares):
            findings.append(self._finding("FARE_BRAND_NOT_IN_SELECTED_OPTION", "blocking", "The selected fare brand does not belong to the selected itinerary."))
        required = {item.get("code") for item in version.get("client_payload", {}).get("warnings", []) if item.get("required")}
        stored = await self.db.collection(ACKNOWLEDGEMENT_COLLECTION).find_many({
            "agency_id": delivery["agency_id"], "delivery_version_id": version["id"], "recipient_id": recipient_id
        })
        acknowledged = {item.get("warning_code") for item in stored} | set(decision.get("acknowledged_warning_codes") or [])
        missing = sorted(required - acknowledged)
        if missing:
            findings.append(self._finding("MANDATORY_WARNING_NOT_ACKNOWLEDGED", "blocking", f"Acknowledge required warnings: {', '.join(missing)}."))
        if any(item.get("client_blocking") for item in version.get("client_payload", {}).get("warnings", [])):
            findings.append(self._finding("CLIENT_BLOCKING_WARNING_PRESENT", "blocking", "The agency must resolve a blocking warning before acceptance."))
        if not decision.get("terms_acknowledged"):
            findings.append(self._finding("MANDATORY_WARNING_NOT_ACKNOWLEDGED", "blocking", "Confirm the offer terms before accepting."))
        return findings

    async def _record_interaction(
        self,
        delivery: dict[str, Any],
        version: dict[str, Any],
        recipient: dict[str, Any],
        interaction_type: str,
        *,
        option_id: str | None = None,
        fare_brand_id: str | None = None,
        warning_code: str | None = None,
        interaction_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self.db.collection(INTERACTION_COLLECTION).insert_one(JourneyOfferClientInteraction(
            agency_id=delivery["agency_id"],
            delivery_id=delivery["id"],
            delivery_version_id=version["id"],
            recipient_id=recipient["id"],
            interaction_type=interaction_type,
            option_id=option_id,
            fare_brand_id=fare_brand_id,
            warning_code=warning_code,
            interaction_metadata=self._sanitize_client(interaction_metadata or {}),
        ).model_dump(mode="json"))

    async def _portal_recipient(
        self, context: dict[str, Any], delivery_id: str, *, required: bool = True
    ) -> dict[str, Any] | None:
        agency_id = context["account"]["agency_id"]
        client_id = context["account"]["client_id"]
        delivery = await self.db.collection(DELIVERY_COLLECTION).find_one({"agency_id": agency_id, "id": delivery_id, "client_id": client_id})
        if not delivery:
            if required:
                raise JourneyOfferDeliveryError("RECIPIENT_NOT_AUTHORIZED", "Offer delivery was not found for this portal client.")
            return None
        recipients = await self.db.collection(RECIPIENT_COLLECTION).find_many({"agency_id": agency_id, "delivery_id": delivery_id, "client_id": client_id})
        account_id = context["account"]["id"]
        recipient = next((item for item in recipients if item.get("portal_user_id") == account_id and item.get("access_status") == "authorized"), None)
        if not recipient:
            recipient = next((item for item in recipients if not item.get("portal_user_id") and item.get("access_status") == "authorized"), None)
        if not recipient and required:
            raise JourneyOfferDeliveryError("RECIPIENT_NOT_AUTHORIZED", "This portal identity is not an authorized recipient.")
        return recipient

    async def _select_presentation_snapshot(
        self, agency_id: str, presentation_id: str, snapshot_id: str | None
    ) -> dict[str, Any]:
        query = {"agency_id": agency_id, "presentation_id": presentation_id}
        rows = await self.db.collection("journey_presentation_snapshots").find_many(query)
        if snapshot_id:
            snapshot = next((item for item in rows if item.get("id") == snapshot_id), None)
        else:
            finalized = [item for item in rows if item.get("finalized")]
            snapshot = sorted(finalized, key=lambda item: int(item.get("version_number") or 0), reverse=True)[0] if finalized else None
        if not snapshot:
            raise JourneyOfferDeliveryError("PRESENTATION_SNAPSHOT_REQUIRED", "A finalized Phase 56.3 presentation snapshot is required.")
        if not snapshot.get("finalized"):
            raise JourneyOfferDeliveryError("PRESENTATION_SNAPSHOT_NOT_FINALIZED", "The selected presentation snapshot is not finalized.")
        if not snapshot.get("source_hash"):
            raise JourneyOfferDeliveryError("PRESENTATION_SNAPSHOT_HASH_MISMATCH", "The selected presentation snapshot has no source hash.")
        return snapshot

    async def _validate_passengers(self, agency_id: str, client_id: str, passenger_ids: list[str]) -> None:
        for passenger_id in passenger_ids:
            passenger = await self.db.collection("passenger_profiles").find_one({"agency_id": agency_id, "id": passenger_id})
            relationship = await self.db.collection("client_passenger_relationships").find_one({
                "agency_id": agency_id, "client_id": client_id, "passenger_id": passenger_id, "status": "active"
            })
            if not passenger or not relationship:
                raise JourneyOfferDeliveryError("RECIPIENT_NOT_AUTHORIZED", "Passenger must belong to the delivery client and agency.")

    async def _require_delivery(self, agency_id: str, delivery_id: str) -> dict[str, Any]:
        delivery = await self.db.collection(DELIVERY_COLLECTION).find_one({"agency_id": agency_id, "id": delivery_id})
        if not delivery:
            raise JourneyOfferDeliveryError("AGENCY_ISOLATION_VIOLATION", "Offer delivery was not found for this agency.")
        return delivery

    async def _require_version(self, agency_id: str, delivery_id: str, version_id: str) -> dict[str, Any]:
        version = await self.db.collection(VERSION_COLLECTION).find_one({"agency_id": agency_id, "delivery_id": delivery_id, "id": version_id})
        if not version:
            raise JourneyOfferDeliveryError("AGENCY_ISOLATION_VIOLATION", "Offer delivery version was not found for this agency.")
        return version

    async def _require_recipient(self, agency_id: str, delivery_id: str, recipient_id: str) -> dict[str, Any]:
        recipient = await self.db.collection(RECIPIENT_COLLECTION).find_one({"agency_id": agency_id, "delivery_id": delivery_id, "id": recipient_id})
        if not recipient:
            raise JourneyOfferDeliveryError("RECIPIENT_NOT_AUTHORIZED", "Delivery recipient was not found for this agency.")
        return recipient

    async def _require_actionable_version(
        self, agency_id: str, delivery: dict[str, Any], version_id: str, *, historical_ok: bool = False
    ) -> dict[str, Any]:
        version = await self._require_version(agency_id, delivery["id"], version_id)
        if delivery.get("status") == "revoked" or delivery.get("revoked_at") or version.get("status") == "revoked":
            raise JourneyOfferDeliveryError("DELIVERY_REVOKED", "This offer delivery has been revoked.")
        if self._expired(version) or self._expired(delivery):
            if not historical_ok:
                raise JourneyOfferDeliveryError("DELIVERY_EXPIRED", "This offer delivery has expired.")
        if version.get("status") == "superseded" and not historical_ok:
            raise JourneyOfferDeliveryError("DELIVERY_VERSION_SUPERSEDED", "A newer offer delivery version is available.")
        if version.get("status") not in {"released", "expired", "revoked", "superseded"} or not version.get("immutable"):
            raise JourneyOfferDeliveryError("DELIVERY_VERSION_NOT_RELEASED", "The offer delivery version has not been released.")
        return version

    async def _latest_version(self, agency_id: str, delivery_id: str) -> dict[str, Any] | None:
        versions = await self.list_versions(agency_id, delivery_id)
        return versions[0] if versions else None

    async def _latest_released_version(self, agency_id: str, delivery_id: str) -> dict[str, Any] | None:
        versions = await self.list_versions(agency_id, delivery_id)
        return next((item for item in versions if item.get("status") == "released" and item.get("immutable")), None)

    async def _latest_client_visible_version(self, agency_id: str, delivery_id: str) -> dict[str, Any] | None:
        versions = await self.list_versions(agency_id, delivery_id)
        return next((item for item in versions if item.get("immutable") and item.get("status") in {"released", "expired", "superseded"}), None)

    async def _select_accept_decision(self, agency_id: str, delivery_id: str, decision_id: str | None) -> dict[str, Any]:
        query = {"agency_id": agency_id, "delivery_id": delivery_id, "decision_type": "accept", "status": "submitted"}
        rows = await self.db.collection(DECISION_COLLECTION).find_many(query)
        if decision_id:
            decision = next((item for item in rows if item.get("id") == decision_id), None)
        else:
            decision = sorted(rows, key=lambda item: str(item.get("submitted_at") or ""), reverse=True)[0] if rows else None
        if not decision:
            raise JourneyOfferDeliveryError("ACCEPTANCE_HANDOFF_NOT_READY", "An explicit accept decision is required for handoff.")
        return decision

    async def _resolve_offer_option(
        self, agency_id: str, delivery: dict[str, Any], version: dict[str, Any], decision: dict[str, Any]
    ) -> str | None:
        selected = next((item for item in version.get("client_payload", {}).get("options", []) if item.get("id") == decision.get("selected_option_id")), None)
        if not selected:
            return None
        composition_option_id = selected.get("composition_option_id")
        source = await self.db.collection("journey_option_alternatives").find_one({"agency_id": agency_id, "id": composition_option_id}) if composition_option_id else None
        source_metadata = (source or {}).get("metadata") or {}
        candidates = self._tokens([
            source_metadata.get("offer_option_id"),
            source_metadata.get("canonical_offer_option_id"),
            selected.get("offer_option_id"),
        ])
        offer_options = await self.db.collection("offer_options").find_many({"agency_id": agency_id, "workspace_id": delivery.get("offer_id")})
        for option in offer_options:
            metadata = option.get("metadata") or {}
            if option.get("id") in candidates or option.get("composition_option_id") == composition_option_id or metadata.get("composition_option_id") == composition_option_id:
                return option["id"]
        return offer_options[0]["id"] if len(offer_options) == 1 and len(version.get("client_payload", {}).get("options") or []) == 1 else None

    async def _audit(
        self,
        event_type: str,
        delivery: dict[str, Any],
        user: dict[str, Any] | None,
        *,
        version_id: str | None = None,
        recipient_id: str | None = None,
        actor_type: str = "agency_user",
        summary: str,
    ) -> None:
        actor_id = self._actor(user)
        event = JourneyOfferDeliveryAuditEvent(
            agency_id=delivery["agency_id"],
            delivery_id=delivery["id"],
            delivery_version_id=version_id,
            recipient_id=recipient_id,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            summary=summary,
        )
        await self.db.collection(AUDIT_COLLECTION).insert_one(event.model_dump(mode="json"))
        await self.db.collection("audit_events").insert_one(AuditEvent(
            agency_id=delivery["agency_id"],
            actor_user_id=actor_id if actor_type == "agency_user" else None,
            event_type=f"offer_delivery.{event_type}",
            entity_type="offer_delivery",
            entity_id=delivery["id"],
            summary=summary,
            metadata={"delivery_version_id": version_id, "recipient_id": recipient_id, "actor_type": actor_type},
        ).model_dump(mode="json"))

    async def _timeline(
        self, delivery: dict[str, Any], event_type: str, summary: str, user: dict[str, Any] | None
    ) -> None:
        await self.db.collection("operational_timelines").insert_one(OperationalTimeline(
            agency_id=delivery["agency_id"],
            timeline_reference=f"JOD-{new_id()[:10].upper()}",
            created_by=self._actor(user),
            trip_workspace_id=delivery.get("trip_id"),
            event_type=event_type,
            event_category="offer_delivery",
            event_source="phase_56_4",
            event_status="recorded",
            summary=summary,
            internal_only=True,
            passenger_visible=False,
            metadata={"offer_delivery_id": delivery["id"]},
        ).model_dump(mode="json"))

    def _sanitize_client(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: self._sanitize_client(item)
                for key, item in value.items()
                if key not in CLIENT_RESTRICTED_FIELDS and not key.startswith("internal_")
            }
        if isinstance(value, list):
            return [self._sanitize_client(item) for item in value]
        return value

    def _restricted_keys(self, value: Any) -> set[str]:
        found: set[str] = set()
        if isinstance(value, dict):
            for key, item in value.items():
                if key in CLIENT_RESTRICTED_FIELDS or key.startswith("internal_"):
                    found.add(key)
                found.update(self._restricted_keys(item))
        elif isinstance(value, list):
            for item in value:
                found.update(self._restricted_keys(item))
        return found

    def _client_delivery(self, item: dict[str, Any]) -> dict[str, Any]:
        return self._sanitize_client({
            key: item.get(key) for key in [
                "id", "delivery_code", "status", "audience_type", "language_code", "currency_code", "title",
                "client_intro", "client_footer", "expires_at", "released_at", "revoked_at", "superseded_at",
            ]
        })

    def _client_version(self, item: dict[str, Any]) -> dict[str, Any]:
        return {key: item.get(key) for key in ["id", "version_number", "status", "released_at", "expires_at", "superseded_by_version_id"]}

    def _client_recipient(self, item: dict[str, Any]) -> dict[str, Any]:
        return {key: item.get(key) for key in ["id", "recipient_role", "display_name", "access_status", "locale", "timezone", "first_opened_at", "last_opened_at"]}

    def _client_question(self, item: dict[str, Any]) -> dict[str, Any]:
        return {key: item.get(key) for key in ["id", "parent_question_id", "audience", "message_text", "status", "created_by_type", "created_at", "answered_at"]}

    def _client_decision(self, item: dict[str, Any]) -> dict[str, Any]:
        return {key: item.get(key) for key in ["id", "decision_type", "selected_option_id", "selected_fare_brand_id", "client_comment", "acknowledged_warning_codes", "terms_acknowledged", "submitted_at", "status", "handoff_status"]}

    def _client_acknowledgement(self, item: dict[str, Any]) -> dict[str, Any]:
        return {key: item.get(key) for key in ["id", "warning_code", "warning_snapshot", "acknowledged_at", "acknowledgement_text", "required"]}

    def _client_document(self, item: dict[str, Any]) -> dict[str, Any]:
        return {key: item.get(key) for key in ["id", "document_type", "language_code", "status", "generated_at", "available_at", "downloaded_at", "checksum"]}

    def _client_interaction(self, item: dict[str, Any]) -> dict[str, Any]:
        return {key: item.get(key) for key in ["id", "interaction_type", "option_id", "fare_brand_id", "warning_code", "occurred_at"]}

    def _platform_delivery(self, item: dict[str, Any]) -> dict[str, Any]:
        return {key: item.get(key) for key in [
            "id", "agency_id", "delivery_code", "presentation_id", "presentation_snapshot_id", "journey_id",
            "composition_id", "offer_id", "status", "audience_type", "language_code", "currency_code",
            "expires_at", "released_at", "revoked_at", "superseded_at", "created_at", "updated_at",
        ]}

    def _portal_safety_flags(self) -> dict[str, bool]:
        flags = self.safety_flags()
        return {key: value for key, value in flags.items() if key != "agency_isolation_enabled"} | {
            "tenant_isolation_enabled": True,
            "internal_content_removed": True,
        }

    def _unknown_count(self, value: Any) -> int:
        if isinstance(value, dict):
            return sum(self._unknown_count(item) for item in value.values())
        if isinstance(value, list):
            return sum(self._unknown_count(item) for item in value)
        return 1 if isinstance(value, str) and value.lower() in {"unknown", "not_assessed", "manual_review_required"} else 0

    def _plain_warning(self, code: str) -> str:
        labels = {
            "client_blocking_review": "This option still has a blocking item that your agency must resolve.",
            "airline_confirmation_required": "This service still requires airline confirmation.",
            "interline_review_required": "Carrier responsibility for this itinerary still needs manual review.",
            "codeshare_review_required": "The marketing and operating carriers differ; conditions may vary.",
            "baggage_unknown": "Baggage inclusion is not yet confirmed.",
        }
        return labels.get(code, str(code).replace("_", " ").capitalize())

    def _finding(self, code: str, severity: str, message: str) -> dict[str, Any]:
        return {"code": code, "severity": severity, "message": message}

    def _expired(self, item: dict[str, Any]) -> bool:
        expires = self._dt(item.get("expires_at"))
        return bool(expires and expires <= self._now())

    def _dt(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, date):
            return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
        if isinstance(value, str) and value:
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                return None
        return None

    def _normalize(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._normalize(value[key]) for key in sorted(value)}
        if isinstance(value, list):
            return [self._normalize(item) for item in value]
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value

    def _hash(self, value: Any) -> str:
        return sha256(json.dumps(self._normalize(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()

    def _tokens(self, values: Any) -> list[str]:
        if values is None:
            return []
        if not isinstance(values, list):
            values = [values]
        result: list[str] = []
        for value in values:
            if value is not None and str(value) and str(value) not in result:
                result.append(str(value))
        return result

    def _choice(self, value: str, allowed: list[str], label: str) -> str:
        if value not in allowed:
            raise JourneyOfferDeliveryError("DELIVERY_SOURCE_REQUIRED", f"Unsupported {label}: {value}.")
        return value

    def _actor(self, user: dict[str, Any] | None) -> str | None:
        return (user or {}).get("id") or (user or {}).get("email")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)
