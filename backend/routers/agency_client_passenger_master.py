from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    ClientMasterRecordCreate,
    ClientMasterRecordUpdate,
    ClientPassengerMasterLinkCreate,
    ClientPortalAccessProfileCreate,
    PassengerKnownDocumentCreate,
    PassengerMasterRecordCreate,
    PassengerMasterRecordUpdate,
    PassengerOperationalPreferenceCreate,
    PassengerServiceHistoryCreate,
)
from services.client_passenger_master_service import (
    PHASE_LABEL,
    ClientPassengerMasterError,
    ClientPassengerMasterService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(tags=["agency-client-passenger-master"])

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


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/agencies/{agency_id}/client-master")
async def list_agency_client_master(
    agency_id: str,
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    portal_status: str | None = Query(default=None),
    passenger: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await ClientPassengerMasterService(db).agency_clients_response(
        agency_id,
        search=search,
        status=status_filter,
        portal_status=portal_status,
        passenger=passenger,
    )


@router.get("/api/agencies/{agency_id}/client-master/summary")
async def summarize_agency_client_master(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await ClientPassengerMasterService(db).agency_summary(agency_id)


@router.post("/api/agencies/{agency_id}/client-master", status_code=status.HTTP_201_CREATED)
async def create_agency_client_master(
    agency_id: str,
    payload: ClientMasterRecordCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ClientPassengerMasterService(db).create_client_record(payload, user, agency_id=agency_id)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/agencies/{agency_id}/client-master/{record_id}")
async def get_agency_client_master(
    agency_id: str,
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = ClientPassengerMasterService(db)
    try:
        record = await service.get_client_record(record_id, agency_id=agency_id)
    except ClientPassengerMasterError:
        raise not_found("Client master metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "client_master_record": record, "metadata_only": True, **service.safety_flags()}


@router.put("/api/agencies/{agency_id}/client-master/{record_id}")
async def update_agency_client_master(
    agency_id: str,
    record_id: str,
    payload: ClientMasterRecordUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ClientPassengerMasterService(db).update_client_record(record_id, payload, user, agency_id=agency_id)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/agencies/{agency_id}/client-master/{record_id}")
async def archive_agency_client_master(
    agency_id: str,
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ClientPassengerMasterService(db).archive_client_record(record_id, user, agency_id=agency_id)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/agencies/{agency_id}/passenger-master")
async def list_agency_passenger_master(
    agency_id: str,
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    service: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await ClientPassengerMasterService(db).agency_passengers_response(
        agency_id,
        search=search,
        status=status_filter,
        service=service,
    )


@router.get("/api/agencies/{agency_id}/passenger-master/summary")
async def summarize_agency_passenger_master(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await ClientPassengerMasterService(db).agency_summary(agency_id)


@router.post("/api/agencies/{agency_id}/passenger-master", status_code=status.HTTP_201_CREATED)
async def create_agency_passenger_master(
    agency_id: str,
    payload: PassengerMasterRecordCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ClientPassengerMasterService(db).create_passenger_record(payload, user, agency_id=agency_id)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/agencies/{agency_id}/passenger-master/{record_id}")
async def get_agency_passenger_master(
    agency_id: str,
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = ClientPassengerMasterService(db)
    try:
        record = await service.get_passenger_record(record_id, agency_id=agency_id)
    except ClientPassengerMasterError:
        raise not_found("Passenger master metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "passenger_master_record": record, "metadata_only": True, **service.safety_flags()}


@router.put("/api/agencies/{agency_id}/passenger-master/{record_id}")
async def update_agency_passenger_master(
    agency_id: str,
    record_id: str,
    payload: PassengerMasterRecordUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ClientPassengerMasterService(db).update_passenger_record(record_id, payload, user, agency_id=agency_id)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/agencies/{agency_id}/passenger-master/{record_id}")
async def archive_agency_passenger_master(
    agency_id: str,
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ClientPassengerMasterService(db).archive_passenger_record(record_id, user, agency_id=agency_id)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/agencies/{agency_id}/client-passenger-links", status_code=status.HTTP_201_CREATED)
async def create_agency_client_passenger_link(
    agency_id: str,
    payload: ClientPassengerMasterLinkCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ClientPassengerMasterService(db).create_link(payload, user, agency_id=agency_id)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/agencies/{agency_id}/passenger-service-history", status_code=status.HTTP_201_CREATED)
async def create_agency_passenger_service_history(
    agency_id: str,
    payload: PassengerServiceHistoryCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ClientPassengerMasterService(db).create_service_history(payload, user, agency_id=agency_id)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/agencies/{agency_id}/passenger-operational-preferences", status_code=status.HTTP_201_CREATED)
async def create_agency_passenger_operational_preference(
    agency_id: str,
    payload: PassengerOperationalPreferenceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ClientPassengerMasterService(db).create_operational_preference(payload, user, agency_id=agency_id)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/agencies/{agency_id}/passenger-known-documents", status_code=status.HTTP_201_CREATED)
async def create_agency_passenger_known_document(
    agency_id: str,
    payload: PassengerKnownDocumentCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ClientPassengerMasterService(db).create_known_document(payload, user, agency_id=agency_id)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/agencies/{agency_id}/client-portal-access-profiles", status_code=status.HTTP_201_CREATED)
async def create_agency_client_portal_access_profile(
    agency_id: str,
    payload: ClientPortalAccessProfileCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ClientPassengerMasterService(db).create_portal_access_profile(payload, user, agency_id=agency_id)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc
