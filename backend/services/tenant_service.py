from typing import Any, Iterable, Mapping, Sequence

from fastapi import HTTPException, status

from database import Database
from services.portal_identity_link_service import (
    PortalIdentityLinkError,
    resolve_portal_identity_context,
)


PLATFORM_ROLE_ORDER = {
    "platform_support": 1,
    "platform_knowledge_editor": 2,
    "platform_admin": 3,
    "platform_owner": 4,
}

AGENCY_ROLE_ORDER = {
    "agency_readonly": 1,
    "agency_accountant": 2,
    "agency_agent": 3,
    "agency_admin": 4,
    "agency_owner": 5,
}

INTERNAL_PORTAL_FIELDS = {
    "agency_id",
    "created_by_user_id",
    "assigned_user_id",
    "actor_user_id",
    "internal_notes",
    "internal_warning",
    "reconciliation_notes",
    "airline_knowledge",
    "medical_notes_internal",
    "travel_document_notes",
    "passport_number",
    "sent_snapshot",
    "booking_snapshot",
    "source_snapshot",
    "metadata",
}


def forbidden(message: str = "You do not have access to this resource.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)


def not_found(message: str = "Resource not found.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


async def get_membership(db: Database, agency_id: str, user_id: str) -> dict:
    membership = await db.collection("agency_staff_memberships").find_one(
        {"agency_id": agency_id, "user_id": user_id}
    )
    if membership is None or membership.get("status") != "active":
        raise forbidden("Active agency membership is required.")
    return membership


async def assert_agency_access(db: Database, agency_id: str, user: dict) -> dict:
    agency = await db.collection("agencies").find_one({"id": agency_id})
    if agency is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")

    await get_membership(db, agency_id, user["id"])
    return agency


async def require_agency_context(db: Database, agency_id: str, user: dict) -> dict:
    agency = await assert_agency_access(db, agency_id, user)
    membership = await db.collection("agency_staff_memberships").find_one(
        {"agency_id": agency_id, "user_id": user["id"]}
    )
    return {"agency_id": agency_id, "agency": agency, "membership": membership, "user": user}


def filter_by_agency(agency_id: str, extra_filters: Mapping[str, Any] | None = None) -> dict:
    filters = {"agency_id": agency_id}
    if extra_filters:
        filters.update({key: value for key, value in extra_filters.items() if value is not None})
    return filters


def assert_agency_record(record: Mapping[str, Any] | None, agency_id: str, message: str = "Resource not found.") -> Mapping[str, Any]:
    if not record:
        raise not_found(message)
    if record.get("agency_id") != agency_id:
        raise not_found(message)
    return record


def deny_cross_agency_access(record: Mapping[str, Any] | None, agency_id: str, message: str = "Resource not found.") -> Mapping[str, Any]:
    return assert_agency_record(record, agency_id, message)


async def require_any_platform_role(user: dict, allowed_roles: Iterable[str]) -> None:
    if user.get("global_role") not in set(allowed_roles):
        raise forbidden("Required platform role is missing.")


async def require_any_agency_role(db: Database, agency_id: str, user: dict, allowed_roles: Iterable[str]) -> dict:
    membership = await get_membership(db, agency_id, user["id"])
    if membership.get("agency_role") not in set(allowed_roles):
        raise forbidden("Required agency role is missing.")
    return membership


async def portal_client_context(db: Database, auth_identity_id: str) -> dict:
    try:
        context = await resolve_portal_identity_context(db, auth_identity_id)
    except PortalIdentityLinkError as exc:
        raise forbidden(str(exc)) from exc
    if not context or context.get("subject_type") != "client":
        raise forbidden("Client portal mapping is required.")
    return context


async def assert_portal_owns_client_record(db: Database, ctx: dict, collection_name: str, record_id: str, message: str = "Portal resource not found.") -> dict:
    if ctx.get("subject_type") != "client":
        raise forbidden("Client portal mapping is required.")
    record = await db.collection(collection_name).find_one(
        {
            "agency_id": ctx["account"]["agency_id"],
            "client_id": ctx["account"].get("client_profile_id") or ctx["account"].get("client_id"),
            "id": record_id,
        }
    )
    if not record:
        raise not_found(message)
    return record


async def assert_portal_can_view_passenger(db: Database, ctx: dict, passenger_id: str) -> dict:
    if ctx.get("subject_type") == "passenger":
        linked_passenger_id = ctx["account"].get("passenger_profile_id")
        if linked_passenger_id != passenger_id:
            raise not_found("Portal passenger not found.")
        passenger = await db.collection("passenger_profiles").find_one(
            {"agency_id": ctx["account"]["agency_id"], "id": linked_passenger_id}
        )
        if not passenger or passenger.get("status") == "archived":
            raise not_found("Portal passenger not found.")
        return {"passenger": passenger, "relationship": None}
    relationship = await db.collection("client_passenger_relationships").find_one(
        {
            "agency_id": ctx["account"]["agency_id"],
            "client_id": ctx["account"].get("client_profile_id") or ctx["account"].get("client_id"),
            "passenger_id": passenger_id,
            "status": "active",
            "can_view": True,
        }
    )
    if not relationship:
        raise not_found("Portal passenger not found.")
    passenger = await db.collection("passenger_profiles").find_one(
        {"agency_id": ctx["account"]["agency_id"], "id": passenger_id}
    )
    if not passenger or passenger.get("status") == "archived":
        raise not_found("Portal passenger not found.")
    return {"passenger": passenger, "relationship": relationship}


def safe_public_projection(record: Mapping[str, Any], allowed_fields: Sequence[str]) -> dict:
    projected = {field: record.get(field) for field in allowed_fields if field in record}
    leaked = sorted(set(projected).intersection(INTERNAL_PORTAL_FIELDS))
    if leaked:
        raise RuntimeError(f"Unsafe portal projection includes internal fields: {', '.join(leaked)}")
    return projected


def assert_portal_projection_safe(payload: Any) -> None:
    if isinstance(payload, Mapping):
        leaked = sorted(set(payload).intersection(INTERNAL_PORTAL_FIELDS))
        if leaked:
            raise RuntimeError(f"Unsafe portal payload includes internal fields: {', '.join(leaked)}")
        for value in payload.values():
            assert_portal_projection_safe(value)
    elif isinstance(payload, list):
        for value in payload:
            assert_portal_projection_safe(value)
