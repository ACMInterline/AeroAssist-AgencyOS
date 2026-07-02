from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OfferDecisionPackAdvisorAttachmentRequest,
    OfferDecisionPackBuildRequest,
    OfferDecisionPackReviewNoteCreate,
    OfferDecisionPackReviewNoteUpdate,
    OfferDecisionPackSnapshotCreate,
)
from services.offer_decision_pack_service import OfferDecisionPackService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/offer-decision-packs", tags=["agency-offer-decision-packs"])

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


def bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.get("/summary")
async def get_agency_offer_decision_pack_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        **await OfferDecisionPackService(db).summary(agency_id=agency_id),
        "agency_operational_layer": True,
        "metadata_only": True,
    }


@router.get("/packs")
async def list_agency_offer_decision_packs(
    agency_id: str,
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionPackService(db).list_packs(agency_id=agency_id, offer_workspace_id=offer_workspace_id)}


@router.post("/packs/build", status_code=status.HTTP_201_CREATED)
async def build_agency_offer_decision_pack(
    agency_id: str,
    payload: OfferDecisionPackBuildRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionPackService(db).build_pack(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/packs/{pack_id}")
async def get_agency_offer_decision_pack_detail(
    agency_id: str,
    pack_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    detail = await OfferDecisionPackService(db).get_pack_detail(pack_id, agency_id)
    if not detail:
        raise not_found("Offer decision pack not found.")
    return detail


@router.post("/packs/{pack_id}/attach-advisor-evidence")
async def attach_agency_offer_decision_pack_advisor_evidence(
    agency_id: str,
    pack_id: str,
    payload: OfferDecisionPackAdvisorAttachmentRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        result = await OfferDecisionPackService(db).attach_advisor_evidence(agency_id, pack_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    if not result:
        raise not_found("Offer decision pack not found.")
    return result


@router.post("/packs/{pack_id}/review-notes", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_pack_review_note(
    agency_id: str,
    pack_id: str,
    payload: OfferDecisionPackReviewNoteCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    result = await OfferDecisionPackService(db).create_review_note(agency_id, pack_id, payload, user)
    if not result:
        raise not_found("Offer decision pack not found.")
    return result


@router.patch("/packs/{pack_id}/review-notes/{note_id}")
async def update_agency_offer_decision_pack_review_note(
    agency_id: str,
    pack_id: str,
    note_id: str,
    payload: OfferDecisionPackReviewNoteUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    result = await OfferDecisionPackService(db).update_review_note(agency_id, pack_id, note_id, payload)
    if not result:
        raise not_found("Offer decision pack review note not found.")
    return result


@router.post("/packs/{pack_id}/snapshots", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_pack_snapshot(
    agency_id: str,
    pack_id: str,
    payload: OfferDecisionPackSnapshotCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    result = await OfferDecisionPackService(db).create_snapshot(agency_id, pack_id, payload)
    if not result:
        raise not_found("Offer decision pack not found.")
    return result


@router.get("/options")
async def list_agency_offer_decision_pack_options(
    agency_id: str,
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionPackService(db).list_options(agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}


@router.get("/evidence")
async def list_agency_offer_decision_pack_evidence(
    agency_id: str,
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionPackService(db).list_evidence(agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}


@router.get("/warnings")
async def list_agency_offer_decision_pack_warnings(
    agency_id: str,
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionPackService(db).list_warnings(agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}


@router.get("/review-notes")
async def list_agency_offer_decision_pack_review_notes(
    agency_id: str,
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionPackService(db).list_review_notes(agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}


@router.get("/snapshots")
async def list_agency_offer_decision_pack_snapshots(
    agency_id: str,
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionPackService(db).list_snapshots(agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}
