import re
from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status

from database import Database
from models import (
    AuditEvent,
    ClientPassengerRelationship,
    PassengerProfile,
    RequestPassenger,
    RequestPassengerIdentityConfirm,
    RequestTimelineEvent,
)
from persistence_query import PaginationRequest
from persistence_repository import PersistenceRepository


INTAKE_PLACEHOLDER_BIRTH_DATE = "1900-01-01"
INTAKE_PLACEHOLDER_NOTE = "Created as a placeholder from request intake conversion."
INTAKE_PLACEHOLDER_REASON = "Legacy intake conversion created a synthetic master passenger."
PLACEHOLDER_FIRST_NAME = re.compile(r"^Passenger ([1-9][0-9]*)$")


async def _list_agency_records(
    db: Database,
    collection_name: str,
    agency_id: str,
    filters: Optional[dict[str, Any]] = None,
    *,
    hard_limit: int = 10000,
) -> list[dict[str, Any]]:
    repository = PersistenceRepository(db)
    records: list[dict[str, Any]] = []
    cursor: Optional[str] = None
    while len(records) < hard_limit:
        page = await repository.find_agency_records(
            collection_name=collection_name,
            agency_id=agency_id,
            filters=filters,
            sort_field="created_at",
            sort_direction="asc",
            pagination=PaginationRequest.build(
                limit=min(100, hard_limit - len(records)),
                cursor=cursor,
            ),
        )
        records.extend(page.items)
        if not page.pagination.has_more or not page.pagination.next_cursor:
            break
        cursor = page.pagination.next_cursor
    return records


def compact_text(value: Any, limit: int) -> Optional[str]:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text[:limit] if text else None


def unresolved_request_passenger(
    *,
    agency_id: str,
    request_id: str,
    index: int,
    proposed_identity: Optional[dict[str, Any]] = None,
    service_needs_summary: Optional[str] = None,
    source_intake_id: Optional[str] = None,
) -> RequestPassenger:
    proposed = {
        key: value
        for key, value in (proposed_identity or {}).items()
        if value is not None and value != ""
    }
    display_name = compact_text(proposed.get("display_name"), 160)
    if not display_name:
        display_name = " ".join(
            value
            for value in [
                compact_text(proposed.get("first_name"), 80),
                compact_text(proposed.get("last_name"), 80),
            ]
            if value
        )
    passenger_type = proposed.get("passenger_type") or "ADT"
    return RequestPassenger(
        agency_id=agency_id,
        request_id=request_id,
        passenger_id=None,
        passenger_link_mode="unresolved",
        client_passenger_relationship_id=None,
        role_in_request="traveler",
        is_primary_traveler=index == 0,
        service_needs_summary=compact_text(service_needs_summary, 1000),
        snapshot_display_name=display_name or f"Unresolved traveler {index + 1}",
        snapshot_date_of_birth=proposed.get("date_of_birth"),
        snapshot_passenger_type=passenger_type,
        identity_status="unresolved",
        identity_source="request_intake" if source_intake_id else "request_builder",
        proposed_identity_json=proposed,
        source_intake_id=source_intake_id,
    )


async def _write_audit(
    db: Database,
    agency_id: str,
    actor_user_id: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    summary: str,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    event = AuditEvent(
        agency_id=agency_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata=metadata or {},
    )
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


async def _write_request_timeline(
    db: Database,
    agency_id: str,
    request_id: str,
    actor_user_id: str,
    event_type: str,
    title: str,
    summary: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    event = RequestTimelineEvent(
        agency_id=agency_id,
        request_id=request_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        title=title,
        summary=summary,
        visibility="internal",
        metadata=metadata or {},
    )
    await db.collection("request_timeline_events").insert_one(event.model_dump(mode="json"))


async def _get_active_passenger(db: Database, agency_id: str, passenger_id: str) -> dict:
    passenger = await db.collection("passenger_profiles").find_one(
        {"agency_id": agency_id, "id": passenger_id}
    )
    if not passenger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passenger profile not found.")
    if passenger.get("status") in {"archived", "duplicate_merged", "quarantined"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archived, merged, or quarantined passenger profiles cannot confirm identity.",
        )
    return passenger


async def _create_confirmed_passenger(
    db: Database,
    agency_id: str,
    request_passenger: dict,
    payload: RequestPassengerIdentityConfirm,
) -> dict:
    duplicate = await db.collection("passenger_profiles").find_one(
        {
            "agency_id": agency_id,
            "first_name": compact_text(payload.first_name, 80),
            "last_name": compact_text(payload.last_name, 80),
            "date_of_birth": payload.date_of_birth.isoformat(),
        }
    )
    if duplicate and duplicate.get("status") not in {"archived", "duplicate_merged", "quarantined"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A matching passenger profile already exists. Confirm identity by selecting that profile.",
        )
    display_name = compact_text(payload.display_name, 160) or " ".join(
        value
        for value in [
            compact_text(payload.first_name, 80),
            compact_text(payload.middle_name, 80),
            compact_text(payload.last_name, 80),
        ]
        if value
    )
    passenger = PassengerProfile(
        agency_id=agency_id,
        first_name=compact_text(payload.first_name, 80) or "",
        middle_name=compact_text(payload.middle_name, 80),
        last_name=compact_text(payload.last_name, 80) or "",
        display_name=display_name,
        date_of_birth=payload.date_of_birth,
        passenger_type=payload.passenger_type,
        gender=compact_text(payload.gender, 80),
        nationality=compact_text(payload.nationality, 80),
        residence_country=compact_text(payload.residence_country, 80),
        primary_language=compact_text(payload.primary_language, 20) or "en",
        source_intake_id=request_passenger.get("source_intake_id"),
    )
    return await db.collection("passenger_profiles").insert_one(passenger.model_dump(mode="json"))


async def _ensure_client_relationship(
    db: Database,
    agency_id: str,
    client_id: str,
    passenger_id: str,
    relationship_type: str,
    request_id: str,
) -> dict:
    relationship = await db.collection("client_passenger_relationships").find_one(
        {
            "agency_id": agency_id,
            "client_id": client_id,
            "passenger_id": passenger_id,
            "status": "active",
        }
    )
    if relationship:
        return relationship
    model = ClientPassengerRelationship(
        agency_id=agency_id,
        client_id=client_id,
        passenger_id=passenger_id,
        relationship_type=relationship_type,
        can_request_travel=True,
        notes=f"Created after explicit identity confirmation for request {request_id}.",
    )
    return await db.collection("client_passenger_relationships").insert_one(
        model.model_dump(mode="json")
    )


async def _sync_confirmed_identity(
    db: Database,
    agency_id: str,
    request_id: str,
    request_passenger_id: str,
    passenger_id: str,
) -> None:
    scoped_collections = (
        ("request_passenger_segment_services", "passenger_id"),
        ("request_pets", "passenger_id"),
        ("request_special_items", "owner_passenger_id"),
    )
    for collection_name, passenger_field in scoped_collections:
        records = await _list_agency_records(
            db,
            collection_name,
            agency_id,
            {
                "request_id": request_id,
                "request_passenger_id": request_passenger_id,
            },
        )
        for record in records:
            await db.collection(collection_name).update_one(
                {"agency_id": agency_id, "id": record["id"]},
                {passenger_field: passenger_id},
            )

    services = await _list_agency_records(
        db,
        "requested_services",
        agency_id,
        {"request_id": request_id},
    )
    for service in services:
        if not service.get("applies_to_all_passengers"):
            continue
        passenger_ids = [
            value
            for value in service.get("passenger_ids") or []
            if value
        ]
        if passenger_id not in passenger_ids:
            passenger_ids.append(passenger_id)
            await db.collection("requested_services").update_one(
                {"agency_id": agency_id, "id": service["id"]},
                {"passenger_ids": passenger_ids},
            )


async def confirm_request_passenger_identity(
    db: Database,
    agency_id: str,
    request_id: str,
    request_passenger_id: str,
    payload: RequestPassengerIdentityConfirm,
    actor_user_id: str,
) -> dict[str, Any]:
    request = await db.collection("travel_requests").find_one(
        {"agency_id": agency_id, "id": request_id}
    )
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    request_passenger = await db.collection("request_passengers").find_one(
        {
            "agency_id": agency_id,
            "request_id": request_id,
            "id": request_passenger_id,
            "status": "active",
        }
    )
    if not request_passenger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request passenger not found.")

    if request_passenger.get("passenger_id"):
        if payload.existing_passenger_id == request_passenger["passenger_id"]:
            return {
                "request_passenger": request_passenger,
                "passenger": await _get_active_passenger(
                    db, agency_id, request_passenger["passenger_id"]
                ),
                "already_confirmed": True,
            }
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Request passenger identity is already confirmed and cannot be replaced here.",
        )

    passenger = (
        await _get_active_passenger(db, agency_id, payload.existing_passenger_id)
        if payload.existing_passenger_id
        else await _create_confirmed_passenger(db, agency_id, request_passenger, payload)
    )
    duplicate_link = await db.collection("request_passengers").find_one(
        {
            "agency_id": agency_id,
            "request_id": request_id,
            "passenger_id": passenger["id"],
            "status": "active",
        }
    )
    if duplicate_link and duplicate_link.get("id") != request_passenger_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Passenger profile is already linked to this request.",
        )
    relationship = await _ensure_client_relationship(
        db,
        agency_id,
        request["client_id"],
        passenger["id"],
        str(payload.relationship_type),
        request_id,
    )
    confirmed_at = datetime.now(timezone.utc)
    updated = await db.collection("request_passengers").update_one(
        {
            "agency_id": agency_id,
            "request_id": request_id,
            "id": request_passenger_id,
            "passenger_id": None,
        },
        {
            "passenger_id": passenger["id"],
            "passenger_link_mode": "existing",
            "client_passenger_relationship_id": relationship["id"],
            "snapshot_display_name": passenger["display_name"],
            "snapshot_date_of_birth": passenger["date_of_birth"],
            "snapshot_passenger_type": passenger["passenger_type"],
            "identity_status": "confirmed",
            "identity_source": (
                "existing_passenger_profile"
                if payload.existing_passenger_id
                else "explicit_identity_confirmation"
            ),
            "identity_confirmed_at": confirmed_at,
            "identity_confirmed_by_user_id": actor_user_id,
            "identity_confirmation_reason": compact_text(payload.confirmation_reason, 500),
        },
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Passenger identity changed during confirmation. Reload and review before retrying.",
        )

    await _sync_confirmed_identity(
        db, agency_id, request_id, request_passenger_id, passenger["id"]
    )
    confirmed_links = await _list_agency_records(
        db,
        "request_passengers",
        agency_id,
        {"request_id": request_id, "status": "active"},
    )
    await db.collection("travel_requests").update_one(
        {"agency_id": agency_id, "id": request_id},
        {
            "has_existing_passenger_links": any(
                item.get("passenger_id") and item.get("passenger_link_mode") == "existing"
                for item in confirmed_links
            )
        },
    )
    await _write_audit(
        db,
        agency_id,
        actor_user_id,
        "request.passenger_identity_confirmed",
        "request_passenger",
        request_passenger_id,
        "Confirmed request passenger identity.",
        {
            "request_id": request_id,
            "passenger_id": passenger["id"],
            "confirmation_mode": (
                "existing_profile" if payload.existing_passenger_id else "new_profile"
            ),
        },
    )
    await _write_request_timeline(
        db,
        agency_id,
        request_id,
        actor_user_id,
        "request.passenger_identity_confirmed",
        "Passenger identity confirmed",
        passenger["display_name"],
        {"request_passenger_id": request_passenger_id, "passenger_id": passenger["id"]},
    )
    return {
        "request_passenger": updated,
        "passenger": passenger,
        "relationship": relationship,
        "already_confirmed": False,
    }


def is_legacy_intake_placeholder(profile: dict[str, Any]) -> bool:
    first_name = str(profile.get("first_name") or "")
    match = PLACEHOLDER_FIRST_NAME.fullmatch(first_name)
    expected_display_name = f"{first_name} details pending"
    birth_date = profile.get("date_of_birth")
    birth_date_text = birth_date.isoformat() if isinstance(birth_date, date) else str(birth_date)
    return bool(
        match
        and profile.get("last_name") == "Details pending"
        and profile.get("display_name") == expected_display_name
        and birth_date_text == INTAKE_PLACEHOLDER_BIRTH_DATE
        and profile.get("travel_document_notes") == INTAKE_PLACEHOLDER_NOTE
    )


async def find_legacy_intake_placeholder_candidates(
    db: Database,
    agency_id: str,
) -> list[dict[str, Any]]:
    profiles = await _list_agency_records(db, "passenger_profiles", agency_id)
    candidates: list[dict[str, Any]] = []
    for profile in profiles:
        if not is_legacy_intake_placeholder(profile):
            continue
        request_passengers = await _list_agency_records(
            db,
            "request_passengers",
            agency_id,
            {"passenger_id": profile["id"]},
        )
        proven_links = []
        for request_passenger in request_passengers:
            request = await db.collection("travel_requests").find_one(
                {
                    "agency_id": agency_id,
                    "id": request_passenger.get("request_id"),
                }
            )
            if request and request.get("source_intake_id"):
                proven_links.append(
                    {
                        "request_passenger": request_passenger,
                        "request": request,
                        "source_intake_id": request["source_intake_id"],
                    }
                )
        if proven_links:
            candidates.append({"profile": profile, "links": proven_links})
    return candidates


async def quarantine_legacy_intake_placeholders(
    db: Database,
    agency_id: str,
    actor_user_id: str,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    candidates = await find_legacy_intake_placeholder_candidates(db, agency_id)
    report = {
        "agency_id": agency_id,
        "mode": "apply" if apply else "dry_run",
        "candidate_count": len(candidates),
        "quarantined_count": 0,
        "migrated_request_passenger_count": 0,
        "candidate_ids": [item["profile"]["id"] for item in candidates],
    }
    if not apply:
        return report

    for candidate in candidates:
        profile = candidate["profile"]
        if (
            profile.get("status") == "quarantined"
            and profile.get("identity_integrity_status") == "quarantined_intake_placeholder"
        ):
            continue
        quarantined_at = datetime.now(timezone.utc)
        await db.collection("passenger_profiles").update_one(
            {"agency_id": agency_id, "id": profile["id"]},
            {
                "status": "quarantined",
                "identity_integrity_status": "quarantined_intake_placeholder",
                "source_intake_id": candidate["links"][0]["source_intake_id"],
                "quarantined_at": quarantined_at,
                "quarantined_by_user_id": actor_user_id,
                "quarantine_reason": INTAKE_PLACEHOLDER_REASON,
            },
        )
        report["quarantined_count"] += 1

        relationships = await _list_agency_records(
            db,
            "client_passenger_relationships",
            agency_id,
            {"passenger_id": profile["id"]},
        )
        for relationship in relationships:
            prior_notes = compact_text(relationship.get("notes"), 1500)
            await db.collection("client_passenger_relationships").update_one(
                {"agency_id": agency_id, "id": relationship["id"]},
                {
                    "status": "archived",
                    "notes": " ".join(
                        value
                        for value in [
                            prior_notes,
                            "Archived because the linked passenger was a legacy intake placeholder.",
                        ]
                        if value
                    )[:2000],
                },
            )

        for link in candidate["links"]:
            request_passenger = link["request_passenger"]
            sequence_match = PLACEHOLDER_FIRST_NAME.fullmatch(
                str(profile.get("first_name") or "")
            )
            sequence = int(sequence_match.group(1)) if sequence_match else 1
            await db.collection("request_passengers").update_one(
                {
                    "agency_id": agency_id,
                    "request_id": request_passenger["request_id"],
                    "id": request_passenger["id"],
                    "passenger_id": profile["id"],
                },
                {
                    "passenger_id": None,
                    "passenger_link_mode": "unresolved",
                    "client_passenger_relationship_id": None,
                    "snapshot_display_name": f"Unresolved traveler {sequence}",
                    "snapshot_date_of_birth": None,
                    "snapshot_passenger_type": "ADT",
                    "identity_status": "source_quarantined",
                    "identity_source": "legacy_intake_placeholder_quarantine",
                    "proposed_identity_json": {},
                    "source_intake_id": link["source_intake_id"],
                    "quarantined_passenger_profile_id": profile["id"],
                    "identity_confirmed_at": None,
                    "identity_confirmed_by_user_id": None,
                    "identity_confirmation_reason": None,
                },
            )
            await _remove_quarantined_profile_references(
                db,
                agency_id,
                request_passenger["request_id"],
                request_passenger["id"],
                profile["id"],
            )
            remaining_links = await _list_agency_records(
                db,
                "request_passengers",
                agency_id,
                {
                    "request_id": request_passenger["request_id"],
                    "status": "active",
                },
            )
            await db.collection("travel_requests").update_one(
                {"agency_id": agency_id, "id": request_passenger["request_id"]},
                {
                    "has_existing_passenger_links": any(
                        item.get("passenger_id")
                        and item.get("passenger_link_mode") == "existing"
                        for item in remaining_links
                    )
                },
            )
            await _write_request_timeline(
                db,
                agency_id,
                request_passenger["request_id"],
                actor_user_id,
                "request.passenger_placeholder_quarantined",
                "Synthetic passenger placeholder quarantined",
                "Identity must be confirmed before a passenger profile is linked.",
                {
                    "request_passenger_id": request_passenger["id"],
                    "quarantined_passenger_profile_id": profile["id"],
                },
            )
            report["migrated_request_passenger_count"] += 1

        await _write_audit(
            db,
            agency_id,
            actor_user_id,
            "passenger.intake_placeholder_quarantined",
            "passenger_profile",
            profile["id"],
            "Quarantined a legacy synthetic intake passenger profile.",
            {
                "request_passenger_ids": [
                    item["request_passenger"]["id"] for item in candidate["links"]
                ],
                "source_intake_ids": list(
                    dict.fromkeys(item["source_intake_id"] for item in candidate["links"])
                ),
            },
        )
    return report


async def _remove_quarantined_profile_references(
    db: Database,
    agency_id: str,
    request_id: str,
    request_passenger_id: str,
    passenger_profile_id: str,
) -> None:
    for collection_name, passenger_field in (
        ("request_passenger_segment_services", "passenger_id"),
        ("request_pets", "passenger_id"),
        ("request_special_items", "owner_passenger_id"),
    ):
        records = await _list_agency_records(
            db,
            collection_name,
            agency_id,
            {
                "request_id": request_id,
                "request_passenger_id": request_passenger_id,
            },
        )
        for record in records:
            if record.get(passenger_field) == passenger_profile_id:
                await db.collection(collection_name).update_one(
                    {"agency_id": agency_id, "id": record["id"]},
                    {passenger_field: None},
                )

    services = await _list_agency_records(
        db,
        "requested_services",
        agency_id,
        {"request_id": request_id},
    )
    for service in services:
        passenger_ids = [
            value
            for value in service.get("passenger_ids") or []
            if value and value != passenger_profile_id
        ]
        if passenger_ids != (service.get("passenger_ids") or []):
            await db.collection("requested_services").update_one(
                {"agency_id": agency_id, "id": service["id"]},
                {"passenger_ids": passenger_ids},
            )
