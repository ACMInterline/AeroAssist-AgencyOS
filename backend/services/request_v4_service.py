from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Iterable

from fastapi import HTTPException, status

from database import Database
from models import (
    AuditEvent,
    ClientProfile,
    PassengerServiceRequest,
    RequestCaseFlag,
    RequestPassenger,
    RequestPassengerSegmentService,
    RequestPet,
    RequestPetSegmentTransport,
    RequestSegment,
    RequestSpecialItem,
    RequestSpecialItemSegment,
    RequestedService,
    RequestTimelineEvent,
    RequestV4Payload,
    RequestV4Update,
    TravelRequest,
)
from persistence_query import MAXIMUM_QUERY_LIMIT, PaginationRequest
from persistence_repository import PersistenceRepository
from services.canonical_reference_service import (
    reference_snapshot,
    resolve_reference,
    validate_ptc_for_date,
)


REQUEST_V4_VERSION = 4
REQUEST_V4_PROJECTION_COLLECTIONS = (
    "request_passengers",
    "request_segments",
    "passenger_service_requests",
    "requested_services",
    "request_passenger_segment_services",
    "request_pets",
    "request_pet_segment_transport",
    "request_special_items",
    "request_special_item_segments",
)

SERVICE_CATEGORY_MAP = {
    "children_traveling_alone": "UMNR",
    "wheelchair_and_mobility_assistance": "PRM",
    "medical_equipment_and_travel_support": "MEDICAL",
    "service_animal": "SERVICE_ANIMAL",
    "hearing_and_visual_impairments": "PRM",
    "invisible_cognitive_or_language_support": "OTHER",
    "extra_seat_support": "SEATING",
    "special_items_and_equipment": "CARGO",
    "documents_and_travel_compliance": "OTHER",
}

SERVICE_LABELS = {
    "children_traveling_alone": "Children traveling alone",
    "wheelchair_and_mobility_assistance": "Wheelchair and mobility assistance",
    "medical_equipment_and_travel_support": "Medical equipment and travel support",
    "service_animal": "Service animal",
    "hearing_and_visual_impairments": "Hearing and visual assistance",
    "invisible_cognitive_or_language_support": "Cognitive or language support",
    "extra_seat_support": "Extra seat support",
    "special_items_and_equipment": "Special items and equipment",
    "documents_and_travel_compliance": "Documents and travel compliance",
}

LEGACY_SERVICE_KEY_MAP = {
    "mobility_assistance": "wheelchair_and_mobility_assistance",
    "medical_travel": "medical_equipment_and_travel_support",
    "unaccompanied_minor": "children_traveling_alone",
    "child_travel_support": "children_traveling_alone",
    "airport_assistance": "hearing_and_visual_impairments",
    "special_baggage": "special_items_and_equipment",
    "sports_equipment": "special_items_and_equipment",
    "documents_visa": "documents_and_travel_compliance",
    "pet_travel": "special_items_and_equipment",
    "booking_planning": "documents_and_travel_compliance",
    "disruption_support": "documents_and_travel_compliance",
    "refund_exchange": "documents_and_travel_compliance",
    "claims_support": "documents_and_travel_compliance",
    "other": "documents_and_travel_compliance",
}


def request_v4_readiness_metadata() -> dict[str, Any]:
    return {
        "canonical_owner": "TravelRequest",
        "request_version": REQUEST_V4_VERSION,
        "typed_canonical_payload_enabled": True,
        "canonical_child_projection_enabled": True,
        "compatibility_projection_enabled": True,
        "legacy_records_remain_readable": True,
        "public_intake_creates_unresolved_travelers_only": True,
        "explicit_passenger_identity_confirmation_required": True,
        "dry_run_legacy_analysis_enabled": True,
        "production_migration_enabled": False,
        "readiness_required": False,
    }


def _text(value: Any, limit: int = 1000) -> str | None:
    if value is None:
        return None
    normalized = " ".join(str(value).split())
    return normalized[:limit] if normalized else None


def _hhmm_or_empty(value: Any) -> str:
    normalized = str(value or "").strip()
    try:
        datetime.strptime(normalized, "%H:%M")
    except ValueError:
        return ""
    return normalized


def _request_source(value: str) -> str:
    mapping = {
        "public_submission": "public_website",
        "public_website": "public_website",
        "website_form": "website_form",
        "client_portal": "client_portal",
        "staff_created": "staff_created",
        "phone": "staff_created",
        "email": "staff_created",
        "whatsapp": "staff_created",
        "walk_in": "staff_created",
        "imported": "imported",
        "internal": "internal",
    }
    return mapping.get(value, "staff_created")


def _request_status(value: str) -> str:
    return value if value in {
        "draft",
        "new",
        "triage",
        "waiting_for_client",
        "in_progress",
        "ready_for_offer",
        "offer_created",
        "closed",
        "cancelled",
        "archived",
    } else "new"


def _request_priority(value: str) -> str:
    return value if value in {"low", "normal", "high", "urgent"} else "normal"


def _trip_type(quote_mode: str) -> str:
    return {
        "one_way": "one_way",
        "round_trip": "round_trip",
        "multi_city": "multi_city",
        "open_jaw": "multi_city",
    }.get(quote_mode, "unknown")


def _route_summary(payload: RequestV4Payload) -> str:
    first = payload.itinerary_segments[0]
    last = payload.itinerary_segments[-1]
    return f"{first.origin_iata or first.origin_label} -> {last.destination_iata or last.destination_label}"


def _service_summary(payload: RequestV4Payload) -> str | None:
    keys: list[str] = []
    for passenger in payload.passengers:
        keys.extend(passenger.selected_services)
    labels = [SERVICE_LABELS[key] for key in dict.fromkeys(keys)]
    return "; ".join(labels) if labels else None


async def _write_audit(
    db: Database,
    agency_id: str,
    actor_user_id: str | None,
    event_type: str,
    request_id: str,
    summary: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    event = AuditEvent(
        agency_id=agency_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type="travel_request",
        entity_id=request_id,
        summary=summary,
        metadata=metadata or {},
    )
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


async def _write_timeline(
    db: Database,
    agency_id: str,
    request_id: str,
    actor_user_id: str | None,
    event_type: str,
    title: str,
    summary: str | None = None,
) -> None:
    event = RequestTimelineEvent(
        agency_id=agency_id,
        request_id=request_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        title=title,
        summary=summary,
        visibility="internal",
        metadata={"request_version": REQUEST_V4_VERSION},
    )
    await db.collection("request_timeline_events").insert_one(event.model_dump(mode="json"))


async def _workspace_id(db: Database, agency_id: str) -> str | None:
    workspace = await db.collection("agency_workspaces").find_one({"agency_id": agency_id, "status": "active"})
    return workspace.get("id") if workspace else None


async def _next_reference(db: Database, agency_id: str) -> str:
    count = await db.collection("travel_requests").count({"agency_id": agency_id})
    return f"REQ-{count + 1:05d}"


async def _resolve_client(db: Database, agency_id: str, payload: RequestV4Payload) -> dict[str, Any]:
    existing = await db.collection("client_profiles").find_one(
        {"agency_id": agency_id, "primary_email": str(payload.contact.email)}
    )
    if existing:
        return existing
    client = ClientProfile(
        agency_id=agency_id,
        display_name=f"{payload.contact.first_name} {payload.contact.last_name}".strip(),
        primary_email=payload.contact.email,
        primary_phone=_text(payload.contact.phone, 80),
        internal_notes="Created from a canonical Request V4 contact.",
    )
    return await db.collection("client_profiles").insert_one(client.model_dump(mode="json"))


async def validate_passenger_links(db: Database, agency_id: str, payload: RequestV4Payload) -> None:
    for passenger in payload.passengers:
        if not passenger.passenger_profile_id:
            if passenger.identity_status == "confirmed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"passengers.{passenger.passenger_local_id}.identity_status cannot be confirmed without an explicitly linked passenger profile.",
                )
            continue
        profile = await db.collection("passenger_profiles").find_one(
            {"agency_id": agency_id, "id": passenger.passenger_profile_id}
        )
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"passengers.{passenger.passenger_local_id}.passenger_profile_id must belong to this agency.",
            )
        if profile.get("status") in {"archived", "duplicate_merged", "quarantined"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"passengers.{passenger.passenger_local_id}.passenger_profile_id is not an active passenger.",
            )
        passenger.identity_status = "confirmed"


async def _resolve_optional_snapshot(
    db: Database,
    domain: str,
    *,
    reference_id: str,
    code: str,
    agency_id: str,
    allow_uninitialized_legacy: bool = True,
) -> tuple[dict[str, Any] | None, str]:
    if not reference_id and not code:
        return None, "not_supplied"
    try:
        return await resolve_reference(
            db,
            domain,
            reference_id=reference_id or None,
            code=code or None,
            agency_id=agency_id,
            active_required=True,
            allow_uninitialized_legacy=allow_uninitialized_legacy,
        )
    except HTTPException as exc:
        if not reference_id and code and exc.status_code == status.HTTP_400_BAD_REQUEST:
            return None, "unknown_legacy_value"
        raise


async def resolve_request_references(
    db: Database,
    agency_id: str,
    payload: RequestV4Payload,
    *,
    historical_payload: RequestV4Payload | None = None,
    allow_legacy_ptc: bool = False,
) -> None:
    reconciliation_messages: list[str] = []

    def record_reconciliation(domain: str, code: str, resolution: str) -> None:
        if resolution == "unknown_legacy_value":
            reconciliation_messages.append(
                f"{domain}:{code} is not mapped to an active canonical reference."
            )

    historical_passengers = {
        item.passenger_local_id: item for item in historical_payload.passengers
    } if historical_payload else {}
    first_departure = payload.itinerary_segments[0].departure_date
    for passenger in payload.passengers:
        historical = historical_passengers.get(passenger.passenger_local_id)
        same_historical_reference = bool(
            historical
            and historical.passenger_type_code_id
            and (
                passenger.passenger_type_code_id == historical.passenger_type_code_id
                or (
                    not passenger.passenger_type_code_id
                    and passenger.passenger_type_code == historical.passenger_type_code
                )
            )
        )
        if same_historical_reference:
            record = await db.collection("global_reference_records").find_one(
                {
                    "domain": "passenger_types",
                    "id": historical.passenger_type_code_id,
                }
            )
            passenger.passenger_type_code_id = historical.passenger_type_code_id
            passenger.passenger_type_code = historical.passenger_type_code
            passenger.passenger_type_label = historical.passenger_type_label
            if not record:
                passenger.passenger_type_reconciliation_status = "missing_reference_historical"
                reconciliation_messages.append(
                    f"passenger_types:{historical.passenger_type_code} historical reference is missing."
                )
            elif (
                str(record.get("scope") or "global") != "global"
                and record.get("agency_id") != agency_id
            ):
                record = None
                passenger.passenger_type_reconciliation_status = "cross_scope_reference_historical"
                reconciliation_messages.append(
                    f"passenger_types:{historical.passenger_type_code} historical reference needs scope reconciliation."
                )
            else:
                passenger.passenger_type_reconciliation_status = (
                    "resolved_inactive_historical"
                    if not record.get("is_active", True)
                    else historical.passenger_type_reconciliation_status or "resolved"
                )
        else:
            if allow_legacy_ptc and not passenger.passenger_type_code_id:
                record, resolution = await _resolve_optional_snapshot(
                    db,
                    "passenger_types",
                    reference_id="",
                    code=passenger.passenger_type_code,
                    agency_id=agency_id,
                )
            else:
                record, resolution = await resolve_reference(
                    db,
                    "passenger_types",
                    reference_id=passenger.passenger_type_code_id or None,
                    code=passenger.passenger_type_code or None,
                    agency_id=agency_id,
                    active_required=True,
                    allow_uninitialized_legacy=True,
                )
            if record:
                snapshot = reference_snapshot(record)
                passenger.passenger_type_code_id = snapshot["id"]
                legacy_alias = next(
                    (
                        str(alias).upper()
                        for alias in record.get("aliases") or []
                        if str(alias).upper() == passenger.passenger_type_code.upper()
                    ),
                    None,
                )
                passenger.passenger_type_code = legacy_alias or snapshot["code"]
                passenger.passenger_type_label = snapshot["label"]
                passenger.passenger_type_reconciliation_status = (
                    "resolved"
                    if (record.get("metadata_json") or record.get("metadata") or {}).get("passenger_category")
                    else "legacy_reference_incomplete"
                )
            else:
                passenger.passenger_type_reconciliation_status = resolution
                record_reconciliation(
                    "passenger_types",
                    passenger.passenger_type_code,
                    resolution,
                )
        if record and (record.get("metadata_json") or record.get("metadata") or {}).get("passenger_category"):
            validation = validate_ptc_for_date(
                record,
                date_of_birth=passenger.date_of_birth,
                travel_date=first_departure,
            )
            passenger.calculated_age_on_first_segment = validation["age"]
            passenger.passenger_type_validation_messages = [
                *validation["errors"],
                *validation["warnings"],
            ]
            if validation["errors"] and not same_historical_reference:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "field": f"passengers.{passenger.passenger_local_id}.passenger_type_code_id",
                        "messages": validation["errors"],
                    },
                )
        elif record:
            passenger.passenger_type_validation_messages = [
                "Passenger type reference requires metadata reconciliation."
            ]

        nationality, nationality_resolution = await _resolve_optional_snapshot(
            db,
            "countries",
            reference_id=passenger.nationality_reference_id,
            code=passenger.nationality_code,
            agency_id=agency_id,
        )
        if nationality:
            snapshot = reference_snapshot(nationality)
            passenger.nationality_reference_id = snapshot["id"]
            passenger.nationality_code = snapshot["code"]
            passenger.nationality_label = snapshot["label"]
        else:
            record_reconciliation(
                "countries",
                passenger.nationality_code,
                nationality_resolution,
            )

    trip = payload.trip
    cabin, cabin_resolution = await _resolve_optional_snapshot(
        db,
        "cabin_classes",
        reference_id=trip.preferred_cabin_id,
        code=str(trip.preferred_cabin),
        agency_id=agency_id,
    )
    if cabin:
        snapshot = reference_snapshot(cabin)
        if snapshot["code"] not in {"Y", "W", "C", "F"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected cabin reference is not compatible with Request V4.",
            )
        trip.preferred_cabin_id = snapshot["id"]
        trip.preferred_cabin = snapshot["code"]
        trip.preferred_cabin_label = snapshot["label"]
    else:
        record_reconciliation(
            "cabin_classes",
            str(trip.preferred_cabin),
            cabin_resolution,
        )

    currency, currency_resolution = await _resolve_optional_snapshot(
        db,
        "currencies",
        reference_id=trip.budget_currency_id,
        code=trip.budget_currency,
        agency_id=agency_id,
    )
    if currency:
        snapshot = reference_snapshot(currency)
        trip.budget_currency_id = snapshot["id"]
        trip.budget_currency = snapshot["code"]
        trip.budget_currency_label = snapshot["label"]
    else:
        record_reconciliation("currencies", trip.budget_currency, currency_resolution)

    async def resolve_airline_list(ids: list[str], codes: list[str]) -> tuple[list[str], list[str], list[str]]:
        source: list[tuple[str, str]] = []
        if ids:
            source.extend((reference_id, "") for reference_id in ids)
        else:
            source.extend(("", code) for code in codes)
        resolved_ids: list[str] = []
        resolved_codes: list[str] = []
        resolved_labels: list[str] = []
        for reference_id, code in source:
            record, resolution = await _resolve_optional_snapshot(
                db,
                "airlines",
                reference_id=reference_id,
                code=code,
                agency_id=agency_id,
            )
            if record:
                snapshot = reference_snapshot(record)
                resolved_ids.append(snapshot["id"])
                resolved_codes.append(snapshot["code"])
                resolved_labels.append(snapshot["label"])
            elif resolution == "reference_catalogue_uninitialized" and code:
                resolved_codes.append(code)
            elif resolution == "unknown_legacy_value" and code:
                resolved_codes.append(code)
                record_reconciliation("airlines", code, resolution)
        return resolved_ids, resolved_codes, resolved_labels

    (
        trip.preferred_airline_ids,
        trip.preferred_airlines,
        trip.preferred_airline_labels,
    ) = await resolve_airline_list(trip.preferred_airline_ids, trip.preferred_airlines)
    (
        trip.excluded_airline_ids,
        trip.excluded_airlines,
        trip.excluded_airline_labels,
    ) = await resolve_airline_list(trip.excluded_airline_ids, trip.excluded_airlines)
    conflict = sorted(set(trip.preferred_airlines).intersection(trip.excluded_airlines))
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Airline cannot be both preferred and excluded: {', '.join(conflict)}.",
        )

    for segment in payload.itinerary_segments:
        for prefix, reference_id, code in (
            ("origin", segment.origin_airport_id, segment.origin_iata),
            ("destination", segment.destination_airport_id, segment.destination_iata),
        ):
            record, resolution = await _resolve_optional_snapshot(
                db,
                "airports",
                reference_id=reference_id,
                code=code,
                agency_id=agency_id,
            )
            if record:
                snapshot = reference_snapshot(record)
                setattr(segment, f"{prefix}_airport_id", snapshot["id"])
                setattr(segment, f"{prefix}_iata", snapshot["code"])
                setattr(segment, f"{prefix}_label", snapshot["label"])
                country_code = str(
                    (record.get("metadata_json") or record.get("metadata") or {}).get("country_code")
                    or ""
                ).upper()
                if country_code:
                    setattr(segment, f"{prefix}_country_code", country_code)
            else:
                record_reconciliation("airports", code, resolution)
        for prefix, reference_id, code in (
            ("marketing", segment.marketing_carrier_id, segment.marketing_carrier),
            ("operating", segment.operating_carrier_id, segment.operating_carrier),
        ):
            record, resolution = await _resolve_optional_snapshot(
                db,
                "airlines",
                reference_id=reference_id,
                code=code,
                agency_id=agency_id,
            )
            if record:
                snapshot = reference_snapshot(record)
                setattr(segment, f"{prefix}_carrier_id", snapshot["id"])
                setattr(segment, f"{prefix}_carrier", snapshot["code"])
                setattr(segment, f"{prefix}_carrier_label", snapshot["label"])
            else:
                record_reconciliation("airlines", code, resolution)
        cabin, segment_cabin_resolution = await _resolve_optional_snapshot(
            db,
            "cabin_classes",
            reference_id=segment.cabin_id,
            code=str(segment.cabin),
            agency_id=agency_id,
        )
        if cabin:
            snapshot = reference_snapshot(cabin)
            if snapshot["code"] not in {"Y", "W", "C", "F"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Segment {segment.segment_local_id} cabin reference is not Request V4 compatible.",
                )
            segment.cabin_id = snapshot["id"]
            segment.cabin = snapshot["code"]
            segment.cabin_label = snapshot["label"]
        else:
            record_reconciliation(
                "cabin_classes",
                str(segment.cabin),
                segment_cabin_resolution,
            )

    for pet in payload.pets:
        for domain, id_field, code_field, label_field in (
            ("pet_species", "species_reference_id", "species_key", "species_label"),
            ("pet_breeds", "breed_reference_id", "breed_key", "breed_label"),
            ("container_types", "container_type_reference_id", "crate_type", "container_type_label"),
        ):
            record, resolution = await _resolve_optional_snapshot(
                db,
                domain,
                reference_id=getattr(pet, id_field),
                code=getattr(pet, code_field),
                agency_id=agency_id,
            )
            if record:
                snapshot = reference_snapshot(record)
                setattr(pet, id_field, snapshot["id"])
                setattr(pet, code_field, snapshot["code"])
                setattr(pet, label_field, snapshot["label"])
            else:
                record_reconciliation(
                    domain,
                    str(getattr(pet, code_field) or ""),
                    resolution,
                )

    for item in payload.special_items:
        category, category_resolution = await _resolve_optional_snapshot(
            db,
            "special_item_categories",
            reference_id=item.item_category_reference_id,
            code=item.item_category,
            agency_id=agency_id,
        )
        if category:
            snapshot = reference_snapshot(category)
            item.item_category_reference_id = snapshot["id"]
            item.item_category_label = snapshot["label"]
        else:
            record_reconciliation(
                "special_item_categories",
                item.item_category,
                category_resolution,
            )
        currency_code = str(item.details.get("currency") or "")
        currency, item_currency_resolution = await _resolve_optional_snapshot(
            db,
            "currencies",
            reference_id=item.declared_value_currency_id,
            code=currency_code,
            agency_id=agency_id,
        )
        if currency:
            snapshot = reference_snapshot(currency)
            item.declared_value_currency_id = snapshot["id"]
            item.declared_value_currency_label = snapshot["label"]
            item.details["currency"] = snapshot["code"]
        else:
            record_reconciliation(
                "currencies",
                currency_code,
                item_currency_resolution,
            )

    payload.admin_metadata.reference_reconciliation_messages = sorted(
        set(
            [
                *payload.admin_metadata.reference_reconciliation_messages,
                *reconciliation_messages,
            ]
        )
    )


async def _upsert_projection(
    db: Database,
    collection_name: str,
    model: Any,
    agency_id: str,
    request_id: str,
    identity_filter: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    filters = {"agency_id": agency_id, "request_id": request_id, **identity_filter}
    existing = await db.collection(collection_name).find_one(filters)
    if existing:
        return await db.collection(collection_name).update_one(
            {"agency_id": agency_id, "request_id": request_id, "id": existing["id"]},
            payload,
        )
    item = model(**payload)
    return await db.collection(collection_name).insert_one(item.model_dump(mode="json"))


def _active_segment_ids(detail: dict[str, Any], local_to_id: dict[str, str]) -> tuple[list[str], list[str]]:
    local_ids = detail.get("segment_ids") or list(local_to_id)
    return local_ids, [local_to_id[value] for value in local_ids]


def _service_code(service_key: str, detail: dict[str, Any]) -> str:
    if service_key == "wheelchair_and_mobility_assistance":
        return detail.get("confirmed_ssr_code") or detail.get("suggested_ssr_code") or "MANUAL_REVIEW"
    if service_key == "children_traveling_alone":
        return "UMNR"
    if service_key == "medical_equipment_and_travel_support":
        if detail.get("portable_oxygen_concentrator"):
            return "POC"
        return "MEDA"
    if service_key == "service_animal":
        return "SVAN"
    return service_key.upper()[:32]


def _client_visible_service_details(service_key: str, detail: dict[str, Any]) -> dict[str, Any]:
    visible_keys = {
        "segment_scope_mode",
        "segment_ids",
        "child_age",
        "escort_needed",
        "airline_um_service_required",
        "confirmed_ssr_code",
        "own_mobility_device",
        "medical_clearance_needed",
        "medif_required",
        "oxygen_needed",
        "portable_oxygen_concentrator",
        "stretcher_needed",
        "companion_required",
        "fit_to_fly_status",
        "species",
        "documentation_status",
        "approval_status",
        "hearing_support",
        "visual_support",
        "preferred_communication_method",
        "escort_or_navigation_support",
        "support_type",
        "preferred_language",
        "companion_present",
        "reason",
        "extra_seat_count",
        "adjacent_seat_required",
        "item_local_ids",
        "item_type",
        "quantity",
        "weight_kg",
        "destination_documents_needed",
        "visa_transit_concern",
        "deadline",
        "notes",
    }
    return {key: value for key, value in detail.items() if key in visible_keys}


async def project_canonical_request(
    db: Database,
    request: dict[str, Any],
    payload: RequestV4Payload,
) -> dict[str, Any]:
    agency_id = request["agency_id"]
    request_id = request["id"]
    workspace_id = request.get("workspace_id") or await _workspace_id(db, agency_id)
    passenger_local_to_record: dict[str, dict[str, Any]] = {}
    for index, passenger in enumerate(payload.passengers):
        profile = None
        if passenger.passenger_profile_id:
            profile = await db.collection("passenger_profiles").find_one(
                {"agency_id": agency_id, "id": passenger.passenger_profile_id}
            )
        proposed_identity = {
            "first_name": passenger.first_name,
            "last_name": passenger.last_name,
            "display_name": " ".join(part for part in [passenger.first_name, passenger.last_name] if part),
            "date_of_birth": passenger.date_of_birth,
            "passenger_type": passenger.passenger_type_code,
            "nationality": passenger.nationality_code or passenger.nationality_label,
        }
        display_name = (
            profile.get("display_name")
            if profile
            else proposed_identity["display_name"] or f"Unresolved traveler {index + 1}"
        )
        row = await _upsert_projection(
            db,
            "request_passengers",
            RequestPassenger,
            agency_id,
            request_id,
            {"passenger_local_id": passenger.passenger_local_id},
            {
                "agency_id": agency_id,
                "workspace_id": workspace_id,
                "request_id": request_id,
                "travel_request_id": request_id,
                "passenger_local_id": passenger.passenger_local_id,
                "passenger_id": passenger.passenger_profile_id,
                "passenger_link_mode": "existing" if profile else "unresolved",
                "role_in_request": "traveler",
                "is_primary_traveler": index == 0,
                "service_needs_summary": _text(passenger.notes, 1000),
                "snapshot_display_name": display_name,
                "snapshot_date_of_birth": passenger.date_of_birth,
                "snapshot_passenger_type": passenger.passenger_type_code,
                "passenger_type_code_id": passenger.passenger_type_code_id or None,
                "passenger_type_code": passenger.passenger_type_code,
                "passenger_type_label": passenger.passenger_type_label,
                "passenger_type_reconciliation_status": passenger.passenger_type_reconciliation_status,
                "passenger_type_validation_messages": passenger.passenger_type_validation_messages,
                "calculated_age_on_first_segment": passenger.calculated_age_on_first_segment,
                "nationality_reference_id": passenger.nationality_reference_id or None,
                "nationality_label": passenger.nationality_label or None,
                "nationality_code": passenger.nationality_code or None,
                "selected_services": passenger.selected_services,
                "service_details": passenger.service_details,
                "identity_status": "confirmed" if profile else "unresolved",
                "identity_source": "explicit_existing_passenger_profile" if profile else "request_v4_unresolved",
                "proposed_identity_json": {} if profile else proposed_identity,
                "canonical_request_version": REQUEST_V4_VERSION,
                "canonical_projection": True,
                "status": "active",
            },
        )
        passenger_local_to_record[passenger.passenger_local_id] = row

    segment_local_to_record: dict[str, dict[str, Any]] = {}
    for segment in payload.itinerary_segments:
        row = await _upsert_projection(
            db,
            "request_segments",
            RequestSegment,
            agency_id,
            request_id,
            {"segment_local_id": segment.segment_local_id},
            {
                "agency_id": agency_id,
                "workspace_id": workspace_id,
                "request_id": request_id,
                "travel_request_id": request_id,
                "segment_local_id": segment.segment_local_id,
                "sequence": segment.segment_order,
                "origin_text": segment.origin_label,
                "origin_airport_id": segment.origin_airport_id or None,
                "origin_airport_code": segment.origin_iata or None,
                "origin_country_id": segment.origin_country_id or None,
                "origin_country": segment.origin_country_code or None,
                "destination_text": segment.destination_label,
                "destination_airport_id": segment.destination_airport_id or None,
                "destination_airport_code": segment.destination_iata or None,
                "destination_country_id": segment.destination_country_id or None,
                "destination_country": segment.destination_country_code or None,
                "departure_date": segment.departure_date,
                "departure_time_window": segment.departure_time or None,
                "arrival_date": segment.arrival_date,
                "arrival_time_window": segment.arrival_time or None,
                "marketing_airline": segment.marketing_carrier or None,
                "marketing_airline_id": segment.marketing_carrier_id or None,
                "marketing_airline_label": segment.marketing_carrier_label or None,
                "operating_airline": segment.operating_carrier or None,
                "operating_airline_id": segment.operating_carrier_id or None,
                "operating_airline_label": segment.operating_carrier_label or None,
                "preferred_airline_code": segment.marketing_carrier or None,
                "preferred_flight_number": segment.flight_number or None,
                "cabin_preference": segment.cabin,
                "cabin_reference_id": segment.cabin_id or None,
                "cabin_label": segment.cabin_label or None,
                "canonical_request_version": REQUEST_V4_VERSION,
                "canonical_projection": True,
                "notes": _text(segment.notes, 2000),
                "status": "active",
            },
        )
        segment_local_to_record[segment.segment_local_id] = row

    segment_local_to_id = {
        local_id: record["id"] for local_id, record in segment_local_to_record.items()
    }
    aggregate_services: dict[str, dict[str, Any]] = {}
    for passenger in payload.passengers:
        passenger_record = passenger_local_to_record[passenger.passenger_local_id]
        for service_key in passenger.selected_services:
            detail = passenger.service_details[service_key]
            local_segment_ids, segment_ids = _active_segment_ids(detail, segment_local_to_id)
            service_code = _service_code(service_key, detail)
            generated_key = f"request-v4:{passenger.passenger_local_id}:{service_key}"
            service_request = await _upsert_projection(
                db,
                "passenger_service_requests",
                PassengerServiceRequest,
                agency_id,
                request_id,
                {"generated_key": generated_key},
                {
                    "agency_id": agency_id,
                    "request_id": request_id,
                    "request_passenger_id": passenger_record["id"],
                    "request_passenger_local_id": passenger.passenger_local_id,
                    "request_segment_ids": segment_ids,
                    "request_segment_local_ids": local_segment_ids,
                    "request_service_key": service_key,
                    "segment_scope_mode": detail["segment_scope_mode"],
                    "passenger_id": passenger.passenger_profile_id,
                    "segment_id": segment_ids[0] if len(segment_ids) == 1 else None,
                    "service_key": service_key,
                    "service_label": SERVICE_LABELS[service_key],
                    "service_catalogue_category": service_key,
                    "category": SERVICE_CATEGORY_MAP[service_key],
                    "service_type": service_code,
                    "ssr_code": service_code if service_code in {"WCHR", "WCHS", "WCHC", "UMNR", "MEDA", "POC", "SVAN"} else None,
                    "metadata_json": {"request_version": REQUEST_V4_VERSION},
                    "client_visible_details_json": _client_visible_service_details(service_key, detail),
                    "internal_details_json": detail,
                    "generated_key": generated_key,
                    "canonical_request_version": REQUEST_V4_VERSION,
                    "canonical_projection": True,
                    "status": "requested",
                },
            )
            aggregate = aggregate_services.setdefault(
                service_key,
                {
                    "passenger_ids": [],
                    "segment_ids": [],
                    "passenger_service_request_ids": [],
                    "relation_ids": [],
                    "details": [],
                },
            )
            if passenger.passenger_profile_id:
                aggregate["passenger_ids"].append(passenger.passenger_profile_id)
            aggregate["segment_ids"].extend(segment_ids)
            aggregate["passenger_service_request_ids"].append(service_request["id"])
            aggregate["details"].append(detail)
            for segment_id, segment_local_id in zip(segment_ids, local_segment_ids):
                relation_key = (
                    f"request-v4:{passenger.passenger_local_id}:{segment_local_id}:{service_key}"
                )
                relation = await _upsert_projection(
                    db,
                    "request_passenger_segment_services",
                    RequestPassengerSegmentService,
                    agency_id,
                    request_id,
                    {"generated_key": relation_key},
                    {
                        "agency_id": agency_id,
                        "workspace_id": workspace_id,
                        "request_id": request_id,
                        "travel_request_id": request_id,
                        "request_passenger_id": passenger_record["id"],
                        "request_segment_id": segment_id,
                        "passenger_id": passenger.passenger_profile_id,
                        "segment_id": segment_id,
                        "service_key": service_key,
                        "service_family_code": service_key,
                        "service_code": service_code,
                        "service_label": SERVICE_LABELS[service_key],
                        "service_details_json": detail,
                        "applicability_status": "requested",
                        "generated_key": relation_key,
                        "notes": _text(detail.get("notes"), 1000),
                    },
                )
                aggregate["relation_ids"].append(relation["id"])

    for service_key, aggregate in aggregate_services.items():
        first_detail = aggregate["details"][0]
        service_code = _service_code(service_key, first_detail)
        requested_service = await _upsert_projection(
            db,
            "requested_services",
            RequestedService,
            agency_id,
            request_id,
            {"service_key": service_key, "canonical_request_version": REQUEST_V4_VERSION},
            {
                "agency_id": agency_id,
                "workspace_id": workspace_id,
                "request_id": request_id,
                "travel_request_id": request_id,
                "passenger_service_request_id": aggregate[
                    "passenger_service_request_ids"
                ][0],
                "request_passenger_segment_service_ids": aggregate["relation_ids"],
                "service_key": service_key,
                "service_family_code": service_key,
                "service_code": service_code,
                "service_name": SERVICE_LABELS[service_key],
                "service_category": service_key,
                "service_details_json": first_detail,
                "status": "requested",
                "details": _text(first_detail.get("notes"), 2000),
                "detail_payload": first_detail,
                "passenger_ids": list(dict.fromkeys(aggregate["passenger_ids"])),
                "segment_ids": list(dict.fromkeys(aggregate["segment_ids"])),
                "applies_to_all_passengers": len(aggregate["details"]) == len(payload.passengers),
                "applies_to_all_segments": all(
                    detail.get("segment_scope_mode") == "all_segments"
                    for detail in aggregate["details"]
                ),
                "canonical_request_version": REQUEST_V4_VERSION,
                "canonical_projection": True,
                "client_visible_summary": SERVICE_LABELS[service_key],
            },
        )
        for relation_id in aggregate["relation_ids"]:
            await db.collection("request_passenger_segment_services").update_one(
                {
                    "agency_id": agency_id,
                    "request_id": request_id,
                    "id": relation_id,
                },
                {"requested_service_id": requested_service["id"]},
            )

    for pet in payload.pets:
        passenger_record = (
            passenger_local_to_record.get(pet.linked_passenger_local_id)
            if pet.linked_passenger_local_id
            else None
        )
        local_segment_ids = pet.segment_ids or list(segment_local_to_record)
        pet_row = await _upsert_projection(
            db,
            "request_pets",
            RequestPet,
            agency_id,
            request_id,
            {"pet_local_id": pet.pet_local_id},
            {
                "agency_id": agency_id,
                "workspace_id": workspace_id,
                "request_id": request_id,
                "travel_request_id": request_id,
                "request_passenger_id": passenger_record.get("id") if passenger_record else None,
                "passenger_id": passenger_record.get("passenger_id") if passenger_record else None,
                "pet_local_id": pet.pet_local_id,
                "linked_passenger_local_id": pet.linked_passenger_local_id,
                "segment_scope_mode": pet.segment_scope_mode,
                "segment_local_ids": local_segment_ids,
                "pet_category": pet.pet_category,
                "species_reference_id": pet.species_reference_id or None,
                "species": pet.species_label,
                "species_key": pet.species_key or None,
                "breed_reference_id": pet.breed_reference_id or None,
                "breed": pet.breed_label or None,
                "breed_key": pet.breed_key or None,
                "colour": pet.colour or None,
                "sex": pet.sex or None,
                "date_of_birth": pet.date_of_birth,
                "age_text": pet.age_text or None,
                "is_pregnant": pet.is_pregnant,
                "is_nursing": pet.is_nursing,
                "aggression_risk": pet.aggression_risk,
                "aggression_notes": pet.aggression_notes or None,
                "pet_weight_kg": pet.pet_weight_kg,
                "container_weight_kg": pet.container_weight_kg,
                "combined_weight_kg": pet.total_weight_kg,
                "requested_transport_mode": pet.pet_category.lower(),
                "carrier_dimensions_cm": {
                    "length_cm": pet.carrier_length_cm,
                    "width_cm": pet.carrier_width_cm,
                    "height_cm": pet.carrier_height_cm,
                },
                "container_type_reference_id": pet.container_type_reference_id or None,
                "container_type_label": pet.container_type_label or None,
                "crate_type": pet.crate_type or None,
                "vaccination_passport_uploaded": pet.vaccination_passport_uploaded,
                "rabies_vaccination_date": pet.rabies_vaccination_date,
                "rabies_serology_done": pet.rabies_serology_done,
                "rabies_serology_date": pet.rabies_serology_date,
                "rabies_serology_result": pet.rabies_serology_result or None,
                "microchip_number": pet.microchip_number or None,
                "microchip_implantation_date": pet.microchip_implantation_date,
                "eu_pet_passport": pet.eu_pet_passport,
                "import_permits_notes": pet.import_permits_notes or None,
                "quarantine_documents_notes": pet.quarantine_documents_notes or None,
                "country_specific_restrictions_notes": pet.country_specific_restrictions_notes or None,
                "documentation_status": "provided" if pet.vaccination_passport_uploaded else "pending_information",
                "special_requirements": pet.special_instructions or None,
                "carrier_required": pet.pet_category in {"PETC", "AVIH"},
                "service_animal": pet.pet_category == "SVAN",
                "generated_key": f"request-v4:pet:{pet.pet_local_id}",
                "canonical_request_version": REQUEST_V4_VERSION,
                "canonical_projection": True,
                "notes": pet.special_instructions or None,
                "status": "active",
            },
        )
        for local_segment_id in local_segment_ids:
            segment_id = segment_local_to_record[local_segment_id]["id"]
            generated_key = f"request-v4:pet-segment:{pet.pet_local_id}:{local_segment_id}"
            await _upsert_projection(
                db,
                "request_pet_segment_transport",
                RequestPetSegmentTransport,
                agency_id,
                request_id,
                {"generated_key": generated_key},
                {
                    "agency_id": agency_id,
                    "workspace_id": workspace_id,
                    "request_id": request_id,
                    "travel_request_id": request_id,
                    "request_pet_id": pet_row["id"],
                    "request_segment_id": segment_id,
                    "requested_transport_mode": pet.pet_category.lower(),
                    "transport_mode": pet.pet_category.lower(),
                    "generated_key": generated_key,
                    "status": "requested",
                },
            )

    item_category_map = {
        "weapon": "other",
        "sports_equipment": "sports_equipment",
        "musical_instrument": "musical_instrument",
        "valuables_fragile": "valuable_item",
        "other": "other",
    }
    for item in payload.special_items:
        passenger_record = (
            passenger_local_to_record.get(item.linked_passenger_local_id)
            if item.linked_passenger_local_id
            else None
        )
        local_segment_ids = item.segment_ids or list(segment_local_to_record)
        details = item.details
        category_code = item_category_map[item.item_category]
        item_name = (
            details.get("weapon_type")
            or details.get("equipment_type")
            or details.get("instrument_type")
            or details.get("item_type")
            or item.item_category.replace("_", " ")
        )
        item_row = await _upsert_projection(
            db,
            "request_special_items",
            RequestSpecialItem,
            agency_id,
            request_id,
            {"item_local_id": item.item_local_id},
            {
                "agency_id": agency_id,
                "workspace_id": workspace_id,
                "request_id": request_id,
                "travel_request_id": request_id,
                "request_passenger_id": passenger_record.get("id") if passenger_record else None,
                "owner_passenger_id": passenger_record.get("passenger_id") if passenger_record else None,
                "item_local_id": item.item_local_id,
                "linked_passenger_local_id": item.linked_passenger_local_id,
                "segment_scope_mode": item.segment_scope_mode,
                "segment_local_ids": local_segment_ids,
                "item_type": item.item_category,
                "item_category_reference_id": item.item_category_reference_id or None,
                "item_category_label": item.item_category_label or None,
                "item_category_code": category_code,
                "item_name": item_name,
                "description": details.get("notes") or item_name,
                "quantity": int(details.get("quantity") or 1),
                "weight_kg": details.get("weight_kg"),
                "dimensions_cm": {
                    "length_cm": details.get("length_cm"),
                    "width_cm": details.get("width_cm"),
                    "height_cm": details.get("height_cm"),
                },
                "transport_location": "passenger_cabin" if details.get("cabin_transport_requested") else "checked_baggage",
                "usage_in_cabin_flag": bool(details.get("cabin_transport_requested")),
                "special_handling_instructions": details.get("notes"),
                "documentation_status": details.get("approval_status"),
                "declared_value_currency_id": item.declared_value_currency_id or None,
                "declared_value_currency_label": item.declared_value_currency_label or None,
                "requires_policy_check": True,
                "generated_key": f"request-v4:item:{item.item_local_id}",
                "canonical_request_version": REQUEST_V4_VERSION,
                "canonical_projection": True,
                "canonical_details": details,
                "notes": details.get("notes"),
                "status": "active",
            },
        )
        for local_segment_id in local_segment_ids:
            segment_id = segment_local_to_record[local_segment_id]["id"]
            generated_key = f"request-v4:item-segment:{item.item_local_id}:{local_segment_id}"
            await _upsert_projection(
                db,
                "request_special_item_segments",
                RequestSpecialItemSegment,
                agency_id,
                request_id,
                {"generated_key": generated_key},
                {
                    "agency_id": agency_id,
                    "workspace_id": workspace_id,
                    "request_id": request_id,
                    "travel_request_id": request_id,
                    "request_special_item_id": item_row["id"],
                    "request_segment_id": segment_id,
                    "transport_location": "passenger_cabin" if details.get("cabin_transport_requested") else "checked_baggage",
                    "applicability_status": "requested",
                    "generated_key": generated_key,
                },
            )

    service_keys = {
        service_key
        for passenger in payload.passengers
        for service_key in passenger.selected_services
    }
    case_flags: dict[str, tuple[str, str]] = {}
    if service_keys:
        case_flags["segment_scoped_services"] = ("Segment-scoped services", "info")
    if "medical_equipment_and_travel_support" in service_keys:
        case_flags["medical_review"] = ("Medical review required", "high")
    if (
        "documents_and_travel_compliance" in service_keys
        or payload.pets
        or payload.special_items
    ):
        case_flags["document_followup"] = ("Document follow-up required", "medium")
    if payload.pets:
        case_flags["pet_transport"] = ("Pet transport requested", "medium")
    if payload.special_items:
        case_flags["special_items"] = ("Special item transport requested", "medium")
    for flag_code, (flag_label, severity) in case_flags.items():
        await _upsert_projection(
            db,
            "request_case_flags",
            RequestCaseFlag,
            agency_id,
            request_id,
            {"generated_key": f"request-v4:flag:{flag_code}"},
            {
                "agency_id": agency_id,
                "workspace_id": workspace_id,
                "request_id": request_id,
                "travel_request_id": request_id,
                "flag_code": flag_code,
                "flag_label": flag_label,
                "severity": severity,
                "source": "canonical_v4_projection",
                "generated_key": f"request-v4:flag:{flag_code}",
                "status": "active",
            },
        )
    for flag_code in {
        "segment_scoped_services",
        "medical_review",
        "document_followup",
        "pet_transport",
        "special_items",
    }.difference(case_flags):
        existing_flag = await db.collection("request_case_flags").find_one(
            {
                "agency_id": agency_id,
                "request_id": request_id,
                "generated_key": f"request-v4:flag:{flag_code}",
            }
        )
        if existing_flag and existing_flag.get("status") == "active":
            await db.collection("request_case_flags").update_one(
                {
                    "agency_id": agency_id,
                    "request_id": request_id,
                    "id": existing_flag["id"],
                },
                {"status": "archived"},
            )

    return {
        "passenger_count": len(payload.passengers),
        "segment_count": len(payload.itinerary_segments),
        "service_count": len(aggregate_services),
        "pet_count": len(payload.pets),
        "special_item_count": len(payload.special_items),
    }


def _request_parent_updates(payload: RequestV4Payload) -> dict[str, Any]:
    first_segment = payload.itinerary_segments[0]
    last_segment = payload.itinerary_segments[-1]
    service_keys = {
        key for passenger in payload.passengers for key in passenger.selected_services
    }
    return {
        "request_version": REQUEST_V4_VERSION,
        "canonical_payload": payload.model_dump(mode="json"),
        "canonical_payload_updated_at": datetime.now(timezone.utc),
        "canonical_projection_status": "syncing",
        "canonical_projection_warnings": list(
            payload.admin_metadata.reference_reconciliation_messages
        ),
        "title": payload.trip.trip_label
        or f"{payload.contact.first_name} {payload.contact.last_name} request",
        "status": _request_status(payload.admin_metadata.status),
        "priority": _request_priority(payload.admin_metadata.priority),
        "source": _request_source(payload.admin_metadata.source),
        "trip_type": _trip_type(payload.trip.quote_mode),
        "requested_departure_date": first_segment.departure_date,
        "requested_return_date": (
            last_segment.arrival_date or last_segment.departure_date
            if payload.trip.quote_mode in {"round_trip", "multi_city", "open_jaw"}
            else None
        ),
        "route_summary": _route_summary(payload),
        "service_summary": _service_summary(payload),
        "origin_summary": first_segment.origin_iata or first_segment.origin_label,
        "destination_summary": last_segment.destination_iata or last_segment.destination_label,
        "first_departure_date": first_segment.departure_date,
        "last_arrival_date": last_segment.arrival_date,
        "requires_medical_review": "medical_equipment_and_travel_support" in service_keys,
        "requires_airline_policy_review": bool(
            service_keys
            or payload.pets
            or payload.special_items
        ),
        "requires_document_followup": (
            "documents_and_travel_compliance" in service_keys
            or any(
                pet.pet_category in {"PETC", "AVIH", "SVAN"}
                and not pet.vaccination_passport_uploaded
                for pet in payload.pets
            )
        ),
        "has_existing_passenger_links": any(
            passenger.passenger_profile_id for passenger in payload.passengers
        ),
        "client_notes": _text(payload.request_level_notes, 4000),
        "internal_notes": _text(payload.admin_metadata.internal_notes, 4000),
        "assigned_user_id": payload.admin_metadata.assigned_to or None,
        "builder_payload_snapshot": {
            "request_version": REQUEST_V4_VERSION,
            "source": "canonical_payload",
        },
        "canonical_alignment_notes": {
            "canonical_owner": "TravelRequest",
            "child_projection_owner": "request_v4_service",
            "compatibility_projection": True,
        },
    }


async def create_request_v4(
    db: Database,
    agency_id: str,
    payload: RequestV4Payload,
    actor_user_id: str,
    *,
    source_intake_id: str | None = None,
    allow_legacy_ptc: bool = False,
) -> dict[str, Any]:
    await resolve_request_references(
        db,
        agency_id,
        payload,
        allow_legacy_ptc=allow_legacy_ptc,
    )
    await validate_passenger_links(db, agency_id, payload)
    client = await _resolve_client(db, agency_id, payload)
    parent = TravelRequest(
        agency_id=agency_id,
        workspace_id=await _workspace_id(db, agency_id),
        client_id=client["id"],
        created_by_user_id=actor_user_id,
        request_reference=await _next_reference(db, agency_id),
        source_intake_id=source_intake_id,
        source_entry_path="/api/public/requests" if source_intake_id else "/api/agencies/{agency_id}/requests",
        submission_channel="public_website" if source_intake_id else "staff_console",
        account_origin_at_submission="new_public_contact" if source_intake_id else "staff_created",
        **_request_parent_updates(payload),
    )
    created = await db.collection("travel_requests").insert_one(parent.model_dump(mode="json"))
    try:
        counts = await project_canonical_request(db, created, payload)
    except Exception as exc:
        await db.collection("travel_requests").update_one(
            {"agency_id": agency_id, "id": created["id"]},
            {
                "canonical_projection_status": "reconciliation_required",
                "canonical_projection_warnings": [
                    f"Compatibility projection requires retry ({exc.__class__.__name__})."
                ],
            },
        )
        raise
    updated = await db.collection("travel_requests").update_one(
        {"agency_id": agency_id, "id": created["id"]},
        {
            "canonical_projection_status": "current",
            "passenger_count": counts["passenger_count"],
            "service_count": counts["service_count"],
            "pet_count": counts["pet_count"],
            "special_service_count": (
                counts["service_count"] + counts["pet_count"] + counts["special_item_count"]
            ),
        },
    )
    await _write_audit(
        db,
        agency_id,
        actor_user_id,
        "request.v4_created",
        created["id"],
        f"Created canonical Request V4 {created['request_reference']}.",
        counts,
    )
    await _write_timeline(
        db,
        agency_id,
        created["id"],
        actor_user_id,
        "request.v4_created",
        "Request created",
        _route_summary(payload),
    )
    return await request_detail_v4(db, updated)


def _merge_collection(
    current: list[dict[str, Any]],
    submitted: list[dict[str, Any]],
    local_id_field: str,
    removed_ids: Iterable[str],
) -> list[dict[str, Any]]:
    removed = set(removed_ids)
    if removed.intersection(item[local_id_field] for item in submitted):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{local_id_field} cannot be both submitted and explicitly removed.",
        )
    result = list(submitted)
    submitted_ids = {item[local_id_field] for item in submitted}
    result.extend(
        item
        for item in current
        if item[local_id_field] not in submitted_ids and item[local_id_field] not in removed
    )
    return result


async def _archive_removed_projection(
    db: Database,
    agency_id: str,
    request_id: str,
    collection_name: str,
    local_id_field: str,
    removed_ids: Iterable[str],
    status_value: str,
) -> None:
    for local_id in set(removed_ids):
        existing = await db.collection(collection_name).find_one(
            {
                "agency_id": agency_id,
                "request_id": request_id,
                local_id_field: local_id,
                "canonical_request_version": REQUEST_V4_VERSION,
            }
        )
        if existing:
            await db.collection(collection_name).update_one(
                {"agency_id": agency_id, "request_id": request_id, "id": existing["id"]},
                {"status": status_value},
            )


async def update_request_v4(
    db: Database,
    agency_id: str,
    request_id: str,
    update: RequestV4Update,
    actor_user_id: str,
) -> dict[str, Any]:
    request = await db.collection("travel_requests").find_one(
        {"agency_id": agency_id, "id": request_id}
    )
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    if request.get("request_version") != REQUEST_V4_VERSION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Legacy requests remain readable but must be reconciled before canonical V4 aggregate editing.",
        )
    current_payload = RequestV4Payload.model_validate(request.get("canonical_payload") or {})
    submitted = update.canonical_payload.model_dump(mode="json")
    current = current_payload.model_dump(mode="json")
    submitted["passengers"] = _merge_collection(
        current["passengers"],
        submitted["passengers"],
        "passenger_local_id",
        update.remove_passenger_local_ids,
    )
    submitted["itinerary_segments"] = _merge_collection(
        current["itinerary_segments"],
        submitted["itinerary_segments"],
        "segment_local_id",
        update.remove_segment_local_ids,
    )
    submitted["pets"] = _merge_collection(
        current["pets"],
        submitted["pets"],
        "pet_local_id",
        update.remove_pet_local_ids,
    )
    submitted["special_items"] = _merge_collection(
        current["special_items"],
        submitted["special_items"],
        "item_local_id",
        update.remove_item_local_ids,
    )
    payload = RequestV4Payload.model_validate(submitted)
    await resolve_request_references(
        db,
        agency_id,
        payload,
        historical_payload=current_payload,
    )
    await validate_passenger_links(db, agency_id, payload)
    client = await _resolve_client(db, agency_id, payload)
    await db.collection("travel_requests").update_one(
        {"agency_id": agency_id, "id": request_id},
        {"client_id": client["id"], **_request_parent_updates(payload)},
    )
    try:
        counts = await project_canonical_request(db, request, payload)
        await _archive_removed_projection(
            db,
            agency_id,
            request_id,
            "request_passengers",
            "passenger_local_id",
            update.remove_passenger_local_ids,
            "archived",
        )
        await _archive_removed_projection(
            db,
            agency_id,
            request_id,
            "request_segments",
            "segment_local_id",
            update.remove_segment_local_ids,
            "archived",
        )
        await _archive_removed_projection(
            db,
            agency_id,
            request_id,
            "request_pets",
            "pet_local_id",
            update.remove_pet_local_ids,
            "archived",
        )
        await _archive_removed_projection(
            db,
            agency_id,
            request_id,
            "request_special_items",
            "item_local_id",
            update.remove_item_local_ids,
            "archived",
        )
    except Exception as exc:
        await db.collection("travel_requests").update_one(
            {"agency_id": agency_id, "id": request_id},
            {
                "canonical_projection_status": "reconciliation_required",
                "canonical_projection_warnings": [
                    f"Canonical data was saved; compatibility projection requires retry ({exc.__class__.__name__})."
                ],
            },
        )
        raise
    await db.collection("travel_requests").update_one(
        {"agency_id": agency_id, "id": request_id},
        {
            "canonical_projection_status": "current",
            "canonical_projection_warnings": list(
                payload.admin_metadata.reference_reconciliation_messages
            ),
            "passenger_count": counts["passenger_count"],
            "service_count": counts["service_count"],
            "pet_count": counts["pet_count"],
            "special_service_count": (
                counts["service_count"] + counts["pet_count"] + counts["special_item_count"]
            ),
        },
    )
    await _write_audit(
        db,
        agency_id,
        actor_user_id,
        "request.v4_updated",
        request_id,
        "Updated canonical Request V4 aggregate.",
        {
            "explicit_removals": {
                "passengers": update.remove_passenger_local_ids,
                "segments": update.remove_segment_local_ids,
                "pets": update.remove_pet_local_ids,
                "special_items": update.remove_item_local_ids,
            }
        },
    )
    await _write_timeline(
        db,
        agency_id,
        request_id,
        actor_user_id,
        "request.v4_updated",
        "Request details updated",
    )
    return await request_detail_v4(db, request_id=request_id, agency_id=agency_id)


async def request_detail_v4(
    db: Database,
    request: dict[str, Any] | None = None,
    *,
    agency_id: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    if request is None:
        request = await db.collection("travel_requests").find_one(
            {"agency_id": agency_id, "id": request_id}
        )
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    agency_id = request["agency_id"]
    request_id = request["id"]
    client = await db.collection("client_profiles").find_one(
        {"agency_id": agency_id, "id": request["client_id"]}
    )
    linked_trip = (
        await db.collection("trip_dossiers").find_one(
            {"agency_id": agency_id, "id": request["trip_id"]}
        )
        if request.get("trip_id")
        else None
    )
    repository = PersistenceRepository(db)

    async def related(
        collection_name: str,
        *,
        filters: dict[str, Any] | None = None,
        sort_field: str = "created_at",
    ) -> list[dict[str, Any]]:
        page = await repository.find_agency_records(
            collection_name=collection_name,
            agency_id=agency_id,
            filters={"request_id": request_id, **(filters or {})},
            sort_field=sort_field,
            sort_direction="asc",
            pagination=PaginationRequest.build(limit=MAXIMUM_QUERY_LIMIT),
        )
        return page.items

    detail = {
        "request": request,
        "client": client,
        "linked_trip": linked_trip,
        "passengers": await related("request_passengers", filters={"status": "active"}),
        "segments": await related(
            "request_segments",
            filters={"status": "active"},
            sort_field="sequence",
        ),
        "services": await related("requested_services"),
        "passenger_services": await related("passenger_service_requests"),
        "case_flags": await related("request_case_flags", filters={"status": "active"}),
        "passenger_segment_services": await related(
            "request_passenger_segment_services"
        ),
        "pets": await related("request_pets", filters={"status": "active"}),
        "pet_segment_transport": await related("request_pet_segment_transport"),
        "special_items": await related(
            "request_special_items",
            filters={"status": "active"},
        ),
        "special_item_segments": await related("request_special_item_segments"),
        "messages": await related("request_messages"),
        "tasks": await related("request_tasks"),
        "timeline": await related("request_timeline_events"),
    }
    if request.get("request_version") == REQUEST_V4_VERSION:
        detail["canonical_request"] = RequestV4Payload.model_validate(
            request.get("canonical_payload") or {}
        ).model_dump(mode="json")
        detail["migration_status"] = "canonical_v4"
    else:
        detail["canonical_request"] = None
        detail["migration_status"] = "legacy_readable_manual_reconciliation"
    return detail


def _legacy_service_detail(
    service_key: str,
    details: dict[str, Any],
    segment_scope_mode: str,
    segment_ids: list[str],
) -> dict[str, Any]:
    scope = {
        "segment_scope_mode": segment_scope_mode,
        "segment_ids": segment_ids,
    }
    if service_key == "wheelchair_and_mobility_assistance":
        suggested = (
            details.get("suggested_ssr_code")
            or details.get("confirmed_ssr_code")
            or "manual_review"
        )
        confirmed = details.get("confirmed_ssr_code") or suggested
        if confirmed == "use_suggested":
            confirmed = suggested
        return {
            **scope,
            "assessment_version": details.get("assessment_version") or "v2_assessment_driven",
            "passenger_context_tags": details.get("passenger_context_tags") or [],
            "passenger_context_notes": details.get("passenger_context_notes") or "",
            "functional_assessment": details.get("functional_assessment") or {},
            "suggested_ssr_code": suggested,
            "suggested_ssr_reason": details.get("suggested_ssr_reason") or "",
            "recommendation_confidence": details.get("recommendation_confidence") or "manual_review",
            "confirmed_ssr_code": confirmed,
            "override_reason": details.get("override_reason") or "",
            "final_assistance_label": details.get("final_assistance_label") or "",
            "own_mobility_device": details.get("own_mobility_device") or "no",
            "own_device_details": details.get("own_device_details") or {},
            "battery_details": details.get("battery_details") or {},
        }
    if service_key == "children_traveling_alone":
        return {
            **scope,
            "child_age": int(details["child_age"]) if str(details.get("child_age") or "").isdigit() else None,
            "escort_needed": bool(details.get("escort_needed")),
            "handover_contact": details.get("handover_contact") or "",
            "pickup_contact": details.get("pickup_contact") or "",
            "airline_um_service_required": bool(details.get("airline_um_service_required")),
            "notes": details.get("notes") or "",
        }
    if service_key == "medical_equipment_and_travel_support":
        return {
            **scope,
            "medical_clearance_needed": bool(details.get("medical_clearance_needed")),
            "medif_required": bool(details.get("medif_required")),
            "oxygen_needed": bool(details.get("oxygen_needed")),
            "portable_oxygen_concentrator": bool(details.get("portable_oxygen_concentrator")),
            "equipment_type": details.get("equipment_type") or "",
            "device_make_model": details.get("device_make_model") or "",
            "stretcher_needed": bool(details.get("stretcher_needed")),
            "companion_required": bool(details.get("companion_required")),
            "fit_to_fly_status": details.get("fit_to_fly_status") or "unknown",
            "notes": details.get("notes") or "",
        }
    if service_key == "hearing_and_visual_impairments":
        return {
            **scope,
            "hearing_support": bool(details.get("hearing_support")),
            "visual_support": bool(details.get("visual_support")),
            "preferred_communication_method": details.get("preferred_communication_method") or "",
            "escort_or_navigation_support": True,
            "notes": details.get("summary") or "",
        }
    if service_key == "special_items_and_equipment":
        return {
            **scope,
            "item_type": details.get("item_type") or "Manual review",
            "quantity": int(details.get("quantity") or 1),
            "notes": details.get("summary") or details.get("notes") or "",
        }
    return {
        **scope,
        "destination_documents_needed": [],
        "visa_transit_concern": details.get("visa_transit_concern") or "",
        "notes": details.get("summary") or details.get("notes") or "",
    }


async def builder_payload_to_v4(
    db: Database,
    agency_id: str,
    builder: Any,
) -> RequestV4Payload:
    data = builder.model_dump(mode="json") if hasattr(builder, "model_dump") else deepcopy(builder)
    client_data = data.get("client") or {}
    client = None
    if client_data.get("client_id"):
        client = await db.collection("client_profiles").find_one(
            {"agency_id": agency_id, "id": client_data["client_id"]}
        )
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    display_name = (
        (client or {}).get("display_name")
        or client_data.get("name")
        or "Client"
    ).strip()
    name_parts = display_name.split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else "Contact"
    email = (client or {}).get("primary_email") or client_data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client email is required for a canonical Request V4.",
        )
    segments_data = data.get("segments") or []
    if not segments_data and data.get("origin") and data.get("destination"):
        segments_data = [
            {
                "sequence": 1,
                "origin_text": data["origin"],
                "destination_text": data["destination"],
                "departure_date": data.get("departure_date"),
                "notes": data.get("route_notes"),
            }
        ]
    segments = []
    for index, segment in enumerate(segments_data):
        local_id = str(segment.get("segment_key") or f"seg_{index + 1}")
        departure_date = segment.get("departure_date") or data.get("departure_date")
        if not departure_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"segments.{index}.departure_date is required for Request V4.",
            )
        segments.append(
            {
                "segment_local_id": local_id,
                "segment_order": index + 1,
                "origin_label": segment.get("origin_text") or "",
                "origin_iata": (
                    segment.get("origin_text", "").upper()
                    if len(segment.get("origin_text", "")) == 3
                    else ""
                ),
                "destination_label": segment.get("destination_text") or "",
                "destination_iata": (
                    segment.get("destination_text", "").upper()
                    if len(segment.get("destination_text", "")) == 3
                    else ""
                ),
                "departure_date": departure_date,
                "departure_time": _hhmm_or_empty(segment.get("departure_time_window")),
                "arrival_date": segment.get("arrival_date"),
                "arrival_time": _hhmm_or_empty(segment.get("arrival_time_window")),
                "marketing_carrier": segment.get("marketing_airline") or "",
                "operating_carrier": segment.get("operating_airline") or "",
                "flight_number": segment.get("flight_number") or "",
                "cabin": {
                    "economy": "Y",
                    "premium_economy": "W",
                    "business": "C",
                    "first": "F",
                }.get(segment.get("cabin_preference"), segment.get("cabin_preference") or "Y"),
                "notes": segment.get("notes") or "",
            }
        )
    segment_ids = [segment["segment_local_id"] for segment in segments]
    passenger_data = data.get("passengers") or [{}]
    passengers: list[dict[str, Any]] = []
    passenger_key_to_local: dict[str, str] = {}
    for index, passenger in enumerate(passenger_data):
        local_id = str(passenger.get("request_passenger_key") or f"pax_{index + 1}")
        profile = None
        if passenger.get("passenger_id"):
            profile = await db.collection("passenger_profiles").find_one(
                {"agency_id": agency_id, "id": passenger["passenger_id"]}
            )
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"passengers.{index}.passenger_id must belong to this agency.",
                )
        first = passenger.get("first_name") or ""
        last = passenger.get("last_name") or ""
        if profile:
            profile_name = (profile.get("display_name") or "").split(maxsplit=1)
            first = profile_name[0] if profile_name else first
            last = profile_name[1] if len(profile_name) > 1 else last
        ptc = {
            "adult": ("ADT", "Adult"),
            "child": ("CHD", "Child"),
            "infant": ("INF", "Infant"),
            "senior": ("SRC", "Senior"),
            "unaccompanied_minor": ("UMNR", "Unaccompanied minor"),
        }.get(passenger.get("passenger_type"), (passenger.get("passenger_type") or "ADT", "Traveler"))
        passengers.append(
            {
                "passenger_local_id": local_id,
                "passenger_profile_id": passenger.get("passenger_id"),
                "identity_status": "confirmed" if profile else "unresolved",
                "passenger_type_code": ptc[0],
                "passenger_type_label": ptc[1],
                "first_name": first,
                "last_name": last,
                "date_of_birth": passenger.get("date_of_birth"),
                "notes": passenger.get("notes") or passenger.get("mobility_notes") or passenger.get("medical_notes") or "",
                "selected_services": [],
                "service_details": {},
            }
        )
        passenger_key_to_local[local_id] = local_id
        if passenger.get("passenger_id"):
            passenger_key_to_local[passenger["passenger_id"]] = local_id

    for service in data.get("services") or []:
        service_key = LEGACY_SERVICE_KEY_MAP.get(service.get("category"), "documents_and_travel_compliance")
        selected_segment_ids = (
            segment_ids
            if service.get("applies_to_all_segments", True)
            else [
                value
                for value in service.get("segment_ids") or []
                if value in segment_ids
            ]
        )
        scope_mode = "all_segments" if service.get("applies_to_all_segments", True) else "selected_segments"
        detail = _legacy_service_detail(
            service_key,
            service.get("details") or {},
            scope_mode,
            [] if scope_mode == "all_segments" else selected_segment_ids,
        )
        target_local_ids = (
            [passenger["passenger_local_id"] for passenger in passengers]
            if service.get("applies_to_all_passengers", True)
            else [
                passenger_key_to_local[value]
                for value in service.get("passenger_ids") or []
                if value in passenger_key_to_local
            ]
        )
        if not target_local_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Every service must be assigned to at least one request passenger.",
            )
        for passenger in passengers:
            if passenger["passenger_local_id"] not in target_local_ids:
                continue
            passenger["selected_services"].append(service_key)
            passenger["service_details"][service_key] = detail

    pets = []
    for index, pet in enumerate(data.get("pets") or []):
        dimensions = pet.get("carrier_dimensions_cm") or {}
        category = str(pet.get("requested_transport_mode") or "other").upper()
        if category not in {"PETC", "AVIH", "SVAN", "ESAN"}:
            category = "OTHER"
        if category in {"PETC", "AVIH"} and not all(
            dimensions.get(key) for key in ("length_cm", "width_cm", "height_cm")
        ):
            category = "OTHER"
        transport_rows = pet.get("segment_transports") or []
        selected = [
            row.get("segment_key")
            for row in transport_rows
            if row.get("segment_key") in segment_ids
        ]
        linked = passenger_key_to_local.get(
            pet.get("request_passenger_key") or pet.get("passenger_id") or ""
        )
        pets.append(
            {
                "pet_local_id": str(pet.get("pet_key") or f"pet_{index + 1}"),
                "linked_passenger_local_id": linked,
                "segment_scope_mode": "selected_segments" if selected else "all_segments",
                "segment_ids": selected,
                "pet_category": category,
                "species_label": pet.get("species") or "Unknown animal",
                "breed_label": pet.get("breed") or pet.get("breed_free_text") or "",
                "pet_weight_kg": pet.get("pet_weight_kg"),
                "container_weight_kg": pet.get("container_weight_kg"),
                "carrier_length_cm": dimensions.get("length_cm"),
                "carrier_width_cm": dimensions.get("width_cm"),
                "carrier_height_cm": dimensions.get("height_cm"),
                "special_instructions": pet.get("notes") or pet.get("special_requirements") or "",
            }
        )

    special_items = []
    category_map = {
        "sports_equipment": "sports_equipment",
        "musical_instrument": "musical_instrument",
        "fragile_item": "valuables_fragile",
        "valuable_item": "valuables_fragile",
        "weapon": "weapon",
    }
    for index, item in enumerate(data.get("special_items") or []):
        category = category_map.get(item.get("item_category_code"), "other")
        dimensions = item.get("dimensions_cm") or {}
        details = {
            "quantity": item.get("quantity") or 1,
            "weight_kg": item.get("weight_kg"),
            "length_cm": dimensions.get("length_cm"),
            "width_cm": dimensions.get("width_cm"),
            "height_cm": dimensions.get("height_cm"),
            "notes": item.get("notes") or item.get("description") or "",
        }
        if category == "sports_equipment":
            details["equipment_type"] = item.get("item_name") or "Sports equipment"
        elif category == "musical_instrument":
            details["instrument_type"] = item.get("item_name") or "Musical instrument"
        else:
            details["item_type"] = item.get("item_name") or item.get("description") or "Special item"
        details = {key: value for key, value in details.items() if value not in (None, "")}
        transport_rows = item.get("segment_transports") or []
        selected = [
            row.get("segment_key")
            for row in transport_rows
            if row.get("segment_key") in segment_ids
        ]
        special_items.append(
            {
                "item_local_id": str(item.get("item_key") or f"item_{index + 1}"),
                "linked_passenger_local_id": passenger_key_to_local.get(
                    item.get("request_passenger_key") or item.get("owner_passenger_id") or ""
                ),
                "segment_scope_mode": "selected_segments" if selected else "all_segments",
                "segment_ids": selected,
                "item_category": category,
                "details": details,
            }
        )

    quote_mode = {
        "round_trip": "round_trip",
        "multi_city": "multi_city",
        "open_jaw": "open_jaw",
    }.get(data.get("trip_type"), "one_way")
    return RequestV4Payload.model_validate(
        {
            "request_version": REQUEST_V4_VERSION,
            "contact": {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": (client or {}).get("primary_phone") or client_data.get("phone"),
            },
            "trip": {
                "trip_label": data.get("title") or "",
                "trip_purpose": "leisure",
                "quote_mode": quote_mode,
                "preferred_cabin": segments[0].get("cabin") if segments else "Y",
            },
            "itinerary_segments": segments,
            "passengers": passengers,
            "pets": pets,
            "special_items": special_items,
            "request_level_notes": data.get("route_notes") or data.get("client_visible_notes") or "",
            "admin_metadata": {
                "source": data.get("source") or "staff_created",
                "status": data.get("status") or "new",
                "priority": data.get("priority") or "normal",
                "internal_notes": data.get("internal_notes") or "",
            },
        }
    )


async def analyze_legacy_requests(
    db: Database,
    *,
    agency_id: str | None = None,
) -> dict[str, Any]:
    repository = PersistenceRepository(db)
    query = {
        "collection_name": "travel_requests",
        "pagination": PaginationRequest.build(
            limit=MAXIMUM_QUERY_LIMIT,
            include_total=True,
        ),
    }
    page = (
        await repository.find_agency_records(agency_id=agency_id, **query)
        if agency_id
        else await repository.find_platform_records(**query)
    )
    requests = page.items
    legacy = [item for item in requests if item.get("request_version") != REQUEST_V4_VERSION]
    results = []
    for request in legacy:
        request_filter = {"agency_id": request["agency_id"], "request_id": request["id"]}
        passenger_count = await db.collection("request_passengers").count(request_filter)
        segment_count = await db.collection("request_segments").count(request_filter)
        service_count = await db.collection("requested_services").count(request_filter)
        issues = []
        if not passenger_count:
            issues.append("missing_request_passengers")
        if not segment_count:
            issues.append("missing_request_segments")
        if not request.get("client_id"):
            issues.append("missing_client_link")
        results.append(
            {
                "agency_id": request["agency_id"],
                "request_id": request["id"],
                "request_reference": request.get("request_reference"),
                "passenger_count": passenger_count,
                "segment_count": segment_count,
                "service_count": service_count,
                "migration_status": (
                    "manual_reconciliation_required" if issues else "adapter_ready"
                ),
                "issues": issues,
            }
        )
    return {
        "dry_run": True,
        "writes_performed": 0,
        "request_count": len(requests),
        "available_request_count": page.pagination.total,
        "analysis_truncated": page.pagination.has_more,
        "legacy_request_count": len(legacy),
        "canonical_v4_count": len(requests) - len(legacy),
        "items": results,
    }
