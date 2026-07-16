#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE, phase_is_exact
from config import get_settings
from database import Database
from persistence_query import (
    COLLECTION_OWNERSHIP_REGISTRY,
    GOVERNED_INDEX_SPECS,
    MAXIMUM_QUERY_LIMIT,
    PaginationRequest,
    QueryValidationError,
    persistence_readiness_metadata,
    query_diagnostic_records,
)
from persistence_repository import PersistenceRepository


RELEASE_PHASE = "phase_56_5_6_persistence_scalability_tenant_query_hardening_foundation"


def expect_validation_error(function, message: str) -> None:
    try:
        function()
    except QueryValidationError:
        return
    raise AssertionError(message)


async def expect_async_validation_error(awaitable, message: str) -> None:
    try:
        await awaitable
    except QueryValidationError:
        return
    raise AssertionError(message)


async def verify_repository_foundation() -> None:
    original_db_mode = os.environ.get("AEROASSIST_DB_MODE")
    os.environ["AEROASSIST_DB_MODE"] = "memory"
    try:
        db = Database()
    finally:
        if original_db_mode is None:
            os.environ.pop("AEROASSIST_DB_MODE", None)
        else:
            os.environ["AEROASSIST_DB_MODE"] = original_db_mode
    repository = PersistenceRepository(db)
    created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for record in (
        {"id": "passenger-b", "agency_id": "agency-a", "passenger_status": "active", "updated_at": created_at, "created_at": created_at, "contact_email": "private-a@example.test"},
        {"id": "passenger-a", "agency_id": "agency-a", "passenger_status": "active", "updated_at": created_at, "created_at": created_at, "contact_email": "private-b@example.test"},
        {"id": "passenger-c", "agency_id": "agency-b", "passenger_status": "active", "updated_at": created_at, "created_at": created_at, "contact_email": "other@example.test"},
    ):
        await db.collection("passenger_workspaces").insert_one(record)

    first = await repository.find_agency_records(
        collection_name="passenger_workspaces",
        agency_id="agency-a",
        filters={"passenger_status": "active"},
        sort_field="updated_at",
        sort_direction="desc",
        pagination=PaginationRequest.build(limit=1, include_total=True),
    )
    if [item["id"] for item in first.items] != ["passenger-b"] or first.pagination.total != 2 or not first.pagination.next_cursor:
        raise AssertionError(f"Deterministic tenant page was incorrect: {first}")
    second = await repository.find_agency_records(
        collection_name="passenger_workspaces",
        agency_id="agency-a",
        filters={"passenger_status": "active"},
        sort_field="updated_at",
        sort_direction="desc",
        pagination=PaginationRequest.build(limit=1, cursor=first.pagination.next_cursor),
    )
    if [item["id"] for item in second.items] != ["passenger-a"]:
        raise AssertionError("Stable tie-breaker pagination did not return the second tenant record.")
    offset_page = await repository.find_agency_records(
        collection_name="passenger_workspaces",
        agency_id="agency-a",
        filters={"passenger_status": {"$in": ["active"]}},
        sort_field="updated_at",
        sort_direction="desc",
        pagination=PaginationRequest.build(limit=1, offset=1),
        projection=["passenger_status"],
    )
    if offset_page.items != [{"id": "passenger-a", "passenger_status": "active"}]:
        raise AssertionError(f"Offset or safe projection contract was incorrect: {offset_page.items}")
    await expect_async_validation_error(
        repository.find_agency_records(
            collection_name="passenger_workspaces",
            agency_id="agency-b",
            sort_field="updated_at",
            pagination=PaginationRequest.build(limit=1, cursor=first.pagination.next_cursor),
        ),
        "A pagination cursor crossed tenants.",
    )
    await expect_async_validation_error(
        repository.find_agency_records(
            collection_name="passenger_workspaces",
            agency_id="agency-a",
            filters={"agency_id": "agency-b"},
        ),
        "A caller overrode the repository tenant predicate.",
    )
    await expect_async_validation_error(
        repository.find_agency_records(
            collection_name="passenger_workspaces",
            agency_id="agency-a",
            filters={"passenger_status": {"$where": "private-a@example.test"}},
        ),
        "An unsafe MongoDB operator was accepted.",
    )
    await expect_async_validation_error(
        repository.find_agency_records(
            collection_name="passenger_workspaces",
            agency_id="agency-a",
            filters={"passenger_status": {"$in": [str(index) for index in range(101)]}},
        ),
        "An unbounded $in filter was accepted.",
    )
    await expect_async_validation_error(
        repository.find_agency_records(
            collection_name="passenger_workspaces",
            agency_id="agency-a",
            sort_field="contact_email",
        ),
        "An unallowlisted sort field was accepted.",
    )
    await expect_async_validation_error(
        repository.find_agency_records(
            collection_name="passenger_workspaces",
            agency_id="agency-a",
            projection=["contact_email"],
        ),
        "An unsafe projection was accepted.",
    )
    await expect_async_validation_error(
        repository.find_agency_records(
            collection_name="passenger_workspaces",
            agency_id="agency-a",
            sort_direction="sideways",
        ),
        "An unsupported sort direction was accepted.",
    )
    if await repository.count_agency_records(collection_name="passenger_workspaces", agency_id="agency-a") != 2:
        raise AssertionError("Tenant-scoped count included another agency.")
    await expect_async_validation_error(
        repository.find_global_records(collection_name="passenger_workspaces"),
        "The global helper accessed a tenant-owned collection.",
    )
    await expect_async_validation_error(
        repository.find_agency_records(collection_name="airline_profiles", agency_id="agency-a"),
        "The agency helper accessed a platform-global collection.",
    )
    platform_page = await repository.find_platform_records(
        collection_name="passenger_workspaces",
        sort_field="updated_at",
        pagination=PaginationRequest.build(limit=10),
    )
    if {item["agency_id"] for item in platform_page.items} != {"agency-a", "agency-b"}:
        raise AssertionError("Governed platform visibility did not preserve existing cross-agency access.")

    for record in (
        {"id": "queue-global", "agency_id": None, "queue_code": "triage", "updated_at": created_at},
        {"id": "queue-agency", "agency_id": "agency-a", "queue_code": "triage", "updated_at": created_at},
    ):
        await db.collection("operational_queue_definitions").insert_one(record)
    mixed = await repository.find_mixed_records(
        collection_name="operational_queue_definitions",
        agency_id="agency-a",
        identity_field="queue_code",
        pagination=PaginationRequest.build(limit=10),
    )
    if len(mixed.items) != 1 or mixed.items[0]["id"] != "queue-agency":
        raise AssertionError("Mixed projection precedence did not prefer the agency override.")

    diagnostics = json.dumps(query_diagnostic_records(), sort_keys=True)
    if "private-a@example.test" in diagnostics or "contact_email" in diagnostics:
        raise AssertionError("Query diagnostics leaked filter or passenger values.")


def verify_contracts_and_registration() -> None:
    settings = get_settings()
    if settings.query_default_limit != 50 or settings.query_maximum_limit != 250:
        raise AssertionError("Canonical pagination defaults are not configured as expected.")
    if PaginationRequest.build(limit=MAXIMUM_QUERY_LIMIT + 500).limit != settings.query_maximum_limit:
        raise AssertionError("Excessive pagination limit was not capped consistently.")
    expect_validation_error(lambda: PaginationRequest.build(limit=0), "Zero limit was accepted.")
    expect_validation_error(lambda: PaginationRequest.build(offset=-1), "Negative offset was accepted.")
    if not COLLECTION_OWNERSHIP_REGISTRY or not GOVERNED_INDEX_SPECS:
        raise AssertionError("Collection ownership or governed index registry is empty.")
    index_names = [item["name"] for item in GOVERNED_INDEX_SPECS]
    if len(index_names) != len(set(index_names)):
        raise AssertionError("Governed index names are not unique.")
    database_text = (BACKEND / "database.py").read_text(encoding="utf-8")
    if "drop_index(" in database_text or "drop_indexes(" in database_text:
        raise AssertionError("Destructive automatic index changes were introduced.")
    server_text = (BACKEND / "server.py").read_text(encoding="utf-8")
    if "@bounded_query_context(READINESS_QUERY_LIMIT)" not in server_text or "asyncio.wait_for" not in server_text:
        raise AssertionError("Detailed readiness is not bounded and timeout controlled.")
    readiness = persistence_readiness_metadata()
    required_true = (
        "bounded_query_helpers_enabled",
        "tenant_scoped_repository_enabled",
        "platform_global_repository_enabled",
        "pagination_contract_enabled",
        "deterministic_sorting_enabled",
        "sort_allowlist_enabled",
        "filter_operator_allowlist_enabled",
        "tenant_override_prevention_enabled",
        "collection_ownership_registry_enabled",
        "index_governance_enabled",
        "readiness_queries_bounded",
        "destructive_index_changes_disabled",
        "cross_tenant_querying_disabled",
    )
    if any(readiness.get(key) is not True for key in required_true) or readiness.get("readiness_required") is not False:
        raise AssertionError(f"Persistence readiness metadata is incomplete: {readiness}")
    if "frontend/src/pages" in "\n".join(str(path) for path in ROOT.glob("frontend/src/pages/**/*Persistence*")):
        raise AssertionError("This infrastructure phase introduced a product page.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--static", action="store_true", help="Retained for CI tier compatibility; the smoke uses disposable in-memory data in both modes.")
    parser.parse_args()
    if not phase_is_exact(CURRENT_BUILD_PHASE, RELEASE_PHASE):
        raise AssertionError(f"Canonical phase marker mismatch: {CURRENT_BUILD_PHASE}")
    verify_contracts_and_registration()
    asyncio.run(verify_repository_foundation())
    print("Phase 56.5.6 persistence scalability and tenant query hardening foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
