from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import Database, get_database
from models import (
    PassengerServiceConfirmationRequest,
    PassengerServiceFulfilmentLinkRequest,
    PassengerServiceOutcomeRequest,
    PassengerServiceReconciliationRequest,
    PassengerServiceRequestCreate,
)
from services.special_services_service import SpecialServicesService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["agency-special-services"])

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


async def ensure_request(db: Database, agency_id: str, request_id: str) -> dict:
    request = await db.collection("travel_requests").find_one({"agency_id": agency_id, "id": request_id})
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    return request


async def ensure_trip(db: Database, agency_id: str, trip_id: str) -> dict:
    trip = await db.collection("trip_dossiers").find_one({"agency_id": agency_id, "id": trip_id})
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found.")
    return trip


async def ensure_booking(db: Database, agency_id: str, booking_id: str) -> dict:
    booking = await db.collection("bookings").find_one({"agency_id": agency_id, "id": booking_id})
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    return booking


@router.get("/requests/{request_id}/special-services")
async def list_request_special_services(
    agency_id: str,
    request_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    request = await ensure_request(db, agency_id, request_id)
    service = SpecialServicesService(db)
    return {"request": request, "items": await service.list_services_for_request(agency_id, request_id)}


@router.post("/requests/{request_id}/special-services", status_code=status.HTTP_201_CREATED)
async def create_request_special_service(
    agency_id: str,
    request_id: str,
    payload: PassengerServiceRequestCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await ensure_request(db, agency_id, request_id)
    service = SpecialServicesService(db)
    created = await service.add_service_request(agency_id, payload, user["id"], request_id=request_id)
    return {"service": created}


@router.get("/trips/{trip_id}/special-services")
async def list_trip_special_services(
    agency_id: str,
    trip_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    trip = await ensure_trip(db, agency_id, trip_id)
    service = SpecialServicesService(db)
    return {"trip": trip, "items": await service.list_services_for_trip(agency_id, trip_id)}


@router.post("/trips/{trip_id}/special-services", status_code=status.HTTP_201_CREATED)
async def create_trip_special_service(
    agency_id: str,
    trip_id: str,
    payload: PassengerServiceRequestCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await ensure_trip(db, agency_id, trip_id)
    service = SpecialServicesService(db)
    created = await service.add_service_request(agency_id, payload, user["id"], trip_id=trip_id)
    return {"service": created}


@router.post("/special-services/{service_id}/evaluate")
async def evaluate_special_service(
    agency_id: str,
    service_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = SpecialServicesService(db)
    result = await service.evaluate_service_request(agency_id, service_id, user["id"])
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Special service request not found.")
    return result


@router.post("/special-services/{service_id}/generate-ssr-osi")
async def generate_special_service_ssr_osi(
    agency_id: str,
    service_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = SpecialServicesService(db)
    result = await service.generate_ssr_osi_for_service(agency_id, service_id, user["id"])
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Special service request not found.")
    return result


@router.post("/trips/{trip_id}/generate-ssr-osi")
async def generate_trip_special_services_ssr_osi(
    agency_id: str,
    trip_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await ensure_trip(db, agency_id, trip_id)
    service = SpecialServicesService(db)
    return await service.generate_ssr_osi_for_trip(agency_id, trip_id, user["id"])


@router.get("/passenger-services")
async def list_passenger_service_fulfilment_cases(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "agency_id": agency_id,
        "items": await SpecialServicesService(db).list_fulfilment_cases(agency_id),
        "manual_external_status_only": True,
        "provider_execution_disabled": True,
    }


@router.get("/passenger-services/{service_id}/link-options")
async def list_passenger_service_fulfilment_link_options(
    agency_id: str,
    service_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await SpecialServicesService(db).fulfilment_link_options(agency_id, service_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/passenger-services/{service_id}")
async def get_passenger_service_fulfilment_case(
    agency_id: str,
    service_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = await SpecialServicesService(db).get_service_or_none(agency_id, service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passenger-service request not found.")
    return {"agency_id": agency_id, "service": service, "provider_execution_disabled": True}


@router.post("/passenger-services/{service_id}/fulfilment/links")
async def link_passenger_service_fulfilment_records(
    agency_id: str,
    service_id: str,
    payload: PassengerServiceFulfilmentLinkRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await SpecialServicesService(db).link_fulfilment_records(agency_id, service_id, payload, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/passenger-services/{service_id}/document-requirement")
async def ensure_passenger_service_document_requirement(
    agency_id: str,
    service_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await SpecialServicesService(db).ensure_document_requirement(agency_id, service_id, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/passenger-services/{service_id}/fulfilment/confirmations")
async def record_passenger_service_confirmation(
    agency_id: str,
    service_id: str,
    payload: PassengerServiceConfirmationRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await SpecialServicesService(db).record_confirmation(agency_id, service_id, payload, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/passenger-services/{service_id}/fulfilment/reconcile")
async def reconcile_passenger_service_fulfilment(
    agency_id: str,
    service_id: str,
    payload: PassengerServiceReconciliationRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await SpecialServicesService(db).reconcile_fulfilment(agency_id, service_id, payload, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/passenger-services/{service_id}/fulfilment/outcome")
async def record_passenger_service_fulfilment_outcome(
    agency_id: str,
    service_id: str,
    payload: PassengerServiceOutcomeRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await SpecialServicesService(db).record_fulfilment_outcome(agency_id, service_id, payload, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/bookings/{booking_id}/special-services/from-parsed-pnr")
async def import_special_services_from_parsed_pnr(
    agency_id: str,
    booking_id: str,
    payload: dict,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    booking = await ensure_booking(db, agency_id, booking_id)
    trip_id = payload.get("trip_id") or booking.get("trip_id")
    if not trip_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="trip_id is required for parsed PNR import.")
    await ensure_trip(db, agency_id, trip_id)
    service = SpecialServicesService(db)
    return await service.from_parsed_pnr(agency_id, trip_id, booking_id, payload.get("parsed_pnr") or payload, user["id"])
