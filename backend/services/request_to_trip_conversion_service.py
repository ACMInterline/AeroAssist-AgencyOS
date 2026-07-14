from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from database import Database
from models import (
    OperationalDeadlineCreate,
    OperationalTaskAutomationRunRequest,
    OperationalWorkflowEvent,
    OperationalWorkflowInstance,
    RequestTripConversionExecuteRequest,
    RequestTripConversionIssue,
    RequestTripConversionPlan,
    RequestTripConversionPreviewRequest,
    RequestTripConversionRun,
    RequestTripEntityMapping,
    new_id,
)
from services.operational_sla_deadline_service import OperationalSlaDeadlineService
from services.task_automation_dependency_service import TaskAutomationDependencyService
from services.trip_dossier_service import create_trip_from_request, link_request_to_trip, write_request_timeline, write_trip_timeline


PHASE_LABEL = "phase_55_5_airline_distribution_pss_gds_ndc_capability_intelligence_foundation"

REQUEST_TRIP_CONVERSION_PLANS_COLLECTION = "request_trip_conversion_plans"
REQUEST_TRIP_CONVERSION_RUNS_COLLECTION = "request_trip_conversion_runs"
REQUEST_TRIP_ENTITY_MAPPINGS_COLLECTION = "request_trip_entity_mappings"
REQUEST_TRIP_CONVERSION_ISSUES_COLLECTION = "request_trip_conversion_issues"

CONVERSION_MODES = ["new_trip", "existing_trip"]
CONVERSION_PLAN_STATUSES = ["preview", "valid", "blocked", "executed", "archived"]
CONVERSION_RUN_STATUSES = ["planned", "blocked", "executed", "reused_existing_conversion", "failed"]
CONVERSION_ISSUE_TYPES = ["critical", "warning", "manual_review"]
CONVERSION_MAPPING_TYPES = [
    "request_segment_to_trip_segment",
    "request_passenger_to_trip_passenger",
    "request_passenger_to_passenger_profile",
    "request_service_to_trip_service",
    "request_scoped_service_to_trip_service",
    "pet_applicability_carry_forward",
    "special_item_applicability_carry_forward",
    "request_offer_linkage",
]


class RequestToTripConversionError(Exception):
    pass


class RequestToTripConversionService:
    def __init__(self, db: Database):
        self.db = db
        self.task_automation = TaskAutomationDependencyService(db)
        self.deadlines = OperationalSlaDeadlineService(db)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "request_to_trip_operational_conversion_foundation": True,
            "request_remains_intake_origin": True,
            "trip_becomes_operational_shell": True,
            "never_use_request_id_as_trip_id": True,
            "source_snapshots_preserved": True,
            "idempotent_safe_retry_enabled": True,
            "booking_execution_disabled": True,
            "ticketing_disabled": True,
            "provider_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "background_workers_disabled": True,
            "automatic_production_seeding_disabled": True,
            "human_authority_final": True,
        }

    async def build_preview(self, payload: RequestTripConversionPreviewRequest | dict[str, Any], user: dict, agency_id: str | None = None, persist: bool = True) -> dict[str, Any]:
        data = self._payload(payload)
        if agency_id:
            data["agency_id"] = agency_id
        if not data.get("agency_id"):
            raise RequestToTripConversionError("Agency id is required for request-to-trip conversion preview.")
        if not data.get("request_id"):
            raise RequestToTripConversionError("Request id is required for request-to-trip conversion preview.")

        context = await self._request_context(data["agency_id"], data["request_id"])
        mode = "existing_trip" if data.get("existing_trip_id") else "new_trip"
        idempotency_key = data.get("idempotency_key") or self._idempotency_key(data["agency_id"], data["request_id"], data.get("existing_trip_id"))
        validation = await self.validate_context(context, existing_trip_id=data.get("existing_trip_id"))
        preview = self._preview_snapshot(context, mode=mode, existing_trip_id=data.get("existing_trip_id"), idempotency_key=idempotency_key)
        plan_status = "blocked" if validation["critical_issues"] else "valid"
        plan_record = None
        issue_records: list[dict[str, Any]] = []

        if persist:
            plan = RequestTripConversionPlan(
                agency_id=data["agency_id"],
                plan_reference=self._plan_reference(),
                request_id=data["request_id"],
                target_trip_id=data.get("existing_trip_id"),
                conversion_mode=mode,
                plan_status=plan_status,
                idempotency_key=idempotency_key,
                preview_snapshot_json=preview,
                validation_summary_json=validation["summary"],
                missing_data_warnings=validation["warnings"],
                critical_issues=validation["critical_issues"],
                remediation_guidance=validation["remediation_guidance"],
                source_request_snapshot_json=context["source_snapshot"],
                created_by=user.get("id"),
                updated_by=user.get("id"),
                metadata={**(data.get("metadata") or {}), "notes": data.get("notes")},
            )
            plan_record = await self.db.collection(REQUEST_TRIP_CONVERSION_PLANS_COLLECTION).insert_one(plan.model_dump(mode="json"))
            issue_records = await self._store_issues(
                agency_id=data["agency_id"],
                request_id=data["request_id"],
                plan_id=plan_record["id"],
                run_id=None,
                trip_id=data.get("existing_trip_id"),
                issues=[*validation["critical_issues"], *validation["warnings"]],
                user=user,
            )

        return {
            "phase": PHASE_LABEL,
            "plan": plan_record,
            "preview": preview,
            "validation": validation,
            "issues": issue_records,
            "idempotency_key": idempotency_key,
            "conversion_mode": mode,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def validate_conversion(self, payload: RequestTripConversionPreviewRequest | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        result = await self.build_preview(payload, user, agency_id=agency_id, persist=True)
        return {**result, "validation_only": True}

    async def execute_conversion(self, payload: RequestTripConversionExecuteRequest | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        data = self._payload(payload)
        if agency_id:
            data["agency_id"] = agency_id
        if not data.get("agency_id") or not data.get("request_id"):
            raise RequestToTripConversionError("Agency id and request id are required for request-to-trip conversion execution.")

        context = await self._request_context(data["agency_id"], data["request_id"])
        mode = "existing_trip" if data.get("existing_trip_id") else "new_trip"
        idempotency_key = data.get("idempotency_key") or self._idempotency_key(data["agency_id"], data["request_id"], data.get("existing_trip_id"))

        existing_run = await self.db.collection(REQUEST_TRIP_CONVERSION_RUNS_COLLECTION).find_one({"agency_id": data["agency_id"], "idempotency_key": idempotency_key, "run_status": "executed"})
        if existing_run and not data.get("force_retry"):
            return await self._reuse_run(existing_run, idempotency_key)

        prior_trip_id = context["request"].get("trip_id")
        if prior_trip_id and not data.get("existing_trip_id") and not data.get("force_retry"):
            prior_run = await self.db.collection(REQUEST_TRIP_CONVERSION_RUNS_COLLECTION).find_one({"agency_id": data["agency_id"], "request_id": data["request_id"], "trip_id": prior_trip_id, "run_status": "executed"})
            if prior_run:
                return await self._reuse_run(prior_run, idempotency_key)

        preview_result = await self.build_preview(data, user, agency_id=data["agency_id"], persist=True)
        plan = preview_result.get("plan") or {}
        validation = preview_result["validation"]
        run_id = new_id()
        base_run = RequestTripConversionRun(
            id=run_id,
            agency_id=data["agency_id"],
            run_reference=self._run_reference(),
            plan_id=data.get("plan_id") or plan.get("id"),
            request_id=data["request_id"],
            trip_id=data.get("existing_trip_id"),
            conversion_mode=mode,
            run_status="blocked" if validation["critical_issues"] else "planned",
            idempotency_key=idempotency_key if not data.get("force_retry") else f"{idempotency_key}:retry:{new_id()[:8]}",
            source_request_snapshot_json=context["source_snapshot"],
            validation_summary_json=validation["summary"],
            warning_count=len(validation["warnings"]),
            critical_issue_count=len(validation["critical_issues"]),
            retry_of_run_id=existing_run.get("id") if existing_run and data.get("force_retry") else None,
            created_by=user.get("id"),
            updated_by=user.get("id"),
            metadata={**(data.get("metadata") or {}), "conversion_reason": data.get("conversion_reason")},
        )
        run = await self.db.collection(REQUEST_TRIP_CONVERSION_RUNS_COLLECTION).insert_one(base_run.model_dump(mode="json"))

        await self._store_issues(
            agency_id=data["agency_id"],
            request_id=data["request_id"],
            plan_id=run.get("plan_id"),
            run_id=run["id"],
            trip_id=data.get("existing_trip_id"),
            issues=[*validation["critical_issues"], *validation["warnings"]],
            user=user,
        )

        if validation["critical_issues"]:
            updated = await self.db.collection(REQUEST_TRIP_CONVERSION_RUNS_COLLECTION).update_one(
                {"id": run["id"]},
                {
                    "run_status": "blocked",
                    "result_snapshot_json": {
                        "blocked": True,
                        "critical_issues": validation["critical_issues"],
                        "remediation_guidance": validation["remediation_guidance"],
                        "metadata_only": True,
                    },
                    "updated_by": user.get("id"),
                    **self.safety_flags(),
                },
            )
            return {
                "phase": PHASE_LABEL,
                "run": updated or run,
                "plan": plan,
                "trip": None,
                "mappings": [],
                "validation": validation,
                "conversion_blocked": True,
                "metadata_only": True,
                **self.safety_flags(),
            }

        try:
            actor_user_id = user.get("id") or "system"
            if data.get("existing_trip_id"):
                trip = await link_request_to_trip(self.db, data["agency_id"], data["existing_trip_id"], data["request_id"], actor_user_id)
            else:
                trip = await create_trip_from_request(self.db, data["agency_id"], data["request_id"], actor_user_id)
            if trip["id"] == data["request_id"]:
                raise RequestToTripConversionError("Trip id matched request id; conversion refuses to use request id as trip id.")
        except Exception as exc:
            updated = await self.db.collection(REQUEST_TRIP_CONVERSION_RUNS_COLLECTION).update_one(
                {"id": run["id"]},
                {
                    "run_status": "failed",
                    "result_snapshot_json": {"error": str(exc), "metadata_only": True},
                    "updated_by": user.get("id"),
                    **self.safety_flags(),
                },
            )
            raise RequestToTripConversionError(str(exc)) from exc

        mappings = await self._create_entity_mappings(data["agency_id"], run["id"], run.get("plan_id"), data["request_id"], trip["id"], context, user)
        carry_forward = await self._carry_forward_offers(data["agency_id"], run["id"], run.get("plan_id"), data["request_id"], trip["id"], user)
        mappings.extend(carry_forward)
        integrations = await self._emit_conversion_integrations(data["agency_id"], data["request_id"], trip, run, context, user, data)
        result_snapshot = {
            "trip_id": trip["id"],
            "trip_reference": trip.get("trip_reference"),
            "mapping_count": len(mappings),
            "mapping_type_counts": self._counts(mappings, "mapping_type"),
            "warning_count": len(validation["warnings"]),
            "workflow_instance_id": integrations.get("workflow_instance_id"),
            "workflow_event_id": integrations.get("workflow_event_id"),
            "task_automation_run_id": integrations.get("task_automation_run_id"),
            "deadline_id": integrations.get("deadline_id"),
            "timeline_event_ids": integrations.get("timeline_event_ids") or [],
            "source_request_snapshot_preserved": True,
            "request_id_used_as_trip_id": trip["id"] == data["request_id"],
            "metadata_only": True,
        }
        updated_run = await self.db.collection(REQUEST_TRIP_CONVERSION_RUNS_COLLECTION).update_one(
            {"id": run["id"]},
            {
                "trip_id": trip["id"],
                "run_status": "executed",
                "result_snapshot_json": result_snapshot,
                "mapping_count": len(mappings),
                "workflow_instance_id": integrations.get("workflow_instance_id"),
                "task_automation_run_id": integrations.get("task_automation_run_id"),
                "deadline_id": integrations.get("deadline_id"),
                "timeline_event_ids": integrations.get("timeline_event_ids") or [],
                "executed_at": self._now(),
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if run.get("plan_id"):
            await self.db.collection(REQUEST_TRIP_CONVERSION_PLANS_COLLECTION).update_one({"id": run["plan_id"]}, {"plan_status": "executed", "target_trip_id": trip["id"], "updated_by": user.get("id")})

        return {
            "phase": PHASE_LABEL,
            "run": updated_run or run,
            "plan": plan,
            "trip": trip,
            "mappings": mappings,
            "validation": validation,
            "integrations": integrations,
            "idempotent_reused": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def platform_dashboard(self, agency_id: str | None = None, request_id: str | None = None, trip_id: str | None = None, status: str | None = None) -> dict[str, Any]:
        return await self._dashboard(agency_id=agency_id, request_id=request_id, trip_id=trip_id, status=status)

    async def agency_dashboard(self, agency_id: str, request_id: str | None = None, trip_id: str | None = None, status: str | None = None) -> dict[str, Any]:
        return await self._dashboard(agency_id=agency_id, request_id=request_id, trip_id=trip_id, status=status)

    async def list_plans(self, agency_id: str | None = None, request_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        query = self._query(agency_id=agency_id, request_id=request_id)
        if status:
            query["plan_status"] = self._norm(status)
        records = await self.db.collection(REQUEST_TRIP_CONVERSION_PLANS_COLLECTION).find_many(query or None)
        records.sort(key=lambda item: self._sort_text(item.get("created_at")), reverse=True)
        return [{**record, **self.safety_flags()} for record in records]

    async def list_runs(self, agency_id: str | None = None, request_id: str | None = None, trip_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        query = self._query(agency_id=agency_id, request_id=request_id, trip_id=trip_id)
        if status:
            query["run_status"] = self._norm(status)
        records = await self.db.collection(REQUEST_TRIP_CONVERSION_RUNS_COLLECTION).find_many(query or None)
        records.sort(key=lambda item: self._sort_text(item.get("created_at")), reverse=True)
        return [{**record, **self.safety_flags()} for record in records]

    async def list_mappings(self, agency_id: str | None = None, run_id: str | None = None, request_id: str | None = None, trip_id: str | None = None, mapping_type: str | None = None) -> list[dict[str, Any]]:
        query = self._query(agency_id=agency_id, request_id=request_id, trip_id=trip_id)
        if run_id:
            query["run_id"] = run_id
        if mapping_type:
            query["mapping_type"] = self._norm(mapping_type)
        records = await self.db.collection(REQUEST_TRIP_ENTITY_MAPPINGS_COLLECTION).find_many(query or None)
        records.sort(key=lambda item: self._sort_text(item.get("created_at")), reverse=True)
        return [{**record, **self.safety_flags()} for record in records]

    async def list_issues(self, agency_id: str | None = None, run_id: str | None = None, request_id: str | None = None, severity: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        query = self._query(agency_id=agency_id, request_id=request_id)
        if run_id:
            query["run_id"] = run_id
        if severity:
            query["severity"] = self._norm(severity)
        if status:
            query["status"] = self._norm(status)
        records = await self.db.collection(REQUEST_TRIP_CONVERSION_ISSUES_COLLECTION).find_many(query or None)
        records.sort(key=lambda item: self._sort_text(item.get("created_at")), reverse=True)
        return [{**record, **self.safety_flags()} for record in records]

    async def validate_context(self, context: dict[str, Any], existing_trip_id: str | None = None) -> dict[str, Any]:
        request = context["request"]
        critical: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        if not request.get("client_id"):
            critical.append(self._issue("missing_client_linkage", "critical", "Client linkage is required before creating the trip shell.", "Resolve or attach the request client before conversion."))
        if not context["passengers"]:
            critical.append(self._issue("missing_passengers", "critical", "At least one normalized request passenger is required.", "Add or resolve passengers before conversion."))
        if not context["segments"]:
            critical.append(self._issue("missing_segments", "critical", "At least one normalized request segment is required.", "Add request itinerary segments before conversion."))
        if existing_trip_id:
            trip = await self.db.collection("trip_dossiers").find_one({"agency_id": request["agency_id"], "id": existing_trip_id})
            if not trip:
                critical.append(self._issue("target_trip_missing", "critical", "The explicitly selected target trip was not found for this agency.", "Select a valid existing trip owned by this agency."))
            elif trip.get("id") == request.get("id"):
                critical.append(self._issue("request_id_as_trip_id", "critical", "The request id cannot be used as the trip id.", "Select a real trip dossier or create a new trip shell."))
        if request.get("trip_id") and existing_trip_id and request.get("trip_id") != existing_trip_id:
            critical.append(self._issue("request_already_linked_to_different_trip", "critical", "The request is already linked to a different trip.", "Review the existing request-trip relationship before retrying conversion."))

        for passenger in context["passengers"]:
            if not passenger.get("passenger_id"):
                warnings.append(
                    self._issue(
                        "unresolved_passenger_identity",
                        "warning",
                        f"Passenger {passenger.get('snapshot_display_name') or passenger.get('id')} is not linked to a canonical passenger profile.",
                        "Staff may convert with this warning, but should resolve the passenger profile before booking or ticketing.",
                        source_entity_type="request_passenger",
                        source_entity_id=passenger.get("id"),
                    )
                )
        for segment in context["segments"]:
            if not segment.get("origin_airport_code") or not segment.get("destination_airport_code"):
                warnings.append(
                    self._issue(
                        "segment_airport_code_incomplete",
                        "warning",
                        f"Segment {segment.get('sequence')} has incomplete airport-code precision.",
                        "Confirm airport codes before offer, booking, or ticketing work continues.",
                        source_entity_type="request_segment",
                        source_entity_id=segment.get("id"),
                    )
                )
        for service in context["requested_services"]:
            if not service.get("applies_to_all_passengers") and not service.get("passenger_ids"):
                warnings.append(self._issue("service_passenger_scope_incomplete", "warning", f"Service {service.get('service_code')} has incomplete passenger scope.", "Review service passenger scope after conversion.", "requested_service", service.get("id")))
            if not service.get("applies_to_all_segments") and not service.get("segment_ids"):
                warnings.append(self._issue("service_segment_scope_incomplete", "warning", f"Service {service.get('service_code')} has incomplete segment scope.", "Review service segment scope after conversion.", "requested_service", service.get("id")))
        if request.get("trip_id") and not existing_trip_id:
            warnings.append(self._issue("request_already_linked_to_trip", "warning", "Request is already linked to a trip; execution will reuse existing conversion metadata when possible.", "Review the existing trip before retrying."))

        summary = {
            "critical_issue_count": len(critical),
            "warning_count": len(warnings),
            "can_execute": not critical,
            "can_execute_with_warnings": not critical and bool(warnings),
            "missing_data_warning_count": len(warnings),
            "metadata_only": True,
        }
        return {
            "summary": summary,
            "critical_issues": critical,
            "warnings": warnings,
            "remediation_guidance": list(dict.fromkeys([item.get("remediation_guidance") for item in [*critical, *warnings] if item.get("remediation_guidance")])),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def _dashboard(self, agency_id: str | None = None, request_id: str | None = None, trip_id: str | None = None, status: str | None = None) -> dict[str, Any]:
        runs = await self.list_runs(agency_id=agency_id, request_id=request_id, trip_id=trip_id, status=status)
        plans = await self.list_plans(agency_id=agency_id, request_id=request_id)
        mappings = await self.list_mappings(agency_id=agency_id, request_id=request_id, trip_id=trip_id)
        issues = await self.list_issues(agency_id=agency_id, request_id=request_id)
        return {
            "phase": PHASE_LABEL,
            "summary": {
                "plan_count": len(plans),
                "run_count": len(runs),
                "mapping_count": len(mappings),
                "issue_count": len(issues),
                "critical_issue_count": len([item for item in issues if item.get("severity") == "critical"]),
                "warning_count": len([item for item in issues if item.get("severity") == "warning"]),
                "run_status_counts": self._counts(runs, "run_status"),
                "mapping_type_counts": self._counts(mappings, "mapping_type"),
            },
            "recent_runs": runs[:10],
            "recent_plans": plans[:10],
            "recent_issues": issues[:10],
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def _request_context(self, agency_id: str, request_id: str) -> dict[str, Any]:
        request = await self.db.collection("travel_requests").find_one({"agency_id": agency_id, "id": request_id})
        if not request:
            raise RequestToTripConversionError("Request metadata was not found for this agency.")
        passengers = await self.db.collection("request_passengers").find_many({"agency_id": agency_id, "request_id": request_id, "status": "active"})
        segments = await self.db.collection("request_segments").find_many({"agency_id": agency_id, "request_id": request_id, "status": "active"})
        requested_services = await self.db.collection("requested_services").find_many({"agency_id": agency_id, "request_id": request_id})
        scoped_services = await self.db.collection("request_passenger_segment_services").find_many({"agency_id": agency_id, "request_id": request_id})
        pets = await self.db.collection("request_pets").find_many({"agency_id": agency_id, "request_id": request_id, "status": "active"})
        pet_segments = await self.db.collection("request_pet_segment_transport").find_many({"agency_id": agency_id, "request_id": request_id})
        special_items = await self.db.collection("request_special_items").find_many({"agency_id": agency_id, "request_id": request_id, "status": "active"})
        special_item_segments = await self.db.collection("request_special_item_segments").find_many({"agency_id": agency_id, "request_id": request_id})
        offer_workspaces = await self.db.collection("offer_workspaces").find_many({"agency_id": agency_id, "request_id": request_id})
        offers = await self.db.collection("offers").find_many({"agency_id": agency_id, "request_id": request_id})
        context = {
            "request": request,
            "passengers": passengers,
            "segments": segments,
            "requested_services": requested_services,
            "scoped_services": scoped_services,
            "pets": pets,
            "pet_segments": pet_segments,
            "special_items": special_items,
            "special_item_segments": special_item_segments,
            "offer_workspaces": offer_workspaces,
            "offers": offers,
        }
        context["source_snapshot"] = self._source_snapshot(context)
        return context

    def _source_snapshot(self, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "request": self._snapshot(context["request"]),
            "passengers": [self._snapshot(item) for item in context["passengers"]],
            "segments": [self._snapshot(item) for item in context["segments"]],
            "requested_services": [self._snapshot(item) for item in context["requested_services"]],
            "scoped_services": [self._snapshot(item) for item in context["scoped_services"]],
            "pets": [self._snapshot(item) for item in context["pets"]],
            "pet_segments": [self._snapshot(item) for item in context["pet_segments"]],
            "special_items": [self._snapshot(item) for item in context["special_items"]],
            "special_item_segments": [self._snapshot(item) for item in context["special_item_segments"]],
            "offer_workspaces": [self._snapshot(item) for item in context["offer_workspaces"]],
            "offers": [self._snapshot(item) for item in context["offers"]],
            "captured_at": self._now().isoformat(),
            "metadata_only": True,
        }

    def _preview_snapshot(self, context: dict[str, Any], mode: str, existing_trip_id: str | None, idempotency_key: str) -> dict[str, Any]:
        request = context["request"]
        route = request.get("route_summary") or " / ".join([f"{item.get('origin_text') or item.get('origin_airport_code')} to {item.get('destination_text') or item.get('destination_airport_code')}" for item in context["segments"]])
        return {
            "request_id": request["id"],
            "request_reference": request.get("request_reference"),
            "conversion_mode": mode,
            "target_trip_id": existing_trip_id,
            "generated_trip_shell": {
                "trip_reference_strategy": "generated_by_trip_dossier_service",
                "trip_id_strategy": "new_unique_id_or_explicit_existing_trip_id",
                "request_id_used_as_trip_id": False,
                "primary_client_id": request.get("client_id"),
                "primary_request_id": request["id"],
                "trip_title": request.get("title") or route or f"Trip from {request.get('request_reference')}",
                "trip_status": "planning",
                "route_summary": route,
                "service_summary": request.get("service_summary"),
            },
            "counts": {
                "request_passengers": len(context["passengers"]),
                "request_segments": len(context["segments"]),
                "requested_services": len(context["requested_services"]),
                "scoped_services": len(context["scoped_services"]),
                "pets": len(context["pets"]),
                "special_items": len(context["special_items"]),
                "linked_offer_workspaces": len(context["offer_workspaces"]),
                "linked_offers": len(context["offers"]),
            },
            "wizard_steps": [
                "review_request",
                "resolve_client_passengers",
                "review_segments",
                "review_services_pets_items",
                "review_offers",
                "preview_generated_trip",
                "execute",
                "show_mapping_results",
            ],
            "idempotency_key": idempotency_key,
            "metadata_only": True,
        }

    async def _create_entity_mappings(self, agency_id: str, run_id: str, plan_id: str | None, request_id: str, trip_id: str, context: dict[str, Any], user: dict) -> list[dict[str, Any]]:
        mappings: list[dict[str, Any]] = []
        trip_passengers = await self.db.collection("trip_passengers").find_many({"agency_id": agency_id, "trip_id": trip_id})
        trip_segments = await self.db.collection("trip_segments").find_many({"agency_id": agency_id, "trip_id": trip_id})
        trip_services = await self.db.collection("trip_service_items").find_many({"agency_id": agency_id, "trip_id": trip_id})
        passenger_by_request = {item.get("source_request_passenger_id"): item for item in trip_passengers if item.get("source_request_passenger_id")}
        segment_by_request = {item.get("source_request_segment_id"): item for item in trip_segments if item.get("source_request_segment_id")}
        service_by_request = {item.get("source_request_service_id"): item for item in trip_services if item.get("source_request_service_id")}
        scoped_service_by_request = {item.get("source_passenger_segment_service_id"): item for item in trip_services if item.get("source_passenger_segment_service_id")}

        for passenger in context["passengers"]:
            target = passenger_by_request.get(passenger["id"])
            if target:
                mappings.append(await self._insert_mapping(agency_id, run_id, plan_id, request_id, trip_id, "request_passenger_to_trip_passenger", "request_passenger", passenger["id"], "trip_passenger", target["id"], passenger, target, user))
            if passenger.get("passenger_id"):
                mappings.append(await self._insert_mapping(agency_id, run_id, plan_id, request_id, trip_id, "request_passenger_to_passenger_profile", "request_passenger", passenger["id"], "passenger_profile", passenger["passenger_id"], passenger, {"id": passenger["passenger_id"]}, user))
        for segment in context["segments"]:
            target = segment_by_request.get(segment["id"])
            if target:
                mappings.append(await self._insert_mapping(agency_id, run_id, plan_id, request_id, trip_id, "request_segment_to_trip_segment", "request_segment", segment["id"], "trip_segment", target["id"], segment, target, user))
        for service in context["requested_services"]:
            target = service_by_request.get(service["id"])
            if target:
                mappings.append(await self._insert_mapping(agency_id, run_id, plan_id, request_id, trip_id, "request_service_to_trip_service", "requested_service", service["id"], "trip_service_item", target["id"], service, target, user))
        for service in context["scoped_services"]:
            target = scoped_service_by_request.get(service["id"])
            if target:
                mappings.append(await self._insert_mapping(agency_id, run_id, plan_id, request_id, trip_id, "request_scoped_service_to_trip_service", "request_passenger_segment_service", service["id"], "trip_service_item", target["id"], service, target, user))
        for pet in context["pets"]:
            transports = [item for item in context["pet_segments"] if item.get("request_pet_id") == pet["id"]]
            mappings.append(await self._insert_mapping(agency_id, run_id, plan_id, request_id, trip_id, "pet_applicability_carry_forward", "request_pet", pet["id"], "trip_dossier", trip_id, {**pet, "segment_transports": transports}, {"id": trip_id}, user, status="carried_forward"))
        for item in context["special_items"]:
            segments = [row for row in context["special_item_segments"] if row.get("request_special_item_id") == item["id"]]
            mappings.append(await self._insert_mapping(agency_id, run_id, plan_id, request_id, trip_id, "special_item_applicability_carry_forward", "request_special_item", item["id"], "trip_dossier", trip_id, {**item, "segment_applicability": segments}, {"id": trip_id}, user, status="carried_forward"))
        return mappings

    async def _carry_forward_offers(self, agency_id: str, run_id: str, plan_id: str | None, request_id: str, trip_id: str, user: dict) -> list[dict[str, Any]]:
        mappings: list[dict[str, Any]] = []
        for collection_name, entity_type in [("offer_workspaces", "offer_workspace"), ("offers", "offer")]:
            records = await self.db.collection(collection_name).find_many({"agency_id": agency_id, "request_id": request_id})
            for record in records:
                if collection_name == "offer_workspaces" and not record.get("trip_id"):
                    record = await self.db.collection(collection_name).update_one({"id": record["id"]}, {"trip_id": trip_id, "updated_by": user.get("id")}) or record
                mappings.append(await self._insert_mapping(agency_id, run_id, plan_id, request_id, trip_id, "request_offer_linkage", entity_type, record["id"], "trip_dossier", trip_id, record, {"id": trip_id}, user, status="carried_forward"))
        return mappings

    async def _insert_mapping(
        self,
        agency_id: str,
        run_id: str,
        plan_id: str | None,
        request_id: str,
        trip_id: str,
        mapping_type: str,
        source_entity_type: str,
        source_entity_id: str,
        target_entity_type: str,
        target_entity_id: str,
        source_snapshot: dict[str, Any],
        target_snapshot: dict[str, Any],
        user: dict,
        status: str = "mapped",
    ) -> dict[str, Any]:
        existing = await self.db.collection(REQUEST_TRIP_ENTITY_MAPPINGS_COLLECTION).find_one(
            {
                "agency_id": agency_id,
                "run_id": run_id,
                "mapping_type": mapping_type,
                "source_entity_type": source_entity_type,
                "source_entity_id": source_entity_id,
                "target_entity_type": target_entity_type,
                "target_entity_id": target_entity_id,
            }
        )
        if existing:
            return existing
        mapping = RequestTripEntityMapping(
            agency_id=agency_id,
            run_id=run_id,
            plan_id=plan_id,
            request_id=request_id,
            trip_id=trip_id,
            mapping_type=mapping_type,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            target_entity_type=target_entity_type,
            target_entity_id=target_entity_id,
            mapping_status=status,
            mapping_snapshot_json={"request_id": request_id, "trip_id": trip_id, "metadata_only": True},
            source_snapshot_json=self._snapshot(source_snapshot),
            target_snapshot_json=self._snapshot(target_snapshot),
            created_by=user.get("id"),
            updated_by=user.get("id"),
        )
        return await self.db.collection(REQUEST_TRIP_ENTITY_MAPPINGS_COLLECTION).insert_one(mapping.model_dump(mode="json"))

    async def _emit_conversion_integrations(self, agency_id: str, request_id: str, trip: dict[str, Any], run: dict[str, Any], context: dict[str, Any], user: dict, payload: dict[str, Any]) -> dict[str, Any]:
        actor_user_id = user.get("id") or "system"
        await write_request_timeline(
            self.db,
            agency_id,
            request_id,
            actor_user_id,
            "request_trip_conversion_executed",
            "Request converted to trip dossier",
            trip.get("trip_reference"),
            {"run_id": run["id"], "trip_id": trip["id"], "metadata_only": True},
        )
        await write_trip_timeline(
            self.db,
            agency_id,
            trip.get("workspace_id"),
            trip["id"],
            actor_user_id,
            "request_trip_conversion_executed",
            "Request-to-trip conversion recorded",
            context["request"].get("request_reference"),
            {"run_id": run["id"], "request_id": request_id, "metadata_only": True},
        )

        workflow_instance = OperationalWorkflowInstance(
            agency_id=agency_id,
            workflow_definition_id="default:trip_lifecycle_default:1.0",
            entity_type="trip",
            entity_id=trip["id"],
            current_state="planning",
            workflow_status="active",
            context_snapshot_json={
                "request_id": request_id,
                "run_id": run["id"],
                "trip_reference": trip.get("trip_reference"),
                "conversion_mode": run.get("conversion_mode"),
                "metadata_only": True,
            },
            started_at=self._now(),
            created_by=user.get("id"),
            updated_by=user.get("id"),
            metadata={"source": "request_to_trip_conversion"},
        )
        workflow_record = await self.db.collection("operational_workflow_instances").insert_one(workflow_instance.model_dump(mode="json"))
        workflow_event = OperationalWorkflowEvent(
            agency_id=agency_id,
            workflow_instance_id=workflow_record["id"],
            event_type="workflow_started",
            event_code="request_trip_conversion_started_trip_workflow",
            event_status="recorded",
            source_module="request_to_trip_conversion",
            source_entity_type="trip",
            source_entity_id=trip["id"],
            payload_json={"request_id": request_id, "run_id": run["id"], "metadata_only": True},
            occurred_at=self._now(),
        )
        workflow_event_record = await self.db.collection("operational_workflow_events").insert_one(workflow_event.model_dump(mode="json"))

        task_automation_run_id = None
        deadline_id = None
        if payload.get("generate_tasks_deadlines", True):
            automation_result = await self.task_automation.run_automation(
                OperationalTaskAutomationRunRequest(
                    agency_id=agency_id,
                    trigger_event="pre_trip_check",
                    source_entity_type="trip",
                    source_entity_id=trip["id"],
                    request_id=request_id,
                    idempotency_key=f"request-trip-conversion:{agency_id}:{request_id}:{trip['id']}:pre-trip-check",
                    event_snapshot_json={
                        "request_id": request_id,
                        "trip_id": trip["id"],
                        "source_label": trip.get("trip_reference") or context["request"].get("request_reference"),
                        "title": trip.get("trip_title"),
                        "conversion_run_id": run["id"],
                        "workflow_instance_id": workflow_record["id"],
                        "metadata_only": True,
                    },
                    template_codes=["final_trip_document_check"],
                    metadata={"request_to_trip_conversion_run_id": run["id"]},
                ),
                user,
                agency_id=agency_id,
            )
            task_automation_run_id = (automation_result.get("run") or {}).get("id")
            first_task_id = None
            tasks_created = (automation_result.get("run") or {}).get("tasks_created") or []
            if tasks_created:
                first_task_id = tasks_created[0].get("task_id")
            deadline_result = await self.deadlines.create_deadline(
                OperationalDeadlineCreate(
                    agency_id=agency_id,
                    source_entity_type="trip",
                    source_entity_id=trip["id"],
                    workflow_instance_id=workflow_record["id"],
                    workflow_event_id=workflow_event_record["id"],
                    request_task_id=first_task_id,
                    deadline_type="task_deadline",
                    priority=context["request"].get("priority") or "normal",
                    due_at=self._now() + timedelta(hours=24),
                    source_snapshot_json={
                        "request_id": request_id,
                        "trip_id": trip["id"],
                        "conversion_run_id": run["id"],
                        "conversion_result_snapshot": True,
                        "metadata_only": True,
                    },
                    metadata={"request_to_trip_conversion_run_id": run["id"]},
                ),
                user,
                agency_id=agency_id,
            )
            deadline_id = (deadline_result.get("deadline") or {}).get("id")

        return {
            "workflow_instance_id": workflow_record["id"],
            "workflow_event_id": workflow_event_record["id"],
            "task_automation_run_id": task_automation_run_id,
            "deadline_id": deadline_id,
            "timeline_event_ids": [],
            "metadata_only": True,
        }

    async def _store_issues(self, agency_id: str, request_id: str, plan_id: str | None, run_id: str | None, trip_id: str | None, issues: list[dict[str, Any]], user: dict) -> list[dict[str, Any]]:
        records = []
        for issue in issues:
            record = RequestTripConversionIssue(
                agency_id=agency_id,
                plan_id=plan_id,
                run_id=run_id,
                request_id=request_id,
                trip_id=trip_id,
                issue_code=self._norm(issue.get("issue_code") or issue.get("code") or "conversion_issue"),
                issue_type=self._norm(issue.get("issue_type") or issue.get("severity") or "warning"),
                severity=self._norm(issue.get("severity") or "warning"),
                status="open",
                title=issue.get("title") or issue.get("description") or "Conversion issue",
                description=issue.get("description"),
                source_entity_type=issue.get("source_entity_type"),
                source_entity_id=issue.get("source_entity_id"),
                remediation_guidance=issue.get("remediation_guidance"),
                issue_snapshot_json=issue,
                created_by=user.get("id"),
                updated_by=user.get("id"),
            )
            records.append(await self.db.collection(REQUEST_TRIP_CONVERSION_ISSUES_COLLECTION).insert_one(record.model_dump(mode="json")))
        return records

    async def _reuse_run(self, existing_run: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        trip = None
        if existing_run.get("trip_id"):
            trip = await self.db.collection("trip_dossiers").find_one({"agency_id": existing_run["agency_id"], "id": existing_run["trip_id"]})
        mappings = await self.list_mappings(agency_id=existing_run["agency_id"], run_id=existing_run["id"])
        issues = await self.list_issues(agency_id=existing_run["agency_id"], run_id=existing_run["id"])
        return {
            "phase": PHASE_LABEL,
            "run": existing_run,
            "trip": trip,
            "mappings": mappings,
            "issues": issues,
            "idempotency_key": idempotency_key,
            "idempotent_reused": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def _issue(self, code: str, severity: str, title: str, remediation: str, source_entity_type: str | None = None, source_entity_id: str | None = None) -> dict[str, Any]:
        return {
            "issue_code": self._norm(code),
            "issue_type": self._norm(severity),
            "severity": self._norm(severity),
            "title": title,
            "description": title,
            "source_entity_type": source_entity_type,
            "source_entity_id": source_entity_id,
            "remediation_guidance": remediation,
            "metadata_only": True,
        }

    def _payload(self, payload: Any) -> dict[str, Any]:
        if hasattr(payload, "model_dump"):
            return payload.model_dump(mode="json", exclude_none=True)
        return dict(payload or {})

    def _query(self, **values: Any) -> dict[str, Any]:
        return {key: value for key, value in values.items() if value not in (None, "")}

    def _snapshot(self, item: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in dict(item or {}).items() if key != "_id"}

    def _counts(self, records: list[dict[str, Any]], field: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in records:
            key = str(record.get(field) or "unknown")
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _idempotency_key(self, agency_id: str, request_id: str, existing_trip_id: str | None = None) -> str:
        return f"request-trip-conversion:{agency_id}:{request_id}:{existing_trip_id or 'new-trip'}"

    def _plan_reference(self) -> str:
        return f"RTC-PREV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{new_id()[:8].upper()}"

    def _run_reference(self) -> str:
        return f"RTC-RUN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{new_id()[:8].upper()}"

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _norm(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")

    def _sort_text(self, value: Any) -> str:
        return str(value or "")
