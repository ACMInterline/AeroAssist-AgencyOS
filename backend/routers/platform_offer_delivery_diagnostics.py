from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.offer_delivery_client_interaction_service import (
    AUDIT_EVENT_TYPES,
    DECISION_TYPES,
    OfferDeliveryClientInteractionService,
    JourneyOfferDeliveryError,
    PHASE_LABEL,
    VALIDATION_CODES,
)


router = APIRouter(prefix="/api/platform/offer-delivery-diagnostics", tags=["platform-offer-delivery-diagnostics"])
PLATFORM_ROLES = {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}


def require_platform(user: dict) -> None:
    if user.get("global_role") not in PLATFORM_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform access is required.")


@router.get("")
async def dashboard(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    return await OfferDeliveryClientInteractionService(db).dashboard()


@router.get("/summary")
async def summary(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    service = OfferDeliveryClientInteractionService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summarize_readiness(), "read_only": True, **service.safety_flags()}


@router.get("/filters")
async def filters(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    service = OfferDeliveryClientInteractionService(db)
    return {"phase": PHASE_LABEL, "filters": service.filters(), "read_only": True, **service.safety_flags()}


@router.get("/deliveries")
async def deliveries(
    agency_id: str | None = Query(default=None),
    delivery_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    require_platform(user)
    service = OfferDeliveryClientInteractionService(db)
    items = await service.list_deliveries(agency_id, status=delivery_status, include_archived=True)
    safe_items = [service._platform_delivery(item) for item in items]
    return {"phase": PHASE_LABEL, "items": safe_items, "count": len(safe_items), "read_only": True, **service.safety_flags()}


@router.get("/deliveries/{delivery_id}")
async def detail(delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    try:
        return await OfferDeliveryClientInteractionService(db).platform_detail(delivery_id)
    except JourneyOfferDeliveryError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": exc.code, "message": str(exc)}) from exc


@router.get("/deliveries/{delivery_id}/versions")
async def versions(delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    service = OfferDeliveryClientInteractionService(db)
    delivery = await db.collection("journey_offer_deliveries").find_one({"id": delivery_id})
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer delivery was not found.")
    items = await service.list_versions(delivery["agency_id"], delivery_id)
    safe_items = [service._client_version(item) | {"source_snapshot_hash": item.get("source_snapshot_hash"), "payload_hash": item.get("payload_hash"), "immutable": item.get("immutable")} for item in items]
    return {"phase": PHASE_LABEL, "items": safe_items, "count": len(safe_items), "read_only": True, **service.safety_flags()}


@router.get("/validation-codes")
async def validation_codes(user: dict = Depends(get_current_user)) -> dict:
    require_platform(user)
    return {"phase": PHASE_LABEL, "items": VALIDATION_CODES, "read_only": True}


@router.get("/decision-types")
async def decision_types(user: dict = Depends(get_current_user)) -> dict:
    require_platform(user)
    return {"phase": PHASE_LABEL, "items": DECISION_TYPES, "read_only": True}


@router.get("/audit-event-types")
async def audit_event_types(user: dict = Depends(get_current_user)) -> dict:
    require_platform(user)
    return {"phase": PHASE_LABEL, "items": AUDIT_EVENT_TYPES, "read_only": True}
