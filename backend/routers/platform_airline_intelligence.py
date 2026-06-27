from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import AirlineIntelligenceProfileCreate, AirlineIntelligenceProfileUpdate
from services.airline_intelligence_service import AirlineIntelligenceService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-intelligence", tags=["platform-airline-intelligence"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


def clean_updates(payload: Any) -> dict:
    return payload.model_dump(mode="json", exclude_unset=True)


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


@router.get("/airlines")
async def list_airline_intelligence_airlines(
    search: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AirlineIntelligenceService(db)
    return {"items": await service.list_airlines(search), "actor_user_id": user["id"]}


@router.get("/airlines/{airline_id}")
async def get_airline_intelligence_airline(
    airline_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AirlineIntelligenceService(db)
    profile = await service.get_profile(airline_id)
    airline = await service.get_airline_record(airline_id)
    if profile is None and airline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Airline intelligence profile not found.")
    return {"airline": airline, "profile": profile, "actor_user_id": user["id"]}


@router.post("/airlines", status_code=status.HTTP_201_CREATED)
async def create_airline_intelligence_airline(
    payload: AirlineIntelligenceProfileCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    service = AirlineIntelligenceService(db)
    profile = await service.create_profile(payload, user["id"])
    return {"profile": profile, "actor_user_id": user["id"]}


@router.put("/airlines/{airline_id}")
async def update_airline_intelligence_airline(
    airline_id: str,
    payload: AirlineIntelligenceProfileUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    service = AirlineIntelligenceService(db)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    updated = await service.update_profile(airline_id, payload, user["id"])
    if updated is None:
        create_payload = AirlineIntelligenceProfileCreate(**{**updates, "airline_id": updates.get("airline_id") or airline_id})
        updated = await service.create_profile(create_payload, user["id"])
    return {"profile": updated, "actor_user_id": user["id"]}
