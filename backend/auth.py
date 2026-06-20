from typing import Callable, Iterable, Optional

from fastapi import Depends, Header, HTTPException, status

from database import Database, get_database
from services.seed_service import DEMO_OWNER_EMAIL, seed_core_data
from services.tenant_service import assert_agency_access, require_any_agency_role, require_any_platform_role


async def get_current_user(
    x_demo_user_email: Optional[str] = Header(default=None),
    db: Database = Depends(get_database),
) -> dict:
    await seed_core_data(db)
    email = x_demo_user_email or DEMO_OWNER_EMAIL
    user = await db.collection("platform_users").find_one({"email": email})
    if user is None or user.get("status") != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Active demo user not found.")
    return user


def require_platform_role(roles: Iterable[str]) -> Callable:
    async def dependency(user: dict = Depends(get_current_user)) -> dict:
        await require_any_platform_role(user, roles)
        return user

    return dependency


def require_agency_role(agency_id_param: str, roles: Iterable[str]) -> Callable:
    async def dependency(
        db: Database = Depends(get_database),
        user: dict = Depends(get_current_user),
        agency_id: str = "",
    ) -> dict:
        target_agency_id = agency_id or agency_id_param
        return await require_any_agency_role(db, target_agency_id, user, roles)

    return dependency


async def get_current_agency_context(
    agency_id: str,
    db: Database = Depends(get_database),
    user: dict = Depends(get_current_user),
) -> dict:
    agency = await assert_agency_access(db, agency_id, user)
    membership = await db.collection("agency_staff_memberships").find_one(
        {"agency_id": agency_id, "user_id": user["id"]}
    )
    return {
        "agency": agency,
        "membership": membership,
        "user": user,
    }
