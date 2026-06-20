from typing import Iterable

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


def forbidden(message: str = "You do not have access to this resource.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)


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
