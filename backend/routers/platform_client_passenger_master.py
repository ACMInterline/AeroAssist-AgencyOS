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
from services.tenant_service import require_any_platform_role


router = APIRouter(tags=["platform-client-passenger-master"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/platform/client-master")
async def list_platform_client_master(
    agency_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    portal_status: str | None = Query(default=None),
    passenger: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await ClientPassengerMasterService(db).platform_clients_response(
        agency_id=agency_id,
        search=search,
        status=status_filter,
        portal_status=portal_status,
        passenger=passenger,
        include_archived=include_archived,
    )


@router.get("/api/platform/client-master/summary")
async def summarize_platform_client_master(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await ClientPassengerMasterService(db).platform_summary(agency_id)


@router.post("/api/platform/client-master", status_code=status.HTTP_201_CREATED)
async def create_platform_client_master(
    payload: ClientMasterRecordCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ClientPassengerMasterService(db).create_client_record(payload, user)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/client-master/{record_id}")
async def get_platform_client_master(
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = ClientPassengerMasterService(db)
    try:
        record = await service.get_client_record(record_id)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "client_master_record": record, "metadata_only": True, **service.safety_flags()}


@router.put("/api/platform/client-master/{record_id}")
async def update_platform_client_master(
    record_id: str,
    payload: ClientMasterRecordUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ClientPassengerMasterService(db).update_client_record(record_id, payload, user)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/platform/client-master/{record_id}")
async def archive_platform_client_master(
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ClientPassengerMasterService(db).archive_client_record(record_id, user)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/passenger-master")
async def list_platform_passenger_master(
    agency_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    service: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await ClientPassengerMasterService(db).platform_passengers_response(
        agency_id=agency_id,
        search=search,
        status=status_filter,
        service=service,
        include_archived=include_archived,
    )


@router.get("/api/platform/passenger-master/summary")
async def summarize_platform_passenger_master(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await ClientPassengerMasterService(db).platform_summary(agency_id)


@router.post("/api/platform/passenger-master", status_code=status.HTTP_201_CREATED)
async def create_platform_passenger_master(
    payload: PassengerMasterRecordCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ClientPassengerMasterService(db).create_passenger_record(payload, user)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/passenger-master/{record_id}")
async def get_platform_passenger_master(
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = ClientPassengerMasterService(db)
    try:
        record = await service.get_passenger_record(record_id)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "passenger_master_record": record, "metadata_only": True, **service.safety_flags()}


@router.put("/api/platform/passenger-master/{record_id}")
async def update_platform_passenger_master(
    record_id: str,
    payload: PassengerMasterRecordUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ClientPassengerMasterService(db).update_passenger_record(record_id, payload, user)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/platform/passenger-master/{record_id}")
async def archive_platform_passenger_master(
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ClientPassengerMasterService(db).archive_passenger_record(record_id, user)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/platform/client-passenger-links", status_code=status.HTTP_201_CREATED)
async def create_platform_client_passenger_link(
    payload: ClientPassengerMasterLinkCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ClientPassengerMasterService(db).create_link(payload, user)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/platform/passenger-service-history", status_code=status.HTTP_201_CREATED)
async def create_platform_passenger_service_history(
    payload: PassengerServiceHistoryCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ClientPassengerMasterService(db).create_service_history(payload, user)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/platform/passenger-operational-preferences", status_code=status.HTTP_201_CREATED)
async def create_platform_passenger_operational_preference(
    payload: PassengerOperationalPreferenceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ClientPassengerMasterService(db).create_operational_preference(payload, user)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/platform/passenger-known-documents", status_code=status.HTTP_201_CREATED)
async def create_platform_passenger_known_document(
    payload: PassengerKnownDocumentCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ClientPassengerMasterService(db).create_known_document(payload, user)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/platform/client-portal-access-profiles", status_code=status.HTTP_201_CREATED)
async def create_platform_client_portal_access_profile(
    payload: ClientPortalAccessProfileCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ClientPassengerMasterService(db).create_portal_access_profile(payload, user)
    except ClientPassengerMasterError as exc:
        raise bad_request(str(exc)) from exc
