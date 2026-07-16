#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from persistence_query import (
    COLLECTION_OWNERSHIP_REGISTRY,
    GOVERNED_INDEX_SPECS,
    CollectionOwnershipType,
)
from database import AGENCY_OWNED_COLLECTIONS


MIGRATED_LIST_SERVICES = (
    "passenger_workspace_service.py",
    "travel_request_workspace_service.py",
    "trip_workspace_service.py",
    "offer_workspace_service.py",
    "booking_workspace_service.py",
    "document_workspace_service.py",
    "timeline_workspace_service.py",
    "agent_work_queue_service.py",
    "airline_service_coverage_gap_service.py",
    "airline_intelligence_scale_readiness_service.py",
    "canonical_journey_itinerary_service.py",
    "journey_option_fare_brand_composition_service.py",
)


def find_many_counts() -> tuple[int, int]:
    total = 0
    zero_argument = 0
    for path in BACKEND.rglob("*.py"):
        if "scripts" in path.parts or "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute) or node.func.attr != "find_many":
                continue
            total += 1
            if not node.args and not node.keywords:
                zero_argument += 1
    return total, zero_argument


def bounded_without_sort() -> list[str]:
    findings: list[str] = []
    for path in BACKEND.rglob("*.py"):
        if "scripts" in path.parts or "__pycache__" in path.parts or path.name == "database.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute) or node.func.attr != "find_many":
                continue
            keywords = {item.arg for item in node.keywords if item.arg}
            if "limit" in keywords and "sort" not in keywords:
                findings.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    return findings


def validate() -> tuple[dict[str, int], list[str]]:
    errors: list[str] = []
    exception_path = Path(__file__).with_name("persistence_query_legacy_exceptions.json")
    exceptions = json.loads(exception_path.read_text(encoding="utf-8"))
    total, zero_argument = find_many_counts()
    if total > exceptions["production_find_many_call_ceiling"]:
        errors.append("Production find_many call count exceeded the documented legacy ceiling.")
    if zero_argument > exceptions["production_zero_argument_find_many_ceiling"]:
        errors.append("Zero-argument find_many count exceeded the documented legacy ceiling.")
    unsorted_bounded = bounded_without_sort()
    if unsorted_bounded:
        errors.append(f"Bounded find_many calls without deterministic sort: {unsorted_bounded}")

    direct_find = []
    for path in BACKEND.rglob("*.py"):
        if path.name == "database.py" or "scripts" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if ".collection.find(" in text or ".to_list(length=None" in text.replace(" ", ""):
            direct_find.append(str(path.relative_to(ROOT)))
    if direct_find:
        errors.append(f"Direct risky Mongo access found outside database adapter: {direct_find}")

    for name, ownership in COLLECTION_OWNERSHIP_REGISTRY.items():
        if ownership.collection_name != name:
            errors.append(f"Ownership registry key mismatch for {name}.")
        if ownership.default_sort not in ownership.allowed_sort_fields:
            errors.append(f"Default sort is not allowlisted for {name}.")
        if ownership.ownership in {
            CollectionOwnershipType.AGENCY_OWNED,
            CollectionOwnershipType.IMMUTABLE_SNAPSHOT,
            CollectionOwnershipType.AUDIT_SECURITY,
            CollectionOwnershipType.OPERATIONAL_EPHEMERAL,
        } and ownership.tenant_field != "agency_id":
            errors.append(f"Tenant-owned registry entry {name} lacks agency_id ownership.")
        if ownership.ownership in {
            CollectionOwnershipType.AGENCY_OWNED,
            CollectionOwnershipType.IMMUTABLE_SNAPSHOT,
            CollectionOwnershipType.AUDIT_SECURITY,
            CollectionOwnershipType.OPERATIONAL_EPHEMERAL,
        } and name not in AGENCY_OWNED_COLLECTIONS:
            errors.append(f"Tenant-owned registry entry is absent from the database collection registry: {name}.")

    names: set[str] = set()
    for spec in GOVERNED_INDEX_SPECS:
        if spec["name"] in names:
            errors.append(f"Duplicate governed index name: {spec['name']}")
        names.add(spec["name"])
        if spec["collection"] not in COLLECTION_OWNERSHIP_REGISTRY:
            errors.append(f"Governed index collection is not registered: {spec['collection']}")
        ownership = COLLECTION_OWNERSHIP_REGISTRY.get(spec["collection"])
        if ownership and spec["name"] not in ownership.recommended_indexes:
            errors.append(f"Governed index is absent from collection ownership recommendations: {spec['name']}")
        if ownership and ownership.tenant_field and ownership.ownership is not CollectionOwnershipType.MIXED_PROJECTION:
            if not spec["keys"] or spec["keys"][0][0] != ownership.tenant_field:
                errors.append(f"Tenant index does not begin with {ownership.tenant_field}: {spec['name']}")

    database_text = (BACKEND / "database.py").read_text(encoding="utf-8")
    if "drop_index(" in database_text or "drop_indexes(" in database_text:
        errors.append("Automatic index dropping is present in the database startup path.")
    server_text = (BACKEND / "server.py").read_text(encoding="utf-8")
    for token in ("@bounded_query_context(READINESS_QUERY_LIMIT)", "asyncio.wait_for", "readiness_database_timeout_seconds"):
        if token not in server_text:
            errors.append(f"Detailed readiness bounding is missing {token!r}.")

    for service_name in MIGRATED_LIST_SERVICES:
        text = (BACKEND / "services" / service_name).read_text(encoding="utf-8")
        if "PersistenceRepository" not in text:
            errors.append(f"Migrated service does not use the governed repository: {service_name}")

    return {
        "production_find_many_calls": total,
        "production_zero_argument_find_many_calls": zero_argument,
        "registered_collections": len(COLLECTION_OWNERSHIP_REGISTRY),
        "governed_indexes": len(GOVERNED_INDEX_SPECS),
        "migrated_list_services": len(MIGRATED_LIST_SERVICES),
    }, errors


def main() -> int:
    summary, errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("Persistence query foundation validation passed: " + json.dumps(summary, sort_keys=True))
    print("Static validation is a guardrail and does not replace runtime tenant-isolation tests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
