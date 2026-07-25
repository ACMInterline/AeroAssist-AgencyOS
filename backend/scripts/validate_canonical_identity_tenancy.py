#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from phase_assertions import assert_application_phase_at_least  # noqa: E402
from services.authorization_service import (  # noqa: E402
    AGENCY_ROLE_PERMISSIONS,
    PERMISSIONS,
    PLATFORM_ROLE_PERMISSIONS,
    PORTAL_IDENTITY_PERMISSIONS,
)


MINIMUM_PHASE = "phase_59_0_product_experience_recovery"
REQUIRED_PERMISSIONS = {
    "manage_platform",
    "manage_agencies",
    "manage_platform_users",
    "manage_agency_users",
    "view_airline_knowledge",
    "edit_airline_knowledge",
    "view_clients",
    "edit_clients",
    "view_passengers",
    "edit_passengers",
    "view_requests",
    "edit_requests",
    "view_offers",
    "edit_offers",
    "view_trips",
    "edit_trips",
    "view_bookings",
    "edit_bookings",
    "view_tickets_emds",
    "edit_tickets_emds",
    "view_documents",
    "edit_documents",
    "view_tasks",
    "edit_tasks",
    "view_finance",
    "edit_finance",
    "edit_commercial_ledger",
    "view_supplier_costs",
    "view_margins",
    "view_audit",
    "manage_settings",
    "portal_view_client",
    "portal_view_passenger",
}
REQUIRED_MODELS = {
    "AuthIdentity",
    "AuthSession",
    "PlatformUser",
    "AgencyStaffMembership",
    "PortalAccessMapping",
    "PortalAccessMappingCreate",
    "PortalAccessMappingRevoke",
    "ClientProfile",
    "PassengerProfile",
    "ClientPassengerRelationship",
}
REQUIRED_DOCS = (
    "docs/architecture/canonical-identity-and-tenancy-contract.md",
    "docs/architecture/portal-identity-linkage-contract.md",
    "docs/architecture/canonical-domain-ownership-map.md",
    "docs/architecture/canonical-domain-migration-register.md",
)


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def declared_classes(relative: str) -> set[str]:
    tree = ast.parse(source(relative))
    return {node.name for node in tree.body if isinstance(node, ast.ClassDef)}


def require_markers(relative: str, markers: tuple[str, ...], errors: list[str]) -> None:
    text = source(relative)
    for marker in markers:
        if marker not in text:
            errors.append(f"{relative}: missing {marker!r}")


def main() -> int:
    errors: list[str] = []

    assert_application_phase_at_least(
        MINIMUM_PHASE,
        MINIMUM_PHASE,
        source="canonical identity contract",
    )
    missing_permissions = REQUIRED_PERMISSIONS - set(PERMISSIONS)
    if missing_permissions:
        errors.append(f"Permission vocabulary is incomplete: {sorted(missing_permissions)}")
    if {"view_supplier_costs", "view_margins"} & set(
        AGENCY_ROLE_PERMISSIONS["agency_agent"]
    ):
        errors.append("Agency Agent can view supplier costs or margins.")
    if (
        "view_finance" not in AGENCY_ROLE_PERMISSIONS["agency_agent"]
        or "edit_finance" not in AGENCY_ROLE_PERMISSIONS["agency_agent"]
        or "edit_commercial_ledger"
        in AGENCY_ROLE_PERMISSIONS["agency_agent"]
    ):
        errors.append(
            "Agency Agent after-sales access is missing or ledger mutation is allowed."
        )
    if not all(
        "edit_airline_knowledge" in AGENCY_ROLE_PERMISSIONS[role]
        for role in ("agency_owner", "agency_admin", "agency_agent")
    ):
        errors.append("Agency operational roles lost established airline knowledge editing.")
    if any(
        permission.startswith("edit_")
        for permission in AGENCY_ROLE_PERMISSIONS["agency_readonly"]
    ):
        errors.append("Agency Read-only has mutation permissions.")
    if AGENCY_ROLE_PERMISSIONS["agency_accountant"] - {
        "view_clients",
        "view_passengers",
        "view_bookings",
        "view_tickets_emds",
        "view_documents",
        "view_tasks",
        "view_finance",
        "edit_finance",
        "edit_commercial_ledger",
        "view_supplier_costs",
        "view_margins",
    }:
        errors.append("Agency Accountant exceeds the reviewed finance context.")
    if PLATFORM_ROLE_PERMISSIONS["platform_knowledge_editor"] != {
        "view_airline_knowledge",
        "edit_airline_knowledge",
    }:
        errors.append("Platform Knowledge Editor permission scope is not exact.")
    if PORTAL_IDENTITY_PERMISSIONS != {
        "client_portal": frozenset({"portal_view_client"}),
        "passenger_portal": frozenset({"portal_view_passenger"}),
    }:
        errors.append("Portal identity permission scopes are not isolated.")

    missing_models = REQUIRED_MODELS - declared_classes("backend/models.py")
    if missing_models:
        errors.append(f"Canonical identity models are missing: {sorted(missing_models)}")

    require_markers(
        "backend/models.py",
        (
            'PASSENGER_PORTAL = "passenger_portal"',
            "auth_identity_id",
            "subject_type",
            "client_profile_id",
            "passenger_profile_id",
            "active_mapping_key",
            "active_subject_key",
            "linkage_version",
            "replaces_mapping_id",
        ),
        errors,
    )
    require_markers(
        "backend/services/authorization_service.py",
        (
            "require_active_membership",
            "authorize_staff_request",
            "agency_request_permission",
            "platform_request_permission",
            "project_authorized_commercial_fields",
            "require_commercial_field_permissions",
            "platform_role_agency_override_disabled",
        ),
        errors,
    )
    require_markers(
        "backend/services/portal_identity_link_service.py",
        (
            "Your portal account is not linked to a profile yet.",
            "create_portal_mapping",
            "revoke_portal_mapping",
            "resolve_portal_identity_context",
            "auth_identity_id",
            "Replacement predecessor must be explicitly revoked first.",
            "portal_mapping.legacy_invitation_activated",
            '"authorization_by_email": False',
        ),
        errors,
    )
    portal_service = source("backend/services/portal_identity_link_service.py")
    portal_router = source("backend/routers/portal.py")
    auth_source = source("backend/auth.py")
    if 'find_one({"user_email"' in portal_service or 'find_many({"user_email"' in portal_service:
        errors.append("Portal service still authorizes through email lookup.")
    if 'find_one({"user_email"' in portal_router or 'find_many({"user_email"' in portal_router:
        errors.append("Portal router still authorizes through email lookup.")
    if '"portal_access_mappings").find_one' in auth_source:
        errors.append("Current-user resolution bypasses the explicit Portal link service.")
    if (
        'staff_identity = identity.get("identity_type") in {"platform_user", "agency_staff"}'
        not in auth_source
        or "await resolve_staff_user(db, identity) if staff_identity else None"
        not in auth_source
    ):
        errors.append("Current-user resolution permits non-staff identities to enter staff compatibility lookup.")

    tenant_source = source("backend/services/tenant_service.py")
    for function_name in ("assert_agency_access", "require_any_agency_role"):
        tree = ast.parse(tenant_source)
        function = next(
            (
                node
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == function_name
            ),
            None,
        )
        if function is None:
            errors.append(f"Tenant helper {function_name} is missing.")
            continue
        function_text = ast.get_source_segment(tenant_source, function) or ""
        if "global_role" in function_text or "platform_override" in function_text:
            errors.append(f"{function_name} retains a Platform Agency bypass.")

    database_source = source("backend/database.py")
    require_markers(
        "backend/database.py",
        (
            "portal_access_mappings_active_identity_unique",
            "portal_access_mappings_active_subject_unique",
            "portal_access_mappings_identity_status_lookup",
            "portal_access_mappings_client_subject_lookup",
            "portal_access_mappings_passenger_subject_lookup",
            '"active_mapping_key": {"$type": "string"}',
            '"active_subject_key": {"$type": "string"}',
        ),
        errors,
    )
    if (
        '"keys": [("agency_id", ASCENDING), ("user_email", ASCENDING)]'
        in database_source
    ):
        errors.append("Startup still requests the legacy email-authority index.")

    require_markers(
        "backend/server.py",
        (
            "portal_access_mappings.router",
            '"canonical_identity_tenancy_contract"',
            "identity_tenancy_readiness_metadata()",
        ),
        errors,
    )
    require_markers(
        "backend/services/identity_tenancy_migration_service.py",
        (
            "writes_performed",
            "dry_run",
            "email_match_is_authoritative",
            "cross_agency",
            "ambiguous",
            "active_membership_without_active_identity",
            "legacy_active_portal_profile_without_active_mapping",
            "duplicate_active_portal_subject_mapping",
        ),
        errors,
    )
    require_markers(
        "backend/services/client_passenger_master_service.py",
        (
            "_require_canonical_source",
            "_reject_duplicate_projection",
            "_guard_unlinked_compatibility_update",
            "canonical_source_projection",
            "Active or invited legacy Portal metadata requires an explicit PortalAccessMapping source.",
        ),
        errors,
    )
    require_markers(
        "backend/routers/auth.py",
        (
            "Existing identity type is incompatible with this invitation.",
            'portal_types = {"client_portal", "passenger_portal"}',
        ),
        errors,
    )
    require_markers(
        "backend/routers/agencies.py",
        (
            "An active staff AuthIdentity is required.",
            '{"identity_id": identity["id"]}',
            'identity_id=identity["id"]',
        ),
        errors,
    )
    require_markers(
        "backend/scripts/create_first_platform_owner.py",
        ('identity_id=created_identity["id"]',),
        errors,
    )
    for relative in (
        "backend/routers/platform_client_passenger_master.py",
        "backend/routers/agency_client_passenger_master.py",
    ):
        router_source = source(relative)
        if "require_permission" not in router_source:
            errors.append(f"{relative}: compatibility routes do not use the central permission resolver.")
        if "PLATFORM_ROLES" in router_source or "require_any_agency_role" in router_source:
            errors.append(f"{relative}: compatibility routes retain direct role-list authorization.")
    require_markers(
        "backend/routers/agency_journey_option_composition.py",
        (
            "permission_projected_service",
            'require_permission(user, "view_offers")',
            'require_permission(user, "edit_offers")',
            "require_commercial_field_permissions(payload, user)",
        ),
        errors,
    )
    journey_router = source(
        "backend/routers/agency_journey_option_composition.py"
    )
    if (
        "READ_ROLES" in journey_router
        or "WRITE_ROLES" in journey_router
        or "PLATFORM_ROLES" in journey_router
        or "require_any_agency_role" in journey_router
    ):
        errors.append(
            "Agency Journey Option Composition retains direct role-list authorization."
        )
    require_markers(
        "backend/routers/agency_offer_builder.py",
        (
            "offer_builder_service",
            "offer_comparison_service",
            'require_permission(user, "view_offers")',
            'require_permission(user, "edit_offers")',
            'require_commercial_field_permissions(payload.model_dump(mode="json"), user)',
        ),
        errors,
    )
    offer_builder_router = source("backend/routers/agency_offer_builder.py")
    if (
        "READ_ROLES" in offer_builder_router
        or "WRITE_ROLES" in offer_builder_router
        or "require_any_agency_role" in offer_builder_router
    ):
        errors.append(
            "Agency Offer Builder retains direct role-list authorization."
        )
    migration_cli = source("backend/scripts/analyze_identity_tenancy_migration.py")
    migration_service = source(
        "backend/services/identity_tenancy_migration_service.py"
    )
    if (
        "--apply" not in migration_cli
        or "intentionally unavailable" not in migration_cli.lower()
        or "if apply:" not in migration_service
        or "Write mode is intentionally unavailable" not in migration_service
    ):
        errors.append("Migration CLI does not explicitly reject write mode.")

    require_markers(
        "frontend/src/App.jsx",
        ("AuthorizationProvider", "AuthorizationBoundary"),
        errors,
    )
    require_markers(
        "frontend/src/context/AuthorizationContext.jsx",
        (
            "/api/auth/me",
            "Your portal account is not linked to a profile yet.",
            "agency_memberships",
            "subject_type",
            'pathname.startsWith("/agency")',
            "scopedPermissions",
        ),
        errors,
    )
    require_markers(
        "frontend/src/pages/agency/JourneyOptionCompositionWorkspacePage.jsx",
        (
            'authorization.hasPermission("view_supplier_costs")',
            'authorization.hasPermission("view_margins")',
            "Supplier cost and margin details remain restricted",
        ),
        errors,
    )
    require_markers(
        "frontend/src/pages/agency/OfferBuilderPage.jsx",
        (
            "useAuthorization",
            'authorization.hasPermission("view_margins")',
            "pricingLineTypes",
        ),
        errors,
    )

    for relative in REQUIRED_DOCS:
        if not (ROOT / relative).is_file():
            errors.append(f"Required contract document is missing: {relative}")
    serialized_docs = "\n".join(source(relative) for relative in REQUIRED_DOCS)
    for marker in (
        "agency_id",
        "workspace_id",
        "AuthIdentity",
        "PortalAccessMapping",
        "PassengerProfile",
        "ClientProfile",
        "email",
        "dry-run",
    ):
        if marker not in serialized_docs:
            errors.append(f"Identity documentation is missing {marker!r}.")

    inventory = json.loads(source("backend/scripts/smoke_inventory.json"))
    scripts = {item["script_path"] for item in inventory.get("scripts", [])}
    focused_smoke = "backend/scripts/smoke_canonical_identity_tenancy_contract.py"
    if focused_smoke not in scripts:
        errors.append("Focused identity/tenancy smoke is not inventoried.")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(
        "Canonical identity and tenancy source validation passed: role permissions, "
        "strict agency membership, explicit Portal links, additive partial indexes, "
        "dry-run migration safety, frontend context, routes, readiness, and docs verified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
