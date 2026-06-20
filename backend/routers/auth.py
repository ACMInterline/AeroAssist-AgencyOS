from fastapi import APIRouter, Depends

from auth import get_current_user
from database import Database, get_database
from models import DemoLoginRequest
from services.seed_service import seed_core_data

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me")
async def read_me(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    memberships = await db.collection("agency_staff_memberships").find_many({"user_id": user["id"]})
    return {"user": user, "memberships": memberships}


@router.post("/demo-login")
async def demo_login(payload: DemoLoginRequest, db: Database = Depends(get_database)) -> dict:
    await seed_core_data(db)
    user = await db.collection("platform_users").find_one({"email": payload.email})
    if user is None:
        return {
            "ok": False,
            "message": "Demo user not found. Seed core data and retry.",
        }
    return {
        "ok": True,
        "message": "Demo login uses the X-Demo-User-Email header in development.",
        "demo_header": {"X-Demo-User-Email": user["email"]},
        "user": user,
    }
