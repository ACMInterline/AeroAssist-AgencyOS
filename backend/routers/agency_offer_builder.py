import inspect
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OfferBuilderSegmentCreate,
    OfferFareBundleCreate,
    OfferOptionCreate,
    OfferOptionUpdate,
    OfferPricingLineCreate,
    OfferRecommendationRequest,
    OfferWorkspaceCreate,
    OfferWorkspaceUpdate,
)
from services.offer_builder_service import OfferBuilderService
from services.offer_comparison_service import OfferComparisonService
from services.authorization_service import (
    project_authorized_commercial_fields,
    require_commercial_field_permissions,
    require_permission,
)


router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["agency-offer-builder"])

async def require_read(_db: Database, _agency_id: str, user: dict) -> None:
    require_permission(user, "view_offers")


async def require_write(_db: Database, _agency_id: str, user: dict) -> None:
    require_permission(user, "edit_offers")


class PermissionProjectedOfferService:
    def __init__(self, service: Any, principal: dict[str, Any]) -> None:
        self._service = service
        self._principal = principal

    def __getattr__(self, name: str) -> Any:
        member = getattr(self._service, name)
        if not inspect.iscoroutinefunction(member):
            return member

        async def projected(*args: Any, **kwargs: Any) -> Any:
            result = await member(*args, **kwargs)
            return project_authorized_commercial_fields(result, self._principal)

        return projected


def offer_builder_service(
    db: Database,
    user: dict[str, Any],
) -> PermissionProjectedOfferService:
    return PermissionProjectedOfferService(OfferBuilderService(db), user)


def offer_comparison_service(
    db: Database,
    user: dict[str, Any],
) -> PermissionProjectedOfferService:
    return PermissionProjectedOfferService(OfferComparisonService(db), user)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.get("/offer-workspaces")
async def list_offer_workspaces(
    agency_id: str,
    request_id: Optional[str] = Query(default=None),
    trip_id: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = offer_builder_service(db, user)
    return {"items": await service.list_workspaces(agency_id, request_id=request_id, trip_id=trip_id, status=status_filter)}


@router.post("/offer-workspaces", status_code=status.HTTP_201_CREATED)
async def create_offer_workspace(
    agency_id: str,
    payload: OfferWorkspaceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    require_commercial_field_permissions(payload.model_dump(mode="json"), user)
    service = offer_builder_service(db, user)
    try:
        workspace = await service.create_workspace(agency_id, payload, user.get("id"))
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {"workspace": workspace}


@router.get("/offer-workspaces/{workspace_id}")
async def get_offer_workspace(
    agency_id: str,
    workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = offer_builder_service(db, user)
    detail = await service.workspace_detail(agency_id, workspace_id)
    if detail is None:
        raise not_found("Offer workspace not found.")
    return detail


@router.put("/offer-workspaces/{workspace_id}")
async def update_offer_workspace(
    agency_id: str,
    workspace_id: str,
    payload: OfferWorkspaceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = offer_builder_service(db, user)
    try:
        workspace = await service.update_workspace(agency_id, workspace_id, payload, user.get("id"))
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    if workspace is None:
        raise not_found("Offer workspace not found.")
    return {"workspace": workspace}


@router.post("/requests/{request_id}/offer-workspace", status_code=status.HTTP_201_CREATED)
async def create_offer_workspace_from_request(
    agency_id: str,
    request_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = offer_builder_service(db, user)
    workspace = await service.create_workspace_from_request(agency_id, request_id, user.get("id"))
    if workspace is None:
        raise not_found("Request not found.")
    return {"workspace": workspace}


@router.post("/trips/{trip_id}/offer-workspace", status_code=status.HTTP_201_CREATED)
async def create_offer_workspace_from_trip(
    agency_id: str,
    trip_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = offer_builder_service(db, user)
    workspace = await service.create_workspace_from_trip(agency_id, trip_id, user.get("id"))
    if workspace is None:
        raise not_found("Trip not found.")
    return {"workspace": workspace}


@router.post("/offer-workspaces/{workspace_id}/options", status_code=status.HTTP_201_CREATED)
async def create_offer_option(
    agency_id: str,
    workspace_id: str,
    payload: OfferOptionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = offer_builder_service(db, user)
    option = await service.create_option(agency_id, workspace_id, payload, user.get("id"))
    if option is None:
        raise not_found("Offer workspace not found.")
    return {"option": option}


@router.put("/offer-options/{option_id}")
async def update_offer_option(
    agency_id: str,
    option_id: str,
    payload: OfferOptionUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = offer_builder_service(db, user)
    option = await service.update_option(agency_id, option_id, payload, user.get("id"))
    if option is None:
        raise not_found("Offer option not found.")
    return {"option": option}


@router.post("/offer-options/{option_id}/clone", status_code=status.HTTP_201_CREATED)
async def clone_offer_option(
    agency_id: str,
    option_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = offer_builder_service(db, user)
    option = await service.clone_option(agency_id, option_id, user.get("id"))
    if option is None:
        raise not_found("Offer option not found.")
    return {"option": option}


@router.post("/offer-options/{option_id}/evaluate-rules")
async def evaluate_offer_option_rules(
    agency_id: str,
    option_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = offer_builder_service(db, user)
    result = await service.evaluate_option_rules(agency_id, option_id, user.get("id"))
    if result is None:
        raise not_found("Offer option not found.")
    return result


@router.post("/offer-options/{option_id}/recalculate-pricing")
async def recalculate_offer_option_pricing(
    agency_id: str,
    option_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = offer_builder_service(db, user)
    result = await service.recalculate_option_pricing(agency_id, option_id, user.get("id"))
    if result is None:
        raise not_found("Offer option not found.")
    return result


@router.post("/offer-options/{option_id}/segments", status_code=status.HTTP_201_CREATED)
async def add_offer_option_segment(
    agency_id: str,
    option_id: str,
    payload: OfferBuilderSegmentCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = offer_builder_service(db, user)
    segment = await service.add_segment(agency_id, option_id, payload, user.get("id"))
    if segment is None:
        raise not_found("Offer option not found.")
    return {"segment": segment}


@router.post("/offer-options/{option_id}/fare-bundles", status_code=status.HTTP_201_CREATED)
async def add_offer_option_fare_bundle(
    agency_id: str,
    option_id: str,
    payload: OfferFareBundleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = offer_builder_service(db, user)
    fare_bundle = await service.add_fare_bundle(agency_id, option_id, payload, user.get("id"))
    if fare_bundle is None:
        raise not_found("Offer option not found.")
    return {"fare_bundle": fare_bundle}


@router.post("/offer-options/{option_id}/pricing-lines", status_code=status.HTTP_201_CREATED)
async def add_offer_option_pricing_line(
    agency_id: str,
    option_id: str,
    payload: OfferPricingLineCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    require_commercial_field_permissions(payload.model_dump(mode="json"), user)
    service = offer_builder_service(db, user)
    pricing_line = await service.add_pricing_line(agency_id, option_id, payload, user.get("id"))
    if pricing_line is None:
        raise not_found("Offer option not found.")
    return {"pricing_line": pricing_line}


@router.get("/offer-workspaces/{workspace_id}/comparison")
async def get_offer_comparison(
    agency_id: str,
    workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = offer_comparison_service(db, user)
    matrix = await service.build_matrix(agency_id, workspace_id)
    if matrix is None:
        raise not_found("Offer workspace not found.")
    return {"matrix": matrix}


@router.post("/offer-workspaces/{workspace_id}/comparison/snapshot", status_code=status.HTTP_201_CREATED)
async def save_offer_comparison_snapshot(
    agency_id: str,
    workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = offer_comparison_service(db, user)
    snapshot = await service.save_snapshot(agency_id, workspace_id, user.get("id"))
    if snapshot is None:
        raise not_found("Offer workspace not found.")
    return {"snapshot": snapshot}


@router.post("/offer-workspaces/{workspace_id}/recommend")
async def recommend_offer_option(
    agency_id: str,
    workspace_id: str,
    payload: OfferRecommendationRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = offer_comparison_service(db, user)
    result = await service.recommend_option(agency_id, workspace_id, payload.option_id, payload.tag, payload.rank, user.get("id"))
    if result is None:
        raise not_found("Offer workspace or option not found.")
    return result
