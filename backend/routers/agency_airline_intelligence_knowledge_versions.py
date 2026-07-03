from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import Database, get_database
from services.airline_intelligence_knowledge_version_service import AirlineIntelligenceKnowledgeVersionService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/airline-intelligence-knowledge-versions", tags=["agency-airline-intelligence-knowledge-versions"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


@router.get("/summary")
async def get_agency_airline_intelligence_knowledge_version_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await AirlineIntelligenceKnowledgeVersionService(db).agency_summary(agency_id)


@router.get("/current")
async def get_agency_current_airline_intelligence_knowledge_version(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    detail = await AirlineIntelligenceKnowledgeVersionService(db).agency_current_version(agency_id)
    return detail or {
        "version": None,
        "items": [],
        "read_only": True,
        "payloads_hidden": True,
        "plain_language_overview": "No current airline intelligence knowledge version is visible for this agency yet.",
    }


@router.get("/preview")
async def get_agency_preview_airline_intelligence_knowledge_version(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    detail = await AirlineIntelligenceKnowledgeVersionService(db).agency_preview_version(agency_id)
    return detail or {
        "version": None,
        "items": [],
        "read_only": True,
        "payloads_hidden": True,
        "plain_language_overview": "No preview airline intelligence knowledge version is assigned to this agency yet.",
    }


@router.get("/versions")
async def list_agency_airline_intelligence_knowledge_versions(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return {
        "items": await AirlineIntelligenceKnowledgeVersionService(db).agency_versions(agency_id),
        "read_only": True,
        "payloads_hidden": True,
    }


@router.get("/versions/{version_id}")
async def get_agency_airline_intelligence_knowledge_version(
    agency_id: str,
    version_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    detail = await AirlineIntelligenceKnowledgeVersionService(db).get_version(version_id, agency_view=True)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Airline intelligence knowledge version not found.")
    if detail.get("version", {}).get("agency_visibility_mode") not in {"visible", "preview"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Airline intelligence knowledge version not visible for agency users.")
    return detail
