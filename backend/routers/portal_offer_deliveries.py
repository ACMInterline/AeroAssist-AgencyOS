from fastapi import APIRouter, Body, Depends, HTTPException, status

from database import Database, get_database
from routers.portal import portal_context, safe_response
from services.offer_delivery_client_interaction_service import (
    OfferDeliveryClientInteractionService,
    JourneyOfferDeliveryError,
)


router = APIRouter(prefix="/api/portal/offer-deliveries", tags=["portal-offer-deliveries"])


def portal_error(exc: JourneyOfferDeliveryError) -> HTTPException:
    forbidden = {"RECIPIENT_NOT_AUTHORIZED", "RECIPIENT_REVOKED", "AGENCY_ISOLATION_VIOLATION"}
    code = status.HTTP_404_NOT_FOUND if exc.code in forbidden else status.HTTP_409_CONFLICT if exc.code in {
        "DELIVERY_EXPIRED", "DELIVERY_REVOKED", "DELIVERY_VERSION_SUPERSEDED", "DECISION_ALREADY_SUBMITTED"
    } else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail={"code": exc.code, "message": str(exc)})


@router.get("")
async def list_deliveries(ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    try:
        return safe_response(await OfferDeliveryClientInteractionService(db).portal_list(ctx))
    except JourneyOfferDeliveryError as exc:
        raise portal_error(exc) from exc


@router.get("/{delivery_id}")
async def get_delivery(delivery_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    try:
        return safe_response(await OfferDeliveryClientInteractionService(db).portal_detail(ctx, delivery_id))
    except JourneyOfferDeliveryError as exc:
        raise portal_error(exc) from exc


@router.post("/{delivery_id}/open")
async def record_open(delivery_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    try:
        return safe_response(await OfferDeliveryClientInteractionService(db).portal_detail(ctx, delivery_id, record_open=True))
    except JourneyOfferDeliveryError as exc:
        raise portal_error(exc) from exc


@router.get("/{delivery_id}/comparison")
async def comparison(delivery_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    try:
        detail = await OfferDeliveryClientInteractionService(db).portal_detail(ctx, delivery_id)
        return safe_response({"phase": detail["phase"], "comparison": detail["client_safe_payload"].get("comparison"), "options": detail["client_safe_payload"].get("options") or [], "fare_brands": detail["client_safe_payload"].get("fare_brands") or []})
    except JourneyOfferDeliveryError as exc:
        raise portal_error(exc) from exc


@router.get("/{delivery_id}/options/{option_id}")
async def option_detail(delivery_id: str, option_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    try:
        detail = await OfferDeliveryClientInteractionService(db).portal_detail(ctx, delivery_id)
        payload = detail["client_safe_payload"]
        option = next((item for item in payload.get("options") or [] if item.get("id") == option_id), None)
        if not option:
            raise JourneyOfferDeliveryError("OPTION_NOT_IN_RELEASED_VERSION", "Option was not found in this released version.")
        return safe_response({"phase": detail["phase"], "option": option, "segments": [item for item in payload.get("segments") or [] if item.get("option_projection_id") == option_id], "connections": [item for item in payload.get("connections") or [] if item.get("option_projection_id") == option_id], "service_suitability": [item for item in payload.get("service_suitability") or [] if item.get("option_projection_id") == option_id]})
    except JourneyOfferDeliveryError as exc:
        raise portal_error(exc) from exc


@router.get("/{delivery_id}/fare-brands/{fare_brand_id}")
async def fare_brand_detail(delivery_id: str, fare_brand_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    try:
        detail = await OfferDeliveryClientInteractionService(db).portal_detail(ctx, delivery_id)
        fare = next((item for item in detail["client_safe_payload"].get("fare_brands") or [] if item.get("id") == fare_brand_id), None)
        if not fare:
            raise JourneyOfferDeliveryError("FARE_BRAND_NOT_IN_SELECTED_OPTION", "Fare brand was not found in this released version.")
        return safe_response({"phase": detail["phase"], "fare_brand": fare})
    except JourneyOfferDeliveryError as exc:
        raise portal_error(exc) from exc


@router.post("/{delivery_id}/interactions", status_code=status.HTTP_201_CREATED)
async def interaction(delivery_id: str, payload: dict = Body(...), ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    try:
        return safe_response(await OfferDeliveryClientInteractionService(db).portal_record_interaction(ctx, delivery_id, payload))
    except JourneyOfferDeliveryError as exc:
        raise portal_error(exc) from exc


@router.post("/{delivery_id}/selection", status_code=status.HTTP_201_CREATED)
async def selection(delivery_id: str, payload: dict = Body(...), ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    service = OfferDeliveryClientInteractionService(db)
    try:
        results = []
        if payload.get("selected_option_id"):
            results.append(await service.portal_record_interaction(ctx, delivery_id, {"interaction_type": "preferred_option_selected", "option_id": payload["selected_option_id"]}))
        if payload.get("selected_fare_brand_id"):
            results.append(await service.portal_record_interaction(ctx, delivery_id, {"interaction_type": "preferred_fare_brand_selected", "option_id": payload.get("selected_option_id"), "fare_brand_id": payload["selected_fare_brand_id"]}))
        return safe_response({"phase": results[0]["phase"] if results else None, "selection_recorded": bool(results), "interactions": [item["interaction"] for item in results]})
    except JourneyOfferDeliveryError as exc:
        raise portal_error(exc) from exc


@router.post("/{delivery_id}/warnings/acknowledge", status_code=status.HTTP_201_CREATED)
async def acknowledge(delivery_id: str, payload: dict = Body(...), ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    try:
        return safe_response(await OfferDeliveryClientInteractionService(db).portal_acknowledge_warning(ctx, delivery_id, payload))
    except JourneyOfferDeliveryError as exc:
        raise portal_error(exc) from exc


@router.post("/{delivery_id}/questions", status_code=status.HTTP_201_CREATED)
async def question(delivery_id: str, payload: dict = Body(...), ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    try:
        return safe_response(await OfferDeliveryClientInteractionService(db).portal_submit_question(ctx, delivery_id, payload))
    except JourneyOfferDeliveryError as exc:
        raise portal_error(exc) from exc


@router.post("/{delivery_id}/decisions/preview")
async def decision_preview(delivery_id: str, payload: dict = Body(...), ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    try:
        return safe_response(await OfferDeliveryClientInteractionService(db).portal_decision_preview(ctx, delivery_id, payload))
    except JourneyOfferDeliveryError as exc:
        raise portal_error(exc) from exc


@router.post("/{delivery_id}/decisions", status_code=status.HTTP_201_CREATED)
async def decision(delivery_id: str, payload: dict = Body(...), ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    try:
        return safe_response(await OfferDeliveryClientInteractionService(db).portal_submit_decision(ctx, delivery_id, payload))
    except JourneyOfferDeliveryError as exc:
        raise portal_error(exc) from exc


@router.get("/{delivery_id}/documents")
async def documents(delivery_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    try:
        return safe_response(await OfferDeliveryClientInteractionService(db).portal_documents(ctx, delivery_id))
    except JourneyOfferDeliveryError as exc:
        raise portal_error(exc) from exc


@router.post("/{delivery_id}/documents/{document_link_id}/download")
async def document_download(delivery_id: str, document_link_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    try:
        return safe_response(await OfferDeliveryClientInteractionService(db).portal_record_document_download(ctx, delivery_id, document_link_id))
    except JourneyOfferDeliveryError as exc:
        raise portal_error(exc) from exc
