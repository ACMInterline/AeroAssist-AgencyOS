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
from database import database, ensure_mongo_indexes
from fastapi import HTTPException
from models import (
    AuthIdentity,
    AuthSession,
    ClientMasterRecord,
    ClientMasterRecordCreate,
    ClientMasterRecordUpdate,
    Invitation,
    PortalAccessMappingCreate,
    now_utc,
)
from pydantic import ValidationError
from phase_assertions import assert_application_phase_at_least
from security import hash_password, hash_token
from server import app
from services.authorization_service import (
    PERMISSIONS,
    agency_request_permission,
    agency_permissions,
    identity_tenancy_readiness_metadata,
    project_authorized_commercial_fields,
    require_commercial_field_permissions,
)
from services.client_passenger_master_service import (
    ClientPassengerMasterError,
    ClientPassengerMasterService,
)
from services.identity_tenancy_migration_service import analyze_identity_tenancy_migration
from services.portal_identity_link_service import (
    PortalIdentityLinkConflict,
    PortalIdentityLinkNotFound,
    create_portal_mapping,
)


AGENCY_A = "identity-contract-agency-a"
AGENCY_B = "identity-contract-agency-b"
PASSWORD = "identity-contract-smoke-password"
MINIMUM_PHASE = "phase_59_0_product_experience_recovery"


class IndexRegressionCollection:
    def __init__(self) -> None:
        self.indexes: dict[str, dict] = {}

    async def index_information(self) -> dict[str, dict]:
        return {
            name: {**value, "key": list(value.get("key") or [])}
            for name, value in self.indexes.items()
        }

    async def create_index(
        self,
        keys: list[tuple[str, object]],
        **options: object,
    ) -> str:
        index_keys = list(keys)
        name = str(
            options.get("name")
            or "_".join(f"{field}_{direction}" for field, direction in index_keys)
        )
        self.indexes[name] = {
            "key": index_keys,
            **{key: value for key, value in options.items() if key != "name"},
        }
        return name


class IndexRegressionDatabase:
    def __init__(self) -> None:
        self.collections: dict[str, IndexRegressionCollection] = {}

    def __getitem__(self, collection_name: str) -> IndexRegressionCollection:
        if collection_name not in self.collections:
            self.collections[collection_name] = IndexRegressionCollection()
        return self.collections[collection_name]


async def verify_index_compatibility() -> None:
    mongo = IndexRegressionDatabase()
    mappings = mongo["portal_access_mappings"]
    mappings.indexes["agency_id_1_user_email_1"] = {
        "key": [("agency_id", 1), ("user_email", 1)],
        "unique": True,
    }

    await ensure_mongo_indexes(mongo)

    legacy = mappings.indexes.get("agency_id_1_user_email_1")
    if legacy != {
        "key": [("agency_id", 1), ("user_email", 1)],
        "unique": True,
    }:
        raise AssertionError("Startup mutated the historical Portal email index.")
    expected_partial = {
        "portal_access_mappings_active_identity_unique": {
            "active_mapping_key": {"$type": "string"}
        },
        "portal_access_mappings_active_subject_unique": {
            "active_subject_key": {"$type": "string"}
        },
    }
    for index_name, partial_filter in expected_partial.items():
        index = mappings.indexes.get(index_name) or {}
        if not index.get("unique") or index.get("partialFilterExpression") != partial_filter:
            raise AssertionError(
                f"{index_name} does not safely exclude historical missing/null keys."
            )


async def create_principal(
    key: str,
    identity_type: str,
    *,
    global_role: str | None = None,
    agency_id: str | None = None,
    agency_role: str | None = None,
) -> tuple[dict, str, str | None]:
    email = f"{key}@identity-contract.example"
    identity = AuthIdentity(
        email=email,
        normalized_email=email,
        password_hash=hash_password(PASSWORD),
        identity_type=identity_type,
        status="active",
    )
    identity = await database.collection("auth_identities").insert_one(
        identity.model_dump(mode="json")
    )
    user_id = None
    if identity_type in {"platform_user", "agency_staff"}:
        user_id = f"identity-contract-user-{key}"
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
                    "id": f"identity-contract-membership-{key}",
                    "agency_id": agency_id,
                    "workspace_id": f"{agency_id}-workspace",
                    "user_id": user_id,
                    "identity_id": identity["id"],
                    "agency_role": agency_role,
                    "status": "active",
                }
            )
    token = f"identity-contract-token-{key}"
    session = AuthSession(
        identity_id=identity["id"],
        token_hash=hash_token(token),
        expires_at=now_utc() + timedelta(minutes=30),
    )
    await database.collection("auth_sessions").insert_one(session.model_dump(mode="json"))
    return identity, token, user_id


async def seed_fixture() -> dict:
    for agency_id in (AGENCY_A, AGENCY_B):
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

    owner_a = await create_principal(
        "owner-a", "agency_staff", agency_id=AGENCY_A, agency_role="agency_owner"
    )
    readonly_a = await create_principal(
        "readonly-a", "agency_staff", agency_id=AGENCY_A, agency_role="agency_readonly"
    )
    agent_a = await create_principal(
        "agent-a", "agency_staff", agency_id=AGENCY_A, agency_role="agency_agent"
    )
    accountant_a = await create_principal(
        "accountant-a", "agency_staff", agency_id=AGENCY_A, agency_role="agency_accountant"
    )
    owner_b = await create_principal(
        "owner-b", "agency_staff", agency_id=AGENCY_B, agency_role="agency_owner"
    )
    platform_owner = await create_principal(
        "platform-owner", "platform_user", global_role="platform_owner"
    )
    knowledge_editor = await create_principal(
        "knowledge-editor", "platform_user", global_role="platform_knowledge_editor"
    )
    direct_staff_email = "direct-staff@identity-contract.example"
    direct_staff_identity = AuthIdentity(
        email=direct_staff_email,
        normalized_email=direct_staff_email,
        password_hash=hash_password(PASSWORD),
        identity_type="agency_staff",
        status="active",
    )
    direct_staff_identity = await database.collection("auth_identities").insert_one(
        direct_staff_identity.model_dump(mode="json")
    )

    client_a = await database.collection("client_profiles").insert_one(
        {
            "id": "identity-contract-client-a",
            "agency_id": AGENCY_A,
            "client_type": "individual",
            "display_name": "Client A",
            "primary_email": "shared.portal@example.test",
            "status": "active",
            "portal_status": "active",
        }
    )
    client_b = await database.collection("client_profiles").insert_one(
        {
            "id": "identity-contract-client-b",
            "agency_id": AGENCY_B,
            "client_type": "individual",
            "display_name": "Client B",
            "primary_email": "shared.portal@example.test",
            "status": "active",
            "portal_status": "active",
        }
    )
    legacy_invite_client = await database.collection("client_profiles").insert_one(
        {
            "id": "identity-contract-legacy-invite-client-a",
            "agency_id": AGENCY_A,
            "client_type": "individual",
            "display_name": "Legacy Invite Client",
            "primary_email": "portal-legacy-invite@identity-contract.example",
            "status": "active",
            "portal_status": "invited",
        }
    )
    passenger_a = await database.collection("passenger_profiles").insert_one(
        {
            "id": "identity-contract-passenger-a",
            "agency_id": AGENCY_A,
            "first_name": "Passenger",
            "last_name": "A",
            "display_name": "Passenger A",
            "date_of_birth": date(1985, 4, 3).isoformat(),
            "passenger_type": "ADT",
            "status": "active",
        }
    )
    passenger_b = await database.collection("passenger_profiles").insert_one(
        {
            "id": "identity-contract-passenger-b",
            "agency_id": AGENCY_B,
            "first_name": "Passenger",
            "last_name": "B",
            "display_name": "Passenger B",
            "date_of_birth": date(1988, 7, 8).isoformat(),
            "passenger_type": "ADT",
            "status": "active",
        }
    )
    await database.collection("client_passenger_relationships").insert_one(
        {
            "id": "identity-contract-relationship-a",
            "agency_id": AGENCY_A,
            "client_id": client_a["id"],
            "passenger_id": passenger_a["id"],
            "relationship_type": "self",
            "can_view": True,
            "status": "active",
        }
    )

    portal_client = await create_principal("portal-client", "client_portal")
    portal_passenger = await create_principal("portal-passenger", "passenger_portal")
    portal_unlinked = await create_principal("portal-unlinked", "client_portal")
    portal_email_only = await create_principal("portal-email-only", "client_portal")
    portal_ambiguous = await create_principal("portal-ambiguous", "client_portal")
    portal_legacy_invite = await create_principal(
        "portal-legacy-invite", "client_portal"
    )
    portal_inactive_link = await create_principal(
        "portal-inactive-link", "client_portal"
    )
    stale_staff = await create_principal(
        "stale-staff",
        "agency_staff",
        agency_id=AGENCY_A,
        agency_role="agency_agent",
    )
    await database.collection("platform_users").insert_one(
        {
            "id": "identity-contract-colliding-platform-user",
            "email": portal_client[0]["email"],
            "full_name": "Colliding Staff Email",
            "global_role": "platform_owner",
            "status": "active",
        }
    )
    portal_staff_invitation_token = "identity-contract-portal-staff-invitation"
    portal_staff_invitation = Invitation(
        agency_id=AGENCY_A,
        invited_email=portal_client[0]["email"],
        normalized_email=portal_client[0]["normalized_email"],
        invitation_type="agency_staff",
        target_role="agency_agent",
        invited_by_user_id=owner_a[2],
        token_hash=hash_token(portal_staff_invitation_token),
        expires_at=now_utc() + timedelta(minutes=30),
    )
    await database.collection("invitations").insert_one(
        portal_staff_invitation.model_dump(mode="json")
    )

    client_mapping = await create_portal_mapping(
        database,
        AGENCY_A,
        PortalAccessMappingCreate(
            auth_identity_id=portal_client[0]["id"],
            subject_type="client",
            client_profile_id=client_a["id"],
        ),
        owner_a[2],
    )
    await create_portal_mapping(
        database,
        AGENCY_A,
        PortalAccessMappingCreate(
            auth_identity_id=portal_passenger[0]["id"],
            subject_type="passenger",
            passenger_profile_id=passenger_a["id"],
        ),
        owner_a[2],
    )
    await database.collection("portal_access_mappings").insert_one(
        {
            "id": "identity-contract-legacy-email-mapping",
            "agency_id": AGENCY_A,
            "client_id": client_a["id"],
            "user_email": portal_email_only[0]["email"],
            "portal_status": "active",
            "linkage_version": "legacy_email",
        }
    )
    legacy_invitation_token = "identity-contract-legacy-client-invitation"
    legacy_invitation = Invitation(
        agency_id=AGENCY_A,
        invited_email=portal_legacy_invite[0]["email"],
        invited_name="Legacy Invite Client",
        normalized_email=portal_legacy_invite[0]["normalized_email"],
        invitation_type="client_portal",
        target_client_id=legacy_invite_client["id"],
        invited_by_user_id=owner_a[2],
        token_hash=hash_token(legacy_invitation_token),
        expires_at=now_utc() + timedelta(minutes=30),
    )
    await database.collection("invitations").insert_one(
        legacy_invitation.model_dump(mode="json")
    )
    await database.collection("portal_access_mappings").insert_one(
        {
            "id": "identity-contract-legacy-invited-mapping",
            "agency_id": AGENCY_A,
            "client_id": legacy_invite_client["id"],
            "user_email": portal_legacy_invite[0]["email"],
            "portal_status": "invited",
            "display_name": "Legacy Invite Client",
            "linkage_version": "legacy_email",
        }
    )
    await database.collection("portal_access_mappings").insert_one(
        {
            "id": "identity-contract-inactive-identity-mapping",
            "agency_id": AGENCY_A,
            "auth_identity_id": portal_inactive_link[0]["id"],
            "subject_type": "passenger",
            "passenger_profile_id": passenger_a["id"],
            "status": "active",
            "portal_status": "active",
            "linkage_version": "explicit_identity_v1",
        }
    )
    await database.collection("auth_identities").update_one(
        {"id": portal_inactive_link[0]["id"]},
        {"status": "revoked"},
    )
    await database.collection("auth_identities").update_one(
        {"id": stale_staff[0]["id"]},
        {"status": "revoked"},
    )
    await database.collection("client_portal_access_profiles").insert_one(
        {
            "id": "identity-contract-unlinked-legacy-portal-profile",
            "agency_id": AGENCY_A,
            "portal_access_reference": "CPA-IDENTITY-CONTRACT",
            "portal_status": "active",
            "client_master_record_id": "historical-client-master",
        }
    )
    for mapping_id, agency_id, client_id in (
        (
            "identity-contract-ambiguous-mapping-a",
            AGENCY_A,
            "identity-contract-missing-ambiguous-client-a",
        ),
        (
            "identity-contract-ambiguous-mapping-b",
            AGENCY_B,
            "identity-contract-missing-ambiguous-client-b",
        ),
    ):
        await database.collection("portal_access_mappings").insert_one(
            {
                "id": mapping_id,
                "agency_id": agency_id,
                "auth_identity_id": portal_ambiguous[0]["id"],
                "subject_type": "client",
                "client_profile_id": client_id,
                "client_id": client_id,
                "status": "active",
                "portal_status": "active",
                "linkage_version": "explicit_identity_v1",
            }
        )

    try:
        await create_portal_mapping(
            database,
            AGENCY_A,
            PortalAccessMappingCreate(
                auth_identity_id=portal_client[0]["id"],
                subject_type="client",
                client_profile_id=client_a["id"],
            ),
            owner_a[2],
        )
    except PortalIdentityLinkConflict:
        pass
    else:
        raise AssertionError("Duplicate active portal mapping was accepted.")

    cross_identity = await create_principal("portal-cross", "client_portal")
    try:
        await create_portal_mapping(
            database,
            AGENCY_A,
            PortalAccessMappingCreate(
                auth_identity_id=cross_identity[0]["id"],
                subject_type="client",
                client_profile_id=client_b["id"],
            ),
            owner_a[2],
        )
    except PortalIdentityLinkNotFound:
        pass
    else:
        raise AssertionError("Cross-agency portal subject mapping was accepted.")

    journey_id = "identity-contract-journey-a"
    composition_id = "identity-contract-composition-a"
    option_id = "identity-contract-option-a"
    fare_id = "identity-contract-fare-a"
    await database.collection("journey_representations").insert_one(
        {
            "id": journey_id,
            "agency_id": AGENCY_A,
            "journey_reference": "IDENTITY-COMMERCIAL-TEST",
            "title": "Permission projection fixture",
            "status": "draft",
        }
    )
    await database.collection("journey_option_compositions").insert_one(
        {
            "id": composition_id,
            "agency_id": AGENCY_A,
            "journey_id": journey_id,
            "title": "Permission projection fixture",
            "status": "draft",
        }
    )
    await database.collection("journey_option_alternatives").insert_one(
        {
            "id": option_id,
            "agency_id": AGENCY_A,
            "composition_id": composition_id,
            "journey_id": journey_id,
            "option_code": "OPTION-A",
            "display_order": 1,
            "status": "draft",
        }
    )
    await database.collection("journey_fare_brand_choices").insert_one(
        {
            "id": fare_id,
            "agency_id": AGENCY_A,
            "composition_id": composition_id,
            "option_id": option_id,
            "display_order": 1,
            "client_safe_label": "Permission Test Fare",
        }
    )
    await database.collection("journey_commercial_price_breakdowns").insert_one(
        {
            "id": "identity-contract-price-a",
            "agency_id": AGENCY_A,
            "composition_id": composition_id,
            "option_id": option_id,
            "fare_choice_id": fare_id,
            "currency": "EUR",
            "supplier_amount": 500,
            "markup_amount": 75,
            "total_selling_amount": 575,
        }
    )
    offer_workspace_id = "identity-contract-offer-workspace-a"
    offer_option_id = "identity-contract-offer-option-a"
    await database.collection("offer_workspaces").insert_one(
        {
            "id": offer_workspace_id,
            "agency_id": AGENCY_A,
            "title": "Permission projection offer",
            "status": "draft",
            "currency": "EUR",
        }
    )
    await database.collection("offer_options").insert_one(
        {
            "id": offer_option_id,
            "agency_id": AGENCY_A,
            "workspace_id": offer_workspace_id,
            "label": "Permission projection option",
            "option_type": "flight",
            "status": "draft",
            "currency": "EUR",
        }
    )
    for line_id, line_type, label, amount in (
        ("identity-contract-base-line-a", "base_fare", "Fare", 500),
        ("identity-contract-commission-line-a", "commission", "Commission", 25),
    ):
        await database.collection("offer_pricing_lines").insert_one(
            {
                "id": line_id,
                "agency_id": AGENCY_A,
                "option_id": offer_option_id,
                "line_type": line_type,
                "label": label,
                "amount": amount,
                "currency": "EUR",
            }
        )

    return {
        "owner_a": owner_a,
        "readonly_a": readonly_a,
        "agent_a": agent_a,
        "accountant_a": accountant_a,
        "owner_b": owner_b,
        "platform_owner": platform_owner,
        "knowledge_editor": knowledge_editor,
        "portal_client": portal_client,
        "portal_passenger": portal_passenger,
        "portal_unlinked": portal_unlinked,
        "portal_email_only": portal_email_only,
        "portal_ambiguous": portal_ambiguous,
        "portal_legacy_invite": portal_legacy_invite,
        "legacy_invitation_token": legacy_invitation_token,
        "legacy_invite_client_id": legacy_invite_client["id"],
        "client_a": client_a,
        "passenger_a": passenger_a,
        "passenger_b": passenger_b,
        "client_mapping": client_mapping,
        "portal_staff_invitation_token": portal_staff_invitation_token,
        "commercial_composition_id": composition_id,
        "commercial_option_id": option_id,
        "commercial_fare_id": fare_id,
        "offer_workspace_id": offer_workspace_id,
        "offer_option_id": offer_option_id,
        "direct_staff_email": direct_staff_email,
        "direct_staff_identity_id": direct_staff_identity["id"],
    }


def http_request(
    base_url: str,
    method: str,
    path: str,
    token: str | None = None,
    body: dict | None = None,
) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"{base_url}{path}",
        method=method,
        headers=headers,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
    )
    try:
        response = urllib.request.urlopen(request, timeout=10)
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
    actual, payload = http_request(base_url, method, path, token, body)
    if actual != expected:
        raise AssertionError(f"{method} {path} returned {actual}, expected {expected}: {payload}")
    return payload


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(base_url: str) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            if http_request(base_url, "GET", "/api/health")[0] == 200:
                return
        except OSError:
            pass
        time.sleep(0.05)
    raise AssertionError("Disposable identity contract server did not start.")


async def verify_dry_run_and_compatibility(fixture: dict) -> None:
    service = ClientPassengerMasterService(database)
    try:
        ClientMasterRecordCreate(
            agency_id=AGENCY_A,
            client_master_reference="identity-contract-unlinked-create",
            profile={"display_name": "Unlinked compatibility client"},
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("A new unlinked Client Master compatibility record was accepted.")

    legacy = await service.create_client_record(
        ClientMasterRecordCreate(
            agency_id=AGENCY_A,
            client_master_reference="identity-contract-client-master",
            source_client_profile_id=fixture["client_a"]["id"],
            profile={"display_name": "Compatibility client"},
        ),
        {"id": fixture["owner_a"][2]},
        agency_id=AGENCY_A,
    )
    contract = legacy["client_master_record"]["compatibility_contract"]
    if contract["authoritative"] is not False or contract["canonical_owner"] != "ClientProfile":
        raise AssertionError("Legacy Client Master write was not classified as compatibility-only.")
    if legacy["client_master_record"]["metadata"].get("write_contract") != "canonical_source_projection":
        raise AssertionError("Compatibility writer did not record the canonical-source projection contract.")

    try:
        await service.create_client_record(
            ClientMasterRecordCreate(
                agency_id=AGENCY_A,
                client_master_reference="identity-contract-duplicate-client-master",
                source_client_profile_id=fixture["client_a"]["id"],
                profile={"display_name": "Duplicate compatibility client"},
            ),
            {"id": fixture["owner_a"][2]},
            agency_id=AGENCY_A,
        )
    except ClientPassengerMasterError:
        pass
    else:
        raise AssertionError("A duplicate active Client Master compatibility projection was accepted.")

    historical = ClientMasterRecord(
        agency_id=AGENCY_A,
        client_master_reference="identity-contract-historical-unlinked-client-master",
        profile={"display_name": "Historical compatibility client"},
    )
    historical = await database.collection("client_master_records").insert_one(
        historical.model_dump(mode="json")
    )
    historical_read = await service.get_client_record(historical["id"], agency_id=AGENCY_A)
    if historical_read["compatibility_contract"]["authoritative"] is not False:
        raise AssertionError("Historical unlinked compatibility reads were not preserved.")
    try:
        await service.update_client_record(
            historical["id"],
            ClientMasterRecordUpdate(profile={"display_name": "Independent new truth"}),
            {"id": fixture["owner_a"][2]},
            agency_id=AGENCY_A,
        )
    except ClientPassengerMasterError:
        pass
    else:
        raise AssertionError("Historical unlinked compatibility data accepted identity-shaped mutation.")

    before = {
        name: await database.collection(name).count()
        for name in (
            "portal_access_mappings",
            "client_profiles",
            "passenger_profiles",
            "client_master_records",
        )
    }
    report = await analyze_identity_tenancy_migration(database)
    after = {
        name: await database.collection(name).count()
        for name in before
    }
    if before != after or report["writes_performed"] != 0 or not report["dry_run"]:
        raise AssertionError("Identity/tenancy migration analysis performed writes.")
    issue_types = {item["issue_type"] for item in report["issues"]}
    if not {
        "legacy_email_portal_mapping",
        "cross_agency_client_email_collision",
        "ambiguous_active_portal_mappings",
        "inactive_identity_active_portal_mapping",
        "active_membership_without_active_identity",
        "legacy_active_portal_profile_without_active_mapping",
        "duplicate_active_portal_subject_mapping",
    }.issubset(issue_types):
        raise AssertionError(f"Dry-run analysis missed expected reconciliation issues: {issue_types}")


def verify_permission_contract() -> None:
    if not set(PERMISSIONS).issuperset(
        {"manage_platform", "view_supplier_costs", "view_margins", "portal_view_passenger"}
    ):
        raise AssertionError("Central permission vocabulary is incomplete.")
    agent = agency_permissions("agency_agent")
    if "view_supplier_costs" in agent or "view_margins" in agent:
        raise AssertionError("Agency agent received supplier cost or margin access.")
    if not {"view_finance", "edit_finance"}.issubset(agent):
        raise AssertionError("Agency agent lost established invoice/payment access.")
    if not all(
        "edit_airline_knowledge" in agency_permissions(role)
        for role in ("agency_owner", "agency_admin", "agency_agent")
    ):
        raise AssertionError(
            "Agency operational roles lost established airline knowledge editing."
        )
    commercial = {
        "price_breakdown": {
            "supplier_amount": 500,
            "markup_amount": 75,
            "total_selling_amount": 575,
        },
        "pricing_lines": [
            {"line_type": "commission", "label": "Commission", "amount": 25},
            {"line_type": "base_fare", "label": "Fare", "amount": 500},
        ],
    }
    agent_projection = project_authorized_commercial_fields(
        commercial, {"_permissions": sorted(agent)}
    )
    if (
        "supplier_amount" in agent_projection["price_breakdown"]
        or "markup_amount" in agent_projection["price_breakdown"]
        or agent_projection["price_breakdown"].get("total_selling_amount") != 575
        or agent_projection["pricing_lines"] != [
            {"line_type": "base_fare", "label": "Fare", "amount": 500}
        ]
    ):
        raise AssertionError("Agency Agent commercial response projection is unsafe.")
    owner_projection = project_authorized_commercial_fields(
        commercial,
        {"_permissions": sorted(agency_permissions("agency_owner"))},
    )
    if owner_projection != commercial:
        raise AssertionError("Agency Owner commercial permissions removed reviewed fields.")
    try:
        require_commercial_field_permissions(
            {"markup_amount": 75},
            {"_permissions": sorted(agent)},
        )
    except HTTPException as exc:
        if exc.status_code != 403:
            raise
    else:
        raise AssertionError("Agency Agent could submit protected margin metadata.")
    try:
        require_commercial_field_permissions(
            {"line_type": "commission", "label": "Commission", "amount": 25},
            {"_permissions": sorted(agent)},
        )
    except HTTPException as exc:
        if exc.status_code != 403:
            raise
    else:
        raise AssertionError("Agency Agent could submit a protected commission line.")
    accountant = agency_permissions("agency_accountant")
    if not {"view_finance", "edit_finance"}.issubset(accountant):
        raise AssertionError("Agency accountant finance permissions are incomplete.")
    if {"edit_clients", "edit_passengers", "edit_requests"} & accountant:
        raise AssertionError("Agency accountant received unrelated operational edit access.")
    if any(permission.startswith("edit_") for permission in agency_permissions("agency_readonly")):
        raise AssertionError("Agency read-only role received mutation permissions.")
    expected_route_permissions = {
        "/api/agencies/agency-a/client-passenger-links": "edit_clients",
        "/api/agencies/agency-a/client-portal-access-profiles": "edit_clients",
        "/api/agencies/agency-a/passenger-service-history": "edit_passengers",
        "/api/agencies/agency-a/passenger-operational-preferences": "edit_passengers",
        "/api/agencies/agency-a/passenger-known-documents": "edit_passengers",
    }
    for path, expected in expected_route_permissions.items():
        actual = agency_request_permission(path, "POST")
        if actual != expected:
            raise AssertionError(
                f"Central route permission mismatch for {path}: {actual}, expected {expected}."
            )


def verify_runtime(base_url: str, fixture: dict) -> None:
    tokens = {key: value[1] for key, value in fixture.items() if isinstance(value, tuple)}
    clients_path = f"/api/agencies/{AGENCY_A}/clients"
    assert_status(base_url, "GET", clients_path, 401)
    assert_status(base_url, "GET", clients_path, 200, tokens["owner_a"])
    assert_status(
        base_url,
        "GET",
        f"/api/agencies/{AGENCY_B}/clients?workspace_id={AGENCY_A}-workspace",
        403,
        tokens["owner_a"],
    )
    assert_status(base_url, "GET", clients_path, 403, tokens["platform_owner"])
    assert_status(base_url, "GET", "/api/platform/audit-events", 403, tokens["owner_a"])
    assert_status(base_url, "GET", "/api/platform/audit-events", 200, tokens["platform_owner"])
    assert_status(base_url, "GET", "/api/platform/audit-events", 403, tokens["knowledge_editor"])
    assert_status(
        base_url,
        "POST",
        clients_path,
        403,
        tokens["readonly_a"],
        {
            "display_name": "Forbidden mutation",
            "primary_email": "forbidden@example.test",
        },
    )

    client_me = assert_status(base_url, "GET", "/api/portal/me", 200, tokens["portal_client"])
    if client_me["subject_type"] != "client" or client_me["client"]["id"] != fixture["client_a"]["id"]:
        raise AssertionError("Client Portal did not resolve its explicit Client subject.")
    client_passengers = assert_status(
        base_url, "GET", "/api/portal/passengers", 200, tokens["portal_client"]
    )
    if [item["id"] for item in client_passengers["items"]] != [fixture["passenger_a"]["id"]]:
        raise AssertionError("Client Portal passenger scope exceeded explicit relationships.")
    assert_status(base_url, "GET", clients_path, 403, tokens["portal_client"])
    assert_status(base_url, "GET", "/api/platform/audit-events", 403, tokens["portal_client"])
    portal_current = assert_status(
        base_url, "GET", "/api/auth/me", 200, tokens["portal_client"]
    )
    if portal_current.get("user") or portal_current["authorization"].get("platform"):
        raise AssertionError("Portal identity inherited staff access through an email collision.")
    elevation = assert_status(
        base_url,
        "POST",
        "/api/auth/invitations/accept",
        409,
        tokens["portal_client"],
        {
            "token": fixture["portal_staff_invitation_token"],
            "password": PASSWORD,
        },
    )
    if elevation.get("detail") != "Existing identity type is incompatible with this invitation.":
        raise AssertionError(f"Portal-to-staff invitation rejection was unclear: {elevation}")

    passenger_me = assert_status(
        base_url, "GET", "/api/portal/me", 200, tokens["portal_passenger"]
    )
    if passenger_me["subject_type"] != "passenger" or passenger_me["passenger"]["id"] != fixture["passenger_a"]["id"]:
        raise AssertionError("Passenger Portal did not resolve its explicit Passenger subject.")
    passenger_list = assert_status(
        base_url, "GET", "/api/portal/passengers", 200, tokens["portal_passenger"]
    )
    if [item["id"] for item in passenger_list["items"]] != [fixture["passenger_a"]["id"]]:
        raise AssertionError("Passenger Portal returned another Passenger.")
    assert_status(
        base_url,
        "GET",
        f"/api/portal/passengers/{fixture['passenger_a']['id']}",
        200,
        tokens["portal_passenger"],
    )
    assert_status(
        base_url,
        "GET",
        f"/api/portal/passengers/{fixture['passenger_b']['id']}",
        404,
        tokens["portal_passenger"],
    )
    assert_status(base_url, "GET", "/api/portal/requests", 403, tokens["portal_passenger"])
    assert_status(base_url, "GET", clients_path, 403, tokens["portal_passenger"])
    assert_status(base_url, "GET", "/api/platform/audit-events", 403, tokens["portal_passenger"])

    unlinked = assert_status(base_url, "GET", "/api/portal/me", 403, tokens["portal_unlinked"])
    if unlinked.get("detail") != "Your portal account is not linked to a profile yet.":
        raise AssertionError(f"Unlinked Portal state is unclear: {unlinked}")
    email_only = assert_status(
        base_url, "GET", "/api/portal/me", 403, tokens["portal_email_only"]
    )
    if email_only.get("detail") != "Your portal account is not linked to a profile yet.":
        raise AssertionError("Legacy email equality granted Portal access.")
    ambiguous_current = assert_status(
        base_url, "GET", "/api/auth/me", 200, tokens["portal_ambiguous"]
    )
    ambiguous_portal = ambiguous_current["authorization"]["portal"]
    if ambiguous_portal.get("linked") or ambiguous_portal.get("message") != "Portal access requires operator review.":
        raise AssertionError("Ambiguous Portal linkage did not produce a safe review state.")
    assert_status(
        base_url, "GET", "/api/portal/me", 403, tokens["portal_ambiguous"]
    )

    current = assert_status(base_url, "GET", "/api/auth/me", 200, tokens["owner_a"])
    if not {"identity", "authorization", "user", "memberships"}.issubset(current):
        raise AssertionError("Current-user response does not separate identity and authorization.")
    if "password_hash" in json.dumps(current) or current["authorization"].get("portal"):
        raise AssertionError("Current-user response leaked credentials or an unrelated business subject.")

    mapping_id = fixture["client_mapping"]["id"]
    assert_status(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/portal-access-mappings/{mapping_id}/revoke",
        200,
        tokens["owner_a"],
        {"reason": "Focused revocation regression"},
    )
    revoked = assert_status(base_url, "GET", "/api/portal/me", 403, tokens["portal_client"])
    if revoked.get("detail") != "Your portal account is not linked to a profile yet.":
        raise AssertionError("Revoked Portal mapping retained access.")
    replacement = assert_status(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/portal-access-mappings",
        201,
        tokens["owner_a"],
        {
            "auth_identity_id": fixture["portal_unlinked"][0]["id"],
            "subject_type": "client",
            "client_profile_id": fixture["client_a"]["id"],
            "replaces_mapping_id": mapping_id,
        },
    )["portal_mapping"]
    predecessor = assert_status(
        base_url,
        "GET",
        f"/api/agencies/{AGENCY_A}/portal-access-mappings/{mapping_id}",
        200,
        tokens["owner_a"],
    )["portal_mapping"]
    if predecessor.get("replacement_mapping_id") != replacement["id"]:
        raise AssertionError("Explicit Portal replacement linkage was not preserved.")
    replacement_access = assert_status(
        base_url, "GET", "/api/portal/me", 200, tokens["portal_unlinked"]
    )
    if replacement_access.get("client", {}).get("id") != fixture["client_a"]["id"]:
        raise AssertionError("Explicit replacement mapping did not grant only its reviewed subject.")

    accepted_legacy_invite = assert_status(
        base_url,
        "POST",
        "/api/auth/invitations/accept",
        200,
        tokens["portal_legacy_invite"],
        {
            "token": fixture["legacy_invitation_token"],
            "email": fixture["portal_legacy_invite"][0]["email"],
            "password": PASSWORD,
            "display_name": "Legacy Invite Client",
        },
    )
    legacy_mapping = accepted_legacy_invite["auth"]["authorization"]["portal"]["mapping"]
    if (
        legacy_mapping.get("id") != "identity-contract-legacy-invited-mapping"
        or legacy_mapping.get("auth_identity_id")
        != fixture["portal_legacy_invite"][0]["id"]
        or legacy_mapping.get("client_profile_id")
        != fixture["legacy_invite_client_id"]
    ):
        raise AssertionError("Reviewed legacy Portal invitation was not upgraded in place.")

    assert_status(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/staff",
        409,
        tokens["owner_a"],
        {
            "email": "missing-identity@identity-contract.example",
            "full_name": "Missing Identity",
            "agency_role": "agency_agent",
            "status": "active",
        },
    )
    direct_staff = assert_status(
        base_url,
        "POST",
        f"/api/agencies/{AGENCY_A}/staff",
        201,
        tokens["owner_a"],
        {
            "email": fixture["direct_staff_email"],
            "full_name": "Direct Staff",
            "agency_role": "agency_agent",
            "status": "active",
        },
    )
    if (
        direct_staff["user"].get("identity_id")
        != fixture["direct_staff_identity_id"]
        or direct_staff["membership"].get("identity_id")
        != fixture["direct_staff_identity_id"]
    ):
        raise AssertionError("Direct staff compatibility adapter created identity-free records.")

    composition_path = (
        f"/api/agencies/{AGENCY_A}/journey-option-compositions/"
        f"{fixture['commercial_composition_id']}"
    )
    owner_commercial = assert_status(
        base_url, "GET", composition_path, 200, tokens["owner_a"]
    )
    owner_price = owner_commercial["price_breakdowns"][0]
    if owner_price.get("supplier_amount") != 500 or owner_price.get("markup_amount") != 75:
        raise AssertionError("Agency Owner lost reviewed supplier-cost or margin access.")
    agent_commercial = assert_status(
        base_url, "GET", composition_path, 200, tokens["agent_a"]
    )
    agent_price = agent_commercial["price_breakdowns"][0]
    if (
        "supplier_amount" in agent_price
        or "markup_amount" in agent_price
        or agent_price.get("total_selling_amount") != 575
    ):
        raise AssertionError("Agency Agent received protected commercial fields.")
    assert_status(
        base_url,
        "PUT",
        (
            f"{composition_path}/options/{fixture['commercial_option_id']}"
            f"/fare-brands/{fixture['commercial_fare_id']}/pricing"
        ),
        403,
        tokens["agent_a"],
        {"markup_amount": 20},
    )
    offer_path = (
        f"/api/agencies/{AGENCY_A}/offer-workspaces/"
        f"{fixture['offer_workspace_id']}"
    )
    owner_offer = assert_status(
        base_url, "GET", offer_path, 200, tokens["owner_a"]
    )
    if not any(
        line.get("line_type") == "commission"
        for line in owner_offer["pricing_lines"]
    ):
        raise AssertionError("Agency Owner lost reviewed commission-line access.")
    agent_offer = assert_status(
        base_url, "GET", offer_path, 200, tokens["agent_a"]
    )
    if any(
        line.get("line_type") == "commission"
        for line in agent_offer["pricing_lines"]
    ):
        raise AssertionError("Agency Agent received a protected commission line.")
    assert_status(
        base_url,
        "POST",
        (
            f"/api/agencies/{AGENCY_A}/offer-options/"
            f"{fixture['offer_option_id']}/pricing-lines"
        ),
        403,
        tokens["agent_a"],
        {
            "line_type": "commission",
            "label": "Restricted commission",
            "amount": 10,
            "currency": "EUR",
        },
    )

    assert_status(base_url, "GET", clients_path, 200, tokens["agent_a"])
    asyncio.run(
        database.collection("agency_staff_memberships").update_one(
            {"id": "identity-contract-membership-agent-a"},
            {"status": "revoked"},
        )
    )
    assert_status(base_url, "GET", clients_path, 403, tokens["agent_a"])

    readiness = assert_status(base_url, "GET", "/api/readiness", 200)
    assert_application_phase_at_least(
        readiness.get("phase"),
        MINIMUM_PHASE,
        source="canonical identity readiness",
    )
    section = readiness.get("canonical_identity_tenancy_contract") or {}
    if not section.get("agency_id_sole_authorization_tenant_boundary"):
        raise AssertionError("Canonical identity/tenancy readiness metadata is missing.")


def verify_source_contract() -> None:
    if DOMAIN_OWNERSHIP_BY_KEY["passenger_portal_identity"]["target_write_owner"] != "PortalAccessMapping":
        raise AssertionError("Passenger Portal identity decision was not resolved canonically.")
    if DOMAIN_OWNERSHIP_BY_KEY["crm_client"]["target_write_owner"] != "ClientProfile":
        raise AssertionError("ClientProfile is not the canonical Client write owner.")
    if DOMAIN_OWNERSHIP_BY_KEY["passenger"]["target_write_owner"] != "PassengerProfile":
        raise AssertionError("PassengerProfile is not the canonical Passenger write owner.")
    readiness = identity_tenancy_readiness_metadata()
    if not readiness["email_authoritative_portal_access_disabled"]:
        raise AssertionError("Email-based Portal authorization remains enabled.")
    app_source = (ROOT / "frontend/src/App.jsx").read_text(encoding="utf-8")
    context_source = (ROOT / "frontend/src/context/AuthorizationContext.jsx").read_text(encoding="utf-8")
    if "AuthorizationProvider" not in app_source or "AuthorizationBoundary" not in app_source:
        raise AssertionError("Frontend current-user authorization boundary is not registered.")
    if "Your portal account is not linked to a profile yet." not in context_source:
        raise AssertionError("Frontend unlinked Portal state is missing.")


def main() -> int:
    verify_permission_contract()
    verify_source_contract()
    asyncio.run(verify_index_compatibility())
    fixture = asyncio.run(seed_fixture())
    asyncio.run(verify_dry_run_and_compatibility(fixture))

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
        raise AssertionError("Disposable identity contract server did not stop.")

    print(
        "Canonical identity and tenancy contract smoke passed: explicit Client/Passenger "
        "Portal links, strict Agency membership, centralized permissions, revocation, "
        "compatibility projections, and dry-run migration analysis verified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
