from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    AuditEvent,
    EMDRecord,
    EmdSourceContext,
    EmdCoupon,
    EmdCouponStatus,
    EmdCreateFromBookingServiceRequest,
    EmdRecordUpdate,
    EmdStatus,
    EmdType,
    BookingProviderTarget,
    ManualEmdCreate,
    ManualTicketCreate,
    OperationalWorkItemActionRequest,
    OperationalWorkItemGenerateRequest,
    TicketCoupon,
    TicketCouponStatus,
    TicketCreateFromBookingRequest,
    TicketEmdTimelineEvent,
    TicketRecord,
    TicketResultReconciliationRequest,
    TicketRecordUpdate,
    TicketSourceContext,
    TicketStatus,
    TicketType,
    TripTimelineEvent,
)
from services.agent_work_queue_service import AgentWorkQueueService


PHASE_LABEL = "phase_36_4_6_standalone_change_exchange_foundation"


class TicketEmdError(ValueError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _date_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    text = str(value)
    if "T" not in text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _record_summary(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    return {
        "id": record.get("id"),
        "pnr_locator": record.get("pnr_locator"),
        "provider": record.get("provider"),
        "provider_status": record.get("provider_status"),
        "booking_status": record.get("booking_status"),
    }


def _workspace_summary(workspace: dict[str, Any] | None) -> dict[str, Any] | None:
    if not workspace:
        return None
    return {
        "id": workspace.get("id"),
        "workspace_number": workspace.get("workspace_number"),
        "title": workspace.get("title"),
        "status": workspace.get("status"),
        "provider_target": workspace.get("provider_target"),
    }


def _trip_summary(trip: dict[str, Any] | None) -> dict[str, Any] | None:
    if not trip:
        return None
    return {
        "id": trip.get("id"),
        "trip_reference": trip.get("trip_reference"),
        "trip_title": trip.get("trip_title"),
        "route_summary": trip.get("route_summary"),
        "date_summary": trip.get("date_summary"),
        "status": trip.get("trip_status"),
    }


def _ticket_summary(ticket: dict[str, Any] | None) -> dict[str, Any] | None:
    if not ticket:
        return None
    return {
        "id": ticket.get("id"),
        "ticket_number": ticket.get("ticket_number"),
        "issue_status": ticket.get("issue_status") or ticket.get("status"),
        "passenger_id": ticket.get("passenger_id"),
    }


def _item_identity(item: dict[str, Any]) -> set[str]:
    return {
        str(value)
        for value in [
            item.get("id"),
            item.get("passenger_id"),
            item.get("source_request_passenger_id"),
            item.get("request_passenger_id"),
            item.get("profile_id"),
        ]
        if value
    }


def _segment_identity(item: dict[str, Any], index: int) -> str:
    return str(
        item.get("id")
        or item.get("segment_id")
        or item.get("offer_segment_id")
        or item.get("source_request_segment_id")
        or f"segment-{index + 1}"
    )


def _service_catalogue_mapping(service: dict[str, Any]) -> dict[str, Any]:
    for key in ["service_catalogue_snapshot_json", "service_catalogue_snapshot", "catalogue_snapshot_json"]:
        if isinstance(service.get(key), dict):
            return service[key]
    if isinstance(service.get("service_catalogue"), dict):
        return service["service_catalogue"]
    return {}


def _service_key(service: dict[str, Any]) -> str | None:
    mapping = _service_catalogue_mapping(service)
    return (
        service.get("service_key")
        or service.get("service_code")
        or service.get("catalogue_key")
        or mapping.get("service_key")
        or mapping.get("service_code")
        or mapping.get("key")
    )


def _service_catalogue_id(service: dict[str, Any]) -> str | None:
    mapping = _service_catalogue_mapping(service)
    return service.get("service_catalogue_id") or mapping.get("id") or mapping.get("service_catalogue_id")


def _service_label(service: dict[str, Any]) -> str | None:
    mapping = _service_catalogue_mapping(service)
    return (
        service.get("service_label")
        or service.get("service_name")
        or service.get("label")
        or mapping.get("label")
        or mapping.get("name")
        or _service_key(service)
    )


def _service_category(service: dict[str, Any]) -> str | None:
    mapping = _service_catalogue_mapping(service)
    return service.get("service_category") or service.get("category") or mapping.get("category")


def _emd_applicability(service: dict[str, Any]) -> str | None:
    mapping = _service_catalogue_mapping(service)
    return (
        service.get("emd_applicability")
        or mapping.get("emd_applicability")
        or mapping.get("emd_required")
        or mapping.get("emd_behavior")
    )


class TicketEmdService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.work_queue = AgentWorkQueueService(db)

    async def create_ticket_from_booking_record(
        self,
        agency_id: str,
        payload: TicketCreateFromBookingRequest,
        user: dict,
    ) -> dict[str, Any] | None:
        booking_record = await self._get_booking_record(agency_id, payload.booking_record_id)
        if booking_record is None:
            return None
        workspace = await self._get_workspace_for_record(agency_id, booking_record)
        passenger = self._select_passenger(booking_record, payload.passenger_id)
        segments = booking_record.get("segments_json") or (workspace or {}).get("segments_snapshot_json") or []
        pricing = booking_record.get("pricing_json") or (workspace or {}).get("pricing_snapshot_json") or {}
        pricing_summary = pricing.get("summary") if isinstance(pricing, dict) else {}
        pricing_summary = pricing_summary or pricing if isinstance(pricing, dict) else {}
        source = (workspace or {}).get("source_snapshot_json") or {}
        trip_snapshot = source.get("trip_accepted_offer_snapshot") or {}
        readiness = source.get("booking_readiness_package") or {}
        ticket = TicketRecord(
            agency_id=agency_id,
            source_context=TicketSourceContext.BOOKING_RECORD,
            trip_id=booking_record.get("trip_id"),
            request_id=booking_record.get("request_id"),
            booking_workspace_id=booking_record.get("booking_workspace_id"),
            booking_record_id=booking_record["id"],
            passenger_id=payload.passenger_id or self._passenger_id(passenger),
            passenger_snapshot_json=passenger or {},
            issuing_provider=booking_record.get("provider") or (workspace or {}).get("provider_target") or "manual",
            issue_status=TicketStatus.DRAFT,
            status=TicketStatus.DRAFT,
            ticket_type=TicketType.MANUAL_MIRROR,
            currency=pricing_summary.get("currency"),
            base_fare_amount=pricing_summary.get("base_fare_amount") or pricing_summary.get("base_fare"),
            taxes_amount=pricing_summary.get("taxes_amount") or pricing_summary.get("taxes"),
            total_amount=pricing_summary.get("total_amount"),
            pricing_snapshot_json=pricing,
            fare_basis_json=self._fare_basis_snapshot(segments),
            fare_bundle_snapshot_json=trip_snapshot.get("confirmed_fare_bundle_json") or {},
            rules_snapshot_json=readiness.get("readiness_checks_json") or {},
            segments_snapshot_json=segments,
            warnings_json=booking_record.get("warnings_json") or (workspace or {}).get("warnings_json") or [],
            internal_notes=payload.internal_notes,
            created_by_user_id=user.get("id"),
        )
        created = await self.db.collection("ticket_records").insert_one(ticket.model_dump(mode="json"))

        coupons = []
        if payload.create_coupons:
            for index, segment in enumerate(segments):
                coupon = TicketCoupon(
                    agency_id=agency_id,
                    ticket_record_id=created["id"],
                    booking_record_id=booking_record["id"],
                    booking_workspace_id=booking_record.get("booking_workspace_id"),
                    trip_id=booking_record.get("trip_id"),
                    passenger_id=created.get("passenger_id"),
                    segment_id=_segment_identity(segment, index),
                    coupon_number=index + 1,
                    marketing_carrier=segment.get("marketing_airline_code") or segment.get("marketing_airline"),
                    operating_carrier=segment.get("operating_airline_code") or segment.get("operating_airline"),
                    flight_number=segment.get("flight_number"),
                    origin_airport_code=segment.get("origin_airport_code") or segment.get("origin_airport"),
                    destination_airport_code=segment.get("destination_airport_code") or segment.get("destination_airport"),
                    departure_at=_date_time(segment.get("departure_at") or segment.get("departure_datetime")),
                    arrival_at=_date_time(segment.get("arrival_at") or segment.get("arrival_datetime")),
                    cabin=segment.get("cabin") or segment.get("cabin_class"),
                    rbd=segment.get("rbd") or segment.get("booking_class"),
                    fare_basis=segment.get("fare_basis"),
                    coupon_status=TicketCouponStatus.DRAFT,
                    segment_snapshot_json=segment,
                )
                coupons.append(await self.db.collection("ticket_coupons").insert_one(coupon.model_dump(mode="json")))
            if coupons:
                created = await self.db.collection("ticket_records").update_one(
                    {"agency_id": agency_id, "id": created["id"]},
                    {"coupons_json": coupons},
                ) or created

        await self._write_timeline(
            agency_id,
            "ticket.created_from_booking_record",
            "Draft ticket mirror created",
            user.get("id"),
            ticket_record_id=created["id"],
            booking_record_id=booking_record["id"],
            booking_workspace_id=booking_record.get("booking_workspace_id"),
            trip_id=booking_record.get("trip_id"),
            description="Created a draft internal ticket mirror without ticketing provider execution.",
            payload_json={"provider_ticketing_disabled": True},
        )
        return await self.get_ticket_detail(agency_id, created["id"])

    async def create_emd_from_booking_service(
        self,
        agency_id: str,
        payload: EmdCreateFromBookingServiceRequest,
        user: dict,
    ) -> dict[str, Any] | None:
        booking_record = await self._get_booking_record(agency_id, payload.booking_record_id)
        if booking_record is None:
            return None
        workspace = await self._get_workspace_for_record(agency_id, booking_record)
        passenger = self._select_passenger(booking_record, payload.passenger_id)
        service = self._resolve_service(booking_record, workspace, payload)
        segments = booking_record.get("segments_json") or (workspace or {}).get("segments_snapshot_json") or []
        linked_segment_ids = payload.linked_segment_ids or self._service_segment_ids(service, segments)
        ticket_coupons = await self._linked_ticket_coupons(agency_id, payload.ticket_record_id, linked_segment_ids)
        linked_ticket_coupon_ids = [item["id"] for item in ticket_coupons]
        warnings = []
        applicability = _emd_applicability(service)
        if applicability and str(applicability).lower() not in {"required", "conditional", "true"}:
            warnings.append(
                {
                    "code": "service_not_emd_applicable",
                    "message": "Selected service is not marked as EMD-required or conditional in the service catalogue snapshot.",
                    "severity": "warning",
                    "emd_applicability": applicability,
                }
            )
        elif not applicability:
            warnings.append(
                {
                    "code": "service_emd_applicability_unknown",
                    "message": "Selected service has no EMD applicability metadata in the booking snapshot.",
                    "severity": "warning",
                }
            )

        emd = EMDRecord(
            agency_id=agency_id,
            source_context=EmdSourceContext.BOOKING_SERVICE,
            trip_id=booking_record.get("trip_id"),
            request_id=booking_record.get("request_id"),
            booking_workspace_id=booking_record.get("booking_workspace_id"),
            booking_record_id=booking_record["id"],
            ticket_record_id=payload.ticket_record_id,
            ticket_id=payload.ticket_record_id,
            passenger_id=payload.passenger_id or self._passenger_id(passenger),
            passenger_snapshot_json=passenger or {},
            emd_type=EmdType.MANUAL_MIRROR,
            service_code=_service_key(service),
            service_name=_service_label(service),
            service_key=payload.service_key or _service_key(service),
            service_catalogue_id=payload.service_catalogue_id or _service_catalogue_id(service),
            service_label=_service_label(service),
            service_category=_service_category(service),
            linked_service_snapshot_json=service,
            linked_segment_ids=linked_segment_ids,
            linked_ticket_coupon_ids=linked_ticket_coupon_ids,
            issuing_provider=booking_record.get("provider") or (workspace or {}).get("provider_target") or "manual",
            issue_status=EmdStatus.DRAFT,
            status=EmdStatus.DRAFT,
            warnings_json=warnings,
            internal_notes=payload.internal_notes,
            created_by_user_id=user.get("id"),
        )
        created = await self.db.collection("emd_records").insert_one(emd.model_dump(mode="json"))

        coupons = []
        if payload.create_coupons:
            coupon_sources = ticket_coupons or self._segments_by_ids(segments, linked_segment_ids)
            if not coupon_sources:
                coupon_sources = [{}]
            for index, source in enumerate(coupon_sources):
                segment = source.get("segment_snapshot_json") or source if isinstance(source, dict) else {}
                coupon = EmdCoupon(
                    agency_id=agency_id,
                    emd_record_id=created["id"],
                    booking_record_id=booking_record["id"],
                    booking_workspace_id=booking_record.get("booking_workspace_id"),
                    trip_id=booking_record.get("trip_id"),
                    passenger_id=created.get("passenger_id"),
                    segment_id=source.get("segment_id") or (_segment_identity(segment, index) if segment else None),
                    ticket_coupon_id=source.get("id") if source.get("ticket_record_id") else None,
                    coupon_number=index + 1,
                    service_key=created.get("service_key"),
                    service_label=created.get("service_label"),
                    service_category=created.get("service_category"),
                    coupon_status=EmdCouponStatus.DRAFT,
                    service_snapshot_json=service,
                    segment_snapshot_json=segment,
                )
                coupons.append(await self.db.collection("emd_coupons").insert_one(coupon.model_dump(mode="json")))

        await self._write_timeline(
            agency_id,
            "emd.created_from_booking_service",
            "Draft EMD mirror created",
            user.get("id"),
            emd_record_id=created["id"],
            booking_record_id=booking_record["id"],
            booking_workspace_id=booking_record.get("booking_workspace_id"),
            trip_id=booking_record.get("trip_id"),
            description="Created a draft internal EMD mirror without EMD provider issuance.",
            payload_json={"provider_emd_issuance_disabled": True, "service_key": created.get("service_key")},
        )
        return await self.get_emd_detail(agency_id, created["id"])

    async def create_manual_ticket(
        self,
        agency_id: str,
        payload: ManualTicketCreate,
        user: dict,
    ) -> dict[str, Any]:
        booking_record = await self._get_booking_record(agency_id, payload.booking_record_id)
        if payload.booking_record_id and booking_record is None:
            raise TicketEmdError("Booking record not found for manual ticket.")
        workspace = await self._get_workspace_for_record(agency_id, booking_record) if booking_record else await self._get_workspace(agency_id, payload.booking_workspace_id)
        if payload.booking_workspace_id and workspace is None:
            raise TicketEmdError("Booking workspace not found for manual ticket.")
        passenger = self._select_passenger(booking_record, payload.passenger_id) if booking_record else None
        passenger_snapshot = payload.passenger_snapshot_json or passenger or {}
        segments = payload.segments_snapshot_json or (booking_record or {}).get("segments_json") or (workspace or {}).get("segments_snapshot_json") or []
        pricing = payload.pricing_snapshot_json or (booking_record or {}).get("pricing_json") or (workspace or {}).get("pricing_snapshot_json") or {}
        pricing_summary = pricing.get("summary") if isinstance(pricing, dict) else {}
        pricing_summary = pricing_summary or pricing if isinstance(pricing, dict) else {}
        source_context = _enum_value(payload.source_context or TicketSourceContext.STANDALONE_MANUAL.value)
        trip_id = payload.trip_id or (booking_record or {}).get("trip_id") or (workspace or {}).get("trip_id")
        booking_workspace_id = payload.booking_workspace_id or (booking_record or {}).get("booking_workspace_id") or (workspace or {}).get("id")
        provider = _enum_value(payload.issuing_provider or (booking_record or {}).get("provider") or (workspace or {}).get("provider_target") or "manual")
        ticket = TicketRecord(
            agency_id=agency_id,
            source_context=source_context,
            trip_id=trip_id,
            request_id=(booking_record or {}).get("request_id") or (workspace or {}).get("request_id"),
            booking_workspace_id=booking_workspace_id,
            booking_record_id=(booking_record or {}).get("id") or payload.booking_record_id,
            client_id=payload.client_id or (booking_record or {}).get("client_id") or (workspace or {}).get("client_id"),
            passenger_id=payload.passenger_id or self._passenger_id(passenger),
            passenger_snapshot_json=passenger_snapshot,
            original_ticket_record_id=payload.original_ticket_record_id,
            exchange_operation_id=payload.exchange_operation_id,
            import_draft_id=payload.import_draft_id,
            ticket_number=payload.ticket_number,
            validating_airline_code=payload.validating_carrier,
            validating_carrier=payload.validating_carrier,
            issuing_provider=provider,
            issue_status=payload.issue_status,
            status=payload.issue_status,
            ticket_type=TicketType.MANUAL_MIRROR,
            currency=payload.currency or pricing_summary.get("currency"),
            base_fare_amount=payload.base_fare_amount if payload.base_fare_amount is not None else pricing_summary.get("base_fare_amount") or pricing_summary.get("base_fare"),
            taxes_amount=payload.taxes_amount if payload.taxes_amount is not None else pricing_summary.get("taxes_amount") or pricing_summary.get("taxes"),
            total_amount=payload.total_amount if payload.total_amount is not None else pricing_summary.get("total_amount"),
            pricing_snapshot_json=pricing,
            fare_basis_json=self._fare_basis_snapshot(segments),
            segments_snapshot_json=segments,
            warnings_json=[],
            internal_notes=payload.internal_notes,
            client_visible_notes=payload.client_visible_notes,
            external_evidence_reference=payload.external_evidence_reference,
            external_result_status=payload.external_result_status,
            reconciliation_status="unreconciled",
            transition_correlation_id=f"booking:{(booking_record or {}).get('id') or payload.booking_record_id or booking_workspace_id or trip_id or 'standalone'}:ticket-result",
            created_by_user_id=user.get("id"),
        )
        if _enum_value(payload.issue_status) == TicketStatus.ISSUED.value and not payload.external_evidence_reference:
            ticket.warnings_json.append({"code": "external_ticket_evidence_missing", "severity": "warning", "message": "Externally issued ticket evidence requires manual review."})
        created = await self.db.collection("ticket_records").insert_one(ticket.model_dump(mode="json"))
        coupons = []
        if payload.create_coupons:
            for index, segment in enumerate(segments):
                coupon = TicketCoupon(
                    agency_id=agency_id,
                    ticket_record_id=created["id"],
                    booking_record_id=created.get("booking_record_id"),
                    booking_workspace_id=created.get("booking_workspace_id"),
                    trip_id=created.get("trip_id"),
                    passenger_id=created.get("passenger_id"),
                    segment_id=_segment_identity(segment, index),
                    coupon_number=index + 1,
                    marketing_carrier=segment.get("marketing_airline_code") or segment.get("marketing_airline"),
                    operating_carrier=segment.get("operating_airline_code") or segment.get("operating_airline"),
                    flight_number=segment.get("flight_number"),
                    origin_airport_code=segment.get("origin_airport_code") or segment.get("origin_airport"),
                    destination_airport_code=segment.get("destination_airport_code") or segment.get("destination_airport"),
                    departure_at=_date_time(segment.get("departure_at") or segment.get("departure_datetime")),
                    arrival_at=_date_time(segment.get("arrival_at") or segment.get("arrival_datetime")),
                    cabin=segment.get("cabin") or segment.get("cabin_class"),
                    rbd=segment.get("rbd") or segment.get("booking_class"),
                    fare_basis=segment.get("fare_basis"),
                    coupon_status=TicketCouponStatus.DRAFT,
                    segment_snapshot_json=segment,
                )
                coupons.append(await self.db.collection("ticket_coupons").insert_one(coupon.model_dump(mode="json")))
            if coupons:
                created = await self.db.collection("ticket_records").update_one(
                    {"agency_id": agency_id, "id": created["id"]},
                    {"coupons_json": coupons},
                ) or created
        await self._write_timeline(
            agency_id,
            "ticket.created_manual",
            "Manual ticket mirror created",
            user.get("id"),
            ticket_record_id=created["id"],
            booking_record_id=created.get("booking_record_id"),
            booking_workspace_id=created.get("booking_workspace_id"),
            trip_id=created.get("trip_id"),
            description="Created an internal ticket mirror without ticketing provider execution.",
            payload_json={"source_context": source_context, "provider_ticketing_disabled": True},
        )
        if created.get("trip_id"):
            await self._write_trip_timeline(
                agency_id,
                created["trip_id"],
                user.get("id"),
                "trip.ticket_mirror_created_manual",
                "Manual ticket mirror created",
                created.get("ticket_number") or created["id"],
                {"ticket_record_id": created["id"], "source_context": source_context, "provider_ticketing_disabled": True},
            )
        evidence = self._ticket_transition_evidence(
            created,
            user,
            "booking_record" if created.get("booking_record_id") else "booking_workspace",
            created.get("booking_record_id") or created.get("booking_workspace_id"),
            "external_result_recorded",
            created.get("warnings_json") or [],
        )
        await self._write_ticket_audit(created, user, "ticket.external_result_recorded", evidence)
        await self._sync_ticket_work_item(created, user, evidence)
        return await self.get_ticket_detail(agency_id, created["id"])

    async def reconcile_ticket_result(
        self,
        agency_id: str,
        ticket_record_id: str,
        payload: TicketResultReconciliationRequest,
        user: dict,
    ) -> dict[str, Any] | None:
        ticket = await self.db.collection("ticket_records").find_one({"agency_id": agency_id, "id": ticket_record_id})
        if ticket is None:
            return None
        data = payload.model_dump(mode="json", exclude_none=True)
        allowed = {"unreconciled", "matched", "mismatch", "manual_review", "unknown"}
        if data["reconciliation_status"] not in allowed:
            raise TicketEmdError("Unsupported ticket reconciliation status.")
        evidence_reference = data.get("external_evidence_reference") or ticket.get("external_evidence_reference")
        mismatches = data.get("unresolved_mismatches_json") or []
        if data["reconciliation_status"] == "matched" and not evidence_reference:
            raise TicketEmdError("Matched ticket reconciliation requires external evidence metadata.")
        if data["reconciliation_status"] == "matched" and mismatches:
            raise TicketEmdError("A matched ticket cannot retain unresolved mismatches.")
        now = datetime.now(timezone.utc)
        updates = {
            "reconciliation_status": data["reconciliation_status"],
            "external_result_status": data.get("external_result_status", "unknown"),
            "external_evidence_reference": evidence_reference,
            "unresolved_mismatches_json": mismatches,
            "last_reconciled_at": now,
            "reconciled_by_user_id": user.get("id"),
            "updated_by_user_id": user.get("id"),
        }
        if data.get("internal_notes") is not None:
            updates["internal_notes"] = data["internal_notes"]
        if data.get("client_visible_notes") is not None:
            updates["client_visible_notes"] = data["client_visible_notes"]
        updated = await self.db.collection("ticket_records").update_one(
            {"agency_id": agency_id, "id": ticket_record_id}, updates
        )
        evidence = self._ticket_transition_evidence(
            updated or {**ticket, **updates},
            user,
            "ticket_record",
            ticket_record_id,
            data["reconciliation_status"],
            mismatches,
        )
        await self._write_timeline(
            agency_id,
            "ticket.external_result_reconciled",
            "External ticket result reconciled",
            user.get("id"),
            ticket_record_id=ticket_record_id,
            booking_record_id=ticket.get("booking_record_id"),
            booking_workspace_id=ticket.get("booking_workspace_id"),
            trip_id=ticket.get("trip_id"),
            description="Recorded manual reconciliation of an externally obtained ticket result; no ticket was issued or changed.",
            payload_json=evidence,
        )
        await self._write_ticket_audit(updated or ticket, user, "ticket.external_result_reconciled", evidence)
        await self._sync_ticket_work_item(updated or {**ticket, **updates}, user, evidence)
        return await self.get_ticket_detail(agency_id, ticket_record_id)

    async def create_manual_emd(
        self,
        agency_id: str,
        payload: ManualEmdCreate,
        user: dict,
    ) -> dict[str, Any]:
        booking_record = await self._get_booking_record(agency_id, payload.booking_record_id)
        if payload.booking_record_id and booking_record is None:
            raise TicketEmdError("Booking record not found for manual EMD.")
        workspace = await self._get_workspace_for_record(agency_id, booking_record) if booking_record else await self._get_workspace(agency_id, payload.booking_workspace_id)
        if payload.booking_workspace_id and workspace is None:
            raise TicketEmdError("Booking workspace not found for manual EMD.")
        ticket = None
        if payload.ticket_record_id:
            ticket = await self.db.collection("ticket_records").find_one({"agency_id": agency_id, "id": payload.ticket_record_id})
            if ticket is None:
                raise TicketEmdError("Ticket record not found for manual EMD.")
        passenger = self._select_passenger(booking_record, payload.passenger_id) if booking_record else None
        source_context = _enum_value(payload.source_context or EmdSourceContext.STANDALONE_MANUAL.value)
        trip_id = payload.trip_id or (booking_record or {}).get("trip_id") or (workspace or {}).get("trip_id") or (ticket or {}).get("trip_id")
        booking_workspace_id = payload.booking_workspace_id or (booking_record or {}).get("booking_workspace_id") or (workspace or {}).get("id") or (ticket or {}).get("booking_workspace_id")
        service_snapshot = payload.linked_service_snapshot_json or {
            "service_key": payload.service_key,
            "service_catalogue_id": payload.service_catalogue_id,
            "service_label": payload.service_label,
            "service_category": payload.service_category,
        }
        emd = EMDRecord(
            agency_id=agency_id,
            source_context=source_context,
            trip_id=trip_id,
            request_id=(booking_record or {}).get("request_id") or (workspace or {}).get("request_id"),
            booking_workspace_id=booking_workspace_id,
            booking_record_id=(booking_record or {}).get("id") or payload.booking_record_id,
            ticket_record_id=payload.ticket_record_id,
            ticket_id=payload.ticket_record_id,
            client_id=payload.client_id or (booking_record or {}).get("client_id") or (workspace or {}).get("client_id") or (ticket or {}).get("client_id"),
            passenger_id=payload.passenger_id or self._passenger_id(passenger) or (ticket or {}).get("passenger_id"),
            passenger_snapshot_json=(ticket or {}).get("passenger_snapshot_json") or passenger or {},
            original_emd_record_id=payload.original_emd_record_id,
            exchange_operation_id=payload.exchange_operation_id,
            import_draft_id=payload.import_draft_id,
            emd_number=payload.emd_number,
            emd_type=payload.emd_type,
            service_code=payload.service_key,
            service_name=payload.service_label,
            service_key=payload.service_key,
            service_catalogue_id=payload.service_catalogue_id,
            service_label=payload.service_label or payload.service_key or "Manual EMD service",
            service_category=payload.service_category,
            linked_service_snapshot_json=service_snapshot,
            linked_segment_ids=payload.linked_segment_ids or [],
            linked_ticket_coupon_ids=payload.linked_ticket_coupon_ids or [],
            issuing_provider=BookingProviderTarget.MANUAL,
            issue_status=payload.issue_status,
            status=payload.issue_status,
            currency=payload.currency,
            amount=payload.amount,
            taxes_amount=payload.taxes_amount,
            total_amount=payload.total_amount,
            pricing_snapshot_json={
                "amount": payload.amount,
                "taxes_amount": payload.taxes_amount,
                "total_amount": payload.total_amount,
                "currency": payload.currency,
            },
            warnings_json=[],
            internal_notes=payload.internal_notes,
            created_by_user_id=user.get("id"),
        )
        created = await self.db.collection("emd_records").insert_one(emd.model_dump(mode="json"))
        coupons = []
        if payload.create_coupons:
            coupon_sources = await self._coupons_by_ids(agency_id, payload.linked_ticket_coupon_ids)
            if not coupon_sources:
                coupon_sources = self._segments_by_ids(
                    (booking_record or {}).get("segments_json") or (workspace or {}).get("segments_snapshot_json") or (ticket or {}).get("segments_snapshot_json") or [],
                    payload.linked_segment_ids or [],
                )
            if not coupon_sources:
                coupon_sources = [{}]
            for index, source in enumerate(coupon_sources):
                segment = source.get("segment_snapshot_json") or source if isinstance(source, dict) else {}
                coupon = EmdCoupon(
                    agency_id=agency_id,
                    emd_record_id=created["id"],
                    booking_record_id=created.get("booking_record_id"),
                    booking_workspace_id=created.get("booking_workspace_id"),
                    trip_id=created.get("trip_id"),
                    passenger_id=created.get("passenger_id"),
                    segment_id=source.get("segment_id") or (_segment_identity(segment, index) if segment else None),
                    ticket_coupon_id=source.get("id") if source.get("ticket_record_id") else None,
                    coupon_number=index + 1,
                    service_key=created.get("service_key"),
                    service_label=created.get("service_label"),
                    service_category=created.get("service_category"),
                    coupon_status=EmdCouponStatus.DRAFT,
                    service_snapshot_json=service_snapshot,
                    segment_snapshot_json=segment,
                )
                coupons.append(await self.db.collection("emd_coupons").insert_one(coupon.model_dump(mode="json")))
        await self._write_timeline(
            agency_id,
            "emd.created_manual",
            "Manual EMD mirror created",
            user.get("id"),
            emd_record_id=created["id"],
            ticket_record_id=created.get("ticket_record_id"),
            booking_record_id=created.get("booking_record_id"),
            booking_workspace_id=created.get("booking_workspace_id"),
            trip_id=created.get("trip_id"),
            description="Created an internal EMD mirror without EMD provider issuance.",
            payload_json={"source_context": source_context, "provider_emd_issuance_disabled": True},
        )
        if created.get("trip_id"):
            await self._write_trip_timeline(
                agency_id,
                created["trip_id"],
                user.get("id"),
                "trip.emd_mirror_created_manual",
                "Manual EMD mirror created",
                created.get("emd_number") or created["id"],
                {"emd_record_id": created["id"], "source_context": source_context, "provider_emd_issuance_disabled": True},
            )
        return await self.get_emd_detail(agency_id, created["id"])

    async def list_tickets(self, agency_id: str, filters: dict[str, Any]) -> dict[str, Any]:
        query = {"agency_id": agency_id}
        for key in ["trip_id", "booking_workspace_id", "booking_record_id", "passenger_id", "ticket_number"]:
            if filters.get(key):
                query[key] = filters[key]
        if filters.get("issue_status"):
            query["issue_status"] = filters["issue_status"]
        items = await self.db.collection("ticket_records").find_many(query)
        items.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
        return {"items": items}

    async def get_ticket_detail(self, agency_id: str, ticket_record_id: str) -> dict[str, Any]:
        ticket = await self.db.collection("ticket_records").find_one(
            {"agency_id": agency_id, "id": ticket_record_id}
        )
        if ticket is None:
            return {}
        coupons = await self.db.collection("ticket_coupons").find_many(
            {"agency_id": agency_id, "ticket_record_id": ticket_record_id}
        )
        booking_record = await self._get_booking_record(agency_id, ticket.get("booking_record_id"))
        workspace = await self._get_workspace_for_record(agency_id, booking_record) if booking_record else None
        trip = await self._get_trip(agency_id, ticket.get("trip_id"))
        emds = await self.db.collection("emd_records").find_many(
            {"agency_id": agency_id, "ticket_record_id": ticket_record_id}
        )
        timeline = await self.db.collection("ticket_emd_timeline_events").find_many(
            {"agency_id": agency_id, "ticket_record_id": ticket_record_id}
        )
        timeline.sort(key=lambda item: str(item.get("created_at") or ""))
        return {
            "ticket": ticket,
            "client_safe_ticket": {
                key: value
                for key, value in ticket.items()
                if key not in {"internal_notes", "provider_payload_json", "provider_response_json", "warnings_json"}
            },
            "coupons": coupons,
            "booking_record_summary": _record_summary(booking_record),
            "booking_workspace_summary": _workspace_summary(workspace),
            "trip_summary": _trip_summary(trip),
            "linked_emds": emds,
            "timeline": timeline,
            "warnings": ticket.get("warnings_json") or [],
            "provider_execution_disabled": True,
        }

    async def update_ticket_record(
        self,
        agency_id: str,
        ticket_record_id: str,
        payload: TicketRecordUpdate,
        user: dict,
    ) -> dict[str, Any] | None:
        ticket = await self.db.collection("ticket_records").find_one(
            {"agency_id": agency_id, "id": ticket_record_id}
        )
        if ticket is None:
            return None
        updates = payload.model_dump(exclude_unset=True, mode="json")
        if "issue_status" in updates:
            updates["status"] = updates["issue_status"]
            if updates["issue_status"] == TicketStatus.ISSUED.value and not ticket.get("issued_at"):
                updates["issued_at"] = _now_iso()
            if updates["issue_status"] == TicketStatus.VOIDED.value and not ticket.get("voided_at"):
                updates["voided_at"] = _now_iso()
            if updates["issue_status"] == TicketStatus.REFUNDED.value and not ticket.get("refunded_at"):
                updates["refunded_at"] = _now_iso()
            if updates["issue_status"] == TicketStatus.EXCHANGED.value and not ticket.get("exchanged_at"):
                updates["exchanged_at"] = _now_iso()
        if updates.get("validating_carrier") and not updates.get("validating_airline_code"):
            updates["validating_airline_code"] = updates["validating_carrier"]
        updates["updated_by_user_id"] = user.get("id")
        await self.db.collection("ticket_records").update_one(
            {"agency_id": agency_id, "id": ticket_record_id},
            updates,
        )
        await self._write_timeline(
            agency_id,
            "ticket.updated",
            "Ticket mirror updated",
            user.get("id"),
            ticket_record_id=ticket_record_id,
            booking_record_id=ticket.get("booking_record_id"),
            booking_workspace_id=ticket.get("booking_workspace_id"),
            trip_id=ticket.get("trip_id"),
            description="Updated manual ticket mirror fields without ticketing provider execution.",
            payload_json={"updated_fields": sorted(updates.keys()), "provider_ticketing_disabled": True},
        )
        return await self.get_ticket_detail(agency_id, ticket_record_id)

    async def list_emds(self, agency_id: str, filters: dict[str, Any]) -> dict[str, Any]:
        query = {"agency_id": agency_id}
        for key in [
            "trip_id",
            "booking_workspace_id",
            "booking_record_id",
            "ticket_record_id",
            "passenger_id",
            "service_key",
            "emd_number",
        ]:
            if filters.get(key):
                query[key] = filters[key]
        if filters.get("issue_status"):
            query["issue_status"] = filters["issue_status"]
        items = await self.db.collection("emd_records").find_many(query)
        items.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
        return {"items": items}

    async def get_emd_detail(self, agency_id: str, emd_record_id: str) -> dict[str, Any]:
        emd = await self.db.collection("emd_records").find_one(
            {"agency_id": agency_id, "id": emd_record_id}
        )
        if emd is None:
            return {}
        coupons = await self.db.collection("emd_coupons").find_many(
            {"agency_id": agency_id, "emd_record_id": emd_record_id}
        )
        ticket = None
        if emd.get("ticket_record_id"):
            ticket = await self.db.collection("ticket_records").find_one(
                {"agency_id": agency_id, "id": emd["ticket_record_id"]}
            )
        booking_record = await self._get_booking_record(agency_id, emd.get("booking_record_id"))
        workspace = await self._get_workspace_for_record(agency_id, booking_record) if booking_record else None
        trip = await self._get_trip(agency_id, emd.get("trip_id"))
        timeline = await self.db.collection("ticket_emd_timeline_events").find_many(
            {"agency_id": agency_id, "emd_record_id": emd_record_id}
        )
        timeline.sort(key=lambda item: str(item.get("created_at") or ""))
        return {
            "emd": emd,
            "coupons": coupons,
            "ticket_summary": _ticket_summary(ticket),
            "booking_record_summary": _record_summary(booking_record),
            "booking_workspace_summary": _workspace_summary(workspace),
            "trip_summary": _trip_summary(trip),
            "timeline": timeline,
            "warnings": emd.get("warnings_json") or [],
            "service_mapping": self._service_mapping_summary(emd.get("linked_service_snapshot_json") or emd),
            "provider_execution_disabled": True,
        }

    async def update_emd_record(
        self,
        agency_id: str,
        emd_record_id: str,
        payload: EmdRecordUpdate,
        user: dict,
    ) -> dict[str, Any] | None:
        emd = await self.db.collection("emd_records").find_one(
            {"agency_id": agency_id, "id": emd_record_id}
        )
        if emd is None:
            return None
        updates = payload.model_dump(exclude_unset=True, mode="json")
        if "issue_status" in updates:
            updates["status"] = updates["issue_status"]
            if updates["issue_status"] == EmdStatus.ISSUED.value and not emd.get("issued_at"):
                updates["issued_at"] = _now_iso()
            if updates["issue_status"] == EmdStatus.VOIDED.value and not emd.get("voided_at"):
                updates["voided_at"] = _now_iso()
            if updates["issue_status"] == EmdStatus.REFUNDED.value and not emd.get("refunded_at"):
                updates["refunded_at"] = _now_iso()
            if updates["issue_status"] == EmdStatus.EXCHANGED.value and not emd.get("exchanged_at"):
                updates["exchanged_at"] = _now_iso()
        if updates.get("reason_for_issuance_code") and not updates.get("rfic_code"):
            updates["rfic_code"] = updates["reason_for_issuance_code"]
        if updates.get("reason_for_issuance_subcode") and not updates.get("rfisc_code"):
            updates["rfisc_code"] = updates["reason_for_issuance_subcode"]
        updates["updated_by_user_id"] = user.get("id")
        await self.db.collection("emd_records").update_one(
            {"agency_id": agency_id, "id": emd_record_id},
            updates,
        )
        await self._write_timeline(
            agency_id,
            "emd.updated",
            "EMD mirror updated",
            user.get("id"),
            emd_record_id=emd_record_id,
            booking_record_id=emd.get("booking_record_id"),
            booking_workspace_id=emd.get("booking_workspace_id"),
            trip_id=emd.get("trip_id"),
            description="Updated manual EMD mirror fields without EMD provider issuance.",
            payload_json={"updated_fields": sorted(updates.keys()), "provider_emd_issuance_disabled": True},
        )
        return await self.get_emd_detail(agency_id, emd_record_id)

    async def build_ticket_emd_readiness_summary(
        self,
        agency_id: str,
        booking_record_id: str,
    ) -> dict[str, Any] | None:
        booking_record = await self._get_booking_record(agency_id, booking_record_id)
        if booking_record is None:
            return None
        tickets = await self.db.collection("ticket_records").find_many(
            {"agency_id": agency_id, "booking_record_id": booking_record_id}
        )
        emds = await self.db.collection("emd_records").find_many(
            {"agency_id": agency_id, "booking_record_id": booking_record_id}
        )
        services = self._flatten_services(booking_record.get("services_json") or {})
        required_services = [
            service
            for service in services
            if str(_emd_applicability(service) or "").lower() in {"required", "conditional", "true"}
        ]
        emd_keys = {item.get("service_key") for item in emds if item.get("service_key")}
        emd_catalogue_ids = {item.get("service_catalogue_id") for item in emds if item.get("service_catalogue_id")}
        services_without_emd = [
            self._service_mapping_summary(service)
            for service in required_services
            if (_service_key(service) not in emd_keys and _service_catalogue_id(service) not in emd_catalogue_ids)
        ]
        warnings = []
        if services_without_emd:
            warnings.append(
                {
                    "code": "services_without_emd",
                    "message": "One or more EMD-applicable services do not have an EMD mirror yet.",
                    "severity": "warning",
                }
            )
        return {
            "booking_record_id": booking_record_id,
            "ticket_count": len(tickets),
            "emd_count": len(emds),
            "missing_ticket_numbers": len([item for item in tickets if not item.get("ticket_number")]),
            "missing_emd_numbers": len([item for item in emds if not item.get("emd_number")]),
            "services_requiring_emd": [self._service_mapping_summary(service) for service in required_services],
            "services_without_emd": services_without_emd,
            "warnings": warnings,
            "provider_execution_disabled": True,
        }

    async def _get_booking_record(self, agency_id: str, booking_record_id: str | None) -> dict[str, Any] | None:
        if not booking_record_id:
            return None
        return await self.db.collection("booking_records").find_one(
            {"agency_id": agency_id, "id": booking_record_id}
        )

    async def _get_workspace_for_record(
        self,
        agency_id: str,
        booking_record: dict[str, Any],
    ) -> dict[str, Any] | None:
        workspace_id = booking_record.get("booking_workspace_id")
        if not workspace_id:
            return None
        return await self.db.collection("booking_workspaces").find_one(
            {"agency_id": agency_id, "id": workspace_id}
        )

    async def _get_workspace(self, agency_id: str, booking_workspace_id: str | None) -> dict[str, Any] | None:
        if not booking_workspace_id:
            return None
        return await self.db.collection("booking_workspaces").find_one(
            {"agency_id": agency_id, "id": booking_workspace_id}
        )

    async def _get_trip(self, agency_id: str, trip_id: str | None) -> dict[str, Any] | None:
        if not trip_id:
            return None
        return await self.db.collection("trip_dossiers").find_one(
            {"agency_id": agency_id, "id": trip_id}
        )

    def _passenger_id(self, passenger: dict[str, Any] | None) -> str | None:
        if not passenger:
            return None
        for key in ["id", "passenger_id", "source_request_passenger_id", "request_passenger_id"]:
            if passenger.get(key):
                return passenger[key]
        return None

    def _select_passenger(self, booking_record: dict[str, Any], passenger_id: str | None) -> dict[str, Any] | None:
        passengers = _as_list(booking_record.get("passengers_json"))
        if passenger_id:
            for passenger in passengers:
                if passenger_id in _item_identity(passenger):
                    return passenger
        return passengers[0] if passengers else None

    def _fare_basis_snapshot(self, segments: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "items": [
                {
                    "segment_id": _segment_identity(segment, index),
                    "fare_basis": segment.get("fare_basis"),
                    "booking_class": segment.get("booking_class") or segment.get("rbd"),
                }
                for index, segment in enumerate(segments)
            ]
        }

    def _flatten_services(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        services: list[dict[str, Any]] = []
        for value in _as_dict(snapshot).values():
            if isinstance(value, list):
                services.extend([item for item in value if isinstance(item, dict)])
            elif isinstance(value, dict):
                nested = value.get("items")
                if isinstance(nested, list):
                    services.extend([item for item in nested if isinstance(item, dict)])
        return services

    def _resolve_service(
        self,
        booking_record: dict[str, Any],
        workspace: dict[str, Any] | None,
        payload: EmdCreateFromBookingServiceRequest,
    ) -> dict[str, Any]:
        services = self._flatten_services(booking_record.get("services_json") or {})
        if not services and workspace:
            services = self._flatten_services(workspace.get("services_snapshot_json") or {})
        for service in services:
            if payload.service_key and payload.service_key == _service_key(service):
                return service
            if payload.service_catalogue_id and payload.service_catalogue_id == _service_catalogue_id(service):
                return service
        return services[0] if services else {
            "service_key": payload.service_key,
            "service_catalogue_id": payload.service_catalogue_id,
            "service_label": payload.service_key or payload.service_catalogue_id or "Manual EMD service",
        }

    def _service_segment_ids(
        self,
        service: dict[str, Any],
        segments: list[dict[str, Any]],
    ) -> list[str]:
        ids = service.get("segment_ids") or service.get("linked_segment_ids") or service.get("associated_segment_ids")
        if isinstance(ids, list) and ids:
            return [str(item) for item in ids]
        if service.get("segment_id"):
            return [str(service["segment_id"])]
        return [_segment_identity(segment, index) for index, segment in enumerate(segments)]

    def _segments_by_ids(
        self,
        segments: list[dict[str, Any]],
        segment_ids: list[str],
    ) -> list[dict[str, Any]]:
        selected = []
        wanted = set(segment_ids)
        for index, segment in enumerate(segments):
            if _segment_identity(segment, index) in wanted:
                selected.append(segment)
        return selected

    async def _linked_ticket_coupons(
        self,
        agency_id: str,
        ticket_record_id: str | None,
        linked_segment_ids: list[str],
    ) -> list[dict[str, Any]]:
        if not ticket_record_id:
            return []
        coupons = await self.db.collection("ticket_coupons").find_many(
            {"agency_id": agency_id, "ticket_record_id": ticket_record_id}
        )
        if not linked_segment_ids:
            return coupons
        wanted = set(linked_segment_ids)
        return [item for item in coupons if item.get("segment_id") in wanted]

    async def _coupons_by_ids(self, agency_id: str, coupon_ids: list[str]) -> list[dict[str, Any]]:
        if not coupon_ids:
            return []
        found = []
        wanted = set(coupon_ids)
        for coupon_id in wanted:
            coupon = await self.db.collection("ticket_coupons").find_one({"agency_id": agency_id, "id": coupon_id})
            if coupon:
                found.append(coupon)
        return found

    def _service_mapping_summary(self, service: dict[str, Any]) -> dict[str, Any]:
        mapping = _service_catalogue_mapping(service)
        return {
            "service_key": _service_key(service),
            "service_catalogue_id": _service_catalogue_id(service),
            "service_label": _service_label(service),
            "service_category": _service_category(service),
            "emd_applicability": _emd_applicability(service),
            "pricing_applicability": service.get("pricing_applicability") or mapping.get("pricing_applicability"),
            "ssr_mapping": service.get("ssr_mapping_json") or mapping.get("ssr_mapping_json") or mapping.get("ssr_mapping"),
            "osi_mapping": service.get("osi_mapping_json") or mapping.get("osi_mapping_json") or mapping.get("osi_mapping"),
            "required_documents": service.get("required_documents_json") or mapping.get("required_documents_json") or mapping.get("required_documents"),
        }

    def _ticket_transition_evidence(
        self,
        ticket: dict[str, Any],
        user: dict,
        source_type: str,
        source_id: str | None,
        result: str,
        warnings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "agency_id": ticket["agency_id"],
            "actor_user_id": user.get("id"),
            "source_entity_type": source_type,
            "source_entity_id": source_id,
            "target_entity_type": "ticket_record",
            "target_entity_id": ticket["id"],
            "correlation_id": ticket.get("transition_correlation_id") or f"booking:{ticket.get('booking_record_id') or ticket.get('booking_workspace_id') or 'standalone'}:ticket-result",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "result": result,
            "warnings": warnings,
            "internal_only": True,
            "client_visible_summary": ticket.get("client_visible_notes"),
            "external_ticketing_performed": False,
            "manual_external_result": True,
        }

    async def _write_ticket_audit(
        self,
        ticket: dict[str, Any],
        user: dict,
        event_type: str,
        evidence: dict[str, Any],
    ) -> None:
        audit = AuditEvent(
            agency_id=ticket["agency_id"],
            actor_user_id=user.get("id"),
            event_type=event_type,
            entity_type="ticket_record",
            entity_id=ticket["id"],
            summary=f"Ticket external-result state recorded as {evidence['result']}.",
            metadata=evidence,
        )
        await self.db.collection("audit_events").insert_one(audit.model_dump(mode="json"))

    async def _sync_ticket_work_item(
        self,
        ticket: dict[str, Any],
        user: dict,
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        reconciliation_status = ticket.get("reconciliation_status") or "unreconciled"
        generated = await self.work_queue.generate_work_item(
            OperationalWorkItemGenerateRequest(
                agency_id=ticket["agency_id"],
                work_item_type="booking_awaiting_ticketing",
                source_entity_type="ticket_record",
                source_entity_id=ticket["id"],
                title=f"Reconcile external ticket {ticket.get('ticket_number') or ticket['id']}",
                summary=f"External ticket result reconciliation: {reconciliation_status}.",
                priority="high" if reconciliation_status in {"mismatch", "manual_review", "unknown"} else "normal",
                severity="high" if reconciliation_status == "mismatch" else "medium",
                queue_code="urgent_critical" if reconciliation_status == "mismatch" else "unassigned",
                blocker_status="manual_review" if reconciliation_status != "matched" else "not_blocked",
                generation_reason="external_ticket_result_reconciliation",
                source_snapshot_json=evidence,
                compatibility_mapping_json={
                    "ticket_record_id": ticket["id"],
                    "booking_record_id": ticket.get("booking_record_id"),
                    "booking_workspace_id": ticket.get("booking_workspace_id"),
                },
            ),
            user,
            agency_id=ticket["agency_id"],
        )
        work_item = generated.get("work_item") or {}
        if work_item.get("id"):
            if reconciliation_status == "matched" and work_item.get("status") != "completed":
                await self.work_queue.apply_action(
                    work_item["id"], "complete", OperationalWorkItemActionRequest(reason="External ticket result matched reviewed evidence."), user, agency_id=ticket["agency_id"]
                )
            elif reconciliation_status in {"mismatch", "manual_review", "unknown"} and work_item.get("status") != "blocked":
                await self.work_queue.apply_action(
                    work_item["id"], "block", OperationalWorkItemActionRequest(reason="External ticket result requires manual reconciliation.", blocker_status="manual_review"), user, agency_id=ticket["agency_id"]
                )
            await self.db.collection("ticket_records").update_one(
                {"agency_id": ticket["agency_id"], "id": ticket["id"]}, {"work_item_id": work_item["id"]}
            )
        return work_item

    async def _write_timeline(
        self,
        agency_id: str,
        event_type: str,
        title: str,
        actor_user_id: str | None,
        *,
        booking_workspace_id: str | None = None,
        booking_record_id: str | None = None,
        ticket_record_id: str | None = None,
        emd_record_id: str | None = None,
        trip_id: str | None = None,
        description: str | None = None,
        payload_json: dict[str, Any] | None = None,
    ) -> None:
        event = TicketEmdTimelineEvent(
            agency_id=agency_id,
            booking_workspace_id=booking_workspace_id,
            booking_record_id=booking_record_id,
            ticket_record_id=ticket_record_id,
            emd_record_id=emd_record_id,
            trip_id=trip_id,
            event_type=event_type,
            title=title,
            description=description,
            actor_user_id=actor_user_id,
            payload_json={
                "phase": PHASE_LABEL,
                **(payload_json or {}),
            },
        )
        await self.db.collection("ticket_emd_timeline_events").insert_one(event.model_dump(mode="json"))

    async def _write_trip_timeline(
        self,
        agency_id: str,
        trip_id: str,
        actor_user_id: str | None,
        event_type: str,
        title: str,
        summary: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        event = TripTimelineEvent(
            agency_id=agency_id,
            trip_id=trip_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            title=title,
            summary=summary,
            metadata=metadata or {},
        )
        await self.db.collection("trip_timeline_events").insert_one(event.model_dump(mode="json"))
