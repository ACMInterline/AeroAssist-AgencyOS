from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OfferPolicyAdvisorAttachmentRequest,
    OfferPolicyAdvisorContextBuildRequest,
    OfferPolicyAdvisorDecisionNoteCreate,
    OfferPolicyAdvisorEvaluationRequest,
    OfferPolicyAdvisorSavedSnapshotCreate,
)
from services.offer_policy_advisor_service import OfferPolicyAdvisorService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/offer-policy-advisor", tags=["agency-offer-policy-advisor"])

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
async def get_agency_offer_policy_advisor_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    summary = await OfferPolicyAdvisorService(db).summary(agency_id=agency_id)
    return {
        **summary,
        "agency_global_mutation_blocked": True,
        "metadata_only": True,
    }


@router.get("/contexts")
async def list_agency_offer_policy_advisor_contexts(
    agency_id: str,
    offer_workspace_id: str | None = Query(default=None),
    offer_option_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "items": await OfferPolicyAdvisorService(db).list_contexts(
            agency_id=agency_id,
            offer_workspace_id=offer_workspace_id,
            offer_option_id=offer_option_id,
        )
    }


@router.post("/contexts/build", status_code=status.HTTP_201_CREATED)
async def build_agency_offer_policy_advisor_context(
    agency_id: str,
    payload: OfferPolicyAdvisorContextBuildRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferPolicyAdvisorService(db).build_context(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/contexts/{context_id}")
async def get_agency_offer_policy_advisor_context(
    agency_id: str,
    context_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OfferPolicyAdvisorService(db)
    context = await service.get_context(context_id, agency_id)
    if not context:
        raise not_found("Offer policy advisor context not found.")
    return {
        "context": context,
        "airline_rows": await service.list_airline_rows(agency_id=agency_id, context_id=context_id),
        "warnings": await service.list_warnings(agency_id=agency_id, context_id=context_id),
        "decision_notes": await service.list_decision_notes(agency_id=agency_id, context_id=context_id),
        "saved_snapshots": await service.list_saved_snapshots(agency_id=agency_id, context_id=context_id),
    }


@router.post("/contexts/{context_id}/evaluate", status_code=status.HTTP_201_CREATED)
async def evaluate_agency_offer_policy_advisor_context(
    agency_id: str,
    context_id: str,
    payload: OfferPolicyAdvisorEvaluationRequest | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    result = await OfferPolicyAdvisorService(db).evaluate_context(agency_id, context_id, payload, user)
    if not result:
        raise not_found("Offer policy advisor context not found.")
    return result


@router.post("/contexts/{context_id}/attach")
async def attach_agency_offer_policy_advisor_artifacts(
    agency_id: str,
    context_id: str,
    payload: OfferPolicyAdvisorAttachmentRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    result = await OfferPolicyAdvisorService(db).attach_artifacts(agency_id, context_id, payload)
    if not result:
        raise not_found("Offer policy advisor context not found.")
    return result


@router.post("/contexts/{context_id}/decision-notes", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_policy_advisor_decision_note(
    agency_id: str,
    context_id: str,
    payload: OfferPolicyAdvisorDecisionNoteCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    result = await OfferPolicyAdvisorService(db).create_decision_note(agency_id, context_id, payload, user)
    if not result:
        raise not_found("Offer policy advisor context not found.")
    return result


@router.post("/contexts/{context_id}/saved-snapshots", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_policy_advisor_saved_snapshot(
    agency_id: str,
    context_id: str,
    payload: OfferPolicyAdvisorSavedSnapshotCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    result = await OfferPolicyAdvisorService(db).create_saved_snapshot(agency_id, context_id, payload)
    if not result:
        raise not_found("Offer policy advisor context not found.")
    return result


@router.get("/airline-rows")
async def list_agency_offer_policy_advisor_airline_rows(
    agency_id: str,
    context_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferPolicyAdvisorService(db).list_airline_rows(agency_id=agency_id, context_id=context_id, offer_workspace_id=offer_workspace_id)}


@router.get("/warnings")
async def list_agency_offer_policy_advisor_warnings(
    agency_id: str,
    context_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferPolicyAdvisorService(db).list_warnings(agency_id=agency_id, context_id=context_id, offer_workspace_id=offer_workspace_id)}


@router.get("/decision-notes")
async def list_agency_offer_policy_advisor_decision_notes(
    agency_id: str,
    context_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferPolicyAdvisorService(db).list_decision_notes(agency_id=agency_id, context_id=context_id, offer_workspace_id=offer_workspace_id)}


@router.get("/saved-snapshots")
async def list_agency_offer_policy_advisor_saved_snapshots(
    agency_id: str,
    context_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferPolicyAdvisorService(db).list_saved_snapshots(agency_id=agency_id, context_id=context_id, offer_workspace_id=offer_workspace_id)}
