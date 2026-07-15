from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any, Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel

from database import Database
from models import (
    JourneyAuthoringApplication,
    JourneyAuthoringCorrection,
    JourneyAuthoringSession,
    JourneyAuthoringTemplate,
    JourneyAuthoringValidation,
    JourneyFieldProvenance,
    JourneyImportSource,
    JourneySegmentDraft,
    new_id,
)
from services.canonical_journey_itinerary_service import CanonicalJourneyItineraryService
from services.gds_parser_service import GdsParserService


PHASE_LABEL = "phase_56_2_journey_option_fare_brand_composition_workspace_foundation"

SESSION_COLLECTION = "journey_authoring_sessions"
SOURCE_COLLECTION = "journey_import_sources"
DRAFT_COLLECTION = "journey_segment_drafts"
PROVENANCE_COLLECTION = "journey_field_provenance"
CORRECTION_COLLECTION = "journey_authoring_corrections"
VALIDATION_COLLECTION = "journey_authoring_validations"
APPLICATION_COLLECTION = "journey_authoring_applications"
TEMPLATE_COLLECTION = "journey_authoring_templates"

AUTHORING_COLLECTIONS = [
    SESSION_COLLECTION,
    SOURCE_COLLECTION,
    DRAFT_COLLECTION,
    PROVENANCE_COLLECTION,
    CORRECTION_COLLECTION,
    VALIDATION_COLLECTION,
    APPLICATION_COLLECTION,
    TEMPLATE_COLLECTION,
]

SESSION_STATUSES = [
    "draft", "imported", "normalized", "requires_review", "ready_to_apply",
    "partially_applied", "applied", "archived",
]
AUTHORING_MODES = ["manual", "pasted_text", "parser_run", "booking_import", "existing_journey", "mixed"]
SOURCE_TYPES = [
    "manual", "gds_cryptic", "gds_graphical_text", "airline_confirmation",
    "agency_itinerary", "website_text", "email_text", "pdf_extracted_text",
    "booking_import_draft", "parser_run", "structured_json", "existing_journey", "other",
]
SEGMENT_TYPES = ["flight", "surface", "rail", "bus", "ferry", "unknown"]
APPLICATION_MODES = [
    "create_new_journey", "create_new_option", "append_to_option",
    "replace_draft_option", "update_unfinalized_option",
]
VALIDATION_CODES = [
    "missing_departure_airport", "missing_arrival_airport", "missing_departure_datetime",
    "missing_arrival_datetime", "missing_marketing_carrier", "missing_flight_number",
    "invalid_airport_code", "invalid_airline_code", "missing_departure_timezone",
    "missing_arrival_timezone", "invalid_segment_chronology", "segment_overlap",
    "duplicate_segment", "sequence_mismatch", "negative_connection", "short_connection_review",
    "long_connection_review", "overnight_connection", "airport_change", "terminal_change",
    "surface_discontinuity", "same_flight_continuation", "codeshare_review",
    "interline_review", "unresolved_import_line",
]

EDITABLE_DRAFT_FIELDS = {
    "sequence", "option_group_key", "leg_group_key", "segment_type",
    "marketing_carrier_code", "marketing_carrier_name", "marketing_flight_number",
    "operating_carrier_code", "operating_carrier_name", "operating_flight_number",
    "departure_airport_code", "departure_airport_name", "departure_city", "departure_country",
    "arrival_airport_code", "arrival_airport_name", "arrival_city", "arrival_country",
    "departure_terminal", "arrival_terminal", "departure_local_datetime", "arrival_local_datetime",
    "departure_timezone", "arrival_timezone", "equipment_code", "equipment_label", "cabin",
    "booking_class", "fare_family_code", "fare_brand_label", "status_code",
    "married_segment_indicator", "technical_stop_indicator", "technical_stop_details",
    "surface_segment_indicator", "notes", "review_status", "confirmed_at", "confirmed_by",
}

REQUIRED_FLIGHT_FIELDS = {
    "departure_airport_code": 15,
    "arrival_airport_code": 15,
    "departure_local_datetime": 15,
    "arrival_local_datetime": 15,
    "marketing_carrier_code": 10,
    "marketing_flight_number": 10,
    "departure_timezone": 10,
    "arrival_timezone": 10,
}


class JourneyAuthoringError(ValueError):
    pass


class FinalizedJourneyMutationError(JourneyAuthoringError):
    pass


class JourneySegmentAuthoringService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "journey_segment_authoring_enabled": True,
            "authoring_sessions_collection_enabled": True,
            "import_sources_collection_enabled": True,
            "segment_drafts_collection_enabled": True,
            "field_provenance_enabled": True,
            "correction_history_enabled": True,
            "validation_records_enabled": True,
            "application_trace_enabled": True,
            "manual_segment_entry_enabled": True,
            "pasted_text_import_enabled": True,
            "parser_run_import_enabled": True,
            "booking_import_draft_integration_enabled": True,
            "existing_journey_import_enabled": True,
            "deterministic_duration_calculation_enabled": True,
            "deterministic_connection_calculation_enabled": True,
            "timezone_aware_calculation_enabled": True,
            "duplicate_detection_enabled": True,
            "chronology_validation_enabled": True,
            "bulk_segment_editing_enabled": True,
            "segment_reordering_enabled": True,
            "internal_reference_enrichment_enabled": True,
            "raw_source_preservation_enabled": True,
            "agent_confirmation_separation_enabled": True,
            "finalized_journey_snapshot_mutation_disabled": True,
            "agency_isolation_enabled": True,
            "platform_diagnostics_enabled": True,
            "live_schedule_lookup_disabled": True,
            "live_pricing_disabled": True,
            "external_api_calls_disabled": True,
            "scraping_disabled": True,
            "provider_connectivity_disabled": True,
            "provider_execution_disabled": True,
            "automatic_publication_disabled": True,
            "background_workers_disabled": True,
            "ai_disabled": True,
            "automatic_production_seeding_disabled": True,
        }

    def filters(self) -> dict[str, Any]:
        return {
            "statuses": SESSION_STATUSES,
            "authoring_modes": AUTHORING_MODES,
            "source_types": SOURCE_TYPES,
            "segment_types": SEGMENT_TYPES,
            "application_modes": APPLICATION_MODES,
            "validation_codes": VALIDATION_CODES,
            "validation_severities": ["info", "warning", "error", "critical"],
            "value_statuses": ["imported", "normalized", "enriched", "agent_confirmed", "agent_overridden", "unresolved", "rejected"],
        }

    async def create_authoring_session(self, agency_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = self._payload(payload)
        if data.get("agency_id") not in {None, agency_id}:
            raise JourneyAuthoringError("Authoring session agency_id must match the route agency.")
        mode = self._token(data.get("authoring_mode") or "manual")
        source_type = self._token(data.get("source_type") or "manual")
        values = {
            **data,
            "agency_id": agency_id,
            "title": str(data.get("title") or "Journey authoring session").strip(),
            "authoring_mode": mode if mode in AUTHORING_MODES else "manual",
            "source_type": source_type if source_type in SOURCE_TYPES else "other",
            "created_by": self._actor(user),
        }
        stored = await self.db.collection(SESSION_COLLECTION).insert_one(JourneyAuthoringSession(**values).model_dump(mode="json"))
        return self._response("session", stored)

    async def list_authoring_sessions(
        self,
        agency_id: str | None = None,
        *,
        status: str | None = None,
        source_type: str | None = None,
        journey_id: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters = {key: value for key, value in {"agency_id": agency_id, "status": status, "source_type": source_type, "journey_id": journey_id}.items() if value not in {None, ""}}
        items = await self.db.collection(SESSION_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if item.get("status") != "archived" and not item.get("archived_at")]
        return sorted(items, key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)

    async def get_authoring_session(self, agency_id: str, session_id: str, *, include_restricted_source_metadata: bool = False) -> dict[str, Any]:
        session = await self._require_session(agency_id, session_id)
        sources = await self.list_sources(agency_id, session_id)
        if not include_restricted_source_metadata:
            sources = [self._agency_safe_source(item) for item in sources]
        return {
            "phase": PHASE_LABEL,
            "session": session,
            "sources": sources,
            "segments": await self.list_segment_drafts(agency_id, session_id, include_archived=True),
            "validations": await self.list_validations(agency_id, session_id),
            "corrections": await self.list_corrections(agency_id, session_id),
            "provenance": await self.list_field_provenance(agency_id, session_id),
            "applications": await self.db.collection(APPLICATION_COLLECTION).find_many({"agency_id": agency_id, "authoring_session_id": session_id}),
            **self.safety_flags(),
        }

    async def update_authoring_session(self, agency_id: str, session_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require_session(agency_id, session_id)
        if existing.get("status") == "archived":
            raise JourneyAuthoringError("Archived authoring sessions cannot be edited.")
        allowed = {
            "journey_id", "trip_id", "offer_id", "booking_id", "passenger_context_ids", "title",
            "authoring_mode", "source_type", "source_label", "parser_profile_id", "parser_run_id",
            "booking_import_draft_id", "metadata",
        }
        updates = {key: value for key, value in self._payload(payload).items() if key in allowed}
        validated = JourneyAuthoringSession(**{**existing, **updates}).model_dump(mode="json")
        updated = await self.db.collection(SESSION_COLLECTION).update_one({"id": session_id, "agency_id": agency_id}, validated)
        if not updated:
            raise JourneyAuthoringError("Authoring session could not be updated.")
        return self._response("session", updated)

    async def archive_authoring_session(self, agency_id: str, session_id: str, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require_session(agency_id, session_id)
        if existing.get("status") == "archived":
            return self._response("session", existing)
        updated = await self.db.collection(SESSION_COLLECTION).update_one(
            {"id": session_id, "agency_id": agency_id},
            {"status": "archived", "archived_at": self._now(), "metadata": {**(existing.get("metadata") or {}), "archived_by": self._actor(user)}},
        )
        return {**self._response("session", updated or existing), "physical_deletion": False}

    async def import_raw_text(self, agency_id: str, session_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        session = await self._require_editable_session(agency_id, session_id)
        data = self._payload(payload)
        raw_text = str(data.get("raw_text") or "")
        if not raw_text.strip():
            raise JourneyAuthoringError("raw_text is required.")
        source_type = self._token(data.get("source_type") or "gds_cryptic")
        if source_type not in SOURCE_TYPES:
            source_type = "other"
        source = await self._store_source(
            agency_id,
            session_id,
            {
                **data,
                "source_type": source_type,
                "raw_text": raw_text,
                "raw_payload": data.get("raw_payload") or {"unparsed_lines_retained": True},
            },
            user,
        )
        parsed = await GdsParserService(self.db).parse_text(
            agency_id,
            {"raw_text": raw_text, "parser_profile_id": data.get("parser_profile_id")},
            user,
        )
        parser_run = parsed.get("parser_run") or {}
        created = await self._drafts_from_parser_preview(
            agency_id,
            session_id,
            source,
            parsed.get("normalized_preview") or {},
            user,
            default_year=data.get("default_year"),
        )
        used_lines = {str(item.get("raw_segment_text") or "").strip() for item in created}
        fallback = []
        for line in raw_text.splitlines():
            if line.strip() and line.strip() not in used_lines:
                recognized = self._recognize_common_segment_line(line, data.get("default_year"))
                if recognized:
                    fallback.append(await self._create_imported_draft(agency_id, session_id, source, recognized, user, "normalized"))
        unresolved_lines = [line for line in raw_text.splitlines() if line.strip() and line.strip() not in used_lines and not any(item.get("raw_segment_text") == line.strip() for item in fallback)]
        await self.db.collection(SOURCE_COLLECTION).update_one(
            {"id": source["id"], "agency_id": agency_id},
            {"parser_run_id": parser_run.get("id"), "parser_profile_id": parser_run.get("parser_profile_id"), "raw_payload": {**(source.get("raw_payload") or {}), "unparsed_lines": unresolved_lines, "parser_warnings": parsed.get("warnings") or []}},
        )
        await self.db.collection(SESSION_COLLECTION).update_one(
            {"id": session_id, "agency_id": agency_id},
            {
                "status": "imported",
                "authoring_mode": "mixed" if session.get("authoring_mode") == "manual" and await self._active_draft_count(agency_id, session_id) > len(created) + len(fallback) else "pasted_text",
                "source_type": source_type,
                "source_label": source.get("source_label"),
                "parser_profile_id": parser_run.get("parser_profile_id"),
                "parser_run_id": parser_run.get("id"),
                "source_hash": source["source_hash"],
            },
        )
        result = await self.recalculate_session(agency_id, session_id)
        return {
            **result,
            "source": self._agency_safe_source(source),
            "created_segments": created + fallback,
            "unparsed_lines": unresolved_lines,
            "unparsed_text_preserved": True,
            "existing_gds_parser_reused": True,
        }

    async def import_parser_run(self, agency_id: str, session_id: str, parser_run_id: str, user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_session(agency_id, session_id)
        run = await self.db.collection("gds_parser_runs").find_one({"id": parser_run_id, "agency_id": agency_id})
        if not run:
            raise JourneyAuthoringError("Parser run was not found for this agency.")
        entities = await self.db.collection("gds_parsed_entities").find_many({"agency_id": agency_id, "parser_run_id": parser_run_id})
        source = await self._store_source(
            agency_id,
            session_id,
            {
                "source_type": "parser_run",
                "source_label": f"Parser run {parser_run_id}",
                "raw_text": run.get("input_excerpt") or "",
                "raw_payload": {"parser_run": run, "parsed_entities": entities, "raw_text_may_be_excerpt": True},
                "parser_profile_id": run.get("parser_profile_id"),
                "parser_run_id": parser_run_id,
                "extraction_status": "parser_run_imported_with_preserved_excerpt",
            },
            user,
        )
        created = await self._drafts_from_parser_preview(agency_id, session_id, source, run.get("normalized_preview_json") or {}, user)
        await self.db.collection(SESSION_COLLECTION).update_one(
            {"id": session_id, "agency_id": agency_id},
            {"status": "imported", "authoring_mode": "parser_run", "source_type": "parser_run", "parser_profile_id": run.get("parser_profile_id"), "parser_run_id": parser_run_id, "source_hash": source["source_hash"]},
        )
        await self.recalculate_session(agency_id, session_id)
        return {"phase": PHASE_LABEL, "source": self._agency_safe_source(source), "created_segments": created, "count": len(created), "existing_gds_parser_reused": True, **self.safety_flags()}

    async def import_booking_import_draft(self, agency_id: str, session_id: str, booking_import_draft_id: str, user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_session(agency_id, session_id)
        draft = await self.db.collection("booking_import_drafts").find_one({"id": booking_import_draft_id, "agency_id": agency_id})
        if not draft:
            raise JourneyAuthoringError("Booking import draft was not found for this agency.")
        raw_text = str(draft.get("raw_text") or "")
        preview = draft.get("normalized_preview_json") or draft.get("parsed_json") or {}
        parser_run_id = draft.get("latest_parser_run_id")
        if not preview.get("segments") and raw_text:
            parsed = await GdsParserService(self.db).parse_text(agency_id, {"raw_text": raw_text, "booking_import_draft_id": booking_import_draft_id}, user)
            preview = parsed.get("normalized_preview") or {}
            parser_run_id = (parsed.get("parser_run") or {}).get("id")
        source = await self._store_source(
            agency_id,
            session_id,
            {
                "source_type": "booking_import_draft",
                "source_label": draft.get("title") or draft.get("name") or f"Booking import {booking_import_draft_id}",
                "raw_text": raw_text,
                "raw_payload": {"booking_import_draft_snapshot": draft, "normalized_preview": preview},
                "parser_profile_id": draft.get("latest_parser_profile_id"),
                "parser_run_id": parser_run_id,
                "booking_import_draft_id": booking_import_draft_id,
            },
            user,
        )
        created = await self._drafts_from_parser_preview(agency_id, session_id, source, preview, user)
        await self.db.collection(SESSION_COLLECTION).update_one(
            {"id": session_id, "agency_id": agency_id},
            {"status": "imported", "authoring_mode": "booking_import", "source_type": "booking_import_draft", "parser_run_id": parser_run_id, "booking_import_draft_id": booking_import_draft_id, "source_hash": source["source_hash"]},
        )
        await self.recalculate_session(agency_id, session_id)
        return {"phase": PHASE_LABEL, "source": self._agency_safe_source(source), "created_segments": created, "count": len(created), "booking_import_draft_reused": True, **self.safety_flags()}

    async def import_existing_journey(self, agency_id: str, session_id: str, journey_id: str, user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_session(agency_id, session_id)
        complete = await CanonicalJourneyItineraryService(self.db).get_complete_journey(agency_id, journey_id)
        source_payload = self._jsonable(complete)
        source = await self._store_source(
            agency_id,
            session_id,
            {"source_type": "existing_journey", "source_label": (complete.get("journey") or {}).get("journey_reference"), "raw_text": json.dumps(source_payload, sort_keys=True), "raw_payload": source_payload},
            user,
        )
        option_keys = {item["id"]: f"option-{item.get('option_number') or index + 1}" for index, item in enumerate(complete.get("itinerary_options") or [])}
        leg_keys = {item["id"]: f"leg-{item.get('leg_number') or index + 1}" for index, item in enumerate(complete.get("legs") or [])}
        created = []
        for segment in complete.get("segments") or []:
            values = self._draft_values_from_canonical(segment)
            values["option_group_key"] = option_keys.get(segment.get("itinerary_option_id"), "option-1")
            values["leg_group_key"] = leg_keys.get(segment.get("leg_id"), "leg-1")
            created.append(await self._create_imported_draft(agency_id, session_id, source, values, user, "imported"))
        await self.db.collection(SESSION_COLLECTION).update_one(
            {"id": session_id, "agency_id": agency_id},
            {"status": "imported", "authoring_mode": "existing_journey", "source_type": "existing_journey", "journey_id": journey_id, "source_hash": source["source_hash"]},
        )
        await self.recalculate_session(agency_id, session_id)
        return {"phase": PHASE_LABEL, "source": self._agency_safe_source(source), "created_segments": created, "count": len(created), "canonical_journey_reused": True, **self.safety_flags()}

    async def list_sources(self, agency_id: str, session_id: str) -> list[dict[str, Any]]:
        await self._require_session(agency_id, session_id)
        items = await self.db.collection(SOURCE_COLLECTION).find_many({"agency_id": agency_id, "authoring_session_id": session_id})
        return sorted(items, key=lambda item: str(item.get("imported_at") or item.get("created_at") or ""))

    async def create_manual_segment_draft(self, agency_id: str, session_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_session(agency_id, session_id)
        data = self._payload(payload)
        existing = await self.list_segment_drafts(agency_id, session_id)
        values = {
            **{key: value for key, value in data.items() if key in EDITABLE_DRAFT_FIELDS},
            "agency_id": agency_id,
            "authoring_session_id": session_id,
            "sequence": int(data.get("sequence") or len(existing) + 1),
            "source_confidence": data.get("source_confidence") if data.get("source_confidence") is not None else 1.0,
            "source_provenance": {"source_type": "manual", "value_status": "agent_confirmed"},
            "confirmed_by": self._actor(user),
            "confirmed_at": self._now(),
            "review_status": data.get("review_status") or "agent_confirmed",
        }
        record = JourneySegmentDraft(**self._calculate_draft(values)).model_dump(mode="json")
        stored = await self.db.collection(DRAFT_COLLECTION).insert_one(record)
        for field in EDITABLE_DRAFT_FIELDS:
            if self._present(data.get(field)):
                await self._record_provenance(agency_id, session_id, stored["id"], field, data.get(field), data.get(field), "agent_confirmed", "manual", user, source_reference=None)
        await self._refresh_session_summary(agency_id, session_id)
        return self._response("segment", stored)

    async def list_segment_drafts(self, agency_id: str, session_id: str, *, include_archived: bool = False) -> list[dict[str, Any]]:
        await self._require_session(agency_id, session_id)
        items = await self.db.collection(DRAFT_COLLECTION).find_many({"agency_id": agency_id, "authoring_session_id": session_id})
        if not include_archived:
            items = [item for item in items if item.get("active", True) and not item.get("archived_at")]
        return sorted(items, key=lambda item: (str(item.get("option_group_key") or ""), int(item.get("sequence") or 0), str(item.get("created_at") or "")))

    async def update_segment_draft(self, agency_id: str, session_id: str, segment_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_session(agency_id, session_id)
        existing = await self._require_draft(agency_id, session_id, segment_id)
        if not existing.get("active", True):
            raise JourneyAuthoringError("Archived segment drafts must be restored before editing.")
        data = {key: value for key, value in self._payload(payload).items() if key in EDITABLE_DRAFT_FIELDS}
        actor = self._actor(user)
        for field, value in data.items():
            if self._jsonable(existing.get(field)) != self._jsonable(value):
                await self._record_correction(agency_id, session_id, segment_id, field, "manual_override", existing.get(field), value, user, str(self._payload(payload).get("reason") or "Agent edit"))
                await self._record_provenance(agency_id, session_id, segment_id, field, existing.get(field), value, "agent_overridden", "manual", user, source_reference=existing.get("source_id"))
        values = self._calculate_draft({**existing, **data, "confirmed_by": actor, "confirmed_at": self._now(), "review_status": "agent_confirmed"})
        updated = await self.db.collection(DRAFT_COLLECTION).update_one({"id": segment_id, "agency_id": agency_id, "authoring_session_id": session_id}, JourneySegmentDraft(**values).model_dump(mode="json"))
        await self._refresh_session_summary(agency_id, session_id)
        return self._response("segment", updated or values)

    async def archive_segment_draft(self, agency_id: str, session_id: str, segment_id: str, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require_draft(agency_id, session_id, segment_id)
        updated = await self.db.collection(DRAFT_COLLECTION).update_one({"id": segment_id, "agency_id": agency_id}, {"active": False, "archived_at": self._now()})
        await self._record_correction(agency_id, session_id, segment_id, None, "delete", existing, updated, user, "Segment draft archived; no physical deletion")
        await self._refresh_session_summary(agency_id, session_id)
        return {**self._response("segment", updated or existing), "physical_deletion": False}

    async def restore_segment_draft(self, agency_id: str, session_id: str, segment_id: str, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require_draft(agency_id, session_id, segment_id)
        updated = await self.db.collection(DRAFT_COLLECTION).update_one({"id": segment_id, "agency_id": agency_id}, {"active": True, "archived_at": None})
        await self._record_correction(agency_id, session_id, segment_id, None, "restore", existing, updated, user, "Segment draft restored")
        await self._refresh_session_summary(agency_id, session_id)
        return self._response("segment", updated or existing)

    async def reorder_segment_drafts(self, agency_id: str, session_id: str, segment_ids: list[str], user: dict[str, Any]) -> dict[str, Any]:
        active = await self.list_segment_drafts(agency_id, session_id)
        active_ids = {item["id"] for item in active}
        if set(segment_ids) != active_ids or len(segment_ids) != len(active_ids):
            raise JourneyAuthoringError("Reorder must include every active segment draft exactly once.")
        for sequence, segment_id in enumerate(segment_ids, start=1):
            existing = next(item for item in active if item["id"] == segment_id)
            if int(existing.get("sequence") or 0) != sequence:
                await self.db.collection(DRAFT_COLLECTION).update_one({"id": segment_id, "agency_id": agency_id}, {"sequence": sequence})
                await self._record_correction(agency_id, session_id, segment_id, "sequence", "reorder", existing.get("sequence"), sequence, user, "Segment order changed")
        return {"phase": PHASE_LABEL, "items": await self.list_segment_drafts(agency_id, session_id), "count": len(segment_ids), **self.safety_flags()}

    async def bulk_update_segment_drafts(self, agency_id: str, session_id: str, segment_ids: list[str], updates: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        allowed = {key: value for key, value in updates.items() if key in EDITABLE_DRAFT_FIELDS and key not in {"sequence"}}
        if not allowed:
            raise JourneyAuthoringError("No supported bulk update fields were provided.")
        items = []
        for segment_id in segment_ids:
            items.append((await self.update_segment_draft(agency_id, session_id, segment_id, {**allowed, "reason": "Bulk segment update"}, user))["segment"])
        return {"phase": PHASE_LABEL, "items": items, "count": len(items), **self.safety_flags()}

    async def assign_segments(self, agency_id: str, session_id: str, segment_ids: list[str], *, option_group_key: str | None, leg_group_key: str | None, user: dict[str, Any]) -> dict[str, Any]:
        updates = {key: value for key, value in {"option_group_key": option_group_key, "leg_group_key": leg_group_key}.items() if value}
        if not updates:
            raise JourneyAuthoringError("An option_group_key or leg_group_key is required.")
        result = await self.bulk_update_segment_drafts(agency_id, session_id, segment_ids, updates, user)
        for segment_id in segment_ids:
            await self._record_correction(agency_id, session_id, segment_id, None, "assignment", None, updates, user, "Segment grouping assignment")
        return result

    async def split_segment_draft(self, agency_id: str, session_id: str, segment_id: str, children: list[dict[str, Any]], user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require_draft(agency_id, session_id, segment_id)
        if len(children) < 2:
            raise JourneyAuthoringError("Split requires at least two explicit child segment payloads.")
        created = []
        for offset, child in enumerate(children):
            payload = {**{key: existing.get(key) for key in EDITABLE_DRAFT_FIELDS}, **child, "sequence": int(existing.get("sequence") or 1) + offset}
            created.append((await self.create_manual_segment_draft(agency_id, session_id, payload, user))["segment"])
        await self.archive_segment_draft(agency_id, session_id, segment_id, user)
        await self._record_correction(agency_id, session_id, segment_id, None, "split", existing, [item["id"] for item in created], user, "Explicit split")
        ordered = await self.list_segment_drafts(agency_id, session_id)
        await self.reorder_segment_drafts(agency_id, session_id, [item["id"] for item in ordered], user)
        return {"phase": PHASE_LABEL, "source_segment_id": segment_id, "created_segments": created, "count": len(created), **self.safety_flags()}

    async def merge_segment_drafts(self, agency_id: str, session_id: str, segment_ids: list[str], payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        if len(segment_ids) < 2:
            raise JourneyAuthoringError("Merge requires at least two segment drafts.")
        items = [await self._require_draft(agency_id, session_id, segment_id) for segment_id in segment_ids]
        ordered = sorted(items, key=lambda item: int(item.get("sequence") or 0))
        if any(not item.get("active", True) for item in ordered) or any(ordered[index + 1].get("sequence") != ordered[index].get("sequence") + 1 for index in range(len(ordered) - 1)):
            raise JourneyAuthoringError("Only contiguous active drafts may be merged.")
        if len({item.get("segment_type") for item in ordered}) != 1:
            raise JourneyAuthoringError("Merged drafts must share a segment type.")
        base = {key: ordered[0].get(key) for key in EDITABLE_DRAFT_FIELDS}
        base.update({key: value for key, value in payload.items() if key in EDITABLE_DRAFT_FIELDS})
        base.setdefault("departure_airport_code", ordered[0].get("departure_airport_code"))
        base.setdefault("arrival_airport_code", ordered[-1].get("arrival_airport_code"))
        base.setdefault("departure_local_datetime", ordered[0].get("departure_local_datetime"))
        base.setdefault("arrival_local_datetime", ordered[-1].get("arrival_local_datetime"))
        merged = (await self.create_manual_segment_draft(agency_id, session_id, base, user))["segment"]
        for item in ordered:
            await self.archive_segment_draft(agency_id, session_id, item["id"], user)
        await self._record_correction(agency_id, session_id, merged["id"], None, "merge", segment_ids, merged, user, "Explicit merge")
        return {"phase": PHASE_LABEL, "merged_segment": merged, "archived_segment_ids": segment_ids, **self.safety_flags()}

    async def normalize_session(self, agency_id: str, session_id: str) -> dict[str, Any]:
        await self._require_editable_session(agency_id, session_id)
        for item in await self.list_segment_drafts(agency_id, session_id):
            calculated = self._calculate_draft({**item, "normalized_at": self._now()})
            await self.db.collection(DRAFT_COLLECTION).update_one({"id": item["id"], "agency_id": agency_id}, JourneySegmentDraft(**calculated).model_dump(mode="json"))
        await self.db.collection(SESSION_COLLECTION).update_one({"id": session_id, "agency_id": agency_id}, {"status": "normalized"})
        return await self.recalculate_session(agency_id, session_id)

    async def enrich_session_from_internal_reference_data(self, agency_id: str, session_id: str, user: dict[str, Any]) -> dict[str, Any]:
        await self._require_editable_session(agency_id, session_id)
        references = await self.db.collection("global_reference_records").find_many()
        references = [item for item in references if item.get("agency_id") in {None, agency_id}]
        airports = self._reference_map(references, "airports")
        airlines = self._reference_map(references, "airlines")
        changed = []
        for item in await self.list_segment_drafts(agency_id, session_id):
            updates: dict[str, Any] = {}
            candidates = [
                ("departure_airport_code", "departure_airport_name", "label", airports),
                ("departure_airport_code", "departure_city", "city", airports),
                ("departure_airport_code", "departure_country", "country", airports),
                ("departure_airport_code", "departure_timezone", "timezone", airports),
                ("arrival_airport_code", "arrival_airport_name", "label", airports),
                ("arrival_airport_code", "arrival_city", "city", airports),
                ("arrival_airport_code", "arrival_country", "country", airports),
                ("arrival_airport_code", "arrival_timezone", "timezone", airports),
                ("marketing_carrier_code", "marketing_carrier_name", "label", airlines),
                ("operating_carrier_code", "operating_carrier_name", "label", airlines),
            ]
            for code_field, target_field, metadata_key, records in candidates:
                if item.get(target_field) not in {None, ""} or await self._field_agent_confirmed(agency_id, session_id, item["id"], target_field):
                    continue
                reference = records.get(str(item.get(code_field) or "").upper())
                value = self._reference_value(reference, metadata_key) if reference else None
                if value not in {None, ""}:
                    updates[target_field] = value
                    await self._record_provenance(agency_id, session_id, item["id"], target_field, None, value, "enriched", "internal_reference", user, source_reference=reference.get("id"), enrichment_source_type="global_reference_record", enrichment_source_id=reference.get("id"))
                    await self._record_correction(agency_id, session_id, item["id"], target_field, "enrichment", None, value, user, "Governed internal reference enrichment")
            if updates:
                calculated = self._calculate_draft({**item, **updates})
                changed.append(await self.db.collection(DRAFT_COLLECTION).update_one({"id": item["id"], "agency_id": agency_id}, JourneySegmentDraft(**calculated).model_dump(mode="json")))
        await self._refresh_session_summary(agency_id, session_id)
        return {"phase": PHASE_LABEL, "updated_segments": changed, "count": len(changed), "external_lookup_performed": False, **self.safety_flags()}

    async def recalculate_session(self, agency_id: str, session_id: str) -> dict[str, Any]:
        await self._require_session(agency_id, session_id)
        active = await self.list_segment_drafts(agency_id, session_id)
        normalized = []
        for item in active:
            calculated = self._calculate_draft(item)
            normalized.append(await self.db.collection(DRAFT_COLLECTION).update_one({"id": item["id"], "agency_id": agency_id}, JourneySegmentDraft(**calculated).model_dump(mode="json")) or calculated)
        normalized_hash = self._hash([{key: item.get(key) for key in sorted(item) if key not in {"updated_at"}} for item in normalized])
        summary = await self._refresh_session_summary(agency_id, session_id, normalized_hash=normalized_hash)
        connections = self._connection_preview(normalized)
        return {"phase": PHASE_LABEL, "segments": normalized, "connections": connections, "summary": summary, **self.safety_flags()}

    async def validate_session(self, agency_id: str, session_id: str) -> dict[str, Any]:
        await self._require_session(agency_id, session_id)
        prior = await self.db.collection(VALIDATION_COLLECTION).find_many({"agency_id": agency_id, "authoring_session_id": session_id})
        now = self._now()
        for item in prior:
            if not item.get("resolved_at") and not item.get("superseded_at"):
                await self.db.collection(VALIDATION_COLLECTION).update_one({"id": item["id"], "agency_id": agency_id}, {"superseded_at": now})
        segments = await self.list_segment_drafts(agency_id, session_id)
        findings = self._validation_findings(segments)
        stored = []
        for finding in findings:
            model = JourneyAuthoringValidation(agency_id=agency_id, authoring_session_id=session_id, **finding)
            stored.append(await self.db.collection(VALIDATION_COLLECTION).insert_one(model.model_dump(mode="json")))
        blocking = sum(bool(item.get("blocking")) for item in stored)
        warnings = sum(item.get("severity") == "warning" for item in stored)
        status = "requires_review" if blocking or warnings else "ready_to_apply"
        validation_summary = {"total": len(stored), "blocking": blocking, "warnings": warnings, "severity_counts": self._counts(stored, "severity")}
        await self.db.collection(SESSION_COLLECTION).update_one(
            {"id": session_id, "agency_id": agency_id},
            {"status": status, "validation_summary": validation_summary, "blocking_errors_count": blocking, "warnings_count": warnings},
        )
        return {"phase": PHASE_LABEL, "items": stored, "count": len(stored), "summary": validation_summary, "status": status, "completeness_is_not_operational_approval": True, **self.safety_flags()}

    async def list_validations(self, agency_id: str, session_id: str, *, active_only: bool = False) -> list[dict[str, Any]]:
        await self._require_session(agency_id, session_id)
        items = await self.db.collection(VALIDATION_COLLECTION).find_many({"agency_id": agency_id, "authoring_session_id": session_id})
        if active_only:
            items = [item for item in items if not item.get("resolved_at") and not item.get("superseded_at")]
        return sorted(items, key=lambda item: str(item.get("detected_at") or item.get("created_at") or ""), reverse=True)

    async def resolve_validation(self, agency_id: str, session_id: str, validation_id: str, resolution_note: str, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self.db.collection(VALIDATION_COLLECTION).find_one({"id": validation_id, "agency_id": agency_id, "authoring_session_id": session_id})
        if not existing:
            raise JourneyAuthoringError("Validation was not found for this agency session.")
        if existing.get("resolved_at"):
            return self._response("validation", existing)
        updated = await self.db.collection(VALIDATION_COLLECTION).update_one(
            {"id": validation_id, "agency_id": agency_id},
            {"resolved_at": self._now(), "resolved_by": self._actor(user), "resolution_note": resolution_note},
        )
        await self._refresh_session_summary(agency_id, session_id)
        return self._response("validation", updated or existing)

    async def list_corrections(self, agency_id: str, session_id: str) -> list[dict[str, Any]]:
        await self._require_session(agency_id, session_id)
        items = await self.db.collection(CORRECTION_COLLECTION).find_many({"agency_id": agency_id, "authoring_session_id": session_id})
        return sorted(items, key=lambda item: str(item.get("corrected_at") or ""), reverse=True)

    async def list_field_provenance(self, agency_id: str, session_id: str) -> list[dict[str, Any]]:
        await self._require_session(agency_id, session_id)
        items = await self.db.collection(PROVENANCE_COLLECTION).find_many({"agency_id": agency_id, "authoring_session_id": session_id})
        return sorted(items, key=lambda item: str(item.get("changed_at") or ""), reverse=True)

    async def preview_application(self, agency_id: str, session_id: str, payload: BaseModel | dict[str, Any]) -> dict[str, Any]:
        data = self._payload(payload)
        validation = await self.validate_session(agency_id, session_id)
        session = await self._require_session(agency_id, session_id)
        segments = await self.list_segment_drafts(agency_id, session_id)
        mode = self._token(data.get("application_mode") or ("create_new_option" if data.get("journey_id") or session.get("journey_id") else "create_new_journey"))
        journey_id = data.get("journey_id") or session.get("journey_id")
        target_editable = True
        target_reason = None
        if journey_id:
            complete = await CanonicalJourneyItineraryService(self.db).get_complete_journey(agency_id, str(journey_id))
            finalized = [item for item in complete.get("snapshots") or [] if item.get("immutable") or item.get("finalized_at")]
            if finalized:
                target_editable = False
                target_reason = "The target Journey has a finalized immutable snapshot. Create a new Journey instead."
        return {
            "phase": PHASE_LABEL,
            "application_mode": mode,
            "journey_id": journey_id,
            "target_option_id": data.get("option_id"),
            "target_editable": target_editable,
            "target_reason": target_reason,
            "segment_count": len(segments),
            "option_groups": sorted({item.get("option_group_key") or "option-1" for item in segments}),
            "leg_groups": sorted({item.get("leg_group_key") or "leg-1" for item in segments}),
            "connections": self._connection_preview(segments),
            "validation_summary": validation["summary"],
            "blocking": bool(validation["summary"]["blocking"] or not segments or not target_editable),
            "source_references_retained": True,
            "automatic_publication": False,
            "finalized_snapshot_mutation": False,
            **self.safety_flags(),
        }

    async def apply_session_to_journey(self, agency_id: str, session_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = self._payload(payload)
        preview = await self.preview_application(agency_id, session_id, data)
        if preview["blocking"]:
            if not preview["target_editable"]:
                raise FinalizedJourneyMutationError(preview["target_reason"] or "Finalized Journey snapshots cannot be mutated.")
            raise JourneyAuthoringError("The authoring session has blocking validation findings or no active segments.")
        session = await self._require_editable_session(agency_id, session_id)
        segments = await self.list_segment_drafts(agency_id, session_id)
        mode = preview["application_mode"]
        if mode not in APPLICATION_MODES:
            raise JourneyAuthoringError("Unsupported application_mode.")
        canonical = CanonicalJourneyItineraryService(self.db)
        created_ids: list[str] = []
        replaced_ids: list[str] = []
        journey_id = str(data.get("journey_id") or session.get("journey_id") or "")
        if mode == "create_new_journey":
            created = await canonical.create_journey(
                {
                    "agency_id": agency_id,
                    "title": data.get("journey_title") or session.get("title") or "Authored journey",
                    "journey_type": data.get("journey_type") or "unknown",
                    "source_entity_type": "journey_authoring_session",
                    "source_entity_id": session_id,
                    "client_id": data.get("client_id"),
                    "passenger_ids": session.get("passenger_context_ids") or [],
                    "status": "draft",
                    "metadata": {"journey_authoring_session_id": session_id, "trip_id": session.get("trip_id"), "raw_source_preserved": True},
                },
                user,
                agency_id=agency_id,
            )
            journey_id = created["journey"]["id"]
            created_ids.append(journey_id)
        if not journey_id:
            raise JourneyAuthoringError("journey_id is required for this application mode.")
        complete = await canonical.get_complete_journey(agency_id, journey_id)
        if any(item.get("immutable") or item.get("finalized_at") for item in complete.get("snapshots") or []):
            raise FinalizedJourneyMutationError("The target Journey has a finalized immutable snapshot.")
        target_option_id = data.get("option_id")
        if mode == "replace_draft_option":
            if not target_option_id:
                raise JourneyAuthoringError("option_id is required to replace a draft option.")
            target = next((item for item in complete.get("itinerary_options") or [] if item.get("id") == target_option_id), None)
            if not target or target.get("status") not in {"draft", "proposed"}:
                raise JourneyAuthoringError("Only an existing draft or proposed option may be replaced.")
            await self.db.collection("journey_itinerary_options").update_one({"id": target_option_id, "agency_id": agency_id}, {"status": "superseded", "metadata": {**(target.get("metadata") or {}), "replaced_by_authoring_session_id": session_id}})
            replaced_ids.append(str(target_option_id))
            for old_segment in complete.get("segments") or []:
                if old_segment.get("itinerary_option_id") == target_option_id:
                    await self.db.collection("journey_segment_representations").update_one({"id": old_segment["id"], "agency_id": agency_id}, {"status": "superseded"})
                    replaced_ids.append(old_segment["id"])
            target_option_id = None
        created_segment_ids: list[str] = []
        created_option_ids: list[str] = []
        grouped = self._group_segments(segments)
        if mode in {"append_to_option", "update_unfinalized_option"}:
            if not target_option_id or not any(item.get("id") == target_option_id for item in complete.get("itinerary_options") or []):
                raise JourneyAuthoringError("A valid option_id is required for append/update mode.")
            grouped = {"selected-option": segments}
        for option_index, (_, option_segments) in enumerate(grouped.items(), start=1):
            option_id = target_option_id
            if not option_id:
                option = await canonical.create_option(
                    agency_id,
                    journey_id,
                    {
                        "title": data.get("option_title") or f"Authored itinerary option {option_index}",
                        "source_entity_type": "journey_authoring_session",
                        "source_entity_id": session_id,
                        "status": "draft",
                        "source_provenance": {"source_type": "journey_authoring_session", "source_reference": session_id, "agent_confirmed": True},
                    },
                    user,
                )
                option_id = option["itinerary_option"]["id"]
                created_ids.append(option_id)
                created_option_ids.append(option_id)
            leg_map: dict[str, str] = {}
            for leg_index, leg_key in enumerate(dict.fromkeys(str(item.get("leg_group_key") or "leg-1") for item in option_segments), start=1):
                leg = await canonical.create_leg(
                    agency_id,
                    journey_id,
                    {"itinerary_option_id": option_id, "leg_number": leg_index, "leg_type": "flight", "presentation_label": leg_key, "metadata": {"authoring_session_id": session_id, "authoring_leg_group_key": leg_key}},
                    user,
                )
                leg_id = leg["leg"]["id"]
                leg_map[leg_key] = leg_id
                created_ids.append(leg_id)
            application_segments = []
            for segment in sorted(option_segments, key=lambda item: int(item.get("sequence") or 0)):
                projected = await canonical.create_segment(
                    agency_id,
                    journey_id,
                    self._canonical_segment_payload(segment, option_id, leg_map.get(str(segment.get("leg_group_key") or "leg-1")), session_id),
                    user,
                )
                projected_segment = projected["segment"]
                application_segments.append(projected_segment)
                created_segment_ids.append(projected_segment["id"])
                created_ids.append(projected_segment["id"])
            for inbound, outbound in zip(application_segments, application_segments[1:]):
                connection = await canonical.create_connection(
                    agency_id,
                    journey_id,
                    {"itinerary_option_id": option_id, "inbound_segment_id": inbound["id"], "outbound_segment_id": outbound["id"], "metadata": {"authoring_session_id": session_id, "mct_claimed": False}},
                    user,
                )
                created_ids.append(connection["connection"]["id"])
        result_hash = self._hash({"journey_id": journey_id, "created_ids": created_ids, "draft_ids": [item["id"] for item in segments], "mode": mode})
        application = JourneyAuthoringApplication(
            agency_id=agency_id,
            authoring_session_id=session_id,
            journey_id=journey_id,
            option_id=created_option_ids[0] if len(created_option_ids) == 1 else target_option_id,
            applied_segment_draft_ids=[item["id"] for item in segments],
            created_journey_record_ids=created_ids,
            replaced_journey_record_ids=replaced_ids,
            application_mode=mode,
            applied_by=self._actor(user),
            result_hash=result_hash,
            warnings=[item["validation_code"] for item in await self.list_validations(agency_id, session_id, active_only=True) if not item.get("blocking")],
            metadata={"created_option_ids": created_option_ids, "canonical_journey_service_reused": True},
        )
        stored = await self.db.collection(APPLICATION_COLLECTION).insert_one(application.model_dump(mode="json"))
        await self.db.collection(SESSION_COLLECTION).update_one({"id": session_id, "agency_id": agency_id}, {"journey_id": journey_id, "status": "applied"})
        return {
            "phase": PHASE_LABEL,
            "application": stored,
            "journey": await canonical.get_complete_journey(agency_id, journey_id),
            "created_record_ids": created_ids,
            "replaced_record_ids": replaced_ids,
            "canonical_journey_reused": True,
            "automatic_publication": False,
            **self.safety_flags(),
        }

    async def list_templates(self, agency_id: str) -> list[dict[str, Any]]:
        items = await self.db.collection(TEMPLATE_COLLECTION).find_many({"agency_id": agency_id})
        return sorted(items, key=lambda item: str(item.get("name") or "").lower())

    async def create_template(self, agency_id: str, payload: BaseModel | dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = self._payload(payload)
        model = JourneyAuthoringTemplate(agency_id=agency_id, created_by=self._actor(user), **data)
        stored = await self.db.collection(TEMPLATE_COLLECTION).insert_one(model.model_dump(mode="json"))
        return self._response("template", stored)

    async def update_template(self, agency_id: str, template_id: str, payload: BaseModel | dict[str, Any]) -> dict[str, Any]:
        existing = await self.db.collection(TEMPLATE_COLLECTION).find_one({"id": template_id, "agency_id": agency_id})
        if not existing:
            raise JourneyAuthoringError("Authoring template was not found for this agency.")
        allowed = {"name", "default_segment_type", "default_cabin", "default_status_code", "default_source_type", "default_timezone_strategy", "active", "metadata"}
        values = {**existing, **{key: value for key, value in self._payload(payload).items() if key in allowed}}
        updated = await self.db.collection(TEMPLATE_COLLECTION).update_one({"id": template_id, "agency_id": agency_id}, JourneyAuthoringTemplate(**values).model_dump(mode="json"))
        return self._response("template", updated or values)

    async def summarize_authoring_readiness(self, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        sessions = await self.db.collection(SESSION_COLLECTION).find_many(filters)
        sources = await self.db.collection(SOURCE_COLLECTION).find_many(filters)
        segments = await self.db.collection(DRAFT_COLLECTION).find_many(filters)
        validations = await self.db.collection(VALIDATION_COLLECTION).find_many(filters)
        corrections = await self.db.collection(CORRECTION_COLLECTION).find_many(filters)
        applications = await self.db.collection(APPLICATION_COLLECTION).find_many(filters)
        active_validations = [item for item in validations if not item.get("resolved_at") and not item.get("superseded_at")]
        active_sessions = [item for item in sessions if item.get("status") != "archived" and not item.get("archived_at")]
        active_segments = [item for item in segments if item.get("active", True) and not item.get("archived_at")]
        return {
            "authoring_session_count": len(sessions),
            "active_authoring_session_count": len(active_sessions),
            "requires_review_session_count": sum(item.get("status") == "requires_review" for item in sessions),
            "import_source_count": len(sources),
            "segment_draft_count": len(segments),
            "unresolved_segment_count": sum(item.get("review_status") not in {"agent_confirmed", "confirmed"} or bool(item.get("blocking_errors")) for item in active_segments),
            "confirmed_segment_count": sum(item.get("review_status") in {"agent_confirmed", "confirmed"} for item in active_segments),
            "validation_count": len(validations),
            "blocking_validation_count": sum(bool(item.get("blocking")) for item in active_validations),
            "correction_count": len(corrections),
            "application_count": len(applications),
            "parser_linked_session_count": sum(bool(item.get("parser_run_id")) for item in sessions),
            "booking_import_linked_session_count": sum(bool(item.get("booking_import_draft_id")) for item in sessions),
            "average_completeness": round(sum(int(item.get("completeness_score") or 0) for item in active_sessions) / len(active_sessions), 1) if active_sessions else 0,
            "source_type_counts": self._counts(sources, "source_type"),
            "status_counts": self._counts(sessions, "status"),
            "validation_severity_counts": self._counts(active_validations, "severity"),
            "agency_counts": self._counts(sessions, "agency_id") if not agency_id else {agency_id: len(sessions)},
        }

    async def dashboard(self, agency_id: str | None = None) -> dict[str, Any]:
        items = await self.list_authoring_sessions(agency_id=agency_id, include_archived=True)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "summary": await self.summarize_authoring_readiness(agency_id),
            "filters": self.filters(),
            "readiness_required": False,
            "diagnostic_statement": "Journey authoring preserves raw input and prepares metadata drafts for explicit application to canonical Journey records. It performs no live schedule lookup, provider action, AI inference, or automatic publication.",
            **self.safety_flags(),
        }

    async def _store_source(self, agency_id: str, session_id: str, data: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        raw_text = str(data.get("raw_text") or "")
        raw_payload = self._jsonable(data.get("raw_payload")) if data.get("raw_payload") is not None else None
        source_hash = self._hash({"raw_text": raw_text, "raw_payload": raw_payload})
        allowed = set(JourneyImportSource.model_fields) - {"id", "agency_id", "authoring_session_id", "created_at", "updated_at", "imported_by", "imported_at", "source_hash"}
        values = {
            **{key: value for key, value in data.items() if key in allowed},
            "agency_id": agency_id,
            "authoring_session_id": session_id,
            "raw_text": raw_text,
            "raw_payload": raw_payload,
            "source_hash": source_hash,
            "imported_by": self._actor(user),
        }
        return await self.db.collection(SOURCE_COLLECTION).insert_one(JourneyImportSource(**values).model_dump(mode="json"))

    async def _drafts_from_parser_preview(self, agency_id: str, session_id: str, source: dict[str, Any], preview: dict[str, Any], user: dict[str, Any], default_year: Any = None) -> list[dict[str, Any]]:
        created = []
        for index, segment in enumerate(preview.get("segments") or [], start=1):
            values = self._draft_values_from_parser(segment, index, default_year)
            created.append(await self._create_imported_draft(agency_id, session_id, source, values, user, "normalized"))
        return created

    async def _create_imported_draft(self, agency_id: str, session_id: str, source: dict[str, Any], values: dict[str, Any], user: dict[str, Any], value_status: str) -> dict[str, Any]:
        existing_count = await self._active_draft_count(agency_id, session_id)
        record_values = {
            **values,
            "agency_id": agency_id,
            "authoring_session_id": session_id,
            "source_id": source["id"],
            "sequence": int(values.get("sequence") or existing_count + 1),
            "source_provenance": {"source_type": source.get("source_type"), "source_reference": source["id"], "value_status": value_status},
            "normalized_at": self._now(),
        }
        stored = await self.db.collection(DRAFT_COLLECTION).insert_one(JourneySegmentDraft(**self._calculate_draft(record_values)).model_dump(mode="json"))
        for field, value in values.items():
            if field in EDITABLE_DRAFT_FIELDS and self._present(value):
                await self._record_provenance(
                    agency_id, session_id, stored["id"], field, value, value, value_status,
                    str(source.get("source_type") or "other"), user,
                    source_reference=source["id"], parser_confidence=values.get("source_confidence"),
                )
        return stored

    def _draft_values_from_parser(self, segment: dict[str, Any], sequence: int, default_year: Any = None) -> dict[str, Any]:
        departure = segment.get("departure_local_datetime") or segment.get("departure_datetime")
        arrival = segment.get("arrival_local_datetime") or segment.get("arrival_datetime")
        if not departure:
            departure = self._combine_parser_datetime(segment.get("departure_date"), segment.get("departure_time"), default_year)
        if not arrival:
            arrival = self._combine_parser_datetime(segment.get("arrival_date") or segment.get("departure_date"), segment.get("arrival_time"), default_year)
        return {
            "sequence": segment.get("sequence") or sequence,
            "segment_type": segment.get("segment_type") or "flight",
            "marketing_carrier_code": segment.get("marketing_carrier_code") or segment.get("marketing_airline_code") or segment.get("airline_code"),
            "marketing_flight_number": segment.get("marketing_flight_number") or segment.get("flight_number"),
            "operating_carrier_code": segment.get("operating_carrier_code") or segment.get("operating_airline_code"),
            "operating_flight_number": segment.get("operating_flight_number"),
            "departure_airport_code": segment.get("departure_airport_code") or segment.get("origin") or segment.get("origin_airport"),
            "arrival_airport_code": segment.get("arrival_airport_code") or segment.get("destination") or segment.get("destination_airport"),
            "departure_local_datetime": departure,
            "arrival_local_datetime": arrival,
            "departure_timezone": segment.get("departure_timezone"),
            "arrival_timezone": segment.get("arrival_timezone"),
            "departure_terminal": segment.get("departure_terminal"),
            "arrival_terminal": segment.get("arrival_terminal"),
            "cabin": segment.get("cabin") or segment.get("cabin_class"),
            "booking_class": segment.get("booking_class") or segment.get("booking_class_code"),
            "status_code": segment.get("status") or segment.get("status_code"),
            "equipment_code": segment.get("aircraft_code") or segment.get("equipment_code"),
            "source_confidence": segment.get("confidence"),
            "raw_segment_text": segment.get("raw_line") or segment.get("raw_segment_text") or segment.get("source_text"),
            "metadata": {"parser_segment": self._jsonable(segment), "date_requires_agent_confirmation": bool((segment.get("departure_date") or segment.get("arrival_date")) and not default_year and not departure)},
        }

    def _draft_values_from_canonical(self, segment: dict[str, Any]) -> dict[str, Any]:
        return {
            "sequence": segment.get("segment_number"),
            "segment_type": segment.get("segment_type") or "flight",
            "marketing_carrier_code": segment.get("marketing_carrier_code"),
            "marketing_flight_number": segment.get("marketing_flight_number"),
            "operating_carrier_code": segment.get("operating_carrier_code"),
            "operating_flight_number": segment.get("operating_flight_number"),
            "departure_airport_code": segment.get("origin_airport_code"),
            "arrival_airport_code": segment.get("destination_airport_code"),
            "departure_local_datetime": segment.get("departure_local"),
            "arrival_local_datetime": segment.get("arrival_local"),
            "departure_timezone": segment.get("departure_timezone"),
            "arrival_timezone": segment.get("arrival_timezone"),
            "departure_terminal": segment.get("departure_terminal"),
            "arrival_terminal": segment.get("arrival_terminal"),
            "equipment_code": segment.get("aircraft_code"),
            "equipment_label": segment.get("aircraft_display_name"),
            "cabin": segment.get("cabin_code"),
            "booking_class": segment.get("booking_class_code"),
            "status_code": segment.get("status"),
            "source_confidence": 1.0,
            "source_segment_reference": segment.get("id"),
            "metadata": {"canonical_segment_snapshot": self._jsonable(segment)},
        }

    def _recognize_common_segment_line(self, line: str, default_year: Any = None) -> dict[str, Any] | None:
        text = re.sub(r"\s+", " ", line.strip().upper())
        patterns = [
            re.compile(r"^(?:\d+\s+)?(?P<carrier>[A-Z0-9]{2})\s*(?P<flight>\d{1,4}[A-Z]?)\s+(?:(?P<rbd>[A-Z])\s+)?(?P<date>\d{1,2}[A-Z]{3})\s+(?P<origin>[A-Z]{3})\s*(?P<destination>[A-Z]{3})\s+(?:(?P<status>[A-Z]{2}\d?)\s+)?(?P<departure>\d{4}|\d{1,2}:\d{2})\s+(?P<arrival>\d{4}|\d{1,2}:\d{2})$"),
            re.compile(r"^(?P<carrier>[A-Z0-9]{2})\s+(?P<flight>\d{1,4}[A-Z]?)\s+(?P<date>\d{1,2}[A-Z]{3})\s+(?P<origin>[A-Z]{3})\s+(?P<destination>[A-Z]{3})\s+(?P<departure>\d{4}|\d{1,2}:\d{2})\s+(?P<arrival>\d{4}|\d{1,2}:\d{2})$"),
            re.compile(r"^(?P<carrier>[A-Z0-9]{2})\s+(?P<flight>\d{1,4}[A-Z]?)\s+(?P<origin>[A-Z]{3})\s+(?P<destination>[A-Z]{3})$"),
        ]
        for pattern in patterns:
            match = pattern.match(text)
            if not match:
                continue
            values = match.groupdict()
            departure = self._combine_parser_datetime(values.get("date"), values.get("departure"), default_year)
            arrival = self._combine_parser_datetime(values.get("date"), values.get("arrival"), default_year)
            return {
                "marketing_carrier_code": values.get("carrier"),
                "marketing_flight_number": values.get("flight"),
                "booking_class": values.get("rbd"),
                "departure_airport_code": values.get("origin"),
                "arrival_airport_code": values.get("destination"),
                "departure_local_datetime": departure,
                "arrival_local_datetime": arrival,
                "status_code": values.get("status"),
                "source_confidence": 0.72 if departure else 0.55,
                "raw_segment_text": line.strip(),
                "metadata": {"fallback_pattern_recognizer": True, "date_requires_agent_confirmation": bool(values.get("date") and not default_year)},
            }
        return None

    def _combine_parser_datetime(self, date_value: Any, time_value: Any, default_year: Any) -> str | None:
        if not date_value or not time_value:
            return None
        date_text = str(date_value).strip().upper()
        time_text = str(time_value).strip().replace(":", "")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_text):
            try:
                return datetime.fromisoformat(f"{date_text}T{time_text[:2]}:{time_text[2:4]}:00").isoformat()
            except ValueError:
                return None
        if not default_year or not re.fullmatch(r"\d{1,2}[A-Z]{3}", date_text) or not re.fullmatch(r"\d{4}", time_text):
            return None
        try:
            return datetime.strptime(f"{date_text}{int(default_year)} {time_text}", "%d%b%Y %H%M").isoformat()
        except (TypeError, ValueError):
            return None

    def _calculate_draft(self, values: dict[str, Any]) -> dict[str, Any]:
        result = dict(values)
        result["marketing_carrier_code"] = self._upper_or_none(result.get("marketing_carrier_code"))
        result["operating_carrier_code"] = self._upper_or_none(result.get("operating_carrier_code"))
        result["departure_airport_code"] = self._upper_or_none(result.get("departure_airport_code"))
        result["arrival_airport_code"] = self._upper_or_none(result.get("arrival_airport_code"))
        departure_local = self._datetime(result.get("departure_local_datetime"))
        arrival_local = self._datetime(result.get("arrival_local_datetime"))
        departure_utc = self._explicit_utc(departure_local, result.get("departure_timezone"))
        arrival_utc = self._explicit_utc(arrival_local, result.get("arrival_timezone"))
        result["departure_local_datetime"] = departure_local
        result["arrival_local_datetime"] = arrival_local
        result["departure_utc"] = departure_utc
        result["arrival_utc"] = arrival_utc
        result["scheduled_duration_minutes"] = self._minutes(departure_utc, arrival_utc) if departure_utc and arrival_utc and arrival_utc >= departure_utc else None
        if departure_local and arrival_local:
            result["arrival_day_offset"] = (arrival_local.date() - departure_local.date()).days
            result["overnight_indicator"] = result["arrival_day_offset"] != 0
        result["surface_segment_indicator"] = bool(result.get("surface_segment_indicator") or result.get("segment_type") == "surface")
        result["codeshare_indicator"] = bool(result.get("marketing_carrier_code") and result.get("operating_carrier_code") and result.get("marketing_carrier_code") != result.get("operating_carrier_code"))
        completeness = self._completeness(result)
        result.update(completeness)
        return result

    def _validation_findings(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []

        def add(code: str, severity: str, category: str, message: str, segment_id: str | None = None, fields: list[str] | None = None, blocking: bool = False) -> None:
            findings.append({"segment_draft_id": segment_id, "validation_code": code, "severity": severity, "category": category, "message": message, "field_names": fields or [], "blocking": blocking})

        ordered = sorted(segments, key=lambda item: int(item.get("sequence") or 0))
        seen: dict[tuple[Any, ...], str] = {}
        for expected, item in enumerate(ordered, start=1):
            segment_id = item.get("id")
            if int(item.get("sequence") or 0) != expected:
                add("sequence_mismatch", "warning", "schedule", "Segment sequence has a gap or duplicate position.", segment_id, ["sequence"])
            if item.get("segment_type") == "flight":
                required = [
                    ("departure_airport_code", "missing_departure_airport", "Departure airport is required."),
                    ("arrival_airport_code", "missing_arrival_airport", "Arrival airport is required."),
                    ("departure_local_datetime", "missing_departure_datetime", "Departure local date and time are required."),
                    ("arrival_local_datetime", "missing_arrival_datetime", "Arrival local date and time are required or must be resolved by an agent."),
                    ("marketing_carrier_code", "missing_marketing_carrier", "Marketing carrier is required unless explicitly unknown."),
                    ("marketing_flight_number", "missing_flight_number", "Flight number is required unless explicitly unknown."),
                ]
                for field, code, message in required:
                    if item.get(field) in {None, ""}:
                        add(code, "error", "missing_information", message, segment_id, [field], True)
                for field in ["departure_airport_code", "arrival_airport_code"]:
                    if item.get(field) and not re.fullmatch(r"[A-Z]{3}", str(item[field])):
                        add("invalid_airport_code", "error", "format", "Airport codes must use three letters.", segment_id, [field], True)
                if item.get("marketing_carrier_code") and not re.fullmatch(r"[A-Z0-9]{2,3}", str(item["marketing_carrier_code"])):
                    add("invalid_airline_code", "error", "format", "Carrier code format requires manual correction.", segment_id, ["marketing_carrier_code"], True)
                if item.get("departure_local_datetime") and not item.get("departure_timezone") and not self._is_aware(self._datetime(item.get("departure_local_datetime"))):
                    add("missing_departure_timezone", "error", "missing_information", "Departure timezone is required for deterministic elapsed time.", segment_id, ["departure_timezone"], True)
                if item.get("arrival_local_datetime") and not item.get("arrival_timezone") and not self._is_aware(self._datetime(item.get("arrival_local_datetime"))):
                    add("missing_arrival_timezone", "error", "missing_information", "Arrival timezone is required for deterministic elapsed time.", segment_id, ["arrival_timezone"], True)
                departure_utc = self._datetime(item.get("departure_utc"))
                arrival_utc = self._datetime(item.get("arrival_utc"))
                if departure_utc and arrival_utc and arrival_utc < departure_utc:
                    add("invalid_segment_chronology", "critical", "schedule", "Arrival occurs before departure after timezone normalization.", segment_id, ["departure_local_datetime", "arrival_local_datetime"], True)
                if not item.get("operating_carrier_code"):
                    add("codeshare_review", "info", "operational_review", "Operating carrier is unknown; confirm when operational responsibility matters.", segment_id, ["operating_carrier_code"])
                elif item.get("codeshare_indicator"):
                    add("codeshare_review", "warning", "operational_review", "Marketing and operating carriers differ; carrier responsibility requires review.", segment_id, ["marketing_carrier_code", "operating_carrier_code"])
            signature = (
                item.get("marketing_carrier_code"), item.get("marketing_flight_number"), item.get("departure_airport_code"),
                item.get("arrival_airport_code"),
                str(item.get("departure_local_datetime")) if item.get("departure_local_datetime") else None,
                str(item.get("arrival_local_datetime")) if item.get("arrival_local_datetime") else None,
            )
            if any(signature) and signature in seen:
                add("duplicate_segment", "error", "schedule", "An identical segment draft already exists in this session.", segment_id, blocking=True)
            else:
                seen[signature] = str(segment_id)
        for inbound, outbound in zip(ordered, ordered[1:]):
            inbound_arrival = self._datetime(inbound.get("arrival_utc"))
            outbound_departure = self._datetime(outbound.get("departure_utc"))
            connection = self._minutes(inbound_arrival, outbound_departure) if inbound_arrival and outbound_departure else None
            outbound_id = outbound.get("id")
            if connection is not None and connection < 0:
                add("negative_connection", "critical", "schedule", "The next segment departs before the previous segment arrives.", outbound_id, ["departure_local_datetime"], True)
                add("segment_overlap", "error", "schedule", "Segment schedules overlap.", outbound_id, blocking=True)
            elif connection is not None and connection < 60:
                add("short_connection_review", "warning", "schedule", "Connection duration may require manual review; no minimum connection time is asserted.", outbound_id)
            elif connection is not None and connection > 480:
                add("long_connection_review", "info", "schedule", "Long connection duration may require manual review.", outbound_id)
            if inbound_arrival and outbound_departure and inbound_arrival.date() != outbound_departure.date():
                add("overnight_connection", "info", "schedule", "Connection crosses a calendar day.", outbound_id)
            if inbound.get("arrival_airport_code") and outbound.get("departure_airport_code") and inbound.get("arrival_airport_code") != outbound.get("departure_airport_code"):
                add("surface_discontinuity", "warning", "schedule", "The previous destination differs from the next origin; a surface gap or airport change requires review.", outbound_id, ["departure_airport_code"])
                add("airport_change", "warning", "schedule", "Airport change or surface transfer may be required.", outbound_id)
            if inbound.get("arrival_terminal") and outbound.get("departure_terminal") and inbound.get("arrival_terminal") != outbound.get("departure_terminal"):
                add("terminal_change", "info", "schedule", "A terminal change is indicated by the known terminal metadata.", outbound_id)
            if inbound.get("marketing_carrier_code") == outbound.get("marketing_carrier_code") and inbound.get("marketing_flight_number") == outbound.get("marketing_flight_number"):
                add("same_flight_continuation", "info", "carrier", "Adjacent segments use the same marketing flight number; continuation requires review.", outbound_id)
            carriers = {inbound.get("operating_carrier_code") or inbound.get("marketing_carrier_code"), outbound.get("operating_carrier_code") or outbound.get("marketing_carrier_code")}
            carriers.discard(None)
            if len(carriers) > 1:
                add("interline_review", "info", "operational_review", "Adjacent segments involve different carriers; no through-service or interline support is assumed.", outbound_id)
        return findings

    def _connection_preview(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        ordered = sorted(segments, key=lambda item: (str(item.get("option_group_key") or ""), int(item.get("sequence") or 0)))
        for inbound, outbound in zip(ordered, ordered[1:]):
            if inbound.get("option_group_key") != outbound.get("option_group_key"):
                continue
            inbound_arrival = self._datetime(inbound.get("arrival_utc"))
            outbound_departure = self._datetime(outbound.get("departure_utc"))
            minutes = self._minutes(inbound_arrival, outbound_departure) if inbound_arrival and outbound_departure else None
            airport_change = bool(inbound.get("arrival_airport_code") and outbound.get("departure_airport_code") and inbound.get("arrival_airport_code") != outbound.get("departure_airport_code"))
            results.append({
                "inbound_segment_draft_id": inbound.get("id"),
                "outbound_segment_draft_id": outbound.get("id"),
                "connection_minutes": minutes,
                "airport_code": inbound.get("arrival_airport_code"),
                "airport_change_required": airport_change,
                "terminal_change_required": bool(inbound.get("arrival_terminal") and outbound.get("departure_terminal") and inbound.get("arrival_terminal") != outbound.get("departure_terminal")),
                "overnight": bool(inbound_arrival and outbound_departure and inbound_arrival.date() != outbound_departure.date()),
                "manual_review_required": minutes is None or minutes < 60 or airport_change,
                "minimum_connection_time_asserted": False,
            })
        return results

    def _canonical_segment_payload(self, item: dict[str, Any], option_id: str, leg_id: str | None, session_id: str) -> dict[str, Any]:
        return {
            "itinerary_option_id": option_id,
            "leg_id": leg_id,
            "segment_number": item.get("sequence"),
            "source_entity_type": "journey_authoring_session",
            "source_entity_id": session_id,
            "source_segment_id": item.get("id"),
            "segment_type": item.get("segment_type") or "flight",
            "marketing_carrier_code": item.get("marketing_carrier_code"),
            "marketing_flight_number": item.get("marketing_flight_number"),
            "operating_carrier_code": item.get("operating_carrier_code"),
            "operating_flight_number": item.get("operating_flight_number"),
            "origin_airport_code": item.get("departure_airport_code"),
            "destination_airport_code": item.get("arrival_airport_code"),
            "departure_local": item.get("departure_local_datetime"),
            "arrival_local": item.get("arrival_local_datetime"),
            "departure_timezone": item.get("departure_timezone"),
            "arrival_timezone": item.get("arrival_timezone"),
            "departure_utc": item.get("departure_utc"),
            "arrival_utc": item.get("arrival_utc"),
            "scheduled_duration_minutes": item.get("scheduled_duration_minutes"),
            "aircraft_code": item.get("equipment_code"),
            "aircraft_display_name": item.get("equipment_label"),
            "departure_terminal": item.get("departure_terminal"),
            "arrival_terminal": item.get("arrival_terminal"),
            "cabin_code": item.get("cabin"),
            "booking_class_code": item.get("booking_class"),
            "status": "proposed",
            "manual_review_required": bool(item.get("blocking_errors") or item.get("warnings")),
            "warning_codes": list(item.get("warnings") or []),
            "manually_adjusted": item.get("review_status") in {"agent_confirmed", "agent_overridden"},
            "source_provenance": {"source_type": "journey_authoring_session", "source_reference": session_id, "source_segment_draft_id": item.get("id"), "raw_source_id": item.get("source_id"), "agent_confirmed": item.get("review_status") == "agent_confirmed"},
            "metadata": {"authoring_session_id": session_id, "authoring_segment_draft_id": item.get("id"), "fare_family_code": item.get("fare_family_code"), "status_code": item.get("status_code")},
        }

    def _completeness(self, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("segment_type") != "flight":
            fields = ["departure_airport_code", "arrival_airport_code"]
            score = round(sum(1 for field in fields if values.get(field) not in {None, ""}) / len(fields) * 100)
        else:
            score = sum(weight for field, weight in REQUIRED_FLIGHT_FIELDS.items() if values.get(field) not in {None, ""})
        status = "complete" if score == 100 else "partial" if score >= 50 else "incomplete"
        blocking = [field for field in ["departure_airport_code", "arrival_airport_code", "departure_local_datetime", "arrival_local_datetime"] if values.get(field) in {None, ""}]
        warnings = []
        if values.get("segment_type") == "flight" and not values.get("operating_carrier_code"):
            warnings.append("operating_carrier_unknown")
        if values.get("departure_local_datetime") and not values.get("departure_timezone") and not self._is_aware(self._datetime(values.get("departure_local_datetime"))):
            warnings.append("departure_timezone_unknown")
        if values.get("arrival_local_datetime") and not values.get("arrival_timezone") and not self._is_aware(self._datetime(values.get("arrival_local_datetime"))):
            warnings.append("arrival_timezone_unknown")
        return {"completeness_score": score, "completeness_status": status, "blocking_errors": blocking, "warnings": sorted(set([*(values.get("warnings") or []), *warnings]))}

    async def _refresh_session_summary(self, agency_id: str, session_id: str, *, normalized_hash: str | None = None) -> dict[str, Any]:
        session = await self._require_session(agency_id, session_id)
        segments = await self.list_segment_drafts(agency_id, session_id)
        validations = await self.db.collection(VALIDATION_COLLECTION).find_many({"agency_id": agency_id, "authoring_session_id": session_id})
        active_validations = [item for item in validations if not item.get("resolved_at") and not item.get("superseded_at")]
        blocking = sum(bool(item.get("blocking")) for item in active_validations)
        warnings = sum(item.get("severity") == "warning" for item in active_validations)
        score = round(sum(int(item.get("completeness_score") or 0) for item in segments) / len(segments)) if segments else 0
        updates = {
            "completeness_score": score,
            "blocking_errors_count": blocking,
            "warnings_count": warnings,
            "validation_summary": {"total": len(active_validations), "blocking": blocking, "warnings": warnings, "severity_counts": self._counts(active_validations, "severity")},
        }
        if normalized_hash:
            updates["normalized_hash"] = normalized_hash
        if session.get("status") not in {"archived", "applied"} and segments:
            updates["status"] = "requires_review" if blocking or warnings or score < 100 else "ready_to_apply"
        updated = await self.db.collection(SESSION_COLLECTION).update_one({"id": session_id, "agency_id": agency_id}, updates)
        return updated or {**session, **updates}

    async def _record_provenance(
        self,
        agency_id: str,
        session_id: str,
        segment_id: str,
        field_name: str,
        raw_value: Any,
        normalized_value: Any,
        value_status: str,
        source_type: str,
        user: dict[str, Any],
        *,
        source_reference: str | None,
        parser_confidence: float | None = None,
        enrichment_source_type: str | None = None,
        enrichment_source_id: str | None = None,
    ) -> dict[str, Any]:
        model = JourneyFieldProvenance(
            agency_id=agency_id,
            authoring_session_id=session_id,
            segment_draft_id=segment_id,
            field_name=field_name,
            raw_value=self._jsonable(raw_value),
            normalized_value=self._jsonable(normalized_value),
            confirmed_value=self._jsonable(normalized_value) if value_status in {"agent_confirmed", "agent_overridden"} else None,
            value_status=value_status,
            source_type=source_type,
            source_reference=source_reference,
            parser_confidence=parser_confidence,
            enrichment_source_type=enrichment_source_type,
            enrichment_source_id=enrichment_source_id,
            changed_by=self._actor(user),
        )
        return await self.db.collection(PROVENANCE_COLLECTION).insert_one(model.model_dump(mode="json"))

    async def _record_correction(self, agency_id: str, session_id: str, segment_id: str | None, field_name: str | None, correction_type: str, previous_value: Any, new_value: Any, user: dict[str, Any], reason: str) -> dict[str, Any]:
        model = JourneyAuthoringCorrection(
            agency_id=agency_id,
            authoring_session_id=session_id,
            segment_draft_id=segment_id,
            field_name=field_name,
            correction_type=correction_type,
            previous_value=self._jsonable(previous_value),
            new_value=self._jsonable(new_value),
            reason=reason,
            corrected_by=self._actor(user),
        )
        return await self.db.collection(CORRECTION_COLLECTION).insert_one(model.model_dump(mode="json"))

    async def _field_agent_confirmed(self, agency_id: str, session_id: str, segment_id: str, field_name: str) -> bool:
        items = await self.db.collection(PROVENANCE_COLLECTION).find_many({"agency_id": agency_id, "authoring_session_id": session_id, "segment_draft_id": segment_id, "field_name": field_name})
        items.sort(key=lambda item: str(item.get("changed_at") or item.get("created_at") or ""), reverse=True)
        return bool(items and items[0].get("value_status") in {"agent_confirmed", "agent_overridden"})

    async def _require_session(self, agency_id: str, session_id: str) -> dict[str, Any]:
        item = await self.db.collection(SESSION_COLLECTION).find_one({"id": session_id, "agency_id": agency_id})
        if not item:
            raise JourneyAuthoringError("Journey authoring session was not found for this agency.")
        return item

    async def _require_editable_session(self, agency_id: str, session_id: str) -> dict[str, Any]:
        item = await self._require_session(agency_id, session_id)
        if item.get("status") == "archived":
            raise JourneyAuthoringError("Archived authoring sessions cannot be changed.")
        return item

    async def _require_draft(self, agency_id: str, session_id: str, segment_id: str) -> dict[str, Any]:
        item = await self.db.collection(DRAFT_COLLECTION).find_one({"id": segment_id, "agency_id": agency_id, "authoring_session_id": session_id})
        if not item:
            raise JourneyAuthoringError("Segment draft was not found for this agency session.")
        return item

    async def _active_draft_count(self, agency_id: str, session_id: str) -> int:
        return len(await self.list_segment_drafts(agency_id, session_id))

    def _reference_map(self, references: list[dict[str, Any]], domain: str) -> dict[str, dict[str, Any]]:
        result = {}
        for item in references:
            if str(item.get("domain") or "").lower() != domain:
                continue
            code = str(item.get("code") or item.get("key") or "").upper()
            if code:
                result[code] = item
        return result

    def _reference_value(self, reference: dict[str, Any], key: str) -> Any:
        metadata = reference.get("metadata_json") or reference.get("metadata") or {}
        if key == "label":
            return reference.get("label") or metadata.get("name") or metadata.get("display_name")
        aliases = {
            "city": ["city", "city_name", "municipality"],
            "country": ["country", "country_name", "country_code"],
            "timezone": ["timezone", "time_zone", "iana_timezone"],
        }
        for candidate in aliases.get(key, [key]):
            if metadata.get(candidate) not in {None, ""}:
                return metadata[candidate]
        return None

    def _group_segments(self, segments: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in segments:
            grouped.setdefault(str(item.get("option_group_key") or "option-1"), []).append(item)
        return grouped

    def _explicit_utc(self, local_value: datetime | None, timezone_name: Any) -> datetime | None:
        if not local_value:
            return None
        if local_value.tzinfo is not None and local_value.utcoffset() is not None:
            return local_value.astimezone(timezone.utc)
        if not timezone_name:
            return None
        try:
            return local_value.replace(tzinfo=ZoneInfo(str(timezone_name))).astimezone(timezone.utc)
        except (ZoneInfoNotFoundError, ValueError):
            return None

    def _datetime(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    def _is_aware(self, value: datetime | None) -> bool:
        return bool(value and value.tzinfo is not None and value.utcoffset() is not None)

    def _minutes(self, start: datetime | None, end: datetime | None) -> int | None:
        if not start or not end:
            return None
        return int((end - start).total_seconds() // 60)

    def _agency_safe_source(self, source: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in source.items() if key != "restricted_metadata"}

    def _payload(self, payload: BaseModel | dict[str, Any]) -> dict[str, Any]:
        return payload.model_dump(exclude_unset=True) if isinstance(payload, BaseModel) else dict(payload or {})

    def _jsonable(self, value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {str(key): self._jsonable(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._jsonable(item) for item in value]
        return value

    def _hash(self, value: Any) -> str:
        return sha256(json.dumps(self._jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()

    def _counts(self, items: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
        result: dict[str, int] = {}
        for item in items:
            value = str(item.get(key) or "unknown")
            result[value] = result.get(value, 0) + 1
        return result

    def _actor(self, user: dict[str, Any]) -> str | None:
        return user.get("id") or user.get("email")

    def _token(self, value: Any) -> str:
        return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")

    def _upper_or_none(self, value: Any) -> str | None:
        text = str(value or "").strip().upper()
        return text or None

    def _present(self, value: Any) -> bool:
        return value is not None and value != ""

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _response(self, key: str, value: dict[str, Any]) -> dict[str, Any]:
        return {"phase": PHASE_LABEL, key: value, **self.safety_flags()}
