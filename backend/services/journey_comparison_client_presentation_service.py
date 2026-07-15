from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from hashlib import sha256
from typing import Any

from database import Database
from models import (
    JourneyComparisonConnectionProjection,
    JourneyComparisonDimension,
    JourneyComparisonFareBrandProjection,
    JourneyComparisonOptionProjection,
    JourneyComparisonPresentation,
    JourneyComparisonResult,
    JourneyComparisonSegmentProjection,
    JourneyComparisonServiceSuitabilityProjection,
    JourneyPresentationConfiguration,
    JourneyPresentationContentBlock,
    JourneyPresentationHandoff,
    JourneyPresentationReview,
    JourneyPresentationSnapshot,
)
from services.journey_option_fare_brand_composition_service import (
    JourneyOptionCompositionError,
    JourneyOptionFareBrandCompositionService,
)


from build_phase import CURRENT_BUILD_PHASE

CAPABILITY_PHASE = "phase_56_3_journey_comparison_client_presentation_foundation"
PHASE_LABEL = CURRENT_BUILD_PHASE

PRESENTATION_COLLECTION = "journey_comparison_presentations"
OPTION_COLLECTION = "journey_comparison_option_projections"
SEGMENT_COLLECTION = "journey_comparison_segment_projections"
CONNECTION_COLLECTION = "journey_comparison_connection_projections"
FARE_COLLECTION = "journey_comparison_fare_brand_projections"
SERVICE_COLLECTION = "journey_comparison_service_suitability_projections"
DIMENSION_COLLECTION = "journey_comparison_dimensions"
RESULT_COLLECTION = "journey_comparison_results"
CONTENT_COLLECTION = "journey_presentation_content_blocks"
CONFIG_COLLECTION = "journey_comparison_presentation_configurations"
SNAPSHOT_COLLECTION = "journey_presentation_snapshots"
REVIEW_COLLECTION = "journey_presentation_reviews"
HANDOFF_COLLECTION = "journey_presentation_handoffs"

PRESENTATION_COLLECTIONS = [
    PRESENTATION_COLLECTION,
    OPTION_COLLECTION,
    SEGMENT_COLLECTION,
    CONNECTION_COLLECTION,
    FARE_COLLECTION,
    SERVICE_COLLECTION,
    DIMENSION_COLLECTION,
    RESULT_COLLECTION,
    CONTENT_COLLECTION,
    CONFIG_COLLECTION,
    SNAPSHOT_COLLECTION,
    REVIEW_COLLECTION,
    HANDOFF_COLLECTION,
]

PRESENTATION_STATUSES = ["draft", "generated", "review_required", "client_ready", "approved", "handed_off", "archived"]
AUDIENCE_TYPES = ["agent", "client", "passenger", "mixed"]
PRESENTATION_MODES = ["comparison", "client_preview", "internal_review", "document_preparation"]
COMPARISON_LAYOUTS = ["option_cards_with_matrix", "option_columns", "compact_matrix", "mobile_cards"]
REVIEW_STATUSES = ["draft", "in_review", "changes_requested", "approved", "rejected", "completed"]
HANDOFF_DESTINATIONS = ["offer_workspace", "document_workspace"]
UNKNOWN_STATES = [
    "confirmed", "supported", "conditionally_supported", "unsupported", "unavailable", "unknown", "not_assessed",
    "manual_review_required", "airline_confirmation_required", "evidence_required", "route_specific",
    "passenger_specific", "provider_specific", "interline_uncertain",
]
VALIDATION_CODES = [
    "missing_composition", "missing_journey", "missing_options", "missing_segments", "segment_source_missing",
    "schedule_unknown", "invalid_chronology", "connection_time_unknown", "minimum_connection_not_assessed",
    "airport_change_review_required", "terminal_change_review_required", "overnight_connection",
    "interline_review_required", "codeshare_review_required", "price_unknown", "currency_mismatch",
    "baggage_unknown", "change_conditions_unknown", "refund_conditions_unknown", "service_suitability_unknown",
    "airline_confirmation_required", "evidence_required", "restricted_content_removed", "review_required",
]

DEFAULT_DIMENSIONS = [
    ("total_price", "Total price", "Total price", "commercial", "currency", "lower"),
    ("price_per_passenger", "Price per passenger", "Per passenger", "commercial", "currency", "lower"),
    ("departure_convenience", "Departure convenience", "Departure", "schedule", "datetime", "informational"),
    ("arrival_convenience", "Arrival convenience", "Arrival", "schedule", "datetime", "informational"),
    ("total_elapsed_time", "Total elapsed time", "Total travel time", "schedule", "duration", "lower"),
    ("flight_time", "Scheduled flight time", "Flight time", "schedule", "duration", "lower"),
    ("connection_time", "Connection time", "Connections", "schedule", "duration", "lower"),
    ("stop_count", "Stop count", "Stops", "schedule", "number", "lower"),
    ("airport_changes", "Airport changes", "Airport changes", "operations", "number", "lower"),
    ("overnight_connections", "Overnight connections", "Overnight connections", "operations", "number", "lower"),
    ("baggage", "Baggage inclusion", "Baggage", "commercial", "text", "higher"),
    ("change_conditions", "Change conditions", "Changes", "commercial", "status", "higher"),
    ("refund_conditions", "Refund conditions", "Refunds", "commercial", "status", "higher"),
    ("seat_inclusion", "Seat inclusion", "Seats", "commercial", "status", "higher"),
    ("meal_inclusion", "Meal inclusion", "Meals", "commercial", "status", "higher"),
    ("priority_services", "Priority services", "Priority services", "commercial", "status", "higher"),
    ("lounge_access", "Lounge access", "Lounge", "commercial", "status", "higher"),
    ("operating_carrier_complexity", "Operating-carrier complexity", "Operating carriers", "operations", "number", "lower"),
    ("interline_complexity", "Interline complexity", "Interline", "operations", "status", "lower"),
    ("special_service_suitability", "Special-service suitability", "Assistance suitability", "services", "status", "higher"),
    ("evidence_confidence", "Evidence confidence", "Information confidence", "governance", "status", "higher"),
    ("unresolved_unknowns", "Unresolved operational unknowns", "Information to confirm", "governance", "number", "lower"),
    ("operational_risk", "Identified operational risk", "Operational review", "operations", "number", "lower"),
    ("manual_review_requirement", "Manual-review requirement", "Manual review", "operations", "status", "lower"),
]

CLIENT_RESTRICTED_FIELDS = {
    "internal_title", "internal_notes", "internal_summary", "internal_operational_text", "internal_connection_text",
    "internal_operational_summary", "internal_text", "source_provenance", "source_references", "source_hash",
    "internal_payload", "snapshot_payload", "calculation_trace", "evidence_refs", "knowledge_version_refs",
    "restricted_contacts", "source_urls", "source_locations", "supplier_cost", "margin", "internal_cost",
}


class JourneyComparisonPresentationError(ValueError):
    pass


class FinalizedJourneyPresentationSnapshotError(JourneyComparisonPresentationError):
    pass


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_none=True, exclude_unset=True)
    return {key: value for key, value in dict(payload or {}).items() if value is not None}


class JourneyComparisonClientPresentationService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "journey_comparison_client_presentation_enabled": True,
            "comparison_presentations_collection_enabled": True,
            "option_projection_enabled": True,
            "segment_projection_enabled": True,
            "connection_projection_enabled": True,
            "fare_brand_projection_enabled": True,
            "service_suitability_projection_enabled": True,
            "deterministic_journey_metrics_enabled": True,
            "deterministic_price_comparison_enabled": True,
            "deterministic_schedule_comparison_enabled": True,
            "baggage_comparison_enabled": True,
            "change_refund_comparison_enabled": True,
            "special_service_comparison_enabled": True,
            "unknown_state_preserved": True,
            "client_internal_content_separation_enabled": True,
            "client_safe_preview_enabled": True,
            "internal_preview_enabled": True,
            "explicit_preferred_option_selection_enabled": True,
            "automatic_preferred_option_selection_disabled": True,
            "immutable_presentation_snapshots_enabled": True,
            "finalized_snapshot_mutation_disabled": True,
            "explicit_review_workflow_enabled": True,
            "metadata_only_offer_handoff_enabled": True,
            "metadata_only_document_handoff_enabled": True,
            "automatic_offer_publication_disabled": True,
            "public_share_links_disabled": True,
            "external_messaging_disabled": True,
            "live_availability_disabled": True,
            "live_pricing_disabled": True,
            "provider_connectivity_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "scraping_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_production_seeding_disabled": True,
            "metadata_only": True,
        }

    def filters(self) -> dict[str, Any]:
        return {
            "statuses": PRESENTATION_STATUSES,
            "audience_types": AUDIENCE_TYPES,
            "presentation_modes": PRESENTATION_MODES,
            "comparison_layouts": COMPARISON_LAYOUTS,
            "review_statuses": REVIEW_STATUSES,
            "handoff_destinations": HANDOFF_DESTINATIONS,
            "unknown_states": UNKNOWN_STATES,
            "validation_codes": VALIDATION_CODES,
            "comparison_dimensions": [item[0] for item in DEFAULT_DIMENSIONS],
            "common_option_target": 3,
            "common_fare_brand_target_per_option": 3,
        }

    async def create_presentation(self, agency_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        composition_id = str(data.get("composition_id") or "")
        if not composition_id:
            raise JourneyComparisonPresentationError("A Phase 56.2 composition reference is required.")
        composition_detail = await self._composition_detail(agency_id, composition_id)
        composition = composition_detail["composition"]
        journey = composition_detail["journey"]
        if data.get("journey_id") and data["journey_id"] != journey["id"]:
            raise JourneyComparisonPresentationError("The Journey reference does not match the source composition.")
        selected_ids = data.get("selected_option_ids") or [
            item["id"] for item in composition_detail["options"] if not item.get("archived_at")
        ]
        valid_option_ids = {item["id"] for item in composition_detail["options"] if not item.get("archived_at")}
        if not set(selected_ids).issubset(valid_option_ids):
            raise JourneyComparisonPresentationError("Selected itinerary options must belong to the source composition and agency.")
        currency = str(data.get("currency_code") or self._composition_currency(composition_detail) or "EUR").upper()
        if len(currency) != 3 or not currency.isalpha():
            raise JourneyComparisonPresentationError("A three-letter presentation currency code is required.")
        values = {
            **data,
            "agency_id": agency_id,
            "composition_id": composition_id,
            "journey_id": journey["id"],
            "offer_id": data.get("offer_id") or composition.get("offer_workspace_id") or composition.get("offer_id"),
            "request_id": data.get("request_id") or composition.get("request_id"),
            "trip_id": data.get("trip_id") or composition.get("trip_id"),
            "title": data.get("title") or f"{composition.get('client_safe_title') or composition.get('title')} comparison",
            "client_title": data.get("client_title") or composition.get("client_safe_title") or composition.get("title"),
            "status": data.get("status") or "draft",
            "currency_code": currency,
            "selected_option_ids": selected_ids,
            "preferred_option_id": None,
            "created_by": self._actor(user),
            "updated_by": self._actor(user),
            "source_hash": self._hash({"composition": composition, "journey": journey, "selected_option_ids": selected_ids}),
        }
        self._choice(values["status"], PRESENTATION_STATUSES, "presentation status")
        self._choice(values.get("audience_type", "client"), AUDIENCE_TYPES, "audience type")
        stored = await self.db.collection(PRESENTATION_COLLECTION).insert_one(
            JourneyComparisonPresentation(**values).model_dump(mode="json")
        )
        await self._ensure_configuration(stored)
        await self._ensure_dimensions(stored)
        await self._audit("journey_comparison_presentation.created", stored, user)
        return {"phase": PHASE_LABEL, "presentation": stored, **self.safety_flags()}

    async def create_from_composition(self, agency_id: str, composition_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        created = await self.create_presentation(agency_id, {**payload_dict(payload), "composition_id": composition_id}, user)
        generated = await self.generate(agency_id, created["presentation"]["id"], user)
        return generated

    async def create_from_journey(self, agency_id: str, journey_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        journey = await self.db.collection("journey_representations").find_one({"id": journey_id, "agency_id": agency_id})
        if not journey:
            raise JourneyComparisonPresentationError("Canonical Journey was not found for this agency.")
        compositions = await JourneyOptionFareBrandCompositionService(self.db).list_compositions(agency_id, journey_id=journey_id)
        if not compositions:
            raise JourneyComparisonPresentationError("Create a Phase 56.2 Journey Option Composition before preparing client presentation.")
        return await self.create_from_composition(agency_id, compositions[0]["id"], payload, user)

    async def create_from_offer(self, agency_id: str, offer_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        await self._find_destination(agency_id, "offer_workspace", offer_id)
        service = JourneyOptionFareBrandCompositionService(self.db)
        compositions = await service.list_compositions(agency_id, offer_id=offer_id)
        if not compositions:
            compositions = await service.list_compositions(agency_id, offer_workspace_id=offer_id)
        if not compositions:
            raise JourneyComparisonPresentationError("Create a Phase 56.2 composition linked to this Offer Workspace before presentation.")
        return await self.create_from_composition(agency_id, compositions[0]["id"], {**payload_dict(payload), "offer_id": offer_id}, user)

    async def list_presentations(self, agency_id: str | None = None, **filters: Any) -> list[dict[str, Any]]:
        items = await self.db.collection(PRESENTATION_COLLECTION).find_many({"agency_id": agency_id} if agency_id else None)
        if not filters.get("include_archived"):
            items = [item for item in items if not item.get("archived_at")]
        for field in ["composition_id", "journey_id", "offer_id", "status", "audience_type"]:
            if filters.get(field):
                items = [item for item in items if item.get(field) == filters[field]]
        return sorted(items, key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)

    async def get_presentation(self, agency_id: str, presentation_id: str, *, client_safe: bool = False) -> dict[str, Any]:
        presentation = await self._require_presentation(agency_id, presentation_id)
        queries = {
            "options": OPTION_COLLECTION,
            "segments": SEGMENT_COLLECTION,
            "connections": CONNECTION_COLLECTION,
            "fare_brands": FARE_COLLECTION,
            "service_suitability": SERVICE_COLLECTION,
            "dimensions": DIMENSION_COLLECTION,
            "comparison_results": RESULT_COLLECTION,
            "content_blocks": CONTENT_COLLECTION,
            "snapshots": SNAPSHOT_COLLECTION,
            "reviews": REVIEW_COLLECTION,
            "handoffs": HANDOFF_COLLECTION,
        }
        values: dict[str, Any] = {}
        for key, collection in queries.items():
            rows = await self.db.collection(collection).find_many({"agency_id": agency_id, "presentation_id": presentation_id})
            if key in {"segments", "connections", "fare_brands", "service_suitability", "content_blocks"}:
                rows = [item for item in rows if not item.get("archived_at")]
            values[key] = rows
        values["options"] = sorted([item for item in values["options"] if not item.get("is_archived")], key=lambda item: int(item.get("display_order") or 0))
        for key in ["segments", "connections", "fare_brands", "dimensions", "content_blocks"]:
            values[key] = sorted(values[key], key=lambda item: int(item.get("display_order") or 0))
        values["comparison_results"] = sorted(values["comparison_results"], key=lambda item: str(item.get("generated_at") or ""), reverse=True)
        values["snapshots"] = sorted(values["snapshots"], key=lambda item: int(item.get("version_number") or 0), reverse=True)
        values["reviews"] = sorted(values["reviews"], key=lambda item: str(item.get("created_at") or ""), reverse=True)
        configuration = await self.db.collection(CONFIG_COLLECTION).find_one({"agency_id": agency_id, "presentation_id": presentation_id})
        payload = {
            "phase": PHASE_LABEL,
            "presentation": presentation,
            "configuration": configuration,
            **values,
            **self.safety_flags(),
        }
        return self._sanitize_client(payload) if client_safe else payload

    async def update_presentation(self, agency_id: str, presentation_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require_presentation(agency_id, presentation_id)
        data = payload_dict(payload)
        allowed = {
            "title", "subtitle", "status", "presentation_mode", "audience_type", "language_code", "currency_code",
            "timezone_display_mode", "comparison_layout", "internal_title", "client_title", "client_intro_text",
            "internal_notes", "selected_option_ids", "requires_review", "metadata",
        }
        updates = {key: value for key, value in data.items() if key in allowed}
        if "status" in updates:
            self._choice(updates["status"], PRESENTATION_STATUSES, "presentation status")
        if "audience_type" in updates:
            self._choice(updates["audience_type"], AUDIENCE_TYPES, "audience type")
        if "currency_code" in updates:
            currency = str(updates["currency_code"]).upper()
            if len(currency) != 3 or not currency.isalpha():
                raise JourneyComparisonPresentationError("A three-letter presentation currency code is required.")
            updates["currency_code"] = currency
        if "selected_option_ids" in updates:
            detail = await self._composition_detail(agency_id, existing["composition_id"])
            valid_ids = {item["id"] for item in detail["options"] if not item.get("archived_at")}
            if not set(updates["selected_option_ids"]).issubset(valid_ids):
                raise JourneyComparisonPresentationError("Selected options must belong to the source composition.")
        updates["updated_by"] = self._actor(user)
        validated = JourneyComparisonPresentation(**{**existing, **updates}).model_dump(mode="json")
        stored = await self.db.collection(PRESENTATION_COLLECTION).update_one({"id": presentation_id, "agency_id": agency_id}, validated)
        await self._audit("journey_comparison_presentation.updated", stored or existing, user)
        return {"phase": PHASE_LABEL, "presentation": stored or existing, **self.safety_flags()}

    async def archive_presentation(self, agency_id: str, presentation_id: str, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require_presentation(agency_id, presentation_id)
        stored = await self.db.collection(PRESENTATION_COLLECTION).update_one(
            {"id": presentation_id, "agency_id": agency_id},
            {"status": "archived", "archived_at": self._now(), "updated_by": self._actor(user)},
        )
        await self._audit("journey_comparison_presentation.archived", stored or existing, user)
        return {"phase": PHASE_LABEL, "presentation": stored or existing, "physical_deletion_performed": False, **self.safety_flags()}

    async def generate(self, agency_id: str, presentation_id: str, user: dict[str, Any] | None = None) -> dict[str, Any]:
        presentation = await self._require_presentation(agency_id, presentation_id)
        detail = await self._composition_detail(agency_id, presentation["composition_id"])
        selected = set(presentation.get("selected_option_ids") or [])
        source_options = [
            item for item in detail["options"]
            if not item.get("archived_at") and (not selected or item["id"] in selected)
        ]
        if not source_options:
            raise JourneyComparisonPresentationError("At least one active source itinerary option is required.")
        assignment_rows = [item for item in detail["segment_assignments"] if item.get("included") and not item.get("archived_at")]
        resolved_segments = {
            item["assignment"]["id"]: item.get("segment")
            for item in detail["segments"]
            if item.get("assignment")
        }
        metric_by_id = {item["id"]: item for item in detail["metric_snapshots"]}
        prices_by_fare = {item["fare_choice_id"]: item for item in detail["price_breakdowns"]}
        active_option_ids: list[str] = []
        active_segment_ids: list[str] = []
        active_connection_ids: list[str] = []
        active_fare_ids: list[str] = []
        active_service_ids: list[str] = []

        for option_order, source_option in enumerate(sorted(source_options, key=lambda item: int(item.get("display_order") or 0)), start=1):
            assignments = sorted(
                [item for item in assignment_rows if item.get("option_id") == source_option["id"]],
                key=lambda item: int(item.get("display_order") or 0),
            )
            segments = [(assignment, resolved_segments.get(assignment["id"])) for assignment in assignments]
            option_projection = await self._upsert_option_projection(
                presentation,
                source_option,
                metric_by_id.get(source_option.get("metric_snapshot_id")),
                segments,
                option_order,
            )
            active_option_ids.append(option_projection["id"])
            projected_segments: list[dict[str, Any]] = []
            for segment_order, (assignment, source_segment) in enumerate(segments, start=1):
                projection = await self._upsert_segment_projection(
                    presentation, option_projection, assignment, source_segment, segment_order
                )
                projected_segments.append(projection)
                active_segment_ids.append(projection["id"])
            projected_connections = []
            for connection_order in range(max(0, len(projected_segments) - 1)):
                projection = await self._upsert_connection_projection(
                    presentation,
                    option_projection,
                    projected_segments[connection_order],
                    projected_segments[connection_order + 1],
                    connection_order + 1,
                )
                projected_connections.append(projection)
                active_connection_ids.append(projection["id"])

            source_fares = sorted(
                [item for item in detail["fare_brand_choices"] if item.get("option_id") == source_option["id"] and not item.get("archived_at")],
                key=lambda item: int(item.get("display_order") or 0),
            )
            for fare_order, source_fare in enumerate(source_fares, start=1):
                projection = await self._upsert_fare_projection(
                    presentation, option_projection, source_fare, prices_by_fare.get(source_fare["id"]), fare_order
                )
                active_fare_ids.append(projection["id"])

            source_assessments = [item for item in detail["service_assessments"] if item.get("option_id") == source_option["id"]]
            if not source_assessments:
                canonical_option_id = (source_option.get("metadata") or {}).get("canonical_itinerary_option_id")
                source_assessments = await self._journey_service_fallback(agency_id, presentation["journey_id"], canonical_option_id)
            projected_services = []
            for assessment in source_assessments:
                projection = await self._upsert_service_projection(presentation, option_projection, assessment)
                projected_services.append(projection)
                active_service_ids.append(projection["id"])
            await self._refresh_option_projection(option_projection, projected_segments, projected_connections, projected_services)
            await self._ensure_option_content_block(presentation, option_projection)

        await self._archive_stale(OPTION_COLLECTION, agency_id, presentation_id, active_option_ids, option_mode=True)
        await self._archive_stale(SEGMENT_COLLECTION, agency_id, presentation_id, active_segment_ids)
        await self._archive_stale(CONNECTION_COLLECTION, agency_id, presentation_id, active_connection_ids)
        await self._archive_stale(FARE_COLLECTION, agency_id, presentation_id, active_fare_ids)
        await self._archive_stale(SERVICE_COLLECTION, agency_id, presentation_id, active_service_ids)
        await self._ensure_dimensions(presentation)
        comparison = await self.compare(agency_id, presentation_id)
        source_hash = self._hash({
            "composition_source_hash": detail["composition"].get("source_hash"),
            "options": active_option_ids,
            "segments": active_segment_ids,
            "fares": active_fare_ids,
            "services": active_service_ids,
            "comparison": comparison["comparison_result"].get("source_hash"),
        })
        manual_review = comparison["comparison_result"].get("manual_review_required", True)
        stored = await self.db.collection(PRESENTATION_COLLECTION).update_one(
            {"id": presentation_id, "agency_id": agency_id},
            {
                "status": "review_required" if manual_review else "generated",
                "requires_review": manual_review,
                "source_hash": source_hash,
                "updated_by": self._actor(user),
            },
        )
        await self._audit("journey_comparison_presentation.generated", stored or presentation, user, {"source_hash": source_hash})
        return await self.get_presentation(agency_id, presentation_id)

    async def recalculate(self, agency_id: str, presentation_id: str, user: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.generate(agency_id, presentation_id, user)

    async def compare(self, agency_id: str, presentation_id: str) -> dict[str, Any]:
        presentation = await self._require_presentation(agency_id, presentation_id)
        options = await self._active_rows(OPTION_COLLECTION, agency_id, presentation_id)
        fares = await self._active_rows(FARE_COLLECTION, agency_id, presentation_id)
        services = await self._active_rows(SERVICE_COLLECTION, agency_id, presentation_id)
        if not options:
            raise JourneyComparisonPresentationError("Generate option projections before comparison.")
        presentation_currency = presentation.get("currency_code")
        known_fares = [item for item in fares if item.get("grand_total") is not None and item.get("currency_code") == presentation_currency]
        global_lowest = min((float(item["grand_total"]) for item in known_fares), default=None)
        if global_lowest is not None:
            for fare in known_fares:
                difference = round(float(fare["grand_total"]) - global_lowest, 2)
                await self.db.collection(FARE_COLLECTION).update_one({"id": fare["id"], "agency_id": agency_id}, {"price_difference_from_lowest": difference})
                fare["price_difference_from_lowest"] = difference

        option_rows = []
        for option in options:
            option_fares = [item for item in fares if item.get("option_projection_id") == option["id"]]
            comparable = [item for item in option_fares if item.get("grand_total") is not None and item.get("currency_code") == presentation_currency]
            lowest_fare = min(comparable, key=lambda item: float(item["grand_total"])) if comparable else None
            option_services = [item for item in services if item.get("option_projection_id") == option["id"]]
            supported = len([item for item in option_services if item.get("suitability_status") in {"supported", "confirmed"}])
            blocked = len([item for item in option_services if item.get("blocking_indicator")])
            service_review = len([item for item in option_services if item.get("manual_review_required")])
            baggage_scores = [self._baggage_score(item.get("baggage_summary")) for item in option_fares]
            flexibility_scores = [self._status_score(item.get("change_summary")) + self._status_score(item.get("refund_summary")) for item in option_fares]
            risk_score = int(option.get("blocking_warning_count") or 0) * 100 + int(option.get("review_required_count") or 0) * 10 + int(option.get("unknown_value_count") or 0)
            option_rows.append({
                "option_id": option["id"],
                "composition_option_id": option.get("composition_option_id"),
                "label": option.get("option_label"),
                "total_price": lowest_fare.get("grand_total") if lowest_fare else None,
                "price_per_passenger": lowest_fare.get("price_per_passenger") if lowest_fare else None,
                "currency_code": lowest_fare.get("currency_code") if lowest_fare else None,
                "departure_at": option.get("departure_at"),
                "arrival_at": option.get("arrival_at"),
                "total_elapsed_minutes": option.get("total_elapsed_minutes"),
                "total_flight_minutes": option.get("total_flight_minutes"),
                "total_connection_minutes": option.get("total_connection_minutes"),
                "stop_count": option.get("stop_count"),
                "airport_change_count": option.get("airport_change_count"),
                "overnight_connection_count": option.get("overnight_connection_count"),
                "operating_carrier_count": len(option.get("operating_carriers") or []),
                "interline_indicator": option.get("interline_indicator"),
                "baggage_score": max(baggage_scores, default=None),
                "flexibility_score": max(flexibility_scores, default=None),
                "special_service_score": supported * 10 - blocked * 100 - service_review * 5 if option_services else None,
                "operational_risk_score": risk_score,
                "unknown_value_count": option.get("unknown_value_count", 0),
                "manual_review_required": bool(option.get("review_required_count") or blocked or service_review),
            })

        leaders = {
            "fastest_option_id": self._leader(option_rows, "total_elapsed_minutes", lower=True),
            "shortest_flight_time_option_id": self._leader(option_rows, "total_flight_minutes", lower=True),
            "lowest_price_option_id": self._leader(option_rows, "total_price", lower=True),
            "fewest_stops_option_id": self._leader(option_rows, "stop_count", lower=True),
            "best_baggage_option_id": self._leader(option_rows, "baggage_score", lower=False),
            "best_flexibility_option_id": self._leader(option_rows, "flexibility_score", lower=False),
            "best_special_service_option_id": self._leader(option_rows, "special_service_score", lower=False),
            "lowest_operational_risk_option_id": self._leader(option_rows, "operational_risk_score", lower=True),
        }
        dimension_results = self._dimension_results(option_rows, leaders)
        ties = [item for item in dimension_results if len(item.get("leader_option_ids") or []) > 1]
        unresolved = [
            {"option_id": item["option_id"], "count": item.get("unknown_value_count", 0)}
            for item in option_rows if item.get("unknown_value_count")
        ]
        fare_results = [{
            "fare_projection_id": item["id"],
            "option_projection_id": item["option_projection_id"],
            "brand_name": item.get("client_brand_name"),
            "currency_code": item.get("currency_code"),
            "grand_total": item.get("grand_total"),
            "price_difference_from_lowest": item.get("price_difference_from_lowest"),
            "baggage_summary": item.get("baggage_summary") or "unknown",
            "change_summary": item.get("change_summary") or "unknown",
            "refund_summary": item.get("refund_summary") or "unknown",
        } for item in fares]
        values = {
            "agency_id": agency_id,
            "presentation_id": presentation_id,
            "preferred_option_id": presentation.get("preferred_option_id"),
            **leaders,
            "dimension_results": dimension_results,
            "option_scores": option_rows,
            "fare_brand_results": fare_results,
            "tie_results": ties,
            "warning_summary": {
                "blocking": sum(int(item.get("blocking_warning_count") or 0) for item in options),
                "review_required": sum(int(item.get("review_required_count") or 0) for item in options),
                "unknown": sum(int(item.get("unknown_value_count") or 0) for item in options),
            },
            "unresolved_unknowns": unresolved,
            "manual_review_required": any(item.get("manual_review_required") for item in option_rows),
        }
        values["source_hash"] = self._hash(values)
        stored = await self.db.collection(RESULT_COLLECTION).insert_one(JourneyComparisonResult(**values).model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "comparison_result": stored,
            "automatic_preferred_option_selected": False,
            **self.safety_flags(),
        }

    async def select_preferred_option(self, agency_id: str, presentation_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        presentation = await self._require_presentation(agency_id, presentation_id)
        data = payload_dict(payload)
        option_id = str(data.get("option_id") or "")
        option = await self.db.collection(OPTION_COLLECTION).find_one({"agency_id": agency_id, "presentation_id": presentation_id, "id": option_id})
        if not option:
            option = await self.db.collection(OPTION_COLLECTION).find_one({"agency_id": agency_id, "presentation_id": presentation_id, "composition_option_id": option_id})
        if not option or option.get("is_archived"):
            raise JourneyComparisonPresentationError("Preferred option must be an active option projection in this presentation.")
        reason = str(data.get("reason") or "").strip()
        if not reason:
            raise JourneyComparisonPresentationError("An agent reason is required for preferred-option selection.")
        for row in await self.db.collection(OPTION_COLLECTION).find_many({"agency_id": agency_id, "presentation_id": presentation_id}):
            await self.db.collection(OPTION_COLLECTION).update_one({"id": row["id"], "agency_id": agency_id}, {"is_preferred": row["id"] == option["id"]})
        stored = await self.db.collection(PRESENTATION_COLLECTION).update_one(
            {"id": presentation_id, "agency_id": agency_id},
            {
                "preferred_option_id": option["id"],
                "preferred_selected_by": self._actor(user),
                "preferred_selected_at": self._now(),
                "preferred_selection_reason": reason,
                "updated_by": self._actor(user),
            },
        )
        await self._audit("journey_comparison_presentation.preferred_option_selected", stored or presentation, user, {"option_id": option["id"], "reason": reason})
        return {"phase": PHASE_LABEL, "presentation": stored or presentation, "option": option, "automatic_selection": False, **self.safety_flags()}

    async def update_configuration(self, agency_id: str, presentation_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        presentation = await self._require_presentation(agency_id, presentation_id)
        existing = await self._ensure_configuration(presentation)
        immutable = {"id", "agency_id", "presentation_id", "journey_id", "created_at"}
        updates = {key: value for key, value in payload_dict(payload).items() if key not in immutable}
        model = JourneyPresentationConfiguration(**{**existing, **updates}).model_dump(mode="json")
        stored = await self.db.collection(CONFIG_COLLECTION).update_one({"id": existing["id"], "agency_id": agency_id}, model)
        await self._audit("journey_comparison_presentation.configuration_updated", presentation, user)
        return {"phase": PHASE_LABEL, "configuration": stored or existing, **self.safety_flags()}

    async def create_content_block(self, agency_id: str, presentation_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        await self._require_presentation(agency_id, presentation_id)
        data = payload_dict(payload)
        if data.get("option_projection_id"):
            await self._require_projection(OPTION_COLLECTION, agency_id, presentation_id, data["option_projection_id"], "Option projection")
        if data.get("fare_brand_projection_id"):
            await self._require_projection(FARE_COLLECTION, agency_id, presentation_id, data["fare_brand_projection_id"], "Fare-brand projection")
        existing = await self.db.collection(CONTENT_COLLECTION).find_many({"agency_id": agency_id, "presentation_id": presentation_id})
        values = {
            **data,
            "agency_id": agency_id,
            "presentation_id": presentation_id,
            "block_type": data.get("block_type") or "custom",
            "title": data.get("title") or "Presentation note",
            "client_text": data.get("client_text") or "Information to be confirmed.",
            "display_order": int(data.get("display_order") or len(existing) + 1),
        }
        stored = await self.db.collection(CONTENT_COLLECTION).insert_one(JourneyPresentationContentBlock(**values).model_dump(mode="json"))
        await self._audit("journey_comparison_presentation.content_block_created", stored, user)
        return {"phase": PHASE_LABEL, "content_block": stored, **self.safety_flags()}

    async def update_content_block(self, agency_id: str, presentation_id: str, block_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require_projection(CONTENT_COLLECTION, agency_id, presentation_id, block_id, "Content block")
        immutable = {"id", "agency_id", "presentation_id", "created_at"}
        updates = {key: value for key, value in payload_dict(payload).items() if key not in immutable}
        model = JourneyPresentationContentBlock(**{**existing, **updates}).model_dump(mode="json")
        stored = await self.db.collection(CONTENT_COLLECTION).update_one({"id": block_id, "agency_id": agency_id}, model)
        await self._audit("journey_comparison_presentation.content_block_updated", stored or existing, user)
        return {"phase": PHASE_LABEL, "content_block": stored or existing, **self.safety_flags()}

    async def archive_content_block(self, agency_id: str, presentation_id: str, block_id: str, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require_projection(CONTENT_COLLECTION, agency_id, presentation_id, block_id, "Content block")
        stored = await self.db.collection(CONTENT_COLLECTION).update_one({"id": block_id, "agency_id": agency_id}, {"archived_at": self._now()})
        await self._audit("journey_comparison_presentation.content_block_archived", stored or existing, user)
        return {"phase": PHASE_LABEL, "content_block": stored or existing, "physical_deletion_performed": False, **self.safety_flags()}

    async def preview_client(self, agency_id: str, presentation_id: str) -> dict[str, Any]:
        detail = await self.get_presentation(agency_id, presentation_id)
        presentation = detail["presentation"]
        content = [item for item in detail["content_blocks"] if item.get("visibility_scope") != "internal"]
        payload = {
            "presentation": {
                "id": presentation["id"],
                "title": presentation.get("client_title") or presentation.get("title"),
                "subtitle": presentation.get("subtitle"),
                "introduction": presentation.get("client_intro_text"),
                "language_code": presentation.get("language_code"),
                "currency_code": presentation.get("currency_code"),
                "timezone_display_mode": presentation.get("timezone_display_mode"),
                "preferred_option_id": presentation.get("preferred_option_id") if presentation.get("preferred_selected_by") else None,
                "preferred_selection_reason": presentation.get("preferred_selection_reason") if presentation.get("preferred_selected_by") else None,
            },
            "configuration": self._sanitize_client(detail.get("configuration") or {}),
            "options": [self._sanitize_client(item) for item in detail["options"]],
            "segments": [self._sanitize_client(item) for item in detail["segments"]],
            "connections": [self._sanitize_client(item) for item in detail["connections"]],
            "fare_brands": [self._sanitize_client(item) for item in detail["fare_brands"]],
            "service_suitability": [self._sanitize_client(item) for item in detail["service_suitability"]],
            "comparison": self._client_comparison(detail["comparison_results"][0]) if detail["comparison_results"] else None,
            "content_blocks": [self._sanitize_client(item) for item in content],
            "public_share_link": None,
            "published": False,
        }
        return {"phase": PHASE_LABEL, "client_safe_payload": payload, "restricted_content_removed": True, **self.safety_flags()}

    async def preview_internal(self, agency_id: str, presentation_id: str) -> dict[str, Any]:
        detail = await self.get_presentation(agency_id, presentation_id)
        return {"phase": PHASE_LABEL, "internal_payload": detail, "agency_authorized_internal_view": True, **self.safety_flags()}

    async def list_snapshots(self, agency_id: str, presentation_id: str) -> list[dict[str, Any]]:
        await self._require_presentation(agency_id, presentation_id)
        rows = await self.db.collection(SNAPSHOT_COLLECTION).find_many({"agency_id": agency_id, "presentation_id": presentation_id})
        return sorted(rows, key=lambda item: int(item.get("version_number") or 0), reverse=True)

    async def create_snapshot(self, agency_id: str, presentation_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        presentation = await self._require_presentation(agency_id, presentation_id)
        snapshots = await self.list_snapshots(agency_id, presentation_id)
        client = await self.preview_client(agency_id, presentation_id)
        internal = await self.preview_internal(agency_id, presentation_id)
        internal_payload = dict(internal["internal_payload"])
        internal_payload.pop("snapshots", None)
        internal_payload.pop("handoffs", None)
        source_references = [
            {"type": "journey", "id": presentation["journey_id"]},
            {"type": "composition", "id": presentation["composition_id"]},
        ]
        if presentation.get("offer_id"):
            source_references.append({"type": "offer_workspace", "id": presentation["offer_id"]})
        source_hash = self._hash({"client": client["client_safe_payload"], "internal": internal_payload, "sources": source_references})
        data = payload_dict(payload)
        values = {
            "agency_id": agency_id,
            "presentation_id": presentation_id,
            "version_number": max([int(item.get("version_number") or 0) for item in snapshots], default=0) + 1,
            "snapshot_status": "draft",
            "snapshot_payload": {"presentation_id": presentation_id, "source_hash": source_hash},
            "client_safe_payload": client["client_safe_payload"],
            "internal_payload": internal_payload,
            "source_hash": source_hash,
            "source_references": source_references,
            "created_by": self._actor(user),
        }
        stored = await self.db.collection(SNAPSHOT_COLLECTION).insert_one(JourneyPresentationSnapshot(**values).model_dump(mode="json"))
        if data.get("finalize"):
            stored = (await self.finalize_snapshot(agency_id, presentation_id, stored["id"], user))["snapshot"]
        await self._audit("journey_comparison_presentation.snapshot_created", stored, user)
        return {"phase": PHASE_LABEL, "snapshot": stored, **self.safety_flags()}

    async def finalize_snapshot(self, agency_id: str, presentation_id: str, snapshot_id: str, user: dict[str, Any]) -> dict[str, Any]:
        snapshot = await self._require_snapshot(agency_id, presentation_id, snapshot_id)
        if snapshot.get("finalized"):
            return {"phase": PHASE_LABEL, "snapshot": snapshot, "idempotent": True, **self.safety_flags()}
        stored = await self.db.collection(SNAPSHOT_COLLECTION).update_one(
            {"id": snapshot_id, "agency_id": agency_id},
            {"snapshot_status": "finalized", "finalized": True, "finalized_by": self._actor(user), "finalized_at": self._now()},
        )
        await self.db.collection(PRESENTATION_COLLECTION).update_one({"id": presentation_id, "agency_id": agency_id}, {"status": "client_ready", "updated_by": self._actor(user)})
        await self._audit("journey_comparison_presentation.snapshot_finalized", stored or snapshot, user)
        return {"phase": PHASE_LABEL, "snapshot": stored or snapshot, **self.safety_flags()}

    async def update_snapshot(self, agency_id: str, presentation_id: str, snapshot_id: str, payload: Any) -> dict[str, Any]:
        snapshot = await self._require_snapshot(agency_id, presentation_id, snapshot_id)
        if snapshot.get("finalized"):
            raise FinalizedJourneyPresentationSnapshotError("Finalized presentation snapshots are immutable.")
        updates = {key: value for key, value in payload_dict(payload).items() if key not in {"id", "agency_id", "presentation_id", "created_at"}}
        stored = await self.db.collection(SNAPSHOT_COLLECTION).update_one({"id": snapshot_id, "agency_id": agency_id}, updates)
        return {"phase": PHASE_LABEL, "snapshot": stored or snapshot, **self.safety_flags()}

    async def list_reviews(self, agency_id: str, presentation_id: str) -> list[dict[str, Any]]:
        await self._require_presentation(agency_id, presentation_id)
        rows = await self.db.collection(REVIEW_COLLECTION).find_many({"agency_id": agency_id, "presentation_id": presentation_id})
        return sorted(rows, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def create_review(self, agency_id: str, presentation_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        await self._require_presentation(agency_id, presentation_id)
        data = payload_dict(payload)
        if data.get("snapshot_id"):
            await self._require_snapshot(agency_id, presentation_id, data["snapshot_id"])
        status = data.get("review_status") or "in_review"
        self._choice(status, REVIEW_STATUSES, "review status")
        values = {**data, "agency_id": agency_id, "presentation_id": presentation_id, "review_status": status, "reviewer_id": data.get("reviewer_id") or self._actor(user)}
        if status in {"approved", "rejected", "completed"}:
            values["completed_at"] = self._now()
        stored = await self.db.collection(REVIEW_COLLECTION).insert_one(JourneyPresentationReview(**values).model_dump(mode="json"))
        if status == "approved":
            await self.db.collection(PRESENTATION_COLLECTION).update_one(
                {"id": presentation_id, "agency_id": agency_id},
                {"status": "approved", "requires_review": False, "updated_by": self._actor(user)},
            )
        await self._audit("journey_comparison_presentation.review_created", stored, user)
        return {"phase": PHASE_LABEL, "review": stored, **self.safety_flags()}

    async def update_review(self, agency_id: str, presentation_id: str, review_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require_projection(REVIEW_COLLECTION, agency_id, presentation_id, review_id, "Presentation review")
        data = payload_dict(payload)
        status = data.get("review_status", existing.get("review_status"))
        self._choice(status, REVIEW_STATUSES, "review status")
        updates = {key: value for key, value in data.items() if key not in {"id", "agency_id", "presentation_id", "created_at"}}
        updates["review_status"] = status
        if status in {"approved", "rejected", "completed"}:
            updates["completed_at"] = self._now()
        validated = JourneyPresentationReview(**{**existing, **updates}).model_dump(mode="json")
        stored = await self.db.collection(REVIEW_COLLECTION).update_one({"id": review_id, "agency_id": agency_id}, validated)
        if status == "approved":
            await self.db.collection(PRESENTATION_COLLECTION).update_one({"id": presentation_id, "agency_id": agency_id}, {"status": "approved", "requires_review": False, "updated_by": self._actor(user)})
        await self._audit("journey_comparison_presentation.review_updated", stored or existing, user)
        return {"phase": PHASE_LABEL, "review": stored or existing, **self.safety_flags()}

    async def preview_handoff(self, agency_id: str, presentation_id: str, payload: Any) -> dict[str, Any]:
        presentation = await self._require_presentation(agency_id, presentation_id)
        data = payload_dict(payload)
        destination_type = data.get("destination_type") or "offer_workspace"
        self._choice(destination_type, HANDOFF_DESTINATIONS, "handoff destination")
        snapshot = await self._select_snapshot(agency_id, presentation_id, data.get("snapshot_id"))
        destination_id = data.get("destination_id") or (presentation.get("offer_id") if destination_type == "offer_workspace" else None)
        if destination_id:
            await self._find_destination(agency_id, destination_type, destination_id)
        projected_options = await self._active_rows(OPTION_COLLECTION, agency_id, presentation_id)
        preview = {
            "presentation_id": presentation_id,
            "snapshot_id": snapshot["id"],
            "destination_type": destination_type,
            "destination_id": destination_id,
            "client_safe_payload": snapshot.get("client_safe_payload") or {},
            "agency_branding_references": ["agency_settings"],
            "language_code": presentation.get("language_code"),
            "currency_code": presentation.get("currency_code"),
            "document_type_suggestion": "itinerary_comparison" if destination_type == "document_workspace" else None,
            "source_references": snapshot.get("source_references") or [],
            "selected_option_projection_ids": [item["id"] for item in projected_options],
            "preferred_option_id": presentation.get("preferred_option_id"),
            "explicit_agent_decision": bool(presentation.get("preferred_selected_by")),
            "payload_hash": snapshot.get("source_hash"),
            "prohibited_actions": ["publish", "send", "public_share", "accept", "book", "ticket", "issue_emd", "provider_call", "render_pdf"],
        }
        return {"phase": PHASE_LABEL, "preview": preview, "can_apply": True, "automatic_action_performed": False, **self.safety_flags()}

    async def apply_handoff(self, agency_id: str, presentation_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        preview = await self.preview_handoff(agency_id, presentation_id, payload)
        data = preview["preview"]
        existing = await self.db.collection(HANDOFF_COLLECTION).find_one({
            "agency_id": agency_id,
            "presentation_id": presentation_id,
            "snapshot_id": data["snapshot_id"],
            "destination_type": data["destination_type"],
            "destination_id": data.get("destination_id"),
            "handoff_status": "applied",
        })
        if existing:
            return {"phase": PHASE_LABEL, "handoff": existing, "created": False, "idempotent": True, "destination_mutated": False, **self.safety_flags()}
        values = {
            "agency_id": agency_id,
            "presentation_id": presentation_id,
            "snapshot_id": data["snapshot_id"],
            "destination_type": data["destination_type"],
            "destination_id": data.get("destination_id"),
            "handoff_status": "applied",
            "payload_hash": data["payload_hash"],
            "preview_payload": data,
            "source_references": data.get("source_references") or [],
            "created_by": self._actor(user),
            "applied_at": self._now(),
        }
        stored = await self.db.collection(HANDOFF_COLLECTION).insert_one(JourneyPresentationHandoff(**values).model_dump(mode="json"))
        await self.db.collection(PRESENTATION_COLLECTION).update_one({"id": presentation_id, "agency_id": agency_id}, {"status": "handed_off", "updated_by": self._actor(user)})
        await self._audit("journey_comparison_presentation.handoff_applied", stored, user)
        return {
            "phase": PHASE_LABEL,
            "handoff": stored,
            "created": True,
            "destination_mutated": False,
            "offer_published": False,
            "document_rendered": False,
            "message_sent": False,
            "provider_execution_performed": False,
            **self.safety_flags(),
        }

    async def summarize_readiness(self, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        presentations = await self.db.collection(PRESENTATION_COLLECTION).find_many(filters)
        options = await self.db.collection(OPTION_COLLECTION).find_many(filters)
        segments = await self.db.collection(SEGMENT_COLLECTION).find_many(filters)
        connections = await self.db.collection(CONNECTION_COLLECTION).find_many(filters)
        fares = await self.db.collection(FARE_COLLECTION).find_many(filters)
        services = await self.db.collection(SERVICE_COLLECTION).find_many(filters)
        results = await self.db.collection(RESULT_COLLECTION).find_many(filters)
        blocks = await self.db.collection(CONTENT_COLLECTION).find_many(filters)
        snapshots = await self.db.collection(SNAPSHOT_COLLECTION).find_many(filters)
        reviews = await self.db.collection(REVIEW_COLLECTION).find_many(filters)
        handoffs = await self.db.collection(HANDOFF_COLLECTION).find_many(filters)
        status_counts = {status: len([item for item in presentations if item.get("status") == status]) for status in PRESENTATION_STATUSES}
        audience_counts = {audience: len([item for item in presentations if item.get("audience_type") == audience]) for audience in AUDIENCE_TYPES}
        agency_counts: dict[str, int] = {}
        for item in presentations:
            key = item.get("agency_id") or "unknown"
            agency_counts[key] = agency_counts.get(key, 0) + 1
        return {
            "presentation_count": len(presentations),
            "active_presentation_count": len([item for item in presentations if not item.get("archived_at")]),
            "review_required_presentation_count": len([item for item in presentations if item.get("requires_review")]),
            "option_projection_count": len([item for item in options if not item.get("is_archived")]),
            "segment_projection_count": len([item for item in segments if not item.get("archived_at")]),
            "connection_projection_count": len([item for item in connections if not item.get("archived_at")]),
            "fare_brand_projection_count": len([item for item in fares if not item.get("archived_at")]),
            "service_suitability_projection_count": len([item for item in services if not item.get("archived_at")]),
            "comparison_result_count": len(results),
            "preferred_option_selection_count": len([item for item in presentations if item.get("preferred_selected_by")]),
            "content_block_count": len([item for item in blocks if not item.get("archived_at")]),
            "snapshot_count": len(snapshots),
            "finalized_snapshot_count": len([item for item in snapshots if item.get("finalized")]),
            "review_count": len(reviews),
            "approved_review_count": len([item for item in reviews if item.get("review_status") == "approved"]),
            "handoff_count": len(handoffs),
            "blocking_warning_count": sum(int(item.get("blocking_warning_count") or 0) for item in options),
            "manual_review_count": len([item for item in services if item.get("manual_review_required")]) + len([item for item in connections if item.get("manual_review_required")]),
            "unknown_value_count": sum(int(item.get("unknown_value_count") or 0) for item in options),
            "status_counts": status_counts,
            "audience_type_counts": audience_counts,
            "agency_counts": agency_counts,
        }

    async def dashboard(self, agency_id: str | None = None) -> dict[str, Any]:
        items = await self.list_presentations(agency_id, include_archived=True)
        return {
            "phase": PHASE_LABEL,
            "summary": await self.summarize_readiness(agency_id),
            "items": [self._platform_summary(item) for item in items[:20]],
            "filters": self.filters(),
            "platform_diagnostics_read_only": agency_id is None,
            "diagnostic": "Phase 56.3 converts existing canonical Journey and composition data into deterministic, client-safe itinerary and fare-brand comparisons with explicit operational suitability, unknown states, agent-controlled preference, immutable snapshots, and reviewable handoffs. It does not retrieve live fares or availability, publish offers, create public share links, send messages, or execute provider operations.",
            **self.safety_flags(),
        }

    async def platform_detail(self, presentation_id: str) -> dict[str, Any]:
        presentation = await self.db.collection(PRESENTATION_COLLECTION).find_one({"id": presentation_id})
        if not presentation:
            raise JourneyComparisonPresentationError("Journey comparison presentation was not found.")
        agency_id = str(presentation["agency_id"])
        summary = {
            "presentation": self._platform_summary(presentation),
            "option_count": await self.db.collection(OPTION_COLLECTION).count({"agency_id": agency_id, "presentation_id": presentation_id}),
            "segment_count": await self.db.collection(SEGMENT_COLLECTION).count({"agency_id": agency_id, "presentation_id": presentation_id}),
            "fare_brand_count": await self.db.collection(FARE_COLLECTION).count({"agency_id": agency_id, "presentation_id": presentation_id}),
            "service_suitability_count": await self.db.collection(SERVICE_COLLECTION).count({"agency_id": agency_id, "presentation_id": presentation_id}),
            "snapshots": [self._snapshot_summary(item) for item in await self.list_snapshots(agency_id, presentation_id)],
        }
        return {"phase": PHASE_LABEL, **summary, "read_only": True, **self.safety_flags()}

    async def _upsert_option_projection(self, presentation: dict[str, Any], source_option: dict[str, Any], metric: dict[str, Any] | None, segments: list[tuple[dict[str, Any], dict[str, Any] | None]], order: int) -> dict[str, Any]:
        source_segments = [segment for _, segment in segments if segment]
        first = source_segments[0] if source_segments else {}
        last = source_segments[-1] if source_segments else {}
        marketing = self._tokens([self._field(item, "marketing_carrier_code", "marketing_carrier") for item in source_segments])
        operating = self._tokens([self._field(item, "operating_carrier_code", "operating_carrier") for item in source_segments])
        warnings = self._tokens([*(source_option.get("warning_codes") or []), *((metric or {}).get("warning_codes") or [])])
        unknown_count = sum(1 for value in [
            self._field(first, "departure_local", "departure_utc"), self._field(last, "arrival_local", "arrival_utc"),
            (metric or {}).get("total_elapsed_minutes"), source_option.get("carrier_summary"),
        ] if value in {None, ""})
        values = {
            "agency_id": presentation["agency_id"],
            "presentation_id": presentation["id"],
            "composition_option_id": source_option["id"],
            "journey_option_id": (source_option.get("metadata") or {}).get("canonical_itinerary_option_id"),
            "option_number": order,
            "option_label": source_option.get("client_safe_label") or source_option.get("option_code") or f"Option {order}",
            "carrier_summary": source_option.get("carrier_summary") or ", ".join(marketing or operating) or "Carrier to confirm",
            "marketing_carriers": marketing or (metric or {}).get("marketing_carriers") or [],
            "operating_carriers": operating or (metric or {}).get("operating_carriers") or [],
            "validating_carrier": (metric or {}).get("validating_carrier"),
            "origin": self._field(first, "origin_airport_code", "departure_airport_code"),
            "destination": self._field(last, "destination_airport_code", "arrival_airport_code"),
            "departure_at": self._field(first, "departure_local", "departure_utc"),
            "arrival_at": self._field(last, "arrival_local", "arrival_utc"),
            "total_elapsed_minutes": (metric or {}).get("total_elapsed_minutes"),
            "total_flight_minutes": (metric or {}).get("scheduled_flight_minutes"),
            "total_connection_minutes": (metric or {}).get("total_connection_minutes"),
            "stop_count": int((metric or {}).get("stop_count") or max(0, len(source_segments) - 1)),
            "segment_count": len(source_segments),
            "connection_count": max(0, len(source_segments) - 1),
            "shortest_connection_minutes": (metric or {}).get("shortest_connection_minutes"),
            "longest_connection_minutes": (metric or {}).get("longest_connection_minutes"),
            "overnight_connection_count": 1 if (metric or {}).get("overnight_connection_indicator") else 0,
            "airport_change_count": 1 if (metric or {}).get("airport_change_indicator") else 0,
            "terminal_change_count": 1 if (metric or {}).get("terminal_change_indicator") else 0,
            "interline_indicator": bool((metric or {}).get("interline_indicator")),
            "codeshare_indicator": bool((metric or {}).get("codeshare_indicator")),
            "route_summary": source_option.get("route_summary") or self._route_summary(source_segments),
            "schedule_summary": self._schedule_summary(first, last, (metric or {}).get("total_elapsed_minutes")),
            "client_summary": source_option.get("headline") or source_option.get("operational_summary"),
            "internal_summary": source_option.get("internal_notes") or source_option.get("operational_summary"),
            "warning_count": len(warnings),
            "blocking_warning_count": len([item for item in warnings if item in {"missing_active_segments", "invalid_segment_chronology", "negative_connection", "price_arithmetic_invalid"}]),
            "review_required_count": len(warnings),
            "unknown_value_count": unknown_count,
            "completeness_score": int((metric or {}).get("itinerary_completeness_score") or 0),
            "display_order": order,
            "is_preferred": presentation.get("preferred_option_id") in {source_option["id"]},
            "is_archived": False,
            "source_hash": self._hash({"option": source_option, "metric": metric, "segment_ids": [item.get("id") for item in source_segments]}),
            "source_provenance": {"composition_id": presentation["composition_id"], "composition_option_id": source_option["id"], "metric_snapshot_id": (metric or {}).get("id")},
        }
        return await self._upsert(OPTION_COLLECTION, JourneyComparisonOptionProjection, {"agency_id": presentation["agency_id"], "presentation_id": presentation["id"], "composition_option_id": source_option["id"]}, values)

    async def _upsert_segment_projection(self, presentation: dict[str, Any], option: dict[str, Any], assignment: dict[str, Any], source: dict[str, Any] | None, order: int) -> dict[str, Any]:
        source = source or {}
        departure = self._field(source, "departure_local", "departure_utc")
        arrival = self._field(source, "arrival_local", "arrival_utc")
        departure_utc = self._dt(source.get("departure_utc"))
        arrival_utc = self._dt(source.get("arrival_utc"))
        duration = source.get("scheduled_duration_minutes")
        if duration is None and departure_utc and arrival_utc:
            duration = self._minutes(departure_utc, arrival_utc)
        marketing = self._field(source, "marketing_carrier_code", "marketing_carrier")
        operating = self._field(source, "operating_carrier_code", "operating_carrier")
        operated_by = None
        if operating and operating != marketing:
            operated_by = f"Operated by {operating}"
        values = {
            "agency_id": presentation["agency_id"],
            "presentation_id": presentation["id"],
            "option_projection_id": option["id"],
            "source_segment_id": assignment.get("source_segment_id"),
            "segment_number": order,
            "marketing_carrier": marketing,
            "operating_carrier": operating,
            "flight_number": self._field(source, "marketing_flight_number", "flight_number"),
            "origin_airport_code": self._field(source, "origin_airport_code", "departure_airport_code"),
            "destination_airport_code": self._field(source, "destination_airport_code", "arrival_airport_code"),
            "departure_terminal": source.get("departure_terminal"),
            "arrival_terminal": source.get("arrival_terminal"),
            "departure_at": departure,
            "arrival_at": arrival,
            "departure_utc": source.get("departure_utc"),
            "arrival_utc": source.get("arrival_utc"),
            "duration_minutes": duration,
            "aircraft_type": self._field(source, "aircraft_display_name", "aircraft_code", "aircraft_type"),
            "cabin_code": self._field(source, "cabin_code", "cabin_class"),
            "booking_class": self._field(source, "booking_class_code", "booking_class"),
            "codeshare_indicator": bool(source.get("codeshare_indicator") or (marketing and operating and marketing != operating)),
            "client_operated_by_text": operated_by,
            "internal_operational_text": f"Canonical Journey segment {assignment.get('source_segment_id')}; source remains unchanged.",
            "date_change_indicator": self._date_change(departure, arrival),
            "display_order": order,
            "source_provenance": {"assignment_id": assignment.get("id"), "canonical_segment_id": assignment.get("source_segment_id"), "assignment_provenance": assignment.get("provenance") or {}},
            "archived_at": None,
        }
        return await self._upsert(SEGMENT_COLLECTION, JourneyComparisonSegmentProjection, {"agency_id": presentation["agency_id"], "presentation_id": presentation["id"], "option_projection_id": option["id"], "source_segment_id": assignment.get("source_segment_id")}, values)

    async def _upsert_connection_projection(self, presentation: dict[str, Any], option: dict[str, Any], inbound: dict[str, Any], outbound: dict[str, Any], order: int) -> dict[str, Any]:
        inbound_arrival = self._dt(inbound.get("arrival_utc"))
        outbound_departure = self._dt(outbound.get("departure_utc"))
        minutes = self._minutes(inbound_arrival, outbound_departure) if inbound_arrival and outbound_departure else None
        inbound_airport = inbound.get("destination_airport_code")
        outbound_airport = outbound.get("origin_airport_code")
        airport_change = bool(inbound_airport and outbound_airport and inbound_airport != outbound_airport)
        terminal_change = bool(not airport_change and inbound.get("arrival_terminal") and outbound.get("departure_terminal") and inbound.get("arrival_terminal") != outbound.get("departure_terminal"))
        overnight = self._date_change(inbound.get("arrival_at"), outbound.get("departure_at"))
        warnings = ["minimum_connection_not_assessed"]
        if minutes is None:
            warnings.append("connection_time_unknown")
        elif minutes < 0:
            warnings.append("invalid_chronology")
        if airport_change:
            warnings.append("airport_change_review_required")
        if terminal_change:
            warnings.append("terminal_change_review_required")
        if overnight:
            warnings.append("overnight_connection")
        airport_label = f"{inbound_airport} to {outbound_airport}" if airport_change else inbound_airport or outbound_airport or "airport to confirm"
        duration_text = self._duration(minutes) if minutes is not None else "duration to confirm"
        values = {
            "agency_id": presentation["agency_id"],
            "presentation_id": presentation["id"],
            "option_projection_id": option["id"],
            "inbound_segment_id": inbound["id"],
            "outbound_segment_id": outbound["id"],
            "airport_code": airport_label,
            "arrival_terminal": inbound.get("arrival_terminal"),
            "departure_terminal": outbound.get("departure_terminal"),
            "connection_minutes": minutes,
            "airport_change_indicator": airport_change,
            "terminal_change_indicator": terminal_change,
            "overnight_indicator": overnight,
            "self_transfer_indicator": False,
            "baggage_recheck_indicator": airport_change,
            "through_check_status": "unknown",
            "minimum_connection_status": "not_assessed",
            "connection_status": "invalid" if minutes is not None and minutes < 0 else "manual_review_required",
            "client_connection_text": f"Connection at {airport_label}: {duration_text}. Minimum connection compliance has not been assessed.",
            "internal_connection_text": "No governed MCT or through-check assertion is available; verify airline, airport, ticketing, and baggage context.",
            "warning_codes": warnings,
            "manual_review_required": True,
            "display_order": order,
            "source_provenance": {"inbound_projection_id": inbound["id"], "outbound_projection_id": outbound["id"], "calculation": "stored UTC timestamp difference" if minutes is not None else "not calculated"},
            "archived_at": None,
        }
        return await self._upsert(CONNECTION_COLLECTION, JourneyComparisonConnectionProjection, {"agency_id": presentation["agency_id"], "presentation_id": presentation["id"], "option_projection_id": option["id"], "inbound_segment_id": inbound["id"], "outbound_segment_id": outbound["id"]}, values)

    async def _upsert_fare_projection(self, presentation: dict[str, Any], option: dict[str, Any], fare: dict[str, Any], price: dict[str, Any] | None, order: int) -> dict[str, Any]:
        price = price or {}
        base = self._number(price.get("base_amount")) or self._number(price.get("supplier_amount"))
        taxes = self._number(price.get("tax_amount"))
        agency_fee = sum(self._number(price.get(key)) or 0 for key in ["ticketing_fee", "assistance_fee", "markup_amount"])
        service_fee = self._number(price.get("service_fee"))
        ancillary = self._number(price.get("ancillary_amount"))
        discount = self._number(price.get("discount_amount"))
        total = self._number(price.get("total_selling_amount"))
        passenger_count = max(1, int(price.get("passenger_count") or 1))
        attribute_map = {
            "baggage": fare.get("baggage_summary"),
            "changeability": fare.get("changeability"),
            "refundability": fare.get("refundability"),
            "seat_selection": fare.get("seat_selection_inclusion"),
            "meals": fare.get("meal_inclusion"),
            "priority": ", ".join(self._tokens([fare.get("priority_check_in"), fare.get("priority_boarding"), fare.get("fast_track")])),
            "lounge": fare.get("lounge_inclusion"),
        }
        unknown = [key for key, value in attribute_map.items() if value in {None, "", "unknown"}]
        review = list(unknown) if fare.get("requires_review") else []
        warnings = []
        if total is None:
            warnings.append("price_unknown")
        warnings.extend(f"{key}_unknown" for key in unknown)
        values = {
            "agency_id": presentation["agency_id"],
            "presentation_id": presentation["id"],
            "option_projection_id": option["id"],
            "composition_fare_choice_id": fare["id"],
            "fare_brand_id": fare.get("fare_family_id"),
            "brand_name": fare.get("external_brand_name") or fare.get("client_safe_label") or "Fare brand",
            "client_brand_name": fare.get("client_safe_label") or fare.get("external_brand_name") or "Fare option",
            "cabin_name": fare.get("cabin"),
            "booking_class_summary": fare.get("booking_class"),
            "currency_code": price.get("currency"),
            "base_fare": base,
            "taxes": taxes,
            "agency_fee": round(agency_fee, 2) if price else None,
            "service_fee": service_fee,
            "ancillary_total": ancillary,
            "discount_total": discount,
            "grand_total": total,
            "passenger_count": passenger_count,
            "price_per_passenger": round(total / passenger_count, 2) if total is not None else None,
            "baggage_summary": fare.get("baggage_summary") or "unknown",
            "change_summary": fare.get("changeability") or "unknown",
            "refund_summary": fare.get("refundability") or "unknown",
            "seat_summary": fare.get("seat_selection_inclusion") or "unknown",
            "meal_summary": fare.get("meal_inclusion") or "unknown",
            "priority_summary": attribute_map["priority"] or "unknown",
            "lounge_summary": fare.get("lounge_inclusion") or "unknown",
            "mileage_summary": (fare.get("metadata") or {}).get("mileage_summary") or "unknown",
            "included_services": fare.get("included_service_codes") or [],
            "excluded_services": fare.get("excluded_service_codes") or [],
            "unknown_attributes": unknown,
            "manual_review_attributes": review,
            "warning_codes": warnings,
            "display_order": order,
            "is_recommended": False,
            "source_hash": self._hash({"fare": fare, "price": price}),
            "source_provenance": {"composition_fare_choice_id": fare["id"], "price_breakdown_id": price.get("id"), "source_type": fare.get("source_type"), "evidence_refs": fare.get("evidence_refs") or [], "knowledge_version_refs": fare.get("knowledge_version_refs") or []},
            "archived_at": None,
        }
        return await self._upsert(FARE_COLLECTION, JourneyComparisonFareBrandProjection, {"agency_id": presentation["agency_id"], "presentation_id": presentation["id"], "option_projection_id": option["id"], "composition_fare_choice_id": fare["id"]}, values)

    async def _upsert_service_projection(self, presentation: dict[str, Any], option: dict[str, Any], assessment: dict[str, Any]) -> dict[str, Any]:
        feasibility = assessment.get("feasibility_status") or "unknown"
        confirmation_required = bool(assessment.get("airline_confirmation_required") or assessment.get("approval_required") or assessment.get("confirmation_status") in {"pending", "unknown"})
        document_required = bool(assessment.get("document_required"))
        warnings = self._tokens([*(assessment.get("warning_codes") or []), *(assessment.get("operational_warning_codes") or [])])
        if feasibility in {"unknown", "not_assessed"}:
            warnings.append("service_suitability_unknown")
        if confirmation_required:
            warnings.append("airline_confirmation_required")
        warnings = self._tokens(warnings)
        blocking = feasibility in {"unsupported", "unavailable"}
        manual = blocking or confirmation_required or feasibility in {"unknown", "not_assessed", "conditional", "conditionally_supported"}
        service_code = assessment.get("service_code") or "OTHER"
        values = {
            "agency_id": presentation["agency_id"],
            "presentation_id": presentation["id"],
            "option_projection_id": option["id"],
            "passenger_id": assessment.get("passenger_id"),
            "service_code": service_code,
            "service_name": assessment.get("service_name") or service_code,
            "category": assessment.get("category") or "passenger_service",
            "assessment_status": assessment.get("assessment_status") or "not_assessed",
            "suitability_status": feasibility,
            "airline_support_status": assessment.get("airline_capability_status") or "unknown",
            "evidence_status": assessment.get("knowledge_freshness_status") or "unknown",
            "policy_status": assessment.get("policy_ownership_status") or "unknown",
            "pricing_status": assessment.get("pricing_status") or ("required" if assessment.get("emd_required") or assessment.get("EMD_required") else "not_assessed"),
            "confirmation_requirement": "airline_confirmation_required" if confirmation_required else "not_required",
            "documentation_requirement": "required" if document_required else "not_required",
            "deadline_summary": assessment.get("deadline_summary"),
            "client_safe_summary": assessment.get("client_safe_summary") or self._service_client_summary(service_code, feasibility, confirmation_required),
            "internal_operational_summary": assessment.get("internal_summary") or "Review the canonical service assessment and airline evidence before commitment.",
            "warning_codes": warnings,
            "blocking_indicator": blocking,
            "manual_review_required": manual,
            "source_references": [{"type": "service_assessment", "id": assessment.get("id")}, *[{"type": "evidence", "id": item} for item in assessment.get("evidence_refs") or []]],
            "archived_at": None,
        }
        key = {"agency_id": presentation["agency_id"], "presentation_id": presentation["id"], "option_projection_id": option["id"], "service_code": service_code, "passenger_id": assessment.get("passenger_id")}
        return await self._upsert(SERVICE_COLLECTION, JourneyComparisonServiceSuitabilityProjection, key, values)

    async def _refresh_option_projection(self, option: dict[str, Any], segments: list[dict[str, Any]], connections: list[dict[str, Any]], services: list[dict[str, Any]]) -> None:
        first = segments[0] if segments else {}
        last = segments[-1] if segments else {}
        departure_utc = self._dt(first.get("departure_utc"))
        arrival_utc = self._dt(last.get("arrival_utc"))
        total_elapsed = self._minutes(departure_utc, arrival_utc) if departure_utc and arrival_utc else option.get("total_elapsed_minutes")
        flight_minutes = [item.get("duration_minutes") for item in segments if item.get("duration_minutes") is not None]
        connection_minutes = [item.get("connection_minutes") for item in connections if item.get("connection_minutes") is not None and item.get("connection_minutes") >= 0]
        unknown_count = sum(1 for item in segments for key in ["departure_at", "arrival_at", "marketing_carrier", "origin_airport_code", "destination_airport_code"] if item.get(key) in {None, ""})
        unknown_count += sum(len(item.get("unknown_attributes") or []) for item in await self._active_rows(FARE_COLLECTION, option["agency_id"], option["presentation_id"], option_id=option["id"]))
        unknown_count += len([item for item in services if item.get("suitability_status") in {"unknown", "not_assessed"}])
        warnings = self._tokens([*(option.get("source_provenance", {}).get("warning_codes") or []), *[code for item in connections for code in item.get("warning_codes") or []], *[code for item in services for code in item.get("warning_codes") or []]])
        blocking = len([item for item in services if item.get("blocking_indicator")]) + len([item for item in connections if item.get("connection_status") == "invalid"])
        review = len([item for item in connections if item.get("manual_review_required")]) + len([item for item in services if item.get("manual_review_required")])
        required_values = [first.get("departure_at"), last.get("arrival_at"), total_elapsed, segments]
        complete = len([item for item in required_values if item is not None and item != "" and item != []])
        await self.db.collection(OPTION_COLLECTION).update_one({"id": option["id"], "agency_id": option["agency_id"]}, {
            "departure_at": first.get("departure_at"),
            "arrival_at": last.get("arrival_at"),
            "total_elapsed_minutes": total_elapsed,
            "total_flight_minutes": sum(flight_minutes) if flight_minutes else None,
            "total_connection_minutes": sum(connection_minutes) if connection_minutes else (0 if len(segments) <= 1 else None),
            "shortest_connection_minutes": min(connection_minutes) if connection_minutes else None,
            "longest_connection_minutes": max(connection_minutes) if connection_minutes else None,
            "segment_count": len(segments),
            "connection_count": len(connections),
            "stop_count": len(connections),
            "overnight_connection_count": len([item for item in connections if item.get("overnight_indicator")]),
            "airport_change_count": len([item for item in connections if item.get("airport_change_indicator")]),
            "terminal_change_count": len([item for item in connections if item.get("terminal_change_indicator")]),
            "warning_count": len(warnings),
            "blocking_warning_count": blocking,
            "review_required_count": review,
            "unknown_value_count": unknown_count,
            "completeness_score": round(complete / len(required_values) * 100),
            "schedule_summary": self._schedule_summary(first, last, total_elapsed),
        })

    async def _ensure_configuration(self, presentation: dict[str, Any]) -> dict[str, Any]:
        existing = await self.db.collection(CONFIG_COLLECTION).find_one({"agency_id": presentation["agency_id"], "presentation_id": presentation["id"]})
        if existing:
            return existing
        return await self.db.collection(CONFIG_COLLECTION).insert_one(JourneyPresentationConfiguration(
            agency_id=presentation["agency_id"],
            presentation_id=presentation["id"],
            journey_id=None,
            display_mode="client_comparison",
            client_safe_mode=True,
            show_internal_information=False,
            locale=presentation.get("language_code") or "en",
        ).model_dump(mode="json"))

    async def _ensure_dimensions(self, presentation: dict[str, Any]) -> list[dict[str, Any]]:
        existing = await self.db.collection(DIMENSION_COLLECTION).find_many({"agency_id": presentation["agency_id"], "presentation_id": presentation["id"]})
        by_code = {item["dimension_code"]: item for item in existing}
        result = []
        for order, (code, label, client_label, category, data_type, direction) in enumerate(DEFAULT_DIMENSIONS, start=1):
            if code in by_code:
                result.append(by_code[code])
                continue
            result.append(await self.db.collection(DIMENSION_COLLECTION).insert_one(JourneyComparisonDimension(
                agency_id=presentation["agency_id"],
                presentation_id=presentation["id"],
                dimension_code=code,
                label=label,
                client_label=client_label,
                description=f"Deterministic {label.lower()} comparison; unknown values remain explicit.",
                category=category,
                data_type=data_type,
                display_order=order,
                importance="high" if code in {"total_price", "total_elapsed_time", "special_service_suitability", "operational_risk"} else "standard",
                scoring_direction=direction,
                internal_only=code in {"evidence_confidence", "operational_risk"},
            ).model_dump(mode="json")))
        return result

    async def _ensure_option_content_block(self, presentation: dict[str, Any], option: dict[str, Any]) -> dict[str, Any]:
        existing = await self.db.collection(CONTENT_COLLECTION).find_one({"agency_id": presentation["agency_id"], "presentation_id": presentation["id"], "option_projection_id": option["id"], "block_type": "generated_option_summary"})
        values = {
            "agency_id": presentation["agency_id"],
            "presentation_id": presentation["id"],
            "option_projection_id": option["id"],
            "block_type": "generated_option_summary",
            "title": option.get("option_label") or "Itinerary option",
            "client_text": option.get("client_summary") or f"{option.get('route_summary') or 'Route to confirm'} with {option.get('carrier_summary') or 'carrier to confirm'}.",
            "internal_text": option.get("internal_summary"),
            "icon_key": "plane",
            "display_order": int(option.get("display_order") or 0),
            "visibility_scope": "client_and_internal",
            "severity": "review_required" if option.get("review_required_count") else "informational",
            "source_references": [{"type": "option_projection", "id": option["id"]}],
            "archived_at": None,
        }
        if existing:
            model = JourneyPresentationContentBlock(**{**existing, **values}).model_dump(mode="json")
            return await self.db.collection(CONTENT_COLLECTION).update_one({"id": existing["id"], "agency_id": presentation["agency_id"]}, model) or existing
        return await self.db.collection(CONTENT_COLLECTION).insert_one(JourneyPresentationContentBlock(**values).model_dump(mode="json"))

    async def _journey_service_fallback(self, agency_id: str, journey_id: str, itinerary_option_id: str | None) -> list[dict[str, Any]]:
        rows = await self.db.collection("journey_service_presentations").find_many({"agency_id": agency_id, "journey_id": journey_id})
        return [item for item in rows if not item.get("itinerary_option_id") or not itinerary_option_id or item.get("itinerary_option_id") == itinerary_option_id]

    async def _composition_detail(self, agency_id: str, composition_id: str) -> dict[str, Any]:
        try:
            return await JourneyOptionFareBrandCompositionService(self.db).get_composition(agency_id, composition_id)
        except JourneyOptionCompositionError as exc:
            raise JourneyComparisonPresentationError(str(exc)) from exc

    async def _require_presentation(self, agency_id: str, presentation_id: str) -> dict[str, Any]:
        item = await self.db.collection(PRESENTATION_COLLECTION).find_one({"id": presentation_id, "agency_id": agency_id})
        if not item:
            raise JourneyComparisonPresentationError("Journey comparison presentation was not found for this agency.")
        return item

    async def _require_projection(self, collection: str, agency_id: str, presentation_id: str, record_id: str, label: str) -> dict[str, Any]:
        item = await self.db.collection(collection).find_one({"id": record_id, "agency_id": agency_id, "presentation_id": presentation_id})
        if not item:
            raise JourneyComparisonPresentationError(f"{label} was not found for this agency presentation.")
        return item

    async def _require_snapshot(self, agency_id: str, presentation_id: str, snapshot_id: str) -> dict[str, Any]:
        return await self._require_projection(SNAPSHOT_COLLECTION, agency_id, presentation_id, snapshot_id, "Presentation snapshot")

    async def _select_snapshot(self, agency_id: str, presentation_id: str, snapshot_id: str | None) -> dict[str, Any]:
        if snapshot_id:
            snapshot = await self._require_snapshot(agency_id, presentation_id, snapshot_id)
            if not snapshot.get("finalized"):
                raise JourneyComparisonPresentationError("A finalized presentation snapshot is required for handoff.")
            return snapshot
        snapshots = await self.list_snapshots(agency_id, presentation_id)
        snapshot = next((item for item in snapshots if item.get("finalized")), None)
        if not snapshot:
            raise JourneyComparisonPresentationError("Create and finalize a presentation snapshot before handoff.")
        return snapshot

    async def _find_destination(self, agency_id: str, destination_type: str, destination_id: str) -> dict[str, Any]:
        collections = ["offer_workspaces_v2", "offer_workspaces", "offers"] if destination_type == "offer_workspace" else ["document_workspaces"]
        for collection in collections:
            item = await self.db.collection(collection).find_one({"id": destination_id, "agency_id": agency_id})
            if item:
                return {**item, "_source_collection": collection}
        label = "Offer Workspace" if destination_type == "offer_workspace" else "Document Workspace"
        raise JourneyComparisonPresentationError(f"{label} was not found for this agency.")

    async def _upsert(self, collection: str, model_class: Any, filters: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
        existing = await self.db.collection(collection).find_one(filters)
        if existing:
            model = model_class(**{**existing, **values, "id": existing["id"], "created_at": existing["created_at"]}).model_dump(mode="json")
            return await self.db.collection(collection).update_one({"id": existing["id"], "agency_id": values["agency_id"]}, model) or existing
        return await self.db.collection(collection).insert_one(model_class(**values).model_dump(mode="json"))

    async def _archive_stale(self, collection: str, agency_id: str, presentation_id: str, active_ids: list[str], *, option_mode: bool = False) -> None:
        rows = await self.db.collection(collection).find_many({"agency_id": agency_id, "presentation_id": presentation_id})
        for row in rows:
            if row["id"] not in active_ids:
                update = {"is_archived": True} if option_mode else {"archived_at": self._now()}
                await self.db.collection(collection).update_one({"id": row["id"], "agency_id": agency_id}, update)

    async def _active_rows(self, collection: str, agency_id: str, presentation_id: str, *, option_id: str | None = None) -> list[dict[str, Any]]:
        rows = await self.db.collection(collection).find_many({"agency_id": agency_id, "presentation_id": presentation_id})
        rows = [item for item in rows if not item.get("archived_at") and not item.get("is_archived")]
        if option_id:
            rows = [item for item in rows if item.get("option_projection_id") == option_id]
        return rows

    def _dimension_results(self, rows: list[dict[str, Any]], leaders: dict[str, str | None]) -> list[dict[str, Any]]:
        mapping = {
            "total_price": ("total_price", leaders["lowest_price_option_id"], "lower"),
            "price_per_passenger": ("price_per_passenger", None, "lower"),
            "departure_convenience": ("departure_at", None, "informational"),
            "arrival_convenience": ("arrival_at", None, "informational"),
            "total_elapsed_time": ("total_elapsed_minutes", leaders["fastest_option_id"], "lower"),
            "flight_time": ("total_flight_minutes", leaders["shortest_flight_time_option_id"], "lower"),
            "connection_time": ("total_connection_minutes", None, "lower"),
            "stop_count": ("stop_count", leaders["fewest_stops_option_id"], "lower"),
            "airport_changes": ("airport_change_count", None, "lower"),
            "overnight_connections": ("overnight_connection_count", None, "lower"),
            "baggage": ("baggage_score", leaders["best_baggage_option_id"], "higher"),
            "change_conditions": ("flexibility_score", leaders["best_flexibility_option_id"], "higher"),
            "refund_conditions": ("flexibility_score", leaders["best_flexibility_option_id"], "higher"),
            "seat_inclusion": (None, None, "informational"),
            "meal_inclusion": (None, None, "informational"),
            "priority_services": (None, None, "informational"),
            "lounge_access": (None, None, "informational"),
            "operating_carrier_complexity": ("operating_carrier_count", None, "lower"),
            "interline_complexity": ("interline_indicator", None, "lower"),
            "special_service_suitability": ("special_service_score", leaders["best_special_service_option_id"], "higher"),
            "evidence_confidence": (None, None, "informational"),
            "unresolved_unknowns": ("unknown_value_count", None, "lower"),
            "operational_risk": ("operational_risk_score", leaders["lowest_operational_risk_option_id"], "lower"),
            "manual_review_requirement": ("manual_review_required", None, "lower"),
        }
        results = []
        for code, _, client_label, _, _, _ in DEFAULT_DIMENSIONS:
            field, leader, direction = mapping[code]
            values = [{"option_id": item["option_id"], "value": item.get(field) if field else "not_assessed", "state": "unknown" if field and item.get(field) is None else "not_assessed" if not field else "known"} for item in rows]
            known = [item for item in values if item["state"] == "known"]
            leader_ids = []
            if leader:
                target = next((item["value"] for item in known if item["option_id"] == leader), None)
                leader_ids = [item["option_id"] for item in known if item["value"] == target] if target is not None else []
            results.append({"dimension_code": code, "client_label": client_label, "direction": direction, "values": values, "leader_option_ids": leader_ids, "unknown_count": len(values) - len(known)})
        return results

    def _leader(self, rows: list[dict[str, Any]], field: str, *, lower: bool) -> str | None:
        known = [item for item in rows if item.get(field) is not None]
        if not known:
            return None
        target = (min if lower else max)(item[field] for item in known)
        leaders = [item["option_id"] for item in known if item[field] == target]
        return leaders[0] if len(leaders) == 1 else None

    def _baggage_score(self, value: Any) -> int | None:
        text = str(value or "").lower()
        if not text or text == "unknown":
            return None
        pieces = [int(item) for item in re.findall(r"(\d+)\s+(?:checked|cabin|bag)", text)]
        weights = [int(item) for item in re.findall(r"(\d+)\s*kg", text)]
        return sum(pieces) * 100 + sum(weights) + (10 if "personal item included" in text else 0)

    def _status_score(self, value: Any) -> int:
        text = str(value or "unknown").lower()
        if text in {"included", "supported", "refundable", "changeable", "confirmed"}:
            return 3
        if text in {"conditional", "conditionally_supported", "with_fee"}:
            return 2
        if text in {"not_included", "unsupported", "nonrefundable", "non_refundable"}:
            return 1
        return 0

    def _client_comparison(self, result: dict[str, Any]) -> dict[str, Any]:
        return {
            "generated_at": result.get("generated_at"),
            "preferred_option_id": result.get("preferred_option_id"),
            "dimension_results": [item for item in result.get("dimension_results") or [] if item.get("dimension_code") not in {"evidence_confidence", "operational_risk"}],
            "fare_brand_results": result.get("fare_brand_results") or [],
            "tie_results": [item for item in result.get("tie_results") or [] if item.get("dimension_code") not in {"evidence_confidence", "operational_risk"}],
            "warning_summary": result.get("warning_summary") or {},
            "unresolved_unknowns": result.get("unresolved_unknowns") or [],
            "manual_review_required": result.get("manual_review_required", True),
            "automatic_preferred_option_selected": False,
        }

    def _platform_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {key: item.get(key) for key in ["id", "agency_id", "composition_id", "journey_id", "offer_id", "title", "status", "audience_type", "language_code", "currency_code", "requires_review", "created_at", "updated_at", "archived_at"]}

    def _snapshot_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {key: item.get(key) for key in ["id", "presentation_id", "version_number", "snapshot_status", "source_hash", "finalized", "created_at", "finalized_at"]}

    def _sanitize_client(self, value: Any) -> Any:
        if isinstance(value, list):
            return [self._sanitize_client(item) for item in value]
        if not isinstance(value, dict):
            return value
        result = {}
        for key, item in value.items():
            if key in CLIENT_RESTRICTED_FIELDS or key.startswith("internal_"):
                continue
            result[key] = self._sanitize_client(item)
        return result

    def _service_client_summary(self, service_code: str, feasibility: str, confirmation_required: bool) -> str:
        state = feasibility.replace("_", " ") if feasibility else "not assessed"
        confirmation = " Airline confirmation is required." if confirmation_required else ""
        return f"{service_code}: {state}.{confirmation}"

    def _composition_currency(self, detail: dict[str, Any]) -> str | None:
        currencies = self._tokens([item.get("currency") for item in detail.get("price_breakdowns") or []])
        return currencies[0] if len(currencies) == 1 else None

    def _schedule_summary(self, first: dict[str, Any], last: dict[str, Any], total_minutes: int | None) -> str:
        departure = self._field(first, "departure_at", "departure_local", "departure_utc")
        arrival = self._field(last, "arrival_at", "arrival_local", "arrival_utc")
        if not departure or not arrival:
            return "Schedule information is incomplete."
        return f"{departure} to {arrival}; {self._duration(total_minutes) if total_minutes is not None else 'total duration to confirm'}"

    def _route_summary(self, segments: list[dict[str, Any]]) -> str:
        if not segments:
            return "Route to confirm"
        points = [self._field(segments[0], "origin_airport_code", "departure_airport_code") or "???"]
        points.extend(self._field(item, "destination_airport_code", "arrival_airport_code") or "???" for item in segments)
        return " - ".join(points)

    def _field(self, item: dict[str, Any], *names: str) -> Any:
        return next((item.get(name) for name in names if item.get(name) is not None), None)

    def _tokens(self, values: Any) -> list[str]:
        result = []
        for value in values or []:
            if value is None:
                continue
            token = str(value).strip()
            if token and token not in result:
                result.append(token)
        return result

    def _number(self, value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _dt(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
        except ValueError:
            return None

    def _date_change(self, start: Any, end: Any) -> bool:
        start_value = self._dt(start)
        end_value = self._dt(end)
        return bool(start_value and end_value and end_value.date() > start_value.date())

    def _minutes(self, start: datetime, end: datetime) -> int:
        return round((end - start).total_seconds() / 60)

    def _duration(self, value: int | None) -> str:
        if value is None:
            return "duration unknown"
        return f"{value // 60}h {value % 60}m"

    def _choice(self, value: Any, allowed: list[str], label: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in allowed:
            raise JourneyComparisonPresentationError(f"Unsupported {label}: {value}.")
        return normalized

    def _normalize_for_hash(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._normalize_for_hash(item) for key, item in sorted(value.items()) if key not in {"updated_at", "generated_at"}}
        if isinstance(value, list):
            return [self._normalize_for_hash(item) for item in value]
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value

    def _hash(self, value: Any) -> str:
        return sha256(json.dumps(self._normalize_for_hash(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()

    def _actor(self, user: dict[str, Any] | None) -> str | None:
        if not user:
            return None
        return str(user.get("id") or user.get("user_id") or user.get("email") or "") or None

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    async def _audit(self, action: str, target: dict[str, Any], user: dict[str, Any] | None, metadata: dict[str, Any] | None = None) -> None:
        await self.db.collection("audit_logs").insert_one({
            "id": self._hash({"action": action, "target": target.get("id"), "at": self._now().isoformat()})[:32],
            "actor_user_id": self._actor(user),
            "agency_id": target.get("agency_id"),
            "action": action,
            "target_type": "journey_comparison_presentation",
            "target_id": target.get("id"),
            "metadata_json": metadata or {},
            "created_at": self._now(),
            "updated_at": self._now(),
        })
