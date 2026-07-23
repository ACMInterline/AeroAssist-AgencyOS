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
from copy import deepcopy
from datetime import date, timedelta
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

import uvicorn
from pydantic import ValidationError

from canonical_domain_ownership import DOMAIN_OWNERSHIP_BY_KEY
from database import database
from models import (
    AuthIdentity,
    AuthSession,
    PassengerProfile,
    RequestV4Payload,
    TravelRequest,
    now_utc,
)
from phase_assertions import assert_application_phase_at_least
from security import hash_password, hash_token
from server import app
from services.request_v4_service import analyze_legacy_requests


AGENCY_A = "request-v4-agency-a"
AGENCY_B = "request-v4-agency-b"
MINIMUM_PHASE = "phase_59_0_product_experience_recovery"


def base_payload(quote_mode: str = "one_way") -> dict:
    return {
        "request_version": 4,
        "contact": {
            "first_name": "Canonical",
            "last_name": "Traveler",
            "email": "canonical.request@example.com",
        },
        "trip": {
            "trip_label": "Canonical request smoke",
            "trip_purpose": "leisure",
            "quote_mode": quote_mode,
            "preferred_cabin": "Y",
        },
        "itinerary_segments": [
            {
                "segment_local_id": "seg_1",
                "segment_order": 1,
                "origin_label": "Sofia",
                "origin_iata": "SOF",
                "destination_label": "London Heathrow",
                "destination_iata": "LHR",
                "departure_date": "2030-06-15",
                "departure_time": "09:30",
                "arrival_date": "2030-06-15",
                "arrival_time": "11:00",
                "cabin": "Y",
            }
        ],
        "passengers": [
            {
                "passenger_local_id": "pax_1",
                "identity_status": "unresolved",
                "passenger_type_code": "ADT",
                "passenger_type_label": "Adult",
                "first_name": "Canonical",
                "last_name": "Traveler",
                "date_of_birth": "2000-06-16",
                "selected_services": [],
                "service_details": {},
            }
        ],
        "pets": [],
        "special_items": [],
        "request_level_notes": "Typed request smoke.",
        "admin_metadata": {
            "source": "staff_created",
            "status": "new",
            "priority": "normal",
        },
    }


def assert_invalid(payload: dict, field_fragment: str) -> None:
    try:
        RequestV4Payload.model_validate(payload)
    except ValidationError as exc:
        errors = exc.errors()
        if not any(
            field_fragment in ".".join(str(part) for part in error["loc"])
            or field_fragment in error["msg"]
            or field_fragment in error["type"]
            for error in errors
        ):
            raise AssertionError(
                f"Validation did not identify {field_fragment}: {errors}"
            ) from exc
    else:
        raise AssertionError(f"Invalid Request V4 payload was accepted: {field_fragment}")


def service_payload(service_key: str, details: dict) -> dict:
    payload = base_payload()
    payload["passengers"][0]["selected_services"] = [service_key]
    payload["passengers"][0]["service_details"] = {
        service_key: {
            "segment_scope_mode": "all_segments",
            "segment_ids": [],
            **details,
        }
    }
    return payload


def verify_model_contract() -> None:
    for quote_mode in ("one_way", "round_trip", "multi_city", "open_jaw"):
        payload = base_payload(quote_mode)
        if quote_mode in {"multi_city", "open_jaw"}:
            payload["itinerary_segments"].append(
                {
                    "segment_local_id": "seg_2",
                    "segment_order": 2,
                    "origin_label": "London Heathrow",
                    "origin_iata": "LHR",
                    "destination_label": "New York JFK",
                    "destination_iata": "JFK",
                    "departure_date": "2030-06-18",
                    "cabin": "Y",
                }
            )
        assert RequestV4Payload.model_validate(payload).trip.quote_mode == quote_mode

    payload = base_payload()
    del payload["contact"]["first_name"]
    assert_invalid(payload, "contact.first_name")
    payload = base_payload()
    payload["itinerary_segments"] = []
    assert_invalid(payload, "itinerary_segments")
    payload = base_payload()
    payload["itinerary_segments"][0]["destination_iata"] = "SOF"
    assert_invalid(payload, "itinerary_segments")
    payload = base_payload()
    payload["itinerary_segments"][0]["segment_order"] = 2
    assert_invalid(payload, "segment_order")
    payload = base_payload()
    payload["itinerary_segments"].append(deepcopy(payload["itinerary_segments"][0]))
    payload["itinerary_segments"][1]["segment_order"] = 2
    assert_invalid(payload, "segment")
    payload = base_payload()
    payload["passengers"] = []
    assert_invalid(payload, "passengers")
    payload = base_payload()
    payload["passengers"].append(deepcopy(payload["passengers"][0]))
    assert_invalid(payload, "passenger")

    parsed = RequestV4Payload.model_validate(base_payload())
    assert parsed.passengers[0].calculated_age_on_first_segment == 29

    payload = base_payload()
    payload["passengers"][0]["selected_services"] = ["extra_seat_support"]
    assert_invalid(payload, "service")
    payload = service_payload(
        "extra_seat_support",
        {
            "segment_scope_mode": "selected_segments",
            "segment_ids": ["seg_missing"],
            "reason": "Passenger comfort",
        },
    )
    assert_invalid(payload, "segment")

    for code in ("WCHR", "WCHS", "WCHC"):
        RequestV4Payload.model_validate(
            service_payload(
                "wheelchair_and_mobility_assistance",
                {
                    "suggested_ssr_code": code,
                    "confirmed_ssr_code": code,
                    "final_assistance_label": f"{code} assistance",
                },
            )
        )
    RequestV4Payload.model_validate(
        service_payload(
            "medical_equipment_and_travel_support",
            {"medical_clearance_needed": True, "medif_required": True},
        )
    )
    RequestV4Payload.model_validate(
        service_payload(
            "children_traveling_alone",
            {
                "child_age": 11,
                "airline_um_service_required": True,
                "handover_contact": "Parent A",
                "pickup_contact": "Parent B",
            },
        )
    )
    RequestV4Payload.model_validate(
        service_payload(
            "service_animal",
            {"species": "dog", "task_or_support": "Mobility support"},
        )
    )

    for category in ("PETC", "AVIH"):
        payload = base_payload()
        payload["pets"] = [{
            "pet_local_id": "pet_1",
            "linked_passenger_local_id": "pax_1",
            "pet_category": category,
            "species_label": "Dog",
        }]
        assert_invalid(payload, "carrier")
    payload = base_payload()
    payload["pets"] = [{
        "pet_local_id": "pet_1",
        "linked_passenger_local_id": "pax_missing",
        "pet_category": "OTHER",
        "species_label": "Dog",
    }]
    assert_invalid(payload, "passenger")

    payload = base_payload()
    payload["special_items"] = [{
        "item_local_id": "item_1",
        "linked_passenger_local_id": "pax_missing",
        "item_category": "other",
        "details": {"item_type": "Box"},
    }]
    assert_invalid(payload, "passenger")

    payload = base_payload()
    payload["special_items"] = [{
        "item_local_id": "item_1",
        "item_category": "weapon",
        "details": {"weapon_type": "Sporting equipment"},
    }]
    assert_invalid(payload, "weapon")
    for category, key in (
        ("sports_equipment", "equipment_type"),
        ("musical_instrument", "instrument_type"),
    ):
        payload = base_payload()
        payload["special_items"] = [{
            "item_local_id": "item_1",
            "item_category": category,
            "details": {key: "Test item", "weight_kg": 12},
        }]
        RequestV4Payload.model_validate(payload)
    payload = base_payload()
    payload["special_items"] = [{
        "item_local_id": "item_1",
        "item_category": "valuables_fragile",
        "details": {"item_type": "Camera", "declared_value": 500, "currency": "EU"},
    }]
    assert_invalid(payload, "currency")


async def create_principal(
    key: str,
    agency_id: str | None,
    agency_role: str | None,
    *,
    global_role: str | None = None,
) -> tuple[str, str]:
    email = f"{key}@request-v4.example"
    identity = AuthIdentity(
        email=email,
        normalized_email=email,
        password_hash=hash_password("request-v4-password"),
        identity_type="agency_staff",
        status="active",
    )
    identity = await database.collection("auth_identities").insert_one(
        identity.model_dump(mode="json")
    )
    user_id = f"request-v4-user-{key}"
    await database.collection("platform_users").insert_one(
        {
            "id": user_id,
            "identity_id": identity["id"],
            "email": email,
            "full_name": key.replace("-", " ").title(),
            "global_role": global_role,
            "status": "active",
        }
    )
    if agency_id and agency_role:
        await database.collection("agency_staff_memberships").insert_one(
            {
                "id": f"request-v4-membership-{key}",
                "agency_id": agency_id,
                "workspace_id": f"{agency_id}-workspace",
                "user_id": user_id,
                "identity_id": identity["id"],
                "agency_role": agency_role,
                "status": "active",
            }
        )
    token = f"request-v4-token-{key}"
    session = AuthSession(
        identity_id=identity["id"],
        token_hash=hash_token(token),
        expires_at=now_utc() + timedelta(hours=1),
    )
    await database.collection("auth_sessions").insert_one(
        session.model_dump(mode="json")
    )
    return token, user_id


async def seed_fixture() -> dict:
    database._memory_collections.clear()
    for agency_id in (AGENCY_A, AGENCY_B):
        await database.collection("agencies").insert_one(
            {"id": agency_id, "name": agency_id, "slug": agency_id, "status": "active"}
        )
        await database.collection("agency_workspaces").insert_one(
            {
                "id": f"{agency_id}-workspace",
                "agency_id": agency_id,
                "name": "Operations",
                "status": "active",
            }
        )
    owner_a = await create_principal("owner-a", AGENCY_A, "agency_owner")
    readonly_a = await create_principal("readonly-a", AGENCY_A, "agency_readonly")
    owner_b = await create_principal("owner-b", AGENCY_B, "agency_owner")
    platform_without_membership = await create_principal(
        "platform-without-membership",
        None,
        None,
        global_role="platform_admin",
    )
    passenger_a = PassengerProfile(
        agency_id=AGENCY_A,
        first_name="Agency",
        last_name="A",
        display_name="Agency A Passenger",
        date_of_birth=date(1990, 1, 1),
    )
    passenger_b = PassengerProfile(
        agency_id=AGENCY_B,
        first_name="Agency",
        last_name="B",
        display_name="Agency B Passenger",
        date_of_birth=date(1991, 1, 1),
    )
    passenger_a = await database.collection("passenger_profiles").insert_one(
        passenger_a.model_dump(mode="json")
    )
    passenger_b = await database.collection("passenger_profiles").insert_one(
        passenger_b.model_dump(mode="json")
    )
    return {
        "owner_a": owner_a,
        "readonly_a": readonly_a,
        "owner_b": owner_b,
        "platform_without_membership": platform_without_membership,
        "passenger_a": passenger_a,
        "passenger_b": passenger_b,
    }


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


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
    req = urllib.request.Request(
        f"{base_url}{path}",
        method=method,
        headers=headers,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
    )
    try:
        response = urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        raw = response.read().decode("utf-8")
        return response.status, json.loads(raw) if raw else {}


def expect(
    base_url: str,
    method: str,
    path: str,
    status: int,
    token: str | None = None,
    body: dict | None = None,
) -> dict:
    actual, payload = request(base_url, method, path, token, body)
    if actual != status:
        raise AssertionError(f"{method} {path} returned {actual}, expected {status}: {payload}")
    return payload


def wait_for_server(base_url: str) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            if request(base_url, "GET", "/api/health")[0] == 200:
                return
        except OSError:
            pass
        time.sleep(0.05)
    raise AssertionError("Disposable Request V4 server did not start.")


async def insert_legacy_request(owner_user_id: str) -> str:
    client = await database.collection("client_profiles").find_one(
        {"agency_id": AGENCY_A}
    )
    legacy = TravelRequest(
        agency_id=AGENCY_A,
        client_id=client["id"],
        created_by_user_id=owner_user_id,
        request_reference="REQ-LEGACY",
        title="Readable legacy request",
    )
    await database.collection("travel_requests").insert_one(
        legacy.model_dump(mode="json")
    )
    return legacy.id


async def assert_dry_run() -> None:
    before = await database.collection("travel_requests").count()
    analysis = await analyze_legacy_requests(database)
    after = await database.collection("travel_requests").count()
    assert analysis["dry_run"] is True
    assert analysis["writes_performed"] == 0
    assert before == after


def verify_runtime(base_url: str, fixture: dict) -> None:
    owner_a_token, owner_a_id = fixture["owner_a"]
    readonly_token, _ = fixture["readonly_a"]
    owner_b_token, _ = fixture["owner_b"]
    platform_without_membership_token, _ = fixture["platform_without_membership"]
    health = expect(base_url, "GET", "/api/health", 200)
    assert_application_phase_at_least(
        health.get("phase"),
        MINIMUM_PHASE,
        source="/api/health",
    )
    readiness = expect(base_url, "GET", "/api/readiness", 200)
    if readiness.get("canonical_request_v4", {}).get("request_version") != 4:
        raise AssertionError("Request V4 readiness metadata is missing.")

    before_profiles = asyncio.run(
        database.collection("passenger_profiles").count({"agency_id": AGENCY_A})
    )
    create_payload = base_payload()
    create_payload["itinerary_segments"].append(
        {
            "segment_local_id": "seg_2",
            "segment_order": 2,
            "origin_label": "London Heathrow",
            "origin_iata": "LHR",
            "destination_label": "New York JFK",
            "destination_iata": "JFK",
            "departure_date": "2030-06-16",
            "cabin": "Y",
        }
    )
    create_payload["passengers"].append(
        {
            "passenger_local_id": "pax_2",
            "identity_status": "unresolved",
            "passenger_type_code": "ADT",
            "passenger_type_label": "Adult",
            "first_name": "Second",
            "last_name": "Traveler",
            "selected_services": [],
            "service_details": {},
        }
    )
    created = expect(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/requests",
        201,
        owner_a_token,
        create_payload,
    )
    request_id = created["request"]["id"]
    after_profiles = asyncio.run(
        database.collection("passenger_profiles").count({"agency_id": AGENCY_A})
    )
    if before_profiles != after_profiles:
        raise AssertionError("Request creation auto-created a PassengerProfile.")

    detail = expect(
        base_url,
        "GET",
        f"/api/agencies/{AGENCY_A}/requests/{request_id}",
        200,
        owner_a_token,
    )
    if detail["request"].get("canonical_projection_status") != "current":
        raise AssertionError("Compatibility projection is not current.")
    if detail["passengers"][0].get("identity_status") != "unresolved":
        raise AssertionError("Request passenger identity was not unresolved.")
    if detail["passengers"][0].get("snapshot_passenger_type") != "ADT":
        raise AssertionError("PTC compatibility fields were not preserved.")
    if not detail["segments"] or detail["segments"][0].get("segment_local_id") != "seg_1":
        raise AssertionError("Segment compatibility projection was not generated.")

    expect(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/requests/{request_id}/segments",
        409,
        owner_a_token,
        {"sequence": 2, "origin_text": "LHR", "destination_text": "JFK"},
    )
    expect(
        base_url,
        "GET",
        f"/api/agencies/{AGENCY_A}/requests/{request_id}",
        403,
        owner_b_token,
    )
    expect(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/requests",
        403,
        readonly_token,
        base_payload(),
    )
    expect(
        base_url,
        "GET",
        f"/api/agencies/{AGENCY_A}/requests/{request_id}",
        403,
        platform_without_membership_token,
    )
    expect(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/requests",
        403,
        platform_without_membership_token,
        base_payload(),
    )

    legacy_create_count = asyncio.run(
        database.collection("travel_requests").count({"agency_id": AGENCY_A})
    )
    expect(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/requests",
        422,
        owner_a_token,
        {
            "client_id": detail["request"]["client_id"],
            "title": "Legacy create body must not create parallel truth",
        },
    )
    if asyncio.run(database.collection("travel_requests").count({"agency_id": AGENCY_A})) != legacy_create_count:
        raise AssertionError("Legacy create body created a non-V4 TravelRequest.")

    cross = base_payload()
    cross["passengers"][0]["passenger_profile_id"] = fixture["passenger_b"]["id"]
    cross["passengers"][0]["identity_status"] = "confirmed"
    expect(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/requests",
        400,
        owner_a_token,
        cross,
    )

    pet_payload = base_payload()
    pet_payload["contact"]["email"] = "request-v4-pet@example.com"
    pet_payload["pets"] = [{
        "pet_local_id": "pet_1",
        "linked_passenger_local_id": "pax_1",
        "pet_category": "PETC",
        "species_label": "Dog",
        "pet_weight_kg": 5,
        "container_weight_kg": 2,
        "carrier_length_cm": 45,
        "carrier_width_cm": 30,
        "carrier_height_cm": 25,
    }]
    pet_created = expect(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/requests",
        201,
        owner_a_token,
        pet_payload,
    )
    pet_detail = expect(
        base_url,
        "GET",
        f"/api/agencies/{AGENCY_A}/requests/{pet_created['request']['id']}",
        200,
        owner_a_token,
    )
    if pet_detail["pets"][0].get("combined_weight_kg") != 7:
        raise AssertionError("Pet total weight was not server-derived.")

    public_payload = base_payload()
    public_payload["contact"]["email"] = "request-v4-public@example.com"
    public_before = asyncio.run(database.collection("passenger_profiles").count())
    public = expect(
        base_url,
        "POST",
        "/api/public/requests?privacy_policy_accepted=true",
        201,
        None,
        public_payload,
    )
    if set(public.get("intake") or {}) != {"id", "reference_code", "status"}:
        raise AssertionError("Public Request V4 response exposed internal data.")
    intake = asyncio.run(
        database.collection("request_intakes").find_one({"id": public["intake"]["id"]})
    )
    canonical = RequestV4Payload.model_validate(intake.get("canonical_payload") or {})
    if canonical.passengers[0].identity_status != "unresolved":
        raise AssertionError("Public traveler was not retained as unresolved.")
    if asyncio.run(database.collection("passenger_profiles").count()) != public_before:
        raise AssertionError("Public intake created a PassengerProfile.")
    expect(
        base_url,
        "POST",
        "/api/public/requests",
        400,
        None,
        public_payload,
    )

    update_payload = deepcopy(detail["canonical_request"])
    update_payload["passengers"] = update_payload["passengers"][:1]
    update_payload["itinerary_segments"] = update_payload["itinerary_segments"][:1]
    update_payload["request_level_notes"] = "Updated without omitting children."
    update = expect(
        base_url,
        "PATCH",
        f"/api/agencies/{AGENCY_A}/requests/{request_id}",
        200,
        owner_a_token,
        {"canonical_payload": update_payload},
    )
    if len(update["passengers"]) != 2 or len(update["segments"]) != 2:
        raise AssertionError("Aggregate update silently deleted omitted child projections.")
    removed = expect(
        base_url,
        "PATCH",
        f"/api/agencies/{AGENCY_A}/requests/{request_id}",
        200,
        owner_a_token,
        {
            "canonical_payload": update_payload,
            "remove_passenger_local_ids": ["pax_2"],
            "remove_segment_local_ids": ["seg_2"],
        },
    )
    if len(removed["passengers"]) != 1 or len(removed["segments"]) != 1:
        raise AssertionError("Explicit aggregate removal did not archive child projections.")

    legacy_id = asyncio.run(insert_legacy_request(owner_a_id))
    legacy = expect(
        base_url,
        "GET",
        f"/api/agencies/{AGENCY_A}/requests/{legacy_id}",
        200,
        owner_a_token,
    )
    if legacy.get("migration_status") != "legacy_readable_manual_reconciliation":
        raise AssertionError("Legacy request was not retained as readable.")
    asyncio.run(assert_dry_run())


def verify_source_contract() -> None:
    ownership = DOMAIN_OWNERSHIP_BY_KEY["request"]
    if ownership["canonical_model"] != "TravelRequest":
        raise AssertionError("TravelRequest is not the canonical Request owner.")
    source = (ROOT / "backend/services/request_v4_service.py").read_text(encoding="utf-8")
    if "production_migration_enabled\": False" not in source:
        raise AssertionError("Request V4 does not declare migration disabled.")
    frontend = (ROOT / "frontend/src/pages/agency/RequestCreatePage.jsx").read_text(
        encoding="utf-8"
    )
    for label in (
        "1. Contact",
        "2. Journey",
        "3. Passengers",
        "4. Assistance",
        "5. Animals",
        "6. Special items",
        "7. Review",
    ):
        if label not in frontend:
            raise AssertionError(f"Request workflow step is missing: {label}")
    if "/requests/builder" in frontend:
        raise AssertionError("Request page still writes through the legacy builder route.")
    router_source = (ROOT / "backend/routers/requests.py").read_text(encoding="utf-8")
    if "RequestV4Payload | TravelRequestCreate" in router_source:
        raise AssertionError("Canonical Request creation still accepts an independently writable legacy body.")
    detail = (ROOT / "frontend/src/pages/agency/RequestDetailPage.jsx").read_text(
        encoding="utf-8"
    )
    if "JSON.stringify" in detail:
        raise AssertionError("Request detail still renders raw JSON.")


def main() -> int:
    verify_model_contract()
    verify_source_contract()
    fixture = asyncio.run(seed_fixture())
    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="critical")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        wait_for_server(base_url)
        verify_runtime(base_url, fixture)
    finally:
        server.should_exit = True
        thread.join(timeout=10)
    if thread.is_alive():
        raise AssertionError("Disposable Request V4 server did not stop.")
    print(
        "Canonical Request V4 smoke passed: typed aggregate, validation, unresolved "
        "identity, tenant authorization, compatibility projections, legacy readability, "
        "and dry-run analysis verified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
