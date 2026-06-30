from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import GdsParserCorrectionCreate, GdsParserParseTextRequest, GdsParseTrainingSampleCreate
from services.gds_parser_service import GdsParserService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/gds-parser", tags=["agency-gds-parser"])

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


def filters_from(**kwargs: object) -> dict:
    return {key: value for key, value in kwargs.items() if value not in {None, ""}}


@router.get("/profiles")
async def list_parser_profiles(
    agency_id: str,
    provider_family: str | None = None,
    input_format: str | None = None,
    active: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await GdsParserService(db).list_parser_profiles(filters_from(provider_family=provider_family, input_format=input_format, active=active))


@router.get("/runs")
async def list_parser_runs(
    agency_id: str,
    booking_import_draft_id: str | None = None,
    parse_status: str | None = None,
    provider_family_detected: str | None = None,
    input_format_detected: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await GdsParserService(db).list_parser_runs(
        agency_id,
        filters_from(
            booking_import_draft_id=booking_import_draft_id,
            parse_status=parse_status,
            provider_family_detected=provider_family_detected,
            input_format_detected=input_format_detected,
        ),
    )


@router.post("/parse-text", status_code=status.HTTP_201_CREATED)
async def parse_text(
    agency_id: str,
    payload: GdsParserParseTextRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return await GdsParserService(db).parse_text(agency_id, payload, user)


@router.post("/booking-import-drafts/{draft_id}/parse")
async def parse_booking_import_draft(
    agency_id: str,
    draft_id: str,
    payload: dict | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    result = await GdsParserService(db).parse_booking_import_draft(agency_id, draft_id, payload or {}, user)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking import draft not found.")
    return result


@router.get("/runs/{parser_run_id}")
async def get_parser_run(
    agency_id: str,
    parser_run_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    run = await GdsParserService(db).get_parser_run(agency_id, parser_run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parser run not found.")
    return {"parser_run": run, "explicit_import_required": True, "live_gds_connection_disabled": True}


@router.get("/runs/{parser_run_id}/entities")
async def list_parser_run_entities(
    agency_id: str,
    parser_run_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    run = await GdsParserService(db).get_parser_run(agency_id, parser_run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parser run not found.")
    return await GdsParserService(db).list_parsed_entities(agency_id, parser_run_id)


@router.post("/corrections", status_code=status.HTTP_201_CREATED)
async def apply_parser_correction(
    agency_id: str,
    payload: GdsParserCorrectionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    result = await GdsParserService(db).apply_entity_correction(agency_id, payload, user)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parser run not found.")
    return result


@router.post("/runs/{parser_run_id}/training-sample", status_code=status.HTTP_201_CREATED)
async def create_training_sample(
    agency_id: str,
    parser_run_id: str,
    payload: GdsParseTrainingSampleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    result = await GdsParserService(db).create_training_sample_from_run(agency_id, parser_run_id, payload, user)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parser run not found.")
    return result
