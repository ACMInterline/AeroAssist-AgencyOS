from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    PublicRequestIntakeCreate,
    RequestIntakeAction,
    RequestIntakeTriageUpdate,
    StaffRequestIntakeCreate,
)
from services.request_intake_conversion_service import create_intake, convert_intake, write_audit
from services.tenant_service import assert_agency_access, require_any_agency_role

public_router = APIRouter(prefix="/api/public", tags=["public-request-intakes"])
staff_router = APIRouter(prefix="/api/request-intakes", tags=["request-intakes"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


def clean_text(value: str | None, limit: int = 1000) -> str | None:
    if value is None:
        return None
    text = " ".join(value.split())
    return text[:limit] if text else None


def validate_public_payload(payload: PublicRequestIntakeCreate) -> None:
    contact = payload.contact
    travel = payload.travel
    services = payload.services
    if not clean_text(contact.name, 160):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name is required.")
    if not contact.email and not clean_text(contact.phone, 80):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or phone is required.")
    if not (clean_text(travel.origin, 120) and clean_text(travel.destination, 120)) and not clean_text(travel.itinerary_notes, 2000):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Origin/destination or travel description is required.")
    has_service = bool(services.selected_service_categories) or any(
        [
            services.mobility_assistance,
            services.medical_travel,
            services.pet_travel,
            services.child_or_unaccompanied_minor,
            services.special_baggage,
            services.documents_or_visa,
            services.disruption_or_claims,
            services.booking_or_planning,
            services.other,
        ]
    )
    if not has_service and not clean_text(payload.request_details, 3000):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select at least one service type or describe the request.")


def safe_public_intake(intake: dict) -> dict:
    return {"id": intake["id"], "reference_code": intake["reference_code"], "status": "received"}


async def accessible_agency_ids(db: Database, user: dict) -> Optional[set[str]]:
    if user.get("global_role") in {"platform_owner", "platform_admin", "platform_support"}:
        return None
    memberships = await db.collection("agency_staff_memberships").find_many({"user_id": user["id"], "status": "active"})
    return {membership["agency_id"] for membership in memberships}


async def require_intake_read(db: Database, intake: dict, user: dict) -> None:
    agency_id = intake.get("agency_id")
    if user.get("global_role") in {"platform_owner", "platform_admin", "platform_support"}:
        return
    if not agency_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform access required for unassigned intakes.")
    await assert_agency_access(db, agency_id, user)
    await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_intake_write(db: Database, intake: dict, user: dict) -> None:
    agency_id = intake.get("agency_id")
    if user.get("global_role") in {"platform_owner", "platform_admin"}:
        return
    if not agency_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform access required for unassigned intakes.")
    await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


async def get_intake_or_404(db: Database, intake_id: str) -> dict:
    intake = await db.collection("request_intakes").find_one({"id": intake_id})
    if not intake:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request intake not found.")
    return intake


@public_router.post("/request-intakes", status_code=status.HTTP_201_CREATED)
async def submit_public_request_intake(payload: PublicRequestIntakeCreate, db: Database = Depends(get_database)) -> dict:
    validate_public_payload(payload)
    intake = await create_intake(
        db,
        source="public_website",
        contact=payload.contact.model_dump(mode="json"),
        travel=payload.travel.model_dump(mode="json"),
        services=payload.services.model_dump(mode="json"),
        request_details=clean_text(payload.request_details, 3000),
        agency_custom_fields=payload.agency_custom_fields,
        raw_payload=payload.model_dump(mode="json"),
    )
    return {"intake": safe_public_intake(intake), "message": "We received your request. Our team will review it."}


@staff_router.get("")
async def list_request_intakes(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    agency_id: Optional[str] = None,
    search: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if agency_id:
        filters["agency_id"] = agency_id
    items = await db.collection("request_intakes").find_many(filters)
    allowed_agencies = await accessible_agency_ids(db, user)
    if allowed_agencies is not None:
        items = [item for item in items if item.get("agency_id") in allowed_agencies]
    if search:
        needle = search.lower()
        items = [
            item
            for item in items
            if any(
                needle in str(value or "").lower()
                for value in [
                    item.get("reference_code"),
                    (item.get("contact_snapshot") or {}).get("name"),
                    (item.get("contact_snapshot") or {}).get("email"),
                    (item.get("travel_summary") or {}).get("origin"),
                    (item.get("travel_summary") or {}).get("destination"),
                ]
            )
        ]
    items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return {"items": items}


@staff_router.post("", status_code=status.HTTP_201_CREATED)
async def create_staff_request_intake(payload: StaffRequestIntakeCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    if payload.agency_id:
        if user.get("global_role") not in {"platform_owner", "platform_admin"}:
            await require_any_agency_role(db, payload.agency_id, user, WRITE_ROLES)
    elif user.get("global_role") not in {"platform_owner", "platform_admin"}:
        memberships = await db.collection("agency_staff_memberships").find_many({"user_id": user["id"], "status": "active"})
        if len(memberships) == 1:
            payload.agency_id = memberships[0]["agency_id"]
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="agency_id is required when staff belongs to multiple agencies.")
    intake = await create_intake(
        db,
        source=payload.source,
        agency_id=payload.agency_id,
        workspace_id=payload.workspace_id,
        contact=payload.contact.model_dump(mode="json"),
        travel=payload.travel.model_dump(mode="json"),
        services=payload.services.model_dump(mode="json"),
        request_details=clean_text(payload.request_details, 3000),
        agency_custom_fields=payload.agency_custom_fields,
        priority=payload.priority,
        assigned_to=payload.assigned_to,
        triage_notes=payload.triage_notes,
        internal_notes=payload.internal_notes,
        client_visible_notes=payload.client_visible_notes,
        raw_payload=payload.model_dump(mode="json"),
        actor_user_id=user["id"],
    )
    return {"intake": intake}


@staff_router.get("/{intake_id}")
async def get_request_intake(intake_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    intake = await get_intake_or_404(db, intake_id)
    await require_intake_read(db, intake, user)
    request = None
    if intake.get("converted_request_id"):
        request = await db.collection("travel_requests").find_one({"id": intake["converted_request_id"]})
    return {"intake": intake, "converted_request": request}


@staff_router.patch("/{intake_id}/triage")
async def update_request_intake_triage(intake_id: str, payload: RequestIntakeTriageUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    intake = await get_intake_or_404(db, intake_id)
    await require_intake_write(db, intake, user)
    updates = payload.model_dump(exclude_unset=True, mode="json")
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No triage fields provided.")
    if updates.get("agency_id"):
        if user.get("global_role") not in {"platform_owner", "platform_admin"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform admin access required to reroute agency.")
        await assert_agency_access(db, updates["agency_id"], user)
    updates["status"] = "triaged" if intake.get("status") == "new" else intake.get("status")
    updated = await db.collection("request_intakes").update_one({"id": intake_id}, updates, allow_agency_update=True)
    await write_audit(db, updated.get("agency_id"), user["id"], "intake_triaged", "request_intake", intake_id, "Updated request intake triage.", {"fields": sorted(updates.keys())})
    return {"intake": updated}


@staff_router.post("/{intake_id}/convert")
async def convert_request_intake(intake_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    intake = await get_intake_or_404(db, intake_id)
    await require_intake_write(db, intake, user)
    return await convert_intake(db, intake_id, user["id"])


async def update_intake_status(intake_id: str, status_value: str, event_type: str, payload: RequestIntakeAction, user: dict, db: Database) -> dict:
    intake = await get_intake_or_404(db, intake_id)
    await require_intake_write(db, intake, user)
    if intake.get("converted_request_id"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Converted intakes cannot be changed by this action.")
    updates = {"status": status_value, "action_reason": payload.reason}
    if status_value == "duplicate":
        updates["duplicate_of_intake_id"] = payload.duplicate_of_intake_id
    updated = await db.collection("request_intakes").update_one({"id": intake_id}, updates)
    await write_audit(db, updated.get("agency_id"), user["id"], event_type, "request_intake", intake_id, f"Marked intake as {status_value}.", {"reason": payload.reason, "duplicate_of_intake_id": payload.duplicate_of_intake_id})
    return {"intake": updated}


@staff_router.post("/{intake_id}/reject")
async def reject_request_intake(intake_id: str, payload: RequestIntakeAction | None = None, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await update_intake_status(intake_id, "rejected", "intake_rejected", payload or RequestIntakeAction(), user, db)


@staff_router.post("/{intake_id}/archive")
async def archive_request_intake(intake_id: str, payload: RequestIntakeAction | None = None, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await update_intake_status(intake_id, "archived", "intake_archived", payload or RequestIntakeAction(), user, db)


@staff_router.post("/{intake_id}/mark-duplicate")
async def mark_request_intake_duplicate(intake_id: str, payload: RequestIntakeAction, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await update_intake_status(intake_id, "duplicate", "intake_marked_duplicate", payload, user, db)
