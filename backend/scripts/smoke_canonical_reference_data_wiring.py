#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import csv
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
from io import StringIO
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

from canonical_domain_ownership import DOMAIN_OWNERSHIP_BY_KEY
from database import database
from models import AuthIdentity, AuthSession, GlobalReferenceRecord, now_utc
from phase_assertions import assert_application_phase_at_least
from security import hash_password, hash_token
from server import app
from services.canonical_reference_service import (
    REFERENCE_DOMAIN_INVENTORY,
    analyze_reference_wiring,
    find_active_scope_conflict,
    reference_record_usage,
    validate_ptc_for_date,
    validate_ptc_metadata,
)
from services.reference_data_service import (
    REFERENCE_BOOTSTRAP_RECORDS,
    bootstrap_reference_data,
)
from services.reference_domain_usage_service import list_domain_usage


AGENCY_A = "canonical-reference-agency-a"
AGENCY_B = "canonical-reference-agency-b"
MINIMUM_PHASE = "phase_59_0_product_experience_recovery"
REQUIRED_PTC_CODES = {"ADT", "CHD", "INF", "YTH", "SRC", "STU", "SEA", "MIL", "GRP"}
CHECKS: list[str] = []


def check(name: str, condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(f"{name}: {message}")
    CHECKS.append(name)


def ptc_metadata(category: str = "adult", *, minimum: int | None = 18, maximum: int | None = 130) -> dict:
    return {
        "iata_ptc_code": "TST",
        "passenger_category": category,
        "age_min_years": minimum,
        "age_max_years": maximum,
        "requires_date_of_birth": category in {"child", "infant", "youth", "senior"},
        "requires_guardian": category == "infant",
        "is_infant": category == "infant",
        "is_child": category == "child",
        "is_adult": category == "adult",
        "is_senior": category == "senior",
        "applies_to_pricing": True,
        "applies_to_ticketing": True,
        "applies_to_services": True,
        "manual_review_required": category not in {"adult", "child", "infant"},
    }


async def create_principal(
    key: str,
    agency_id: str | None = None,
    agency_role: str | None = None,
    *,
    global_role: str | None = None,
) -> tuple[str, str]:
    email = f"{key}@canonical-reference.example"
    identity = AuthIdentity(
        email=email,
        normalized_email=email,
        password_hash=hash_password("canonical-reference-password"),
        identity_type="agency_staff",
        status="active",
    )
    identity = await database.collection("auth_identities").insert_one(
        identity.model_dump(mode="json")
    )
    user_id = f"canonical-reference-user-{key}"
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
                "id": f"canonical-reference-membership-{key}",
                "agency_id": agency_id,
                "workspace_id": f"{agency_id}-workspace",
                "user_id": user_id,
                "identity_id": identity["id"],
                "agency_role": agency_role,
                "status": "active",
            }
        )
    token = f"canonical-reference-token-{key}"
    session = AuthSession(
        identity_id=identity["id"],
        token_hash=hash_token(token),
        expires_at=now_utc() + timedelta(hours=1),
    )
    await database.collection("auth_sessions").insert_one(session.model_dump(mode="json"))
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
    platform = await create_principal("platform-owner", global_role="platform_owner")
    owner_a = await create_principal("agency-owner-a", AGENCY_A, "agency_owner")
    owner_b = await create_principal("agency-owner-b", AGENCY_B, "agency_owner")
    await bootstrap_reference_data(database, platform[1])
    container = GlobalReferenceRecord(
        domain="container_types",
        code="soft_carrier",
        key="soft_carrier",
        label="Soft-sided carrier",
        source_type="platform",
    )
    await database.collection("global_reference_records").insert_one(
        container.model_dump(mode="json")
    )
    return {"platform": platform, "owner_a": owner_a, "owner_b": owner_b}


async def reference(domain: str, code: str) -> dict:
    records = await database.collection("global_reference_records").find_many(
        {"domain": domain},
        sort=[("sort_order", 1), ("id", 1)],
    )
    normalized = code.upper() if domain in {"passenger_types", "airports", "airlines", "cabin_classes", "countries", "currencies"} else code.lower()
    for record in records:
        record_code = str(record.get("code") or record.get("key") or "")
        if (record_code.upper() if domain in {"passenger_types", "airports", "airlines", "cabin_classes", "countries", "currencies"} else record_code.lower()) == normalized:
            return record
    raise AssertionError(f"Missing reference fixture {domain}:{code}")


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
    raise AssertionError("Disposable canonical reference server did not start.")


def csv_text(rows: list[list[str]]) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(rows)
    return output.getvalue()


async def reference_ids() -> dict[str, dict]:
    return {
        "adt": await reference("passenger_types", "ADT"),
        "bg": await reference("countries", "BG"),
        "sof": await reference("airports", "SOF"),
        "lhr": await reference("airports", "LHR"),
        "lh": await reference("airlines", "LH"),
        "cabin": await reference("cabin_classes", "Y"),
        "eur": await reference("currencies", "EUR"),
        "dog": await reference("pet_species", "dog"),
        "dog_other": await reference("pet_breeds", "dog_other"),
        "container": await reference("container_types", "soft_carrier"),
        "sports": await reference("special_item_categories", "sports_equipment"),
    }


def request_payload(refs: dict[str, dict], *, email: str = "reference-request@example.com") -> dict:
    return {
        "request_version": 4,
        "contact": {
            "first_name": "Reference",
            "last_name": "Traveler",
            "email": email,
        },
        "trip": {
            "trip_label": "Canonical reference smoke",
            "trip_purpose": "leisure",
            "quote_mode": "one_way",
            "preferred_cabin": "Y",
            "preferred_cabin_id": refs["cabin"]["id"],
            "preferred_cabin_label": refs["cabin"]["label"],
            "budget_currency": "EUR",
            "budget_currency_id": refs["eur"]["id"],
            "budget_currency_label": refs["eur"]["label"],
            "preferred_airlines": ["LH"],
            "preferred_airline_ids": [refs["lh"]["id"]],
            "preferred_airline_labels": [refs["lh"]["label"]],
        },
        "itinerary_segments": [
            {
                "segment_local_id": "seg_1",
                "segment_order": 1,
                "origin_label": "Sofia Airport",
                "origin_airport_id": refs["sof"]["id"],
                "origin_iata": "SOF",
                "destination_label": "London Heathrow Airport",
                "destination_airport_id": refs["lhr"]["id"],
                "destination_iata": "LHR",
                "departure_date": "2030-06-15",
                "marketing_carrier": "LH",
                "marketing_carrier_id": refs["lh"]["id"],
                "marketing_carrier_label": refs["lh"]["label"],
                "operating_carrier": "LH",
                "operating_carrier_id": refs["lh"]["id"],
                "operating_carrier_label": refs["lh"]["label"],
                "cabin": "Y",
                "cabin_id": refs["cabin"]["id"],
                "cabin_label": refs["cabin"]["label"],
            }
        ],
        "passengers": [
            {
                "passenger_local_id": "pax_1",
                "identity_status": "unresolved",
                "passenger_type_code_id": refs["adt"]["id"],
                "passenger_type_code": "ADT",
                "passenger_type_label": "Adult",
                "first_name": "Reference",
                "last_name": "Traveler",
                "date_of_birth": "2000-06-16",
                "nationality_reference_id": refs["bg"]["id"],
                "nationality_code": "BG",
                "nationality_label": refs["bg"]["label"],
                "selected_services": [],
                "service_details": {},
            }
        ],
        "pets": [
            {
                "pet_local_id": "pet_1",
                "linked_passenger_local_id": "pax_1",
                "pet_category": "OTHER",
                "species_reference_id": refs["dog"]["id"],
                "species_key": "dog",
                "species_label": refs["dog"]["label"],
                "breed_reference_id": refs["dog_other"]["id"],
                "breed_key": "dog_other",
                "breed_label": refs["dog_other"]["label"],
                "container_type_reference_id": refs["container"]["id"],
                "crate_type": "soft_carrier",
                "container_type_label": refs["container"]["label"],
            }
        ],
        "special_items": [
            {
                "item_local_id": "item_1",
                "linked_passenger_local_id": "pax_1",
                "item_category_reference_id": refs["sports"]["id"],
                "item_category": "sports_equipment",
                "item_category_label": refs["sports"]["label"],
                "declared_value_currency_id": refs["eur"]["id"],
                "declared_value_currency_label": refs["eur"]["label"],
                "details": {
                    "equipment_type": "Bicycle",
                    "declared_value": 500,
                    "currency": "EUR",
                },
            }
        ],
        "request_level_notes": "Canonical references only.",
        "admin_metadata": {
            "source": "staff_created",
            "status": "new",
            "priority": "normal",
        },
    }


def verify_seed_and_metadata() -> None:
    seeds = REFERENCE_BOOTSTRAP_RECORDS["passenger_types"]
    codes = {item["code"] for item in seeds}
    check("01_required_ptc_seeds", codes == REQUIRED_PTC_CODES, f"unexpected PTC codes: {codes}")
    _, duplicate_errors = validate_ptc_metadata({**ptc_metadata(), "iata_ptc_code": "TST"})
    check("05_adt_metadata", not duplicate_errors, f"valid adult metadata failed: {duplicate_errors}")
    chd = next(item for item in seeds if item["code"] == "CHD")
    chd_validation = validate_ptc_for_date(chd, date_of_birth=None, travel_date=date(2030, 1, 1))
    check("06_chd_requires_dob", any("requires date of birth" in item for item in chd_validation["errors"]), "CHD accepted no DOB")
    inf = next(item for item in seeds if item["code"] == "INF")
    inf_validation = validate_ptc_for_date(inf, date_of_birth=None, travel_date=date(2030, 1, 1))
    check(
        "07_inf_dob_and_guardian",
        any("requires date of birth" in item for item in inf_validation["errors"])
        and any("Guardian" in item for item in inf_validation["warnings"]),
        "INF did not require DOB and guardian review",
    )
    yth = next(item for item in seeds if item["code"] == "YTH")
    yth_validation = validate_ptc_for_date(
        yth,
        date_of_birth=date(2010, 1, 2),
        travel_date=date(2030, 1, 1),
    )
    check("08_yth_configured_range", any("maximum" in item for item in yth_validation["errors"]), "YTH range was not metadata driven")
    src = next(item for item in seeds if item["code"] == "SRC")
    changed_src = deepcopy(src)
    changed_src["metadata_json"]["age_min_years"] = 70
    src_validation = validate_ptc_for_date(
        changed_src,
        date_of_birth=date(1962, 1, 1),
        travel_date=date(2030, 1, 1),
    )
    check("09_src_metadata_driven", any("minimum 70" in item for item in src_validation["errors"]), "SRC ignored configured age")
    check("10_special_ptcs_available", {"STU", "SEA", "MIL", "GRP"}.issubset(codes), "review PTCs missing")
    check("11_umnr_ins_not_ptc", not {"UMNR", "INS"}.intersection(codes), "UMNR or INS was seeded as a PTC")
    _, contradictory = validate_ptc_metadata({**ptc_metadata(), "age_min_years": 50, "age_max_years": 20})
    check("04_contradictory_age_rejected", bool(contradictory), "contradictory age range passed")


def verify_source_contract() -> None:
    request_page = (ROOT / "frontend/src/pages/agency/RequestCreatePage.jsx").read_text(encoding="utf-8")
    public_page = (ROOT / "frontend/src/pages/public/HomePage.jsx").read_text(encoding="utf-8")
    passenger_form = (ROOT / "frontend/src/components/PassengerForm.jsx").read_text(encoding="utf-8")
    check("19_airport_selector", "AirportAutocomplete" in request_page and 'domain="airports"' not in request_page, "canonical airport autocomplete missing")
    check("20_airline_selector", "AirlineAutocomplete" in request_page, "canonical airline autocomplete missing")
    check("21_country_selector", "CountrySelect" in request_page and "CountrySelect" in passenger_form, "canonical country selector missing")
    check("22_cabin_selector", 'domain="cabin_classes"' in request_page, "canonical cabin selector missing")
    check("23_currency_selector", "CurrencySelect" in request_page and "CurrencySelect" in public_page, "canonical currency selector missing")
    check("24_species_breed_selectors", 'domain="pet_species"' in request_page and 'domain="pet_breeds"' in request_page, "pet selectors missing")
    priority_sources = request_page + public_page + passenger_form
    check(
        "35_no_hardcoded_ptc_arrays",
        "const passengerTypes" not in priority_sources and '<option value="ADT"' not in priority_sources,
        "priority form retains a hardcoded PTC option array",
    )
    inventory = json.loads((ROOT / "backend/scripts/smoke_inventory.json").read_text(encoding="utf-8"))
    paths = {item["script_path"] for item in inventory["scripts"]}
    check("36_request_v4_regression_registered", "backend/scripts/smoke_canonical_request_v4.py" in paths, "Request V4 smoke missing")
    check("37_passenger_identity_regression_registered", "backend/scripts/smoke_request_passenger_identity_integrity.py" in paths, "Passenger identity smoke missing")
    check("38_identity_tenancy_regression_registered", "backend/scripts/smoke_canonical_identity_tenancy_contract.py" in paths, "Identity smoke missing")
    check("39_p0_security_regressions_registered", "backend/scripts/smoke_audit_event_isolation.py" in paths, "P0 audit smoke missing")
    ownership = DOMAIN_OWNERSHIP_BY_KEY["reference_data"]
    check(
        "40_canonical_ownership",
        ownership["canonical_collection"] == "global_reference_records"
        and ownership["canonical_model"] == "GlobalReferenceRecord",
        "GlobalReferenceRecord ownership changed",
    )
    check(
        "42_smoke_inventory_resolved",
        "backend/scripts/smoke_canonical_reference_data_wiring.py" in paths,
        "focused smoke is not inventoried",
    )


def verify_runtime(base_url: str, fixture: dict) -> None:
    platform_token, platform_user_id = fixture["platform"]
    owner_a_token, _ = fixture["owner_a"]
    owner_b_token, _ = fixture["owner_b"]
    health = expect(base_url, "GET", "/api/health", 200)
    assert_application_phase_at_least(health.get("phase"), MINIMUM_PHASE, source="/api/health")
    readiness = expect(base_url, "GET", "/api/readiness", 200)
    contract = readiness.get("canonical_reference_data_contract") or {}
    if contract.get("normalized_option_contract_enabled") is not True:
        raise AssertionError("Canonical reference readiness registration is missing.")

    refs = asyncio.run(reference_ids())
    duplicate = expect(
        base_url,
        "POST",
        "/api/platform/reference/records",
        409,
        platform_token,
        {
            "domain": "passenger_types",
            "code": "ADT",
            "label": "Duplicate Adult",
            "metadata_json": REFERENCE_BOOTSTRAP_RECORDS["passenger_types"][0]["metadata_json"],
        },
    )
    check("02_duplicate_active_ptc_code", "active reference" in str(duplicate).lower(), "duplicate PTC was not rejected")

    conflicting_key = GlobalReferenceRecord(
        domain="passenger_types",
        code="KEYA",
        key="DUPK",
        label="Key fixture",
        metadata_json={**ptc_metadata(), "iata_ptc_code": "KEYA"},
    )
    asyncio.run(database.collection("global_reference_records").insert_one(conflicting_key.model_dump(mode="json")))
    key_conflict = asyncio.run(
        find_active_scope_conflict(
            database,
            domain="passenger_types",
            code="KEYB",
            key="DUPK",
            scope="global",
            agency_id=None,
        )
    )
    check("03_duplicate_active_ptc_key", key_conflict is not None, "duplicate active key was not detected")

    request_created = expect(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/requests",
        201,
        owner_a_token,
        request_payload(refs),
    )
    request_id = request_created["request"]["id"]
    request_passenger = asyncio.run(
        database.collection("request_passengers").find_one(
            {"agency_id": AGENCY_A, "request_id": request_id}
        )
    )
    check(
        "12_request_ptc_snapshot",
        request_passenger.get("passenger_type_code_id") == refs["adt"]["id"]
        and request_passenger.get("passenger_type_code") == "ADT"
        and request_passenger.get("passenger_type_label") == "Adult",
        "Request passenger did not store ID, code, and label",
    )
    check("14_first_segment_age", request_passenger.get("calculated_age_on_first_segment") == 29, "age did not use first segment date")

    passenger = expect(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/passengers",
        201,
        owner_a_token,
        {
            "first_name": "Profile",
            "last_name": "Traveler",
            "date_of_birth": "1990-01-01",
            "passenger_type": "ADT",
            "passenger_type_code_id": refs["adt"]["id"],
            "passenger_type_code": "ADT",
            "passenger_type_label": "Adult",
            "nationality_reference_id": refs["bg"]["id"],
            "nationality": "BG",
            "nationality_label": refs["bg"]["label"],
        },
    )["passenger"]
    check(
        "13_passenger_profile_ptc_snapshot",
        passenger.get("passenger_type_code_id") == refs["adt"]["id"]
        and passenger.get("passenger_type_code") == "ADT"
        and passenger.get("passenger_type_label") == "Adult",
        "PassengerProfile did not store ID, code, and label",
    )
    expect(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/passengers",
        400,
        owner_a_token,
        {
            "first_name": "Invalid",
            "last_name": "Reference",
            "date_of_birth": "1990-01-01",
            "passenger_type": "ADT",
            "passenger_type_code_id": "missing-ptc-id",
            "passenger_type_code": "ADT",
        },
    )
    check("15_invalid_ptc_id_rejected", True, "")

    expect(
        base_url,
        "PUT",
        f"/api/platform/reference/records/{refs['adt']['id']}",
        200,
        platform_token,
        {"label": "Adult Updated"},
    )
    stored_snapshot = asyncio.run(
        database.collection("request_passengers").find_one({"id": request_passenger["id"]})
    )
    check("18_label_change_preserves_snapshot", stored_snapshot.get("passenger_type_label") == "Adult", "historical snapshot was relabeled")

    unknown_payload = request_payload(refs, email="legacy-reference@example.com")
    unknown_payload["passengers"][0]["nationality_reference_id"] = ""
    unknown_payload["passengers"][0]["nationality_code"] = "ZZ"
    unknown_payload["passengers"][0]["nationality_label"] = "Legacy Unknown"
    unknown = expect(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/requests",
        201,
        owner_a_token,
        unknown_payload,
    )
    messages = (unknown["request"].get("canonical_payload") or {}).get("admin_metadata", {}).get("reference_reconciliation_messages", [])
    check("25_unknown_legacy_flagged", any("countries:ZZ" in item for item in messages), "unknown legacy value was not flagged")

    scoped = GlobalReferenceRecord(
        domain="passenger_types",
        code="BSC",
        key="BSC",
        label="Agency B Scoped",
        agency_id=AGENCY_B,
        scope="agency",
        metadata_json={**ptc_metadata(), "iata_ptc_code": "BSC"},
    )
    scoped = asyncio.run(database.collection("global_reference_records").insert_one(scoped.model_dump(mode="json")))
    expect(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/passengers",
        403,
        owner_a_token,
        {
            "first_name": "Cross",
            "last_name": "Scope",
            "date_of_birth": "1990-01-01",
            "passenger_type": "ADT",
            "passenger_type_code_id": scoped["id"],
            "passenger_type_code": "BSC",
        },
    )
    check("26_cross_scope_rejected", True, "")
    scoped_conflict = asyncio.run(
        find_active_scope_conflict(
            database,
            domain="passenger_types",
            code="ADT",
            key="ADT",
            scope="agency",
            agency_id=AGENCY_B,
        )
    )
    check("27_scoped_conflict_rejected", scoped_conflict is not None, "global/scoped conflict was not detected")

    temp_record = expect(
        base_url,
        "POST",
        "/api/platform/reference/records",
        201,
        platform_token,
        {
            "domain": "passenger_types",
            "code": "TST",
            "label": "Test Adult",
            "metadata_json": ptc_metadata(),
        },
    )["record"]
    expect(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/passengers",
        201,
        owner_a_token,
        {
            "first_name": "Usage",
            "last_name": "Fixture",
            "date_of_birth": "1990-01-01",
            "passenger_type": "ADT",
            "passenger_type_code_id": temp_record["id"],
            "passenger_type_code": "TST",
            "passenger_type_label": "Test Adult",
        },
    )
    usage = asyncio.run(reference_record_usage(database, temp_record))
    blocked = expect(
        base_url,
        "POST",
        f"/api/platform/reference/records/{temp_record['id']}/archive",
        409,
        platform_token,
        {},
    )
    check(
        "28_deactivation_warns_on_active_usage",
        usage["used_by_active_records"] and "used by active" in str(blocked).lower(),
        "active usage did not block ordinary deactivation",
    )
    expect(
        base_url,
        "POST",
        f"/api/platform/reference/records/{temp_record['id']}/archive",
        403,
        owner_a_token,
        {},
    )
    check("29_unauthorized_deactivation_rejected", True, "")
    expect(
        base_url,
        "POST",
        f"/api/platform/reference/records/{temp_record['id']}/archive",
        422,
        platform_token,
        {"force": True},
    )
    deactivated = expect(
        base_url,
        "POST",
        f"/api/platform/reference/records/{temp_record['id']}/archive",
        200,
        platform_token,
        {"force": True, "reason": "Reviewed smoke override"},
    )["record"]
    audit = asyncio.run(
        database.collection("audit_events").find_one(
            {
                "entity_id": temp_record["id"],
                "event_type": "platform_reference_record_archived",
            }
        )
    )
    check(
        "30_forced_override_reason_and_audit",
        deactivated.get("is_active") is False
        and audit is not None
        and (audit.get("metadata") or {}).get("reason") == "Reviewed smoke override",
        "forced deactivation was not reasoned and audited",
    )
    expect(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/passengers",
        409,
        owner_a_token,
        {
            "first_name": "Inactive",
            "last_name": "Selection",
            "date_of_birth": "1990-01-01",
            "passenger_type": "ADT",
            "passenger_type_code_id": temp_record["id"],
            "passenger_type_code": "TST",
        },
    )
    check("16_inactive_ptc_new_selection_rejected", True, "")
    historical = expect(
        base_url,
        "GET",
        f"/api/reference/passenger_types/{temp_record['id']}",
        200,
        platform_token,
    )
    check("17_inactive_historical_readable", historical.get("historical") is True, "inactive historical PTC was unreadable")

    duplicate_import = csv_text(
        [
            ["code", "label", "passenger_category", "metadata_json"],
            ["ZZ1", "Import One", "adult", json.dumps({**ptc_metadata(), "iata_ptc_code": "ZZ1"})],
            ["ZZ1", "Import Two", "adult", json.dumps({**ptc_metadata(), "iata_ptc_code": "ZZ1"})],
        ]
    )
    import_preview = expect(
        base_url,
        "POST",
        "/api/platform/reference/import/preview",
        200,
        platform_token,
        {"domain": "passenger_types", "filename": "ptc.csv", "csv_text": duplicate_import, "mode": "upsert"},
    )
    contradictory_import = csv_text(
        [
            ["code", "label", "passenger_category", "metadata_json"],
            ["ZZ2", "Bad Ages", "adult", json.dumps({**ptc_metadata(), "iata_ptc_code": "ZZ2", "age_min_years": 50, "age_max_years": 20})],
        ]
    )
    bad_preview = expect(
        base_url,
        "POST",
        "/api/platform/reference/import/preview",
        200,
        platform_token,
        {"domain": "passenger_types", "filename": "ptc-bad.csv", "csv_text": contradictory_import, "mode": "upsert"},
    )
    check(
        "31_import_matches_manual_validation",
        import_preview["valid"] is False
        and bad_preview["valid"] is False
        and any("duplicate code" in item.lower() for item in import_preview["errors"])
        and any("age_min_years" in item for item in bad_preview["errors"]),
        "PTC import did not use duplicate and metadata validation",
    )

    usage_registry_a = list_domain_usage()
    usage_registry_b = list_domain_usage()
    check(
        "32_usage_registry_deterministic",
        usage_registry_a == usage_registry_b
        and [item["domain_key"] for item in usage_registry_a] == sorted(item["domain_key"] for item in usage_registry_a)
        and not set(REFERENCE_DOMAIN_INVENTORY).difference(
            {item["domain_key"] for item in usage_registry_a}
            | {"passenger_type_codes", "species", "breeds", "pricing_formula_components", "communication_channels", "service_codes"}
        ),
        "usage registry is incomplete or nondeterministic",
    )
    expect(base_url, "GET", "/api/reference/passenger_types/options?limit=201", 422)
    bounded = expect(base_url, "GET", "/api/reference/passenger_types/options?limit=5", 200)
    check("33_reference_queries_bounded", bounded.get("limit") == 5 and len(bounded.get("items", [])) <= 5, "query limit was not bounded")
    safe_item = bounded["items"][0]
    check(
        "34_public_safe_fields",
        set(safe_item) == {"id", "value", "label", "code", "key", "raw"}
        and not {"agency_id", "updated_by_user_id", "created_by_user_id", "deactivation_reason"}.intersection(safe_item["raw"]),
        "public option exposed persistence or governance fields",
    )

    before = {
        name: asyncio.run(database.collection(name).count())
        for name in (
            "passenger_profiles",
            "request_passengers",
            "travel_requests",
            "request_segments",
            "request_pets",
            "request_special_items",
            "global_reference_records",
        )
    }
    analysis = asyncio.run(analyze_reference_wiring(database))
    after = {
        name: asyncio.run(database.collection(name).count())
        for name in before
    }
    check(
        "41_dry_run_zero_writes",
        analysis["dry_run"] is True
        and analysis["writes_performed"] == 0
        and analysis["write_mode_available"] is False
        and before == after == analysis["before_counts"] == analysis["after_counts"],
        "reference reconciliation analysis wrote data",
    )

    # Keep the second Agency principal active so cross-tenant setup itself is
    # proven valid and cannot be optimized away as an unused fixture.
    expect(base_url, "GET", f"/api/agencies/{AGENCY_B}/passengers", 200, owner_b_token)
    if platform_user_id == "":
        raise AssertionError("Platform owner fixture is invalid.")


def main() -> int:
    verify_seed_and_metadata()
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
        raise AssertionError("Disposable canonical reference server did not stop.")
    check("43_exact_check_count_guard", len(CHECKS) == 42, f"expected 42 checks before guard, got {len(CHECKS)}")
    print(
        "Canonical reference data wiring smoke passed: "
        f"{len(CHECKS) - 1} required checks plus exact-count guard."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
