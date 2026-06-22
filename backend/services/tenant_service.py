from typing import Any, Iterable, Mapping, Sequence

from fastapi import HTTPException, status

from database import Database


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

    if user.get("global_role") in {"platform_owner", "platform_admin", "platform_support"}:
        return agency

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
    if user.get("global_role") in {"platform_owner", "platform_admin"}:
        agency = await db.collection("agencies").find_one({"id": agency_id})
        if agency is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")
        return {"agency_role": "platform_override", "agency_id": agency_id, "user_id": user["id"]}

    membership = await get_membership(db, agency_id, user["id"])
    if membership.get("agency_role") not in set(allowed_roles):
        raise forbidden("Required agency role is missing.")
    return membership


async def portal_client_context(db: Database, user_email: str) -> dict:
    mapping = await db.collection("portal_access_mappings").find_one({"user_email": user_email})
    if not mapping or mapping.get("portal_status") != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Active demo portal account not found.")
    agency_id = mapping["agency_id"]
    agency = await db.collection("agencies").find_one({"id": agency_id})
    client = await db.collection("client_profiles").find_one(
        {"agency_id": agency_id, "id": mapping["client_id"]}
    )
    if not agency or not client or client.get("status") == "archived":
        raise not_found("Portal client context not found.")
    workspace = await db.collection("agency_workspaces").find_one({"agency_id": agency_id})
    return {"account": mapping, "agency": agency, "workspace": workspace, "client": client}


async def assert_portal_owns_client_record(db: Database, ctx: dict, collection_name: str, record_id: str, message: str = "Portal resource not found.") -> dict:
    record = await db.collection(collection_name).find_one(
        {
            "agency_id": ctx["account"]["agency_id"],
            "client_id": ctx["account"]["client_id"],
            "id": record_id,
        }
    )
    if not record:
        raise not_found(message)
    return record


async def assert_portal_can_view_passenger(db: Database, ctx: dict, passenger_id: str) -> dict:
    relationship = await db.collection("client_passenger_relationships").find_one(
        {
            "agency_id": ctx["account"]["agency_id"],
            "client_id": ctx["account"]["client_id"],
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
