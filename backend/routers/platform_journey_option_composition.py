from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.journey_option_fare_brand_composition_service import PHASE_LABEL, JourneyOptionCompositionError, JourneyOptionFareBrandCompositionService


router = APIRouter(prefix="/api/platform/journey-option-compositions", tags=["platform-journey-option-compositions"])
PLATFORM_ROLES = {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}


def require_platform(user: dict) -> None:
    if user.get("global_role") not in PLATFORM_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform access is required.")


@router.get("")
async def dashboard(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    return await JourneyOptionFareBrandCompositionService(db).dashboard()


@router.get("/summary")
async def summary(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    service = JourneyOptionFareBrandCompositionService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summarize_readiness(), "read_only": True, **service.safety_flags()}


@router.get("/filters")
async def filters(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    service = JourneyOptionFareBrandCompositionService(db)
    return {"phase": PHASE_LABEL, "filters": service.filters(), "read_only": True, **service.safety_flags()}


@router.get("/comparison-dimensions")
async def comparison_dimensions(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    service = JourneyOptionFareBrandCompositionService(db)
    return {"phase": PHASE_LABEL, "items": service.filters()["comparison_dimensions"], "read_only": True, **service.safety_flags()}


@router.get("/validation-codes")
async def validation_codes(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    service = JourneyOptionFareBrandCompositionService(db)
    return {"phase": PHASE_LABEL, "items": service.filters()["validation_codes"], "read_only": True, **service.safety_flags()}


@router.get("/compositions")
async def compositions(
    agency_id: str | None = Query(default=None),
    composition_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    require_platform(user)
    service = JourneyOptionFareBrandCompositionService(db)
    items = await service.list_compositions(agency_id, status=composition_status, include_archived=True)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), "read_only": True, **service.safety_flags()}


@router.get("/compositions/{composition_id}")
async def composition_detail(composition_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    record = await db.collection("journey_option_compositions").find_one({"id": composition_id})
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey option composition was not found.")
    try:
        detail = await JourneyOptionFareBrandCompositionService(db).get_composition(str(record["agency_id"]), composition_id)
        return {**detail, "read_only": True, "platform_governance_view": True}
    except JourneyOptionCompositionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
