#!/usr/bin/env python3
"""Run the disposable backend used by the full-system Playwright acceptance suite."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("AEROASSIST_DB_MODE", "memory")
os.environ.setdefault("DEMO_AUTH_ENABLED", "true")
os.environ.setdefault("SEED_ON_STARTUP", "true")
os.environ.setdefault("SEED_ENDPOINT_ENABLED", "false")

from database import database
from models import (
    Agency,
    AuthIdentity,
    DocumentWorkspace,
    DocumentWorkspaceStatus,
    DocumentWorkspaceType,
    OfferBuilderSegmentCreate,
    OfferFareBundleCreate,
    OfferOptionCreate,
    OfferPricingLineCreate,
    OfferWorkspace,
    PortalAccessMapping,
)
from security import hash_password, normalize_email
from server import app
from services.offer_builder_service import OfferBuilderService
from services.offer_delivery_client_interaction_service import (
    OfferDeliveryClientInteractionService,
)
from services.reference_data_service import bootstrap_reference_data
from services.seed_service import DEMO_AGENCY_SLUG, DEMO_PASSWORD


FIXTURE_OFFER_ID = "browser-acceptance-offer"
FIXTURE_PRESENTATION_ID = "browser-acceptance-presentation"
FIXTURE_SNAPSHOT_ID = "browser-acceptance-presentation-snapshot"
FIXTURE_COMPOSITION_ID = "browser-acceptance-composition"
FIXTURE_JOURNEY_ID = "browser-acceptance-journey"
OTHER_AGENCY_ID = "browser-acceptance-other-agency"
PASSENGER_PORTAL_EMAIL = "anna.passenger@example.com"
REVOKED_PORTAL_EMAIL = "revoked.client@example.com"
FIXTURE_DOCUMENT_ID = "browser-acceptance-requested-document"


async def insert_once(collection_name: str, document: dict) -> dict:
    collection = database.collection(collection_name)
    existing = await collection.find_one({"id": document["id"]})
    return existing or await collection.insert_one(document)


async def ensure_portal_mapping(
    *,
    email: str,
    identity_type: str,
    agency_id: str,
    subject_type: str,
    client_id: str | None,
    passenger_id: str | None,
    status: str,
) -> tuple[dict, dict]:
    normalized = normalize_email(email)
    identity = await database.collection("auth_identities").find_one(
        {"normalized_email": normalized}
    )
    if identity is None:
        identity = await database.collection("auth_identities").insert_one(
            AuthIdentity(
                email=email,
                normalized_email=normalized,
                password_hash=hash_password(DEMO_PASSWORD),
                identity_type=identity_type,
                status="active",
            ).model_dump(mode="json")
        )
    mapping = await database.collection("portal_access_mappings").find_one(
        {"agency_id": agency_id, "auth_identity_id": identity["id"]}
    )
    if mapping is None:
        mapping = await database.collection("portal_access_mappings").insert_one(
            PortalAccessMapping(
                agency_id=agency_id,
                auth_identity_id=identity["id"],
                subject_type=subject_type,
                client_profile_id=client_id,
                client_id=client_id,
                passenger_profile_id=passenger_id,
                user_email=email,
                identity_email_snapshot=email,
                display_name="Anna Novak" if status == "active" else "Revoked Client",
                status=status,
                portal_status=status,
                active_mapping_key=identity["id"] if status == "active" else None,
                active_subject_key=(
                    f"{subject_type}:{passenger_id or client_id}"
                    if status == "active"
                    else None
                ),
                linkage_version="explicit_identity_v1",
                created_by="browser_acceptance_fixture",
                updated_by="browser_acceptance_fixture",
            ).model_dump(mode="json")
        )
    return identity, mapping


async def seed_browser_acceptance_fixture() -> None:
    await bootstrap_reference_data(database, "browser_acceptance_fixture")
    agency = await database.collection("agencies").find_one(
        {"slug": DEMO_AGENCY_SLUG}
    )
    owner = await database.collection("platform_users").find_one(
        {"email": "agency.owner@aeroassist.dev"}
    )
    client = await database.collection("client_profiles").find_one(
        {"agency_id": agency["id"], "primary_email": "anna.client@example.com"}
    )
    passenger = await database.collection("passenger_profiles").find_one(
        {"agency_id": agency["id"], "display_name": "Anna Novak"}
    )
    request = (
        await database.collection("travel_requests").find_many(
            {"agency_id": agency["id"], "client_id": client["id"]},
            sort=[("created_at", -1)],
            limit=1,
        )
    )[0]
    client_mapping = await database.collection("portal_access_mappings").find_one(
        {
            "agency_id": agency["id"],
            "client_profile_id": client["id"],
            "subject_type": "client",
            "status": "active",
        }
    )
    if not all([agency, owner, client, passenger, request, client_mapping]):
        raise RuntimeError("Core demo seed did not provide the browser acceptance fixture.")

    await insert_once(
        "agencies",
        Agency(
            id=OTHER_AGENCY_ID,
            name="Browser Acceptance Other Agency",
            slug="browser-acceptance-other",
            legal_name="Browser Acceptance Other Agency Ltd",
            status="active",
        ).model_dump(mode="json"),
    )
    await ensure_portal_mapping(
        email=PASSENGER_PORTAL_EMAIL,
        identity_type="passenger_portal",
        agency_id=agency["id"],
        subject_type="passenger",
        client_id=None,
        passenger_id=passenger["id"],
        status="active",
    )
    await ensure_portal_mapping(
        email=REVOKED_PORTAL_EMAIL,
        identity_type="client_portal",
        agency_id=agency["id"],
        subject_type="client",
        client_id=client["id"],
        passenger_id=None,
        status="revoked",
    )
    await insert_once(
        "document_workspaces",
        DocumentWorkspace(
            id=FIXTURE_DOCUMENT_ID,
            agency_id=agency["id"],
            passenger_workspace_id=passenger["id"],
            passenger_id=passenger["id"],
            passenger_name=passenger["display_name"],
            travel_request_workspace_id=request["id"],
            document_reference="DOC-BROWSER-REQUESTED",
            document_status=DocumentWorkspaceStatus.REQUESTED,
            document_type=DocumentWorkspaceType.PASSPORT_COPY,
            document_category="travel_identity",
            document_title="Requested passport copy",
            document_description="Disposable browser acceptance upload request.",
            required_for_travel=True,
            required_by_airline=True,
            received_status="requested",
            verification_status="pending",
            customer_visible=True,
            internal_only=False,
            created_by="browser_acceptance_fixture",
            updated_by="browser_acceptance_fixture",
        ).model_dump(mode="json"),
    )

    existing_offer = await database.collection("offer_workspaces").find_one(
        {"agency_id": agency["id"], "id": FIXTURE_OFFER_ID}
    )
    if existing_offer is None:
        existing_offer = await database.collection("offer_workspaces").insert_one(
            OfferWorkspace(
                id=FIXTURE_OFFER_ID,
                agency_id=agency["id"],
                request_id=request["id"],
                client_profile_id=client["id"],
                title="Browser acceptance assisted journey",
                currency="EUR",
                client_summary_json={
                    "route": "Sofia to London",
                    "passenger": "Anna Novak",
                },
                internal_notes="BROWSER-INTERNAL-SENTINEL",
                created_by_user_id=owner["id"],
            ).model_dump(mode="json")
        )

    builder = OfferBuilderService(database)
    options = await database.collection("offer_options").find_many(
        {"agency_id": agency["id"], "workspace_id": FIXTURE_OFFER_ID}
    )
    if not options:
        for index, label in enumerate(
            ["Assisted direct option", "Flexible assisted option"], start=1
        ):
            option = await builder.create_option(
                agency["id"],
                FIXTURE_OFFER_ID,
                OfferOptionCreate(
                    label=label,
                    option_order=index,
                    main_airline_code="BA",
                    provider_name="manual",
                    service_feasibility_json={
                        "WCHC": {
                            "status": "conditional",
                            "manual_confirmation_required": True,
                        }
                    },
                    rules_summary_json={
                        "evidence_status": "manual_review",
                        "provider_execution": False,
                    },
                    internal_notes="BROWSER-INTERNAL-SENTINEL",
                ),
                owner["id"],
            )
            await database.collection("offer_options").update_one(
                {"agency_id": agency["id"], "id": option["id"]},
                {
                    "metadata": {
                        "composition_option_id": f"{FIXTURE_COMPOSITION_ID}-{index}"
                    }
                },
            )
            await builder.add_segment(
                agency["id"],
                option["id"],
                OfferBuilderSegmentCreate(
                    sequence=1,
                    marketing_airline_code="BA",
                    operating_airline_code="BA",
                    flight_number=f"BA{890 + index}",
                    origin_airport="SOF",
                    destination_airport="LHR",
                    departure_at=datetime(2027, 2, 10, 12, 0, tzinfo=timezone.utc)
                    + timedelta(hours=index),
                    arrival_at=datetime(2027, 2, 10, 14, 20, tzinfo=timezone.utc)
                    + timedelta(hours=index),
                    cabin_class="economy",
                    booking_class="Y",
                    fare_basis="YFLEX",
                ),
                owner["id"],
            )
            await builder.add_fare_bundle(
                agency["id"],
                option["id"],
                OfferFareBundleCreate(
                    fare_family_name="Economy Flex",
                    cabin_class="economy",
                    booking_class="Y",
                    included_baggage_json={"checked_pieces": 1},
                ),
                owner["id"],
            )
            for line_type, line_label, amount in [
                ("base_fare", "Fare", 220.0 + (index * 20)),
                ("tax", "Taxes", 65.0),
                ("service_fee", "Agency service", 20.0),
            ]:
                await builder.add_pricing_line(
                    agency["id"],
                    option["id"],
                    OfferPricingLineCreate(
                        line_type=line_type,
                        label=line_label,
                        amount=amount,
                        currency="EUR",
                    ),
                    owner["id"],
                )
            await builder.recalculate_option_pricing(
                agency["id"], option["id"], owner["id"]
            )
        options = await database.collection("offer_options").find_many(
            {"agency_id": agency["id"], "workspace_id": FIXTURE_OFFER_ID},
            sort=[("option_order", 1)],
        )

    first_option = options[0]
    first_composition = (first_option.get("metadata") or {}).get(
        "composition_option_id"
    ) or f"{FIXTURE_COMPOSITION_ID}-1"
    now = datetime.now(timezone.utc)
    presentation = await insert_once(
        "journey_comparison_presentations",
        {
            "id": FIXTURE_PRESENTATION_ID,
            "agency_id": agency["id"],
            "journey_id": FIXTURE_JOURNEY_ID,
            "composition_id": FIXTURE_COMPOSITION_ID,
            "offer_id": FIXTURE_OFFER_ID,
            "request_id": request["id"],
            "status": "client_ready",
            "audience_type": "client",
            "language_code": "en",
            "currency_code": "EUR",
            "title": "Browser acceptance options",
            "client_title": "Your assisted travel options",
            "client_intro_text": "Review the exact option and confirm your decision.",
            "internal_notes": "BROWSER-INTERNAL-SENTINEL",
            "metadata": {"client_id": client["id"]},
            "created_at": now,
            "updated_at": now,
        },
    )
    client_payload = {
        "presentation": {
            "title": "Your assisted travel options",
            "status": "client_ready",
        },
        "configuration": {
            "show_connections": True,
            "show_baggage": True,
            "show_flexibility": True,
        },
        "options": [
            {
                "id": "browser-option-projection",
                "composition_option_id": first_composition,
                "title": "Assisted direct option",
                "option_label": "Assisted direct option",
                "origin": "SOF",
                "destination": "LHR",
                "carrier_summary": "British Airways",
                "currency_code": "EUR",
                "total_price": 325,
                "total_elapsed_minutes": 200,
                "stop_count": 0,
                "warning_codes": [],
            }
        ],
        "segments": [
            {
                "id": "browser-segment-projection",
                "option_projection_id": "browser-option-projection",
                "segment_order": 1,
                "origin_airport_code": "SOF",
                "destination_airport_code": "LHR",
                "marketing_carrier": "BA",
                "operating_carrier": "BA",
                "flight_number": "BA891",
                "departure_at": "2027-02-10T13:00:00+00:00",
                "arrival_at": "2027-02-10T15:20:00+00:00",
                "client_operated_by_text": "Operated by British Airways",
            }
        ],
        "connections": [],
        "fare_brands": [
            {
                "id": "browser-fare-projection",
                "option_projection_id": "browser-option-projection",
                "brand_name": "Economy Flex",
                "client_brand_name": "Economy Flex",
                "booking_class_summary": "Y",
                "currency_code": "EUR",
                "grand_total": 325,
                "baggage_summary": "1 checked bag",
                "change_summary": "Changes permitted with fare difference",
                "refund_summary": "Conditional refund",
                "warning_codes": [],
            }
        ],
        "service_suitability": [
            {
                "id": "browser-service-projection",
                "option_projection_id": "browser-option-projection",
                "service_code": "WCHC",
                "service_name": "Wheelchair assistance",
                "suitability_status": "conditional",
                "client_safe_summary": "Airline confirmation remains required.",
                "warning_codes": [],
                "blocking_indicator": False,
            }
        ],
        "comparison": {
            "lowest_price_option_id": "browser-option-projection",
            "preferred_option_id": "browser-option-projection",
        },
        "content_blocks": [
            {
                "id": "browser-content",
                "title": "Important",
                "client_text": "Times are local and subject to airline confirmation.",
            }
        ],
    }
    await insert_once(
        "journey_presentation_snapshots",
        {
            "id": FIXTURE_SNAPSHOT_ID,
            "agency_id": agency["id"],
            "presentation_id": presentation["id"],
            "version_number": 1,
            "snapshot_status": "finalized",
            "client_safe_payload": client_payload,
            "internal_payload": {"internal_notes": "BROWSER-INTERNAL-SENTINEL"},
            "source_hash": "b" * 64,
            "finalized": True,
            "finalized_at": now,
            "created_at": now,
            "updated_at": now,
        },
    )

    delivery_service = OfferDeliveryClientInteractionService(database)
    created = await delivery_service.create_from_presentation(
        agency["id"],
        FIXTURE_PRESENTATION_ID,
        {
            "client_id": client["id"],
            "offer_id": FIXTURE_OFFER_ID,
            "title": "Your assisted travel options",
            "expires_at": (now + timedelta(days=14)).isoformat(),
        },
        owner,
    )
    delivery = created["delivery"]
    recipient_result = await delivery_service.create_recipient(
        agency["id"],
        delivery["id"],
        {
            "portal_user_id": client_mapping["id"],
            "display_name": "Anna Novak",
            "email_reference": "anna.client@example.com",
        },
        owner,
    )
    versions = await delivery_service.list_versions(agency["id"], delivery["id"])
    if versions[0].get("status") == "draft":
        validation = await delivery_service.validate_version(
            agency["id"], delivery["id"], versions[0]["id"]
        )
        if not validation.get("can_release"):
            raise RuntimeError(
                f"Browser delivery fixture did not validate: {validation.get('findings')}"
            )
        await delivery_service.release_version(
            agency["id"],
            delivery["id"],
            versions[0]["id"],
            {"release_notes": "Browser acceptance fixture release."},
            owner,
        )
    await database.collection("browser_acceptance_fixtures").insert_one(
        {
            "id": "full-system-browser-acceptance",
            "agency_id": agency["id"],
            "other_agency_id": OTHER_AGENCY_ID,
            "owner_user_id": owner["id"],
            "client_id": client["id"],
            "passenger_id": passenger["id"],
            "request_id": request["id"],
            "offer_workspace_id": FIXTURE_OFFER_ID,
            "offer_option_ids": [item["id"] for item in options],
            "presentation_id": FIXTURE_PRESENTATION_ID,
            "delivery_id": delivery["id"],
            "recipient_id": recipient_result["recipient"]["id"],
            "internal_sentinel": "BROWSER-INTERNAL-SENTINEL",
            "created_at": now,
            "updated_at": now,
        }
    )


app.add_event_handler("startup", seed_browser_acceptance_fixture)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=18086, access_log=False)
