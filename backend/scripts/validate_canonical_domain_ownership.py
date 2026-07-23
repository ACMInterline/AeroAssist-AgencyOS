#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from canonical_domain_ownership import (  # noqa: E402
    CANONICAL_DOMAIN_OWNERSHIP_REGISTRY,
    CLASSIFICATIONS,
    PRODUCT_KERNEL_LIFECYCLE,
    REQUIRED_DOMAIN_KEYS,
    TENANT_BOUNDARY_DECISION,
)
from scripts.validate_smoke_inventory import validate_inventory  # noqa: E402


WRITE_METHODS = {
    "insert_one",
    "insert_many",
    "update_one",
    "update_many",
    "replace_one",
    "delete_one",
    "delete_many",
    "upsert",
}
PROTECTED_GOVERNANCE_FILES = {
    "backend/database.py",
    "backend/persistence_query.py",
    "backend/persistence_repository.py",
    "backend/server.py",
}
ALLOWED_ROUTE_ROOTS = (
    "/api/auth",
    "/api/platform",
    "/api/agencies",
    "/api/agencies/{agency_id}",
    "/api/portal",
    "/api/reference",
)
SECRET_OR_LOCAL_PATTERNS = (
    re.compile(r"mongodb(?:\+srv)?://", re.IGNORECASE),
    re.compile(r"(?:password|secret|token|api[_-]?key)\s*[:=]\s*[\"'][^\"']+", re.IGNORECASE),
    re.compile(r"/Users/"),
    re.compile(r"[A-Za-z]:\\\\Users\\\\"),
    re.compile(r"/home/[^/\s]+/"),
)


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _module_string_constants(tree: ast.Module) -> dict[str, str]:
    constants: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                constants[target.id] = value.value
    return constants


def _scan_collection_writers() -> dict[str, set[str]]:
    writers: dict[str, set[str]] = defaultdict(set)
    for path in BACKEND.rglob("*.py"):
        if "scripts" in path.parts or path.name in {
            "canonical_domain_ownership.py",
            "database.py",
            "models.py",
            "persistence_query.py",
        }:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        constants = _module_string_constants(tree)

        def resolve_collection(node: ast.AST) -> str | None:
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                return node.value
            if isinstance(node, ast.Name):
                return constants.get(node.id)
            return None

        bindings: dict[str, str] = {}
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Attribute)
                and value.func.attr == "collection"
                and value.args
            ):
                collection_name = resolve_collection(value.args[0])
                if collection_name:
                    for target in targets:
                        bindings[_dotted_name(target)] = collection_name

        for node in ast.walk(tree):
            if (
                not isinstance(node, ast.Call)
                or not isinstance(node.func, ast.Attribute)
                or node.func.attr not in WRITE_METHODS
            ):
                continue
            receiver = node.func.value
            collection_name: str | None = None
            if (
                isinstance(receiver, ast.Call)
                and isinstance(receiver.func, ast.Attribute)
                and receiver.func.attr == "collection"
                and receiver.args
            ):
                collection_name = resolve_collection(receiver.args[0])
            else:
                collection_name = bindings.get(_dotted_name(receiver))
            if collection_name:
                writers[collection_name].add(str(path.relative_to(ROOT)))
    return writers


def _persistence_registered_collections() -> set[str]:
    source = (BACKEND / "database.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    registered: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        target_names = {_dotted_name(target) for target in targets}
        if "AGENCY_OWNED_COLLECTIONS" in target_names and isinstance(node.value, (ast.List, ast.Tuple)):
            for item in node.value.elts:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    registered.add(item.value)
        if target_names.intersection({"unique_indexes", "compound_indexes"}) and isinstance(node.value, ast.Dict):
            for key in node.value.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    registered.add(key.value)

    persistence_tree = ast.parse((BACKEND / "persistence_query.py").read_text(encoding="utf-8"))
    for node in ast.walk(persistence_tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        if isinstance(node.func, ast.Name) and node.func.id in {"_agency", "_ownership"}:
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                registered.add(first.value)
    return registered


def _changed_paths() -> set[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    changed: set[str] = set()
    for line in result.stdout.splitlines():
        value = line[3:].strip()
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        if value:
            changed.add(value)
    return changed


def validate_registry() -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    records = list(CANONICAL_DOMAIN_OWNERSHIP_REGISTRY)
    keys = [record["domain_key"] for record in records]
    if tuple(keys) != REQUIRED_DOMAIN_KEYS:
        errors.append("Required domains are missing, duplicated, or not in deterministic contract order.")
    if len(set(keys)) != len(keys):
        errors.append("Domain keys are not unique.")

    artifact_classes: dict[str, str] = {}
    artifact_domains: dict[str, set[str]] = defaultdict(set)
    model_names: set[str] = set()
    collection_artifacts: set[str] = set()
    for record in records:
        key = record["domain_key"]
        decision_required = record["decision_status"] == "decision_required"
        if decision_required:
            if record["target_write_owner"] is not None:
                errors.append(f"{key}: decision_required domain must not name a target write owner.")
        elif not record["target_write_owner"]:
            errors.append(f"{key}: selected domain lacks a target write owner.")
        if record["decision_status"] not in {"selected", "decision_required"}:
            errors.append(f"{key}: unsupported decision status {record['decision_status']!r}.")
        if decision_required and not record["migration_required"]:
            errors.append(f"{key}: unresolved ownership must be migration_required.")

        tenant = record.get("tenant_contract") or {}
        required_tenant_fields = {
            "scope",
            "tenant_key",
            "ownership_rules",
            "portal_visibility",
            "required_actor_fields",
            "created_by_field",
            "updated_by_field",
            "immutable_tenant_fields",
        }
        missing_tenant_fields = required_tenant_fields - set(tenant)
        if missing_tenant_fields:
            errors.append(f"{key}: tenant contract missing {sorted(missing_tenant_fields)}.")
        if record.get("portal_visibility") != tenant.get("portal_visibility") or not record.get("portal_visibility"):
            errors.append(f"{key}: portal visibility is not explicitly classified.")
        if tenant.get("tenant_key") and tenant["tenant_key"] not in set(tenant.get("immutable_tenant_fields") or ()):
            errors.append(f"{key}: tenant key is not immutable.")

        workspace_is_target = bool(
            record.get("canonical_model")
            and (
                record["canonical_model"].endswith("Workspace")
                or any(
                    artifact["name"] == record["canonical_model"]
                    and artifact["classification"] == "operational_workspace"
                    for artifact in record["artifacts"]
                )
            )
        )
        if workspace_is_target and not record.get("workspace_owner_justification"):
            errors.append(f"{key}: workspace target lacks an explicit ownership justification.")

        has_compatibility_artifact = False
        for artifact in record.get("artifacts") or ():
            artifact_id = artifact.get("artifact_id")
            classification = artifact.get("classification")
            if not artifact_id or classification not in CLASSIFICATIONS:
                errors.append(f"{key}: artifact has an invalid stable ID or classification.")
                continue
            prior = artifact_classes.get(artifact_id)
            if prior and prior != classification:
                errors.append(
                    f"{key}: {artifact_id} is classified as both {prior} and {classification}."
                )
            artifact_classes[artifact_id] = classification
            artifact_domains[artifact_id].add(key)
            source = ROOT / artifact["source_file"]
            if not source.is_file():
                errors.append(f"{key}: artifact source does not exist: {artifact['source_file']}.")
            if artifact["kind"] == "model":
                model_names.add(artifact["name"])
            if artifact["kind"] == "collection":
                collection_artifacts.add(artifact["name"])
            if classification == "compatibility_writer":
                has_compatibility_artifact = True
            if (
                classification == "immutable_snapshot"
                and artifact["name"] == record.get("canonical_model")
                and record.get("target_write_owner")
                and "creation only" not in record["target_write_owner"]
            ):
                errors.append(f"{key}: immutable snapshot is presented as a mutable target owner.")
            if (
                classification == "deprecated"
                and artifact["name"] == record.get("canonical_model")
            ):
                errors.append(f"{key}: deprecated model is named as the canonical target.")
        if has_compatibility_artifact and not record.get("compatibility_writers"):
            errors.append(f"{key}: compatibility writer artifacts are not listed in the contract.")
        if record.get("compatibility_writers") and not record.get("migration_required"):
            errors.append(f"{key}: compatibility writers require migration_required.")
        if not record.get("frontend_consumers"):
            errors.append(f"{key}: no primary frontend consumer is represented.")
        for frontend_path in record.get("frontend_consumers") or ():
            if not (ROOT / frontend_path).is_file():
                errors.append(f"{key}: frontend consumer does not exist: {frontend_path}.")
        for owner in (
            *record.get("current_write_owners", ()),
            *record.get("demo_or_test_writers", ()),
        ):
            if not (ROOT / owner).is_file():
                errors.append(f"{key}: writer source does not exist: {owner}.")

    model_tree = ast.parse((BACKEND / "models.py").read_text(encoding="utf-8"))
    declared_models = {
        node.name
        for node in model_tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for model_name in sorted(model_names - declared_models):
        errors.append(f"Model artifact is not declared in backend/models.py: {model_name}.")

    persistence_collections = _persistence_registered_collections()
    for collection_name in sorted(collection_artifacts - persistence_collections):
        errors.append(f"Collection lacks existing persistence ownership/index registration: {collection_name}.")

    detected_writers = _scan_collection_writers()
    for record in records:
        collection_name = record.get("canonical_collection")
        if not collection_name:
            continue
        represented = set(record.get("current_write_owners") or ())
        missing_writers = detected_writers.get(collection_name, set()) - represented
        if missing_writers:
            errors.append(
                f"{record['domain_key']}: active writers are not represented: "
                + ", ".join(sorted(missing_writers))
            )

    lifecycle_domains = {item["domain_key"] for item in PRODUCT_KERNEL_LIFECYCLE}
    required_continuity = {
        "request",
        "offer",
        "accepted_offer_snapshot",
        "trip",
        "booking_pnr",
        "ticket",
        "invoice",
        "document",
        "client_portal_identity",
    }
    if not required_continuity.issubset(lifecycle_domains):
        errors.append("The Request-to-Portal lifecycle contract is incomplete.")

    for record in records:
        route = record.get("canonical_route_family")
        if not route or not route.startswith("/"):
            continue
        route_parts = tuple(part.strip() for part in route.split(" and "))
        for route_part in route_parts:
            if route_part.startswith("/") and not route_part.startswith(ALLOWED_ROUTE_ROOTS):
                errors.append(f"{record['domain_key']}: non-canonical route family {route_part!r}.")
            if route_part.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
                errors.append(f"{record['domain_key']}: forbidden parallel route root {route_part!r}.")

    serialized = json.dumps(records, sort_keys=True, separators=(",", ":"), default=str)
    if serialized != json.dumps(records, sort_keys=True, separators=(",", ":"), default=str):
        errors.append("Registry serialization is not deterministic.")
    for pattern in SECRET_OR_LOCAL_PATTERNS:
        if pattern.search(serialized):
            errors.append(f"Registry contains a secret-like or local-only value matching {pattern.pattern!r}.")

    if TENANT_BOUNDARY_DECISION.get("decision") != "agency_id_is_canonical_workspace_boundary":
        errors.append("Tenant boundary decision is unresolved or inconsistent.")
    if TENANT_BOUNDARY_DECISION.get("migration_required") is not False:
        errors.append("Registry unexpectedly requires workspace_id tenant migration.")

    changed = _changed_paths()
    protected_changes = sorted(PROTECTED_GOVERNANCE_FILES.intersection(changed))
    if protected_changes:
        errors.append(
            "Corrective ownership work modified existing runtime/persistence governance: "
            + ", ".join(protected_changes)
        )

    smoke_summary, smoke_errors = validate_inventory()
    if smoke_errors:
        errors.extend(f"Smoke inventory: {error}" for error in smoke_errors)

    migration_domains = [record for record in records if record["migration_required"]]
    blockers = [
        {
            "domain_key": record["domain_key"],
            "blockers": list(record.get("blockers") or ()),
        }
        for record in migration_domains
    ]
    summary = {
        "registered_domain_count": len(records),
        "selected_owner_count": sum(record["decision_status"] == "selected" for record in records),
        "decision_required_count": sum(record["decision_status"] == "decision_required" for record in records),
        "migration_required_count": len(migration_domains),
        "classified_artifact_count": len(artifact_classes),
        "persistence_registered_collection_count": len(persistence_collections),
        "smoke_inventory_count": smoke_summary["inventoried_smoke_scripts"],
        "tenant_boundary_decision": TENANT_BOUNDARY_DECISION["decision"],
        "kernel_status": "migration_required" if migration_domains else "canonical",
        "migration_blockers": blockers,
    }
    return summary, errors


def main() -> int:
    summary, errors = validate_registry()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(
        "Canonical domain ownership validation passed: "
        f"{summary['registered_domain_count']} domains, "
        f"{summary['selected_owner_count']} selected, "
        f"{summary['decision_required_count']} decision-required, "
        f"{summary['classified_artifact_count']} classified artifacts."
    )
    print(
        "Tenant boundary: "
        f"{summary['tenant_boundary_decision']}; "
        f"product kernel status: {summary['kernel_status']}."
    )
    print(
        "Migration blockers remain in "
        f"{summary['migration_required_count']} domains; "
        "the registry is valid and does not claim migration readiness."
    )
    for item in summary["migration_blockers"]:
        reasons = "; ".join(item["blockers"]) or "compatibility reconciliation required"
        print(f"MIGRATION_REQUIRED {item['domain_key']}: {reasons}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
