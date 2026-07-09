from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import IntelligentOfferBuilderPackageCreate, IntelligentOfferBuilderPackageUpdate
from services.intelligent_offer_builder_service import (
    IntelligentOfferBuilderError,
    IntelligentOfferBuilderService,
    PHASE_LABEL,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/intelligent-offer-builder", tags=["platform-intelligent-offer-builder"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_intelligent_offer_builder_packages(
    agency_id: str | None = Query(default=None),
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
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await IntelligentOfferBuilderService(db).platform_response(
        agency_id=agency_id,
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
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_intelligent_offer_builder_packages(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await IntelligentOfferBuilderService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_intelligent_offer_builder_package(
    payload: IntelligentOfferBuilderPackageCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await IntelligentOfferBuilderService(db).create_package(payload, user)
    except IntelligentOfferBuilderError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{package_id}")
async def get_platform_intelligent_offer_builder_package(
    package_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = IntelligentOfferBuilderService(db)
    try:
        package = await service.get_platform_package(package_id)
    except IntelligentOfferBuilderError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "intelligent_offer_builder_package": package,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{package_id}")
async def update_platform_intelligent_offer_builder_package(
    package_id: str,
    payload: IntelligentOfferBuilderPackageUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await IntelligentOfferBuilderService(db).update_package(package_id, payload, user)
    except IntelligentOfferBuilderError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{package_id}")
async def archive_platform_intelligent_offer_builder_package(
    package_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await IntelligentOfferBuilderService(db).archive_package(package_id, user)
    except IntelligentOfferBuilderError as exc:
        raise bad_request(str(exc)) from exc
