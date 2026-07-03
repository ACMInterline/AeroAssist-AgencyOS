from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AirlineIntelligenceDataPackChecklistItemCreateRequest,
    AirlineIntelligenceDataPackChecklistItemUpdateRequest,
    AirlineIntelligenceDataPackConflictUpdateRequest,
    AirlineIntelligenceDataPackFieldMappingCreateRequest,
    AirlineIntelligenceDataPackFieldMappingUpdateRequest,
    AirlineIntelligenceDataPackPromotionReadinessRequest,
    AirlineIntelligenceDataPackReviewCreateRequest,
    AirlineIntelligenceDataPackReviewSnapshotCreateRequest,
    AirlineIntelligenceDataPackReviewUpdateRequest,
)
from services.airline_intelligence_data_pack_review_service import AirlineIntelligenceDataPackReviewService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-intelligence-data-pack-reviews", tags=["platform-airline-intelligence-data-pack-reviews"])

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
async def get_platform_airline_intelligence_data_pack_review_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineIntelligenceDataPackReviewService(db).summary()


@router.get("/reviews")
async def list_platform_airline_intelligence_data_pack_reviews(
    pack_id: str | None = Query(default=None),
    review_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceDataPackReviewService(db).list_reviews(pack_id=pack_id, status=review_status),
        "metadata_only": True,
    }


@router.post("/packs/{pack_id}/reviews", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_data_pack_review(
    pack_id: str,
    payload: AirlineIntelligenceDataPackReviewCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackReviewService(db).create_review(pack_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/reviews/{review_id}")
async def get_platform_airline_intelligence_data_pack_review(
    review_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    detail = await AirlineIntelligenceDataPackReviewService(db).get_review(review_id)
    if not detail:
        raise not_found("Airline intelligence data pack review not found.")
    return detail


@router.patch("/reviews/{review_id}")
async def update_platform_airline_intelligence_data_pack_review(
    review_id: str,
    payload: AirlineIntelligenceDataPackReviewUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackReviewService(db).update_review(review_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/reviews/{review_id}/checklist-items")
async def list_platform_airline_intelligence_data_pack_review_checklist_items(
    review_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceDataPackReviewService(db).list_checklist_items(review_id=review_id),
        "metadata_only": True,
    }


@router.post("/reviews/{review_id}/checklist-items", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_data_pack_review_checklist_item(
    review_id: str,
    payload: AirlineIntelligenceDataPackChecklistItemCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackReviewService(db).create_checklist_item(review_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/checklist-items/{checklist_item_id}")
async def update_platform_airline_intelligence_data_pack_review_checklist_item(
    checklist_item_id: str,
    payload: AirlineIntelligenceDataPackChecklistItemUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackReviewService(db).update_checklist_item(checklist_item_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/packs/{pack_id}/field-mappings")
async def list_platform_airline_intelligence_data_pack_field_mappings(
    pack_id: str,
    item_id: str | None = Query(default=None),
    mapping_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceDataPackReviewService(db).list_field_mappings(pack_id=pack_id, item_id=item_id, mapping_status=mapping_status),
        "metadata_only": True,
    }


@router.post("/packs/{pack_id}/field-mappings", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_data_pack_field_mapping(
    pack_id: str,
    payload: AirlineIntelligenceDataPackFieldMappingCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackReviewService(db).create_field_mapping(pack_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/field-mappings/{mapping_id}")
async def update_platform_airline_intelligence_data_pack_field_mapping(
    mapping_id: str,
    payload: AirlineIntelligenceDataPackFieldMappingUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackReviewService(db).update_field_mapping(mapping_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/packs/{pack_id}/detect-conflicts")
async def detect_platform_airline_intelligence_data_pack_conflicts(
    pack_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackReviewService(db).detect_conflicts(pack_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/packs/{pack_id}/conflicts")
async def list_platform_airline_intelligence_data_pack_conflicts(
    pack_id: str,
    conflict_status: str | None = Query(default=None, alias="status"),
    item_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceDataPackReviewService(db).list_conflicts(pack_id=pack_id, item_id=item_id, status=conflict_status),
        "metadata_only": True,
    }


@router.patch("/conflicts/{conflict_id}")
async def update_platform_airline_intelligence_data_pack_conflict(
    conflict_id: str,
    payload: AirlineIntelligenceDataPackConflictUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackReviewService(db).update_conflict(conflict_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/packs/{pack_id}/promotion-readiness", status_code=status.HTTP_201_CREATED)
async def mark_platform_airline_intelligence_data_pack_promotion_readiness(
    pack_id: str,
    payload: AirlineIntelligenceDataPackPromotionReadinessRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackReviewService(db).mark_promotion_readiness(pack_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/packs/{pack_id}/promotion-readiness")
async def list_platform_airline_intelligence_data_pack_promotion_readiness(
    pack_id: str,
    readiness_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceDataPackReviewService(db).list_promotion_readiness(pack_id=pack_id, status=readiness_status),
        "metadata_only": True,
    }


@router.post("/reviews/{review_id}/snapshots", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_data_pack_review_snapshot(
    review_id: str,
    payload: AirlineIntelligenceDataPackReviewSnapshotCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceDataPackReviewService(db).create_snapshot(review_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/packs/{pack_id}/snapshots")
async def list_platform_airline_intelligence_data_pack_review_snapshots(
    pack_id: str,
    review_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceDataPackReviewService(db).list_snapshots(pack_id=pack_id, review_id=review_id),
        "metadata_only": True,
    }
