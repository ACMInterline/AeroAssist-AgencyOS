from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import Database, get_database
from models import PortalAccessMappingCreate, PortalAccessMappingRevoke
from persistence_query import MAXIMUM_QUERY_LIMIT, PaginationRequest
from persistence_repository import PersistenceRepository
from services.authorization_service import require_permission
from services.portal_identity_link_service import (
    PortalIdentityLinkConflict,
    PortalIdentityLinkError,
    PortalIdentityLinkNotFound,
    create_portal_mapping,
    revoke_portal_mapping,
    safe_portal_mapping,
)


router = APIRouter(
    prefix="/api/agencies/{agency_id}/portal-access-mappings",
    tags=["portal-access-mappings"],
)


def portal_error(exc: PortalIdentityLinkError) -> HTTPException:
    if isinstance(exc, PortalIdentityLinkNotFound):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, PortalIdentityLinkConflict):
        code = status.HTTP_409_CONFLICT
    else:
        code = status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=str(exc))


@router.get("")
async def list_mappings(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    require_permission(user, "manage_agency_users")
    page = await PersistenceRepository(db).find_agency_records(
        collection_name="portal_access_mappings",
        agency_id=agency_id,
        sort_field="created_at",
        sort_direction="desc",
        pagination=PaginationRequest.build(limit=MAXIMUM_QUERY_LIMIT),
    )
    return {
        "items": [safe_portal_mapping(item) for item in page.items],
        "pagination": page.pagination.as_dict(),
        "agency_id": agency_id,
        "email_authoritative_access": False,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_mapping(
    agency_id: str,
    payload: PortalAccessMappingCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    require_permission(user, "manage_agency_users")
    try:
        mapping = await create_portal_mapping(db, agency_id, payload, user["id"])
    except PortalIdentityLinkError as exc:
        raise portal_error(exc) from exc
    return {"portal_mapping": safe_portal_mapping(mapping)}


@router.get("/{mapping_id}")
async def get_mapping(
    agency_id: str,
    mapping_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    require_permission(user, "manage_agency_users")
    mapping = await db.collection("portal_access_mappings").find_one(
        {"agency_id": agency_id, "id": mapping_id}
    )
    if not mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal mapping not found.")
    return {"portal_mapping": safe_portal_mapping(mapping)}


@router.post("/{mapping_id}/revoke")
async def revoke_mapping(
    agency_id: str,
    mapping_id: str,
    payload: PortalAccessMappingRevoke,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    require_permission(user, "manage_agency_users")
    try:
        mapping = await revoke_portal_mapping(
            db,
            agency_id,
            mapping_id,
            user["id"],
            payload.reason,
        )
    except PortalIdentityLinkError as exc:
        raise portal_error(exc) from exc
    return {"portal_mapping": safe_portal_mapping(mapping)}
