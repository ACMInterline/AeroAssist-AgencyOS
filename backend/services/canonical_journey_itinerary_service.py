from __future__ import annotations

from datetime import date, datetime, time, timezone
from hashlib import sha256
import json
from typing import Any, Iterable

from pydantic import BaseModel

from database import Database
from models import (
    AuditEvent,
    JourneyConnectionRepresentation,
    JourneyFareBrandPresentation,
    JourneyItineraryOption,
    JourneyLegRepresentation,
    JourneyPresentationConfiguration,
    JourneyRepresentation,
    JourneySegmentRepresentation,
    JourneyServicePresentation,
    JourneySnapshot,
    new_id,
)


PHASE_LABEL = "phase_56_2_journey_option_fare_brand_composition_workspace_foundation"

JOURNEY_COLLECTION = "journey_representations"
OPTION_COLLECTION = "journey_itinerary_options"
LEG_COLLECTION = "journey_leg_representations"
SEGMENT_COLLECTION = "journey_segment_representations"
CONNECTION_COLLECTION = "journey_connection_representations"
FARE_BRAND_COLLECTION = "journey_fare_brand_presentations"
SERVICE_COLLECTION = "journey_service_presentations"
PRESENTATION_COLLECTION = "journey_presentation_configurations"
SNAPSHOT_COLLECTION = "journey_snapshots"

JOURNEY_COLLECTIONS = [
    JOURNEY_COLLECTION,
    OPTION_COLLECTION,
    LEG_COLLECTION,
    SEGMENT_COLLECTION,
    CONNECTION_COLLECTION,
    FARE_BRAND_COLLECTION,
    SERVICE_COLLECTION,
    PRESENTATION_COLLECTION,
    SNAPSHOT_COLLECTION,
]

JOURNEY_STATUSES = ["draft", "active", "complete", "archived"]
PRESENTATION_STATUSES = ["draft", "internal_ready", "client_ready", "finalized", "archived"]
SNAPSHOT_TYPES = [
    "offer_draft",
    "offer_published",
    "offer_accepted",
    "booking_confirmation",
    "ticket_issued",
    "journey_updated",
    "after_sales_revision",
    "client_document",
]
SOURCE_PROVENANCE_TYPES = [
    "manual_entry",
    "gds_cryptic_parser",
    "itinerary_text_parser",
    "booking_import",
    "existing_trip",
    "existing_offer",
    "existing_booking",
    "ticket_record",
    "airline_confirmation",
    "structured_import",
    "external_provider_adapter",
]
SOURCE_DATA_STATES = ["imported", "normalized", "agent_reviewed", "confirmed", "issued", "historical"]


class CanonicalJourneyError(ValueError):
    pass


class FinalizedJourneySnapshotError(CanonicalJourneyError):
    pass


class CanonicalJourneyItineraryService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "canonical_journey_itinerary_representation_enabled": True,
            "canonical_operational_entities_reused": True,
            "duplicate_operational_entities_disabled": True,
            "duplicate_segment_source_of_truth_disabled": True,
            "immutable_journey_snapshots_enabled": True,
            "finalized_snapshot_mutation_disabled": True,
            "source_provenance_enabled": True,
            "agency_isolation_enabled": True,
            "client_safe_projection_enabled": True,
            "live_availability_disabled": True,
            "live_pricing_disabled": True,
            "provider_connectivity_disabled": True,
            "provider_execution_disabled": True,
            "scraping_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_publication_disabled": True,
            "automatic_production_seeding_disabled": True,
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "statuses": JOURNEY_STATUSES,
            "presentation_statuses": PRESENTATION_STATUSES,
            "snapshot_types": SNAPSHOT_TYPES,
            "source_provenance_types": SOURCE_PROVENANCE_TYPES,
            "source_data_states": SOURCE_DATA_STATES,
            "journey_types": ["one_way", "return", "open_jaw", "multi_city", "unknown"],
        }

    async def list_journeys(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        presentation_status: str | None = None,
        source_entity_type: str | None = None,
        source_entity_id: str | None = None,
        client_id: str | None = None,
        passenger_id: str | None = None,
        include_archived: bool = False,
        client_safe: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        for key, value in {
            "agency_id": agency_id,
            "status": status,
            "presentation_status": presentation_status,
            "source_entity_type": source_entity_type,
            "source_entity_id": source_entity_id,
            "client_id": client_id,
        }.items():
            if value not in {None, ""}:
                filters[key] = value
        items = await self.db.collection(JOURNEY_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if item.get("status") != "archived" and not item.get("archived_at")]
        if passenger_id:
            items = [item for item in items if passenger_id in (item.get("passenger_ids") or [])]
        items.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
        return [self._client_safe(item) if client_safe else item for item in items]

    async def dashboard(self, agency_id: str | None = None) -> dict[str, Any]:
        items = await self.list_journeys(agency_id=agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "summary": await self.summary(agency_id=agency_id),
            "filters": self.filter_metadata(),
            "notice": "Journey records are presentation projections over canonical operational records. They do not replace source entities, search availability, calculate live prices, call providers, publish automatically, or execute travel operations.",
            **self.safety_flags(),
        }

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        journeys = await self.list_journeys(agency_id=agency_id, include_archived=True)
        child_filters = {"agency_id": agency_id} if agency_id else None
        options = await self.db.collection(OPTION_COLLECTION).find_many(child_filters)
        legs = await self.db.collection(LEG_COLLECTION).find_many(child_filters)
        segments = await self.db.collection(SEGMENT_COLLECTION).find_many(child_filters)
        connections = await self.db.collection(CONNECTION_COLLECTION).find_many(child_filters)
        fare_brands = await self.db.collection(FARE_BRAND_COLLECTION).find_many(child_filters)
        services = await self.db.collection(SERVICE_COLLECTION).find_many(child_filters)
        snapshots = await self.db.collection(SNAPSHOT_COLLECTION).find_many(child_filters)
        return {
            "journey_count": len(journeys),
            "active_journey_count": sum(item.get("status") != "archived" for item in journeys),
            "incomplete_journey_count": sum(item.get("data_completeness_status") in {"incomplete", "partial", "unknown"} for item in journeys),
            "manual_review_journey_count": sum(bool(item.get("manual_review_required")) for item in journeys),
            "itinerary_option_count": len(options),
            "journey_leg_count": len(legs),
            "journey_segment_count": len(segments),
            "connection_count": len(connections),
            "fare_brand_presentation_count": len(fare_brands),
            "service_presentation_count": len(services),
            "snapshot_count": len(snapshots),
            "finalized_snapshot_count": sum(bool(item.get("immutable") and item.get("finalized_at")) for item in snapshots),
            "status_counts": self._counts(journeys, "status"),
            "presentation_status_counts": self._counts(journeys, "presentation_status"),
            "source_type_counts": self._counts(journeys, "source_entity_type"),
        }

    async def coverage(self) -> dict[str, Any]:
        summary = await self.summary()
        return {
            **summary,
            "journey_representation_collection_enabled": True,
            "itinerary_option_representation_enabled": True,
            "journey_leg_representation_enabled": True,
            "journey_segment_projection_enabled": True,
            "journey_connection_representation_enabled": True,
            "journey_fare_brand_presentation_enabled": True,
            "journey_service_presentation_enabled": True,
            "journey_presentation_configuration_enabled": True,
            "trip_projection_enabled": True,
            "offer_projection_enabled": True,
            "booking_projection_enabled": True,
            "ticket_reference_enabled": True,
        }

    async def create_journey(self, payload: BaseModel | dict[str, Any], user: dict[str, Any], *, agency_id: str | None = None) -> dict[str, Any]:
        data = self._payload(payload)
        requested_agency = str(data.get("agency_id") or agency_id or "").strip()
        if not requested_agency or (agency_id and requested_agency != agency_id):
            raise CanonicalJourneyError("A valid, matching agency_id is required.")
        record_id = data.get("id") or new_id()
        source_type = self._token(data.get("source_entity_type") or "manual_entry")
        source_id = str(data.get("source_entity_id") or f"manual:{record_id}")
        values = {
            **data,
            "id": record_id,
            "agency_id": requested_agency,
            "journey_reference": data.get("journey_reference") or self._reference("JNY"),
            "title": str(data.get("title") or "Untitled journey").strip(),
            "source_entity_type": source_type,
            "source_entity_id": source_id,
            "created_by": self._actor(user),
            "updated_by": self._actor(user),
        }
        values.update(self._journey_completeness(values))
        model = JourneyRepresentation(**values)
        stored = await self.db.collection(JOURNEY_COLLECTION).insert_one(model.model_dump(mode="json"))
        await self._audit("journey.representation_created", stored, user)
        return self._response("journey", stored)

    async def update_journey(self, agency_id: str, journey_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require_journey(journey_id, agency_id)
        if existing.get("status") == "archived":
            raise CanonicalJourneyError("Archived journey representations cannot be edited.")
        updates = {key: value for key, value in self._payload(payload).items() if key not in {"id", "agency_id", "created_at", "created_by"}}
        values = {**existing, **updates, "updated_by": self._actor(user)}
        values.update(self._journey_completeness(values))
        validated = JourneyRepresentation(**values).model_dump(mode="json")
        updated = await self.db.collection(JOURNEY_COLLECTION).update_one({"id": journey_id, "agency_id": agency_id}, validated)
        if not updated:
            raise CanonicalJourneyError("Journey representation could not be updated.")
        await self._audit("journey.representation_updated", updated, user)
        return self._response("journey", updated)

    async def archive_journey(self, agency_id: str, journey_id: str, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require_journey(journey_id, agency_id)
        if existing.get("status") == "archived":
            return self._response("journey", existing)
        updated = await self.db.collection(JOURNEY_COLLECTION).update_one(
            {"id": journey_id, "agency_id": agency_id},
            {"status": "archived", "presentation_status": "archived", "archived_at": self._now(), "updated_by": self._actor(user)},
        )
        if not updated:
            raise CanonicalJourneyError("Journey representation could not be archived.")
        await self._audit("journey.representation_archived", updated, user, {"physical_deletion": False})
        return {**self._response("journey", updated), "physical_deletion": False}

    async def create_option(self, agency_id: str, journey_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        journey = await self._require_journey(journey_id, agency_id)
        data = self._payload(payload)
        existing = await self.db.collection(OPTION_COLLECTION).find_many({"agency_id": agency_id, "journey_id": journey_id})
        option_number = int(data.get("option_number") or len(existing) + 1)
        values = {
            **data,
            "agency_id": agency_id,
            "journey_id": journey_id,
            "option_number": option_number,
            "option_code": data.get("option_code") or f"OPT-{option_number:02d}",
            "title": data.get("title") or f"Itinerary option {option_number}",
            "source_entity_type": data.get("source_entity_type") or journey["source_entity_type"],
            "source_entity_id": data.get("source_entity_id") or journey["source_entity_id"],
            "source_provenance": self._provenance(data.get("source_provenance"), journey["source_entity_type"]),
        }
        stored = await self.db.collection(OPTION_COLLECTION).insert_one(JourneyItineraryOption(**values).model_dump(mode="json"))
        await self._audit("journey.option_created", stored, user)
        return self._response("itinerary_option", stored)

    async def create_leg(self, agency_id: str, journey_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = self._payload(payload)
        option = await self._require_option(journey_id, str(data.get("itinerary_option_id") or ""), agency_id)
        existing = await self.db.collection(LEG_COLLECTION).find_many({"agency_id": agency_id, "journey_id": journey_id, "itinerary_option_id": option["id"]})
        values = {**data, "agency_id": agency_id, "journey_id": journey_id, "itinerary_option_id": option["id"], "leg_number": int(data.get("leg_number") or len(existing) + 1)}
        stored = await self.db.collection(LEG_COLLECTION).insert_one(JourneyLegRepresentation(**values).model_dump(mode="json"))
        await self._audit("journey.leg_created", stored, user)
        return self._response("leg", stored)

    async def create_segment(self, agency_id: str, journey_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = self._payload(payload)
        option = await self._require_option(journey_id, str(data.get("itinerary_option_id") or ""), agency_id)
        leg_id = data.get("leg_id")
        if leg_id:
            await self._require_leg(journey_id, str(leg_id), agency_id)
        existing = await self.db.collection(SEGMENT_COLLECTION).find_many({"agency_id": agency_id, "journey_id": journey_id, "itinerary_option_id": option["id"]})
        source_type = self._token(data.get("source_entity_type") or "manual_entry")
        values = {
            **data,
            "agency_id": agency_id,
            "journey_id": journey_id,
            "itinerary_option_id": option["id"],
            "segment_number": int(data.get("segment_number") or len(existing) + 1),
            "source_entity_type": source_type,
            "source_entity_id": str(data.get("source_entity_id") or option["source_entity_id"]),
            "source_provenance": self._provenance(data.get("source_provenance"), source_type),
        }
        values["codeshare_indicator"] = bool(
            values.get("marketing_carrier_code")
            and values.get("operating_carrier_code")
            and values.get("marketing_carrier_code") != values.get("operating_carrier_code")
        )
        departure = self._datetime(values.get("departure_utc"))
        arrival = self._datetime(values.get("arrival_utc"))
        warnings = self._tokens(values.get("warning_codes"))
        if departure and arrival:
            duration = self._minutes(departure, arrival)
            if duration >= 0:
                values["scheduled_duration_minutes"] = values.get("scheduled_duration_minutes") if values.get("scheduled_duration_minutes") is not None else duration
            else:
                warnings.append("invalid_segment_chronology")
        completeness = self._segment_completeness(values)
        warnings.extend(completeness["warning_codes"])
        values.update(completeness)
        values["warning_codes"] = self._tokens(warnings)
        values["manual_review_required"] = bool(values.get("manual_review_required") or values["warning_codes"])
        stored = await self.db.collection(SEGMENT_COLLECTION).insert_one(JourneySegmentRepresentation(**values).model_dump(mode="json"))
        if leg_id:
            leg = await self._require_leg(journey_id, str(leg_id), agency_id)
            segment_ids = self._tokens([*(leg.get("segment_ids") or []), stored["id"]])
            await self.db.collection(LEG_COLLECTION).update_one({"id": leg["id"], "agency_id": agency_id}, {"segment_ids": segment_ids})
            await self._recalculate_leg(agency_id, journey_id, leg["id"])
        await self._recalculate_option(agency_id, journey_id, option["id"])
        await self._recalculate_journey(agency_id, journey_id)
        await self._audit("journey.segment_projected", stored, user, {"source_segment_id": stored.get("source_segment_id")})
        return self._response("segment", stored)

    async def create_connection(self, agency_id: str, journey_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = self._payload(payload)
        option = await self._require_option(journey_id, str(data.get("itinerary_option_id") or ""), agency_id)
        inbound = await self._require_segment(journey_id, str(data.get("inbound_segment_id") or ""), agency_id)
        outbound = await self._require_segment(journey_id, str(data.get("outbound_segment_id") or ""), agency_id)
        if inbound.get("itinerary_option_id") != option["id"] or outbound.get("itinerary_option_id") != option["id"]:
            raise CanonicalJourneyError("Connection segments must belong to the selected itinerary option.")
        inbound_arrival = self._datetime(inbound.get("arrival_utc"))
        outbound_departure = self._datetime(outbound.get("departure_utc"))
        connection_minutes = self._minutes(inbound_arrival, outbound_departure) if inbound_arrival and outbound_departure else None
        airport_change = bool(inbound.get("destination_airport_code") and outbound.get("origin_airport_code") and inbound.get("destination_airport_code") != outbound.get("origin_airport_code"))
        warnings = self._tokens(data.get("warning_codes"))
        if connection_minutes is None:
            warnings.append("connection_time_unknown")
        elif connection_minutes < 0:
            warnings.append("invalid_connection_chronology")
        if airport_change:
            warnings.append("airport_change_required")
        minimum = data.get("minimum_connection_minutes")
        values = {
            **data,
            "agency_id": agency_id,
            "journey_id": journey_id,
            "itinerary_option_id": option["id"],
            "inbound_segment_id": inbound["id"],
            "outbound_segment_id": outbound["id"],
            "airport_code": data.get("airport_code") or inbound.get("destination_airport_code"),
            "connection_minutes": connection_minutes if connection_minutes is not None else data.get("connection_minutes"),
            "connection_margin_minutes": (connection_minutes - int(minimum)) if connection_minutes is not None and minimum is not None else data.get("connection_margin_minutes"),
            "airport_change_required": airport_change or bool(data.get("airport_change_required")),
            "terminal_change_required": bool(data.get("terminal_change_required") or (inbound.get("arrival_terminal") and outbound.get("departure_terminal") and inbound.get("arrival_terminal") != outbound.get("departure_terminal"))),
            "overnight": self._overnight(inbound, outbound),
            "calendar_day_change": self._calendar_day_change(inbound, outbound),
            "manual_review_required": bool(data.get("manual_review_required") or warnings),
            "warning_codes": self._tokens(warnings),
            "status": "calculated" if connection_minutes is not None and connection_minutes >= 0 else "unknown",
        }
        stored = await self.db.collection(CONNECTION_COLLECTION).insert_one(JourneyConnectionRepresentation(**values).model_dump(mode="json"))
        if inbound.get("leg_id") and inbound.get("leg_id") == outbound.get("leg_id"):
            await self._recalculate_leg(agency_id, journey_id, str(inbound["leg_id"]))
        await self._recalculate_option(agency_id, journey_id, option["id"])
        await self._recalculate_journey(agency_id, journey_id)
        await self._audit("journey.connection_created", stored, user)
        return self._response("connection", stored)

    async def create_fare_brand(self, agency_id: str, journey_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = self._payload(payload)
        option = await self._require_option(journey_id, str(data.get("itinerary_option_id") or ""), agency_id)
        values = {**data, "agency_id": agency_id, "journey_id": journey_id, "itinerary_option_id": option["id"], "source_provenance": self._provenance(data.get("source_provenance"), option["source_entity_type"])}
        stored = await self.db.collection(FARE_BRAND_COLLECTION).insert_one(JourneyFareBrandPresentation(**values).model_dump(mode="json"))
        await self._audit("journey.fare_brand_attached", stored, user)
        return self._response("fare_brand", stored)

    async def create_service_presentation(self, agency_id: str, journey_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        await self._require_journey(journey_id, agency_id)
        data = self._payload(payload)
        if data.get("itinerary_option_id"):
            await self._require_option(journey_id, str(data["itinerary_option_id"]), agency_id)
        if data.get("segment_id"):
            await self._require_segment(journey_id, str(data["segment_id"]), agency_id)
        values = {**data, "agency_id": agency_id, "journey_id": journey_id, "source_provenance": self._provenance(data.get("source_provenance"), "structured_import")}
        stored = await self.db.collection(SERVICE_COLLECTION).insert_one(JourneyServicePresentation(**values).model_dump(mode="json"))
        await self._audit("journey.service_attached", stored, user)
        return self._response("service_presentation", stored)

    async def set_presentation(self, agency_id: str, journey_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        await self._require_journey(journey_id, agency_id)
        data = self._payload(payload)
        if data.get("client_safe_mode"):
            data["show_internal_information"] = False
        existing = await self.db.collection(PRESENTATION_COLLECTION).find_one({"agency_id": agency_id, "journey_id": journey_id})
        values = {**(existing or {}), **data, "agency_id": agency_id, "journey_id": journey_id}
        validated = JourneyPresentationConfiguration(**values).model_dump(mode="json")
        stored = (
            await self.db.collection(PRESENTATION_COLLECTION).update_one({"id": existing["id"], "agency_id": agency_id}, validated)
            if existing
            else await self.db.collection(PRESENTATION_COLLECTION).insert_one(validated)
        )
        if not stored:
            raise CanonicalJourneyError("Journey presentation configuration could not be saved.")
        await self._audit("journey.presentation_configured", stored, user)
        return self._response("presentation", stored)

    async def get_complete_journey(self, agency_id: str, journey_id: str, *, client_safe: bool = False, include_snapshots: bool = True) -> dict[str, Any]:
        journey = await self._require_journey(journey_id, agency_id)
        options = await self._children(OPTION_COLLECTION, agency_id, journey_id, "option_number")
        payload = {
            "journey": journey,
            "itinerary_options": options,
            "legs": await self._children(LEG_COLLECTION, agency_id, journey_id, "leg_number"),
            "segments": await self._children(SEGMENT_COLLECTION, agency_id, journey_id, "segment_number"),
            "connections": await self._children(CONNECTION_COLLECTION, agency_id, journey_id, "created_at"),
            "fare_brands": await self._children(FARE_BRAND_COLLECTION, agency_id, journey_id, "created_at"),
            "services": await self._children(SERVICE_COLLECTION, agency_id, journey_id, "created_at"),
            "presentation": await self.db.collection(PRESENTATION_COLLECTION).find_one({"agency_id": agency_id, "journey_id": journey_id}),
            "snapshots": await self.list_snapshots(agency_id, journey_id) if include_snapshots else [],
            "source_references": self._source_references(journey),
            **self.safety_flags(),
        }
        return self._client_safe(payload) if client_safe else payload

    async def create_snapshot(self, agency_id: str, journey_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        journey = await self._require_journey(journey_id, agency_id)
        data = self._payload(payload)
        existing = await self.list_snapshots(agency_id, journey_id)
        version = max([int(item.get("version_number") or 0) for item in existing] or [0]) + 1
        normalized = self._normalize_for_hash(await self.get_complete_journey(agency_id, journey_id, include_snapshots=False))
        content_hash = sha256(json.dumps(normalized, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
        finalize = bool(data.pop("finalize", True))
        values = {
            **data,
            "agency_id": agency_id,
            "journey_id": journey_id,
            "version_number": version,
            "snapshot_type": data.get("snapshot_type") or "journey_updated",
            "lifecycle_context": data.get("lifecycle_context") or journey.get("lifecycle_context") or "operational",
            "source_entity_type": data.get("source_entity_type") or journey["source_entity_type"],
            "source_entity_id": data.get("source_entity_id") or journey["source_entity_id"],
            "content_hash": content_hash,
            "normalized_payload": normalized,
            "created_by": self._actor(user),
            "finalized_at": self._now() if finalize else None,
            "immutable": finalize,
        }
        stored = await self.db.collection(SNAPSHOT_COLLECTION).insert_one(JourneySnapshot(**values).model_dump(mode="json"))
        await self.db.collection(JOURNEY_COLLECTION).update_one({"id": journey_id, "agency_id": agency_id}, {"current_version_number": version, "updated_by": self._actor(user)})
        await self._audit("journey.snapshot_created", stored, user, {"immutable": finalize, "content_hash": content_hash})
        return self._response("snapshot", stored)

    async def update_snapshot(self, agency_id: str, journey_id: str, snapshot_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        snapshot = await self._require_snapshot(journey_id, snapshot_id, agency_id)
        if snapshot.get("immutable") or snapshot.get("finalized_at"):
            raise FinalizedJourneySnapshotError("Finalized journey snapshots are immutable and cannot be edited.")
        allowed = {key: value for key, value in self._payload(payload).items() if key in {"snapshot_type", "lifecycle_context", "supersedes_snapshot_id", "metadata"}}
        validated = JourneySnapshot(**{**snapshot, **allowed}).model_dump(mode="json")
        updated = await self.db.collection(SNAPSHOT_COLLECTION).update_one({"id": snapshot_id, "agency_id": agency_id}, validated)
        if not updated:
            raise CanonicalJourneyError("Journey snapshot could not be updated.")
        await self._audit("journey.snapshot_updated", updated, user)
        return self._response("snapshot", updated)

    async def finalize_snapshot(self, agency_id: str, journey_id: str, snapshot_id: str, user: dict[str, Any]) -> dict[str, Any]:
        snapshot = await self._require_snapshot(journey_id, snapshot_id, agency_id)
        if snapshot.get("immutable") or snapshot.get("finalized_at"):
            raise FinalizedJourneySnapshotError("Finalized journey snapshots are immutable and cannot be finalized again.")
        updated = await self.db.collection(SNAPSHOT_COLLECTION).update_one({"id": snapshot_id, "agency_id": agency_id}, {"immutable": True, "finalized_at": self._now()})
        if not updated:
            raise CanonicalJourneyError("Journey snapshot could not be finalized.")
        await self._audit("journey.snapshot_finalized", updated, user)
        return self._response("snapshot", updated)

    async def list_snapshots(self, agency_id: str, journey_id: str) -> list[dict[str, Any]]:
        await self._require_journey(journey_id, agency_id)
        items = await self.db.collection(SNAPSHOT_COLLECTION).find_many({"agency_id": agency_id, "journey_id": journey_id})
        return sorted(items, key=lambda item: int(item.get("version_number") or 0), reverse=True)

    async def project_from_trip(self, agency_id: str, trip_id: str, user: dict[str, Any]) -> dict[str, Any]:
        source, source_kind = await self._find_source(agency_id, trip_id, [("trip_workspaces", "trip_workspace"), ("trip_dossiers", "trip_dossier")])
        existing = await self._existing_projection(agency_id, source_kind, trip_id)
        if existing:
            return {"phase": PHASE_LABEL, "created": False, **(await self.get_complete_journey(agency_id, existing["id"])), **self.safety_flags()}
        passengers = source.get("passenger_ids") or [item["id"] for item in await self.db.collection("trip_passengers").find_many({"agency_id": agency_id, "trip_id": trip_id})]
        segments = await self._trip_segments(agency_id, source, source_kind)
        services = await self.db.collection("trip_service_items").find_many({"agency_id": agency_id, "trip_id": trip_id})
        root = await self.create_journey({
            "agency_id": agency_id,
            "title": source.get("trip_title") or source.get("trip_reference") or "Trip journey",
            "journey_type": source.get("journey_type") or source.get("trip_type") or "unknown",
            "lifecycle_context": "trip",
            "source_entity_type": source_kind,
            "source_entity_id": trip_id,
            "client_id": source.get("client_id") or source.get("primary_client_id"),
            "passenger_ids": passengers,
            "primary_passenger_id": passengers[0] if passengers else None,
            "origin_airport_code": source.get("origin_airport"),
            "destination_airport_code": source.get("destination_airport"),
            "departure_date": source.get("departure_date"),
            "return_date": source.get("return_date"),
            "status": "active",
            "metadata": {"source_collection": "trip_workspaces" if source_kind == "trip_workspace" else "trip_dossiers", "source_record_id": trip_id},
        }, user, agency_id=agency_id)
        await self._project_option_bundle(agency_id, root["journey"], {"id": trip_id, "label": "Trip itinerary", "status": "active"}, segments, services, [], [], user, "existing_trip")
        return {"phase": PHASE_LABEL, "created": True, **(await self.get_complete_journey(agency_id, root["journey"]["id"])), **self.safety_flags()}

    async def project_from_offer(self, agency_id: str, offer_id: str, user: dict[str, Any]) -> dict[str, Any]:
        source, source_kind = await self._find_source(agency_id, offer_id, [("offer_workspaces_v2", "offer_workspace_v2"), ("offer_workspaces", "offer_workspace"), ("offers", "offer")])
        existing = await self._existing_projection(agency_id, source_kind, offer_id)
        if existing:
            return {"phase": PHASE_LABEL, "created": False, **(await self.get_complete_journey(agency_id, existing["id"])), **self.safety_flags()}
        acceptance = None
        if source_kind == "offer_workspace":
            acceptances = await self.db.collection("offer_acceptances").find_many(
                {"agency_id": agency_id, "workspace_id": offer_id, "status": "accepted"}
            )
            acceptances.sort(key=lambda item: str(item.get("accepted_at") or item.get("created_at") or ""), reverse=True)
            acceptance = acceptances[0] if acceptances else None
        trip_id = source.get("trip_workspace_id") or source.get("trip_id") or source.get("existing_trip_id")
        root = await self.create_journey({
            "agency_id": agency_id,
            "title": source.get("offer_title") or source.get("title") or "Offer journey",
            "journey_type": (source.get("metadata") or {}).get("journey_type", "unknown"),
            "lifecycle_context": "offer_accepted" if source.get("status") == "accepted" or source.get("offer_status") == "accepted" else "offer",
            "source_entity_type": source_kind,
            "source_entity_id": offer_id,
            "client_id": source.get("client_id"),
            "passenger_ids": source.get("passenger_ids") or [],
            "status": "active",
            "metadata": {
                "source_collection": "offer_workspaces_v2" if source_kind == "offer_workspace_v2" else "offer_workspaces" if source_kind == "offer_workspace" else "offers",
                "trip_reference_id": trip_id,
                "accepted_offer_snapshot_id": acceptance.get("id") if acceptance else None,
                "accepted_offer_snapshot_reused": bool(acceptance),
            },
        }, user, agency_id=agency_id)
        if acceptance:
            routing = acceptance.get("accepted_routing_snapshot_json") or {}
            fare_bundle = acceptance.get("accepted_fare_bundle_snapshot_json") or {}
            pricing = acceptance.get("accepted_pricing_snapshot_json") or {}
            await self._project_option_bundle(
                agency_id,
                root["journey"],
                {
                    "id": acceptance.get("option_id") or acceptance["id"],
                    "label": "Accepted itinerary snapshot",
                    "status": "accepted",
                },
                self._record_list(routing.get("segments")),
                self._record_list(acceptance.get("accepted_services_snapshot_json")),
                self._record_list(fare_bundle.get("items") or fare_bundle.get("primary")),
                self._record_list(pricing.get("lines")),
                user,
                "existing_offer",
            )
            return {"phase": PHASE_LABEL, "created": True, **(await self.get_complete_journey(agency_id, root["journey"]["id"])), **self.safety_flags()}
        options = await self.db.collection("offer_options").find_many({"agency_id": agency_id, "workspace_id": offer_id}) if source_kind == "offer_workspace" else []
        if not options:
            options = [{"id": offer_id, "label": source.get("offer_title") or source.get("title") or "Offer itinerary", "status": source.get("offer_status") or source.get("status") or "draft", "recommendation_rank": None}]
        for option_source in options:
            segments = await self._offer_segments(agency_id, source, source_kind, option_source)
            fare_bundles = await self.db.collection("offer_fare_bundles").find_many({"agency_id": agency_id, "option_id": option_source["id"]})
            pricing = await self.db.collection("offer_pricing_lines").find_many({"agency_id": agency_id, "option_id": option_source["id"]})
            services = await self.db.collection("offer_service_checks").find_many({"agency_id": agency_id, "offer_id": offer_id})
            await self._project_option_bundle(agency_id, root["journey"], option_source, segments, services, fare_bundles, pricing, user, "existing_offer")
        return {"phase": PHASE_LABEL, "created": True, **(await self.get_complete_journey(agency_id, root["journey"]["id"])), **self.safety_flags()}

    async def project_from_booking(self, agency_id: str, booking_id: str, user: dict[str, Any]) -> dict[str, Any]:
        source, source_kind = await self._find_source(agency_id, booking_id, [("booking_workspaces", "booking_workspace"), ("booking_records", "booking_record"), ("bookings", "booking")])
        existing = await self._existing_projection(agency_id, source_kind, booking_id)
        if existing:
            return {"phase": PHASE_LABEL, "created": False, **(await self.get_complete_journey(agency_id, existing["id"])), **self.safety_flags()}
        segments = list(source.get("segments_snapshot_json") or source.get("segments_json") or [])
        if not segments:
            segments = await self._flight_workspace_segments(agency_id, source.get("flight_workspace_ids") or [])
        root = await self.create_journey({
            "agency_id": agency_id,
            "title": source.get("title") or source.get("booking_reference") or source.get("workspace_number") or "Booking journey",
            "journey_type": (source.get("metadata") or {}).get("journey_type", "unknown"),
            "lifecycle_context": "booking_confirmation",
            "source_entity_type": source_kind,
            "source_entity_id": booking_id,
            "client_id": source.get("client_id"),
            "passenger_ids": source.get("passenger_ids") or [str(item.get("id")) for item in source.get("passengers_snapshot_json") or source.get("passengers_json") or [] if item.get("id")],
            "status": "active",
            "metadata": {"trip_reference_id": source.get("trip_workspace_id") or source.get("trip_id"), "offer_reference_id": source.get("offer_workspace_id"), "ticket_reference_ids": source.get("ticket_ids") or [], "emd_reference_ids": source.get("emd_ids") or []},
        }, user, agency_id=agency_id)
        services_value = source.get("services_snapshot_json") or source.get("services_json") or {}
        services = list(services_value.values()) if isinstance(services_value, dict) else list(services_value or [])
        pricing_value = source.get("pricing_snapshot_json") or source.get("pricing_json") or {}
        pricing = pricing_value.get("lines") or [] if isinstance(pricing_value, dict) else []
        await self._project_option_bundle(agency_id, root["journey"], {"id": booking_id, "label": "Booked itinerary", "status": source.get("booking_status") or source.get("status") or "confirmed"}, segments, services, [], pricing, user, "existing_booking")
        return {"phase": PHASE_LABEL, "created": True, **(await self.get_complete_journey(agency_id, root["journey"]["id"])), **self.safety_flags()}

    async def project_from_ticket(self, agency_id: str, ticket_id: str, user: dict[str, Any]) -> dict[str, Any]:
        source, source_kind = await self._find_source(agency_id, ticket_id, [("ticket_workspaces", "ticket_workspace"), ("ticket_records", "ticket_record")])
        existing = await self._existing_projection(agency_id, source_kind, ticket_id)
        if existing:
            return {"phase": PHASE_LABEL, "created": False, **(await self.get_complete_journey(agency_id, existing["id"])), **self.safety_flags()}
        segments = list(source.get("coupon_details") or [])
        root = await self.create_journey({
            "agency_id": agency_id,
            "title": source.get("ticket_reference") or source.get("ticket_number") or "Ticket journey",
            "lifecycle_context": "ticket_issued",
            "source_entity_type": source_kind,
            "source_entity_id": ticket_id,
            "passenger_ids": [source["passenger_id"]] if source.get("passenger_id") else [],
            "status": "active",
            "metadata": {"booking_reference_id": source.get("booking_workspace_id"), "ticket_number": source.get("ticket_number"), "emd_reference_ids": source.get("linked_emd_ids") or []},
        }, user, agency_id=agency_id)
        await self._project_option_bundle(agency_id, root["journey"], {"id": ticket_id, "label": "Ticket itinerary", "status": source.get("ticket_document_status") or "issued"}, segments, [], [], [], user, "ticket_record")
        return {"phase": PHASE_LABEL, "created": True, **(await self.get_complete_journey(agency_id, root["journey"]["id"])), **self.safety_flags()}

    async def project_from_emd(self, agency_id: str, emd_id: str, user: dict[str, Any]) -> dict[str, Any]:
        source, source_kind = await self._find_source(agency_id, emd_id, [("emd_workspaces", "emd_workspace"), ("emd_records", "emd_record")])
        existing = await self._existing_projection(agency_id, source_kind, emd_id)
        if existing:
            return {"phase": PHASE_LABEL, "created": False, **(await self.get_complete_journey(agency_id, existing["id"])), **self.safety_flags()}
        segments = list(source.get("emd_coupon_details") or source.get("coupon_details") or [])
        if not segments:
            segments = await self._flight_workspace_segments(agency_id, source.get("associated_flight_workspace_ids") or source.get("flight_workspace_ids") or [])
        root = await self.create_journey({
            "agency_id": agency_id,
            "title": source.get("emd_reference") or source.get("emd_number") or "EMD journey",
            "lifecycle_context": "emd_record",
            "source_entity_type": source_kind,
            "source_entity_id": emd_id,
            "passenger_ids": [source["passenger_id"]] if source.get("passenger_id") else [],
            "status": "active",
            "metadata": {"booking_reference_id": source.get("booking_workspace_id"), "ticket_reference_id": source.get("ticket_workspace_id"), "emd_number": source.get("emd_number")},
        }, user, agency_id=agency_id)
        services = [{"service_code": source.get("service_code") or source.get("rfic") or "EMD", "service_name": source.get("service_description") or source.get("service_category") or "EMD service", "request_status": source.get("emd_document_status") or "unknown", "EMD_required": True}]
        await self._project_option_bundle(agency_id, root["journey"], {"id": emd_id, "label": "EMD-linked itinerary", "status": source.get("emd_document_status") or "unknown"}, segments, services, [], [], user, "ticket_record")
        return {"phase": PHASE_LABEL, "created": True, **(await self.get_complete_journey(agency_id, root["journey"]["id"])), **self.safety_flags()}

    async def _project_option_bundle(
        self,
        agency_id: str,
        journey: dict[str, Any],
        option_source: dict[str, Any],
        source_segments: list[dict[str, Any]],
        source_services: list[dict[str, Any]],
        fare_bundles: list[dict[str, Any]],
        pricing_lines: list[dict[str, Any]],
        user: dict[str, Any],
        provenance_type: str,
    ) -> None:
        option = (await self.create_option(agency_id, journey["id"], {
            "title": option_source.get("label") or option_source.get("title") or "Itinerary option",
            "source_entity_type": journey["source_entity_type"],
            "source_entity_id": str(option_source.get("id") or journey["source_entity_id"]),
            "status": option_source.get("status") or "draft",
            "recommendation_rank": option_source.get("recommendation_rank"),
            "recommendation_reference_id": option_source.get("recommendation_reference_id"),
            "feasibility_reference_id": option_source.get("feasibility_reference_id"),
            "warning_codes": [item.get("code") or item.get("warning_code") for item in option_source.get("warnings_json") or [] if item.get("code") or item.get("warning_code")],
            "source_provenance": {"provenance_type": provenance_type, "data_state": self._source_state(provenance_type), "verified": False},
        }, user))["itinerary_option"]
        leg = (await self.create_leg(agency_id, journey["id"], {"itinerary_option_id": option["id"], "leg_type": "flight", "presentation_label": option["title"]}, user))["leg"]
        projected_segments: list[dict[str, Any]] = []
        for index, source in enumerate(source_segments, start=1):
            segment_payload = self._segment_payload(source, index, option, leg, provenance_type)
            projected = (await self.create_segment(agency_id, journey["id"], segment_payload, user))["segment"]
            projected_segments.append(projected)
        for inbound, outbound in zip(projected_segments, projected_segments[1:]):
            await self.create_connection(agency_id, journey["id"], {"itinerary_option_id": option["id"], "inbound_segment_id": inbound["id"], "outbound_segment_id": outbound["id"]}, user)
        if projected_segments:
            await self.db.collection(LEG_COLLECTION).update_one({"id": leg["id"], "agency_id": agency_id}, {
                "origin_airport_code": projected_segments[0].get("origin_airport_code"),
                "destination_airport_code": projected_segments[-1].get("destination_airport_code"),
                "departure_at": projected_segments[0].get("departure_utc") or projected_segments[0].get("departure_local"),
                "arrival_at": projected_segments[-1].get("arrival_utc") or projected_segments[-1].get("arrival_local"),
                "segment_ids": [item["id"] for item in projected_segments],
                "status": "active",
            })
        for source in source_services:
            code = source.get("service_code") or source.get("service_key") or source.get("ssr_code") or "SERVICE"
            await self.create_service_presentation(agency_id, journey["id"], {
                "itinerary_option_id": option["id"],
                "passenger_id": source.get("passenger_id"),
                "segment_id": source.get("segment_id"),
                "service_code": str(code),
                "canonical_service_reference_id": source.get("service_catalogue_id"),
                "service_name": source.get("service_name") or source.get("service_label") or str(code),
                "request_status": source.get("request_status") or source.get("status") or "unknown",
                "feasibility_status": source.get("feasibility_status") or source.get("support_status") or "unknown",
                "confirmation_status": source.get("confirmation_status") or "unknown",
                "approval_required": bool(source.get("approval_required") or source.get("requires_airline_confirmation")),
                "document_required": bool(source.get("document_required") or source.get("requires_documents")),
                "EMD_required": bool(source.get("EMD_required") or source.get("emd_required")),
                "SSR_codes": source.get("SSR_codes") or source.get("ssr_codes") or [],
                "client_safe_summary": source.get("client_safe_summary") or source.get("client_visible_summary"),
                "internal_summary": source.get("internal_summary") or source.get("internal_notes") or source.get("notes"),
                "source_provenance": {"provenance_type": provenance_type, "data_state": self._source_state(provenance_type)},
            }, user)
        total_price = sum(float(item.get("amount") or 0) for item in pricing_lines if self._number(item.get("amount")) is not None) if pricing_lines else None
        currencies = self._tokens([item.get("currency") for item in pricing_lines])
        for bundle in fare_bundles:
            await self.create_fare_brand(agency_id, journey["id"], {
                "itinerary_option_id": option["id"],
                "fare_brand_reference_id": bundle.get("id"),
                "fare_family_reference_id": bundle.get("fare_family_reference_id"),
                "cabin_code": bundle.get("cabin_class") or bundle.get("cabin"),
                "booking_class_codes": self._tokens([bundle.get("booking_class")]),
                "brand_name": bundle.get("fare_family_name") or bundle.get("brand_name") or "Fare brand",
                "client_display_name": bundle.get("client_display_name") or bundle.get("fare_family_name"),
                "included_attributes": self._dict_items(bundle.get("included_attributes") or bundle.get("included_baggage_json")),
                "baggage_summary": bundle.get("baggage_summary") or self._summary_text(bundle.get("included_baggage_json")),
                "change_summary": bundle.get("change_summary") or self._summary_text(bundle.get("change_rules_json")),
                "refund_summary": bundle.get("refund_summary") or self._summary_text(bundle.get("refund_rules_json")),
                "seat_summary": bundle.get("seat_summary") or self._summary_text(bundle.get("seat_selection_rules_json")),
                "currency": currencies[0] if len(currencies) == 1 else None,
                "total_price": total_price,
                "price_reference_ids": [item["id"] for item in pricing_lines if item.get("id")],
                "data_status": "imported",
                "source_provenance": {"provenance_type": provenance_type, "data_state": self._source_state(provenance_type)},
            }, user)
        await self.set_presentation(agency_id, journey["id"], {}, user)

    def _segment_payload(self, source: dict[str, Any], index: int, option: dict[str, Any], leg: dict[str, Any], provenance_type: str) -> dict[str, Any]:
        departure = self._source_datetime(source, "departure")
        arrival = self._source_datetime(source, "arrival")
        source_id = source.get("id") or source.get("source_segment_id") or source.get("segment_reference") or f"{option['source_entity_id']}:segment:{index}"
        marketing = source.get("marketing_carrier_code") or source.get("marketing_airline_code") or source.get("marketing_carrier") or source.get("marketing_airline")
        operating = source.get("operating_carrier_code") or source.get("operating_airline_code") or source.get("operating_carrier") or source.get("operating_airline")
        return {
            "itinerary_option_id": option["id"],
            "leg_id": leg["id"],
            "segment_number": int(source.get("segment_order") or source.get("sequence") or source.get("coupon_number") or index),
            "source_entity_type": self._token(source.get("source_entity_type") or self._segment_source_type(provenance_type)),
            "source_entity_id": option["source_entity_id"],
            "source_segment_id": str(source_id),
            "segment_type": source.get("segment_type") or "flight",
            "marketing_carrier_code": marketing,
            "marketing_flight_number": source.get("marketing_flight_number") or source.get("flight_number"),
            "operating_carrier_code": operating,
            "operating_flight_number": source.get("operating_flight_number"),
            "origin_airport_code": source.get("origin_airport_code") or source.get("origin_airport") or source.get("origin"),
            "destination_airport_code": source.get("destination_airport_code") or source.get("destination_airport") or source.get("destination"),
            "departure_local": departure,
            "arrival_local": arrival,
            "departure_utc": source.get("departure_utc") or source.get("departure_at") or source.get("departure_datetime"),
            "arrival_utc": source.get("arrival_utc") or source.get("arrival_at") or source.get("arrival_datetime"),
            "departure_timezone": source.get("departure_timezone"),
            "arrival_timezone": source.get("arrival_timezone"),
            "aircraft_code": source.get("aircraft_code") or source.get("aircraft_type"),
            "aircraft_display_name": source.get("aircraft_display_name"),
            "departure_terminal": source.get("departure_terminal"),
            "arrival_terminal": source.get("arrival_terminal"),
            "cabin_code": source.get("cabin_code") or source.get("cabin") or source.get("cabin_class"),
            "booking_class_code": source.get("booking_class_code") or source.get("booking_class"),
            "status": source.get("segment_status") or source.get("coupon_status") or source.get("status") or "proposed",
            "manually_adjusted": bool(source.get("manually_adjusted")),
            "source_provenance": {"provenance_type": provenance_type, "data_state": self._source_state(provenance_type), "source_reference": str(source_id), "verified": provenance_type in {"ticket_record", "airline_confirmation"}},
            "metadata": {"fare_basis": source.get("fare_basis"), "segment_reference": source.get("segment_reference")},
        }

    async def _trip_segments(self, agency_id: str, source: dict[str, Any], source_kind: str) -> list[dict[str, Any]]:
        if source_kind == "trip_dossier":
            items = await self.db.collection("trip_segments").find_many({"agency_id": agency_id, "trip_id": source["id"]})
            return sorted(items, key=lambda item: int(item.get("segment_order") or 0))
        return await self._flight_workspace_segments(agency_id, source.get("flight_workspace_ids") or [])

    async def _offer_segments(self, agency_id: str, source: dict[str, Any], source_kind: str, option: dict[str, Any]) -> list[dict[str, Any]]:
        if source_kind == "offer_workspace":
            items = await self.db.collection("offer_builder_segments").find_many({"agency_id": agency_id, "option_id": option["id"]})
            return sorted(items, key=lambda item: int(item.get("sequence") or 0))
        if source_kind == "offer_workspace_v2":
            return await self._flight_workspace_segments(agency_id, source.get("flight_workspace_ids") or [])
        items = await self.db.collection("offer_segments").find_many({"agency_id": agency_id, "offer_id": source["id"]})
        return sorted(items, key=lambda item: int(item.get("sequence") or item.get("segment_order") or 0))

    async def _flight_workspace_segments(self, agency_id: str, ids: Iterable[str]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for flight_id in ids:
            item = await self.db.collection("flight_workspaces").find_one({"id": flight_id, "agency_id": agency_id})
            if item:
                items.append(item)
        return sorted(items, key=lambda item: str(item.get("departure_datetime") or item.get("created_at") or ""))

    async def _recalculate_leg(self, agency_id: str, journey_id: str, leg_id: str) -> None:
        leg = await self._require_leg(journey_id, leg_id, agency_id)
        segments = await self.db.collection(SEGMENT_COLLECTION).find_many(
            {"agency_id": agency_id, "journey_id": journey_id, "leg_id": leg_id}
        )
        segments.sort(key=lambda item: (int(item.get("segment_number") or 0), str(item.get("departure_utc") or item.get("departure_local") or "")))
        segment_ids = [item["id"] for item in segments]
        connections = await self.db.collection(CONNECTION_COLLECTION).find_many(
            {"agency_id": agency_id, "journey_id": journey_id, "itinerary_option_id": leg["itinerary_option_id"]}
        )
        connection_ids = [
            item["id"]
            for item in connections
            if item.get("inbound_segment_id") in segment_ids and item.get("outbound_segment_id") in segment_ids
        ]
        first = segments[0] if segments else {}
        last = segments[-1] if segments else {}
        departure_utc = self._datetime(first.get("departure_utc"))
        arrival_utc = self._datetime(last.get("arrival_utc"))
        elapsed = self._minutes(departure_utc, arrival_utc) if departure_utc and arrival_utc else None
        if elapsed is not None and elapsed < 0:
            elapsed = None
        await self.db.collection(LEG_COLLECTION).update_one(
            {"id": leg_id, "agency_id": agency_id},
            {
                "origin_airport_code": first.get("origin_airport_code") or leg.get("origin_airport_code"),
                "destination_airport_code": last.get("destination_airport_code") or leg.get("destination_airport_code"),
                "departure_at": first.get("departure_utc") or first.get("departure_local") or leg.get("departure_at"),
                "arrival_at": last.get("arrival_utc") or last.get("arrival_local") or leg.get("arrival_at"),
                "elapsed_minutes": elapsed,
                "segment_ids": segment_ids,
                "connection_ids": connection_ids,
            },
        )

    async def _recalculate_option(self, agency_id: str, journey_id: str, option_id: str) -> None:
        option = await self._require_option(journey_id, option_id, agency_id)
        segments = await self.db.collection(SEGMENT_COLLECTION).find_many({"agency_id": agency_id, "journey_id": journey_id, "itinerary_option_id": option_id})
        segments.sort(key=lambda item: (int(item.get("segment_number") or 0), str(item.get("departure_utc") or item.get("departure_local") or "")))
        connections = await self.db.collection(CONNECTION_COLLECTION).find_many({"agency_id": agency_id, "journey_id": journey_id, "itinerary_option_id": option_id})
        display_departures = [self._datetime(item.get("departure_utc") or item.get("departure_local")) for item in segments]
        display_arrivals = [self._datetime(item.get("arrival_utc") or item.get("arrival_local")) for item in segments]
        utc_departures = [self._datetime(item.get("departure_utc")) for item in segments]
        utc_arrivals = [self._datetime(item.get("arrival_utc")) for item in segments]
        valid_display_departures = [value for value in display_departures if value]
        valid_display_arrivals = [value for value in display_arrivals if value]
        valid_utc_departures = [value for value in utc_departures if value]
        valid_utc_arrivals = [value for value in utc_arrivals if value]
        first = min(valid_display_departures, key=self._datetime_sort_key) if valid_display_departures else None
        last = max(valid_display_arrivals, key=self._datetime_sort_key) if valid_display_arrivals else None
        first_utc = min(valid_utc_departures, key=self._datetime_sort_key) if valid_utc_departures else None
        last_utc = max(valid_utc_arrivals, key=self._datetime_sort_key) if valid_utc_arrivals else None
        total_elapsed = self._minutes(first_utc, last_utc) if first_utc and last_utc and self._minutes(first_utc, last_utc) >= 0 else None
        flying = [item.get("scheduled_duration_minutes") for item in segments if item.get("scheduled_duration_minutes") is not None]
        connection_values = [item.get("connection_minutes") for item in connections if item.get("connection_minutes") is not None and item.get("connection_minutes") >= 0]
        warnings = self._tokens([*(option.get("warning_codes") or []), *[code for item in segments for code in item.get("warning_codes") or []], *[code for item in connections for code in item.get("warning_codes") or []]])
        await self.db.collection(OPTION_COLLECTION).update_one({"id": option_id, "agency_id": agency_id}, {
            "departure_at": first,
            "arrival_at": last,
            "total_elapsed_minutes": total_elapsed,
            "total_flying_minutes": sum(int(value) for value in flying) if flying else None,
            "total_connection_minutes": sum(int(value) for value in connection_values) if connection_values else None,
            "total_segment_count": len(segments),
            "total_connection_count": len(connections),
            "overnight_connection_count": sum(bool(item.get("overnight")) for item in connections),
            "airport_change_count": sum(bool(item.get("airport_change_required")) for item in connections),
            "surface_sector_count": sum(item.get("segment_type") == "surface" for item in segments),
            "operating_airline_codes": self._tokens([item.get("operating_carrier_code") for item in segments]),
            "marketing_airline_codes": self._tokens([item.get("marketing_carrier_code") for item in segments]),
            "manual_review_required": bool(warnings or any(item.get("manual_review_required") for item in segments + connections)),
            "warning_codes": warnings,
        })

    async def _recalculate_journey(self, agency_id: str, journey_id: str) -> None:
        journey = await self._require_journey(journey_id, agency_id)
        segments = await self.db.collection(SEGMENT_COLLECTION).find_many({"agency_id": agency_id, "journey_id": journey_id})
        segments.sort(key=lambda item: (str(item.get("departure_utc") or item.get("departure_local") or "9999"), int(item.get("segment_number") or 0)))
        values = dict(journey)
        if segments:
            values["origin_airport_code"] = segments[0].get("origin_airport_code") or values.get("origin_airport_code")
            values["destination_airport_code"] = segments[-1].get("destination_airport_code") or values.get("destination_airport_code")
            departure = self._datetime(segments[0].get("departure_utc") or segments[0].get("departure_local"))
            arrival = self._datetime(segments[-1].get("arrival_utc") or segments[-1].get("arrival_local"))
            values["departure_date"] = departure.date() if departure else values.get("departure_date")
            values["return_date"] = arrival.date() if arrival and len(segments) > 1 else values.get("return_date")
        values.update(self._journey_completeness(values, segments))
        await self.db.collection(JOURNEY_COLLECTION).update_one({"id": journey_id, "agency_id": agency_id}, values)

    def _journey_completeness(self, values: dict[str, Any], segments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        checks = [values.get("origin_airport_code"), values.get("destination_airport_code"), values.get("departure_date"), values.get("passenger_ids")]
        score = round(100 * sum(bool(value) for value in checks) / len(checks))
        if segments is not None and not segments:
            score = min(score, 50)
        status = "complete" if score == 100 else "partial" if score >= 50 else "incomplete"
        warnings = [item for item in self._tokens(values.get("warning_codes")) if item not in {"route_incomplete", "segments_missing"}]
        if not values.get("origin_airport_code") or not values.get("destination_airport_code"):
            warnings.append("route_incomplete")
        if segments is not None and not segments:
            warnings.append("segments_missing")
        return {"completeness_score": score, "data_completeness_status": status, "manual_review_required": bool(values.get("manual_review_required") or warnings), "warning_codes": self._tokens(warnings)}

    def _segment_completeness(self, values: dict[str, Any]) -> dict[str, Any]:
        checks = [values.get("origin_airport_code"), values.get("destination_airport_code"), values.get("departure_utc") or values.get("departure_local"), values.get("arrival_utc") or values.get("arrival_local")]
        score = round(100 * sum(bool(value) for value in checks) / len(checks))
        status = "complete" if score == 100 else "partial" if score >= 50 else "incomplete"
        warnings: list[str] = []
        if not values.get("origin_airport_code") or not values.get("destination_airport_code"):
            warnings.append("segment_airports_incomplete")
        if not (values.get("departure_utc") or values.get("departure_local")) or not (values.get("arrival_utc") or values.get("arrival_local")):
            warnings.append("segment_schedule_incomplete")
        return {"completeness_score": score, "data_completeness_status": status, "warning_codes": warnings}

    async def _find_source(self, agency_id: str, source_id: str, candidates: list[tuple[str, str]]) -> tuple[dict[str, Any], str]:
        for collection, source_kind in candidates:
            source = await self.db.collection(collection).find_one({"id": source_id, "agency_id": agency_id})
            if source:
                return source, source_kind
        raise CanonicalJourneyError("Canonical source record was not found for this agency.")

    async def _existing_projection(self, agency_id: str, source_type: str, source_id: str) -> dict[str, Any] | None:
        return await self.db.collection(JOURNEY_COLLECTION).find_one({"agency_id": agency_id, "source_entity_type": source_type, "source_entity_id": source_id})

    async def _require_journey(self, journey_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": journey_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(JOURNEY_COLLECTION).find_one(filters)
        if not item:
            raise CanonicalJourneyError("Journey representation was not found for this agency.")
        return item

    async def _require_option(self, journey_id: str, option_id: str, agency_id: str) -> dict[str, Any]:
        item = await self.db.collection(OPTION_COLLECTION).find_one({"id": option_id, "agency_id": agency_id, "journey_id": journey_id})
        if not item:
            raise CanonicalJourneyError("Itinerary option was not found for this journey.")
        return item

    async def _require_leg(self, journey_id: str, leg_id: str, agency_id: str) -> dict[str, Any]:
        item = await self.db.collection(LEG_COLLECTION).find_one({"id": leg_id, "agency_id": agency_id, "journey_id": journey_id})
        if not item:
            raise CanonicalJourneyError("Journey leg was not found for this journey.")
        return item

    async def _require_segment(self, journey_id: str, segment_id: str, agency_id: str) -> dict[str, Any]:
        item = await self.db.collection(SEGMENT_COLLECTION).find_one({"id": segment_id, "agency_id": agency_id, "journey_id": journey_id})
        if not item:
            raise CanonicalJourneyError("Journey segment projection was not found for this journey.")
        return item

    async def _require_snapshot(self, journey_id: str, snapshot_id: str, agency_id: str) -> dict[str, Any]:
        item = await self.db.collection(SNAPSHOT_COLLECTION).find_one({"id": snapshot_id, "agency_id": agency_id, "journey_id": journey_id})
        if not item:
            raise CanonicalJourneyError("Journey snapshot was not found for this journey.")
        return item

    async def _children(self, collection: str, agency_id: str, journey_id: str, sort_key: str) -> list[dict[str, Any]]:
        items = await self.db.collection(collection).find_many({"agency_id": agency_id, "journey_id": journey_id})
        return sorted(items, key=lambda item: item.get(sort_key) or 0)

    async def _audit(self, event_type: str, item: dict[str, Any], user: dict[str, Any], metadata: dict[str, Any] | None = None) -> None:
        event = AuditEvent(
            agency_id=item.get("agency_id"),
            actor_user_id=self._actor(user),
            event_type=event_type,
            entity_type="canonical_journey_representation",
            entity_id=item["id"],
            summary=event_type.replace(".", " ").replace("_", " ").title(),
            metadata={"journey_id": item.get("journey_id") or item.get("id"), "metadata_only": True, **(metadata or {})},
        )
        await self.db.collection("audit_events").insert_one(event.model_dump(mode="json"))

    def _client_safe(self, value: Any) -> Any:
        restricted = {
            "internal_summary",
            "internal_notes",
            "operational_notes",
            "private_source_location",
            "provider_payload_json",
            "raw_source_payloads",
            "credentials",
            "secret",
            "storage_reference",
        }
        if isinstance(value, list):
            return [self._client_safe(item) for item in value]
        if isinstance(value, dict):
            clean = {key: self._client_safe(child) for key, child in value.items() if key not in restricted}
            if "show_internal_information" in clean:
                clean["show_internal_information"] = False
            clean["client_safe_projection"] = True
            return clean
        return value

    def _normalize_for_hash(self, value: Any) -> Any:
        volatile = {"created_at", "updated_at", "finalized_at", "content_hash", "snapshots", "current_version_number"}
        if isinstance(value, list):
            return [self._normalize_for_hash(item) for item in value]
        if isinstance(value, dict):
            return {key: self._normalize_for_hash(child) for key, child in sorted(value.items()) if key not in volatile}
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value

    def _source_references(self, journey: dict[str, Any]) -> dict[str, Any]:
        metadata = journey.get("metadata") or {}
        return {
            "source_entity_type": journey.get("source_entity_type"),
            "source_entity_id": journey.get("source_entity_id"),
            "trip_reference_id": metadata.get("trip_reference_id"),
            "offer_reference_id": metadata.get("offer_reference_id"),
            "booking_reference_id": metadata.get("booking_reference_id"),
            "ticket_reference_id": metadata.get("ticket_reference_id"),
            "ticket_reference_ids": metadata.get("ticket_reference_ids") or [],
            "emd_reference_ids": metadata.get("emd_reference_ids") or [],
        }

    def _source_datetime(self, source: dict[str, Any], prefix: str) -> Any:
        direct = source.get(f"{prefix}_local") or source.get(f"{prefix}_at") or source.get(f"{prefix}_datetime") or source.get(f"{prefix}_utc")
        if direct:
            return direct
        date_value = source.get(f"{prefix}_date")
        time_value = source.get(f"{prefix}_time")
        parsed_date = self._date(date_value)
        if not parsed_date:
            return None
        parsed_time = self._time(time_value) or time.min
        return datetime.combine(parsed_date, parsed_time)

    def _provenance(self, value: Any, default_type: str) -> dict[str, Any]:
        provenance = dict(value or {}) if isinstance(value, dict) else {}
        provenance_type = self._token(provenance.get("provenance_type") or default_type or "manual_entry")
        if provenance_type not in SOURCE_PROVENANCE_TYPES:
            provenance_type = "structured_import"
        provenance["provenance_type"] = provenance_type
        provenance["data_state"] = self._token(provenance.get("data_state") or self._source_state(provenance_type))
        provenance.setdefault("verified", False)
        return provenance

    def _source_state(self, provenance_type: str) -> str:
        return {"ticket_record": "issued", "airline_confirmation": "confirmed", "existing_booking": "confirmed", "existing_trip": "normalized", "existing_offer": "normalized", "manual_entry": "agent_reviewed"}.get(provenance_type, "imported")

    def _segment_source_type(self, provenance_type: str) -> str:
        return {"existing_trip": "trip_segment", "existing_offer": "offer_segment", "existing_booking": "booking_segment", "ticket_record": "ticket_coupon"}.get(provenance_type, provenance_type)

    def _response(self, key: str, value: Any) -> dict[str, Any]:
        return {"phase": PHASE_LABEL, key: value, **self.safety_flags()}

    def _payload(self, payload: BaseModel | dict[str, Any] | None) -> dict[str, Any]:
        if isinstance(payload, BaseModel):
            return payload.model_dump(mode="json", exclude_unset=True)
        return dict(payload or {})

    def _reference(self, prefix: str) -> str:
        return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

    def _actor(self, user: dict[str, Any]) -> str:
        return str(user.get("id") or user.get("email") or "system")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _token(self, value: Any) -> str:
        return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")

    def _tokens(self, values: Any) -> list[str]:
        if values is None:
            return []
        if not isinstance(values, (list, tuple, set)):
            values = [values]
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            text = str(value or "").strip()
            if text and text.lower() not in seen:
                seen.add(text.lower())
                result.append(text)
        return result

    def _counts(self, items: list[dict[str, Any]], key: str) -> dict[str, int]:
        result: dict[str, int] = {}
        for item in items:
            value = str(item.get(key) or "unknown")
            result[value] = result.get(value, 0) + 1
        return result

    def _datetime(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed
        except ValueError:
            return None

    def _date(self, value: Any) -> date | None:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value)) if value else None
        except ValueError:
            return None

    def _time(self, value: Any) -> time | None:
        if isinstance(value, time):
            return value
        try:
            return time.fromisoformat(str(value)) if value else None
        except ValueError:
            return None

    def _minutes(self, start: datetime, end: datetime) -> int:
        if start.tzinfo is None and end.tzinfo is not None:
            start = start.replace(tzinfo=end.tzinfo)
        if end.tzinfo is None and start.tzinfo is not None:
            end = end.replace(tzinfo=start.tzinfo)
        return round((end - start).total_seconds() / 60)

    def _datetime_sort_key(self, value: datetime) -> float:
        normalized = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        return normalized.timestamp()

    def _overnight(self, inbound: dict[str, Any], outbound: dict[str, Any]) -> bool:
        arrival = self._datetime(inbound.get("arrival_local") or inbound.get("arrival_utc"))
        departure = self._datetime(outbound.get("departure_local") or outbound.get("departure_utc"))
        return bool(arrival and departure and departure.date() > arrival.date())

    def _calendar_day_change(self, inbound: dict[str, Any], outbound: dict[str, Any]) -> bool:
        return self._overnight(inbound, outbound)

    def _number(self, value: Any) -> float | None:
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def _dict_items(self, value: Any) -> list[dict[str, Any]]:
        if isinstance(value, list):
            return [item if isinstance(item, dict) else {"label": str(item)} for item in value]
        if isinstance(value, dict):
            return [{"code": str(key), "value": child} for key, child in value.items()]
        return []

    def _record_list(self, value: Any) -> list[dict[str, Any]]:
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if not isinstance(value, dict) or not value:
            return []
        if any(key in value for key in {"id", "service_code", "service_key", "fare_family_name", "brand_name"}):
            return [value]
        records: list[dict[str, Any]] = []
        for child in value.values():
            if isinstance(child, list):
                records.extend(item for item in child if isinstance(item, dict))
            elif isinstance(child, dict):
                records.append(child)
        return records

    def _summary_text(self, value: Any) -> str | None:
        if not value:
            return None
        if isinstance(value, str):
            return value
        return ", ".join(f"{key}: {child}" for key, child in value.items()) if isinstance(value, dict) else str(value)
