from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import Database, get_database
from services.airline_intelligence_data_pack_review_service import AirlineIntelligenceDataPackReviewService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/airline-intelligence-data-pack-reviews", tags=["agency-airline-intelligence-data-pack-reviews"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


@router.get("/summary")
async def get_agency_airline_intelligence_data_pack_review_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await AirlineIntelligenceDataPackReviewService(db).agency_summary()


@router.get("/coverage")
async def get_agency_airline_intelligence_data_pack_review_coverage(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await AirlineIntelligenceDataPackReviewService(db).agency_coverage()


@router.get("/reviews")
async def list_agency_airline_intelligence_data_pack_reviews(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return {
        "items": await AirlineIntelligenceDataPackReviewService(db).list_reviews(agency_view=True),
        "read_only": True,
        "payloads_hidden": True,
    }


@router.get("/reviews/{review_id}")
async def get_agency_airline_intelligence_data_pack_review(
    agency_id: str,
    review_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    detail = await AirlineIntelligenceDataPackReviewService(db).get_review(review_id, agency_view=True)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Airline intelligence data pack review not found.")
    return detail


@router.get("/packs/{pack_id}/promotion-readiness")
async def get_agency_airline_intelligence_data_pack_promotion_readiness(
    agency_id: str,
    pack_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    service = AirlineIntelligenceDataPackReviewService(db)
    readiness = await service.list_promotion_readiness(pack_id=pack_id)
    return {
        "items": [service._agency_readiness(item) for item in readiness],
        "read_only": True,
        "payloads_hidden": True,
    }
