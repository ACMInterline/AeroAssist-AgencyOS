#!/usr/bin/env python3
"""Persisted V1 pilot acceptance smoke using the in-memory database adapter."""

from __future__ import annotations

import asyncio
import os
import sys
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path


os.environ["AEROASSIST_DB_MODE"] = "memory"
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from database import Database
from models import (
    Agency,
    AgencyStaffMembership,
    AfterSalesCaseCreate,
    AfterSalesFinancialImpactCreate,
    BookingRecordUpdate,
    ClientPassengerRelationship,
    ClientProfile,
    DocumentRenderJob,
    DocumentWorkspaceOutputReconciliationRequest,
    EmdCreateFromBookingServiceRequest,
    Invoice,
    InvoiceLineItem,
    ManualTicketCreate,
    OfferAcceptanceCreate,
    OfferBookingHandoffBookingCreateRequest,
    OfferBookingHandoffBuildRequest,
    OfferBuilderSegmentCreate,
    OfferFareBundleCreate,
    OfferOptionCreate,
    OfferPricingLineCreate,
    OfferWorkspaceTransitionRequest,
    PassengerProfile,
    PassengerServiceConfirmationRequest,
    PassengerServiceFulfilmentLinkRequest,
    PassengerServiceOutcomeRequest,
    PassengerServiceReconciliationRequest,
    PassengerServiceRequestCreate,
    PaymentRecord,
    PlatformUser,
    RequestPassenger,
    RequestPassengerSegmentService,
    RequestSegment,
    RequestTripConversionExecuteRequest,
    RequestedService,
    TicketResultReconciliationRequest,
    TravelRequest,
)
from services.after_sales_workflow_service import AfterSalesWorkflowError, AfterSalesWorkflowService
from services.booking_workspace_service import BookingWorkspaceService
from services.document_workspace_service import DocumentWorkspaceError, DocumentWorkspaceService
from services.offer_acceptance_service import OfferAcceptanceService
from services.offer_builder_service import OfferBuilderService
from services.offer_to_booking_handoff_service import OfferToBookingHandoffError, OfferToBookingHandoffService
from services.request_to_trip_conversion_service import RequestToTripConversionError, RequestToTripConversionService
from services.special_services_service import SpecialServicesService
from services.ticket_emd_service import TicketEmdService
from routers.finance import create_invoice_from_booking_workspace
from build_phase import CURRENT_BUILD_PHASE
from phase_assertions import application_phase_is_at_least


AGENCY_ID = "v1-golden-path-agency"
OTHER_AGENCY_ID = "v1-golden-path-other-agency"
USER_ID = "v1-golden-path-agent"
CORRELATION = "v1-golden-path-case-001"
MINIMUM_PHASE = "phase_54_7_servicing_after_sales_workflow_foundation"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


async def insert(db: Database, collection: str, model) -> dict:
    return await db.collection(collection).insert_one(model.model_dump(mode="json"))


async def expect_error(awaitable, error_type: type[Exception], label: str) -> None:
    try:
        await awaitable
    except error_type:
        return
    raise AssertionError(f"Expected protected failure for {label}.")


async def seed_case(db: Database) -> dict:
    agency = await insert(
        db,
        "agencies",
        Agency(id=AGENCY_ID, name="V1 Golden Path Agency", slug="v1-golden-path", legal_name="V1 Golden Path Agency Ltd", status="active"),
    )
    await insert(
        db,
        "agencies",
        Agency(id=OTHER_AGENCY_ID, name="Other Tenant", slug="v1-golden-other", legal_name="Other Tenant Ltd", status="active"),
    )
    user = await insert(
        db,
        "platform_users",
        PlatformUser(id=USER_ID, email="golden.path.agent@example.com", full_name="Golden Path Agent", status="active"),
    )
    await insert(
        db,
        "agency_staff_memberships",
        AgencyStaffMembership(
            agency_id=AGENCY_ID,
            user_id=USER_ID,
            email=user["email"],
            normalized_email=user["email"],
            agency_role="agency_agent",
            status="active",
        ),
    )
    client = await insert(
        db,
        "client_profiles",
        ClientProfile(
            agency_id=AGENCY_ID,
            display_name="Golden Path Client",
            primary_email="golden.path.client@example.com",
            data_processing_consent=True,
            internal_notes="Internal client note must never enter a client-safe projection.",
            client_visible_notes="Client profile ready.",
        ),
    )
    passenger = await insert(
        db,
        "passenger_profiles",
        PassengerProfile(
            agency_id=AGENCY_ID,
            first_name="Alex",
            last_name="Example",
            display_name="Alex Example",
            date_of_birth=date(1988, 4, 12),
            nationality="BG",
            known_assistance_needs="WCHC assistance required.",
            medical_notes_internal="Internal passenger note.",
        ),
    )
    relationship = await insert(
        db,
        "client_passenger_relationships",
        ClientPassengerRelationship(
            agency_id=AGENCY_ID,
            client_id=client["id"],
            passenger_id=passenger["id"],
            relationship_type="self",
            consent_status="granted",
        ),
    )
    request = await insert(
        db,
        "travel_requests",
        TravelRequest(
            agency_id=AGENCY_ID,
            client_id=client["id"],
            created_by_user_id=USER_ID,
            request_reference="REQ-V1-GOLDEN-001",
            title="Sofia to London assisted travel",
            status="new",
            priority="high",
            source="staff_created",
            requested_departure_date=date(2027, 2, 10),
            trip_type="one_way",
            route_summary="SOF to LHR",
            service_summary="WCHC manual airline confirmation required",
            passenger_count=1,
            service_count=1,
            special_service_count=1,
            internal_notes="Internal request handling note.",
            client_visible_notes="Assistance request received.",
            intake_payload_snapshot={"source": "synthetic_integration_smoke", "correlation_id": CORRELATION},
        ),
    )
    request_passenger = await insert(
        db,
        "request_passengers",
        RequestPassenger(
            agency_id=AGENCY_ID,
            request_id=request["id"],
            passenger_id=passenger["id"],
            passenger_link_mode="existing",
            client_passenger_relationship_id=relationship["id"],
            is_primary_traveler=True,
            service_needs_summary="WCHC",
            snapshot_display_name=passenger["display_name"],
            snapshot_date_of_birth=date(1988, 4, 12),
            snapshot_passenger_type="ADT",
        ),
    )
    request_segment = await insert(
        db,
        "request_segments",
        RequestSegment(
            agency_id=AGENCY_ID,
            request_id=request["id"],
            sequence=1,
            origin_text="Sofia",
            origin_airport_code="SOF",
            destination_text="London Heathrow",
            destination_airport_code="LHR",
            departure_date=date(2027, 2, 10),
            marketing_airline="BA",
            operating_airline="BA",
            preferred_airline_code="BA",
            preferred_flight_number="BA893",
            cabin_preference="economy",
        ),
    )
    requested_service = await insert(
        db,
        "requested_services",
        RequestedService(
            agency_id=AGENCY_ID,
            request_id=request["id"],
            passenger_id=passenger["id"],
            service_key="WCHC",
            service_code="WCHC",
            service_name="Wheelchair to cabin seat",
            service_category="mobility_assistance",
            passenger_ids=[passenger["id"]],
            segment_ids=[request_segment["id"]],
            applies_to_all_passengers=False,
            applies_to_all_segments=False,
            requires_documents=True,
            requires_airline_approval=True,
            internal_notes="Manual airline review required.",
            client_visible_summary="Wheelchair assistance requested.",
        ),
    )
    scope = await insert(
        db,
        "request_passenger_segment_services",
        RequestPassengerSegmentService(
            agency_id=AGENCY_ID,
            request_id=request["id"],
            requested_service_id=requested_service["id"],
            request_passenger_id=request_passenger["id"],
            request_segment_id=request_segment["id"],
            passenger_id=passenger["id"],
            segment_id=request_segment["id"],
            service_key="WCHC",
            service_code="WCHC",
            service_label="Wheelchair to cabin seat",
            applicability_status="requested",
            generated_key=f"{request['id']}:{request_passenger['id']}:{request_segment['id']}:WCHC",
        ),
    )
    return {
        "agency": agency,
        "user": user,
        "client": client,
        "passenger": passenger,
        "relationship": relationship,
        "request": request,
        "request_passenger": request_passenger,
        "request_segment": request_segment,
        "requested_service": requested_service,
        "scope": scope,
    }


async def run_golden_path() -> None:
    db = Database()
    require(db.mode == "memory", "Golden Path smoke must use the isolated in-memory database adapter.")
    context = await seed_case(db)
    user = {"id": USER_ID, "email": context["user"]["email"], "global_role": None}
    request_before = deepcopy(context["request"])

    conversion_service = RequestToTripConversionService(db)
    conversion_payload = RequestTripConversionExecuteRequest(
        agency_id=AGENCY_ID,
        request_id=context["request"]["id"],
        idempotency_key=CORRELATION,
        conversion_reason="Persisted V1 integration smoke.",
    )
    conversion = await conversion_service.execute_conversion(conversion_payload, user, agency_id=AGENCY_ID)
    trip = conversion.get("trip") or {}
    require(trip.get("id") and trip["id"] != context["request"]["id"], "Request conversion did not create a distinct trip.")
    require(conversion.get("run", {}).get("run_status") == "executed", "Request conversion did not execute.")
    mapping_types = {item.get("mapping_type") for item in conversion.get("mappings") or []}
    require("request_passenger_to_trip_passenger" in mapping_types, "Passenger mapping is missing.")
    require("request_segment_to_trip_segment" in mapping_types, "Segment mapping is missing.")
    require("request_scoped_service_to_trip_service" in mapping_types, "Scoped service mapping is missing.")
    conversion_retry = await conversion_service.execute_conversion(conversion_payload, user, agency_id=AGENCY_ID)
    require(conversion_retry.get("trip", {}).get("id") == trip["id"], "Request conversion retry created a duplicate trip.")
    require(conversion_retry.get("idempotent_reused") is True, "Request conversion retry was not explicitly idempotent.")
    request_after = await db.collection("travel_requests").find_one({"agency_id": AGENCY_ID, "id": context["request"]["id"]})
    for field in ["request_reference", "title", "client_id", "intake_payload_snapshot", "internal_notes", "client_visible_notes"]:
        require(request_after.get(field) == request_before.get(field), f"Request source field was mutated: {field}.")
    await expect_error(
        conversion_service.execute_conversion(conversion_payload, user, agency_id=OTHER_AGENCY_ID),
        RequestToTripConversionError,
        "cross-tenant request conversion",
    )

    builder = OfferBuilderService(db)
    offer_workspace = await builder.create_workspace_from_trip(AGENCY_ID, trip["id"], USER_ID)
    require(bool(offer_workspace), "Trip did not create an offer workspace.")
    option = await builder.create_option(
        AGENCY_ID,
        offer_workspace["id"],
        OfferOptionCreate(
            label="BA assisted economy",
            main_airline_code="BA",
            provider_name="manual",
            service_feasibility_json={"WCHC": {"status": "conditional", "manual_confirmation_required": True}},
            rules_summary_json={"evidence_status": "manual_review", "provider_execution": False},
            internal_notes="Internal offer assessment.",
        ),
        USER_ID,
    )
    await builder.add_segment(
        AGENCY_ID,
        option["id"],
        OfferBuilderSegmentCreate(
            sequence=1,
            marketing_airline_code="BA",
            operating_airline_code="BA",
            flight_number="BA893",
            origin_airport="SOF",
            destination_airport="LHR",
            departure_at=datetime(2027, 2, 10, 12, 0, tzinfo=timezone.utc),
            arrival_at=datetime(2027, 2, 10, 14, 20, tzinfo=timezone.utc),
            cabin_class="economy",
            booking_class="Y",
            fare_basis="YFLEX",
        ),
        USER_ID,
    )
    await builder.add_fare_bundle(
        AGENCY_ID,
        option["id"],
        OfferFareBundleCreate(
            fare_family_name="Economy Flex",
            cabin_class="economy",
            booking_class="Y",
            included_baggage_json={"checked_pieces": 1},
        ),
        USER_ID,
    )
    for line_type, label, amount in [("base_fare", "Fare", 220.0), ("tax", "Taxes", 65.0), ("service_fee", "Agency service", 20.0)]:
        await builder.add_pricing_line(
            AGENCY_ID,
            option["id"],
            OfferPricingLineCreate(line_type=line_type, label=label, amount=amount, currency="EUR"),
            USER_ID,
        )
    await builder.recalculate_option_pricing(AGENCY_ID, option["id"], USER_ID)
    offer_workspace = await builder.deliver_workspace(
        AGENCY_ID,
        offer_workspace["id"],
        OfferWorkspaceTransitionRequest(
            expected_version=offer_workspace["version"],
            reason="V1 pilot accepted-offer delivery evidence.",
        ),
        USER_ID,
    )
    option = await builder.get_option_or_none(AGENCY_ID, option["id"])

    acceptance_result = await OfferAcceptanceService(db).accept_offer_option(
        AGENCY_ID,
        offer_workspace["id"],
        option["id"],
        user,
        OfferAcceptanceCreate(
            acceptance_source="internal",
            offer_version=offer_workspace["version"],
            option_version=option["version"],
            acceptance_terms_version="v1-pilot-acceptance-v1",
            provider_target="manual",
            client_visible_summary_json={"option_label": "BA assisted economy", "manual_confirmation_required": True},
            internal_notes="Frozen internal acceptance note.",
        ),
    )
    acceptance = acceptance_result.get("acceptance") or {}
    readiness = acceptance_result.get("booking_readiness") or {}
    trip_snapshot = acceptance_result.get("trip_snapshot") or {}
    require(acceptance.get("status") == "accepted" and readiness.get("id") and trip_snapshot.get("id"), "Offer acceptance did not create frozen readiness evidence.")
    frozen_pricing = deepcopy(acceptance["accepted_pricing_snapshot_json"])
    await db.collection("offer_options").update_one({"agency_id": AGENCY_ID, "id": option["id"]}, {"pricing_summary_json": {"currency": "EUR", "total_amount": 9999.0}})
    immutable_acceptance = await db.collection("offer_acceptances").find_one({"agency_id": AGENCY_ID, "id": acceptance["id"]})
    require(immutable_acceptance["accepted_pricing_snapshot_json"] == frozen_pricing, "Mutable offer edit changed the accepted snapshot.")

    handoff_service = OfferToBookingHandoffService(db)
    handoff_payload = OfferBookingHandoffBuildRequest(
        agency_id=AGENCY_ID,
        acceptance_id=acceptance["id"],
        booking_readiness_package_id=readiness["id"],
        booking_mode="manual",
        idempotency_key=f"{CORRELATION}:handoff",
    )
    handoff_result = await handoff_service.build_handoff(handoff_payload, user, agency_id=AGENCY_ID)
    handoff = handoff_result.get("handoff") or {}
    require(handoff.get("handoff_status") in {"ready", "conditional"}, "Canonical booking handoff was not usable.")
    handoff_retry = await handoff_service.build_handoff(handoff_payload, user, agency_id=AGENCY_ID)
    require(handoff_retry.get("idempotent_reused") is True and handoff_retry.get("handoff", {}).get("id") == handoff["id"], "Booking handoff retry duplicated the handoff.")
    await expect_error(
        handoff_service.build_handoff(handoff_payload, user, agency_id=OTHER_AGENCY_ID),
        OfferToBookingHandoffError,
        "cross-tenant booking handoff",
    )
    booking_result = await handoff_service.create_booking_workspace(
        handoff["id"],
        OfferBookingHandoffBookingCreateRequest(
            provider_target="manual",
            booking_mode="manual",
            create_draft_record=True,
            allow_conditional=True,
            internal_notes="Record external booking result manually; no provider execution.",
        ),
        user,
        agency_id=AGENCY_ID,
    )
    booking_workspace = booking_result.get("booking_workspace") or {}
    booking_record = (booking_result.get("booking_result") or {}).get("booking_record") or {}
    require(booking_workspace.get("id") and booking_record.get("id"), "Handoff did not create booking workspace and record metadata.")
    require(booking_workspace.get("offer_acceptance_id") == acceptance["id"], "Booking workspace lost the accepted-offer relationship.")
    require(booking_workspace.get("client_id") == context["client"]["id"], "Booking workspace lost the canonical client link.")
    require(context["passenger"]["id"] in booking_workspace.get("passenger_ids", []), "Booking workspace lost the canonical passenger link.")
    require(booking_record.get("client_id") == context["client"]["id"], "Booking record lost the canonical client link.")
    booking_retry = await handoff_service.create_booking_workspace(
        handoff["id"], OfferBookingHandoffBookingCreateRequest(), user, agency_id=AGENCY_ID
    )
    require(booking_retry.get("idempotent_reused") is True and booking_retry.get("booking_workspace", {}).get("id") == booking_workspace["id"], "Booking workspace retry duplicated the workspace.")

    booking_service = BookingWorkspaceService(db)
    await booking_service.update_booking_workspace_status(
        AGENCY_ID,
        booking_workspace["id"],
        "booking_in_progress",
        user,
        "Human operator began the external booking step.",
    )
    confirmed_booking = await booking_service.update_booking_record(
        AGENCY_ID,
        booking_record["id"],
        BookingRecordUpdate(
            pnr_locator="V1PILT",
            provider_status="confirmed",
            booking_status="confirmed",
            source_evidence_reference="evidence://booking/manual/V1PILT",
            source_evidence_json={"operator_verified": True},
            expected_version=booking_record["current_external_result_version"],
            reason="Recorded the externally confirmed pilot booking result.",
        ),
        user,
    )
    booking_workspace = (
        (confirmed_booking or {}).get("booking_workspace") or booking_workspace
    )
    booking_record = (confirmed_booking or {}).get("booking_record") or {}
    require(
        booking_record.get("booking_status") == "confirmed"
        and booking_record.get("source_evidence_reference"),
        "Pilot acceptance did not record governed confirmed BookingRecord evidence.",
    )

    ticket_service = TicketEmdService(db)
    ticket_detail = await ticket_service.create_manual_ticket(
        AGENCY_ID,
        ManualTicketCreate(
            booking_record_id=booking_record["id"],
            booking_workspace_id=booking_workspace["id"],
            trip_id=trip["id"],
            client_id=context["client"]["id"],
            passenger_id=context["passenger"]["id"],
            ticket_number="125-1234567890",
            validating_carrier="BA",
            issue_status="issued",
            external_result_status="externally_issued",
            external_evidence_reference="evidence://ticket/manual/125-1234567890",
            client_visible_notes="Ticket result recorded.",
            internal_notes="Internal ticket reconciliation note.",
            create_coupons=True,
        ),
        user,
    )
    ticket = ticket_detail.get("ticket") or {}
    coupons = ticket_detail.get("coupons") or []
    require(ticket.get("id") and coupons, "Externally issued manual ticket metadata or coupons are missing.")
    mismatch = await ticket_service.reconcile_ticket_result(
        AGENCY_ID,
        ticket["id"],
        TicketResultReconciliationRequest(
            reconciliation_status="mismatch",
            external_result_status="externally_issued",
            external_evidence_reference=ticket["external_evidence_reference"],
            unresolved_mismatches_json=[{"code": "coupon_status_unknown", "message": "Manual review required."}],
            internal_notes="Internal mismatch detail.",
            client_visible_notes="Ticket review is in progress.",
        ),
        user,
    )
    require((mismatch.get("ticket") or {}).get("reconciliation_status") == "mismatch", "Ticket failure state was not recoverable and explicit.")
    ticket_detail = await ticket_service.reconcile_ticket_result(
        AGENCY_ID,
        ticket["id"],
        TicketResultReconciliationRequest(
            reconciliation_status="matched",
            external_result_status="externally_issued",
            external_evidence_reference=ticket["external_evidence_reference"],
            unresolved_mismatches_json=[],
            client_visible_notes="Ticket evidence matched.",
        ),
        user,
    )
    require((ticket_detail.get("ticket") or {}).get("reconciliation_status") == "matched", "Ticket result did not reconcile.")
    require("internal_notes" not in (ticket_detail.get("client_safe_ticket") or {}), "Ticket client-safe projection leaked internal notes.")

    emd_detail = await ticket_service.create_emd_from_booking_service(
        AGENCY_ID,
        EmdCreateFromBookingServiceRequest(
            booking_record_id=booking_record["id"],
            passenger_id=context["passenger"]["id"],
            service_key="WCHC",
            ticket_record_id=ticket["id"],
            create_coupons=True,
            internal_notes="Internal EMD service link; no provider execution.",
        ),
        user,
    )
    emd = (emd_detail or {}).get("emd") or {}
    emd_coupons = (emd_detail or {}).get("coupons") or []
    require(emd.get("id") and emd_coupons, "Canonical EMD metadata or coupons are missing.")
    require(emd.get("ticket_record_id") == ticket["id"], "EMD lost its canonical ticket relationship.")

    passenger_service = SpecialServicesService(db)
    service_case = await passenger_service.add_service_request(
        AGENCY_ID,
        PassengerServiceRequestCreate(
            request_id=context["request"]["id"],
            trip_id=trip["id"],
            passenger_id=context["passenger"]["id"],
            segment_id=context["request_segment"]["id"],
            category="PRM",
            service_type="WCHC",
            service_key="WCHC",
            service_label="Wheelchair to cabin seat",
            required_documents_json=[{"document_type": "medical_certificate", "status": "required"}],
            metadata_json={"source_need": "request", "client_visible_summary": "Wheelchair assistance requested."},
        ),
        USER_ID,
    )
    await passenger_service.link_fulfilment_records(
        AGENCY_ID,
        service_case["id"],
        PassengerServiceFulfilmentLinkRequest(
            booking_workspace_id=booking_workspace["id"],
            booking_record_id=booking_record["id"],
            ticket_record_ids=[ticket["id"]],
            emd_record_ids=[emd["id"]],
            emd_coupon_ids=[emd_coupons[0]["id"]],
        ),
        user,
    )
    document_result = await passenger_service.ensure_document_requirement(AGENCY_ID, service_case["id"], user)
    document_retry = await passenger_service.ensure_document_requirement(AGENCY_ID, service_case["id"], user)
    document_workspace = document_result["document_workspace"]
    require(document_result["created"] is True, "Canonical passenger-service document requirement was not created.")
    require(document_retry["created"] is False and document_retry["document_workspace"]["id"] == document_workspace["id"], "Document requirement retry was not idempotent.")
    require(document_workspace["booking_workspace_id"] == booking_workspace["id"], "Document requirement did not retain canonical booking context.")
    document_service = DocumentWorkspaceService(db)
    render_job = await insert(
        db,
        "document_render_jobs",
        DocumentRenderJob(
            agency_id=AGENCY_ID,
            document_type="service_confirmation",
            source_context_type="service_request",
            source_context_id=service_case["id"],
            render_status="rendered",
            render_format="html",
            rendered_html="<p>Synthetic service confirmation output</p>",
            created_by_user_id=USER_ID,
            internal_notes="Internal render note.",
        ),
    )
    generated = await document_service.reconcile_output(
        AGENCY_ID,
        document_workspace["id"],
        DocumentWorkspaceOutputReconciliationRequest(render_job_id=render_job["id"], document_status="generated", review_notes="Output generated; not verified."),
        user,
    )
    require(generated["document_workspace"]["document_status"] == "generated" and not generated["document_workspace"].get("verified_at"), "Rendering incorrectly verified the requirement.")

    link_payload = PassengerServiceFulfilmentLinkRequest(
        booking_workspace_id=booking_workspace["id"],
        booking_record_id=booking_record["id"],
        ticket_record_ids=[ticket["id"]],
        ticket_coupon_ids=[coupons[0]["id"]],
        emd_record_ids=[emd["id"]],
        emd_coupon_ids=[emd_coupons[0]["id"]],
        document_workspace_ids=[document_workspace["id"]],
        next_action="Obtain and review manual airline confirmation.",
    )
    linked = await passenger_service.link_fulfilment_records(AGENCY_ID, service_case["id"], link_payload, user)
    linked_retry = await passenger_service.link_fulfilment_records(AGENCY_ID, service_case["id"], link_payload, user)
    linked_service = linked_retry["service"]
    require(linked_service["ticket_record_ids"] == [ticket["id"]], "Ticket mapping duplicated on retry.")
    require(linked_service["emd_record_ids"] == [emd["id"]], "EMD mapping duplicated on retry.")
    require(linked_service["document_workspace_ids"] == [document_workspace["id"]], "Document mapping duplicated on retry.")
    require("metadata_json" not in linked_service["client_safe_projection"], "Passenger-service client-safe projection leaked internal metadata.")
    fulfilment_options = await passenger_service.fulfilment_link_options(AGENCY_ID, service_case["id"])
    for group, entity_id in [
        ("booking_workspaces", booking_workspace["id"]),
        ("booking_records", booking_record["id"]),
        ("tickets", ticket["id"]),
        ("ticket_coupons", coupons[0]["id"]),
        ("emds", emd["id"]),
        ("emd_coupons", emd_coupons[0]["id"]),
        ("documents", document_workspace["id"]),
    ]:
        option = next((item for item in fulfilment_options["items"][group] if item["id"] == entity_id), None)
        require(option is not None and option.get("label"), f"Passenger-service canonical option missing for {group}.")
        require("context" in option and "warnings" in option, f"Passenger-service context missing for {group}.")
    await expect_error(
        passenger_service.fulfilment_link_options(OTHER_AGENCY_ID, service_case["id"]),
        ValueError,
        "cross-tenant passenger-service selector discovery",
    )
    await expect_error(
        passenger_service.link_fulfilment_records(OTHER_AGENCY_ID, service_case["id"], link_payload, user),
        ValueError,
        "cross-tenant passenger-service linkage",
    )
    conditional = await passenger_service.record_confirmation(
        AGENCY_ID,
        service_case["id"],
        PassengerServiceConfirmationRequest(
            airline_confirmation_status="confirmed",
            airport_handling_confirmation_status="unknown",
            external_manual_status="unknown",
        ),
        user,
    )
    require(conditional["service"]["airline_confirmation_status"] == "conditionally_confirmed", "Confirmation without evidence was presented as certain.")
    confirmed = await passenger_service.record_confirmation(
        AGENCY_ID,
        service_case["id"],
        PassengerServiceConfirmationRequest(
            airline_confirmation_status="confirmed",
            airline_confirmation_evidence_reference="evidence://airline/manual-confirmation/BA-WCHC-001",
            airport_handling_confirmation_status="confirmed",
            airport_handling_evidence_reference="evidence://airport/manual-confirmation/LHR-WCHC-001",
            external_manual_status="confirmed",
            next_action="Verify document and record departure-day outcome.",
        ),
        user,
    )
    require(confirmed["service"]["fulfilment_result"] == "confirmed", "Evidence-backed confirmation was not recorded.")
    unknown = await passenger_service.reconcile_fulfilment(
        AGENCY_ID,
        service_case["id"],
        PassengerServiceReconciliationRequest(
            external_manual_status="unknown",
            fulfilment_result="unknown",
            unresolved_mismatches_json=[{"code": "departure_outcome_pending", "message": "Outcome unknown until manual review."}],
            next_action="Manual departure-day review.",
            internal_notes="Internal reconciliation context.",
            client_visible_summary="Assistance outcome is being reviewed.",
        ),
        user,
    )
    require(unknown["service"]["fulfilment_result"] == "unknown", "Unknown passenger-service state was not preserved.")
    await expect_error(
        passenger_service.record_fulfilment_outcome(
            AGENCY_ID,
            service_case["id"],
            PassengerServiceOutcomeRequest(fulfilment_result="fulfilled", unresolved_mismatches_json=[]),
            user,
        ),
        ValueError,
        "fulfilled service without evidence",
    )
    verified_document = await document_service.reconcile_output(
        AGENCY_ID,
        document_workspace["id"],
        DocumentWorkspaceOutputReconciliationRequest(render_job_id=render_job["id"], document_status="verified", review_notes="Operator reviewed generated output."),
        user,
    )
    require(verified_document["document_workspace"].get("verified_by") == USER_ID and verified_document["document_workspace"].get("verified_at"), "Document verification actor/time is missing.")
    require(verified_document["document_workspace"]["render_job_ids"] == [render_job["id"]], "Document output linkage duplicated on retry.")
    await expect_error(
        document_service.reconcile_output(
            OTHER_AGENCY_ID,
            document_workspace["id"],
            DocumentWorkspaceOutputReconciliationRequest(render_job_id=render_job["id"], document_status="verified"),
            user,
        ),
        DocumentWorkspaceError,
        "cross-tenant document reconciliation",
    )
    fulfilled = await passenger_service.record_fulfilment_outcome(
        AGENCY_ID,
        service_case["id"],
        PassengerServiceOutcomeRequest(
            fulfilment_result="fulfilled",
            evidence_reference="evidence://departure/manual/WCHC-fulfilled-001",
            unresolved_mismatches_json=[],
            client_visible_summary="Assistance was delivered.",
        ),
        user,
    )
    require(fulfilled["service"]["fulfilment_result"] == "fulfilled", "Passenger-service outcome did not resolve.")

    invoice_result = await create_invoice_from_booking_workspace(AGENCY_ID, booking_workspace["id"], user=user, db=db)
    invoice = invoice_result["invoice"]
    require(
        invoice.get("booking_workspace_id") == booking_workspace["id"]
        and invoice.get("booking_record_id") == booking_record["id"],
        "Documents-to-Finance bridge did not preserve canonical booking links.",
    )
    invoice_retry = await create_invoice_from_booking_workspace(AGENCY_ID, booking_workspace["id"], user=user, db=db)
    require(invoice_retry.get("idempotent_reused") is True and invoice_retry["invoice"]["id"] == invoice["id"], "Finance bridge retry duplicated the invoice.")
    invoice = await db.collection("invoices").update_one(
        {"agency_id": AGENCY_ID, "id": invoice["id"]},
        {
            "status": "issued",
            "subtotal_amount": 305.0,
            "total_amount": 305.0,
            "paid_amount": 305.0,
            "due_amount": 0.0,
            "internal_notes": "Internal invoice note.",
            "client_visible_notes": "Paid in full.",
        },
    )
    invoice_line = await insert(
        db,
        "invoice_line_items",
        InvoiceLineItem(
            agency_id=AGENCY_ID,
            invoice_id=invoice["id"],
            booking_id=booking_record["id"],
            ticket_id=ticket["id"],
            line_type="airfare",
            description="Accepted assisted itinerary",
            quantity=1,
            unit_amount=305.0,
            total_amount=305.0,
            currency="EUR",
        ),
    )
    payment = await insert(
        db,
        "payment_records",
        PaymentRecord(
            agency_id=AGENCY_ID,
            invoice_id=invoice["id"],
            booking_id=booking_record["id"],
            client_id=context["client"]["id"],
            status="received",
            method="bank_transfer",
            amount=305.0,
            currency="EUR",
            external_reference="BANK-REF-V1-001",
            reconciliation_status="reconciled",
            internal_notes="Internal bank reconciliation note.",
        ),
    )
    after_sales_service = AfterSalesWorkflowService(db)
    link_options = await after_sales_service.link_options(AGENCY_ID)
    option_groups = link_options["items"]
    isolated_options = await after_sales_service.link_options(OTHER_AGENCY_ID)
    require(
        all(
            booking_workspace["id"] not in {item["id"] for item in group}
            for group in isolated_options["items"].values()
        ),
        "Cross-tenant canonical options leaked into another agency.",
    )
    for group, entity_id in [
        ("bookings", booking_workspace["id"]),
        ("passenger_services", service_case["id"]),
        ("accepted_offer_snapshots", trip_snapshot["id"]),
        ("invoices", invoice["id"]),
        ("invoice_lines", invoice_line["id"]),
        ("payments", payment["id"]),
        ("tickets", ticket["id"]),
        ("emds", emd["id"]),
    ]:
        option = next((item for item in option_groups[group] if item["id"] == entity_id), None)
        require(option is not None and option.get("label"), f"Canonical selector option missing for {group}.")
        require("context" in option and "warnings" in option, f"Canonical selector context missing for {group}.")
    require(link_options.get("immutable_reference_snapshots_enabled") is True, "Selector contract does not preserve immutable references.")
    after_sales_result = await after_sales_service.create_case(
        AfterSalesCaseCreate(
            agency_id=AGENCY_ID,
            case_type="voluntary_change",
            case_status="assessing",
            case_priority="high",
            case_title="Voluntary date change review",
            case_summary="Review affected ticket and commercial records without financial commitment.",
            booking_workspace_id=booking_workspace["id"],
            source_entity_type="trip",
            source_entity_id=trip["id"],
            invoice_ids=[invoice["id"]],
            invoice_line_item_ids=[invoice_line["id"]],
            payment_record_ids=[payment["id"]],
            ticket_record_ids=[ticket["id"]],
            emd_record_ids=[emd["id"]],
            passenger_service_request_ids=[service_case["id"], service_case["id"]],
            accepted_offer_snapshot_id=trip_snapshot["id"],
            booking_reference=booking_workspace.get("booking_reference") or booking_workspace.get("workspace_number"),
            idempotency_key=f"{CORRELATION}:after-sales",
            internal_message_json={"message": "Internal review only."},
            client_message_json={"message": "Your change request is under review."},
        ),
        user,
        agency_id=AGENCY_ID,
    )
    after_sales_case = after_sales_result["case"]
    require(after_sales_case["affected_financial_records"]["invoice_ids"] == [invoice["id"]], "After Sales did not retain invoice linkage.")
    require(after_sales_case["affected_financial_records"]["payment_record_ids"] == [payment["id"]], "After Sales did not retain payment linkage.")
    require(after_sales_case["emd_record_ids"] == [emd["id"]], "After Sales did not retain EMD linkage.")
    require(after_sales_case["passenger_service_request_ids"] == [service_case["id"]], "After Sales did not prevent duplicate passenger-service linkage.")
    require((after_sales_case.get("canonical_reference_snapshot_json") or {}).get("immutable_reference_evidence") is True, "After Sales did not preserve canonical reference evidence.")
    require(any(item.get("source_entity_type") == "passenger_service_request" for item in after_sales_case.get("items") or []), "After Sales did not preserve passenger-service context.")
    captured_ticket = after_sales_case["canonical_reference_snapshot_json"]["references"]["ticket_record_ids"][0]
    await db.collection("ticket_records").update_one(
        {"agency_id": AGENCY_ID, "id": ticket["id"]},
        {"reconciliation_status": "source_changed_after_link"},
    )
    immutable_case = await after_sales_service.get_case(after_sales_case["id"], agency_id=AGENCY_ID)
    require(
        immutable_case["canonical_reference_snapshot_json"]["references"]["ticket_record_ids"][0] == captured_ticket,
        "Canonical reference evidence changed when the source record changed.",
    )
    mismatched_invoice = await insert(
        db,
        "invoices",
        Invoice(
            agency_id=AGENCY_ID,
            invoice_number="INV-V1-OTHER",
            client_id=context["client"]["id"],
            status="draft",
            currency="EUR",
            subtotal_amount=10.0,
            total_amount=10.0,
        ),
    )
    await expect_error(
        after_sales_service.create_case(
            AfterSalesCaseCreate(
                agency_id=AGENCY_ID,
                case_type="refund",
                case_title="Reject mismatched invoice context",
                invoice_ids=[mismatched_invoice["id"]],
                invoice_line_item_ids=[invoice_line["id"]],
                idempotency_key=f"{CORRELATION}:mismatched-invoice",
            ),
            user,
            agency_id=AGENCY_ID,
        ),
        AfterSalesWorkflowError,
        "invoice-line ownership mismatch",
    )
    mismatch_payload = AfterSalesFinancialImpactCreate(
        impact_type="fare_difference",
        amount_category="fare_difference",
        estimate_status="manual_review",
        amount=75.0,
        currency="EUR",
        invoice_ids=[invoice["id"]],
        invoice_line_item_ids=[invoice_line["id"]],
        payment_record_ids=[payment["id"]],
        ticket_record_ids=[ticket["id"]],
        emd_record_ids=[emd["id"]],
        accepted_offer_snapshot_id=trip_snapshot["id"],
        booking_reference=after_sales_case.get("booking_reference"),
        proposed_financial_impact_snapshot_json={"fare_difference": 75.0, "source": "manual_quote"},
        reconciliation_state="manual_review",
        unresolved_mismatches_json=[{"code": "supplier_quote_pending", "message": "Final amount not confirmed."}],
        correlation_id=f"{CORRELATION}:finance:mismatch",
    )
    mismatch_impact = await after_sales_service.create_financial_impact(after_sales_case["id"], mismatch_payload, user, agency_id=AGENCY_ID)
    require(mismatch_impact["financial_impact"]["reconciliation_state"] == "manual_review", "Financial mismatch state was not explicit.")
    impact_retry = await after_sales_service.create_financial_impact(after_sales_case["id"], mismatch_payload, user, agency_id=AGENCY_ID)
    require(impact_retry.get("idempotent_reused") is True and impact_retry["financial_impact"]["id"] == mismatch_impact["financial_impact"]["id"], "Financial mapping retry created a duplicate.")
    resolved_impact = await after_sales_service.create_financial_impact(
        after_sales_case["id"],
        AfterSalesFinancialImpactCreate(
            impact_type="fare_difference",
            amount_category="fare_difference",
            estimate_status="confirmed_metadata",
            amount=70.0,
            currency="EUR",
            invoice_ids=[invoice["id"]],
            invoice_line_item_ids=[invoice_line["id"]],
            payment_record_ids=[payment["id"]],
            ticket_record_ids=[ticket["id"]],
            emd_record_ids=[emd["id"]],
            accepted_offer_snapshot_id=trip_snapshot["id"],
            booking_reference=after_sales_case.get("booking_reference"),
            original_financial_snapshot_json={"invoice_id": invoice["id"], "amount": 305.0},
            proposed_financial_impact_snapshot_json={"fare_difference": 70.0},
            final_reconciled_financial_snapshot_json={"reviewed_fare_difference": 70.0, "reviewed_payment_id": payment["id"]},
            approval_state="approved",
            settlement_state="not_settled",
            reconciliation_state="reconciled",
            unresolved_mismatches_json=[],
            correlation_id=f"{CORRELATION}:finance:resolved",
        ),
        user,
        agency_id=AGENCY_ID,
    )
    require(resolved_impact["financial_impact"]["reconciliation_state"] == "reconciled", "Linked financial impact did not reconcile.")
    await expect_error(
        after_sales_service.create_case(
            AfterSalesCaseCreate(
                agency_id=OTHER_AGENCY_ID,
                case_type="voluntary_change",
                case_title="Cross-tenant rejection",
                booking_workspace_id=booking_workspace["id"],
                invoice_ids=[invoice["id"]],
            ),
            user,
            agency_id=OTHER_AGENCY_ID,
        ),
        AfterSalesWorkflowError,
        "cross-tenant after-sales finance linkage",
    )

    audits = await db.collection("audit_events").find_many({"agency_id": AGENCY_ID}, limit=250)
    transition_pairs = {
        (item.get("metadata") or {}).get("source_entity_type", "") + "->" + (item.get("metadata") or {}).get("target_entity_type", "")
        for item in audits
    }
    for pair in [
        "trip->offer_workspace",
        "accepted_offer->offer_booking_handoff",
        "booking_record->ticket_record",
        "passenger_service_request->document_workspace",
        "financial_records->after_sales_financial_impact",
    ]:
        require(pair in transition_pairs, f"Transition audit evidence is missing: {pair}.")
    required_trace_fields = {
        "agency_id", "actor_user_id", "source_entity_type", "source_entity_id", "target_entity_type",
        "target_entity_id", "correlation_id", "occurred_at", "result", "warnings", "internal_only", "client_visible_summary",
    }
    touched_audits = [item for item in audits if (item.get("metadata") or {}).get("target_entity_type")]
    require(touched_audits, "No touched transition audits were persisted.")
    for audit in touched_audits:
        missing = required_trace_fields - set((audit.get("metadata") or {}).keys())
        require(not missing, f"Transition audit {audit.get('event_type')} lacks fields: {sorted(missing)}")

    timelines = await db.collection("operational_timelines").find_many({"agency_id": AGENCY_ID}, limit=250)
    work_items = await db.collection("operational_work_items").find_many({"agency_id": AGENCY_ID}, limit=250)
    workflows = await db.collection("operational_workflow_instances").find_many({"agency_id": AGENCY_ID}, limit=250)
    require(timelines and work_items and workflows, "Golden Path did not persist timeline, queue, and workflow evidence.")
    require(any((item.get("metadata") or {}).get("correlation_id") for item in timelines), "Operational timelines lack correlated transition evidence.")
    require(not await db.collection("travel_requests").find_one({"agency_id": OTHER_AGENCY_ID, "id": context["request"]["id"]}), "Tenant isolation failed for the request.")

    print("PASS: persisted V1 pilot acceptance")
    print(f"agency={AGENCY_ID} correlation={CORRELATION}")
    print(f"trip={trip['id']} acceptance={acceptance['id']} handoff={handoff['id']} booking={booking_workspace['id']} ticket={ticket['id']} emd={emd['id']}")
    print(f"service={service_case['id']} document={document_workspace['id']} invoice={invoice['id']} after_sales={after_sales_case['id']}")
    print(f"audit_events={len(audits)} timelines={len(timelines)} work_items={len(work_items)} workflows={len(workflows)}")
    print("acceptance_checks=successful_workflow,validation_failure_recovery,mismatch_reconciliation,idempotency,cross_agency_rejection,after_sales_financial_linkage")


def verify_static_contracts() -> None:
    require(
        application_phase_is_at_least(CURRENT_BUILD_PHASE, MINIMUM_PHASE),
        f"Application phase {CURRENT_BUILD_PHASE} predates the integrated After Sales baseline.",
    )
    stale_mapping = "ssr_osi_operational_workspaces"
    service_text = (ROOT / "backend/services/airline_contact_communication_intelligence_service.py").read_text(encoding="utf-8")
    require(stale_mapping not in service_text, "Stale SSR/OSI integration mapping returned.")
    offer_page = (ROOT / "frontend/src/pages/agency/OfferWorkspaceDetailPage.jsx").read_text(encoding="utf-8")
    require("/agency/booking-handoffs" in offer_page, "Primary offer UI does not use booking handoff.")
    require("booking-workspaces/from-readiness" not in offer_page, "Primary offer UI still bypasses booking handoff.")
    trip_page = (ROOT / "frontend/src/pages/agency/TripDetailPage.jsx").read_text(encoding="utf-8")
    offer_builder_page = (ROOT / "frontend/src/pages/agency/OfferBuilderPage.jsx").read_text(encoding="utf-8")
    request_page = (ROOT / "frontend/src/pages/agency/RequestDetailPage.jsx").read_text(encoding="utf-8")
    conversion_page = (ROOT / "frontend/src/pages/agency/RequestTripConversionPage.jsx").read_text(encoding="utf-8")
    require("booking-workspaces/from-readiness" not in trip_page + offer_builder_page, "Trip or Offer Builder UI still bypasses booking handoff.")
    require("/offer-workspace" not in request_page, "Request UI still bypasses the canonical request-to-trip conversion.")
    require("if (!state)" in request_page, "Request Detail does not guard asynchronous state before rendering operational records.")
    require('label="Request id"' not in conversion_page and "Canonical request" in conversion_page, "Request conversion still exposes its canonical source as a raw ID field.")
    require("WorkflowContinuityPanel" in conversion_page and "Continue to trip" in conversion_page, "Request conversion lacks contextual Trip continuation.")
    handoff_page = (ROOT / "frontend/src/pages/agency/BookingHandoffsPage.jsx").read_text(encoding="utf-8")
    require("Canonical source required" in handoff_page and "Return to an accepted offer" in handoff_page, "Booking Handoff does not guard its accepted-offer source.")
    require("Acceptance id" not in handoff_page and "Booking readiness package id" not in handoff_page, "Booking Handoff still exposes canonical source IDs for manual entry.")
    passenger_services_page = (ROOT / "frontend/src/pages/agency/PassengerServicesPage.jsx").read_text(encoding="utf-8")
    require("/link-options" in passenger_services_page and "CanonicalSelector" in passenger_services_page, "Passenger Services does not use canonical fulfilment selectors.")
    require("persistLinks(true)" in passenger_services_page, "Passenger Services does not persist canonical context before continuing to Documents.")
    document_page = (ROOT / "frontend/src/pages/agency/DocumentWorkspacesPage.jsx").read_text(encoding="utf-8")
    require("Create document requirement" in document_page and "/document-requirement" in document_page, "Documents lacks the canonical passenger-service requirement action.")
    special_services_router = (ROOT / "backend/routers/agency_special_services.py").read_text(encoding="utf-8")
    require('passenger-services/{service_id}/document-requirement' in special_services_router, "Passenger-service document bridge route is missing.")
    finance_router = (ROOT / "backend/routers/finance.py").read_text(encoding="utf-8")
    require('booking-workspaces/{booking_workspace_id}/invoice' in finance_router, "Canonical Booking-to-Finance bridge is missing.")
    continuity_component = ROOT / "frontend/src/components/WorkflowContinuityPanel.jsx"
    require(continuity_component.exists(), "Shared workflow continuity panel is missing.")
    continuity_pages = [
        "ClientDetailPage.jsx", "PassengerDetailPage.jsx", "RequestDetailPage.jsx", "RequestTripConversionPage.jsx", "TripDetailPage.jsx",
        "OfferBuilderPage.jsx", "OfferWorkspaceDetailPage.jsx", "BookingHandoffsPage.jsx",
        "BookingWorkspaceDetailPage.jsx", "TicketDetailPage.jsx", "EmdDetailPage.jsx", "PassengerServicesPage.jsx",
        "DocumentWorkspacesPage.jsx", "InvoiceDetailPage.jsx", "AfterSalesPage.jsx",
    ]
    for page_name in continuity_pages:
        page_text = (ROOT / "frontend/src/pages/agency" / page_name).read_text(encoding="utf-8")
        require("WorkflowContinuityPanel" in page_text, f"{page_name} lacks canonical workflow continuity controls.")
    emd_page = (ROOT / "frontend/src/pages/agency/EmdDetailPage.jsx").read_text(encoding="utf-8")
    require("emd_record_id" in emd_page and "/agency/passenger-services" in emd_page, "EMD detail lacks canonical Passenger Services continuation.")
    after_sales_page = (ROOT / "frontend/src/pages/agency/AfterSalesPage.jsx").read_text(encoding="utf-8")
    for manual_label in [
        "Trip workspace id", "Booking workspace id", "Ticket workspace id", "EMD workspace id",
        "Passenger workspace id", "Invoice line item id", "Ticket record id", "EMD record id",
        "Accepted snapshot id", "Booking reference",
    ]:
        require(manual_label not in after_sales_page, f"After Sales still exposes manual canonical entry: {manual_label}.")
    for selector_label in [
        'label="Booking"', 'label="Passenger service"', 'label="Accepted offer"',
        'label="Invoice line"', 'label="Ticket"', 'label="EMD"',
    ]:
        require(selector_label in after_sales_page, f"After Sales selector is missing: {selector_label}.")
    for source_page in ["TicketDetailPage.jsx", "EmdDetailPage.jsx", "PassengerServicesPage.jsx", "InvoiceDetailPage.jsx", "BookingWorkspaceDetailPage.jsx"]:
        source_text = (ROOT / "frontend/src/pages/agency" / source_page).read_text(encoding="utf-8")
        require("/agency/after-sales?" in source_text, f"{source_page} has no canonical After Sales entry point.")
    require((ROOT / "docs/master-review/V1_CANONICAL_OPERATING_SEQUENCE.md").exists(), "Canonical operating sequence is missing.")
    require((ROOT / "docs/master-review/V1_TRANSITION_OWNERSHIP_CONTRACT.md").exists(), "Transition ownership contract is missing.")


if __name__ == "__main__":
    verify_static_contracts()
    asyncio.run(run_golden_path())
