from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import IntelligentOfferBuilderPackageCreate, IntelligentOfferBuilderPackageUpdate
from services.intelligent_offer_builder_service import (
    IntelligentOfferBuilderError,
    IntelligentOfferBuilderService,
    PHASE_LABEL,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/offer-intelligence", tags=["agency-offer-intelligence"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]
PLATFORM_ROLES = {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_agency_offer_intelligence_packages(
    agency_id: str,
    package_status: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    recommendation_level: str | None = Query(default=None),
    readiness_status: str | None = Query(default=None),
    operational_risk: str | None = Query(default=None),
    passenger_need: str | None = Query(default=None),
    destination: str | None = Query(default=None),
    travel_date: str | None = Query(default=None),
    offer_workspace: str | None = Query(default=None),
    client_visibility_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await IntelligentOfferBuilderService(db).agency_response(
        agency_id,
        package_status=package_status,
        airline=airline,
        recommendation_level=recommendation_level,
        readiness_status=readiness_status,
        operational_risk=operational_risk,
        passenger_need=passenger_need,
        destination=destination,
        travel_date=travel_date,
        offer_workspace=offer_workspace,
        client_visibility_status=client_visibility_status,
    )


@router.get("/summary")
async def summarize_agency_offer_intelligence_packages(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await IntelligentOfferBuilderService(db).agency_summary(agency_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_intelligence_package(
    agency_id: str,
    payload: IntelligentOfferBuilderPackageCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await IntelligentOfferBuilderService(db).create_package(payload, user, agency_id=agency_id)
    except IntelligentOfferBuilderError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{package_id}")
async def get_agency_offer_intelligence_package(
    agency_id: str,
    package_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = IntelligentOfferBuilderService(db)
    try:
        package = await service.get_agency_package(agency_id, package_id)
    except IntelligentOfferBuilderError:
        raise not_found("Offer intelligence package metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "intelligent_offer_builder_package": package,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{package_id}")
async def update_agency_offer_intelligence_package(
    agency_id: str,
    package_id: str,
    payload: IntelligentOfferBuilderPackageUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await IntelligentOfferBuilderService(db).update_package(package_id, payload, user, agency_id=agency_id)
    except IntelligentOfferBuilderError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{package_id}")
async def archive_agency_offer_intelligence_package(
    agency_id: str,
    package_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await IntelligentOfferBuilderService(db).archive_package(package_id, user, agency_id=agency_id)
    except IntelligentOfferBuilderError as exc:
        raise bad_request(str(exc)) from exc
