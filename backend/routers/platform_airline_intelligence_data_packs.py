from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AirlineIntelligenceCoverageSnapshotCreateRequest,
    AirlineIntelligenceDataPackCreateRequest,
    AirlineIntelligenceDataPackInlineCsvRequest,
    AirlineIntelligenceDataPackInlineJsonRequest,
    AirlineIntelligenceDataPackItemCreateRequest,
    AirlineIntelligenceDataPackItemUpdateRequest,
    AirlineIntelligenceDataPackReviewNoteCreateRequest,
    AirlineIntelligenceDataPackUpdateRequest,
    AirlineIntelligenceDataPackValidationIssueAcknowledgeRequest,
)
from services.airline_intelligence_data_pack_service import AirlineIntelligenceDataPackService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-intelligence-data-packs", tags=["platform-airline-intelligence-data-packs"])

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
async def get_platform_airline_intelligence_data_pack_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineIntelligenceDataPackService(db).summary()


@router.get("/packs")
async def list_platform_airline_intelligence_data_packs(
    verification_status: str | None = Query(default=None, alias="status"),
    pack_type: str | None = Query(default=None),
    safe_for_agency_display: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceDataPackService(db).list_packs(
            verification_status=verification_status,
            pack_type=pack_type,
            safe_for_agency_display=safe_for_agency_display,
        ),
        "metadata_only": True,
    }


@router.post("/packs", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_data_pack(
    payload: AirlineIntelligenceDataPackCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackService(db).create_pack(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/packs/{pack_id}")
async def get_platform_airline_intelligence_data_pack(
    pack_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    detail = await AirlineIntelligenceDataPackService(db).get_pack(pack_id)
    if not detail:
        raise not_found("Airline intelligence data pack not found.")
    return detail


@router.patch("/packs/{pack_id}")
async def update_platform_airline_intelligence_data_pack(
    pack_id: str,
    payload: AirlineIntelligenceDataPackUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackService(db).update_pack(pack_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/packs/{pack_id}/items")
async def list_platform_airline_intelligence_data_pack_items(
    pack_id: str,
    target_domain: str | None = Query(default=None),
    airline_iata_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceDataPackService(db).list_pack_items(pack_id=pack_id, target_domain=target_domain, airline_iata_code=airline_iata_code),
        "metadata_only": True,
    }


@router.post("/packs/{pack_id}/items", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_data_pack_item(
    pack_id: str,
    payload: AirlineIntelligenceDataPackItemCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackService(db).add_pack_item(pack_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/items/{item_id}")
async def update_platform_airline_intelligence_data_pack_item(
    item_id: str,
    payload: AirlineIntelligenceDataPackItemUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackService(db).update_pack_item(item_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/packs/{pack_id}/validate")
async def validate_platform_airline_intelligence_data_pack(
    pack_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackService(db).validate_pack(pack_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/packs/{pack_id}/dry-run-json", status_code=status.HTTP_201_CREATED)
async def dry_run_platform_airline_intelligence_json_pack(
    pack_id: str,
    payload: AirlineIntelligenceDataPackInlineJsonRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackService(db).create_dry_run_from_inline_json(pack_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/packs/{pack_id}/dry-run-csv", status_code=status.HTTP_201_CREATED)
async def dry_run_platform_airline_intelligence_csv_pack(
    pack_id: str,
    payload: AirlineIntelligenceDataPackInlineCsvRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackService(db).create_dry_run_from_inline_csv(pack_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/packs/{pack_id}/validation-issues")
async def list_platform_airline_intelligence_data_pack_validation_issues(
    pack_id: str,
    issue_status: str | None = Query(default=None, alias="status"),
    severity: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceDataPackService(db).list_validation_issues(pack_id=pack_id, status=issue_status, severity=severity),
        "metadata_only": True,
    }


@router.patch("/validation-issues/{issue_id}/acknowledge")
async def acknowledge_platform_airline_intelligence_data_pack_validation_issue(
    issue_id: str,
    payload: AirlineIntelligenceDataPackValidationIssueAcknowledgeRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackService(db).acknowledge_validation_issue(issue_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/packs/{pack_id}/review-notes")
async def list_platform_airline_intelligence_data_pack_review_notes(
    pack_id: str,
    note_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceDataPackService(db).list_review_notes(pack_id=pack_id, note_type=note_type),
        "metadata_only": True,
    }


@router.post("/packs/{pack_id}/review-notes", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_data_pack_review_note(
    pack_id: str,
    payload: AirlineIntelligenceDataPackReviewNoteCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackService(db).create_review_note(pack_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/coverage-snapshots", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_coverage_snapshot(
    payload: AirlineIntelligenceCoverageSnapshotCreateRequest | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await AirlineIntelligenceDataPackService(db).create_coverage_snapshot(payload or {})


@router.get("/coverage-snapshots")
async def list_platform_airline_intelligence_coverage_snapshots(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceDataPackService(db).list_coverage_snapshots(),
        "metadata_only": True,
    }
