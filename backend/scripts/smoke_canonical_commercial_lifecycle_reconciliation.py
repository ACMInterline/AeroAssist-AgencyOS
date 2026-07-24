#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

os.environ["APP_ENV"] = "development"
os.environ["AEROASSIST_DB_MODE"] = "memory"
os.environ["DEMO_AUTH_ENABLED"] = "false"
os.environ["SEED_ON_STARTUP"] = "false"
os.environ["SEED_ENDPOINT_ENABLED"] = "false"
os.environ["LOG_LEVEL"] = "CRITICAL"

from fastapi import HTTPException

from build_phase import CURRENT_BUILD_PHASE
from canonical_domain_ownership import DOMAIN_OWNERSHIP_BY_KEY
from database import Database
from models import (
    BookingCreateFromReadinessRequest,
    BookingRecordUpdate,
    BookingSourceContext,
    EmdCreateFromBookingServiceRequest,
    ManualBookingWorkspaceCreate,
    ManualEmdCreate,
    ManualTicketCreate,
    OfferAcceptanceCreate,
    OfferBookingHandoffBuildRequest,
    OfferBuilderSegmentCreate,
    OfferDeclineCreate,
    OfferFareBundleCreate,
    OfferOptionCreate,
    OfferOptionUpdate,
    OfferPricingLineCreate,
    OfferWorkspaceCreate,
    OfferWorkspaceTransitionRequest,
    OfferWorkspaceUpdate,
    TicketCreateFromBookingRequest,
    TripDossierCreate,
)
from persistence_query import CollectionOwnershipType, get_collection_ownership
from phase_assertions import assert_application_phase_at_least
from services.authorization_service import (
    project_authorized_commercial_fields,
    require_permission,
)
from services.booking_workspace_service import (
    BookingWorkspaceError,
    BookingWorkspaceService,
)
from services.canonical_commercial_lifecycle_service import (
    CANONICAL_COMMERCIAL_LIFECYCLE,
    LIFECYCLE_WRITER_CLASSIFICATION,
    CommercialLifecycleError,
    analyze_commercial_lifecycle,
    canonical_json_hash,
    validate_lifecycle_transition,
)
from services.offer_acceptance_service import OfferAcceptanceService
from services.offer_builder_service import OfferBuilderService
from services.offer_to_booking_handoff_service import (
    OfferToBookingHandoffError,
    OfferToBookingHandoffService,
)
from services.ticket_emd_service import TicketEmdError, TicketEmdService
from services.trip_dossier_service import (
    confirm_trip_from_accepted_snapshot,
    create_manual_trip,
    create_trip_from_request,
)


MINIMUM_PHASE = "phase_59_0_product_experience_recovery"
AGENCY_A = "canonical-commercial-agency-a"
AGENCY_B = "canonical-commercial-agency-b"
ACTOR = {"id": "canonical-commercial-owner", "identity_id": "identity-owner"}
CHECKS: list[str] = []


def check(name: str, condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(f"{name}: {message}")
    CHECKS.append(name)


async def expect_error(
    name: str,
    awaitable,
    error_type: type[BaseException],
    *,
    code: str | None = None,
) -> BaseException:
    try:
        await awaitable
    except error_type as exc:
        if code is not None and getattr(exc, "code", None) != code:
            raise AssertionError(
                f"{name}: expected error code {code}, got {getattr(exc, 'code', None)}"
            ) from exc
        CHECKS.append(name)
        return exc
    raise AssertionError(f"{name}: expected {error_type.__name__}")


def source(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


async def seed(db: Database) -> None:
    for agency_id in (AGENCY_A, AGENCY_B):
        await db.collection("agencies").insert_one(
            {
                "id": agency_id,
                "name": agency_id,
                "slug": agency_id,
                "status": "active",
            }
        )
    await db.collection("global_reference_records").insert_one(
        {
            "id": "currency-eur",
            "domain": "currencies",
            "code": "EUR",
            "key": "EUR",
            "label": "Euro",
            "scope": "global",
            "is_active": True,
            "sort_order": 1,
        }
    )


async def create_request(
    db: Database,
    request_id: str,
    *,
    agency_id: str = AGENCY_A,
) -> dict:
    request = await db.collection("travel_requests").insert_one(
        {
            "id": request_id,
            "agency_id": agency_id,
            "workspace_id": f"{agency_id}-workspace",
            "request_reference": request_id.upper(),
            "title": f"Request {request_id}",
            "status": "qualified",
            "request_version": 4,
            "client_id": f"{agency_id}-client",
            "trip_type": "one_way",
            "passenger_count": 1,
            "route_summary": "SOF-LHR",
            "source": "staff_created",
        }
    )
    await db.collection("request_passengers").insert_one(
        {
            "id": f"{request_id}-passenger",
            "agency_id": agency_id,
            "request_id": request_id,
            "request_passenger_key": "pax-1",
            "passenger_profile_id": f"{agency_id}-passenger",
            "display_name": "Canonical Traveler",
            "first_name": "Canonical",
            "last_name": "Traveler",
            "passenger_type": "adult",
            "status": "active",
        }
    )
    await db.collection("request_segments").insert_one(
        {
            "id": f"{request_id}-segment",
            "agency_id": agency_id,
            "request_id": request_id,
            "segment_key": "seg-1",
            "sequence": 1,
            "origin_airport_code": "SOF",
            "destination_airport_code": "LHR",
            "departure_date": "2030-07-15",
            "status": "active",
        }
    )
    await db.collection("requested_services").insert_one(
        {
            "id": f"{request_id}-service",
            "agency_id": agency_id,
            "request_id": request_id,
            "service_code": "WCHR",
            "service_key": "WCHR",
            "service_name": "Wheelchair assistance",
            "status": "active",
        }
    )
    return request


async def build_offer(
    db: Database,
    request_id: str,
    *,
    title: str,
    expires_at: datetime | None = None,
) -> tuple[dict, dict]:
    builder = OfferBuilderService(db)
    workspace = await builder.create_workspace(
        AGENCY_A,
        OfferWorkspaceCreate(
            request_id=request_id,
            title=title,
            currency="EUR",
            currency_reference_id="currency-eur",
            expires_at=expires_at,
        ),
        ACTOR["id"],
    )
    option = await builder.create_option(
        AGENCY_A,
        workspace["id"],
        OfferOptionCreate(
            label=f"{title} option",
            option_order=1,
            main_airline_code="BA",
            provider_name="manual",
            pricing_summary_json={"currency": "EUR", "total_amount": 9999},
            service_feasibility_json={"WCHR": {"status": "conditional"}},
            rules_summary_json={"evidence_status": "manual_review"},
        ),
        ACTOR["id"],
    )
    await builder.add_segment(
        AGENCY_A,
        option["id"],
        OfferBuilderSegmentCreate(
            sequence=1,
            marketing_airline_code="BA",
            operating_airline_code="BA",
            flight_number="893",
            origin_airport="SOF",
            destination_airport="LHR",
            departure_at=datetime(2030, 7, 15, 9, 0, tzinfo=timezone.utc),
            arrival_at=datetime(2030, 7, 15, 11, 30, tzinfo=timezone.utc),
            cabin_class="economy",
            booking_class="Y",
            fare_basis="YFLEX",
        ),
        ACTOR["id"],
    )
    await builder.add_fare_bundle(
        AGENCY_A,
        option["id"],
        OfferFareBundleCreate(
            fare_family_name="Economy Flex",
            cabin_class="economy",
            booking_class="Y",
            included_baggage_json={"checked_pieces": 1},
        ),
        ACTOR["id"],
    )
    await builder.add_pricing_line(
        AGENCY_A,
        option["id"],
        OfferPricingLineCreate(
            line_type="base_fare",
            label="Fare",
            amount=200,
            currency="EUR",
        ),
        ACTOR["id"],
    )
    await builder.add_pricing_line(
        AGENCY_A,
        option["id"],
        OfferPricingLineCreate(
            line_type="tax",
            label="Taxes",
            amount=50,
            currency="EUR",
        ),
        ACTOR["id"],
    )
    await builder.recalculate_option_pricing(
        AGENCY_A, option["id"], ACTOR["id"]
    )
    workspace = await builder.get_workspace_or_none(AGENCY_A, workspace["id"])
    workspace = await builder.deliver_workspace(
        AGENCY_A,
        workspace["id"],
        OfferWorkspaceTransitionRequest(
            expected_version=workspace["version"],
            reason=f"Deliver {title} for lifecycle smoke.",
        ),
        ACTOR["id"],
    )
    option = await builder.get_option_or_none(AGENCY_A, option["id"])
    return workspace, option


async def accept(
    db: Database,
    workspace: dict,
    option: dict,
    *,
    key: str,
) -> dict:
    return await OfferAcceptanceService(db).accept_offer_option(
        AGENCY_A,
        workspace["id"],
        option["id"],
        ACTOR,
        OfferAcceptanceCreate(
            acceptance_source="internal",
            offer_version=workspace["version"],
            option_version=option["version"],
            idempotency_key=key,
            channel="agency_staff",
            acceptance_terms_version="commercial-lifecycle-v1",
            consent_evidence_json={"operator_confirmed": True},
            provider_target="manual",
        ),
    )


async def verify_offer_contract(db: Database) -> tuple[dict, dict]:
    builder = OfferBuilderService(db)
    request = await create_request(db, "request-offer")
    workspace = await builder.create_workspace(
        AGENCY_A,
        OfferWorkspaceCreate(
            request_id=request["id"],
            title="Canonical offer",
            currency="EUR",
            currency_reference_id="currency-eur",
        ),
        ACTOR["id"],
    )
    check(
        "01_offer_workspace_canonical_owner",
        workspace["request_id"] == request["id"]
        and DOMAIN_OWNERSHIP_BY_KEY["offer"]["canonical_model"]
        == "OfferWorkspace",
        "OfferWorkspace is not the request-owned canonical Offer.",
    )
    option = await builder.create_option(
        AGENCY_A,
        workspace["id"],
        OfferOptionCreate(
            label="Canonical option",
            option_order=2,
            pricing_summary_json={"total_amount": 12345, "currency": "EUR"},
        ),
        ACTOR["id"],
    )
    cross_agency = await builder.create_option(
        AGENCY_B,
        workspace["id"],
        OfferOptionCreate(label="Cross-agency option", option_order=3),
        ACTOR["id"],
    )
    check(
        "02_option_same_agency_parent",
        cross_agency is None
        and option["offer_workspace_id"] == workspace["id"]
        and option["agency_id"] == workspace["agency_id"],
        "OfferOption escaped its same-Agency parent.",
    )
    await expect_error(
        "03_option_order_unique",
        builder.create_option(
            AGENCY_A,
            workspace["id"],
            OfferOptionCreate(label="Duplicate order", option_order=2),
            ACTOR["id"],
        ),
        CommercialLifecycleError,
        code="DUPLICATE_OFFER_OPTION_ORDER",
    )
    first = await builder.create_option(
        AGENCY_A,
        workspace["id"],
        OfferOptionCreate(label="First option", option_order=1),
        ACTOR["id"],
    )
    detail = await builder.workspace_detail(AGENCY_A, workspace["id"])
    check(
        "04_option_order_stable",
        [item["option_order"] for item in detail["options"]] == [1, 2],
        "Offer options are not rendered in stable option_order.",
    )
    check(
        "05_client_total_not_authoritative",
        not option.get("pricing_summary_json")
        and (option.get("source_payload_json") or {}).get(
            "authoritative_pricing"
        )
        is False,
        "Client-submitted Offer total became authoritative.",
    )
    await builder.add_pricing_line(
        AGENCY_A,
        option["id"],
        OfferPricingLineCreate(
            line_type="base_fare", label="Fare", amount=175, currency="EUR"
        ),
        ACTOR["id"],
    )
    pricing = await builder.recalculate_option_pricing(
        AGENCY_A, option["id"], ACTOR["id"]
    )
    check(
        "06_server_derived_total",
        pricing["pricing_summary"]["total_amount"] == 175
        and pricing["option"]["total_snapshot_json"]["server_derived"] is True,
        "Server did not derive the Offer total from pricing lines.",
    )
    check(
        "07_legacy_offer_guard_registered",
        "ensure_legacy_offer_write_allowed" in source("backend/routers/offers.py")
        and "canonical OfferWorkspace truth" in source("backend/routers/offers.py"),
        "Legacy Offer writes are not guarded after canonical creation.",
    )
    check(
        "08_writer_classification_complete",
        {
            "canonical_writer",
            "governed_adapter",
            "snapshot_writer",
            "projection_writer",
            "compatibility_writer",
            "import_writer",
            "deprecated_writer",
            "decision_required",
            "demo_or_test_writer",
        }.issubset(LIFECYCLE_WRITER_CLASSIFICATION),
        "Lifecycle writer audit classifications are incomplete.",
    )
    # Keep the first option referenced so the stable-order check cannot be
    # optimized away by future test cleanup.
    check(
        "09_option_parent_identity",
        first["workspace_id"] == workspace["id"],
        "Offer option lost its canonical parent.",
    )
    return workspace, option


async def verify_revision_and_decisions(db: Database) -> None:
    builder = OfferBuilderService(db)
    await create_request(db, "request-revision")
    workspace, option = await build_offer(
        db, "request-revision", title="Revision offer"
    )
    await expect_error(
        "10_delivered_option_frozen",
        builder.update_option(
            AGENCY_A,
            option["id"],
            OfferOptionUpdate(
                label="Silently rewritten option",
                expected_version=option["version"],
            ),
            ACTOR["id"],
        ),
        CommercialLifecycleError,
        code="OFFER_EVIDENCE_FROZEN",
    )
    await expect_error(
        "11_material_edit_requires_revision_reason",
        builder.update_workspace(
            AGENCY_A,
            workspace["id"],
            OfferWorkspaceUpdate(
                title="Silently rewritten Offer",
                expected_version=workspace["version"],
            ),
            ACTOR["id"],
        ),
        CommercialLifecycleError,
        code="OFFER_REVISION_REQUIRED",
    )
    revision = await builder.update_workspace(
        AGENCY_A,
        workspace["id"],
        OfferWorkspaceUpdate(
            title="Governed Offer revision",
            expected_version=workspace["version"],
            revision_reason="Client requested a different travel date.",
        ),
        ACTOR["id"],
    )
    superseded = await builder.get_workspace_or_none(AGENCY_A, workspace["id"])
    check(
        "12_material_edit_creates_revision",
        revision["id"] != workspace["id"]
        and revision["previous_version_id"] == workspace["id"]
        and revision["version"] == workspace["version"] + 1,
        "Material edit did not create a governed Offer revision.",
    )
    check(
        "13_superseded_offer_readable",
        superseded["status"] == "superseded"
        and superseded["superseded_by_offer_id"] == revision["id"],
        "Superseded Offer evidence is not preserved and readable.",
    )
    await expect_error(
        "14_superseded_acceptance_rejected",
        OfferAcceptanceService(db).accept_offer_option(
            AGENCY_A,
            workspace["id"],
            option["id"],
            ACTOR,
            OfferAcceptanceCreate(
                offer_version=workspace["version"],
                option_version=option["version"],
            ),
        ),
        CommercialLifecycleError,
        code="OFFER_SUPERSEDED",
    )

    await create_request(db, "request-expired")
    expired_workspace, expired_option = await build_offer(
        db,
        "request-expired",
        title="Expired offer",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    await expect_error(
        "15_expired_acceptance_rejected",
        accept(
            db,
            expired_workspace,
            expired_option,
            key="expired-offer-decision",
        ),
        CommercialLifecycleError,
        code="OFFER_EXPIRED",
    )

    await create_request(db, "request-declined")
    declined_workspace, declined_option = await build_offer(
        db, "request-declined", title="Declined offer"
    )
    trips_before = await db.collection("trip_dossiers").count()
    declined = await OfferAcceptanceService(db).decline_offer_option(
        AGENCY_A,
        declined_workspace["id"],
        declined_option["id"],
        ACTOR,
        OfferDeclineCreate(
            offer_version=declined_workspace["version"],
            option_version=declined_option["version"],
            idempotency_key="decline-exact-version",
            reason="Client selected no option.",
        ),
    )
    check(
        "16_decline_creates_no_trip",
        declined["acceptance"]["status"] == "declined"
        and declined["trip_snapshot"] is None
        and await db.collection("trip_dossiers").count() == trips_before,
        "Decline created downstream Trip truth.",
    )


async def verify_acceptance_and_trip(db: Database) -> dict:
    await create_request(db, "request-accepted")
    workspace, option = await build_offer(
        db, "request-accepted", title="Accepted offer"
    )
    acceptance_service = OfferAcceptanceService(db)
    await expect_error(
        "17_stale_offer_version_rejected",
        acceptance_service.accept_offer_option(
            AGENCY_A,
            workspace["id"],
            option["id"],
            ACTOR,
            OfferAcceptanceCreate(
                offer_version=workspace["version"] - 1,
                option_version=option["version"],
            ),
        ),
        CommercialLifecycleError,
        code="STALE_OFFER_VERSION",
    )
    await expect_error(
        "18_stale_option_version_rejected",
        acceptance_service.accept_offer_option(
            AGENCY_A,
            workspace["id"],
            option["id"],
            ACTOR,
            OfferAcceptanceCreate(
                offer_version=workspace["version"],
                option_version=option["version"] - 1,
            ),
        ),
        CommercialLifecycleError,
        code="STALE_OFFER_OPTION_VERSION",
    )
    accepted = await accept(
        db, workspace, option, key="accepted-exact-version"
    )
    acceptance = accepted["acceptance"]
    snapshot = accepted["trip_snapshot"]
    check(
        "19_acceptance_exact_version",
        acceptance["offer_version"] == workspace["version"]
        and acceptance["option_version"] == option["version"]
        and acceptance["status"] == "accepted",
        "Acceptance did not preserve exact Offer and Option versions.",
    )
    retry = await accept(
        db, workspace, option, key="accepted-exact-version"
    )
    check(
        "20_acceptance_idempotent",
        retry["idempotent_reused"] is True
        and retry["acceptance"]["id"] == acceptance["id"],
        "Acceptance retry created a duplicate decision.",
    )
    check(
        "21_snapshot_created_once",
        await db.collection("trip_accepted_offer_snapshots").count(
            {"agency_id": AGENCY_A, "acceptance_id": acceptance["id"]}
        )
        == 1,
        "Acceptance created more than one immutable snapshot.",
    )
    frozen_snapshot = deepcopy(snapshot)
    await db.collection("global_reference_records").update_one(
        {"id": "currency-eur"}, {"label": "Euro renamed"}
    )
    snapshot_after_label_change = await db.collection(
        "trip_accepted_offer_snapshots"
    ).find_one({"agency_id": AGENCY_A, "id": snapshot["id"]})
    check(
        "22_reference_change_does_not_mutate_snapshot",
        snapshot_after_label_change == frozen_snapshot,
        "Reference-label edit altered immutable accepted evidence.",
    )
    check(
        "23_snapshot_persistence_immutable",
        get_collection_ownership(
            "trip_accepted_offer_snapshots"
        ).ownership
        == CollectionOwnershipType.IMMUTABLE_SNAPSHOT
        and "update_trip_accepted_offer_snapshot"
        not in source("backend/routers/agency_offer_acceptance.py"),
        "Accepted snapshot is not registered as create-only evidence.",
    )
    trip = await db.collection("trip_dossiers").find_one(
        {"agency_id": AGENCY_A, "id": acceptance["trip_id"]}
    )
    check(
        "24_normal_trip_requires_snapshot",
        trip["creation_mode"] == "accepted_offer"
        and trip["accepted_offer_snapshot_id"] == snapshot["id"],
        "Normal confirmed Trip was not created from accepted evidence.",
    )
    check(
        "25_trip_lineage_complete",
        trip["primary_request_id"] == workspace["request_id"]
        and trip["offer_workspace_id"] == workspace["id"]
        and trip["offer_option_id"] == option["id"]
        and trip["offer_acceptance_id"] == acceptance["id"]
        and trip["accepted_offer_snapshot_id"] == snapshot["id"],
        "Trip lineage is incomplete.",
    )
    repeated_trip = await confirm_trip_from_accepted_snapshot(
        db, AGENCY_A, snapshot, acceptance, ACTOR["id"]
    )
    check(
        "26_one_snapshot_one_trip",
        repeated_trip["id"] == trip["id"]
        and await db.collection("trip_dossiers").count(
            {
                "agency_id": AGENCY_A,
                "accepted_offer_snapshot_id": snapshot["id"],
            }
        )
        == 1,
        "Snapshot retry created a duplicate Trip.",
    )
    await expect_error(
        "27_cross_agency_snapshot_rejected",
        confirm_trip_from_accepted_snapshot(
            db, AGENCY_B, snapshot, acceptance, ACTOR["id"]
        ),
        CommercialLifecycleError,
        code="CROSS_AGENCY_LINEAGE",
    )
    check(
        "28_acceptance_payload_hash_matches_snapshot",
        snapshot["source_hash"] == acceptance["accepted_payload_hash"]
        and len(snapshot["source_hash"]) == 64,
        "Accepted snapshot integrity hash does not match the decision.",
    )
    return accepted


async def verify_trip_modes(db: Database) -> None:
    await create_request(db, "request-planning")
    planning = await create_trip_from_request(
        db, AGENCY_A, "request-planning", ACTOR["id"]
    )
    check(
        "29_request_conversion_planning_only",
        planning["trip_status"] == "planning"
        and planning["creation_mode"] == "request_planning_projection"
        and not planning.get("accepted_offer_snapshot_id"),
        "Pre-acceptance Request conversion created confirmed Trip truth.",
    )
    await expect_error(
        "30_manual_confirmed_requires_mode",
        create_manual_trip(
            db,
            AGENCY_A,
            TripDossierCreate(
                trip_title="Ungoverned confirmed Trip",
                trip_status="confirmed",
            ),
            ACTOR["id"],
        ),
        CommercialLifecycleError,
        code="TRIP_CREATION_MODE_REQUIRED",
    )
    await expect_error(
        "31_manual_confirmed_requires_evidence",
        create_manual_trip(
            db,
            AGENCY_A,
            TripDossierCreate(
                trip_title="Missing manual evidence",
                trip_status="confirmed",
                creation_mode="manual_confirmed",
            ),
            ACTOR["id"],
        ),
        CommercialLifecycleError,
        code="TRIP_SOURCE_EVIDENCE_REQUIRED",
    )
    manual = await create_manual_trip(
        db,
        AGENCY_A,
        TripDossierCreate(
            trip_title="Governed manual Trip",
            trip_status="confirmed",
            creation_mode="manual_confirmed",
            source_reference="manual-case-001",
            reason="Existing offline operational file reviewed by owner.",
        ),
        ACTOR["id"],
    )
    check(
        "32_manual_trip_governed",
        manual["reconciliation_status"] == "governed_exception"
        and manual["confirmed_by_user_id"] == ACTOR["id"],
        "Governed manual Trip did not retain actor and evidence.",
    )
    imported = await create_manual_trip(
        db,
        AGENCY_A,
        TripDossierCreate(
            trip_title="Imported booking Trip",
            trip_status="confirmed",
            creation_mode="imported_booking",
            source_reference="PNR-IMPORT-001",
            reason="Reviewed external PNR import.",
        ),
        ACTOR["id"],
    )
    check(
        "33_imported_trip_source_evidence",
        imported["source_reference"] == "PNR-IMPORT-001"
        and imported["creation_reason"],
        "Imported Trip did not preserve source evidence.",
    )


async def verify_handoff_booking_ticket_emd(
    db: Database, accepted: dict
) -> None:
    handoffs = OfferToBookingHandoffService(db)
    acceptance = accepted["acceptance"]
    readiness = accepted["booking_readiness"]
    snapshot = accepted["trip_snapshot"]
    declined = await db.collection("offer_acceptances").find_one(
        {"agency_id": AGENCY_A, "status": "declined"}
    )
    await expect_error(
        "34_handoff_requires_active_acceptance",
        handoffs.build_handoff(
            OfferBookingHandoffBuildRequest(
                agency_id=AGENCY_A,
                acceptance_id=declined["id"],
                booking_mode="manual",
            ),
            ACTOR,
            agency_id=AGENCY_A,
        ),
        OfferToBookingHandoffError,
    )
    payload = OfferBookingHandoffBuildRequest(
        agency_id=AGENCY_A,
        acceptance_id=acceptance["id"],
        booking_readiness_package_id=readiness["id"],
        booking_mode="manual",
        idempotency_key="canonical-commercial-handoff",
    )
    built = await handoffs.build_handoff(
        payload, ACTOR, agency_id=AGENCY_A
    )
    handoff = built["handoff"]
    check(
        "35_handoff_snapshot_backed",
        handoff["trip_accepted_offer_snapshot_id"] == snapshot["id"]
        and handoff["accepted_offer_snapshot_json"],
        "Booking handoff is not backed by immutable accepted evidence.",
    )
    retried = await handoffs.build_handoff(
        payload, ACTOR, agency_id=AGENCY_A
    )
    check(
        "36_handoff_idempotent",
        retried["idempotent_reused"] is True
        and retried["handoff"]["id"] == handoff["id"],
        "Booking handoff retry created duplicate state.",
    )
    created = await handoffs.create_booking_workspace(
        handoff["id"],
        {
            "provider_target": "manual",
            "booking_mode": "manual",
            "allow_conditional": True,
            "create_draft_record": True,
        },
        ACTOR,
        agency_id=AGENCY_A,
    )
    workspace = created["booking_workspace"]
    detail = created["booking_result"]
    record = detail["booking_record"]
    booking_service = BookingWorkspaceService(db)
    if workspace["status"] == "draft":
        moved = await booking_service.update_booking_workspace_status(
            AGENCY_A,
            workspace["id"],
            "ready_to_book",
            ACTOR,
            "Readiness reviewed.",
        )
        workspace = moved["booking_workspace"]
    moved = await booking_service.update_booking_workspace_status(
        AGENCY_A,
        workspace["id"],
        "booking_in_progress",
        ACTOR,
        "Manual booking result entry started.",
    )
    workspace = moved["booking_workspace"]
    await expect_error(
        "37_workspace_cannot_claim_booked_alone",
        booking_service.update_booking_workspace_status(
            AGENCY_A,
            workspace["id"],
            "booked",
            ACTOR,
            "No external result exists.",
        ),
        BookingWorkspaceError,
    )
    await expect_error(
        "38_booking_result_requires_reason",
        booking_service.update_booking_record(
            AGENCY_A,
            record["id"],
            BookingRecordUpdate(
                pnr_locator="CAN123",
                provider_status="confirmed",
                booking_status="confirmed",
                expected_version=record["current_external_result_version"],
            ),
            ACTOR,
        ),
        BookingWorkspaceError,
    )
    confirmed = await booking_service.update_booking_record(
        AGENCY_A,
        record["id"],
        BookingRecordUpdate(
            pnr_locator="CAN123",
            provider_status="confirmed",
            booking_status="confirmed",
            source_evidence_reference="manual-confirmation:CAN123",
            source_evidence_json={
                "reviewed_by": ACTOR["id"],
                "provider_execution_disabled": True,
            },
            expected_version=record["current_external_result_version"],
            reason="Operator reviewed the external PNR confirmation.",
        ),
        ACTOR,
    )
    confirmed_record = confirmed["booking_record"]
    check(
        "39_booking_record_owns_external_result",
        confirmed["booking_workspace"]["status"] == "booked"
        and confirmed_record["booking_status"] == "confirmed"
        and confirmed_record["pnr_locator"] == "CAN123",
        "BookingWorkspace and BookingRecord result ownership remains blurred.",
    )
    check(
        "40_manual_booking_result_evidenced",
        confirmed_record["updated_by_user_id"] == ACTOR["id"]
        and confirmed_record["source_evidence_reference"]
        == "manual-confirmation:CAN123"
        and confirmed_record["result_hash"],
        "Manual BookingRecord lacks actor, source, or result hash.",
    )

    imported = await booking_service.create_manual_booking_workspace(
        AGENCY_A,
        ManualBookingWorkspaceCreate(
            title="Imported booking",
            source_context=BookingSourceContext.IMPORTED_GDS,
            source_reference="import-draft-001",
            reason="Reviewed GDS import.",
            create_draft_record=True,
            segments_json=confirmed_record["segments_json"],
            passengers_json=confirmed_record["passengers_json"],
        ),
        ACTOR,
    )
    imported_workspace = imported["booking_workspace"]
    imported_record = imported["booking_record"]
    await expect_error(
        "41_ticket_requires_confirmed_booking",
        TicketEmdService(db).create_ticket_from_booking_record(
            AGENCY_A,
            TicketCreateFromBookingRequest(
                booking_record_id=imported_record["id"]
            ),
            ACTOR,
        ),
        TicketEmdError,
    )
    await expect_error(
        "42_emd_requires_confirmed_booking",
        TicketEmdService(db).create_emd_from_booking_service(
            AGENCY_A,
            EmdCreateFromBookingServiceRequest(
                booking_record_id=imported_record["id"],
                service_key="WCHR",
            ),
            ACTOR,
        ),
        TicketEmdError,
    )
    imported = await booking_service.update_booking_workspace_status(
        AGENCY_A,
        imported_workspace["id"],
        "ready_to_book",
        ACTOR,
        "Import reviewed.",
    )
    imported = await booking_service.update_booking_workspace_status(
        AGENCY_A,
        imported_workspace["id"],
        "booking_in_progress",
        ACTOR,
        "Import result entry started.",
    )
    imported = await booking_service.update_booking_record(
        AGENCY_A,
        imported_record["id"],
        BookingRecordUpdate(
            pnr_locator="IMP456",
            provider_status="confirmed",
            booking_status="confirmed",
            source_evidence_reference="import-draft-001",
            source_evidence_json={"import_reviewed": True},
            expected_version=imported_record["current_external_result_version"],
            reason="Imported PNR reviewed against source.",
        ),
        ACTOR,
    )
    check(
        "43_imported_pnr_reconciliation_state",
        imported["booking_record"]["source_context"] == "imported_gds"
        and imported["booking_record"]["reconciliation_status"]
        == "import_pending_review",
        "Imported PNR did not preserve reconciliation state.",
    )

    duplicate = await booking_service.create_manual_booking_workspace(
        AGENCY_A,
        ManualBookingWorkspaceCreate(
            title="Duplicate locator attempt",
            source_context=BookingSourceContext.STANDALONE_MANUAL,
            source_reference="manual-attempt-duplicate",
            reason="Duplicate locator regression.",
            create_draft_record=True,
        ),
        ACTOR,
    )
    duplicate_workspace = duplicate["booking_workspace"]
    duplicate_record = duplicate["booking_record"]
    await booking_service.update_booking_workspace_status(
        AGENCY_A,
        duplicate_workspace["id"],
        "ready_to_book",
        ACTOR,
        "Prepared.",
    )
    await booking_service.update_booking_workspace_status(
        AGENCY_A,
        duplicate_workspace["id"],
        "booking_in_progress",
        ACTOR,
        "Manual entry.",
    )
    await expect_error(
        "44_duplicate_active_booking_result_rejected",
        booking_service.update_booking_record(
            AGENCY_A,
            duplicate_record["id"],
            BookingRecordUpdate(
                pnr_locator="CAN123",
                provider_status="confirmed",
                booking_status="confirmed",
                source_evidence_reference="manual-attempt-duplicate",
                source_evidence_json={"manual_confirmation": True},
                expected_version=duplicate_record[
                    "current_external_result_version"
                ],
                reason="Attempt duplicate locator.",
            ),
            ACTOR,
        ),
        BookingWorkspaceError,
    )

    ticket_service = TicketEmdService(db)
    ticket_payload = TicketCreateFromBookingRequest(
        booking_record_id=confirmed_record["id"], create_coupons=True
    )
    ticket = await ticket_service.create_ticket_from_booking_record(
        AGENCY_A, ticket_payload, ACTOR
    )
    ticket_retry = await ticket_service.create_ticket_from_booking_record(
        AGENCY_A, ticket_payload, ACTOR
    )
    check(
        "45_ticket_lineage_and_idempotency",
        ticket["ticket"]["booking_record_id"] == confirmed_record["id"]
        and ticket_retry["ticket"]["id"] == ticket["ticket"]["id"],
        "Normal Ticket lineage retry duplicated or lost BookingRecord.",
    )
    emd_payload = EmdCreateFromBookingServiceRequest(
        booking_record_id=confirmed_record["id"],
        service_key="WCHR",
        ticket_record_id=ticket["ticket"]["id"],
        create_coupons=True,
    )
    emd = await ticket_service.create_emd_from_booking_service(
        AGENCY_A, emd_payload, ACTOR
    )
    emd_retry = await ticket_service.create_emd_from_booking_service(
        AGENCY_A, emd_payload, ACTOR
    )
    check(
        "46_emd_lineage_and_idempotency",
        emd["emd"]["booking_record_id"] == confirmed_record["id"]
        and emd_retry["emd"]["id"] == emd["emd"]["id"],
        "Normal EMD lineage retry duplicated or lost BookingRecord.",
    )
    await expect_error(
        "47_standalone_ticket_requires_exception_metadata",
        ticket_service.create_manual_ticket(
            AGENCY_A, ManualTicketCreate(), ACTOR
        ),
        TicketEmdError,
    )
    standalone_ticket = await ticket_service.create_manual_ticket(
        AGENCY_A,
        ManualTicketCreate(
            source_context="imported_confirmation",
            source_reference="historical-ticket-file-001",
            exception_reason="Historical ticket imported for servicing.",
            ticket_number="2200000000001",
        ),
        ACTOR,
    )
    check(
        "48_standalone_ticket_governed",
        standalone_ticket["ticket"]["standalone_source_reference"]
        == "historical-ticket-file-001",
        "Governed standalone Ticket source was not retained.",
    )
    await expect_error(
        "49_standalone_emd_requires_exception_metadata",
        ticket_service.create_manual_emd(
            AGENCY_A, ManualEmdCreate(), ACTOR
        ),
        TicketEmdError,
    )
    standalone_emd = await ticket_service.create_manual_emd(
        AGENCY_A,
        ManualEmdCreate(
            source_context="imported_confirmation",
            source_reference="historical-emd-file-001",
            exception_reason="Historical EMD imported for servicing.",
            emd_number="2200000000012",
            service_key="WCHR",
        ),
        ACTOR,
    )
    check(
        "50_standalone_emd_governed",
        standalone_emd["emd"]["standalone_source_reference"]
        == "historical-emd-file-001",
        "Governed standalone EMD source was not retained.",
    )
    cross_tenant = await ticket_service.create_ticket_from_booking_record(
        AGENCY_B, ticket_payload, ACTOR
    )
    check(
        "51_cross_agency_booking_lineage_rejected",
        cross_tenant is None
        and await db.collection("ticket_records").count(
            {"agency_id": AGENCY_B}
        )
        == 0,
        "Cross-Agency Ticket lineage was accepted.",
    )


async def verify_transitions_security_and_analysis(db: Database) -> None:
    try:
        validate_lifecycle_transition("offer", "draft", "accepted")
    except CommercialLifecycleError as exc:
        check(
            "52_invalid_transition_rejected",
            exc.code == "INVALID_LIFECYCLE_TRANSITION",
            "Invalid lifecycle transition returned the wrong conflict.",
        )
    else:
        raise AssertionError(
            "52_invalid_transition_rejected: invalid transition was accepted"
        )
    audit_events = await db.collection("audit_events").find_many(
        {"agency_id": AGENCY_A}
    )
    timeline_events = await db.collection("operational_timelines").find_many(
        {"agency_id": AGENCY_A}
    )
    check(
        "53_material_transitions_emit_audit",
        any(
            str(item.get("event_type") or "").startswith(
                ("offer.", "offer_acceptance.", "trip.", "booking_")
            )
            for item in audit_events
        ),
        "Material lifecycle transitions did not emit audit evidence.",
    )
    check(
        "54_material_transitions_emit_timeline",
        any(
            item.get("event_source") == "canonical_commercial_lifecycle"
            for item in timeline_events
        ),
        "Material lifecycle transitions did not emit operational timeline evidence.",
    )
    try:
        require_permission(
            {"_permissions": ["view_offers"]}, "edit_offers"
        )
    except HTTPException as exc:
        check(
            "55_readonly_cannot_transition",
            exc.status_code == 403,
            "Read-only principal did not receive canonical 403.",
        )
    else:
        raise AssertionError(
            "55_readonly_cannot_transition: read-only principal could mutate"
        )
    projected = project_authorized_commercial_fields(
        {
            "total_amount": 250,
            "supplier_cost": 150,
            "margin": 100,
            "pricing_lines": [
                {"line_type": "commission", "amount": 10},
                {"line_type": "tax", "amount": 40},
            ],
        },
        {"_permissions": ["view_offers"]},
    )
    check(
        "56_agent_commercial_projection_redacted",
        "supplier_cost" not in projected
        and "margin" not in projected
        and projected["pricing_lines"] == [
            {"line_type": "tax", "amount": 40}
        ],
        "Supplier cost or margin leaked to an unauthorized agent.",
    )
    portal_router = source("backend/routers/portal_offer_deliveries.py")
    portal_context_source = source("backend/routers/portal.py")
    delivery_service = source(
        "backend/services/offer_delivery_client_interaction_service.py"
    )
    check(
        "57_portal_client_subject_scoped",
        "Depends(portal_context)" in portal_router
        and "portal_user_id" in delivery_service
        and "access_status" in delivery_service,
        "Portal acceptance decisions are not recipient-bound.",
    )
    check(
        "58_passenger_portal_offer_mutation_blocked",
        'subject_type == "passenger"' in portal_context_source
        and "request.method != \"GET\"" in portal_context_source,
        "Passenger Portal can reach Client-wide Offer decisions.",
    )
    ownership = {
        key: DOMAIN_OWNERSHIP_BY_KEY[key]["canonical_model"]
        for key in (
            "offer",
            "offer_option",
            "offer_acceptance",
            "accepted_offer_snapshot",
            "trip",
            "booking_handoff",
            "booking_pnr",
            "ticket",
            "ticket_coupon",
            "emd",
            "emd_coupon",
        )
    }
    check(
        "59_ownership_registry_matches_contract",
        tuple(ownership.values()) == CANONICAL_COMMERCIAL_LIFECYCLE[1:],
        f"Canonical ownership registry drifted: {ownership}",
    )
    report = await analyze_commercial_lifecycle(
        db, maximum_records_per_collection=500
    )
    check(
        "60_migration_analysis_zero_writes",
        report["dry_run"] is True
        and report["write_mode_available"] is False
        and report["writes_performed"] == 0
        and report["counts_unchanged"] is True,
        "Commercial lifecycle migration analysis wrote data.",
    )
    analyzer_source = source(
        "backend/scripts/analyze_commercial_lifecycle_migration.py"
    )
    check(
        "61_migration_cli_has_no_apply_mode",
        "--apply" not in analyzer_source
        and "write_mode_available" not in analyzer_source,
        "Dry-run analyzer exposes a write path.",
    )
    inventory = json.loads(
        source("backend/scripts/smoke_inventory.json")
    )
    inventory_paths = {
        item["script_path"] for item in inventory.get("scripts") or []
    }
    required_regressions = {
        "backend/scripts/smoke_canonical_commercial_lifecycle_reconciliation.py",
        "backend/scripts/smoke_canonical_request_v4.py",
        "backend/scripts/smoke_canonical_reference_data_wiring.py",
        "backend/scripts/smoke_canonical_identity_tenancy_contract.py",
        "backend/scripts/smoke_request_passenger_identity_integrity.py",
        "backend/scripts/smoke_audit_event_isolation.py",
    }
    check(
        "62_inventory_and_required_regressions_registered",
        required_regressions.issubset(inventory_paths),
        "Focused lifecycle or required security regression is missing from inventory.",
    )
    check(
        "63_persistence_contract_registered",
        get_collection_ownership("offer_acceptances").ownership
        == CollectionOwnershipType.AGENCY_OWNED
        and get_collection_ownership(
            "trip_accepted_offer_snapshots"
        ).ownership
        == CollectionOwnershipType.IMMUTABLE_SNAPSHOT,
        "Acceptance lifecycle or immutable snapshot persistence is misclassified.",
    )
    check(
        "64_compatibility_routes_read_only_where_required",
        "read-only compatibility projections"
        in source("backend/routers/bookings.py")
        and "HTTP_409_CONFLICT" in source("backend/routers/bookings.py")
        and "legacy Offer is read-only" in source("backend/routers/portal.py")
        and "canonical OfferWorkspace" in source("backend/routers/portal.py"),
        "Legacy Booking or Portal writer remains independently mutable.",
    )
    check(
        "65_frontend_canonical_flow_registered",
        "/agency/booking-workspaces" in source("frontend/src/App.jsx")
        and "Accepted evidence is frozen" in source(
            "frontend/src/pages/agency/OfferWorkspaceDetailPage.jsx"
        )
        and "Booking result evidence" in source(
            "frontend/src/pages/agency/BookingWorkspaceDetailPage.jsx"
        ),
        "Agency UI does not present the canonical lifecycle.",
    )
    check(
        "66_readiness_contract_registered",
        "canonical_commercial_lifecycle_contract"
        in source("backend/server.py")
        and "provider_booking_execution_disabled"
        in source(
            "backend/services/canonical_commercial_lifecycle_service.py"
        ),
        "Readiness does not expose the non-executory canonical lifecycle contract.",
    )
    for path in (
        "docs/architecture/canonical-commercial-lifecycle-contract.md",
        "docs/architecture/offer-acceptance-and-snapshot-contract.md",
        "docs/architecture/trip-and-booking-ownership-contract.md",
        "docs/architecture/commercial-lifecycle-compatibility-and-migration.md",
    ):
        check(
            f"67_docs_{Path(path).stem}",
            (ROOT / path).is_file(),
            f"Missing lifecycle architecture document: {path}",
        )


async def main_async() -> None:
    assert_application_phase_at_least(
        CURRENT_BUILD_PHASE,
        MINIMUM_PHASE,
        source="build_phase.CURRENT_BUILD_PHASE",
    )
    db = Database()
    await seed(db)
    await verify_offer_contract(db)
    await verify_revision_and_decisions(db)
    accepted = await verify_acceptance_and_trip(db)
    await verify_trip_modes(db)
    await verify_handoff_booking_ticket_emd(db, accepted)
    await verify_transitions_security_and_analysis(db)
    check(
        "68_required_assertion_floor",
        len(CHECKS) >= 68,
        f"Expected at least 68 checks, ran {len(CHECKS)}.",
    )


def main() -> int:
    asyncio.run(main_async())
    print(
        "Canonical commercial lifecycle reconciliation smoke passed: "
        f"{len(CHECKS)} checks."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"Canonical commercial lifecycle reconciliation smoke failed: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
