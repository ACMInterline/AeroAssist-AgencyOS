from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_intelligence_data_pack_service import AirlineIntelligenceDataPackService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/airline-intelligence-data-packs", tags=["agency-airline-intelligence-data-packs"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


@router.get("/summary")
async def get_agency_airline_intelligence_data_pack_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await AirlineIntelligenceDataPackService(db).agency_summary()


@router.get("/coverage")
async def get_agency_airline_intelligence_coverage(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    service = AirlineIntelligenceDataPackService(db)
    snapshots = await service.list_coverage_snapshots()
    return {
        "coverage_snapshot": snapshots[0] if snapshots else None,
        "recent_snapshots": snapshots[:5],
        "read_only": True,
        "plain_language_overview": "This shows which airline information is available for your agency. It is not a booking, ticketing, pricing, or public publishing tool.",
    }


@router.get("/packs")
async def list_agency_airline_intelligence_data_packs(
    agency_id: str,
    safe_for_agency_display: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    service = AirlineIntelligenceDataPackService(db)
    packs = await service.agency_packs()
    if safe_for_agency_display is not None:
        packs = [pack for pack in packs if pack.get("safe_for_agency_display") is safe_for_agency_display]
    return {
        "items": packs,
        "read_only": True,
        "payloads_hidden": True,
    }


@router.get("/packs/{pack_id}")
async def get_agency_airline_intelligence_data_pack(
    agency_id: str,
    pack_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    detail = await AirlineIntelligenceDataPackService(db).get_pack(pack_id, agency_view=True)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Airline intelligence data pack not found.")
    return {
        **detail,
        "read_only": True,
        "payloads_hidden": True,
    }


@router.get("/packs/{pack_id}/items")
async def list_agency_airline_intelligence_data_pack_items(
    agency_id: str,
    pack_id: str,
    target_domain: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    service = AirlineIntelligenceDataPackService(db)
    items = await service.agency_items(pack_id)
    if target_domain:
        items = [item for item in items if item.get("target_domain") == target_domain]
    return {
        "items": items,
        "read_only": True,
        "payloads_hidden": True,
    }
