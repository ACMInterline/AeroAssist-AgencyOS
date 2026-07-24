from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException, Request, status

from database import Database
from persistence_query import MAXIMUM_QUERY_LIMIT, PaginationRequest
from persistence_repository import PersistenceRepository


PERMISSIONS: tuple[str, ...] = (
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
)

_ALL_PLATFORM = frozenset(PERMISSIONS) - {
    "portal_view_client",
    "portal_view_passenger",
}
_AGENCY_OPERATIONAL_VIEW = {
    "view_clients",
    "view_passengers",
    "view_requests",
    "view_offers",
    "view_trips",
    "view_bookings",
    "view_tickets_emds",
    "view_documents",
    "view_tasks",
    "view_airline_knowledge",
}
_AGENCY_OPERATIONAL_EDIT = {
    "edit_airline_knowledge",
    "edit_clients",
    "edit_passengers",
    "edit_requests",
    "edit_offers",
    "edit_trips",
    "edit_bookings",
    "edit_tickets_emds",
    "edit_documents",
    "edit_tasks",
}

PLATFORM_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "platform_owner": _ALL_PLATFORM,
    "platform_admin": _ALL_PLATFORM,
    "platform_knowledge_editor": frozenset(
        {"view_airline_knowledge", "edit_airline_knowledge"}
    ),
    "platform_support": frozenset(
        {
            "view_airline_knowledge",
            "manage_agencies",
        }
    ),
}

AGENCY_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "agency_owner": frozenset(
        _AGENCY_OPERATIONAL_VIEW
        | _AGENCY_OPERATIONAL_EDIT
        | {
            "manage_agency_users",
            "view_finance",
            "edit_finance",
            "edit_commercial_ledger",
            "view_supplier_costs",
            "view_margins",
            "view_audit",
            "manage_settings",
        }
    ),
    "agency_admin": frozenset(
        _AGENCY_OPERATIONAL_VIEW
        | _AGENCY_OPERATIONAL_EDIT
        | {
            "manage_agency_users",
            "view_finance",
            "edit_finance",
            "edit_commercial_ledger",
            "view_supplier_costs",
            "view_margins",
            "view_audit",
            "manage_settings",
        }
    ),
    "agency_agent": frozenset(
        _AGENCY_OPERATIONAL_VIEW
        | _AGENCY_OPERATIONAL_EDIT
        | {"view_finance", "edit_finance"}
    ),
    "agency_accountant": frozenset(
        {
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
        }
    ),
    "agency_readonly": frozenset(_AGENCY_OPERATIONAL_VIEW | {"view_finance"}),
}

PORTAL_IDENTITY_PERMISSIONS: dict[str, frozenset[str]] = {
    "client_portal": frozenset({"portal_view_client"}),
    "passenger_portal": frozenset({"portal_view_passenger"}),
}

_COMMERCIAL_FIELD_PERMISSIONS: dict[str, str] = {
    "supplier_amount": "view_supplier_costs",
    "supplier_cost": "view_supplier_costs",
    "supplier_costs": "view_supplier_costs",
    "internal_cost": "view_supplier_costs",
    "net_cost": "view_supplier_costs",
    "cost_price": "view_supplier_costs",
    "markup_amount": "view_margins",
    "markup_percentage": "view_margins",
    "margin": "view_margins",
    "margin_amount": "view_margins",
    "margin_percentage": "view_margins",
    "gross_margin": "view_margins",
    "net_margin": "view_margins",
    "commission": "view_margins",
    "commission_amount": "view_margins",
    "commission_percentage": "view_margins",
}
_COMMERCIAL_RECORD_PERMISSIONS: dict[str, str] = {
    "commission": "view_margins",
    "margin": "view_margins",
    "markup": "view_margins",
    "supplier_cost": "view_supplier_costs",
    "internal_cost": "view_supplier_costs",
    "net_cost": "view_supplier_costs",
}
_REDACTED = object()

AGENCY_PATH_PATTERN = re.compile(r"^/api/agencies/(?P<agency_id>[^/]+)(?:/|$)")

_PLATFORM_RESOURCE_PERMISSIONS: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (("/api/platform/agencies",), "manage_agencies", "manage_agencies"),
    (("/api/platform/users", "/api/platform/invitations"), "manage_platform_users", "manage_platform_users"),
    (
        (
            "/api/platform/airline",
            "/api/platform/knowledge",
            "/api/platform/policy",
            "/api/platform/reference",
            "/api/platform/capabilit",
            "/api/platform/service-parameter",
            "/api/platform/operational-constraint",
            "/api/platform/operational-evaluation",
            "/api/platform/passenger-service-feasibility",
            "/api/platform/pricing-formula",
            "/api/platform/visual-policy",
            "/api/platform/operational-rule",
            "/api/platform/scenario",
        ),
        "view_airline_knowledge",
        "edit_airline_knowledge",
    ),
)

_AGENCY_RESOURCE_PERMISSIONS: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (
        (
            "clients",
            "client-master",
            "client-passenger-links",
            "client-portal-access-profiles",
        ),
        "view_clients",
        "edit_clients",
    ),
    (
        (
            "passengers",
            "passenger-master",
            "passenger-workspaces",
            "passenger-services",
            "passenger-service-history",
            "passenger-operational-preferences",
            "passenger-known-documents",
        ),
        "view_passengers",
        "edit_passengers",
    ),
    (("requests", "request-", "travel-request"), "view_requests", "edit_requests"),
    (("offers", "offer-", "journey-option", "journey-comparison"), "view_offers", "edit_offers"),
    (("trips", "trip-", "journeys", "journey-authoring"), "view_trips", "edit_trips"),
    (("bookings", "booking-", "gds-parser"), "view_bookings", "edit_bookings"),
    (("tickets", "ticket-", "emds", "emd-"), "view_tickets_emds", "edit_tickets_emds"),
    (("documents", "document-"), "view_documents", "edit_documents"),
    (("invoices", "payments", "finance"), "view_finance", "edit_commercial_ledger"),
    (("refund", "after-sales"), "view_finance", "edit_finance"),
    (("tasks", "work-queue", "deadlines", "workflow", "timeline", "operational-collaboration"), "view_tasks", "edit_tasks"),
    (("audit-events",), "view_audit", "view_audit"),
    (("staff", "portal-access-mappings"), "manage_agency_users", "manage_agency_users"),
    (("settings", "branding", "onboarding", "saas-subscription"), "manage_settings", "manage_settings"),
    (("airline", "policy", "knowledge", "reference"), "view_airline_knowledge", "edit_airline_knowledge"),
)


def platform_permissions(role: str | None) -> frozenset[str]:
    return PLATFORM_ROLE_PERMISSIONS.get(str(role or ""), frozenset())


def agency_permissions(role: str | None) -> frozenset[str]:
    return AGENCY_ROLE_PERMISSIONS.get(str(role or ""), frozenset())


def portal_permissions(identity_type: str | None) -> frozenset[str]:
    return PORTAL_IDENTITY_PERMISSIONS.get(str(identity_type or ""), frozenset())


def has_permission(principal: Mapping[str, Any] | None, permission: str) -> bool:
    return permission in set((principal or {}).get("_permissions") or ())


def require_permission(
    principal: Mapping[str, Any] | None,
    permission: str,
    message: str = "Required permission is missing.",
) -> None:
    if not has_permission(principal, permission):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)


def project_authorized_commercial_fields(
    value: Any,
    principal: Mapping[str, Any] | None,
) -> Any:
    def project(item: Any) -> Any:
        if isinstance(item, list):
            projected_items = [project(nested) for nested in item]
            return [
                nested
                for nested in projected_items
                if nested is not _REDACTED
            ]
        if isinstance(item, tuple):
            projected_items = [project(nested) for nested in item]
            return tuple(
                nested
                for nested in projected_items
                if nested is not _REDACTED
            )
        if not isinstance(item, Mapping):
            return item

        record_type = str(
            item.get("line_type")
            or item.get("pricing_line_type")
            or item.get("amount_category")
            or ""
        ).lower()
        record_permission = _COMMERCIAL_RECORD_PERMISSIONS.get(record_type)
        if record_permission and not has_permission(principal, record_permission):
            return _REDACTED

        projected: dict[str, Any] = {}
        for key, nested in item.items():
            required_permission = _COMMERCIAL_FIELD_PERMISSIONS.get(str(key).lower())
            if required_permission and not has_permission(principal, required_permission):
                continue
            projected_nested = project(nested)
            if projected_nested is not _REDACTED:
                projected[str(key)] = projected_nested
        return projected

    result = project(value)
    return None if result is _REDACTED else result


def require_commercial_field_permissions(
    value: Any,
    principal: Mapping[str, Any] | None,
) -> None:
    missing: set[str] = set()

    def inspect(item: Any) -> None:
        if isinstance(item, Mapping):
            record_type = str(
                item.get("line_type")
                or item.get("pricing_line_type")
                or item.get("amount_category")
                or ""
            ).lower()
            record_permission = _COMMERCIAL_RECORD_PERMISSIONS.get(record_type)
            if record_permission and not has_permission(principal, record_permission):
                missing.add(record_permission)
            for key, nested in item.items():
                required_permission = _COMMERCIAL_FIELD_PERMISSIONS.get(
                    str(key).lower()
                )
                if required_permission and not has_permission(
                    principal, required_permission
                ):
                    missing.add(required_permission)
                inspect(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                inspect(nested)

    inspect(value)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Protected commercial fields require: "
                + ", ".join(sorted(missing))
                + "."
            ),
        )


def safe_platform_user(user: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not user:
        return None
    return {
        key: user.get(key)
        for key in (
            "id",
            "identity_id",
            "email",
            "full_name",
            "global_role",
            "status",
            "created_at",
            "updated_at",
        )
        if key in user
    }


def safe_membership(membership: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: membership.get(key)
        for key in (
            "id",
            "agency_id",
            "workspace_id",
            "user_id",
            "identity_id",
            "agency_role",
            "status",
            "joined_at",
            "created_at",
            "updated_at",
        )
        if key in membership
    }


async def resolve_staff_user(db: Database, identity: Mapping[str, Any]) -> dict[str, Any] | None:
    identity_id = str(identity.get("id") or "")
    user = (
        await db.collection("platform_users").find_one({"identity_id": identity_id})
        if identity_id
        else None
    )
    if user:
        return user
    # Compatibility lookup for pre-contract staff records. Email never resolves
    # portal scope and may be removed after the dry-run reconciliation is clean.
    email = identity.get("email")
    return (
        await db.collection("platform_users").find_one({"email": email})
        if email
        else None
    )


async def active_memberships(
    db: Database,
    user: Mapping[str, Any],
    identity: Mapping[str, Any],
) -> list[dict[str, Any]]:
    page = await PersistenceRepository(db).find_platform_records(
        collection_name="agency_staff_memberships",
        filters={"user_id": user["id"], "status": "active"},
        sort_field="created_at",
        sort_direction="asc",
        pagination=PaginationRequest.build(limit=MAXIMUM_QUERY_LIMIT),
    )
    identity_id = identity.get("id")
    return [
        item
        for item in page.items
        if not item.get("identity_id") or item.get("identity_id") == identity_id
    ]


async def require_active_membership(
    db: Database,
    agency_id: str,
    user: Mapping[str, Any],
    identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    membership = await db.collection("agency_staff_memberships").find_one(
        {"agency_id": agency_id, "user_id": user["id"], "status": "active"}
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active agency membership is required.",
        )
    if (
        identity
        and membership.get("identity_id")
        and membership["identity_id"] != identity.get("id")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agency membership does not belong to this identity.",
        )
    return membership


def agency_request_permission(path: str, method: str) -> str | None:
    match = AGENCY_PATH_PATTERN.match(path)
    if not match:
        return None
    tail = path[match.end() :].lower()
    # Policy comparison writes Agency-local analysis artifacts, not canonical
    # airline knowledge. Endpoint write guards still restrict saved metadata.
    if tail.startswith("policy-comparison/") or tail == "policy-comparison":
        return "view_airline_knowledge"
    mutating = method.upper() not in {"GET", "HEAD", "OPTIONS"}
    for markers, read_permission, write_permission in _AGENCY_RESOURCE_PERMISSIONS:
        if any(marker in tail for marker in markers):
            return write_permission if mutating else read_permission
    return "edit_tasks" if mutating else "view_tasks"


def platform_request_permission(path: str, method: str) -> str:
    mutating = method.upper() not in {"GET", "HEAD", "OPTIONS"}
    lowered = path.lower()
    for markers, read_permission, write_permission in _PLATFORM_RESOURCE_PERMISSIONS:
        if any(lowered.startswith(marker) for marker in markers):
            return write_permission if mutating else read_permission
    return "manage_platform"


async def authorize_staff_request(
    request: Request,
    db: Database,
    identity: Mapping[str, Any],
    user: dict[str, Any],
) -> dict[str, Any]:
    path = request.url.path
    if path.startswith("/api/platform"):
        permissions = platform_permissions(user.get("global_role"))
        required = platform_request_permission(path, request.method)
        if required not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Platform permission {required} is required.",
            )
        user["_permissions"] = sorted(permissions)
        user["_identity_id"] = identity.get("id")
        request.state.authorization = {
            "scope": "platform",
            "required_permission": required,
            "permissions": tuple(sorted(permissions)),
        }
        return user

    match = AGENCY_PATH_PATTERN.match(path)
    if match:
        agency_id = match.group("agency_id")
        membership = await require_active_membership(db, agency_id, user, identity)
        permissions = agency_permissions(membership.get("agency_role"))
        required = agency_request_permission(path, request.method)
        if required and required not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission {required} is required.",
            )
        user["_permissions"] = sorted(permissions)
        user["_identity_id"] = identity.get("id")
        user["_agency_membership"] = membership
        request.state.authorization = {
            "scope": "agency",
            "agency_id": agency_id,
            "membership_id": membership.get("id"),
            "permissions": tuple(sorted(permissions)),
        }
        return user

    permissions = platform_permissions(user.get("global_role"))
    user["_permissions"] = sorted(permissions)
    user["_identity_id"] = identity.get("id")
    return user


def identity_tenancy_readiness_metadata() -> dict[str, Any]:
    return {
        "canonical_identity_and_tenancy_contract_enabled": True,
        "agency_id_sole_authorization_tenant_boundary": True,
        "workspace_id_authorization_disabled": True,
        "central_permission_vocabulary_enabled": True,
        "active_membership_rechecked_per_request": True,
        "platform_role_agency_override_disabled": True,
        "explicit_portal_identity_mapping_enabled": True,
        "email_authoritative_portal_access_disabled": True,
        "client_and_passenger_portal_subjects_supported": True,
        "legacy_identity_compatibility_lookup_enabled": True,
        "legacy_master_writes_deprecated": True,
        "migration_analysis_dry_run_only": True,
        "readiness_required": False,
    }
