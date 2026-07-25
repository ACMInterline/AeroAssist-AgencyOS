#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

os.environ["APP_ENV"] = "development"
os.environ["AEROASSIST_DB_MODE"] = "memory"
os.environ["DEMO_AUTH_ENABLED"] = "false"
os.environ["SEED_ON_STARTUP"] = "false"
os.environ["SEED_ENDPOINT_ENABLED"] = "false"
os.environ["LOG_LEVEL"] = "CRITICAL"

import uvicorn

from build_phase import CURRENT_BUILD_PHASE
from database import database
from models import (
    AuthIdentity,
    AuthSession,
    ClientPassengerRelationship,
    PassengerProfile,
    RequestPassenger,
    RequestedService,
    TravelRequest,
    now_utc,
)
from phase_assertions import assert_application_phase_at_least
from security import hash_password, hash_token
from server import app
from services.request_intake_conversion_service import create_intake, convert_intake
from services.request_passenger_identity_service import (
    INTAKE_PLACEHOLDER_NOTE,
    quarantine_legacy_intake_placeholders,
)


MINIMUM_PHASE = "phase_59_0_product_experience_recovery"
PASSWORD = "request-passenger-integrity-smoke-password"
AGENCY_ONE = "passenger-integrity-agency-one"
AGENCY_TWO = "passenger-integrity-agency-two"


async def seed_user(
    key: str,
    email: str,
    agency_id: str,
    agency_role: str,
) -> str:
    identity = AuthIdentity(
        email=email,
        normalized_email=email,
        password_hash=hash_password(PASSWORD),
        identity_type="agency_staff",
        status="active",
    )
    identity_record = await database.collection("auth_identities").insert_one(
        identity.model_dump(mode="json")
    )
    user_id = f"passenger-integrity-user-{key}"
    await database.collection("platform_users").insert_one(
        {
            "id": user_id,
            "email": email,
            "full_name": key.replace("_", " ").title(),
            "global_role": None,
            "status": "active",
        }
    )
    await database.collection("agency_staff_memberships").insert_one(
        {
            "id": f"passenger-integrity-membership-{key}",
            "agency_id": agency_id,
            "user_id": user_id,
            "agency_role": agency_role,
            "status": "active",
        }
    )
    token = f"passenger-integrity-token-{key}"
    session = AuthSession(
        identity_id=identity_record["id"],
        token_hash=hash_token(token),
        expires_at=now_utc() + timedelta(minutes=30),
    )
    await database.collection("auth_sessions").insert_one(session.model_dump(mode="json"))
    return token


async def seed_fixture() -> dict:
    for agency_id in (AGENCY_ONE, AGENCY_TWO):
        await database.collection("agencies").insert_one(
            {
                "id": agency_id,
                "name": agency_id.replace("-", " ").title(),
                "slug": agency_id,
                "status": "active",
            }
        )
        await database.collection("agency_workspaces").insert_one(
            {
                "id": f"{agency_id}-workspace",
                "agency_id": agency_id,
                "name": "Operations",
                "status": "active",
            }
        )

    tokens = {
        "owner_one": await seed_user(
            "owner-one",
            "passenger.integrity.owner.one@example.com",
            AGENCY_ONE,
            "agency_owner",
        ),
        "readonly_one": await seed_user(
            "readonly-one",
            "passenger.integrity.readonly.one@example.com",
            AGENCY_ONE,
            "agency_readonly",
        ),
        "owner_two": await seed_user(
            "owner-two",
            "passenger.integrity.owner.two@example.com",
            AGENCY_TWO,
            "agency_owner",
        ),
    }
    intake = await create_intake(
        database,
        source="public_website",
        contact={
            "name": "Integrity Smoke Client",
            "email": "integrity.client@example.com",
            "data_processing_consent": True,
        },
        travel={
            "origin": "SOF",
            "destination": "LHR",
            "departure_date": "2026-09-14",
            "passenger_count": 2,
        },
        services={"selected_service_categories": ["mobility assistance"]},
        request_details="Wheelchair assistance details require review.",
        agency_id=AGENCY_ONE,
        workspace_id=f"{AGENCY_ONE}-workspace",
        actor_user_id="passenger-integrity-user-owner-one",
    )
    conversion = await convert_intake(
        database,
        intake["id"],
        "passenger-integrity-user-owner-one",
    )
    cross_agency_passenger = PassengerProfile(
        agency_id=AGENCY_TWO,
        first_name="Cross",
        last_name="Tenant",
        display_name="Cross Tenant",
        date_of_birth=date(1984, 2, 1),
    )
    cross_agency_passenger = await database.collection("passenger_profiles").insert_one(
        cross_agency_passenger.model_dump(mode="json")
    )
    return {
        "tokens": tokens,
        "intake": intake,
        "conversion": conversion,
        "cross_agency_passenger": cross_agency_passenger,
    }


def request(
    base_url: str,
    method: str,
    path: str,
    token: str | None = None,
    body: dict | None = None,
) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    encoded = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{base_url}{path}",
        method=method,
        headers=headers,
        data=encoded,
    )
    try:
        response = urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        raw = response.read().decode("utf-8")
        return response.status, json.loads(raw) if raw else {}


def assert_status(
    base_url: str,
    method: str,
    path: str,
    expected: int,
    token: str | None = None,
    body: dict | None = None,
) -> dict:
    actual, payload = request(base_url, method, path, token, body)
    if actual != expected:
        raise AssertionError(
            f"{method} {path} returned {actual}, expected {expected}: {payload}"
        )
    return payload


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(base_url: str) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            status_code, _ = request(base_url, "GET", "/api/health")
            if status_code == 200:
                return
        except (OSError, urllib.error.URLError):
            time.sleep(0.05)
    raise AssertionError("Disposable passenger identity server did not become ready.")


async def verify_unresolved_conversion(fixture: dict) -> list[dict]:
    request_id = fixture["conversion"]["request"]["id"]
    passengers = await database.collection("request_passengers").find_many(
        {"agency_id": AGENCY_ONE, "request_id": request_id}
    )
    if len(passengers) != 2:
        raise AssertionError("Intake conversion did not create two request-level travelers.")
    if any(item.get("passenger_id") for item in passengers):
        raise AssertionError("Intake conversion still created or linked a master passenger.")
    if any(item.get("identity_status") != "unresolved" for item in passengers):
        raise AssertionError("Intake travelers were not marked unresolved.")
    if any(item.get("snapshot_date_of_birth") is not None for item in passengers):
        raise AssertionError("Intake travelers retained a synthetic birth date.")
    if any(item.get("source_intake_id") != fixture["intake"]["id"] for item in passengers):
        raise AssertionError("Unresolved travelers do not retain intake provenance.")
    if await database.collection("passenger_profiles").count({"agency_id": AGENCY_ONE}):
        raise AssertionError("Intake conversion created a PassengerProfile.")
    services = await database.collection("requested_services").find_many(
        {"agency_id": AGENCY_ONE, "request_id": request_id}
    )
    if any(None in (item.get("passenger_ids") or []) for item in services):
        raise AssertionError("Unresolved passenger IDs leaked into requested service references.")
    return passengers


def verify_confirmation_flow(
    base_url: str,
    fixture: dict,
    request_passengers: list[dict],
) -> tuple[str, str]:
    tokens = fixture["tokens"]
    request_id = fixture["conversion"]["request"]["id"]
    first_path = (
        f"/api/agencies/{AGENCY_ONE}/requests/{request_id}/passengers/"
        f"{request_passengers[0]['id']}/confirm-identity"
    )
    second_path = (
        f"/api/agencies/{AGENCY_ONE}/requests/{request_id}/passengers/"
        f"{request_passengers[1]['id']}/confirm-identity"
    )
    assert_status(base_url, "POST", first_path, 401, body={})
    forbidden_payload = {
        "existing_passenger_id": fixture["cross_agency_passenger"]["id"],
        "confirmation_reason": "Authorization boundary check.",
    }
    assert_status(
        base_url, "POST", first_path, 403, tokens["readonly_one"], forbidden_payload
    )
    assert_status(
        base_url, "POST", first_path, 403, tokens["owner_two"], forbidden_payload
    )
    assert_status(
        base_url,
        "POST",
        first_path,
        422,
        tokens["owner_one"],
        {"confirmation_reason": "Reviewed"},
    )
    assert_status(
        base_url,
        "POST",
        first_path,
        422,
        tokens["owner_one"],
        {
            "first_name": "Passenger 1",
            "last_name": "Details pending",
            "date_of_birth": "1900-01-01",
            "confirmation_reason": "Reviewed",
        },
    )
    first = assert_status(
        base_url,
        "POST",
        first_path,
        200,
        tokens["owner_one"],
        {
            "first_name": "Mila",
            "last_name": "Ivanova",
            "date_of_birth": "1987-04-12",
            "passenger_type": "ADT",
            "relationship_type": "self",
            "confirmation_reason": "Passport identity reviewed by agency owner.",
        },
    )
    first_passenger_id = first["passenger"]["id"]
    if first["request_passenger"].get("identity_status") != "confirmed":
        raise AssertionError("Explicit confirmation did not mark request identity confirmed.")

    offer_path = f"/api/agencies/{AGENCY_ONE}/requests/{request_id}/create-offer"
    assert_status(
        base_url,
        "POST",
        offer_path,
        409,
        tokens["owner_one"],
        {"title": "Blocked until identity resolution"},
    )
    assert_status(
        base_url,
        "POST",
        second_path,
        404,
        tokens["owner_one"],
        {
            "existing_passenger_id": fixture["cross_agency_passenger"]["id"],
            "confirmation_reason": "Cross-tenant profile must not resolve.",
        },
    )
    assert_status(
        base_url,
        "POST",
        second_path,
        409,
        tokens["owner_one"],
        {
            "existing_passenger_id": first_passenger_id,
            "confirmation_reason": "Duplicate link should be rejected.",
        },
    )
    second = assert_status(
        base_url,
        "POST",
        second_path,
        200,
        tokens["owner_one"],
        {
            "first_name": "Petar",
            "last_name": "Ivanov",
            "date_of_birth": "1985-09-03",
            "passenger_type": "ADT",
            "relationship_type": "other",
            "confirmation_reason": "Passport identity reviewed by agency owner.",
        },
    )
    second_passenger_id = second["passenger"]["id"]
    repeated = assert_status(
        base_url,
        "POST",
        second_path,
        200,
        tokens["owner_one"],
        {
            "existing_passenger_id": second_passenger_id,
            "confirmation_reason": "Idempotent confirmation retry.",
        },
    )
    if repeated.get("already_confirmed") is not True:
        raise AssertionError("Identity confirmation retry was not idempotent.")

    offer = assert_status(
        base_url,
        "POST",
        offer_path,
        201,
        tokens["owner_one"],
        {"title": "Identity-confirmed offer"},
    )
    if not offer.get("offer", {}).get("id"):
        raise AssertionError("Offer did not become available after identity confirmation.")
    return first_passenger_id, second_passenger_id


async def verify_builder_stays_request_scoped(base_url: str, fixture: dict) -> None:
    profile_count = await database.collection("passenger_profiles").count(
        {"agency_id": AGENCY_ONE}
    )
    request_id = fixture["conversion"]["request"]["id"]
    source_request = await database.collection("travel_requests").find_one(
        {"agency_id": AGENCY_ONE, "id": request_id}
    )
    result = assert_status(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_ONE}/requests/builder",
        201,
        fixture["tokens"]["owner_one"],
        {
            "client": {"client_id": source_request["client_id"]},
            "passengers": [
                {
                    "passenger_link_mode": "unresolved",
                    "first_name": "Proposed",
                    "last_name": "Traveler",
                    "date_of_birth": "1991-06-08",
                    "passenger_type": "adult",
                }
            ],
            "segments": [
                {
                    "sequence": 1,
                    "origin_text": "SOF",
                    "destination_text": "FRA",
                    "departure_date": "2026-10-01",
                }
            ],
            "services": [
                {
                    "category": "other",
                    "applies_to_all_passengers": True,
                    "applies_to_all_segments": True,
                }
            ],
            "title": "Request-scoped traveler smoke",
        },
    )
    if not result.get("passengers") or result["passengers"][0].get("passenger_id"):
        raise AssertionError("Request builder did not preserve unresolved traveler ownership.")
    if await database.collection("passenger_profiles").count(
        {"agency_id": AGENCY_ONE}
    ) != profile_count:
        raise AssertionError("Request builder created a master PassengerProfile implicitly.")


async def seed_legacy_placeholder(fixture: dict) -> dict:
    client_id = fixture["conversion"]["request"]["client_id"]
    legacy_request = TravelRequest(
        agency_id=AGENCY_ONE,
        workspace_id=f"{AGENCY_ONE}-workspace",
        client_id=client_id,
        created_by_user_id="passenger-integrity-user-owner-one",
        request_reference="REQ-LEGACY-P0",
        title="Legacy placeholder quarantine fixture",
        source_intake_id="legacy-intake-p0",
        has_existing_passenger_links=True,
    )
    legacy_request = await database.collection("travel_requests").insert_one(
        legacy_request.model_dump(mode="json")
    )
    fake = PassengerProfile(
        agency_id=AGENCY_ONE,
        first_name="Passenger 1",
        last_name="Details pending",
        display_name="Passenger 1 details pending",
        date_of_birth=date(1900, 1, 1),
        passenger_type="ADT",
        travel_document_notes=INTAKE_PLACEHOLDER_NOTE,
    )
    fake = await database.collection("passenger_profiles").insert_one(
        fake.model_dump(mode="json")
    )
    legitimate = PassengerProfile(
        agency_id=AGENCY_ONE,
        first_name="Actual",
        last_name="Centenarian",
        display_name="Actual Centenarian",
        date_of_birth=date(1900, 1, 1),
        passenger_type="ADT",
    )
    legitimate = await database.collection("passenger_profiles").insert_one(
        legitimate.model_dump(mode="json")
    )
    relationship = ClientPassengerRelationship(
        agency_id=AGENCY_ONE,
        client_id=client_id,
        passenger_id=fake["id"],
        relationship_type="other",
        notes="Placeholder created from intake INT-LEGACY.",
    )
    relationship = await database.collection(
        "client_passenger_relationships"
    ).insert_one(relationship.model_dump(mode="json"))
    request_passenger = RequestPassenger(
        agency_id=AGENCY_ONE,
        request_id=legacy_request["id"],
        passenger_id=fake["id"],
        client_passenger_relationship_id=relationship["id"],
        snapshot_display_name=fake["display_name"],
        snapshot_date_of_birth=fake["date_of_birth"],
        snapshot_passenger_type="ADT",
    )
    request_passenger = await database.collection("request_passengers").insert_one(
        request_passenger.model_dump(mode="json")
    )
    service = RequestedService(
        agency_id=AGENCY_ONE,
        request_id=legacy_request["id"],
        service_code="MAAS",
        service_name="Meet and assist",
        service_category="assistance",
        passenger_ids=[fake["id"]],
        applies_to_all_passengers=True,
    )
    service = await database.collection("requested_services").insert_one(
        service.model_dump(mode="json")
    )
    return {
        "request": legacy_request,
        "fake": fake,
        "legitimate": legitimate,
        "relationship": relationship,
        "request_passenger": request_passenger,
        "service": service,
    }


async def verify_quarantine(fixture: dict) -> dict:
    legacy = await seed_legacy_placeholder(fixture)
    dry_run = await quarantine_legacy_intake_placeholders(
        database,
        AGENCY_ONE,
        "passenger-integrity-user-owner-one",
        apply=False,
    )
    if dry_run["candidate_count"] != 1 or dry_run["quarantined_count"] != 0:
        raise AssertionError(f"Quarantine dry run was not precise: {dry_run}")
    untouched = await database.collection("passenger_profiles").find_one(
        {"agency_id": AGENCY_ONE, "id": legacy["fake"]["id"]}
    )
    if untouched.get("status") != "active":
        raise AssertionError("Dry run mutated a passenger profile.")

    applied = await quarantine_legacy_intake_placeholders(
        database,
        AGENCY_ONE,
        "passenger-integrity-user-owner-one",
        apply=True,
    )
    if applied["quarantined_count"] != 1 or applied["migrated_request_passenger_count"] != 1:
        raise AssertionError(f"Legacy placeholder migration was incomplete: {applied}")
    quarantined = await database.collection("passenger_profiles").find_one(
        {"agency_id": AGENCY_ONE, "id": legacy["fake"]["id"]}
    )
    if (
        quarantined.get("status") != "quarantined"
        or quarantined.get("identity_integrity_status")
        != "quarantined_intake_placeholder"
    ):
        raise AssertionError("Legacy synthetic profile was not quarantined.")
    migrated = await database.collection("request_passengers").find_one(
        {"agency_id": AGENCY_ONE, "id": legacy["request_passenger"]["id"]}
    )
    if (
        migrated.get("passenger_id") is not None
        or migrated.get("snapshot_date_of_birth") is not None
        or migrated.get("identity_status") != "source_quarantined"
    ):
        raise AssertionError("Legacy request passenger was not migrated to unresolved state.")
    relationship = await database.collection(
        "client_passenger_relationships"
    ).find_one({"agency_id": AGENCY_ONE, "id": legacy["relationship"]["id"]})
    if relationship.get("status") != "archived":
        raise AssertionError("Legacy synthetic client-passenger relationship remained active.")
    service = await database.collection("requested_services").find_one(
        {"agency_id": AGENCY_ONE, "id": legacy["service"]["id"]}
    )
    if legacy["fake"]["id"] in (service.get("passenger_ids") or []):
        raise AssertionError("Legacy synthetic passenger reference remained on requested service.")
    legitimate = await database.collection("passenger_profiles").find_one(
        {"agency_id": AGENCY_ONE, "id": legacy["legitimate"]["id"]}
    )
    if legitimate.get("status") != "active":
        raise AssertionError("A legitimate 1900-01-01 passenger was falsely quarantined.")
    repeated = await quarantine_legacy_intake_placeholders(
        database,
        AGENCY_ONE,
        "passenger-integrity-user-owner-one",
        apply=True,
    )
    if repeated["quarantined_count"] != 0:
        raise AssertionError("Legacy placeholder quarantine was not idempotent.")
    return legacy


def verify_quarantine_routes(base_url: str, fixture: dict, legacy: dict) -> None:
    listed = assert_status(
        base_url,
        "GET",
        f"/api/agencies/{AGENCY_ONE}/passengers",
        200,
        fixture["tokens"]["owner_one"],
    )
    if any(item["id"] == legacy["fake"]["id"] for item in listed.get("items") or []):
        raise AssertionError("Quarantined passenger remained in the active passenger selector.")
    assert_status(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_ONE}/passengers/{legacy['fake']['id']}/restore",
        400,
        fixture["tokens"]["owner_one"],
        {},
    )


def main() -> int:
    assert_application_phase_at_least(
        CURRENT_BUILD_PHASE,
        MINIMUM_PHASE,
        source="canonical build phase",
    )
    fixture = asyncio.run(seed_fixture())
    request_passengers = asyncio.run(verify_unresolved_conversion(fixture))

    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    uvicorn_server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="critical", lifespan="off")
    )
    thread = threading.Thread(target=uvicorn_server.run, daemon=True)
    thread.start()
    try:
        wait_for_server(base_url)
        verify_confirmation_flow(base_url, fixture, request_passengers)
        asyncio.run(verify_builder_stays_request_scoped(base_url, fixture))
        legacy = asyncio.run(verify_quarantine(fixture))
        verify_quarantine_routes(base_url, fixture, legacy)
    finally:
        uvicorn_server.should_exit = True
        thread.join(timeout=10)
    if thread.is_alive():
        raise AssertionError("Disposable passenger identity server did not stop.")

    audit = asyncio.run(
        database.collection("audit_events").find_many(
            {
                "agency_id": AGENCY_ONE,
                "event_type": "passenger.intake_placeholder_quarantined",
            }
        )
    )
    if len(audit) != 1:
        raise AssertionError("Legacy placeholder quarantine audit evidence is missing.")
    print("Request passenger identity integrity smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
