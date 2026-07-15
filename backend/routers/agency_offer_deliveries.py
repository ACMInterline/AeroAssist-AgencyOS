from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.offer_delivery_client_interaction_service import (
    ImmutableJourneyOfferDeliveryVersionError,
    OfferDeliveryClientInteractionService,
    JourneyOfferDeliveryError,
    PHASE_LABEL,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(
    prefix="/api/agencies/{agency_id}/offer-deliveries",
    tags=["agency-offer-deliveries"],
)

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


def service_error(exc: JourneyOfferDeliveryError) -> HTTPException:
    conflict_codes = {"DELIVERY_VERSION_IMMUTABLE", "DELIVERY_ALREADY_RELEASED", "DECISION_ALREADY_SUBMITTED"}
    code = status.HTTP_409_CONFLICT if isinstance(exc, ImmutableJourneyOfferDeliveryVersionError) or exc.code in conflict_codes else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail={"code": exc.code, "message": str(exc)})


@router.get("")
async def list_deliveries(
    agency_id: str,
    delivery_status: str | None = Query(default=None, alias="status"),
    client_id: str | None = Query(default=None),
    passenger_id: str | None = Query(default=None),
    journey_id: str | None = Query(default=None),
    offer_id: str | None = Query(default=None),
    expiry: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OfferDeliveryClientInteractionService(db)
    items = await service.list_deliveries(
        agency_id,
        status=delivery_status,
        client_id=client_id,
        passenger_id=passenger_id,
        journey_id=journey_id,
        offer_id=offer_id,
        expiry=expiry,
        include_archived=include_archived,
    )
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_delivery(
    agency_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        presentation_id = str(payload.get("presentation_id") or "")
        if not presentation_id:
            raise JourneyOfferDeliveryError("DELIVERY_SOURCE_REQUIRED", "A Phase 56.3 presentation_id is required.")
        return await OfferDeliveryClientInteractionService(db).create_from_presentation(agency_id, presentation_id, payload, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.get("/summary")
async def summary(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = OfferDeliveryClientInteractionService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summarize_readiness(agency_id), **service.safety_flags()}


@router.get("/filters")
async def filters(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = OfferDeliveryClientInteractionService(db)
    return {"phase": PHASE_LABEL, "filters": service.filters(), **service.safety_flags()}


@router.post("/from-presentation/{presentation_id}", status_code=status.HTTP_201_CREATED)
async def from_presentation(
    agency_id: str, presentation_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).create_from_presentation(agency_id, presentation_id, payload, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.post("/from-offer/{offer_id}", status_code=status.HTTP_201_CREATED)
async def from_offer(
    agency_id: str, offer_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).create_from_offer(agency_id, offer_id, payload, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.get("/{delivery_id}")
async def get_delivery(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).get_delivery(agency_id, delivery_id)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.put("/{delivery_id}")
async def update_delivery(
    agency_id: str, delivery_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).update_delivery(agency_id, delivery_id, payload, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.post("/{delivery_id}/archive")
async def archive_delivery(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).archive_delivery(agency_id, delivery_id, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.post("/{delivery_id}/revoke")
async def revoke_delivery(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).revoke_delivery(agency_id, delivery_id, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.get("/{delivery_id}/preview/internal")
async def internal_preview(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).preview_internal(agency_id, delivery_id)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.get("/{delivery_id}/preview/client")
async def client_preview(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).preview_client(agency_id, delivery_id)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.get("/{delivery_id}/recipients")
async def recipients(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = OfferDeliveryClientInteractionService(db)
    try:
        items = await service.list_recipients(agency_id, delivery_id)
        return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.post("/{delivery_id}/recipients", status_code=status.HTTP_201_CREATED)
async def create_recipient(
    agency_id: str, delivery_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).create_recipient(agency_id, delivery_id, payload, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.put("/{delivery_id}/recipients/{recipient_id}")
async def update_recipient(
    agency_id: str, delivery_id: str, recipient_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).update_recipient(agency_id, delivery_id, recipient_id, payload, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.post("/{delivery_id}/recipients/{recipient_id}/revoke")
async def revoke_recipient(
    agency_id: str, delivery_id: str, recipient_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).revoke_recipient(agency_id, delivery_id, recipient_id, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.get("/{delivery_id}/versions")
async def versions(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = OfferDeliveryClientInteractionService(db)
    try:
        items = await service.list_versions(agency_id, delivery_id)
        return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.post("/{delivery_id}/versions", status_code=status.HTTP_201_CREATED)
async def create_version(
    agency_id: str, delivery_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).create_version(agency_id, delivery_id, payload, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.get("/{delivery_id}/versions/{version_id}")
async def get_version(agency_id: str, delivery_id: str, version_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).get_version(agency_id, delivery_id, version_id)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.post("/{delivery_id}/versions/{version_id}/validate")
async def validate_version(agency_id: str, delivery_id: str, version_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).validate_version(agency_id, delivery_id, version_id)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.post("/{delivery_id}/versions/{version_id}/release")
async def release_version(
    agency_id: str, delivery_id: str, version_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).release_version(agency_id, delivery_id, version_id, payload, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.post("/{delivery_id}/versions/{version_id}/supersede")
async def supersede_version(
    agency_id: str, delivery_id: str, version_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).supersede_version(agency_id, delivery_id, version_id, payload, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


async def list_related(db: Database, agency_id: str, delivery_id: str, user: dict, kind: str) -> dict:
    await require_read(db, agency_id, user)
    service = OfferDeliveryClientInteractionService(db)
    try:
        method = {"interactions": service.list_interactions, "decisions": service.list_decisions, "questions": service.list_questions}[kind]
        items = await method(agency_id, delivery_id)
        return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.get("/{delivery_id}/interactions")
async def interactions(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await list_related(db, agency_id, delivery_id, user, "interactions")


@router.get("/{delivery_id}/decisions")
async def decisions(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await list_related(db, agency_id, delivery_id, user, "decisions")


@router.get("/{delivery_id}/questions")
async def questions(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await list_related(db, agency_id, delivery_id, user, "questions")


@router.post("/{delivery_id}/questions/{question_id}/reply", status_code=status.HTTP_201_CREATED)
async def reply_question(
    agency_id: str, delivery_id: str, question_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).reply_question(agency_id, delivery_id, question_id, payload, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.post("/{delivery_id}/acceptance-handoff/preview")
async def acceptance_preview(
    agency_id: str, delivery_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).acceptance_handoff_preview(agency_id, delivery_id, payload, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.post("/{delivery_id}/acceptance-handoff/apply")
async def acceptance_apply(
    agency_id: str, delivery_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).acceptance_handoff_apply(agency_id, delivery_id, payload, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.post("/{delivery_id}/document-handoff/preview")
async def document_preview(
    agency_id: str, delivery_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).document_handoff_preview(agency_id, delivery_id, payload)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.post("/{delivery_id}/document-handoff/apply", status_code=status.HTTP_201_CREATED)
async def document_apply(
    agency_id: str, delivery_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDeliveryClientInteractionService(db).document_handoff_apply(agency_id, delivery_id, payload, user)
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.get("/{delivery_id}/documents")
async def documents(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = OfferDeliveryClientInteractionService(db)
    try:
        items = await service.list_documents(agency_id, delivery_id)
        return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc


@router.get("/{delivery_id}/audit-events")
async def audit_events(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = OfferDeliveryClientInteractionService(db)
    try:
        items = await service.list_audit_events(agency_id, delivery_id)
        return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}
    except JourneyOfferDeliveryError as exc:
        raise service_error(exc) from exc
