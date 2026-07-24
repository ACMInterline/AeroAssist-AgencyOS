from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    AuditEvent,
    BookingCreateFromReadinessRequest,
    BookingExecutionInstruction,
    OfferBookingHandoff,
    OfferBookingHandoffBookingCreateRequest,
    OfferBookingHandoffBuildRequest,
    OfferBookingHandoffCheck,
    OfferBookingHandoffMapping,
    OperationalDeadlineCreate,
    OperationalTaskAutomationRunRequest,
    OperationalTimelineCreate,
    OperationalWorkflowEvent,
    OperationalWorkflowInstance,
    new_id,
)
from services.agent_work_queue_service import AgentWorkQueueService
from services.booking_workspace_service import BookingWorkspaceService
from services.operational_sla_deadline_service import OperationalSlaDeadlineService
from services.task_automation_dependency_service import TaskAutomationDependencyService
from services.timeline_workspace_service import OperationalTimelineService
from services.airline_distribution_capability_service import AirlineDistributionCapabilityService


from build_phase import CURRENT_BUILD_PHASE

PHASE_LABEL = CURRENT_BUILD_PHASE

OFFER_BOOKING_HANDOFFS_COLLECTION = "offer_booking_handoffs"
OFFER_BOOKING_HANDOFF_CHECKS_COLLECTION = "offer_booking_handoff_checks"
OFFER_BOOKING_HANDOFF_MAPPINGS_COLLECTION = "offer_booking_handoff_mappings"
BOOKING_EXECUTION_INSTRUCTIONS_COLLECTION = "booking_execution_instructions"

HANDOFF_STATUSES = ["draft", "assessing", "blocked", "conditional", "ready", "handed_off", "booking_created", "failed", "cancelled"]
HANDOFF_CHECK_STATUSES = ["pending", "passed", "warning", "blocked"]
HANDOFF_MAPPING_TYPES = [
    "accepted_offer_to_readiness",
    "passenger_to_booking_passenger",
    "segment_to_booking_segment",
    "service_to_booking_service",
    "document_requirement_to_booking_instruction",
    "approval_requirement_to_booking_instruction",
    "pricing_trace_to_booking",
    "handoff_to_booking_workspace",
]
BOOKING_MODES = ["manual", "pnr_import", "imported_gds", "imported_confirmation", "supplier_reference"]
INSTRUCTION_TYPES = ["manual_booking", "pnr_import", "import_review", "supplier_reference", "ticket_emd_expectation"]


class OfferToBookingHandoffError(ValueError):
    pass


class OfferToBookingHandoffService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.booking_workspaces = BookingWorkspaceService(db)
        self.work_queue = AgentWorkQueueService(db)
        self.deadlines = OperationalSlaDeadlineService(db)
        self.task_automation = TaskAutomationDependencyService(db)
        self.timelines = OperationalTimelineService(db)
        self.distribution_capabilities = AirlineDistributionCapabilityService(db)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "offer_to_booking_handoff_readiness_foundation": True,
            "accepted_offer_snapshot_required": True,
            "accepted_offer_snapshot_reused": True,
            "mutable_offer_reconstruction_disabled": True,
            "booking_readiness_package_reused": True,
            "internal_client_trace_separation_enabled": True,
            "duplicate_handoff_prevention_enabled": True,
            "manual_booking_path_supported": True,
            "imported_booking_path_supported": True,
            "booking_execution_disabled": True,
            "provider_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "payment_processing_disabled": True,
            "external_api_calls_disabled": True,
            "background_workers_disabled": True,
            "ai_disabled": True,
            "human_authority_final": True,
        }

    async def platform_dashboard(self, **filters: Any) -> dict[str, Any]:
        handoffs = await self.list_handoffs(**filters)
        return {
            "phase": PHASE_LABEL,
            "summary": await self.summary(**filters),
            "items": handoffs[:50],
            "recent_checks": await self.list_checks(agency_id=filters.get("agency_id")),
            "recent_mappings": await self.list_mappings(agency_id=filters.get("agency_id")),
            "recent_instructions": await self.list_instructions(agency_id=filters.get("agency_id")),
            "platform_read_only_diagnostics": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_dashboard(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        scoped = {key: value for key, value in filters.items() if key != "agency_id"}
        handoffs = await self.list_handoffs(agency_id=agency_id, **scoped)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": await self.summary(agency_id=agency_id, **scoped),
            "items": handoffs,
            "recent_checks": await self.list_checks(agency_id=agency_id),
            "recent_mappings": await self.list_mappings(agency_id=agency_id),
            "recent_instructions": await self.list_instructions(agency_id=agency_id),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def build_handoff(self, payload: OfferBookingHandoffBuildRequest | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        data = self._payload(payload)
        if agency_id:
            data["agency_id"] = agency_id
        if not data.get("agency_id"):
            raise OfferToBookingHandoffError("Agency id is required for offer-to-booking handoff metadata.")
        data["booking_mode"] = self._norm(data.get("booking_mode") or "manual")
        if data["booking_mode"] not in BOOKING_MODES:
            raise OfferToBookingHandoffError(f"Unsupported booking mode metadata: {data['booking_mode']}.")

        context = await self._resolve_context(data)
        idempotency_key = data.get("idempotency_key") or self._idempotency_key(context, data)
        if not data.get("force_rebuild"):
            existing = await self.db.collection(OFFER_BOOKING_HANDOFFS_COLLECTION).find_one({"agency_id": data["agency_id"], "idempotency_key": idempotency_key})
            if existing and existing.get("handoff_status") not in {"failed", "cancelled"}:
                return {
                    "phase": PHASE_LABEL,
                    "handoff": await self.get_handoff(existing["id"], agency_id=data["agency_id"]),
                    "idempotent_reused": True,
                    "metadata_only": True,
                    **self.safety_flags(),
                }

        checks = self._calculate_checks(context, data)
        handoff_status = self._status_from_checks(checks)
        accepted_snapshot = self._accepted_snapshot(context)
        readiness_snapshot = self._readiness_snapshot(context)
        trace = self._trace_snapshots(context, checks)
        handoff = OfferBookingHandoff(
            agency_id=data["agency_id"],
            handoff_reference=self._handoff_reference(),
            acceptance_id=(context.get("acceptance") or {}).get("id"),
            booking_readiness_package_id=(context.get("readiness") or {}).get("id"),
            trip_accepted_offer_snapshot_id=(context.get("trip_snapshot") or {}).get("id"),
            trip_id=context.get("trip_id"),
            request_id=(context.get("acceptance") or context.get("readiness") or {}).get("request_id"),
            offer_workspace_id=(context.get("acceptance") or context.get("readiness") or {}).get("workspace_id"),
            offer_option_id=(context.get("acceptance") or context.get("readiness") or {}).get("option_id"),
            handoff_status=handoff_status,
            readiness_status=(context.get("readiness") or {}).get("status") or "draft",
            provider_target=self._norm(data.get("provider_target") or (context.get("readiness") or {}).get("provider_target") or "manual"),
            booking_mode=data["booking_mode"],
            idempotency_key=idempotency_key,
            blocker_count=len([check for check in checks if check["status"] == "blocked"]),
            warning_count=len([check for check in checks if check["status"] == "warning"]),
            check_count=len(checks),
            accepted_offer_snapshot_json=accepted_snapshot,
            readiness_snapshot_json=readiness_snapshot,
            policy_trace_json=trace["policy_trace_json"],
            pricing_trace_json=trace["pricing_trace_json"],
            internal_trace_json=trace["internal_trace_json"],
            client_trace_json=trace["client_trace_json"],
            booking_execution_snapshot_json={
                "booking_mode": data["booking_mode"],
                "provider_target": data.get("provider_target"),
                "distribution_capability_planning": context.get("distribution_capability") or {},
                "no_provider_execution": True,
            },
            created_by=user.get("id"),
            updated_by=user.get("id"),
            metadata={**(data.get("metadata") or {}), "notes": data.get("notes")},
        )
        created = await self.db.collection(OFFER_BOOKING_HANDOFFS_COLLECTION).insert_one(handoff.model_dump(mode="json"))
        check_records = await self._store_checks(created, checks, user)
        mapping_records = await self._store_mappings(created, context, user)
        instruction_records = await self._store_instructions(created, context, data, mapping_records, user)
        integrations = await self._emit_handoff_integrations(created, context, checks, user)
        transition = self._transition_evidence(
            created,
            user,
            "accepted_offer",
            created.get("acceptance_id"),
            "offer_booking_handoff",
            created["id"],
            created.get("handoff_status") or "assessed",
            [check for check in checks if check["status"] in {"warning", "blocked"}],
        )
        await self._write_transition_audit(created, user, "offer_booking_handoff.created", transition)

        updated = await self.db.collection(OFFER_BOOKING_HANDOFFS_COLLECTION).update_one(
            {"id": created["id"]},
            {
                "mapping_count": len(mapping_records),
                "instruction_count": len(instruction_records),
                "integration_snapshot_json": integrations,
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        ) or created

        return {
            "phase": PHASE_LABEL,
            "handoff": {**updated, **self.safety_flags()},
            "checks": check_records,
            "mappings": mapping_records,
            "instructions": instruction_records,
            "integrations": integrations,
            "idempotent_reused": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def assess_handoff(self, handoff_id: str, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_handoff(handoff_id, agency_id=agency_id)
        payload = {
            "agency_id": existing["agency_id"],
            "acceptance_id": existing.get("acceptance_id"),
            "booking_readiness_package_id": existing.get("booking_readiness_package_id"),
            "trip_id": existing.get("trip_id"),
            "offer_workspace_id": existing.get("offer_workspace_id"),
            "offer_option_id": existing.get("offer_option_id"),
            "provider_target": existing.get("provider_target"),
            "booking_mode": existing.get("booking_mode") or "manual",
            "idempotency_key": existing.get("idempotency_key"),
            "force_rebuild": True,
            "metadata": {"reassessed_from_handoff_id": existing["id"]},
        }
        await self.db.collection(OFFER_BOOKING_HANDOFFS_COLLECTION).update_one({"id": existing["id"]}, {"handoff_status": "cancelled", "updated_by": user.get("id")})
        return await self.build_handoff(payload, user, agency_id=existing["agency_id"])

    async def create_booking_workspace(self, handoff_id: str, payload: OfferBookingHandoffBookingCreateRequest | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        handoff = await self._require_handoff(handoff_id, agency_id=agency_id)
        data = self._payload(payload)
        if handoff.get("handoff_status") == "blocked":
            raise OfferToBookingHandoffError("Blocked handoff metadata cannot create a booking workspace until blockers are remediated.")
        if handoff.get("handoff_status") == "conditional" and not data.get("allow_conditional", True):
            raise OfferToBookingHandoffError("Conditional handoff metadata requires explicit allow_conditional=true.")
        if handoff.get("booking_workspace_id"):
            booking_detail = await self.booking_workspaces.get_booking_workspace(
                handoff["agency_id"], handoff["booking_workspace_id"]
            )
            return {
                "phase": PHASE_LABEL,
                "handoff": await self.get_handoff(handoff["id"], agency_id=handoff["agency_id"]),
                "booking_workspace": booking_detail.get("booking_workspace") or {},
                "booking_result": booking_detail,
                "idempotent_reused": True,
                "metadata_only": True,
                **self.safety_flags(),
            }
        readiness_id = handoff.get("booking_readiness_package_id")
        if not readiness_id:
            raise OfferToBookingHandoffError("Booking readiness package metadata is required before booking workspace creation.")
        provider_target = self._norm(data.get("provider_target") or handoff.get("provider_target") or "manual")
        booking_result = await self.booking_workspaces.create_booking_workspace_from_readiness(
            handoff["agency_id"],
            BookingCreateFromReadinessRequest(
                booking_readiness_package_id=readiness_id,
                accepted_offer_snapshot_id=handoff.get(
                    "trip_accepted_offer_snapshot_id"
                ),
                offer_booking_handoff_id=handoff["id"],
                provider_target=provider_target,
                internal_notes=data.get("internal_notes") or "Created from Phase 54.6 offer-to-booking handoff metadata.",
                create_draft_record=bool(data.get("create_draft_record", True)),
            ),
            user,
        )
        if not booking_result:
            raise OfferToBookingHandoffError("Booking readiness package metadata was not found.")
        booking_workspace = booking_result.get("booking_workspace") or {}
        await self._store_booking_mapping(handoff, booking_workspace, user)
        integrations = await self._emit_booking_created_integrations(handoff, booking_workspace, user)
        transition = self._transition_evidence(
            handoff,
            user,
            "offer_booking_handoff",
            handoff["id"],
            "booking_workspace",
            booking_workspace["id"],
            "booking_created",
            [],
        )
        await self._write_transition_audit(handoff, user, "offer_booking_handoff.booking_created", transition)
        updated = await self.db.collection(OFFER_BOOKING_HANDOFFS_COLLECTION).update_one(
            {"id": handoff["id"]},
            {
                "handoff_status": "booking_created",
                "booking_workspace_id": booking_workspace.get("id"),
                "booking_record_id": booking_workspace.get("booking_record_id") or (booking_result.get("booking_record") or {}).get("id"),
                "provider_target": provider_target,
                "booking_mode": self._norm(data.get("booking_mode") or handoff.get("booking_mode") or "manual"),
                "booking_created_at": self._now(),
                "integration_snapshot_json": {**(handoff.get("integration_snapshot_json") or {}), **integrations},
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        ) or handoff
        await self.db.collection(BOOKING_EXECUTION_INSTRUCTIONS_COLLECTION).update_one(
            {"agency_id": handoff["agency_id"], "handoff_id": handoff["id"]},
            {"instruction_status": "booking_workspace_created", "booking_workspace_id": booking_workspace.get("id"), "updated_by": user.get("id")},
        )
        return {
            "phase": PHASE_LABEL,
            "handoff": await self._handoff_projection(updated),
            "booking_workspace": booking_workspace,
            "booking_result": booking_result,
            "integrations": integrations,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_handoff(self, handoff_id: str, agency_id: str | None = None) -> dict[str, Any]:
        handoff = await self._require_handoff(handoff_id, agency_id=agency_id)
        return await self._handoff_projection(handoff)

    async def list_handoffs(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        acceptance_id: str | None = None,
        booking_readiness_package_id: str | None = None,
        trip_id: str | None = None,
        offer_workspace_id: str | None = None,
        booking_workspace_id: str | None = None,
        booking_mode: str | None = None,
        include_cancelled: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        query = self._query(
            agency_id=agency_id,
            acceptance_id=acceptance_id,
            booking_readiness_package_id=booking_readiness_package_id,
            trip_id=trip_id,
            offer_workspace_id=offer_workspace_id,
            booking_workspace_id=booking_workspace_id,
        )
        if status:
            query["handoff_status"] = self._norm(status)
        if booking_mode:
            query["booking_mode"] = self._norm(booking_mode)
        records = await self.db.collection(OFFER_BOOKING_HANDOFFS_COLLECTION).find_many(query or None)
        if not include_cancelled:
            records = [item for item in records if item.get("handoff_status") != "cancelled"]
        records.sort(key=lambda item: self._sort_text(item.get("created_at")), reverse=True)
        return [await self._handoff_projection(record, include_children=True) for record in records]

    async def list_checks(self, agency_id: str | None = None, handoff_id: str | None = None, status: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
        query = self._query(agency_id=agency_id, handoff_id=handoff_id)
        if status:
            query["status"] = self._norm(status)
        if category:
            query["category"] = self._norm(category)
        records = await self.db.collection(OFFER_BOOKING_HANDOFF_CHECKS_COLLECTION).find_many(query or None)
        records.sort(key=lambda item: (self._status_order(item.get("status")), str(item.get("check_key") or "")))
        return [{**record, **self.safety_flags()} for record in records]

    async def list_mappings(self, agency_id: str | None = None, handoff_id: str | None = None, mapping_type: str | None = None, booking_workspace_id: str | None = None) -> list[dict[str, Any]]:
        query = self._query(agency_id=agency_id, handoff_id=handoff_id, booking_workspace_id=booking_workspace_id)
        if mapping_type:
            query["mapping_type"] = self._norm(mapping_type)
        records = await self.db.collection(OFFER_BOOKING_HANDOFF_MAPPINGS_COLLECTION).find_many(query or None)
        records.sort(key=lambda item: self._sort_text(item.get("created_at")))
        return [{**record, **self.safety_flags()} for record in records]

    async def list_instructions(self, agency_id: str | None = None, handoff_id: str | None = None, instruction_status: str | None = None, booking_mode: str | None = None) -> list[dict[str, Any]]:
        query = self._query(agency_id=agency_id, handoff_id=handoff_id)
        if instruction_status:
            query["instruction_status"] = self._norm(instruction_status)
        if booking_mode:
            query["booking_mode"] = self._norm(booking_mode)
        records = await self.db.collection(BOOKING_EXECUTION_INSTRUCTIONS_COLLECTION).find_many(query or None)
        records.sort(key=lambda item: self._sort_text(item.get("created_at")), reverse=True)
        return [{**record, **self.safety_flags()} for record in records]

    async def summary(self, **filters: Any) -> dict[str, Any]:
        handoffs = await self.list_handoffs(**filters)
        checks = await self.list_checks(agency_id=filters.get("agency_id"))
        instructions = await self.list_instructions(agency_id=filters.get("agency_id"))
        return {
            "handoff_count": len(handoffs),
            "check_count": len(checks),
            "mapping_count": sum(int(item.get("mapping_count") or 0) for item in handoffs),
            "instruction_count": len(instructions),
            "status_counts": self._counts(handoffs, "handoff_status", HANDOFF_STATUSES),
            "check_status_counts": self._counts(checks, "status", HANDOFF_CHECK_STATUSES),
            "booking_mode_counts": self._counts(handoffs, "booking_mode", BOOKING_MODES),
            "blocked_count": len([item for item in handoffs if item.get("handoff_status") == "blocked"]),
            "conditional_count": len([item for item in handoffs if item.get("handoff_status") == "conditional"]),
            "ready_count": len([item for item in handoffs if item.get("handoff_status") == "ready"]),
            "booking_created_count": len([item for item in handoffs if item.get("handoff_status") == "booking_created"]),
            "metadata_only": True,
        }

    async def _resolve_context(self, data: dict[str, Any]) -> dict[str, Any]:
        agency_id = data["agency_id"]
        readiness = None
        acceptance = None
        trip_snapshot = None
        if data.get("booking_readiness_package_id"):
            readiness = await self.db.collection("booking_readiness_packages").find_one({"agency_id": agency_id, "id": data["booking_readiness_package_id"]})
            if not readiness:
                raise OfferToBookingHandoffError("Booking readiness package metadata was not found for this agency.")
            if readiness.get("acceptance_id"):
                acceptance = await self.db.collection("offer_acceptances").find_one({"agency_id": agency_id, "id": readiness["acceptance_id"]})
        if not acceptance and data.get("acceptance_id"):
            acceptance = await self.db.collection("offer_acceptances").find_one({"agency_id": agency_id, "id": data["acceptance_id"]})
            if not acceptance:
                raise OfferToBookingHandoffError("Offer acceptance metadata was not found for this agency.")
        if not acceptance and data.get("offer_workspace_id"):
            acceptances = await self.db.collection("offer_acceptances").find_many({"agency_id": agency_id, "workspace_id": data["offer_workspace_id"], "status": "accepted"})
            acceptance = self._latest(acceptances)
        if not acceptance and data.get("trip_id"):
            acceptances = await self.db.collection("offer_acceptances").find_many({"agency_id": agency_id, "trip_id": data["trip_id"], "status": "accepted"})
            acceptance = self._latest(acceptances)
        if acceptance and not readiness:
            readiness = await self.db.collection("booking_readiness_packages").find_one({"agency_id": agency_id, "acceptance_id": acceptance["id"]})
        if not readiness and data.get("trip_id"):
            readiness = self._latest(await self.db.collection("booking_readiness_packages").find_many({"agency_id": agency_id, "trip_id": data["trip_id"]}))
        if acceptance:
            trip_snapshot = await self.db.collection("trip_accepted_offer_snapshots").find_one({"agency_id": agency_id, "acceptance_id": acceptance["id"]})
        if not acceptance or acceptance.get("status") != "accepted":
            raise OfferToBookingHandoffError(
                "An active exact-version OfferAcceptance is required before booking handoff."
            )
        if not trip_snapshot or trip_snapshot.get("acceptance_id") != acceptance.get("id"):
            raise OfferToBookingHandoffError(
                "The immutable accepted-offer snapshot is required before booking handoff."
            )
        if trip_snapshot.get("source_hash") != acceptance.get("accepted_payload_hash"):
            raise OfferToBookingHandoffError(
                "Accepted-offer snapshot integrity does not match the acceptance evidence."
            )
        trip_id = (readiness or {}).get("trip_id") or (acceptance or {}).get("trip_id") or data.get("trip_id")
        trip = await self.db.collection("trip_dossiers").find_one({"agency_id": agency_id, "id": trip_id}) if trip_id else None
        existing_booking = None
        if readiness:
            existing_booking = await self.db.collection("booking_workspaces").find_one({"agency_id": agency_id, "booking_readiness_package_id": readiness["id"]})
        airline_codes = self._distribution_airline_codes(readiness or {}, acceptance or {}, trip_snapshot or {})
        provider_target = self._norm(data.get("provider_target") or (readiness or {}).get("provider_target") or "")
        distribution_channel = "manual_offline_process" if provider_target == "manual" else provider_target or None
        distribution_capability = await self.distribution_capabilities.booking_handoff_summary(
            agency_id,
            airline_codes=airline_codes,
            channel_code=distribution_channel,
        )
        return {
            "agency_id": agency_id,
            "acceptance": acceptance,
            "readiness": readiness,
            "trip_snapshot": trip_snapshot,
            "trip_id": trip_id,
            "trip": trip,
            "existing_booking_workspace": existing_booking,
            "distribution_capability": distribution_capability,
        }

    def _calculate_checks(self, context: dict[str, Any], data: dict[str, Any]) -> list[dict[str, Any]]:
        acceptance = context.get("acceptance") or {}
        readiness = context.get("readiness") or {}
        trip_snapshot = context.get("trip_snapshot") or {}
        pricing = readiness.get("pricing_snapshot_json") or acceptance.get("accepted_pricing_snapshot_json") or {}
        pricing_summary = pricing.get("summary") or pricing
        fare_bundle = acceptance.get("accepted_fare_bundle_snapshot_json") or trip_snapshot.get("confirmed_fare_bundle_json") or {}
        segments = readiness.get("segments_snapshot_json") or trip_snapshot.get("confirmed_segments_json") or []
        passengers = readiness.get("passengers_snapshot_json") or trip_snapshot.get("confirmed_passengers_json") or []
        services = readiness.get("services_snapshot_json") or acceptance.get("accepted_services_snapshot_json") or {}
        required_documents = readiness.get("required_documents_json") or []
        policy_violations = readiness.get("policy_violations_json") or []
        warnings = readiness.get("warnings_json") or []
        rules = acceptance.get("rules_feasibility_snapshot_json") or {}
        ssr = readiness.get("ssr_json") or []
        osi = readiness.get("osi_json") or []
        distribution_capability = context.get("distribution_capability") or {}
        distribution_ready = bool(distribution_capability.get("available_channel_count"))
        checks = [
            self._check(
                "accepted_offer_snapshot",
                "Accepted offer snapshot exists",
                "snapshot",
                bool(
                    acceptance
                    and acceptance.get("status") == "accepted"
                    and trip_snapshot
                    and trip_snapshot.get("source_hash")
                    == acceptance.get("accepted_payload_hash")
                ),
                "Immutable accepted-offer snapshot is required before booking handoff.",
                blocked=not bool(trip_snapshot),
            ),
            self._check("trip_linkage", "Trip linkage", "trip", bool(context.get("trip_id")), "Accepted offer must be linked to a trip dossier.", blocked=not bool(context.get("trip_id"))),
            self._check("booking_readiness_package", "Booking readiness package", "readiness", bool(readiness), "Booking readiness package is required for controlled booking workspace creation.", blocked=not bool(readiness)),
            self._check("passenger_mapping", "Passenger mapping", "mapping", bool(passengers), "Passenger snapshot metadata should be present for booking handoff.", blocked=not bool(passengers)),
            self._check("segment_mapping", "Segment mapping", "mapping", bool(segments), "Segment snapshot metadata should be present for booking handoff.", blocked=not bool(segments)),
            self._check("pricing_resolution", "Pricing resolution", "pricing", pricing_summary.get("total_amount") is not None and bool(pricing_summary.get("currency")), "Accepted pricing must include total and currency.", blocked=pricing_summary.get("total_amount") is None),
            self._check("policy_evaluation", "Policy evaluation", "policy", bool(rules) and not policy_violations, "Policy evaluation should be traceable and free of blocking policy violations.", blocked=bool(policy_violations), warning=not bool(rules)),
            self._check("passenger_service_feasibility", "Passenger service feasibility", "service", bool(rules.get("service_feasibility") or services), "Service feasibility metadata should be carried from offer evidence.", warning=not bool(rules.get("service_feasibility") or services)),
            self._check("fare_cabin_baggage", "Fare, cabin, and baggage information", "fare", bool(fare_bundle) or any(item.get("cabin_class") or item.get("fare_basis") or item.get("booking_class") for item in segments), "Fare, cabin, booking class, or baggage metadata should be visible before handoff.", warning=True),
            self._check("airline_recommendation_trace", "Airline recommendation trace", "recommendation", bool(rules.get("recommendation") or rules.get("rules_summary") or (acceptance.get("client_visible_summary_json") or {}).get("option_label")), "Airline recommendation trace is advisory metadata and should remain linked where available.", warning=True),
            self._check("documents_and_approvals", "Approvals and documents", "documents", not required_documents, "Required documents or approvals remain human-reviewed prerequisites.", warning=bool(required_documents)),
            self._check("payment_invoice_prerequisite", "Payment and invoice prerequisite", "payment", pricing_summary.get("total_amount") is not None and bool(pricing_summary.get("currency")), "Payment/invoice prerequisite is metadata-only and must remain human reviewed.", warning=True),
            self._check(
                "supplier_gds_readiness",
                "Supplier/GDS/NDC planning readiness",
                "supplier",
                data.get("booking_mode") == "manual" or distribution_ready,
                "Published distribution capability metadata is advisory; no GDS/NDC/provider action will run.",
                warning=True,
                evidence={"distribution_capability": distribution_capability},
            ),
            self._check("booking_mode", "PNR/import/manual booking mode", "booking", data.get("booking_mode") in BOOKING_MODES, "Select manual, PNR import, supplier reference, or imported confirmation mode.", blocked=data.get("booking_mode") not in BOOKING_MODES),
            self._check("ticket_emd_expectations", "Ticket/EMD expectations", "ticket_emd", bool(ssr or osi or services or fare_bundle), "Ticket and EMD expectations remain metadata-only until later human action.", warning=not bool(ssr or osi or services or fare_bundle)),
            self._check("unresolved_blockers", "Unresolved blockers", "blockers", not bool(policy_violations), "Resolve policy violations or critical missing structures before handoff.", blocked=bool(policy_violations)),
        ]
        if warnings:
            checks.append(self._check("readiness_warnings", "Readiness warnings", "readiness", False, f"{len(warnings)} readiness warning(s) require human review.", warning=True, evidence={"warnings": warnings}))
        return checks

    def _check(self, key: str, label: str, category: str, passed: bool, guidance: str, *, blocked: bool = False, warning: bool = False, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
        if blocked:
            status = "blocked"
            severity = "critical"
        elif passed:
            status = "passed"
            severity = "info"
        elif warning:
            status = "warning"
            severity = "warning"
        else:
            status = "pending"
            severity = "info"
        return {
            "check_key": key,
            "label": label,
            "category": category,
            "status": status,
            "severity": severity,
            "details": guidance,
            "remediation_guidance": guidance if status in {"blocked", "warning", "pending"} else None,
            "evidence_snapshot_json": evidence or {},
        }

    async def _store_checks(self, handoff: dict[str, Any], checks: list[dict[str, Any]], user: dict) -> list[dict[str, Any]]:
        records = []
        for check in checks:
            record = OfferBookingHandoffCheck(
                agency_id=handoff["agency_id"],
                handoff_id=handoff["id"],
                acceptance_id=handoff.get("acceptance_id"),
                booking_readiness_package_id=handoff.get("booking_readiness_package_id"),
                created_by=user.get("id"),
                updated_by=user.get("id"),
                **check,
            )
            records.append(await self.db.collection(OFFER_BOOKING_HANDOFF_CHECKS_COLLECTION).insert_one(record.model_dump(mode="json")))
        return [{**record, **self.safety_flags()} for record in records]

    async def _store_mappings(self, handoff: dict[str, Any], context: dict[str, Any], user: dict) -> list[dict[str, Any]]:
        readiness = context.get("readiness") or {}
        acceptance = context.get("acceptance") or {}
        records: list[dict[str, Any]] = []

        async def add(mapping_type: str, source_type: str, source_id: str | None, target_type: str, target_id: str | None, snapshot: dict[str, Any] | list[Any] | None = None, notes: str | None = None) -> None:
            if not source_id and not target_id:
                return
            mapping = OfferBookingHandoffMapping(
                agency_id=handoff["agency_id"],
                handoff_id=handoff["id"],
                acceptance_id=handoff.get("acceptance_id"),
                booking_readiness_package_id=handoff.get("booking_readiness_package_id"),
                trip_id=handoff.get("trip_id"),
                mapping_type=mapping_type,
                source_entity_type=source_type,
                source_entity_id=str(source_id or "unresolved"),
                target_entity_type=target_type,
                target_entity_id=str(target_id or "unresolved"),
                mapping_status="mapped" if target_id else "unresolved",
                mapping_snapshot_json={"snapshot": snapshot or {}, "metadata_only": True},
                notes=notes,
                created_by=user.get("id"),
                updated_by=user.get("id"),
            )
            records.append(await self.db.collection(OFFER_BOOKING_HANDOFF_MAPPINGS_COLLECTION).insert_one(mapping.model_dump(mode="json")))

        await add("accepted_offer_to_readiness", "offer_acceptance", acceptance.get("id"), "booking_readiness_package", readiness.get("id"), {"acceptance": acceptance, "readiness": readiness})
        for passenger in readiness.get("passengers_snapshot_json") or []:
            await add(
                "passenger_to_booking_passenger",
                "accepted_offer_passenger",
                passenger.get("id") or passenger.get("source_request_passenger_id") or passenger.get("passenger_id"),
                "booking_passenger_snapshot",
                passenger.get("passenger_id") or passenger.get("id"),
                passenger,
            )
        for segment in readiness.get("segments_snapshot_json") or []:
            await add(
                "segment_to_booking_segment",
                "accepted_offer_segment",
                segment.get("id") or segment.get("source_request_segment_id") or segment.get("segment_key"),
                "booking_segment_snapshot",
                segment.get("id") or segment.get("segment_key"),
                segment,
            )
        services = readiness.get("services_snapshot_json") or {}
        for bucket, items in services.items():
            if isinstance(items, list):
                for service in items:
                    await add("service_to_booking_service", bucket, service.get("id") or service.get("service_code") or service.get("service_key"), "booking_service_snapshot", service.get("id") or service.get("service_code") or service.get("service_key"), service)
        for document in readiness.get("required_documents_json") or []:
            await add("document_requirement_to_booking_instruction", "required_document", document.get("id") or document.get("document_type") or document.get("code"), "booking_instruction", handoff["id"], document)
        for item in [*(readiness.get("ssr_json") or []), *(readiness.get("osi_json") or [])]:
            await add("approval_requirement_to_booking_instruction", "ssr_osi_preview", item.get("id") or item.get("code") or item.get("ssr_code"), "booking_instruction", handoff["id"], item)
        pricing = readiness.get("pricing_snapshot_json") or {}
        await add("pricing_trace_to_booking", "accepted_pricing_snapshot", handoff.get("acceptance_id"), "booking_pricing_snapshot", handoff["id"], pricing)
        return [{**record, **self.safety_flags()} for record in records]

    async def _store_instructions(self, handoff: dict[str, Any], context: dict[str, Any], data: dict[str, Any], mappings: list[dict[str, Any]], user: dict) -> list[dict[str, Any]]:
        readiness = context.get("readiness") or {}
        passenger_mappings = [item for item in mappings if item.get("mapping_type") == "passenger_to_booking_passenger"]
        segment_mappings = [item for item in mappings if item.get("mapping_type") == "segment_to_booking_segment"]
        booking_mode = self._norm(data.get("booking_mode") or handoff.get("booking_mode") or "manual")
        instruction_type = "manual_booking" if booking_mode == "manual" else ("pnr_import" if booking_mode == "pnr_import" else "import_review")
        steps = [
            {"step": 1, "label": "Open frozen accepted-offer snapshot", "execution_disabled": True},
            {"step": 2, "label": "Review passenger and segment mappings", "execution_disabled": True},
            {"step": 3, "label": "Review policy, service, document, approval, and pricing traces", "execution_disabled": True},
            {"step": 4, "label": f"Prepare {booking_mode.replace('_', ' ')} booking outside automated execution", "execution_disabled": True},
            {"step": 5, "label": "Record or import resulting booking metadata manually", "execution_disabled": True},
        ]
        instruction = BookingExecutionInstruction(
            agency_id=handoff["agency_id"],
            handoff_id=handoff["id"],
            acceptance_id=handoff.get("acceptance_id"),
            booking_readiness_package_id=handoff.get("booking_readiness_package_id"),
            instruction_reference=self._instruction_reference(),
            instruction_type=instruction_type,
            instruction_status="ready_for_manual_action" if handoff.get("handoff_status") in {"ready", "conditional"} else "blocked",
            provider_target=self._norm(data.get("provider_target") or readiness.get("provider_target") or "manual"),
            booking_mode=booking_mode,
            title="Booking execution instruction metadata",
            summary="Human-controlled booking handoff instructions. No live booking, provider call, ticketing, payment, or external execution runs.",
            instruction_steps=steps,
            passenger_mapping_json=passenger_mappings,
            segment_mapping_json=segment_mappings,
            ticket_expectations_json={"ticket_expected": True, "issuance_disabled": True, "source": "accepted_offer_handoff"},
            emd_expectations_json={"emd_possible": bool((readiness.get("services_snapshot_json") or {}) or readiness.get("ssr_json")), "issuance_disabled": True},
            supplier_readiness_json={
                "provider_target": readiness.get("provider_target") or data.get("provider_target") or "manual",
                "distribution_capability_planning": context.get("distribution_capability") or {},
                "live_connectivity_confirmed": False,
                "gds_ndc_execution_disabled": True,
            },
            pricing_trace_json=handoff.get("pricing_trace_json") or {},
            policy_trace_json=handoff.get("policy_trace_json") or {},
            internal_notes=data.get("notes"),
            created_by=user.get("id"),
            updated_by=user.get("id"),
        )
        created = await self.db.collection(BOOKING_EXECUTION_INSTRUCTIONS_COLLECTION).insert_one(instruction.model_dump(mode="json"))
        return [{**created, **self.safety_flags()}]

    async def _store_booking_mapping(self, handoff: dict[str, Any], booking_workspace: dict[str, Any], user: dict) -> dict[str, Any] | None:
        if not booking_workspace.get("id"):
            return None
        existing = await self.db.collection(OFFER_BOOKING_HANDOFF_MAPPINGS_COLLECTION).find_one({"agency_id": handoff["agency_id"], "handoff_id": handoff["id"], "mapping_type": "handoff_to_booking_workspace"})
        if existing:
            return existing
        mapping = OfferBookingHandoffMapping(
            agency_id=handoff["agency_id"],
            handoff_id=handoff["id"],
            acceptance_id=handoff.get("acceptance_id"),
            booking_readiness_package_id=handoff.get("booking_readiness_package_id"),
            trip_id=handoff.get("trip_id"),
            booking_workspace_id=booking_workspace.get("id"),
            mapping_type="handoff_to_booking_workspace",
            source_entity_type="offer_booking_handoff",
            source_entity_id=handoff["id"],
            target_entity_type="booking_workspace",
            target_entity_id=booking_workspace["id"],
            mapping_snapshot_json={"booking_workspace": booking_workspace, "metadata_only": True},
            created_by=user.get("id"),
            updated_by=user.get("id"),
        )
        return await self.db.collection(OFFER_BOOKING_HANDOFF_MAPPINGS_COLLECTION).insert_one(mapping.model_dump(mode="json"))

    async def _emit_handoff_integrations(self, handoff: dict[str, Any], context: dict[str, Any], checks: list[dict[str, Any]], user: dict) -> dict[str, Any]:
        workflow = OperationalWorkflowInstance(
            agency_id=handoff["agency_id"],
            workflow_definition_id="default:booking_readiness_default:1.0",
            entity_type="booking",
            entity_id=handoff["id"],
            current_state="not_started" if handoff.get("handoff_status") == "blocked" else "readiness_review",
            workflow_status="active",
            context_snapshot_json={"handoff_id": handoff["id"], "acceptance_id": handoff.get("acceptance_id"), "booking_readiness_package_id": handoff.get("booking_readiness_package_id"), "metadata_only": True},
            active_blockers_json=[check for check in checks if check["status"] == "blocked"],
            active_warnings_json=[check for check in checks if check["status"] == "warning"],
            created_by=user.get("id"),
            updated_by=user.get("id"),
            metadata={"source": "offer_to_booking_handoff"},
        )
        workflow_record = await self.db.collection("operational_workflow_instances").insert_one(workflow.model_dump(mode="json"))
        event = OperationalWorkflowEvent(
            agency_id=handoff["agency_id"],
            workflow_instance_id=workflow_record["id"],
            event_type="offer_booking_handoff_assessed",
            event_code="offer_booking_handoff_assessed",
            source_module="offer_to_booking_handoff",
            source_entity_type="offer_booking_handoff",
            source_entity_id=handoff["id"],
            payload_json={"handoff_status": handoff.get("handoff_status"), "metadata_only": True},
        )
        workflow_event = await self.db.collection("operational_workflow_events").insert_one(event.model_dump(mode="json"))
        work_item = await self.work_queue.generate_work_item(
            {
                "agency_id": handoff["agency_id"],
                "work_item_type": "accepted_offer_awaiting_booking",
                "source_entity_type": "offer_booking_handoff",
                "source_entity_id": handoff["id"],
                "workflow_instance_id": workflow_record["id"],
                "workflow_event_id": workflow_event["id"],
                "title": "Review accepted offer booking handoff",
                "summary": "Review accepted-offer snapshot, booking readiness, blockers, warnings, and booking instructions before creating/opening a booking workspace.",
                "priority": "high",
                "severity": "critical" if handoff.get("handoff_status") == "blocked" else "medium",
                "queue_code": "blocked" if handoff.get("handoff_status") == "blocked" else "unassigned",
                "sla_status": "on_track",
                "blocker_status": "blocked" if handoff.get("handoff_status") == "blocked" else ("waiting_documents" if any(check["check_key"] == "documents_and_approvals" and check["status"] == "warning" for check in checks) else "not_blocked"),
                "generation_reason": "Offer-to-booking handoff readiness generated work-item metadata.",
                "source_snapshot_json": {"handoff": handoff, "checks": checks},
            },
            user,
            agency_id=handoff["agency_id"],
        )
        task_run = await self.task_automation.run_automation(
            OperationalTaskAutomationRunRequest(
                agency_id=handoff["agency_id"],
                trigger_event="offer_accepted",
                source_entity_type="offer_booking_handoff",
                source_entity_id=handoff["id"],
                request_id=handoff.get("request_id") or handoff["id"],
                template_codes=["create_booking_readiness_check", "invoice_payment_follow_up"],
                event_snapshot_json={"source_label": handoff.get("handoff_reference"), "handoff_status": handoff.get("handoff_status"), "workflow_instance_id": workflow_record["id"]},
                idempotency_key=f"{handoff['id']}:offer_accepted",
            ),
            user,
            agency_id=handoff["agency_id"],
        )
        deadline = await self.deadlines.create_deadline(
            OperationalDeadlineCreate(
                agency_id=handoff["agency_id"],
                source_entity_type="offer_booking_handoff",
                source_entity_id=handoff["id"],
                workflow_instance_id=workflow_record["id"],
                workflow_event_id=workflow_event["id"],
                work_item_id=(work_item.get("work_item") or {}).get("id"),
                deadline_type="booking_ticketing_deadline",
                priority="high",
                source_snapshot_json={"handoff_status": handoff.get("handoff_status"), "metadata_only": True},
            ),
            user,
            agency_id=handoff["agency_id"],
        )
        timeline = await self.timelines.create_entry(
            OperationalTimelineCreate(
                agency_id=handoff["agency_id"],
                created_by=user.get("id"),
                trip_workspace_id=handoff.get("trip_id"),
                event_type="Offer accepted",
                event_category="booking_handoff",
                event_source="offer_to_booking_handoff",
                event_status=handoff.get("handoff_status"),
                event_priority="high",
                operational_stage="booking_readiness",
                summary="Offer-to-booking handoff readiness metadata was assessed.",
                internal_only=True,
                operational_notes="No booking, provider, payment, ticketing, messaging, or external execution occurred.",
                metadata={
                    "handoff_id": handoff["id"],
                    "workflow_instance_id": workflow_record["id"],
                    **self._transition_evidence(
                        handoff,
                        user,
                        "accepted_offer",
                        handoff.get("acceptance_id"),
                        "offer_booking_handoff",
                        handoff["id"],
                        handoff.get("handoff_status") or "assessed",
                        [check for check in checks if check["status"] in {"warning", "blocked"}],
                    ),
                },
            ),
            user,
        )
        return {
            "workflow_instance_id": workflow_record["id"],
            "workflow_event_id": workflow_event["id"],
            "work_item_id": (work_item.get("work_item") or {}).get("id"),
            "task_automation_run_id": (task_run.get("run") or {}).get("id"),
            "deadline_id": (deadline.get("deadline") or {}).get("id"),
            "timeline_entry_id": (timeline.get("timeline_entry") or {}).get("id"),
            "metadata_only": True,
        }

    async def _emit_booking_created_integrations(self, handoff: dict[str, Any], booking_workspace: dict[str, Any], user: dict) -> dict[str, Any]:
        work_item = await self.work_queue.generate_work_item(
            {
                "agency_id": handoff["agency_id"],
                "work_item_type": "booking_awaiting_ticketing",
                "source_entity_type": "booking_workspace",
                "source_entity_id": booking_workspace["id"],
                "title": "Review booking workspace for ticketing/EMD expectations",
                "summary": "Booking workspace metadata was created from accepted-offer handoff. Review ticket, EMD, payment, and document prerequisites manually.",
                "priority": "high",
                "severity": "medium",
                "queue_code": "unassigned",
                "sla_status": "on_track",
                "blocker_status": "not_blocked",
                "generation_reason": "Booking workspace created from offer-to-booking handoff metadata.",
                "source_snapshot_json": {"handoff_id": handoff["id"], "booking_workspace_id": booking_workspace["id"]},
            },
            user,
            agency_id=handoff["agency_id"],
        )
        deadline = await self.deadlines.create_deadline(
            {
                "agency_id": handoff["agency_id"],
                "source_entity_type": "booking_workspace",
                "source_entity_id": booking_workspace["id"],
                "work_item_id": (work_item.get("work_item") or {}).get("id"),
                "deadline_type": "ticketing_deadline",
                "priority": "high",
                "source_snapshot_json": {"handoff_id": handoff["id"], "booking_workspace_id": booking_workspace["id"], "metadata_only": True},
            },
            user,
            agency_id=handoff["agency_id"],
        )
        timeline = await self.timelines.create_entry(
            OperationalTimelineCreate(
                agency_id=handoff["agency_id"],
                created_by=user.get("id"),
                trip_workspace_id=handoff.get("trip_id"),
                booking_workspace_id=booking_workspace["id"],
                event_type="Booking created",
                event_category="booking_handoff",
                event_source="offer_to_booking_handoff",
                event_status="recorded",
                event_priority="high",
                operational_stage="booking_workspace",
                summary="Booking workspace metadata was created from offer-to-booking handoff.",
                internal_only=True,
                operational_notes="No live booking, provider call, ticket issuance, payment, or external execution occurred.",
                metadata={
                    "handoff_id": handoff["id"],
                    "booking_workspace_id": booking_workspace["id"],
                    **self._transition_evidence(
                        handoff,
                        user,
                        "offer_booking_handoff",
                        handoff["id"],
                        "booking_workspace",
                        booking_workspace["id"],
                        "booking_created",
                        [],
                    ),
                },
            ),
            user,
        )
        return {
            "booking_work_item_id": (work_item.get("work_item") or {}).get("id"),
            "ticketing_deadline_id": (deadline.get("deadline") or {}).get("id"),
            "booking_timeline_entry_id": (timeline.get("timeline_entry") or {}).get("id"),
            "metadata_only": True,
        }

    def _accepted_snapshot(self, context: dict[str, Any]) -> dict[str, Any]:
        acceptance = context.get("acceptance") or {}
        trip_snapshot = context.get("trip_snapshot") or {}
        return {
            "acceptance": self._snapshot(acceptance),
            "trip_accepted_offer_snapshot": self._snapshot(trip_snapshot),
            "pricing": self._snapshot(acceptance.get("accepted_pricing_snapshot_json") or trip_snapshot.get("confirmed_pricing_json") or {}),
            "routing": self._snapshot(acceptance.get("accepted_routing_snapshot_json") or {"segments": trip_snapshot.get("confirmed_segments_json") or []}),
            "fare_bundle": self._snapshot(acceptance.get("accepted_fare_bundle_snapshot_json") or trip_snapshot.get("confirmed_fare_bundle_json") or {}),
            "services": self._snapshot(acceptance.get("accepted_services_snapshot_json") or trip_snapshot.get("confirmed_services_json") or {}),
            "pets": self._snapshot(acceptance.get("accepted_pets_snapshot_json") or trip_snapshot.get("confirmed_pets_json") or {}),
            "special_items": self._snapshot(acceptance.get("accepted_special_items_snapshot_json") or trip_snapshot.get("confirmed_special_items_json") or {}),
            "captured_from_frozen_acceptance": True,
            "mutable_offer_reconstruction_disabled": True,
            "metadata_only": True,
        }

    def _transition_evidence(
        self,
        handoff: dict[str, Any],
        user: dict,
        source_type: str,
        source_id: str | None,
        target_type: str,
        target_id: str,
        result: str,
        warnings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "agency_id": handoff["agency_id"],
            "actor_user_id": user.get("id"),
            "source_entity_type": source_type,
            "source_entity_id": source_id,
            "target_entity_type": target_type,
            "target_entity_id": target_id,
            "correlation_id": f"accepted-offer:{handoff.get('acceptance_id') or 'unknown'}:handoff:{handoff['id']}",
            "occurred_at": self._now().isoformat(),
            "result": result,
            "warnings": warnings,
            "internal_only": True,
            "client_visible_summary": {
                "handoff_reference": handoff.get("handoff_reference"),
                "status": result,
            },
            "provider_execution_performed": False,
        }

    async def _write_transition_audit(
        self,
        handoff: dict[str, Any],
        user: dict,
        event_type: str,
        evidence: dict[str, Any],
    ) -> None:
        audit = AuditEvent(
            agency_id=handoff["agency_id"],
            actor_user_id=user.get("id"),
            event_type=event_type,
            entity_type="offer_booking_handoff",
            entity_id=handoff["id"],
            summary=f"Offer-to-booking handoff transition recorded as {evidence['result']}.",
            metadata=evidence,
        )
        await self.db.collection("audit_events").insert_one(audit.model_dump(mode="json"))

    def _readiness_snapshot(self, context: dict[str, Any]) -> dict[str, Any]:
        readiness = context.get("readiness") or {}
        return {"booking_readiness_package": self._snapshot(readiness), "metadata_only": True}

    def _trace_snapshots(self, context: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
        acceptance = context.get("acceptance") or {}
        readiness = context.get("readiness") or {}
        rules = acceptance.get("rules_feasibility_snapshot_json") or {}
        pricing = readiness.get("pricing_snapshot_json") or acceptance.get("accepted_pricing_snapshot_json") or {}
        return {
            "policy_trace_json": {
                "rules_feasibility_snapshot_json": self._snapshot(rules),
                "policy_violations_json": readiness.get("policy_violations_json") or [],
                "readiness_checks_json": readiness.get("readiness_checks_json") or {},
                "metadata_only": True,
            },
            "pricing_trace_json": {
                "accepted_pricing_snapshot_json": self._snapshot(pricing),
                "payment_processing_disabled": True,
                "fare_recalculation_disabled": True,
                "metadata_only": True,
            },
            "internal_trace_json": {
                "checks": checks,
                "warnings": readiness.get("warnings_json") or [],
                "required_documents": readiness.get("required_documents_json") or [],
                "ssr_json": readiness.get("ssr_json") or [],
                "osi_json": readiness.get("osi_json") or [],
                "distribution_capability_planning": context.get("distribution_capability") or {},
                "metadata_only": True,
            },
            "client_trace_json": {
                "client_visible_summary_json": self._snapshot(acceptance.get("client_visible_summary_json") or {}),
                "internal_notes_excluded": True,
                "metadata_only": True,
            },
        }

    async def _handoff_projection(self, handoff: dict[str, Any], include_children: bool = True) -> dict[str, Any]:
        projected = {**handoff, **self.safety_flags()}
        if include_children:
            projected["checks"] = await self.list_checks(agency_id=handoff["agency_id"], handoff_id=handoff["id"])
            projected["mappings"] = await self.list_mappings(agency_id=handoff["agency_id"], handoff_id=handoff["id"])
            projected["instructions"] = await self.list_instructions(agency_id=handoff["agency_id"], handoff_id=handoff["id"])
        return projected

    async def _require_handoff(self, handoff_id: str, agency_id: str | None = None) -> dict[str, Any]:
        query = {"id": handoff_id}
        if agency_id:
            query["agency_id"] = agency_id
        handoff = await self.db.collection(OFFER_BOOKING_HANDOFFS_COLLECTION).find_one(query)
        if not handoff:
            alt = {"handoff_reference": handoff_id}
            if agency_id:
                alt["agency_id"] = agency_id
            handoff = await self.db.collection(OFFER_BOOKING_HANDOFFS_COLLECTION).find_one(alt)
        if not handoff:
            raise OfferToBookingHandoffError("Offer-to-booking handoff metadata was not found.")
        return handoff

    def _status_from_checks(self, checks: list[dict[str, Any]]) -> str:
        if any(check["status"] == "blocked" for check in checks):
            return "blocked"
        if any(check["status"] in {"warning", "pending"} for check in checks):
            return "conditional"
        return "ready"

    def _distribution_airline_codes(self, readiness: dict[str, Any], acceptance: dict[str, Any], trip_snapshot: dict[str, Any]) -> list[str]:
        segment_sources: list[Any] = [
            readiness.get("segments_snapshot_json") or [],
            (acceptance.get("accepted_routing_snapshot_json") or {}).get("segments") or [],
            trip_snapshot.get("confirmed_segments_json") or [],
        ]
        codes: list[str] = []
        for segments in segment_sources:
            for segment in segments if isinstance(segments, list) else []:
                if not isinstance(segment, dict):
                    continue
                for key in ["airline_code", "marketing_carrier", "operating_carrier", "validating_carrier", "carrier"]:
                    code = str(segment.get(key) or "").strip().upper()
                    if code and code not in codes:
                        codes.append(code)
        return codes

    def _idempotency_key(self, context: dict[str, Any], data: dict[str, Any]) -> str:
        acceptance_id = (context.get("acceptance") or {}).get("id") or "no_acceptance"
        readiness_id = (context.get("readiness") or {}).get("id") or "no_readiness"
        return f"{context['agency_id']}:{acceptance_id}:{readiness_id}:{self._norm(data.get('booking_mode') or 'manual')}"

    def _handoff_reference(self) -> str:
        return f"OBH-{self._now().strftime('%Y%m%d')}-{new_id()[:8].upper()}"

    def _instruction_reference(self) -> str:
        return f"BXI-{self._now().strftime('%Y%m%d')}-{new_id()[:8].upper()}"

    def _query(self, **values: Any) -> dict[str, Any]:
        return {key: value for key, value in values.items() if value not in {None, ""}}

    def _payload(self, payload: Any, *, exclude_unset: bool = False) -> dict[str, Any]:
        if hasattr(payload, "model_dump"):
            return payload.model_dump(mode="json", exclude_none=True, exclude_unset=exclude_unset)
        return {key: value for key, value in dict(payload or {}).items() if value is not None}

    def _latest(self, items: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not items:
            return None
        return sorted(items, key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)[0]

    def _snapshot(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._snapshot(item) for key, item in value.items() if key != "_id"}
        if isinstance(value, list):
            return [self._snapshot(item) for item in value]
        return value

    def _counts(self, items: list[dict[str, Any]], field: str, defaults: list[str] | None = None) -> dict[str, int]:
        counts = {key: 0 for key in defaults or []}
        for item in items:
            value = item.get(field) or "unset"
            counts[value] = counts.get(value, 0) + 1
        return counts

    def _status_order(self, status: str | None) -> int:
        return {"blocked": 0, "warning": 1, "pending": 2, "passed": 3}.get(status or "", 4)

    def _sort_text(self, value: Any) -> str:
        return str(value or "")

    def _norm(self, value: Any) -> str:
        return str(value.value if hasattr(value, "value") else value or "").strip().lower().replace(" ", "_").replace("-", "_")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)
