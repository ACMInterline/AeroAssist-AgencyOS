from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AirlineIntelligenceAgencyConsumptionNoteCreateRequest,
    AirlineIntelligenceAgencyConsumptionProfileCreateRequest,
    AirlineIntelligenceAgencyConsumptionProfileUpdateRequest,
    AirlineIntelligenceAgencyConsumptionSnapshotCreateRequest,
    AirlineIntelligenceAgencyUsageReadinessRequest,
)
from services.airline_intelligence_agency_consumption_service import AirlineIntelligenceAgencyConsumptionService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-intelligence-agency-consumption", tags=["platform-airline-intelligence-agency-consumption"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get("/summary")
async def get_platform_airline_intelligence_agency_consumption_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineIntelligenceAgencyConsumptionService(db).platform_summary()


@router.get("/profiles")
async def list_platform_airline_intelligence_agency_consumption_profiles(
    agency_id: str | None = Query(default=None),
    knowledge_version_id: str | None = Query(default=None),
    profile_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceAgencyConsumptionService(db).list_profiles(
            agency_id=agency_id,
            knowledge_version_id=knowledge_version_id,
            status=profile_status,
        ),
        "metadata_only": True,
    }


@router.post("/profiles", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_agency_consumption_profile(
    payload: AirlineIntelligenceAgencyConsumptionProfileCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceAgencyConsumptionService(db).create_profile(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/profiles/{profile_id}")
async def get_platform_airline_intelligence_agency_consumption_profile(
    profile_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    profile = await AirlineIntelligenceAgencyConsumptionService(db).get_profile(profile_id)
    if not profile:
        raise not_found("Airline intelligence agency consumption profile not found.")
    return {"profile": profile, "metadata_only": True}


@router.patch("/profiles/{profile_id}")
async def update_platform_airline_intelligence_agency_consumption_profile(
    profile_id: str,
    payload: AirlineIntelligenceAgencyConsumptionProfileUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceAgencyConsumptionService(db).update_profile(profile_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/agencies/{agency_id}/assignments")
async def list_platform_airline_intelligence_agency_consumption_assignments(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceAgencyConsumptionService(db).list_agency_visible_assignments(agency_id),
        "metadata_only": True,
        "payloads_hidden": True,
    }


@router.get("/agencies/{agency_id}/usage-readiness")
async def list_platform_airline_intelligence_agency_usage_readiness(
    agency_id: str,
    usage_area: str | None = Query(default=None),
    profile_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceAgencyConsumptionService(db).list_usage_readiness(
            agency_id=agency_id,
            profile_id=profile_id,
            usage_area=usage_area,
        ),
        "metadata_only": True,
    }


@router.post("/agencies/{agency_id}/usage-readiness", status_code=status.HTTP_201_CREATED)
async def calculate_platform_airline_intelligence_agency_usage_readiness(
    agency_id: str,
    payload: AirlineIntelligenceAgencyUsageReadinessRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceAgencyConsumptionService(db).calculate_usage_readiness(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/notes")
async def list_platform_airline_intelligence_agency_consumption_notes(
    agency_id: str | None = Query(default=None),
    profile_id: str | None = Query(default=None),
    visible_to_agency: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceAgencyConsumptionService(db).list_notes(
            agency_id=agency_id,
            profile_id=profile_id,
            visible_to_agency=visible_to_agency,
        ),
        "metadata_only": True,
    }


@router.post("/notes", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_agency_consumption_note(
    payload: AirlineIntelligenceAgencyConsumptionNoteCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceAgencyConsumptionService(db).create_note(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/snapshots")
async def list_platform_airline_intelligence_agency_consumption_snapshots(
    agency_id: str | None = Query(default=None),
    profile_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceAgencyConsumptionService(db).list_snapshots(agency_id=agency_id, profile_id=profile_id),
        "metadata_only": True,
    }


@router.post("/snapshots", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_agency_consumption_snapshot(
    payload: AirlineIntelligenceAgencyConsumptionSnapshotCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceAgencyConsumptionService(db).create_snapshot(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
