from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import Database, get_database
from models import BookingImportDraftCreate, BookingImportDraftImportRequest
from services.booking_import_service import BookingImportError, BookingImportService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["agency-booking-imports"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(exc: BookingImportError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/booking-import-drafts")
async def list_booking_import_drafts(
    agency_id: str,
    source_type: str | None = None,
    parser_status: str | None = None,
    linked_trip_id: str | None = None,
    import_context: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = BookingImportService(db)
    return await service.list_import_drafts(
        agency_id,
        {
            "source_type": source_type,
            "parser_status": parser_status,
            "linked_trip_id": linked_trip_id,
            "import_context": import_context,
        },
    )


@router.post("/booking-import-drafts", status_code=status.HTTP_201_CREATED)
async def create_booking_import_draft(
    agency_id: str,
    payload: BookingImportDraftCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = BookingImportService(db)
    return await service.create_import_draft(agency_id, payload, user)


@router.get("/booking-import-drafts/{draft_id}")
async def get_booking_import_draft(
    agency_id: str,
    draft_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = BookingImportService(db)
    draft = await service.get_import_draft(agency_id, draft_id)
    if not draft:
        raise not_found("Booking import draft not found.")
    return {"draft": draft, "provider_execution_disabled": True}


@router.post("/booking-import-drafts/{draft_id}/parse")
async def parse_booking_import_draft(
    agency_id: str,
    draft_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = BookingImportService(db)
    result = await service.parse_import_draft(agency_id, draft_id, user)
    if result is None:
        raise not_found("Booking import draft not found.")
    return result


@router.post("/booking-import-drafts/{draft_id}/import-as-booking")
async def import_booking_import_draft(
    agency_id: str,
    draft_id: str,
    payload: BookingImportDraftImportRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = BookingImportService(db)
    try:
        result = await service.import_draft_as_booking(agency_id, draft_id, payload, user)
    except BookingImportError as exc:
        raise bad_request(exc)
    if result is None:
        raise not_found("Booking import draft not found.")
    return result
