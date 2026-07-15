from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from typing import Any

from database import Database
from models import (
    JourneyCommercialPriceBreakdown,
    JourneyFareBrandChoice,
    JourneyOptionAlternative,
    JourneyOptionComparisonProfile,
    JourneyOptionComparisonResult,
    JourneyOptionComposition,
    JourneyOptionCompositionSnapshot,
    JourneyOptionMetricSnapshot,
    JourneyOptionOfferHandoff,
    JourneyOptionSegmentAssignment,
    JourneyOptionServiceAssessment,
)
from services.airline_fare_family_brand_intelligence_service import AirlineFareFamilyBrandIntelligenceService


from build_phase import CURRENT_BUILD_PHASE

CAPABILITY_PHASE = "phase_56_2_journey_option_fare_brand_composition_workspace_foundation"
PHASE_LABEL = CURRENT_BUILD_PHASE

COMPOSITION_COLLECTION = "journey_option_compositions"
OPTION_COLLECTION = "journey_option_alternatives"
ASSIGNMENT_COLLECTION = "journey_option_segment_assignments"
FARE_CHOICE_COLLECTION = "journey_fare_brand_choices"
PRICE_COLLECTION = "journey_commercial_price_breakdowns"
METRIC_COLLECTION = "journey_option_metric_snapshots"
SERVICE_ASSESSMENT_COLLECTION = "journey_option_service_assessments"
COMPARISON_PROFILE_COLLECTION = "journey_option_comparison_profiles"
COMPARISON_RESULT_COLLECTION = "journey_option_comparison_results"
SNAPSHOT_COLLECTION = "journey_option_composition_snapshots"
HANDOFF_COLLECTION = "journey_option_offer_handoffs"

COMPOSITION_COLLECTIONS = [
    COMPOSITION_COLLECTION,
    OPTION_COLLECTION,
    ASSIGNMENT_COLLECTION,
    FARE_CHOICE_COLLECTION,
    PRICE_COLLECTION,
    METRIC_COLLECTION,
    SERVICE_ASSESSMENT_COLLECTION,
    COMPARISON_PROFILE_COLLECTION,
    COMPARISON_RESULT_COLLECTION,
    SNAPSHOT_COLLECTION,
    HANDOFF_COLLECTION,
]

COMPOSITION_STATUSES = ["draft", "composing", "requires_review", "ready", "snapshotted", "prepared_for_offer", "archived"]
OPTION_STATUSES = ["draft", "incomplete", "requires_review", "complete", "archived"]
UNCERTAINTY_STATUSES = ["confirmed", "conditional", "unknown", "requires_review"]
WARNING_SEVERITIES = ["blocking", "important", "review_required", "informational", "unknown"]
COMPARISON_DIMENSIONS = [
    "total_price", "route", "departure_time", "arrival_time", "total_elapsed_time", "stops", "connections",
    "shortest_connection", "airport_change", "terminal_change", "overnight", "baggage", "cabin", "fare_brand",
    "changeability", "refundability", "seats", "meals", "lounge", "priority_services",
    "special_service_feasibility", "service_confirmation_requirements", "evidence_confidence",
    "operational_warnings", "client_safe_highlights",
]
VALIDATION_CODES = [
    "missing_active_segments", "duplicate_segment_assignment", "segment_agency_mismatch", "segment_journey_mismatch",
    "segment_schedule_unknown", "invalid_segment_chronology", "connection_time_unknown", "negative_connection",
    "potentially_short_connection", "long_connection_review", "airport_change_review_required",
    "terminal_change_review_required", "overnight_journey", "overnight_connection", "date_change",
    "interline_review_required", "codeshare_review_required", "fare_brand_unknown", "fare_brand_stale",
    "price_missing", "price_arithmetic_invalid", "currency_mismatch", "service_feasibility_unknown",
    "airline_confirmation_required", "critical_knowledge_gap", "restricted_evidence_removed",
]
INTERNAL_FIELDS = {
    "internal_title", "internal_decision_notes", "internal_label", "internal_agent_notes", "internal_summary",
    "internal_cost_visible", "calculation_trace", "trace", "restricted_metadata", "internal_notes",
}


class JourneyOptionCompositionError(ValueError):
    pass


class FinalizedCompositionSnapshotError(JourneyOptionCompositionError):
    pass


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_none=True, exclude_unset=True)
    return {key: value for key, value in dict(payload or {}).items() if value is not None}


class JourneyOptionFareBrandCompositionService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "journey_option_fare_brand_composition_enabled": True,
            "option_compositions_collection_enabled": True,
            "itinerary_alternatives_enabled": True,
            "segment_assignment_projection_enabled": True,
            "fare_brand_choice_composition_enabled": True,
            "manual_fare_brand_entry_enabled": True,
            "governed_fare_brand_import_enabled": True,
            "commercial_price_breakdown_enabled": True,
            "deterministic_price_arithmetic_validation_enabled": True,
            "deterministic_journey_metrics_enabled": True,
            "duration_comparison_enabled": True,
            "connection_comparison_enabled": True,
            "baggage_comparison_enabled": True,
            "change_refund_comparison_enabled": True,
            "special_service_assessment_projection_enabled": True,
            "interline_uncertainty_projection_enabled": True,
            "client_internal_content_separation_enabled": True,
            "immutable_composition_snapshots_enabled": True,
            "finalized_snapshot_mutation_disabled": True,
            "offer_handoff_preview_enabled": True,
            "explicit_offer_handoff_enabled": True,
            "automatic_offer_publication_disabled": True,
            "live_pricing_disabled": True,
            "live_availability_disabled": True,
            "provider_connectivity_disabled": True,
            "external_api_calls_disabled": True,
            "scraping_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_production_seeding_disabled": True,
            "metadata_only": True,
        }

    def filters(self) -> dict[str, Any]:
        return {
            "composition_statuses": COMPOSITION_STATUSES,
            "option_statuses": OPTION_STATUSES,
            "uncertainty_statuses": UNCERTAINTY_STATUSES,
            "warning_severities": WARNING_SEVERITIES,
            "comparison_dimensions": COMPARISON_DIMENSIONS,
            "validation_codes": VALIDATION_CODES,
            "target_option_count": 3,
            "target_fare_choice_count_per_option": 3,
        }

    async def create_composition(self, agency_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        if data.get("agency_id") and data["agency_id"] != agency_id:
            raise JourneyOptionCompositionError("Composition agency_id must match the route agency.")
        journey = await self._require_journey(agency_id, str(data.get("journey_id") or ""))
        await self._validate_optional_links(agency_id, data)
        existing = await self.db.collection(COMPOSITION_COLLECTION).find_many({"agency_id": agency_id, "journey_id": journey["id"]})
        version = max([int(item.get("version_number") or 0) for item in existing] or [0]) + 1
        values = {
            **data,
            "agency_id": agency_id,
            "journey_id": journey["id"],
            "title": data.get("title") or f"{journey.get('title') or 'Journey'} options v{version}",
            "client_safe_title": data.get("client_safe_title") or journey.get("title"),
            "status": data.get("status") or "draft",
            "version_number": version,
            "source_refs": self._source_refs(data, journey),
            "created_by": self._actor(user),
            "updated_by": self._actor(user),
        }
        self._choice(values["status"], COMPOSITION_STATUSES, "composition status")
        stored = await self.db.collection(COMPOSITION_COLLECTION).insert_one(JourneyOptionComposition(**values).model_dump(mode="json"))
        await self._audit("journey_option_composition.created", stored, user)
        return {"phase": PHASE_LABEL, "composition": stored, **self.safety_flags()}

    async def create_from_journey(self, agency_id: str, journey_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        result = await self.create_composition(agency_id, {**payload_dict(payload), "journey_id": journey_id}, user)
        composition = result["composition"]
        canonical_options = await self.db.collection("journey_itinerary_options").find_many({"agency_id": agency_id, "journey_id": journey_id})
        canonical_options.sort(key=lambda item: int(item.get("option_number") or 0))
        if not canonical_options:
            option = (await self.create_option(agency_id, composition["id"], {"client_safe_label": "Option A"}, user))["option"]
            segments = await self.db.collection("journey_segment_representations").find_many({"agency_id": agency_id, "journey_id": journey_id})
            if segments:
                await self.assign_segments(agency_id, composition["id"], option["id"], {"segment_ids": [item["id"] for item in segments]}, user)
        else:
            for canonical in canonical_options:
                option = (await self.create_option(agency_id, composition["id"], {
                    "client_safe_label": canonical.get("title") or f"Option {self._alpha(len(await self._active_options(agency_id, composition['id'])))}",
                    "internal_label": canonical.get("title"),
                    "metadata": {"canonical_itinerary_option_id": canonical["id"]},
                }, user))["option"]
                segments = await self.db.collection("journey_segment_representations").find_many({
                    "agency_id": agency_id, "journey_id": journey_id, "itinerary_option_id": canonical["id"]
                })
                if segments:
                    await self.assign_segments(agency_id, composition["id"], option["id"], {"segment_ids": [item["id"] for item in segments]}, user)
        return await self.get_composition(agency_id, composition["id"])

    async def create_from_authoring_session(self, agency_id: str, session_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        session = await self.db.collection("journey_authoring_sessions").find_one({"id": session_id, "agency_id": agency_id})
        if not session:
            raise JourneyOptionCompositionError("Journey authoring session was not found for this agency.")
        if not session.get("journey_id"):
            applications = await self.db.collection("journey_authoring_applications").find_many({"agency_id": agency_id, "authoring_session_id": session_id})
            applications.sort(key=lambda item: str(item.get("applied_at") or item.get("created_at") or ""), reverse=True)
            if applications:
                session["journey_id"] = applications[0].get("journey_id")
        if not session.get("journey_id"):
            raise JourneyOptionCompositionError("Apply the authoring session to a canonical Journey before composing options.")
        return await self.create_from_journey(agency_id, str(session["journey_id"]), {**payload_dict(payload), "authoring_session_id": session_id}, user)

    async def create_from_offer(self, agency_id: str, offer_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        offer = await self._find_offer(agency_id, offer_id)
        journeys = await self.db.collection("journey_representations").find_many({"agency_id": agency_id})
        journey = next((item for item in journeys if item.get("source_entity_id") == offer_id and "offer" in str(item.get("source_entity_type") or "")), None)
        if not journey:
            raise JourneyOptionCompositionError("Create the canonical Journey projection for this offer before composing options.")
        return await self.create_from_journey(agency_id, journey["id"], {**payload_dict(payload), "offer_id": offer_id, "offer_workspace_id": offer_id}, user)

    async def list_compositions(self, agency_id: str | None = None, **filters: Any) -> list[dict[str, Any]]:
        records = await self.db.collection(COMPOSITION_COLLECTION).find_many({"agency_id": agency_id} if agency_id else None)
        if not filters.get("include_archived"):
            records = [item for item in records if not item.get("archived_at")]
        for field in ["journey_id", "status", "offer_id", "offer_workspace_id"]:
            if filters.get(field):
                records = [item for item in records if item.get(field) == filters[field]]
        records.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
        return records

    async def get_composition(self, agency_id: str, composition_id: str, *, client_safe: bool = False) -> dict[str, Any]:
        composition = await self._require_composition(agency_id, composition_id)
        options = await self._options(agency_id, composition_id, include_archived=True)
        assignments = await self.db.collection(ASSIGNMENT_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id})
        fares = await self.db.collection(FARE_CHOICE_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id})
        prices = await self.db.collection(PRICE_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id})
        metrics = await self.db.collection(METRIC_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id})
        assessments = await self.db.collection(SERVICE_ASSESSMENT_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id})
        comparisons = await self.db.collection(COMPARISON_RESULT_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id})
        snapshots = await self.list_snapshots(agency_id, composition_id)
        handoffs = await self.db.collection(HANDOFF_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id})
        segments = await self._resolve_assignments(agency_id, assignments)
        payload = {
            "phase": PHASE_LABEL,
            "composition": composition,
            "journey": await self._require_journey(agency_id, composition["journey_id"]),
            "options": options,
            "segment_assignments": sorted(assignments, key=lambda item: (int(item.get("display_order") or 0), str(item.get("created_at") or ""))),
            "segments": segments,
            "fare_brand_choices": sorted(fares, key=lambda item: int(item.get("display_order") or 0)),
            "price_breakdowns": prices,
            "metric_snapshots": sorted(metrics, key=lambda item: str(item.get("calculated_at") or ""), reverse=True),
            "service_assessments": assessments,
            "comparison_results": sorted(comparisons, key=lambda item: str(item.get("generated_at") or ""), reverse=True),
            "snapshots": snapshots,
            "offer_handoffs": sorted(handoffs, key=lambda item: str(item.get("created_at") or ""), reverse=True),
            **self.safety_flags(),
        }
        return self._sanitize(payload) if client_safe else payload

    async def update_composition(self, agency_id: str, composition_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require_editable_composition(agency_id, composition_id)
        allowed = {
            "title", "internal_title", "client_safe_title", "status", "request_id", "trip_id", "offer_id",
            "offer_workspace_id", "client_rationale", "internal_decision_notes", "requires_review", "metadata",
        }
        updates = {key: value for key, value in payload_dict(payload).items() if key in allowed}
        if "status" in updates:
            self._choice(updates["status"], COMPOSITION_STATUSES, "composition status")
        await self._validate_optional_links(agency_id, updates)
        updates["updated_by"] = self._actor(user)
        validated = JourneyOptionComposition(**{**existing, **updates}).model_dump(mode="json")
        stored = await self.db.collection(COMPOSITION_COLLECTION).update_one({"id": composition_id, "agency_id": agency_id}, validated)
        await self._audit("journey_option_composition.updated", stored or existing, user)
        return {"phase": PHASE_LABEL, "composition": stored or existing, **self.safety_flags()}

    async def archive_composition(self, agency_id: str, composition_id: str, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require_composition(agency_id, composition_id)
        stored = await self.db.collection(COMPOSITION_COLLECTION).update_one(
            {"id": composition_id, "agency_id": agency_id},
            {"status": "archived", "archived_at": self._now(), "updated_by": self._actor(user)},
        )
        await self._audit("journey_option_composition.archived", stored or existing, user)
        return {"phase": PHASE_LABEL, "composition": stored or existing, "physical_deletion_performed": False, **self.safety_flags()}

    async def create_option(self, agency_id: str, composition_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        composition = await self._require_editable_composition(agency_id, composition_id)
        data = payload_dict(payload)
        options = await self._active_options(agency_id, composition_id)
        order = int(data.get("display_order") or len(options) + 1)
        code = data.get("option_code") or f"OPTION-{self._alpha(order - 1)}"
        values = {
            **data,
            "agency_id": agency_id,
            "composition_id": composition_id,
            "journey_id": composition["journey_id"],
            "option_code": code,
            "display_order": order,
            "client_safe_label": data.get("client_safe_label") or f"Option {self._alpha(order - 1)}",
            "status": data.get("status") or "draft",
            "created_by": self._actor(user),
            "updated_by": self._actor(user),
        }
        self._choice(values["status"], OPTION_STATUSES, "option status")
        stored = await self.db.collection(OPTION_COLLECTION).insert_one(JourneyOptionAlternative(**values).model_dump(mode="json"))
        await self._touch_composition(composition, user, status="composing")
        await self._audit("journey_option_composition.option_created", stored, user)
        return {"phase": PHASE_LABEL, "option": stored, **self.safety_flags()}

    async def update_option(self, agency_id: str, composition_id: str, option_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_composition(agency_id, composition_id)
        option = await self._require_option(agency_id, composition_id, option_id)
        allowed = {
            "internal_label", "internal_notes", "client_safe_label", "headline", "route_summary", "carrier_summary", "commercial_summary",
            "operational_summary", "status", "requires_review", "warning_codes", "metadata",
        }
        updates = {key: value for key, value in payload_dict(payload).items() if key in allowed}
        if "status" in updates:
            self._choice(updates["status"], OPTION_STATUSES, "option status")
            if updates["status"] == "complete" and not await self._active_assignments(agency_id, composition_id, option_id):
                raise JourneyOptionCompositionError("An option without active segments cannot be marked complete.")
        updates["updated_by"] = self._actor(user)
        validated = JourneyOptionAlternative(**{**option, **updates}).model_dump(mode="json")
        stored = await self.db.collection(OPTION_COLLECTION).update_one({"id": option_id, "agency_id": agency_id}, validated)
        await self._audit("journey_option_composition.option_updated", stored or option, user)
        return {"phase": PHASE_LABEL, "option": stored or option, **self.safety_flags()}

    async def clone_option(self, agency_id: str, composition_id: str, option_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        source = await self._require_option(agency_id, composition_id, option_id)
        data = payload_dict(payload)
        copy_fields = {key: source.get(key) for key in ["internal_label", "internal_notes", "client_safe_label", "headline", "route_summary", "carrier_summary", "commercial_summary", "operational_summary", "metadata"]}
        copy_fields.update(data)
        copy_fields.update({"cloned_from_option_id": option_id, "status": "draft", "requires_review": True})
        cloned = (await self.create_option(agency_id, composition_id, copy_fields, user))["option"]
        for assignment in await self._active_assignments(agency_id, composition_id, option_id):
            await self._insert_assignment(agency_id, await self._require_composition(agency_id, composition_id), cloned, {
                "source_segment_id": assignment["source_segment_id"],
                "source_segment_type": assignment.get("source_segment_type"),
                "journey_segment_projection_id": assignment.get("journey_segment_projection_id"),
                "journey_leg_id": assignment.get("journey_leg_id"),
                "assignment_role": assignment.get("assignment_role"),
                "provenance": {**(assignment.get("provenance") or {}), "cloned_from_assignment_id": assignment["id"]},
            }, int(assignment.get("display_order") or 0))
        fares = await self._active_fares(agency_id, composition_id, option_id)
        for fare in fares:
            copied = {key: value for key, value in fare.items() if key not in {"id", "created_at", "updated_at", "option_id", "display_order", "price_breakdown_id", "archived_at"}}
            copied.update({"option_id": cloned["id"], "display_order": int(fare.get("display_order") or 0), "price_breakdown_id": None})
            created_fare = await self.db.collection(FARE_CHOICE_COLLECTION).insert_one(JourneyFareBrandChoice(**copied).model_dump(mode="json"))
            price = await self.db.collection(PRICE_COLLECTION).find_one({"agency_id": agency_id, "fare_choice_id": fare["id"]})
            if price:
                copied_price = {key: value for key, value in price.items() if key not in {"id", "created_at", "updated_at", "option_id", "fare_choice_id"}}
                copied_price.update({"option_id": cloned["id"], "fare_choice_id": created_fare["id"]})
                created_price = await self.db.collection(PRICE_COLLECTION).insert_one(JourneyCommercialPriceBreakdown(**copied_price).model_dump(mode="json"))
                await self.db.collection(FARE_CHOICE_COLLECTION).update_one({"id": created_fare["id"], "agency_id": agency_id}, {"price_breakdown_id": created_price["id"]})
        metrics = await self.calculate_option_metrics(agency_id, composition_id, cloned["id"])
        return {"phase": PHASE_LABEL, "option": cloned, "metric_snapshot": metrics["metric_snapshot"], "cloned_from_option_id": option_id, **self.safety_flags()}

    async def reorder_options(self, agency_id: str, composition_id: str, option_ids: list[str], user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_composition(agency_id, composition_id)
        options = await self._active_options(agency_id, composition_id)
        if set(option_ids) != {item["id"] for item in options} or len(option_ids) != len(options):
            raise JourneyOptionCompositionError("Reorder must include every active option exactly once.")
        ordered = []
        for order, option_id in enumerate(option_ids, start=1):
            updated = await self.db.collection(OPTION_COLLECTION).update_one({"id": option_id, "agency_id": agency_id}, {"display_order": order, "updated_by": self._actor(user)})
            ordered.append(updated)
        await self._audit("journey_option_composition.options_reordered", await self._require_composition(agency_id, composition_id), user, {"option_ids": option_ids})
        return {"phase": PHASE_LABEL, "items": ordered, **self.safety_flags()}

    async def archive_option(self, agency_id: str, composition_id: str, option_id: str, user: dict[str, Any]) -> dict[str, Any]:
        return await self._set_option_archive(agency_id, composition_id, option_id, True, user)

    async def restore_option(self, agency_id: str, composition_id: str, option_id: str, user: dict[str, Any]) -> dict[str, Any]:
        return await self._set_option_archive(agency_id, composition_id, option_id, False, user)

    async def assign_segments(self, agency_id: str, composition_id: str, option_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        composition = await self._require_editable_composition(agency_id, composition_id)
        option = await self._require_option(agency_id, composition_id, option_id)
        data = payload_dict(payload)
        segment_ids = list(data.get("segment_ids") or [])
        assignments = list(data.get("assignments") or [])
        assignments.extend({"source_segment_id": segment_id, "source_segment_type": data.get("source_segment_type") or "journey_segment_projection"} for segment_id in segment_ids)
        if not assignments:
            raise JourneyOptionCompositionError("At least one canonical Journey segment reference is required.")
        if data.get("replace"):
            for existing in await self._active_assignments(agency_id, composition_id, option_id):
                await self.db.collection(ASSIGNMENT_COLLECTION).update_one({"id": existing["id"], "agency_id": agency_id}, {"included": False, "archived_at": self._now()})
        existing = await self._active_assignments(agency_id, composition_id, option_id)
        created = []
        for index, assignment in enumerate(assignments, start=len(existing) + 1):
            created.append(await self._insert_assignment(agency_id, composition, option, assignment, int(assignment.get("display_order") or index)))
        metric = await self.calculate_option_metrics(agency_id, composition_id, option_id)
        await self._audit("journey_option_composition.segments_assigned", option, user, {"assignment_ids": [item["id"] for item in created]})
        return {"phase": PHASE_LABEL, "items": created, "metric_snapshot": metric["metric_snapshot"], **self.safety_flags()}

    async def replace_segment_assignments(self, agency_id: str, composition_id: str, option_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        return await self.assign_segments(agency_id, composition_id, option_id, {**payload_dict(payload), "replace": True}, user)

    async def remove_segment_assignment(self, agency_id: str, composition_id: str, option_id: str, assignment_id: str, user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_composition(agency_id, composition_id)
        assignment = await self.db.collection(ASSIGNMENT_COLLECTION).find_one({"id": assignment_id, "agency_id": agency_id, "composition_id": composition_id, "option_id": option_id})
        if not assignment:
            raise JourneyOptionCompositionError("Segment assignment was not found for this agency option.")
        stored = await self.db.collection(ASSIGNMENT_COLLECTION).update_one({"id": assignment_id, "agency_id": agency_id}, {"included": False, "archived_at": self._now()})
        metric = await self.calculate_option_metrics(agency_id, composition_id, option_id)
        await self._audit("journey_option_composition.segment_assignment_archived", stored or assignment, user)
        return {"phase": PHASE_LABEL, "assignment": stored or assignment, "metric_snapshot": metric["metric_snapshot"], "physical_deletion_performed": False, **self.safety_flags()}

    async def calculate_option_metrics(self, agency_id: str, composition_id: str, option_id: str) -> dict[str, Any]:
        composition = await self._require_composition(agency_id, composition_id)
        option = await self._require_option(agency_id, composition_id, option_id)
        assignments = await self._active_assignments(agency_id, composition_id, option_id)
        resolved = await self._resolve_assignments(agency_id, assignments)
        segments = [item["segment"] for item in sorted(resolved, key=lambda item: int(item["assignment"].get("display_order") or 0)) if item.get("segment")]
        warnings: list[str] = []
        flight_segments = [item for item in segments if self._segment_type(item) == "flight"]
        starts = [self._dt(self._field(item, "departure_utc", "departure_local", "departure_local_datetime")) for item in segments]
        ends = [self._dt(self._field(item, "arrival_utc", "arrival_local", "arrival_local_datetime")) for item in segments]
        departure = next((item for item in starts if item), None)
        arrival = next((item for item in reversed(ends) if item), None)
        total_elapsed = self._minutes(departure, arrival) if departure and arrival else None
        scheduled = 0
        for segment, start, end in zip(segments, starts, ends):
            duration = segment.get("scheduled_duration_minutes")
            if duration is None and start and end:
                duration = self._minutes(start, end)
            if duration is not None and int(duration) >= 0:
                scheduled += int(duration)
            elif start and end:
                warnings.append("invalid_segment_chronology")
            if not start or not end:
                warnings.append("segment_schedule_unknown")
        connections: list[int] = []
        airport_change = False
        terminal_change = False
        overnight_connection = False
        for index in range(max(len(segments) - 1, 0)):
            inbound, outbound = segments[index], segments[index + 1]
            inbound_end, outbound_start = ends[index], starts[index + 1]
            if inbound_end and outbound_start:
                minutes = self._minutes(inbound_end, outbound_start)
                connections.append(minutes)
                if minutes < 0:
                    warnings.append("negative_connection")
                elif minutes < 45:
                    warnings.append("potentially_short_connection")
                elif minutes > 720:
                    warnings.append("long_connection_review")
            else:
                warnings.append("connection_time_unknown")
            inbound_airport = self._field(inbound, "destination_airport_code", "arrival_airport_code")
            outbound_airport = self._field(outbound, "origin_airport_code", "departure_airport_code")
            if inbound_airport and outbound_airport and inbound_airport != outbound_airport:
                airport_change = True
                warnings.append("airport_change_review_required")
            if inbound_airport == outbound_airport and inbound.get("arrival_terminal") and outbound.get("departure_terminal") and inbound.get("arrival_terminal") != outbound.get("departure_terminal"):
                terminal_change = True
                warnings.append("terminal_change_review_required")
            inbound_local = self._dt(self._field(inbound, "arrival_local", "arrival_local_datetime"))
            outbound_local = self._dt(self._field(outbound, "departure_local", "departure_local_datetime"))
            if inbound_local and outbound_local and outbound_local.date() > inbound_local.date():
                overnight_connection = True
                warnings.append("overnight_connection")
        marketing = self._tokens([self._field(item, "marketing_carrier_code") for item in segments])
        operating = self._tokens([self._field(item, "operating_carrier_code", "marketing_carrier_code") for item in segments])
        codeshare = any(bool(item.get("codeshare_indicator")) or (item.get("marketing_carrier_code") and item.get("operating_carrier_code") and item.get("marketing_carrier_code") != item.get("operating_carrier_code")) for item in segments)
        interline = len(operating) > 1 or len(marketing) > 1
        if codeshare:
            warnings.append("codeshare_review_required")
        if interline:
            warnings.append("interline_review_required")
        date_change = any(bool(item.get("overnight_indicator")) or self._date_change(item) for item in segments) or bool(departure and arrival and arrival.date() > departure.date())
        overnight = date_change or overnight_connection
        if overnight:
            warnings.append("overnight_journey")
        timezone_change = any(self._field(item, "departure_timezone") and self._field(item, "arrival_timezone") and self._field(item, "departure_timezone") != self._field(item, "arrival_timezone") for item in segments)
        surface = any(self._segment_type(item) == "surface" or item.get("surface_segment_indicator") for item in segments)
        technical = any(item.get("technical_stop_indicator") for item in segments)
        connection_count = max(len(flight_segments) - 1, 0)
        stop_count = connection_count + sum(len(item.get("technical_stop_details") or []) for item in segments)
        route_classification = "nonstop" if len(flight_segments) == 1 and not technical else "direct" if len(flight_segments) == 1 else "one_stop" if stop_count == 1 else "multi_stop" if stop_count > 1 else "unknown"
        required_fields = ["origin_airport_code", "destination_airport_code"]
        completeness_values = []
        for item in segments:
            known = sum(bool(self._field(item, field, field.replace("origin", "departure").replace("destination", "arrival"))) for field in required_fields)
            known += sum(bool(self._field(item, field)) for field in ["marketing_carrier_code", "departure_utc", "arrival_utc"])
            completeness_values.append(round(known / 5 * 100))
        itinerary_score = round(sum(completeness_values) / len(completeness_values)) if completeness_values else 0
        fares = await self._active_fares(agency_id, composition_id, option_id)
        priced = [item for item in fares if item.get("price_breakdown_id")]
        commercial_score = min(100, round((len(fares) * 15) + (len(priced) * 20))) if fares else 0
        assessments = await self.db.collection(SERVICE_ASSESSMENT_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id, "option_id": option_id})
        service_score = 100 if assessments and all(item.get("feasibility_status") not in {"unknown", "not_assessed"} for item in assessments) else 50 if assessments else 0
        values = {
            "agency_id": agency_id,
            "composition_id": composition_id,
            "option_id": option_id,
            "leg_count": len({item.get("leg_id") for item in segments if item.get("leg_id")}) or (1 if segments else 0),
            "segment_count": len(segments),
            "stop_count": stop_count,
            "connection_count": connection_count,
            "total_elapsed_minutes": total_elapsed if total_elapsed is None or total_elapsed >= 0 else None,
            "scheduled_flight_minutes": scheduled,
            "total_connection_minutes": sum(value for value in connections if value >= 0),
            "shortest_connection_minutes": min(connections) if connections else None,
            "longest_connection_minutes": max(connections) if connections else None,
            "departure_at": departure,
            "arrival_at": arrival,
            "overnight_indicator": overnight,
            "overnight_connection_indicator": overnight_connection,
            "date_change_indicator": date_change,
            "timezone_change_indicator": timezone_change,
            "airport_change_indicator": airport_change,
            "terminal_change_indicator": terminal_change,
            "separate_ticket_indicator": any(bool((item.get("metadata") or {}).get("separate_ticket")) for item in segments),
            "self_transfer_indicator": any(bool((item.get("metadata") or {}).get("self_transfer")) for item in segments),
            "surface_sector_indicator": surface,
            "technical_stop_indicator": technical,
            "interline_indicator": interline,
            "codeshare_indicator": codeshare,
            "route_classification": route_classification,
            "marketing_carriers": marketing,
            "operating_carriers": operating,
            "validating_carrier": option.get("metadata", {}).get("validating_carrier"),
            "itinerary_completeness_score": itinerary_score,
            "commercial_completeness_score": commercial_score,
            "service_completeness_score": service_score,
            "operational_review_required": bool(warnings),
            "warning_codes": self._tokens(warnings),
            "calculation_trace": {
                "source_assignment_ids": [item["id"] for item in assignments],
                "connection_minutes": connections,
                "minimum_connection_time_asserted": False,
                "calculation_method": "deterministic_schedule_projection",
            },
        }
        stored = await self.db.collection(METRIC_COLLECTION).insert_one(JourneyOptionMetricSnapshot(**values).model_dump(mode="json"))
        status = "incomplete" if not segments else "requires_review" if warnings else "complete"
        updated = await self.db.collection(OPTION_COLLECTION).update_one({"id": option_id, "agency_id": agency_id}, {
            "metric_snapshot_id": stored["id"], "status": status, "requires_review": bool(warnings),
            "warning_codes": self._tokens(warnings), "route_summary": self._route_summary(segments),
            "carrier_summary": ", ".join(marketing or operating) or "Carrier unknown",
            "operational_summary": f"{len(segments)} segments, {connection_count} connections, {route_classification.replace('_', ' ')}",
        })
        await self._refresh_composition(composition)
        return {"phase": PHASE_LABEL, "metric_snapshot": stored, "option": updated, "minimum_connection_time_asserted": False, **self.safety_flags()}

    async def create_manual_fare_brand(self, agency_id: str, composition_id: str, option_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        data.update({"source_type": "agency_manual", "manual_entry": True})
        data.setdefault("uncertainty_status", "requires_review")
        data.setdefault("requires_review", True)
        return await self._create_fare_choice(agency_id, composition_id, option_id, data, user)

    async def import_fare_brand(self, agency_id: str, composition_id: str, option_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_composition(agency_id, composition_id)
        await self._require_option(agency_id, composition_id, option_id)
        data = payload_dict(payload)
        family_id = str(data.get("fare_family_id") or "")
        intelligence = AirlineFareFamilyBrandIntelligenceService(self.db)
        families = await intelligence.list_agency_records("fare-families", agency_id)
        visible_family = next((item for item in families if item.get("id") == family_id or item.get("family_code") == family_id or item.get("brand_code") == family_id), None)
        if not visible_family:
            raise JourneyOptionCompositionError("Published governed fare-family metadata was not found for this agency.")
        raw_family = await self.db.collection("airline_fare_families").find_one({"id": visible_family["id"]})
        family = raw_family or visible_family
        attributes = [item for item in await intelligence.list_agency_records("attributes", agency_id, airline_code=family.get("airline_code")) if item.get("fare_family_id") == family["id"]]
        attribute_by_code = {item.get("attribute_code"): item for item in attributes}
        baggage = await intelligence.resolve_baggage({
            "airline_code": family.get("airline_code"), "fare_family_id": family["id"], "brand_code": family.get("brand_code") or family.get("family_code"),
            "cabin": data.get("cabin") or family.get("cabin"), "rbd_code": data.get("booking_class"),
            "marketing_carrier": family.get("airline_code"), "operating_carrier": data.get("operating_carrier") or family.get("airline_code"),
        }, agency_id=agency_id, agency_safe=True)
        safe_evidence = await intelligence.list_agency_records("evidence-links", agency_id, airline_code=family.get("airline_code"))
        evidence_ids = set(family.get("evidence_link_ids") or [])
        evidence_refs = [item["id"] for item in safe_evidence if item.get("id") in evidence_ids]
        included = [item.get("attribute_code") for item in attributes if item.get("included") is True or item.get("attribute_status") == "included"]
        excluded = [item.get("attribute_code") for item in attributes if item.get("included") is False or item.get("attribute_status") in {"excluded", "not_included"}]
        variable = [item.get("attribute_code") for item in attributes if item.get("attribute_status") in {"unknown", "variable", "conditional"}]
        choice = {
            **data,
            "airline_id": family.get("airline_id"),
            "airline_code": family.get("airline_code"),
            "fare_family_id": family["id"],
            "fare_brand_attribute_refs": [item["id"] for item in attributes],
            "external_brand_name": family.get("commercial_name") or family.get("family_name"),
            "client_safe_label": data.get("client_safe_label") or family.get("client_safe_label") or family.get("commercial_name") or family.get("family_name"),
            "cabin": data.get("cabin") or family.get("cabin"),
            "baggage_summary": baggage.get("allowance_summary"),
            "carry_on_summary": self._carry_on_summary(baggage.get("allowance") or {}),
            "seat_selection_inclusion": self._attribute_status(attribute_by_code.get("seat_selection")),
            "meal_inclusion": self._attribute_status(attribute_by_code.get("meals")),
            "lounge_inclusion": self._attribute_status(attribute_by_code.get("lounge")),
            "priority_check_in": self._attribute_status(attribute_by_code.get("priority_check_in")),
            "priority_boarding": self._attribute_status(attribute_by_code.get("priority_boarding")),
            "fast_track": self._attribute_status(attribute_by_code.get("fast_track")),
            "refundability": self._attribute_status(attribute_by_code.get("refundability")),
            "changeability": self._attribute_status(attribute_by_code.get("changeability")),
            "included_service_codes": self._tokens([*(data.get("included_service_codes") or []), *included]),
            "excluded_service_codes": self._tokens([*(data.get("excluded_service_codes") or []), *excluded]),
            "optional_service_codes": self._tokens([*(data.get("optional_service_codes") or []), *variable]),
            "evidence_refs": evidence_refs,
            "knowledge_version_refs": self._tokens([*(data.get("knowledge_version_refs") or []), *((family.get("metadata") or {}).get("knowledge_version_ids") or [])]),
            "source_type": "governed_fare_intelligence",
            "source_provenance": {"fare_family_id": family["id"], "attribute_ids": [item["id"] for item in attributes], "baggage_rule": baggage.get("applied_rule"), "restricted_evidence_removed": len(evidence_ids) != len(evidence_refs)},
            "manual_entry": False,
            "uncertainty_status": "requires_review" if baggage.get("manual_review_required") or variable or family.get("freshness_status") in {"stale", "expired", "review_due", "unknown"} else "confirmed",
            "requires_review": bool(baggage.get("manual_review_required") or variable or family.get("freshness_status") in {"stale", "expired", "review_due", "unknown"}),
        }
        return await self._create_fare_choice(agency_id, composition_id, option_id, choice, user)

    async def duplicate_fare_brand(self, agency_id: str, composition_id: str, option_id: str, fare_choice_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_composition(agency_id, composition_id)
        source = await self._require_fare(agency_id, composition_id, option_id, fare_choice_id)
        overrides = payload_dict(payload)
        copied = {
            key: value
            for key, value in source.items()
            if key not in {"id", "created_at", "updated_at", "display_order", "price_breakdown_id", "archived_at"}
        }
        copied.update(overrides)
        copied.update({
            "price_breakdown_id": None,
            "archived_at": None,
            "source_provenance": {**(source.get("source_provenance") or {}), "cloned_from_fare_choice_id": fare_choice_id},
        })
        result = await self._create_fare_choice(agency_id, composition_id, option_id, copied, user)
        created = result["fare_brand_choice"]
        source_price = await self.db.collection(PRICE_COLLECTION).find_one({"agency_id": agency_id, "fare_choice_id": fare_choice_id})
        if source_price:
            copied_price = {
                key: value
                for key, value in source_price.items()
                if key not in {"id", "created_at", "updated_at", "fare_choice_id"}
            }
            copied_price.update({"fare_choice_id": created["id"], "option_id": option_id})
            stored_price = await self.db.collection(PRICE_COLLECTION).insert_one(
                JourneyCommercialPriceBreakdown(**copied_price).model_dump(mode="json")
            )
            created = await self.db.collection(FARE_CHOICE_COLLECTION).update_one(
                {"id": created["id"], "agency_id": agency_id},
                {"price_breakdown_id": stored_price["id"]},
            )
        await self._audit(
            "journey_option_composition.fare_brand_duplicated",
            created,
            user,
            {"source_fare_choice_id": fare_choice_id},
        )
        return {"phase": PHASE_LABEL, "fare_brand_choice": created, "source_fare_choice_id": fare_choice_id, **self.safety_flags()}

    async def update_fare_brand(self, agency_id: str, composition_id: str, option_id: str, fare_choice_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_composition(agency_id, composition_id)
        choice = await self._require_fare(agency_id, composition_id, option_id, fare_choice_id)
        immutable = {"id", "agency_id", "composition_id", "option_id", "created_at", "source_type", "source_provenance", "fare_family_id"}
        updates = {key: value for key, value in payload_dict(payload).items() if key not in immutable}
        if "uncertainty_status" in updates:
            self._choice(updates["uncertainty_status"], UNCERTAINTY_STATUSES, "uncertainty status")
        validated = JourneyFareBrandChoice(**{**choice, **updates}).model_dump(mode="json")
        stored = await self.db.collection(FARE_CHOICE_COLLECTION).update_one({"id": fare_choice_id, "agency_id": agency_id}, validated)
        await self._audit("journey_option_composition.fare_brand_updated", stored or choice, user)
        return {"phase": PHASE_LABEL, "fare_brand_choice": stored or choice, **self.safety_flags()}

    async def reorder_fare_brands(self, agency_id: str, composition_id: str, option_id: str, fare_choice_ids: list[str], user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_composition(agency_id, composition_id)
        fares = await self._active_fares(agency_id, composition_id, option_id)
        if set(fare_choice_ids) != {item["id"] for item in fares} or len(fare_choice_ids) != len(fares):
            raise JourneyOptionCompositionError("Reorder must include every active fare-brand choice exactly once.")
        items = []
        for order, fare_id in enumerate(fare_choice_ids, start=1):
            items.append(await self.db.collection(FARE_CHOICE_COLLECTION).update_one({"id": fare_id, "agency_id": agency_id}, {"display_order": order}))
        await self._audit("journey_option_composition.fare_brands_reordered", await self._require_option(agency_id, composition_id, option_id), user, {"fare_choice_ids": fare_choice_ids})
        return {"phase": PHASE_LABEL, "items": items, **self.safety_flags()}

    async def archive_fare_brand(self, agency_id: str, composition_id: str, option_id: str, fare_choice_id: str, user: dict[str, Any]) -> dict[str, Any]:
        return await self._set_fare_archive(agency_id, composition_id, option_id, fare_choice_id, True, user)

    async def restore_fare_brand(self, agency_id: str, composition_id: str, option_id: str, fare_choice_id: str, user: dict[str, Any]) -> dict[str, Any]:
        return await self._set_fare_archive(agency_id, composition_id, option_id, fare_choice_id, False, user)

    async def set_price_breakdown(self, agency_id: str, composition_id: str, option_id: str, fare_choice_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_composition(agency_id, composition_id)
        choice = await self._require_fare(agency_id, composition_id, option_id, fare_choice_id)
        data = payload_dict(payload)
        existing = await self.db.collection(PRICE_COLLECTION).find_one({"agency_id": agency_id, "fare_choice_id": fare_choice_id})
        combined = {**(existing or {}), **data}
        validation = self.validate_price_arithmetic(combined, existing=existing)
        currency = validation["currency"]
        amounts = validation["amounts"]
        calculated = validation["calculated_total"]
        values = {
            **combined,
            **{key: float(value) for key, value in amounts.items()},
            "agency_id": agency_id,
            "composition_id": composition_id,
            "option_id": option_id,
            "fare_choice_id": fare_choice_id,
            "currency": currency,
            "total_selling_amount": float(calculated),
            "passenger_count": max(1, int(combined.get("passenger_count") or 1)),
            "calculation_trace": {
                "formula": "(base_amount or supplier_amount) + tax + ancillary + service_fee + ticketing_fee + assistance_fee + markup - discount",
                "calculated_total": float(calculated),
                "arithmetic_valid": True,
                "source_ref": combined.get("source_ref"),
            },
        }
        model = JourneyCommercialPriceBreakdown(**values).model_dump(mode="json")
        stored = await self.db.collection(PRICE_COLLECTION).update_one({"id": existing["id"], "agency_id": agency_id}, model) if existing else await self.db.collection(PRICE_COLLECTION).insert_one(model)
        await self.db.collection(FARE_CHOICE_COLLECTION).update_one({"id": choice["id"], "agency_id": agency_id}, {"price_breakdown_id": stored["id"], "ticketing_deadline": stored.get("ticketing_deadline")})
        await self.calculate_option_metrics(agency_id, composition_id, option_id)
        await self._audit("journey_option_composition.price_saved", stored, user)
        return {"phase": PHASE_LABEL, "price_breakdown": stored, "arithmetic_valid": True, **self.safety_flags()}

    def validate_price_arithmetic(self, payload: Any, *, existing: dict[str, Any] | None = None) -> dict[str, Any]:
        combined = {**(existing or {}), **payload_dict(payload)}
        currency = str(combined.get("currency") or "").upper().strip()
        if len(currency) != 3 or not currency.isalpha():
            raise JourneyOptionCompositionError("A three-letter currency code is required.")
        if existing and existing.get("currency") and existing.get("currency") != currency and not combined.get("conversion_metadata"):
            raise JourneyOptionCompositionError("Currency changes require explicit conversion metadata.")
        amount_fields = ["supplier_amount", "base_amount", "tax_amount", "ancillary_amount", "service_fee", "ticketing_fee", "assistance_fee", "markup_amount", "discount_amount"]
        amounts = {field: self._money(combined.get(field, 0), field) for field in amount_fields}
        if any(value < 0 for value in amounts.values()):
            raise JourneyOptionCompositionError("Commercial amounts must be non-negative; use discount_amount for a discount or explicit credit metadata.")
        commercial_base = amounts["base_amount"] if amounts["base_amount"] else amounts["supplier_amount"]
        calculated = commercial_base + amounts["tax_amount"] + amounts["ancillary_amount"] + amounts["service_fee"] + amounts["ticketing_fee"] + amounts["assistance_fee"] + amounts["markup_amount"] - amounts["discount_amount"]
        supplied_total = self._money(combined.get("total_selling_amount", calculated), "total_selling_amount")
        if abs(supplied_total - calculated) > Decimal("0.01"):
            raise JourneyOptionCompositionError(f"Total selling amount is inconsistent; deterministic total is {calculated:.2f} {currency}.")
        return {"currency": currency, "amounts": amounts, "calculated_total": calculated, "supplied_total": supplied_total}

    async def project_service_assessments(self, agency_id: str, composition_id: str, user: dict[str, Any]) -> dict[str, Any]:
        composition = await self._require_editable_composition(agency_id, composition_id)
        services = await self.db.collection("journey_service_presentations").find_many({"agency_id": agency_id, "journey_id": composition["journey_id"]})
        options = await self._active_options(agency_id, composition_id)
        created = []
        for option in options:
            metrics = await self._latest_metric(agency_id, composition_id, option["id"])
            carriers = (metrics or {}).get("operating_carriers") or (metrics or {}).get("marketing_carriers") or []
            contact_matches = await self._contact_matches(agency_id, carriers)
            option_services = [item for item in services if not item.get("itinerary_option_id") or item.get("itinerary_option_id") == (option.get("metadata") or {}).get("canonical_itinerary_option_id")]
            for service in option_services:
                feasibility = service.get("feasibility_status") or "unknown"
                confirmation = service.get("confirmation_status") or "unknown"
                interline = bool((metrics or {}).get("interline_indicator"))
                warning_codes = self._tokens([
                    *(service.get("operational_warning_codes") or []),
                    "service_feasibility_unknown" if feasibility in {"unknown", "not_assessed"} else None,
                    "airline_confirmation_required" if service.get("approval_required") or confirmation in {"unknown", "pending", "required"} else None,
                    "interline_service_continuity_unknown" if interline else None,
                ])
                manual = bool(warning_codes or service.get("approval_required"))
                values = {
                    "agency_id": agency_id,
                    "composition_id": composition_id,
                    "option_id": option["id"],
                    "passenger_id": service.get("passenger_id"),
                    "service_request_id": service.get("id"),
                    "service_code": service.get("service_code") or "UNKNOWN",
                    "assessment_status": "projected",
                    "feasibility_status": feasibility,
                    "airline_capability_status": (service.get("metadata") or {}).get("airline_capability_status", "unknown"),
                    "airline_confirmation_required": bool(service.get("approval_required") or confirmation in {"unknown", "pending", "required"}),
                    "ssr_required": bool(service.get("SSR_codes")),
                    "osi_required": bool(service.get("OSI_text_references")),
                    "emd_required": bool(service.get("EMD_required")),
                    "document_required": bool(service.get("document_required")),
                    "manual_contact_required": manual,
                    "contact_match_exists": bool(contact_matches),
                    "baggage_continuity_status": "unknown" if interline else "single_carrier_or_not_assessed",
                    "assistance_continuity_status": "unknown" if interline else confirmation,
                    "policy_ownership_status": "requires_operating_carrier_review" if interline else "not_assessed",
                    "knowledge_freshness_status": (service.get("metadata") or {}).get("freshness_status", "unknown"),
                    "critical_knowledge_gap": bool((service.get("metadata") or {}).get("critical_knowledge_gap")),
                    "evidence_refs": self._tokens([service.get("evidence_trace_reference_id")]),
                    "warning_codes": warning_codes,
                    "client_safe_summary": service.get("client_safe_summary") or "Airline confirmation and service availability remain subject to review.",
                    "internal_summary": service.get("internal_summary") or "Projected from canonical Journey service metadata; no airline acceptance is asserted.",
                    "metadata": {"source_journey_service_presentation_id": service.get("id"), "carrier_codes": carriers, "contact_match_ids": [item["id"] for item in contact_matches]},
                }
                created.append(await self.db.collection(SERVICE_ASSESSMENT_COLLECTION).insert_one(JourneyOptionServiceAssessment(**values).model_dump(mode="json")))
            await self.calculate_option_metrics(agency_id, composition_id, option["id"])
        await self._audit("journey_option_composition.services_assessed", composition, user, {"assessment_ids": [item["id"] for item in created]})
        return {"phase": PHASE_LABEL, "items": created, "count": len(created), "airline_acceptance_guaranteed": False, **self.safety_flags()}

    async def generate_comparison(self, agency_id: str, composition_id: str, payload: Any = None) -> dict[str, Any]:
        composition = await self._require_composition(agency_id, composition_id)
        data = payload_dict(payload)
        options = await self._active_options(agency_id, composition_id)
        if not options:
            raise JourneyOptionCompositionError("At least one active itinerary option is required for comparison.")
        profile = await self._comparison_profile(agency_id, composition_id, data)
        rows: list[dict[str, Any]] = []
        for option in options:
            metric = await self._latest_metric(agency_id, composition_id, option["id"])
            if not metric:
                metric = (await self.calculate_option_metrics(agency_id, composition_id, option["id"]))["metric_snapshot"]
            fares = await self._active_fares(agency_id, composition_id, option["id"])
            assessments = await self.db.collection(SERVICE_ASSESSMENT_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id, "option_id": option["id"]})
            if not fares:
                rows.append(self._comparison_row(option, metric, None, None, assessments))
            for fare in fares:
                price = await self.db.collection(PRICE_COLLECTION).find_one({"agency_id": agency_id, "fare_choice_id": fare["id"]})
                rows.append(self._comparison_row(option, metric, fare, price, assessments))
        known_prices = [row for row in rows if row.get("total_price") is not None]
        known_durations = [row for row in rows if row.get("total_elapsed_minutes") is not None]
        lowest_rows = self._minimum_rows(known_prices, "total_price")
        shortest_rows = self._minimum_rows(known_durations, "total_elapsed_minutes")
        fewest_rows = self._minimum_rows(rows, "stops")
        tie_dimensions = self._tokens([
            "total_price" if len(lowest_rows) > 1 else None,
            "total_elapsed_time" if len(shortest_rows) > 1 else None,
            "stops" if len(fewest_rows) > 1 else None,
        ])
        unknown_dimensions = []
        for dimension, field in [("total_price", "total_price"), ("duration", "total_elapsed_minutes"), ("baggage", "baggage"), ("service_feasibility", "special_service_feasibility")]:
            if any(row.get(field) in {None, "unknown", "not_assessed"} for row in rows):
                unknown_dimensions.append(dimension)
        human = [{
            "option": row["option_label"], "fare_brand": row.get("fare_brand") or "Fare brand not supplied",
            "price": f"{row['currency']} {row['total_price']:.2f}" if row.get("currency") and row.get("total_price") is not None else "Price unknown",
            "journey": f"{self._duration(row.get('total_elapsed_minutes'))}, {row.get('stops')} stops",
            "baggage": row.get("baggage") or "Baggage unknown",
            "flexibility": f"Changes {row.get('changeability')}; refunds {row.get('refundability')}",
            "warnings": row.get("operational_warnings") or [],
        } for row in rows]
        normalized = self._normalize_for_hash(rows)
        values = {
            "agency_id": agency_id,
            "composition_id": composition_id,
            "comparison_profile_id": profile["id"],
            "option_ids": [item["id"] for item in options],
            "structured_rows": rows,
            "human_readable_rows": human,
            "lowest_price_option_id": lowest_rows[0]["option_id"] if len(lowest_rows) == 1 else None,
            "shortest_duration_option_id": shortest_rows[0]["option_id"] if len(shortest_rows) == 1 else None,
            "fewest_stops_option_id": fewest_rows[0]["option_id"] if len(fewest_rows) == 1 else None,
            "best_baggage_option_id": self._best_baggage(rows),
            "preferred_option_id": composition.get("preferred_option_id"),
            "tie_dimensions": tie_dimensions,
            "unknown_dimensions": unknown_dimensions,
            "content_hash": self._hash(normalized),
        }
        stored = await self.db.collection(COMPARISON_RESULT_COLLECTION).insert_one(JourneyOptionComparisonResult(**values).model_dump(mode="json"))
        return {"phase": PHASE_LABEL, "comparison_result": stored, "deterministic_hints_only": True, "recommended_option_asserted": False, **self.safety_flags()}

    async def select_preferred_option(self, agency_id: str, composition_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        composition = await self._require_editable_composition(agency_id, composition_id)
        data = payload_dict(payload)
        option = await self._require_option(agency_id, composition_id, str(data.get("option_id") or ""))
        fare_id = data.get("fare_choice_id")
        if fare_id:
            await self._require_fare(agency_id, composition_id, option["id"], str(fare_id))
        updates = {
            "preferred_option_id": option["id"], "preferred_fare_choice_id": fare_id,
            "client_rationale": data.get("client_rationale"), "internal_decision_notes": data.get("internal_decision_notes"),
            "updated_by": self._actor(user),
        }
        stored = await self.db.collection(COMPOSITION_COLLECTION).update_one({"id": composition_id, "agency_id": agency_id}, updates)
        await self._audit("journey_option_composition.preferred_selected", stored or composition, user, {"agent_selected": True})
        return {"phase": PHASE_LABEL, "composition": stored or composition, "agent_selected": True, "automatic_recommendation": False, **self.safety_flags()}

    async def create_snapshot(self, agency_id: str, composition_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        composition = await self._require_composition(agency_id, composition_id)
        data = payload_dict(payload)
        existing = await self.list_snapshots(agency_id, composition_id)
        number = max([int(item.get("snapshot_number") or 0) for item in existing] or [0]) + 1
        complete = await self.get_composition(agency_id, composition_id)
        snapshot_payload = self._normalize_for_hash({key: value for key, value in complete.items() if key not in {"snapshots", "offer_handoffs", "comparison_results"}})
        evidence = self._tokens([ref for item in complete["fare_brand_choices"] for ref in item.get("evidence_refs") or []] + [ref for item in complete["service_assessments"] for ref in item.get("evidence_refs") or []])
        versions = self._tokens([ref for item in complete["fare_brand_choices"] for ref in item.get("knowledge_version_refs") or []])
        finalize = bool(data.get("finalize", False))
        values = {
            "agency_id": agency_id,
            "composition_id": composition_id,
            "journey_id": composition["journey_id"],
            "snapshot_number": number,
            "snapshot_status": "finalized" if finalize else "draft",
            "snapshot_payload": snapshot_payload,
            "source_refs": composition.get("source_refs") or [],
            "evidence_refs": evidence,
            "knowledge_version_refs": versions,
            "content_hash": self._hash(snapshot_payload),
            "finalized": finalize,
            "finalized_at": self._now() if finalize else None,
            "finalized_by": self._actor(user) if finalize else None,
            "created_by": self._actor(user),
            "metadata": data.get("metadata") or {},
        }
        stored = await self.db.collection(SNAPSHOT_COLLECTION).insert_one(JourneyOptionCompositionSnapshot(**values).model_dump(mode="json"))
        await self.db.collection(COMPOSITION_COLLECTION).update_one({"id": composition_id, "agency_id": agency_id}, {"status": "snapshotted", "updated_by": self._actor(user)})
        await self._audit("journey_option_composition.snapshot_created", stored, user)
        return {"phase": PHASE_LABEL, "snapshot": stored, **self.safety_flags()}

    async def finalize_snapshot(self, agency_id: str, composition_id: str, snapshot_id: str, user: dict[str, Any]) -> dict[str, Any]:
        snapshot = await self._require_snapshot(agency_id, composition_id, snapshot_id)
        if snapshot.get("finalized") or snapshot.get("finalized_at"):
            raise FinalizedCompositionSnapshotError("Finalized composition snapshots are immutable and cannot be finalized again.")
        stored = await self.db.collection(SNAPSHOT_COLLECTION).update_one({"id": snapshot_id, "agency_id": agency_id}, {
            "snapshot_status": "finalized", "finalized": True, "finalized_at": self._now(), "finalized_by": self._actor(user),
        })
        await self._audit("journey_option_composition.snapshot_finalized", stored or snapshot, user)
        return {"phase": PHASE_LABEL, "snapshot": stored or snapshot, **self.safety_flags()}

    async def update_snapshot(self, agency_id: str, composition_id: str, snapshot_id: str, payload: Any) -> dict[str, Any]:
        snapshot = await self._require_snapshot(agency_id, composition_id, snapshot_id)
        if snapshot.get("finalized") or snapshot.get("finalized_at"):
            raise FinalizedCompositionSnapshotError("Finalized composition snapshots are immutable and cannot be edited.")
        updates = {key: value for key, value in payload_dict(payload).items() if key in {"snapshot_status", "metadata"}}
        stored = await self.db.collection(SNAPSHOT_COLLECTION).update_one({"id": snapshot_id, "agency_id": agency_id}, updates)
        return {"phase": PHASE_LABEL, "snapshot": stored or snapshot, **self.safety_flags()}

    async def list_snapshots(self, agency_id: str, composition_id: str) -> list[dict[str, Any]]:
        await self._require_composition(agency_id, composition_id)
        items = await self.db.collection(SNAPSHOT_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id})
        return sorted(items, key=lambda item: int(item.get("snapshot_number") or 0), reverse=True)

    async def preview_offer_handoff(self, agency_id: str, composition_id: str, payload: Any) -> dict[str, Any]:
        composition = await self._require_composition(agency_id, composition_id)
        data = payload_dict(payload)
        snapshot = await self._select_snapshot(agency_id, composition_id, data.get("snapshot_id"))
        offer_id = data.get("offer_id") or data.get("offer_workspace_id") or composition.get("offer_id") or composition.get("offer_workspace_id")
        offer = await self._find_offer(agency_id, str(offer_id)) if offer_id else None
        options = await self._active_options(agency_id, composition_id)
        fares = await self.db.collection(FARE_CHOICE_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id})
        warnings = []
        if not snapshot.get("finalized"):
            warnings.append("Composition snapshot is not finalized.")
        if not offer:
            warnings.append("No existing agency offer workspace is selected.")
        preview = {
            "snapshot_id": snapshot["id"],
            "offer_id": offer.get("id") if offer else None,
            "option_links": [{"composition_option_id": item["id"], "route_alternative_id": None, "action": "link_or_create_metadata_on_explicit_apply"} for item in options],
            "fare_links": [{"fare_choice_id": item["id"], "fare_option_id": None, "action": "link_or_create_metadata_on_explicit_apply"} for item in fares if not item.get("archived_at")],
            "warnings": warnings,
            "prohibited_actions": ["publish", "send", "accept", "book", "ticket", "issue_emd", "contact_provider"],
            "source_snapshot_immutable": bool(snapshot.get("finalized")),
        }
        return {"phase": PHASE_LABEL, "preview": preview, "can_apply": bool(snapshot.get("finalized") and offer), "automatic_action_performed": False, **self.safety_flags()}

    async def apply_offer_handoff(self, agency_id: str, composition_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        preview = await self.preview_offer_handoff(agency_id, composition_id, data)
        if not preview["can_apply"]:
            raise JourneyOptionCompositionError("Offer handoff requires a finalized composition snapshot and an existing agency offer workspace.")
        existing = await self.db.collection(HANDOFF_COLLECTION).find_one({"agency_id": agency_id, "composition_id": composition_id, "snapshot_id": preview["preview"]["snapshot_id"], "offer_workspace_id": preview["preview"]["offer_id"]})
        if existing:
            return {"phase": PHASE_LABEL, "offer_handoff": existing, "created": False, **self.safety_flags()}
        values = {
            "agency_id": agency_id,
            "composition_id": composition_id,
            "snapshot_id": preview["preview"]["snapshot_id"],
            "offer_id": data.get("offer_id"),
            "offer_workspace_id": data.get("offer_workspace_id") or preview["preview"]["offer_id"],
            "linked_route_alternative_id": data.get("linked_route_alternative_id"),
            "linked_fare_option_ids": data.get("linked_fare_option_ids") or [],
            "handoff_status": "linked",
            "preview_payload": preview["preview"],
            "route_alternative_links": preview["preview"]["option_links"],
            "fare_option_links": preview["preview"]["fare_links"],
            "created_records": [],
            "warnings": preview["preview"]["warnings"],
            "trace": {"explicit_agent_action": True, "source_snapshot_id": preview["preview"]["snapshot_id"], "offer_records_mutated": False},
            "created_by": self._actor(user),
            "applied_at": self._now(),
        }
        stored = await self.db.collection(HANDOFF_COLLECTION).insert_one(JourneyOptionOfferHandoff(**values).model_dump(mode="json"))
        await self.db.collection(COMPOSITION_COLLECTION).update_one({"id": composition_id, "agency_id": agency_id}, {"status": "prepared_for_offer", "offer_workspace_id": values["offer_workspace_id"], "updated_by": self._actor(user)})
        await self._audit("journey_option_composition.offer_handoff_linked", stored, user)
        return {"phase": PHASE_LABEL, "offer_handoff": stored, "created": True, "offer_records_mutated": False, "provider_execution_performed": False, **self.safety_flags()}

    async def generate_warnings(self, agency_id: str, composition_id: str) -> dict[str, Any]:
        detail = await self.get_composition(agency_id, composition_id)
        warnings: list[dict[str, Any]] = []
        if not [item for item in detail["options"] if not item.get("archived_at")]:
            warnings.append({"code": "missing_itinerary_options", "severity": "blocking", "scope": "composition"})
        for option in detail["options"]:
            if option.get("archived_at"):
                continue
            for code in option.get("warning_codes") or []:
                severity = "blocking" if code in {"missing_active_segments", "invalid_segment_chronology", "negative_connection", "price_arithmetic_invalid"} else "review_required"
                warnings.append({"code": code, "severity": severity, "scope": "option", "option_id": option["id"]})
        for choice in detail["fare_brand_choices"]:
            if not choice.get("archived_at") and choice.get("requires_review"):
                warnings.append({"code": "fare_brand_requires_review", "severity": "review_required", "scope": "fare_brand", "fare_choice_id": choice["id"]})
        for assessment in detail["service_assessments"]:
            for code in assessment.get("warning_codes") or []:
                warnings.append({"code": code, "severity": "review_required", "scope": "service", "assessment_id": assessment["id"]})
        return {"phase": PHASE_LABEL, "items": warnings, "count": len(warnings), "blocking_count": len([item for item in warnings if item["severity"] == "blocking"]), **self.safety_flags()}

    def sanitize_agency_output(self, value: Any) -> Any:
        return self._sanitize(value)

    async def build_readiness_diagnostics(self, agency_id: str | None = None) -> dict[str, Any]:
        return await self.dashboard(agency_id)

    async def summarize_readiness(self, agency_id: str | None = None) -> dict[str, Any]:
        compositions = await self.list_compositions(agency_id, include_archived=True)
        filters = {"agency_id": agency_id} if agency_id else None
        options = await self.db.collection(OPTION_COLLECTION).find_many(filters)
        fares = await self.db.collection(FARE_CHOICE_COLLECTION).find_many(filters)
        prices = await self.db.collection(PRICE_COLLECTION).find_many(filters)
        assessments = await self.db.collection(SERVICE_ASSESSMENT_COLLECTION).find_many(filters)
        comparisons = await self.db.collection(COMPARISON_RESULT_COLLECTION).find_many(filters)
        snapshots = await self.db.collection(SNAPSHOT_COLLECTION).find_many(filters)
        handoffs = await self.db.collection(HANDOFF_COLLECTION).find_many(filters)
        agency_counts: dict[str, int] = {}
        for item in compositions:
            agency_counts[item.get("agency_id") or "unknown"] = agency_counts.get(item.get("agency_id") or "unknown", 0) + 1
        status_counts = {status: len([item for item in compositions if item.get("status") == status]) for status in COMPOSITION_STATUSES}
        warnings = [code for item in options for code in item.get("warning_codes") or []]
        severity = {
            "blocking": len([item for item in warnings if item in {"missing_active_segments", "invalid_segment_chronology", "negative_connection", "price_arithmetic_invalid"}]),
            "review_required": len([item for item in warnings if item not in {"missing_active_segments", "invalid_segment_chronology", "negative_connection", "price_arithmetic_invalid"}]),
            "important": 0,
            "informational": 0,
            "unknown": len([item for item in assessments if item.get("feasibility_status") in {"unknown", "not_assessed"}]),
        }
        return {
            "composition_count": len(compositions),
            "active_composition_count": len([item for item in compositions if not item.get("archived_at")]),
            "incomplete_composition_count": len([item for item in compositions if int(item.get("completeness_score") or 0) < 100]),
            "review_required_composition_count": len([item for item in compositions if item.get("requires_review")]),
            "itinerary_option_count": len(options),
            "fare_brand_choice_count": len(fares),
            "manual_fare_brand_choice_count": len([item for item in fares if item.get("manual_entry")]),
            "imported_fare_brand_choice_count": len([item for item in fares if not item.get("manual_entry")]),
            "price_breakdown_count": len(prices),
            "service_assessment_count": len(assessments),
            "blocking_warning_count": severity["blocking"],
            "comparison_result_count": len(comparisons),
            "snapshot_count": len(snapshots),
            "finalized_snapshot_count": len([item for item in snapshots if item.get("finalized")]),
            "offer_handoff_count": len(handoffs),
            "status_counts": status_counts,
            "warning_severity_counts": severity,
            "agency_counts": agency_counts,
        }

    async def dashboard(self, agency_id: str | None = None) -> dict[str, Any]:
        items = await self.list_compositions(agency_id, include_archived=True)
        recent = items[:20]
        return {
            "phase": PHASE_LABEL,
            "summary": await self.summarize_readiness(agency_id),
            "items": [self._sanitize(item) for item in recent] if agency_id else recent,
            "filters": self.filters(),
            "platform_diagnostics_read_only": agency_id is None,
            "diagnostic": "Phase 56.2 composes canonical Journey segments, governed fare intelligence, explicit agency commercial values, and advisory service assessments into offer-ready alternatives without live fares, availability, publication, provider contact, booking, ticketing, or EMD execution.",
            **self.safety_flags(),
        }

    async def _create_fare_choice(self, agency_id: str, composition_id: str, option_id: str, data: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_composition(agency_id, composition_id)
        await self._require_option(agency_id, composition_id, option_id)
        fares = await self._active_fares(agency_id, composition_id, option_id)
        values = {
            **data,
            "agency_id": agency_id,
            "composition_id": composition_id,
            "option_id": option_id,
            "display_order": int(data.get("display_order") or len(fares) + 1),
            "client_safe_label": data.get("client_safe_label") or data.get("external_brand_name") or "Manual fare choice",
            "source_provenance": data.get("source_provenance") or {"source_type": data.get("source_type") or "agency_manual", "entered_by": self._actor(user)},
        }
        self._choice(values.get("uncertainty_status") or "unknown", UNCERTAINTY_STATUSES, "uncertainty status")
        stored = await self.db.collection(FARE_CHOICE_COLLECTION).insert_one(JourneyFareBrandChoice(**values).model_dump(mode="json"))
        await self._audit("journey_option_composition.fare_brand_created", stored, user)
        return {"phase": PHASE_LABEL, "fare_brand_choice": stored, **self.safety_flags()}

    async def _insert_assignment(self, agency_id: str, composition: dict[str, Any], option: dict[str, Any], data: dict[str, Any], order: int) -> dict[str, Any]:
        segment_id = str(data.get("source_segment_id") or data.get("journey_segment_projection_id") or "")
        source_type = str(data.get("source_segment_type") or "journey_segment_projection")
        if source_type not in {"journey_segment_projection", "journey_segment_representation"}:
            raise JourneyOptionCompositionError("Only canonical Journey segment projections may be assigned to a composition option.")
        segment = await self.db.collection("journey_segment_representations").find_one({"id": segment_id, "agency_id": agency_id})
        if not segment:
            raise JourneyOptionCompositionError("Canonical Journey segment was not found for this agency.")
        if segment.get("journey_id") != composition["journey_id"]:
            raise JourneyOptionCompositionError("Canonical Journey segment belongs to another Journey.")
        active = await self._active_assignments(agency_id, composition["id"], option["id"])
        duplicate = next((item for item in active if item.get("source_segment_id") == segment_id), None)
        if duplicate and not data.get("justification"):
            raise JourneyOptionCompositionError("Duplicate active segment assignment requires explicit justification.")
        values = {
            **data,
            "agency_id": agency_id,
            "composition_id": composition["id"],
            "option_id": option["id"],
            "journey_id": composition["journey_id"],
            "journey_segment_projection_id": segment_id,
            "journey_leg_id": data.get("journey_leg_id") or segment.get("leg_id"),
            "source_segment_type": "journey_segment_projection",
            "source_segment_id": segment_id,
            "display_order": order,
            "included": True,
            "provenance": data.get("provenance") or {"source_collection": "journey_segment_representations", "source_id": segment_id},
        }
        return await self.db.collection(ASSIGNMENT_COLLECTION).insert_one(JourneyOptionSegmentAssignment(**values).model_dump(mode="json"))

    async def _set_option_archive(self, agency_id: str, composition_id: str, option_id: str, archive: bool, user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_composition(agency_id, composition_id)
        option = await self._require_option(agency_id, composition_id, option_id)
        stored = await self.db.collection(OPTION_COLLECTION).update_one({"id": option_id, "agency_id": agency_id}, {
            "status": "archived" if archive else "draft", "archived_at": self._now() if archive else None, "updated_by": self._actor(user),
        })
        await self._audit(f"journey_option_composition.option_{'archived' if archive else 'restored'}", stored or option, user)
        return {"phase": PHASE_LABEL, "option": stored or option, "physical_deletion_performed": False, **self.safety_flags()}

    async def _set_fare_archive(self, agency_id: str, composition_id: str, option_id: str, fare_id: str, archive: bool, user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_composition(agency_id, composition_id)
        fare = await self._require_fare(agency_id, composition_id, option_id, fare_id)
        stored = await self.db.collection(FARE_CHOICE_COLLECTION).update_one({"id": fare_id, "agency_id": agency_id}, {"archived_at": self._now() if archive else None})
        await self._audit(f"journey_option_composition.fare_brand_{'archived' if archive else 'restored'}", stored or fare, user)
        return {"phase": PHASE_LABEL, "fare_brand_choice": stored or fare, "physical_deletion_performed": False, **self.safety_flags()}

    async def _validate_optional_links(self, agency_id: str, data: dict[str, Any]) -> None:
        if data.get("authoring_session_id") and not await self.db.collection("journey_authoring_sessions").find_one({"id": data["authoring_session_id"], "agency_id": agency_id}):
            raise JourneyOptionCompositionError("Journey authoring session was not found for this agency.")
        if data.get("offer_id") or data.get("offer_workspace_id"):
            await self._find_offer(agency_id, str(data.get("offer_workspace_id") or data.get("offer_id")))

    async def _find_offer(self, agency_id: str, offer_id: str) -> dict[str, Any]:
        if not offer_id:
            raise JourneyOptionCompositionError("Offer reference is required.")
        for collection in ["offer_workspaces_v2", "offer_workspaces", "offers"]:
            item = await self.db.collection(collection).find_one({"id": offer_id, "agency_id": agency_id})
            if item:
                return {**item, "_source_collection": collection}
        raise JourneyOptionCompositionError("Offer metadata was not found for this agency.")

    async def _resolve_assignments(self, agency_id: str, assignments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        for assignment in assignments:
            segment = await self.db.collection("journey_segment_representations").find_one({"id": assignment.get("source_segment_id"), "agency_id": agency_id})
            result.append({"assignment": assignment, "segment": segment, "source_missing": segment is None})
        return result

    async def _comparison_profile(self, agency_id: str, composition_id: str, data: dict[str, Any]) -> dict[str, Any]:
        if data.get("comparison_profile_id"):
            profile = await self.db.collection(COMPARISON_PROFILE_COLLECTION).find_one({"id": data["comparison_profile_id"], "agency_id": agency_id, "composition_id": composition_id})
            if not profile:
                raise JourneyOptionCompositionError("Comparison profile was not found for this agency composition.")
            return profile
        existing = await self.db.collection(COMPARISON_PROFILE_COLLECTION).find_one({"agency_id": agency_id, "composition_id": composition_id, "status": "active"})
        if existing:
            return existing
        return await self.db.collection(COMPARISON_PROFILE_COLLECTION).insert_one(JourneyOptionComparisonProfile(
            agency_id=agency_id,
            composition_id=composition_id,
            comparison_dimensions=data.get("comparison_dimensions") or COMPARISON_DIMENSIONS,
            client_visible_dimensions=[item for item in COMPARISON_DIMENSIONS if item not in {"evidence_confidence", "operational_warnings"}],
            internal_dimensions=["evidence_confidence", "operational_warnings"],
        ).model_dump(mode="json"))

    def _comparison_row(self, option: dict[str, Any], metric: dict[str, Any], fare: dict[str, Any] | None, price: dict[str, Any] | None, assessments: list[dict[str, Any]]) -> dict[str, Any]:
        statuses = [item.get("feasibility_status") or "unknown" for item in assessments]
        feasibility = "unsupported" if "unsupported" in statuses else "conditional" if "conditional" in statuses else "unknown" if any(item in {"unknown", "not_assessed"} for item in statuses) or not statuses else "supported"
        return {
            "option_id": option["id"],
            "option_label": option.get("client_safe_label") or option.get("option_code"),
            "fare_choice_id": (fare or {}).get("id"),
            "fare_brand": (fare or {}).get("client_safe_label"),
            "route": option.get("route_summary"),
            "departure_time": metric.get("departure_at"),
            "arrival_time": metric.get("arrival_at"),
            "total_elapsed_minutes": metric.get("total_elapsed_minutes"),
            "stops": metric.get("stop_count", 0),
            "connections": metric.get("connection_count", 0),
            "shortest_connection_minutes": metric.get("shortest_connection_minutes"),
            "airport_change": metric.get("airport_change_indicator", False),
            "terminal_change": metric.get("terminal_change_indicator", False),
            "overnight": metric.get("overnight_indicator", False),
            "currency": (price or {}).get("currency"),
            "total_price": (price or {}).get("total_selling_amount"),
            "baggage": (fare or {}).get("baggage_summary") or "unknown",
            "cabin": (fare or {}).get("cabin") or "unknown",
            "changeability": (fare or {}).get("changeability") or "unknown",
            "refundability": (fare or {}).get("refundability") or "unknown",
            "seats": (fare or {}).get("seat_selection_inclusion") or "unknown",
            "meals": (fare or {}).get("meal_inclusion") or "unknown",
            "lounge": (fare or {}).get("lounge_inclusion") or "unknown",
            "priority_services": self._tokens([(fare or {}).get("priority_check_in"), (fare or {}).get("priority_boarding"), (fare or {}).get("fast_track")]),
            "special_service_feasibility": feasibility,
            "service_confirmation_requirements": self._tokens([item.get("service_code") for item in assessments if item.get("airline_confirmation_required")]),
            "evidence_confidence": "unknown" if not (fare or {}).get("evidence_refs") else "evidence_linked",
            "operational_warnings": self._tokens([*(option.get("warning_codes") or []), *[code for item in assessments for code in item.get("warning_codes") or []]]),
            "client_safe_highlights": (fare or {}).get("client_visible_highlights") or [],
        }

    async def _contact_matches(self, agency_id: str, carriers: list[str]) -> list[dict[str, Any]]:
        contacts = await self.db.collection("airline_contact_directory_entries").find_many()
        return [item for item in contacts if item.get("airline_code") in carriers and item.get("status") in {"active", "verified", "published"} and item.get("agency_id") in {None, agency_id}]

    async def _refresh_composition(self, composition: dict[str, Any]) -> None:
        options = await self._active_options(composition["agency_id"], composition["id"])
        scores = []
        review = False
        for option in options:
            metric = await self._latest_metric(composition["agency_id"], composition["id"], option["id"])
            if metric:
                scores.append(round((int(metric.get("itinerary_completeness_score") or 0) + int(metric.get("commercial_completeness_score") or 0) + int(metric.get("service_completeness_score") or 0)) / 3))
                review = review or bool(metric.get("operational_review_required"))
            else:
                scores.append(0)
        completeness = round(sum(scores) / len(scores)) if scores else 0
        status = "requires_review" if review else "ready" if completeness == 100 and options else "composing"
        await self.db.collection(COMPOSITION_COLLECTION).update_one({"id": composition["id"], "agency_id": composition["agency_id"]}, {"completeness_score": completeness, "requires_review": review, "status": status})

    async def _touch_composition(self, composition: dict[str, Any], user: dict[str, Any], *, status: str | None = None) -> None:
        updates = {"updated_by": self._actor(user)}
        if status and composition.get("status") not in {"snapshotted", "prepared_for_offer", "archived"}:
            updates["status"] = status
        await self.db.collection(COMPOSITION_COLLECTION).update_one({"id": composition["id"], "agency_id": composition["agency_id"]}, updates)

    async def _require_composition(self, agency_id: str, composition_id: str) -> dict[str, Any]:
        item = await self.db.collection(COMPOSITION_COLLECTION).find_one({"id": composition_id, "agency_id": agency_id})
        if not item:
            raise JourneyOptionCompositionError("Journey option composition was not found for this agency.")
        return item

    async def _require_editable_composition(self, agency_id: str, composition_id: str) -> dict[str, Any]:
        item = await self._require_composition(agency_id, composition_id)
        if item.get("archived_at") or item.get("status") == "archived":
            raise JourneyOptionCompositionError("Archived compositions cannot be edited.")
        return item

    async def _require_journey(self, agency_id: str, journey_id: str) -> dict[str, Any]:
        item = await self.db.collection("journey_representations").find_one({"id": journey_id, "agency_id": agency_id})
        if not item:
            raise JourneyOptionCompositionError("Canonical Journey reference was not found for this agency.")
        return item

    async def _require_option(self, agency_id: str, composition_id: str, option_id: str) -> dict[str, Any]:
        item = await self.db.collection(OPTION_COLLECTION).find_one({"id": option_id, "agency_id": agency_id, "composition_id": composition_id})
        if not item:
            raise JourneyOptionCompositionError("Itinerary option was not found for this agency composition.")
        return item

    async def _require_fare(self, agency_id: str, composition_id: str, option_id: str, fare_id: str) -> dict[str, Any]:
        item = await self.db.collection(FARE_CHOICE_COLLECTION).find_one({"id": fare_id, "agency_id": agency_id, "composition_id": composition_id, "option_id": option_id})
        if not item:
            raise JourneyOptionCompositionError("Fare-brand choice was not found for this agency option.")
        return item

    async def _require_snapshot(self, agency_id: str, composition_id: str, snapshot_id: str) -> dict[str, Any]:
        item = await self.db.collection(SNAPSHOT_COLLECTION).find_one({"id": snapshot_id, "agency_id": agency_id, "composition_id": composition_id})
        if not item:
            raise JourneyOptionCompositionError("Composition snapshot was not found for this agency.")
        return item

    async def _select_snapshot(self, agency_id: str, composition_id: str, snapshot_id: str | None) -> dict[str, Any]:
        if snapshot_id:
            return await self._require_snapshot(agency_id, composition_id, snapshot_id)
        snapshots = await self.list_snapshots(agency_id, composition_id)
        finalized = next((item for item in snapshots if item.get("finalized")), None)
        if not finalized:
            raise JourneyOptionCompositionError("A composition snapshot is required for offer handoff preview.")
        return finalized

    async def _options(self, agency_id: str, composition_id: str, *, include_archived: bool = False) -> list[dict[str, Any]]:
        items = await self.db.collection(OPTION_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id})
        if not include_archived:
            items = [item for item in items if not item.get("archived_at")]
        return sorted(items, key=lambda item: int(item.get("display_order") or 0))

    async def _active_options(self, agency_id: str, composition_id: str) -> list[dict[str, Any]]:
        return await self._options(agency_id, composition_id)

    async def _active_assignments(self, agency_id: str, composition_id: str, option_id: str) -> list[dict[str, Any]]:
        items = await self.db.collection(ASSIGNMENT_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id, "option_id": option_id})
        return sorted([item for item in items if item.get("included") and not item.get("archived_at")], key=lambda item: int(item.get("display_order") or 0))

    async def _active_fares(self, agency_id: str, composition_id: str, option_id: str) -> list[dict[str, Any]]:
        items = await self.db.collection(FARE_CHOICE_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id, "option_id": option_id})
        return sorted([item for item in items if not item.get("archived_at")], key=lambda item: int(item.get("display_order") or 0))

    async def _latest_metric(self, agency_id: str, composition_id: str, option_id: str) -> dict[str, Any] | None:
        option = await self._require_option(agency_id, composition_id, option_id)
        if option.get("metric_snapshot_id"):
            item = await self.db.collection(METRIC_COLLECTION).find_one({"id": option["metric_snapshot_id"], "agency_id": agency_id})
            if item:
                return item
        items = await self.db.collection(METRIC_COLLECTION).find_many({"agency_id": agency_id, "composition_id": composition_id, "option_id": option_id})
        return sorted(items, key=lambda item: str(item.get("calculated_at") or item.get("created_at") or ""), reverse=True)[0] if items else None

    def _source_refs(self, data: dict[str, Any], journey: dict[str, Any]) -> list[dict[str, Any]]:
        refs = list(data.get("source_refs") or [])
        refs.append({"type": "journey", "id": journey["id"], "reference": journey.get("journey_reference")})
        for key in ["authoring_session_id", "request_id", "trip_id", "offer_id", "offer_workspace_id"]:
            if data.get(key):
                refs.append({"type": key.removesuffix("_id"), "id": data[key]})
        return refs

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, list):
            return [self._sanitize(item) for item in value]
        if not isinstance(value, dict):
            return value
        sanitized = {}
        for key, item in value.items():
            if key in INTERNAL_FIELDS:
                continue
            if key == "evidence_refs":
                sanitized[key] = list(item or [])
            else:
                sanitized[key] = self._sanitize(item)
        sanitized.setdefault("client_safe", True)
        return sanitized

    def _normalize_for_hash(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._normalize_for_hash(item) for key, item in sorted(value.items()) if key not in {"updated_at", "generated_at"}}
        if isinstance(value, list):
            return [self._normalize_for_hash(item) for item in value]
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value

    def _hash(self, value: Any) -> str:
        return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()

    def _money(self, value: Any, field: str) -> Decimal:
        try:
            return Decimal(str(value or 0)).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise JourneyOptionCompositionError(f"{field} must be a valid monetary amount.") from exc

    def _choice(self, value: Any, allowed: list[str], label: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in allowed:
            raise JourneyOptionCompositionError(f"Unsupported {label}: {value}.")
        return normalized

    def _field(self, item: dict[str, Any], *names: str) -> Any:
        return next((item.get(name) for name in names if item.get(name) is not None), None)

    def _segment_type(self, item: dict[str, Any]) -> str:
        return str(item.get("segment_type") or "flight").lower()

    def _dt(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
        except ValueError:
            return None

    def _minutes(self, start: datetime, end: datetime) -> int:
        return round((end - start).total_seconds() / 60)

    def _date_change(self, item: dict[str, Any]) -> bool:
        start = self._dt(self._field(item, "departure_local", "departure_local_datetime"))
        end = self._dt(self._field(item, "arrival_local", "arrival_local_datetime"))
        return bool(start and end and end.date() > start.date())

    def _route_summary(self, segments: list[dict[str, Any]]) -> str:
        if not segments:
            return "Route unresolved"
        points = [self._field(segments[0], "origin_airport_code", "departure_airport_code") or "???"]
        points.extend(self._field(item, "destination_airport_code", "arrival_airport_code") or "???" for item in segments)
        return " - ".join(points)

    def _tokens(self, values: Any) -> list[str]:
        result = []
        for value in values or []:
            if value is None:
                continue
            token = str(value).strip()
            if token and token not in result:
                result.append(token)
        return result

    def _alpha(self, index: int) -> str:
        return chr(65 + max(0, index) % 26)

    def _attribute_status(self, item: dict[str, Any] | None) -> str:
        if not item:
            return "unknown"
        if item.get("included") is True:
            return "included"
        if item.get("included") is False:
            return "not_included"
        return str(item.get("attribute_status") or "unknown")

    def _carry_on_summary(self, allowance: dict[str, Any]) -> str:
        if allowance.get("cabin_baggage_pieces") is None:
            return "Carry-on allowance unknown"
        weight = f" up to {allowance['cabin_baggage_weight_kg']:g} kg" if allowance.get("cabin_baggage_weight_kg") is not None else ""
        personal = "; personal item included" if allowance.get("personal_item_included") else ""
        return f"{allowance['cabin_baggage_pieces']} cabin bag{weight}{personal}"

    def _minimum_rows(self, rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
        known = [item for item in rows if item.get(field) is not None]
        if not known:
            return []
        value = min(item[field] for item in known)
        return [item for item in known if item[field] == value]

    def _best_baggage(self, rows: list[dict[str, Any]]) -> str | None:
        known = [item for item in rows if item.get("baggage") not in {None, "unknown", "Baggage allowance unknown; verify fare basis and operating-carrier rules."}]
        option_ids = self._tokens([item["option_id"] for item in known])
        return option_ids[0] if len(option_ids) == 1 else None

    def _duration(self, value: int | None) -> str:
        if value is None:
            return "Duration unknown"
        return f"{value // 60}h {value % 60}m"

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
            "target_type": "journey_option_composition",
            "target_id": target.get("id"),
            "metadata_json": metadata or {},
            "created_at": self._now(),
            "updated_at": self._now(),
        })
