from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from persistence_query import MAXIMUM_QUERY_LIMIT, PaginationRequest
from persistence_repository import PersistenceRepository
from models import (
    AuditEvent,
    DocumentWorkspaceCreate,
    DocumentWorkspaceType,
    OperationalTimelineCreate,
    OperationalWorkItemActionRequest,
    OperationalWorkItemGenerateRequest,
    PassengerServiceConfirmationRequest,
    PassengerServiceFulfilmentLinkRequest,
    PassengerServiceOutcomeRequest,
    PassengerServiceReconciliationRequest,
    PassengerServiceRequest,
    PassengerServiceRequestCreate,
    PassengerServiceWorkflow,
    new_id,
)
from services.agent_work_queue_service import AgentWorkQueueService
from services.exception_engine_service import ExceptionEngineService
from services.rules_and_services_registry import normalize_code
from services.service_catalogue_service import find_service_catalogue_record, service_catalogue_snapshot
from services.ssr_osi_generator_service import SsrOsiGeneratorService
from services.timeline_workspace_service import OperationalTimelineService


PASSENGER_SERVICE_CATEGORIES = {"UMNR", "PRM", "MEDICAL", "PETS", "SERVICE_ANIMAL", "CARGO", "VIP", "SEATING", "MEAL", "OTHER"}


def category_for_service_type(service_type: str | None, fallback: str = "OTHER") -> str:
    code = normalize_code(service_type)
    if code == "UMNR":
        return "UMNR"
    if code in {"WCHR", "WCHS", "WCHC", "WCHP", "WCHD", "BLND", "DEAF"}:
        return "PRM"
    if code in {"MEDA", "MEDIF", "OXYG", "STCR"}:
        return "MEDICAL"
    if code in {"PETC", "AVIH"}:
        return "PETS"
    if code == "SVAN":
        return "SERVICE_ANIMAL"
    if code in {"SPEQ", "WEAP"}:
        return "CARGO"
    if code in {"VIP", "VVIP", "DIPB", "DIPLOMAT"}:
        return "VIP"
    if code == "EXST":
        return "SEATING"
    if code == "SPML":
        return "MEAL"
    return fallback if normalize_code(fallback) in PASSENGER_SERVICE_CATEGORIES else "OTHER"


def json_warnings(warnings: list[str]) -> list[dict[str, Any]]:
    return [{"message": warning} for warning in warnings if warning]


def merge_documents(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for group in groups:
        for document in group or []:
            key = (str(document.get("code") or ""), str(document.get("label") or document))
            if key not in seen:
                seen.add(key)
                merged.append(document)
    return merged


async def write_service_audit(
    db: Database,
    agency_id: str,
    actor_user_id: str | None,
    event_type: str,
    entity_id: str,
    summary: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    event = AuditEvent(
        agency_id=agency_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type="passenger_service_request",
        entity_id=entity_id,
        summary=summary,
        metadata=metadata or {},
    )
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


class SpecialServicesService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.exception_engine = ExceptionEngineService(db)
        self.ssr_osi_generator = SsrOsiGeneratorService(db)
        self.work_queue = AgentWorkQueueService(db)
        self.timelines = OperationalTimelineService(db)

    async def add_service_request(
        self,
        agency_id: str,
        payload: PassengerServiceRequestCreate,
        actor_user_id: str | None = None,
        request_id: str | None = None,
        trip_id: str | None = None,
        booking_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json")
        data["service_type"] = normalize_code(data.get("service_type")) or data.get("service_type")
        catalogue_record = await find_service_catalogue_record(
            self.db,
            data.get("service_key") or data.get("service_type") or data.get("ssr_code"),
        )
        if not catalogue_record and data.get("service_catalogue_id"):
            catalogue_record = await self.db.collection("service_catalogue").find_one({"id": data["service_catalogue_id"]})
        catalogue_snapshot = service_catalogue_snapshot(catalogue_record)
        if catalogue_snapshot:
            data["service_catalogue_id"] = data.get("service_catalogue_id") or catalogue_snapshot.get("service_catalogue_id")
            data["service_key"] = data.get("service_key") or catalogue_snapshot.get("service_key")
            data["service_label"] = data.get("service_label") or catalogue_snapshot.get("label")
            data["service_catalogue_category"] = data.get("service_catalogue_category") or catalogue_snapshot.get("category") or catalogue_snapshot.get("rules_category")
            data["service_catalogue_snapshot_json"] = catalogue_snapshot
            data["service_type"] = normalize_code(catalogue_snapshot.get("service_key") or data.get("service_type")) or data.get("service_type")
            data["ssr_code"] = data.get("ssr_code") or catalogue_snapshot.get("ssr_code")
            data["required_documents_json"] = merge_documents(
                data.get("required_documents_json") or [],
                catalogue_snapshot.get("required_documents_json") or [],
            )
            metadata = data.get("metadata_json") or {}
            metadata["service_catalogue_snapshot_json"] = catalogue_snapshot
            data["metadata_json"] = metadata
        data["category"] = category_for_service_type(
            data.get("service_type"),
            data.get("service_catalogue_category") or data.get("category") or "OTHER",
        )
        if request_id:
            data["request_id"] = request_id
        if trip_id:
            data["trip_id"] = trip_id
        if booking_id:
            data["booking_id"] = booking_id
        service_request = PassengerServiceRequest(agency_id=agency_id, **data)
        created = await self.db.collection("passenger_service_requests").insert_one(service_request.model_dump(mode="json"))
        await write_service_audit(
            self.db,
            agency_id,
            actor_user_id,
            "passenger_service_request.created",
            created["id"],
            f"Created special service request {created.get('service_type')}.",
        )
        return created

    async def list_services_for_request(self, agency_id: str, request_id: str) -> list[dict[str, Any]]:
        items = await self.db.collection("passenger_service_requests").find_many({"agency_id": agency_id, "request_id": request_id})
        return sorted(items, key=lambda item: str(item.get("created_at") or ""))

    async def list_services_for_trip(self, agency_id: str, trip_id: str) -> list[dict[str, Any]]:
        items = await self.db.collection("passenger_service_requests").find_many({"agency_id": agency_id, "trip_id": trip_id})
        return sorted(items, key=lambda item: str(item.get("created_at") or ""))

    async def list_services_for_booking(self, agency_id: str, booking_id: str) -> list[dict[str, Any]]:
        items = await self.db.collection("passenger_service_requests").find_many({"agency_id": agency_id, "booking_id": booking_id})
        return sorted(items, key=lambda item: str(item.get("created_at") or ""))

    async def get_service_or_none(self, agency_id: str, service_request_id: str) -> dict[str, Any] | None:
        return await self.db.collection("passenger_service_requests").find_one({"agency_id": agency_id, "id": service_request_id})

    async def list_fulfilment_cases(self, agency_id: str) -> list[dict[str, Any]]:
        page = await PersistenceRepository(self.db).find_agency_records(
            collection_name="passenger_service_requests",
            agency_id=agency_id,
            sort_field="updated_at",
            sort_direction="desc",
            pagination=PaginationRequest.build(limit=MAXIMUM_QUERY_LIMIT),
        )
        items = page.items
        items.sort(key=lambda item: str(item.get("last_reconciled_at") or item.get("updated_at") or item.get("created_at") or ""), reverse=True)
        return [self._client_separated_projection(item) for item in items]

    async def fulfilment_link_options(self, agency_id: str, service_request_id: str) -> dict[str, Any]:
        service = await self._require_service(agency_id, service_request_id)
        collections = {
            "booking_workspaces": "booking_workspaces",
            "booking_records": "booking_records",
            "tickets": "ticket_records",
            "ticket_coupons": "ticket_coupons",
            "emds": "emd_records",
            "emd_coupons": "emd_coupons",
            "documents": "document_workspaces",
            "ssr_osi_workspaces": "ssr_osi_workspaces",
        }
        repository = PersistenceRepository(self.db)
        records = {}
        for key, collection in collections.items():
            page = await repository.find_agency_records(
                collection_name=collection,
                agency_id=agency_id,
                pagination=PaginationRequest.build(limit=MAXIMUM_QUERY_LIMIT),
            )
            records[key] = page.items
        return {
            "agency_id": agency_id,
            "service_request_id": service_request_id,
            "service_context": {
                "request_id": service.get("request_id"),
                "trip_id": service.get("trip_id"),
                "passenger_id": service.get("passenger_id"),
                "booking_workspace_id": service.get("booking_workspace_id"),
                "booking_record_id": service.get("booking_record_id"),
            },
            "items": {
                key: [self._fulfilment_option(service, key, record) for record in values]
                for key, values in records.items()
            },
        }

    async def link_fulfilment_records(
        self,
        agency_id: str,
        service_request_id: str,
        payload: PassengerServiceFulfilmentLinkRequest,
        user: dict,
    ) -> dict[str, Any]:
        service = await self._require_service(agency_id, service_request_id)
        data = payload.model_dump(mode="json", exclude_none=True)
        links = {
            "booking_workspace_id": ("booking_workspaces", data.get("booking_workspace_id")),
            "booking_record_id": ("booking_records", data.get("booking_record_id")),
            "ssr_osi_workspace_id": ("ssr_osi_workspaces", data.get("ssr_osi_workspace_id")),
        }
        for field, (collection, entity_id) in links.items():
            if entity_id:
                record = await self._require_agency_record(collection, entity_id, agency_id, field)
                self._validate_service_context(service, record, field)

        list_links = {
            "ticket_record_ids": "ticket_records",
            "ticket_coupon_ids": "ticket_coupons",
            "emd_record_ids": "emd_records",
            "emd_coupon_ids": "emd_coupons",
            "document_workspace_ids": "document_workspaces",
        }
        resolved: dict[str, list[str]] = {}
        for field, collection in list_links.items():
            resolved[field] = []
            for entity_id in data.get(field) or []:
                record = await self._require_agency_record(collection, entity_id, agency_id, field)
                self._validate_service_context(service, record, field)
                resolved[field].append(entity_id)

        ticket_record_ids = self._deduplicate([*(service.get("ticket_record_ids") or []), *resolved["ticket_record_ids"]])
        emd_record_ids = self._deduplicate([*(service.get("emd_record_ids") or []), *resolved["emd_record_ids"]])
        for coupon_id in resolved["ticket_coupon_ids"]:
            coupon = await self._require_agency_record("ticket_coupons", coupon_id, agency_id, "ticket coupon")
            if ticket_record_ids and coupon.get("ticket_record_id") not in ticket_record_ids:
                raise ValueError("Ticket coupon is not linked to a selected ticket record.")
        for coupon_id in resolved["emd_coupon_ids"]:
            coupon = await self._require_agency_record("emd_coupons", coupon_id, agency_id, "EMD coupon")
            if emd_record_ids and coupon.get("emd_record_id") not in emd_record_ids:
                raise ValueError("EMD coupon is not linked to a selected EMD record.")

        document_ids = self._deduplicate([*(service.get("document_workspace_ids") or []), *resolved["document_workspace_ids"]])
        for document_id in document_ids:
            document = await self._require_agency_record("document_workspaces", document_id, agency_id, "document workspace")
            linked_service = document.get("passenger_service_request_id") or document.get("related_service_requirement")
            if linked_service and linked_service != service_request_id:
                raise ValueError("Document workspace is already linked to a different passenger-service requirement.")
            await self.db.collection("document_workspaces").update_one(
                {"agency_id": agency_id, "id": document_id},
                {"passenger_service_request_id": service_request_id, "related_service_requirement": service_request_id, "updated_by": user.get("id")},
            )

        updates = {
            "booking_workspace_id": data.get("booking_workspace_id") or service.get("booking_workspace_id"),
            "booking_record_id": data.get("booking_record_id") or service.get("booking_record_id"),
            "ssr_osi_workspace_id": data.get("ssr_osi_workspace_id") or service.get("ssr_osi_workspace_id"),
            "ticket_record_ids": ticket_record_ids,
            "ticket_coupon_ids": self._deduplicate([*(service.get("ticket_coupon_ids") or []), *resolved["ticket_coupon_ids"]]),
            "emd_record_ids": emd_record_ids,
            "emd_coupon_ids": self._deduplicate([*(service.get("emd_coupon_ids") or []), *resolved["emd_coupon_ids"]]),
            "document_workspace_ids": document_ids,
            "next_action": data.get("next_action") or service.get("next_action"),
            "due_at": data.get("due_at") or service.get("due_at"),
            "departure_deadline": data.get("departure_deadline") or service.get("departure_deadline"),
        }
        target_type, target_id = self._link_target(updates)
        return await self._record_fulfilment_transition(
            service,
            updates,
            user,
            "passenger_service.fulfilment_linked",
            target_type,
            target_id,
            "linked",
            [],
        )

    async def ensure_document_requirement(
        self,
        agency_id: str,
        service_request_id: str,
        user: dict,
    ) -> dict[str, Any]:
        service = await self._require_service(agency_id, service_request_id)
        existing = await self.db.collection("document_workspaces").find_one(
            {"agency_id": agency_id, "passenger_service_request_id": service_request_id}
        ) or await self.db.collection("document_workspaces").find_one(
            {"agency_id": agency_id, "related_service_requirement": service_request_id}
        )
        if existing and existing.get("document_status") == "archived":
            existing = None
        created_new = False

        booking_workspace = None
        if service.get("booking_workspace_id"):
            booking_workspace = await self._require_agency_record(
                "booking_workspaces", service["booking_workspace_id"], agency_id, "booking workspace"
            )
        if not booking_workspace and service.get("ticket_record_ids"):
            ticket = await self._require_agency_record(
                "ticket_records", service["ticket_record_ids"][0], agency_id, "ticket record"
            )
            if ticket.get("booking_workspace_id"):
                booking_workspace = await self._require_agency_record(
                    "booking_workspaces", ticket["booking_workspace_id"], agency_id, "booking workspace"
                )

        if existing is None:
            from services.document_workspace_service import DocumentWorkspaceService

            requirements = service.get("required_documents_json") or []
            requirement = requirements[0] if requirements and isinstance(requirements[0], dict) else {}
            candidate_type = normalize_code(
                requirement.get("document_type") or requirement.get("code") or "service_instruction"
            ).lower()
            allowed_types = {item.value for item in DocumentWorkspaceType}
            document_type = candidate_type if candidate_type in allowed_types else DocumentWorkspaceType.SERVICE_INSTRUCTION.value
            passenger = None
            if service.get("passenger_id"):
                passenger = await self.db.collection("passenger_workspaces").find_one(
                    {"agency_id": agency_id, "id": service["passenger_id"]}
                )
            passenger_name = " ".join(
                value for value in [
                    (passenger or {}).get("first_name"),
                    (passenger or {}).get("last_name"),
                ] if value
            ) or None
            document_result = await DocumentWorkspaceService(self.db).create_workspace(
                DocumentWorkspaceCreate(
                    agency_id=agency_id,
                    passenger_service_request_id=service_request_id,
                    passenger_workspace_id=service.get("passenger_id"),
                    trip_workspace_id=service.get("trip_id"),
                    booking_workspace_id=(booking_workspace or {}).get("id"),
                    ticket_workspace_id=(service.get("ticket_record_ids") or [None])[0],
                    emd_workspace_id=(service.get("emd_record_ids") or [None])[0],
                    ssr_osi_workspace_id=service.get("ssr_osi_workspace_id"),
                    document_status="required" if requirements else "requested",
                    document_type=document_type,
                    document_category="passenger_service_evidence",
                    document_title=f"{service.get('service_label') or service.get('service_type') or 'Passenger service'} document requirement",
                    passenger_id=service.get("passenger_id"),
                    passenger_name=passenger_name,
                    booking_reference=(booking_workspace or {}).get("booking_reference") or (booking_workspace or {}).get("workspace_number"),
                    airline_pnr=(booking_workspace or {}).get("airline_pnr"),
                    gds_record_locator=(booking_workspace or {}).get("gds_record_locator"),
                    related_service_requirement=service_request_id,
                    related_ssr_code=service.get("ssr_code") or service.get("service_type"),
                    required_for_travel=bool(requirements),
                    required_by_airline=bool(requirements),
                    verification_status="requested",
                    internal_only=True,
                    operational_notes="Created from the canonical passenger-service workflow; no delivery or external action occurred.",
                    metadata={
                        "source": "v1_golden_path",
                        "passenger_service_request_id": service_request_id,
                        "idempotent_requirement": True,
                    },
                ),
                user,
            )
            existing = document_result["document_workspace"]
            created_new = True

        link_result = await self.link_fulfilment_records(
            agency_id,
            service_request_id,
            PassengerServiceFulfilmentLinkRequest(
                booking_workspace_id=(booking_workspace or {}).get("id") or service.get("booking_workspace_id"),
                booking_record_id=(booking_workspace or {}).get("booking_record_id") or service.get("booking_record_id"),
                ticket_record_ids=service.get("ticket_record_ids") or [],
                ticket_coupon_ids=service.get("ticket_coupon_ids") or [],
                emd_record_ids=service.get("emd_record_ids") or [],
                emd_coupon_ids=service.get("emd_coupon_ids") or [],
                document_workspace_ids=self._deduplicate(
                    [*(service.get("document_workspace_ids") or []), existing["id"]]
                ),
                ssr_osi_workspace_id=service.get("ssr_osi_workspace_id"),
                next_action="Review the passenger-service document requirement.",
            ),
            user,
        )
        return {
            "document_workspace": existing,
            "service": link_result.get("service"),
            "created": created_new,
            "idempotent": True,
            "external_execution_performed": False,
        }

    async def record_confirmation(
        self,
        agency_id: str,
        service_request_id: str,
        payload: PassengerServiceConfirmationRequest,
        user: dict,
    ) -> dict[str, Any]:
        service = await self._require_service(agency_id, service_request_id)
        data = payload.model_dump(mode="json", exclude_none=True)
        allowed = {"pending", "requested", "awaiting_external_confirmation", "confirmed", "conditionally_confirmed", "rejected", "cancelled", "not_required", "unknown"}
        for field in ["airline_confirmation_status", "airport_handling_confirmation_status", "external_manual_status"]:
            if data.get(field) not in allowed:
                raise ValueError(f"Unsupported manual confirmation state for {field}.")
        warnings = []
        if data.get("airline_confirmation_status") in {"confirmed", "conditionally_confirmed"} and not data.get("airline_confirmation_evidence_reference"):
            warnings.append({"code": "airline_confirmation_evidence_missing", "severity": "warning"})
            data["airline_confirmation_status"] = "conditionally_confirmed"
        if data.get("airport_handling_confirmation_status") in {"confirmed", "conditionally_confirmed"} and not data.get("airport_handling_evidence_reference"):
            warnings.append({"code": "airport_confirmation_evidence_missing", "severity": "warning"})
            data["airport_handling_confirmation_status"] = "conditionally_confirmed"
        result = "conditionally_confirmed" if warnings else data.get("airline_confirmation_status", "unknown")
        data["fulfilment_result"] = result if result in {"confirmed", "conditionally_confirmed"} else service.get("fulfilment_result", "unknown")
        return await self._record_fulfilment_transition(
            service, data, user, "passenger_service.confirmation_recorded", "external_confirmation", service_request_id, result, warnings
        )

    async def reconcile_fulfilment(
        self,
        agency_id: str,
        service_request_id: str,
        payload: PassengerServiceReconciliationRequest,
        user: dict,
    ) -> dict[str, Any]:
        service = await self._require_service(agency_id, service_request_id)
        data = payload.model_dump(mode="json", exclude_none=True)
        updates = {
            "external_manual_status": data.get("external_manual_status", "unknown"),
            "fulfilment_result": data.get("fulfilment_result", "unknown"),
            "unresolved_mismatches_json": data.get("unresolved_mismatches_json") or [],
            "next_action": data.get("next_action"),
            "metadata_json": self._visibility_metadata(service, data),
        }
        return await self._record_fulfilment_transition(
            service,
            updates,
            user,
            "passenger_service.fulfilment_reconciled",
            "passenger_service_request",
            service_request_id,
            updates["fulfilment_result"],
            updates["unresolved_mismatches_json"],
        )

    async def record_fulfilment_outcome(
        self,
        agency_id: str,
        service_request_id: str,
        payload: PassengerServiceOutcomeRequest,
        user: dict,
    ) -> dict[str, Any]:
        service = await self._require_service(agency_id, service_request_id)
        data = payload.model_dump(mode="json", exclude_none=True)
        outcome = data["fulfilment_result"]
        if outcome == "fulfilled" and not data.get("evidence_reference"):
            raise ValueError("A fulfilled passenger-service outcome requires reviewed evidence metadata.")
        if outcome == "fulfilled" and data.get("unresolved_mismatches_json"):
            raise ValueError("A fulfilled passenger-service outcome cannot retain unresolved mismatches.")
        updates = {
            "fulfilment_result": outcome,
            "external_manual_status": outcome,
            "unresolved_mismatches_json": data.get("unresolved_mismatches_json") or [],
            "next_action": data.get("next_action"),
            "metadata_json": {
                **self._visibility_metadata(service, data),
                "final_outcome_evidence_reference": data.get("evidence_reference"),
            },
        }
        return await self._record_fulfilment_transition(
            service,
            updates,
            user,
            "passenger_service.outcome_recorded",
            "passenger_service_request",
            service_request_id,
            outcome,
            updates["unresolved_mismatches_json"],
        )

    async def _record_fulfilment_transition(
        self,
        service: dict[str, Any],
        updates: dict[str, Any],
        user: dict,
        event_type: str,
        target_entity_type: str,
        target_entity_id: str | None,
        result: str,
        warnings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        agency_id = service["agency_id"]
        now = datetime.now(timezone.utc)
        correlation_id = service.get("fulfilment_correlation_id") or f"passenger-service:{service['id']}:fulfilment"
        if result == "fulfilled":
            updates.setdefault("status", "confirmed")
        elif result == "failed":
            updates.setdefault("status", "blocked")
        elif result == "cancelled":
            updates.setdefault("status", "cancelled")
        updates.update(
            {
                "last_reconciled_at": now,
                "reconciled_by_user_id": user.get("id"),
                "fulfilment_correlation_id": correlation_id,
            }
        )
        updated = await self.db.collection("passenger_service_requests").update_one(
            {"agency_id": agency_id, "id": service["id"]}, updates
        )
        if not updated:
            raise ValueError("Passenger-service fulfilment metadata could not be updated.")

        workflow = await self._ensure_service_workflow(updated, user)
        evidence = {
            "agency_id": agency_id,
            "actor_user_id": user.get("id"),
            "source_entity_type": "passenger_service_request",
            "source_entity_id": service["id"],
            "target_entity_type": target_entity_type,
            "target_entity_id": target_entity_id,
            "correlation_id": correlation_id,
            "occurred_at": now.isoformat(),
            "result": result,
            "warnings": warnings,
            "internal_only": True,
            "client_visible_summary": (updated.get("metadata_json") or {}).get("client_visible_summary"),
            "external_execution_performed": False,
        }
        await write_service_audit(
            self.db,
            agency_id,
            user.get("id"),
            event_type,
            service["id"],
            f"Passenger-service fulfilment recorded as {result}.",
            evidence,
        )
        timeline_result = await self.timelines.create_entry(
            OperationalTimelineCreate(
                agency_id=agency_id,
                timeline_reference=f"PS-TL-{new_id()[:8].upper()}",
                created_by=user.get("id"),
                passenger_workspace_id=updated.get("passenger_id"),
                travel_request_workspace_id=updated.get("request_id"),
                trip_workspace_id=updated.get("trip_id"),
                booking_workspace_id=updated.get("booking_workspace_id"),
                ticket_workspace_id=(updated.get("ticket_record_ids") or [None])[0],
                emd_workspace_id=(updated.get("emd_record_ids") or [None])[0],
                ssr_osi_workspace_id=updated.get("ssr_osi_workspace_id"),
                document_workspace_id=(updated.get("document_workspace_ids") or [None])[0],
                event_type=event_type.replace(".", "_"),
                event_category="passenger_service_fulfilment",
                event_source="special_services",
                event_status=result,
                operational_stage="service_fulfilment",
                operational_result=result,
                summary=f"{updated.get('service_label') or updated.get('service_type')} fulfilment: {result}.",
                internal_only=True,
                passenger_visible=False,
                airline_visible=False,
                operational_notes="Manual reconciliation metadata only; no airline, airport, provider, or messaging action ran.",
                metadata=evidence,
            ),
            user,
        )
        timeline_id = (timeline_result.get("timeline_entry") or {}).get("id")
        work_item_result = await self.work_queue.generate_work_item(
            OperationalWorkItemGenerateRequest(
                agency_id=agency_id,
                work_item_type="service_approval_document_requirement",
                source_entity_type="passenger_service_request",
                source_entity_id=service["id"],
                workflow_instance_id=workflow.get("id"),
                timeline_entry_id=timeline_id,
                title=updated.get("service_label") or f"Passenger service {updated.get('service_type')}",
                summary=updated.get("next_action") or f"Manual fulfilment state: {result}.",
                priority="high" if updated.get("departure_deadline") else "normal",
                severity="high" if result == "failed" or warnings else "medium",
                queue_code=self._service_queue(updated),
                due_at=updated.get("due_at") or updated.get("departure_deadline"),
                blocker_status="manual_review" if result in {"failed", "unknown"} or warnings else "not_blocked",
                generation_reason="passenger_service_fulfilment",
                source_snapshot_json=evidence,
                compatibility_mapping_json={
                    "passenger_service_request_id": service["id"],
                    "passenger_service_workflow_id": workflow.get("id"),
                },
            ),
            user,
            agency_id=agency_id,
        )
        work_item = work_item_result.get("work_item") or {}
        if work_item.get("id"):
            if result in {"fulfilled", "cancelled"} and work_item.get("status") != "completed":
                await self.work_queue.apply_action(
                    work_item["id"], "complete", OperationalWorkItemActionRequest(reason=f"Service outcome recorded as {result}."), user, agency_id=agency_id
                )
            elif (result == "failed" or warnings) and work_item.get("status") != "blocked":
                await self.work_queue.apply_action(
                    work_item["id"], "block", OperationalWorkItemActionRequest(reason="Passenger-service mismatch or evidence review remains.", blocker_status="manual_review"), user, agency_id=agency_id
                )
            elif result not in {"fulfilled", "cancelled", "failed"} and work_item.get("status") == "completed":
                await self.work_queue.apply_action(
                    work_item["id"], "reopen", OperationalWorkItemActionRequest(reason="Passenger-service fulfilment requires further review."), user, agency_id=agency_id
                )
        timeline_ids = self._deduplicate([*(updated.get("timeline_entry_ids") or []), timeline_id])
        final = await self.db.collection("passenger_service_requests").update_one(
            {"agency_id": agency_id, "id": service["id"]},
            {
                "passenger_service_workflow_id": workflow.get("id"),
                "timeline_entry_ids": timeline_ids,
                "work_item_id": work_item.get("id"),
            },
        ) or updated
        return {
            "service": self._client_separated_projection(final),
            "workflow": workflow,
            "timeline_entry": timeline_result.get("timeline_entry"),
            "work_item": work_item,
            "transition_evidence": evidence,
            "provider_execution_disabled": True,
            "manual_external_status_only": True,
        }

    async def _ensure_service_workflow(self, service: dict[str, Any], user: dict) -> dict[str, Any]:
        existing = await self.db.collection("passenger_service_workflows").find_one(
            {"agency_id": service["agency_id"], "passenger_service_request_id": service["id"]}
        )
        readiness = self._workflow_readiness(service)
        values = {
            "booking_workspace_id": service.get("booking_workspace_id"),
            "ticket_workspace_id": (service.get("ticket_record_ids") or [None])[0],
            "emd_workspace_id": (service.get("emd_record_ids") or [None])[0],
            "ssr_osi_workspace_id": service.get("ssr_osi_workspace_id"),
            "document_workspace_id": (service.get("document_workspace_ids") or [None])[0],
            "current_stage": "travel_completed" if service.get("fulfilment_result") == "fulfilled" else "service_fulfilment",
            "next_stage": None if service.get("fulfilment_result") in {"fulfilled", "cancelled"} else "travel_ready",
            "readiness_status": readiness,
            "blocking_requirements": [item.get("code") or "manual_review" for item in service.get("unresolved_mismatches_json") or []],
            "completed_requirements": ["external_result_reconciled"] if service.get("last_reconciled_at") else [],
            "last_updated": datetime.now(timezone.utc),
            "updated_by": user.get("id"),
        }
        if existing:
            return await self.db.collection("passenger_service_workflows").update_one(
                {"agency_id": service["agency_id"], "id": existing["id"]}, values
            ) or existing
        workflow = PassengerServiceWorkflow(
            agency_id=service["agency_id"],
            workflow_reference=f"PSW-{new_id()[:8].upper()}",
            workflow_status="active",
            workflow_type="passenger_service_fulfilment",
            passenger_service_request_id=service["id"],
            passenger_workspace_id=service.get("passenger_id"),
            travel_request_workspace_id=service.get("request_id"),
            trip_workspace_id=service.get("trip_id"),
            started_at=datetime.now(timezone.utc),
            metadata={"canonical_service_owner": "PassengerServiceRequest", "provider_execution_disabled": True},
            **values,
        )
        return await self.db.collection("passenger_service_workflows").insert_one(workflow.model_dump(mode="json"))

    async def _require_service(self, agency_id: str, service_request_id: str) -> dict[str, Any]:
        service = await self.get_service_or_none(agency_id, service_request_id)
        if not service:
            raise ValueError("Passenger-service request was not found for this agency.")
        return service

    async def _require_agency_record(self, collection: str, entity_id: str, agency_id: str, label: str) -> dict[str, Any]:
        record = await self.db.collection(collection).find_one({"agency_id": agency_id, "id": entity_id})
        if not record:
            raise ValueError(f"{label.replace('_', ' ').title()} was not found for this agency.")
        return record

    def _validate_service_context(self, service: dict[str, Any], record: dict[str, Any], label: str) -> None:
        checks = [
            (service.get("trip_id"), record.get("trip_id") or record.get("trip_workspace_id"), "trip"),
            (service.get("passenger_id"), record.get("passenger_id"), "passenger"),
            (service.get("booking_record_id"), record.get("booking_record_id"), "booking"),
        ]
        for expected, actual, context in checks:
            if expected and actual and expected != actual:
                raise ValueError(f"{label.replace('_', ' ').title()} belongs to a different {context} context.")

    def _fulfilment_option(self, service: dict[str, Any], group: str, record: dict[str, Any]) -> dict[str, Any]:
        context = {
            "trip_id": record.get("trip_id") or record.get("trip_workspace_id"),
            "booking_workspace_id": record.get("booking_workspace_id"),
            "booking_record_id": record.get("booking_record_id"),
            "passenger_id": record.get("passenger_id") or record.get("passenger_workspace_id"),
            "ticket_record_id": record.get("ticket_record_id"),
            "emd_record_id": record.get("emd_record_id"),
        }
        labels = {
            "booking_workspaces": record.get("workspace_number") or record.get("booking_reference") or record.get("title"),
            "booking_records": record.get("pnr_locator") or record.get("booking_reference"),
            "tickets": record.get("ticket_number"),
            "ticket_coupons": f"Coupon {record.get('coupon_number')} - {record.get('origin_airport_code') or '?'} to {record.get('destination_airport_code') or '?'}",
            "emds": record.get("emd_number") or record.get("service_label") or record.get("service_key"),
            "emd_coupons": f"Coupon {record.get('coupon_number')} - {record.get('service_label') or record.get('service_key') or 'service'}",
            "documents": record.get("document_display_name") or record.get("document_title") or record.get("document_reference"),
            "ssr_osi_workspaces": record.get("workspace_display_name") or record.get("workspace_reference") or record.get("service_type"),
        }
        status = (
            record.get("booking_status") or record.get("status") or record.get("issue_status")
            or record.get("coupon_status") or record.get("document_status") or record.get("readiness_status")
            or record.get("operational_status") or "unknown"
        )
        warnings: list[str] = []
        for expected, actual, name in [
            (service.get("trip_id"), context["trip_id"], "trip"),
            (service.get("passenger_id"), context["passenger_id"], "passenger"),
            (service.get("booking_record_id"), context["booking_record_id"], "booking"),
        ]:
            if expected and actual and expected != actual:
                warnings.append(f"Different {name} context; linking will be rejected.")
        label = labels.get(group) or record.get("id")
        preview = " | ".join(
            part for part in [
                str(status).replace("_", " "),
                f"trip {context['trip_id']}" if context["trip_id"] else None,
                f"passenger {context['passenger_id']}" if context["passenger_id"] else None,
            ] if part
        )
        return {
            "id": record["id"],
            "label": str(label),
            "status": status,
            "context_preview": preview,
            "context": context,
            "warnings": warnings,
            "immutable_reference": group in {"tickets", "ticket_coupons", "emds", "emd_coupons"},
        }

    def _link_target(self, updates: dict[str, Any]) -> tuple[str, str | None]:
        for field, target_type in [
            ("document_workspace_ids", "document_workspace"),
            ("emd_record_ids", "emd_record"),
            ("ticket_record_ids", "ticket_record"),
            ("booking_record_id", "booking_record"),
            ("booking_workspace_id", "booking_workspace"),
        ]:
            value = updates.get(field)
            if isinstance(value, list) and value:
                return target_type, value[-1]
            if value:
                return target_type, value
        return "passenger_service_request", None

    def _service_queue(self, service: dict[str, Any]) -> str:
        if service.get("unresolved_mismatches_json"):
            return "blocked"
        if service.get("document_workspace_ids") and service.get("fulfilment_result") not in {"fulfilled", "cancelled"}:
            return "waiting_documents"
        return "waiting_airline_supplier"

    def _workflow_readiness(self, service: dict[str, Any]) -> str:
        result = service.get("fulfilment_result") or "unknown"
        if result == "fulfilled":
            return "completed"
        if result == "failed" or service.get("unresolved_mismatches_json"):
            return "blocked"
        if (service.get("airline_confirmation_status") or "unknown") in {"unknown", "pending", "requested", "awaiting_external_confirmation"}:
            return "waiting_for_airline"
        if service.get("document_workspace_ids"):
            return "waiting_for_documents"
        return "ready"

    def _visibility_metadata(self, service: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        return {
            **(service.get("metadata_json") or {}),
            "last_internal_notes": data.get("internal_notes"),
            "client_visible_summary": data.get("client_visible_summary"),
            "internal_client_separation_enabled": True,
        }

    def _client_separated_projection(self, service: dict[str, Any]) -> dict[str, Any]:
        metadata = service.get("metadata_json") or {}
        client_safe = {
            key: value
            for key, value in service.items()
            if key not in {"metadata_json", "evaluation_result_json", "policy_violations_json", "warnings_json", "gds_text"}
        }
        client_safe["client_visible_summary"] = metadata.get("client_visible_summary")
        return {**service, "client_safe_projection": client_safe}

    def _deduplicate(self, values: list[str | None]) -> list[str]:
        return list(dict.fromkeys(value for value in values if value))

    async def segment_context(self, service_request: dict[str, Any]) -> dict[str, Any]:
        agency_id = service_request["agency_id"]
        segment_id = service_request.get("segment_id")
        metadata = service_request.get("metadata_json") or {}
        context: dict[str, Any] = {
            "route_origin": metadata.get("route_origin"),
            "route_destination": metadata.get("route_destination"),
            "aircraft_type": metadata.get("aircraft_type"),
            "iata_code": metadata.get("iata_code") or metadata.get("airline_code"),
            "airline_id": metadata.get("airline_id"),
            "segment_refs_json": metadata.get("segment_refs_json") or [],
        }
        segment = None
        if segment_id:
            segment = await self.db.collection("request_segments").find_one({"agency_id": agency_id, "id": segment_id})
            if segment is None:
                segment = await self.db.collection("trip_segments").find_one({"agency_id": agency_id, "id": segment_id})
        elif service_request.get("request_id"):
            segments = await self.db.collection("request_segments").find_many({"agency_id": agency_id, "request_id": service_request["request_id"]})
            segment = segments[0] if segments else None
        elif service_request.get("trip_id"):
            segments = await self.db.collection("trip_segments").find_many({"agency_id": agency_id, "trip_id": service_request["trip_id"]})
            segment = segments[0] if segments else None
        if segment:
            context["route_origin"] = (
                context.get("route_origin")
                or segment.get("origin_airport_code")
                or segment.get("origin_text")
            )
            context["route_destination"] = (
                context.get("route_destination")
                or segment.get("destination_airport_code")
                or segment.get("destination_text")
            )
            context["iata_code"] = (
                context.get("iata_code")
                or segment.get("preferred_airline_code")
                or segment.get("marketing_airline_code")
                or segment.get("marketing_airline")
                or segment.get("operating_airline_code")
                or segment.get("operating_airline")
            )
            context["aircraft_type"] = context.get("aircraft_type") or segment.get("aircraft_type")
            context["segment_refs_json"] = context.get("segment_refs_json") or [{"segment_id": segment.get("id")}]
        return context

    async def evaluation_context(self, service_request: dict[str, Any]) -> dict[str, Any]:
        metadata = service_request.get("metadata_json") or {}
        segment = await self.segment_context(service_request)
        return {
            "airline_id": segment.get("airline_id"),
            "iata_code": normalize_code(segment.get("iata_code")),
            "route_origin": normalize_code(segment.get("route_origin")),
            "route_destination": normalize_code(segment.get("route_destination")),
            "aircraft_type": normalize_code(segment.get("aircraft_type")),
            "passenger_summary_json": metadata.get("passenger_summary_json") or {},
            "service_category": service_request.get("service_catalogue_category") or service_request.get("category") or category_for_service_type(service_request.get("service_type")),
            "service_key": service_request.get("service_key"),
            "service_label": service_request.get("service_label"),
            "service_catalogue_category": service_request.get("service_catalogue_category"),
            "service_type": service_request.get("service_type"),
            "service_payload_json": metadata,
            "service_catalogue_snapshot_json": service_request.get("service_catalogue_snapshot_json") or metadata.get("service_catalogue_snapshot_json") or {},
            "segment_refs_json": segment.get("segment_refs_json") or [],
        }

    async def evaluate_service_request(self, agency_id: str, service_request_id: str, actor_user_id: str | None = None) -> dict[str, Any] | None:
        service_request = await self.get_service_or_none(agency_id, service_request_id)
        if service_request is None:
            return None
        context = await self.evaluation_context(service_request)
        result = await self.exception_engine.evaluate(context)
        status_value = "validated" if result.get("allowed") else "blocked"
        updates = {
            "evaluation_result_json": result,
            "warnings_json": json_warnings(result.get("warnings") or []),
            "required_documents_json": result.get("required_documents") or [],
            "policy_violations_json": result.get("policy_violations") or [],
            "status": status_value,
        }
        updated = await self.db.collection("passenger_service_requests").update_one({"agency_id": agency_id, "id": service_request_id}, updates)
        await write_service_audit(
            self.db,
            agency_id,
            actor_user_id,
            "passenger_service_request.evaluated",
            service_request_id,
            f"Evaluated special service request {service_request.get('service_type')}.",
            {"allowed": result.get("allowed"), "rules_fired": len(result.get("rules_fired") or [])},
        )
        return {"service": updated, "result": result, "context": context}

    async def generate_ssr_osi_for_service(self, agency_id: str, service_request_id: str, actor_user_id: str | None = None) -> dict[str, Any] | None:
        service_request = await self.get_service_or_none(agency_id, service_request_id)
        if service_request is None:
            return None
        context = await self.evaluation_context(service_request)
        evaluation = await self.exception_engine.evaluate(context)
        generated = await self.ssr_osi_generator.generate(context, evaluation)
        gds_text = "\n".join([*(item.get("text", "") for item in generated.get("ssr") or []), *(item.get("text", "") for item in generated.get("osi") or [])]).strip() or None
        updates = {
            "evaluation_result_json": evaluation,
            "generated_ssr_json": generated.get("ssr") or [],
            "generated_osi_json": generated.get("osi") or [],
            "warnings_json": json_warnings(generated.get("warnings") or []),
            "required_documents_json": generated.get("required_documents") or [],
            "policy_violations_json": evaluation.get("policy_violations") or [],
            "gds_text": gds_text,
            "status": "blocked" if generated.get("blocked") else "validated",
        }
        updated = await self.db.collection("passenger_service_requests").update_one({"agency_id": agency_id, "id": service_request_id}, updates)
        await write_service_audit(
            self.db,
            agency_id,
            actor_user_id,
            "passenger_service_request.ssr_osi_generated",
            service_request_id,
            f"Generated SSR/OSI preview for {service_request.get('service_type')}.",
            {"blocked": generated.get("blocked"), "ssr_count": len(generated.get("ssr") or []), "osi_count": len(generated.get("osi") or [])},
        )
        return {"service": updated, "result": generated, "context": context}

    async def generate_ssr_osi_for_trip(self, agency_id: str, trip_id: str, actor_user_id: str | None = None) -> dict[str, Any]:
        services = await self.list_services_for_trip(agency_id, trip_id)
        generated = []
        for service in services:
            result = await self.generate_ssr_osi_for_service(agency_id, service["id"], actor_user_id)
            if result:
                generated.append(result)
        return {"trip_id": trip_id, "items": generated}

    async def from_parsed_pnr(self, agency_id: str, trip_id: str, booking_id: str | None, parsed_pnr: dict[str, Any], actor_user_id: str | None = None) -> dict[str, Any]:
        created = []
        for entry in parsed_pnr.get("ssr") or parsed_pnr.get("ssrs") or []:
            code = normalize_code(entry.get("code") or entry.get("ssr_code"))
            if not code:
                continue
            payload = PassengerServiceRequestCreate(
                trip_id=trip_id,
                booking_id=booking_id,
                passenger_id=entry.get("passenger_id"),
                segment_id=entry.get("segment_id"),
                category=category_for_service_type(code),
                service_type=code,
                ssr_code=code,
                metadata_json={"parsed_pnr_entry": entry, "source": "parsed_pnr"},
                generated_ssr_json=[entry],
            )
            created.append(await self.add_service_request(agency_id, payload, actor_user_id))
        for entry in parsed_pnr.get("osi") or parsed_pnr.get("osis") or []:
            payload = PassengerServiceRequestCreate(
                trip_id=trip_id,
                booking_id=booking_id,
                category="OTHER",
                service_type=normalize_code(entry.get("service_type")) or "OTHER",
                osi_code=entry.get("code") or entry.get("osi_code"),
                metadata_json={"parsed_pnr_entry": entry, "source": "parsed_pnr"},
                generated_osi_json=[entry],
            )
            created.append(await self.add_service_request(agency_id, payload, actor_user_id))
        return {"created": created, "message": "Parsed PNR SSR/OSI stubs imported into passenger service requests."}
