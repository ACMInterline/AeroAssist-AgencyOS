from datetime import date
from typing import Any

from fastapi import HTTPException, status

from database import Database
from models import (
    AuditEvent,
    RequestCaseFlag,
    RequestPassengerSegmentService,
    RequestPet,
    RequestPetSegmentTransport,
    RequestSpecialItem,
    RequestSpecialItemSegment,
)
from services.reference_data_service import SERVICE_FAMILIES


SERVICE_FAMILY_CODES = {family["code"] for family in SERVICE_FAMILIES}
SERVICE_CATEGORY_TO_FAMILY = {
    "mobility_assistance": "wheelchair_mobility",
    "medical_travel": "medical_assistance",
    "pet_travel": "pets_animals",
    "unaccompanied_minor": "minor_assistance",
    "child_travel_support": "minor_assistance",
    "special_baggage": "special_items",
    "sports_equipment": "special_items",
    "airport_assistance": "sensory_assistance",
}
VALID_PET_TRANSPORT_MODES = {"petc", "avih", "manifest_cargo_advisory"}
VALID_ITEM_CATEGORY_CODES = {
    "wheelchair_device",
    "medical_equipment",
    "oxygen_device",
    "battery_device",
    "sports_equipment",
    "musical_instrument",
    "oversized_baggage",
    "fragile_item",
    "valuable_item",
    "extra_seat_item",
    "stroller",
    "child_restraint_device",
    "other",
}
VALID_TRANSPORT_LOCATIONS = {"passenger_cabin", "baggage_hold", "extra_seat", "checked_baggage", "cargo_advisory"}
MEDICAL_FAMILIES = {"medical_assistance"}
DOCUMENT_SERVICE_CODES = {"MEDA", "STCR", "OXYG", "POC", "UMNR", "SVAN", "MOBILITY_DEVICE"}


def compact(value: Any, limit: int = 500) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text[:limit] if text else None


async def workspace_id_for(db: Database, agency_id: str) -> str | None:
    workspace = await db.collection("agency_workspaces").find_one({"agency_id": agency_id})
    return workspace.get("id") if workspace else None


async def audit(db: Database, agency_id: str, actor_user_id: str | None, event_type: str, request_id: str, count: int) -> None:
    event = AuditEvent(
        agency_id=agency_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type="travel_request",
        entity_id=request_id,
        summary=f"{event_type.replace('_', ' ')}: {count}",
        metadata={"count": count},
    )
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


async def upsert_by_generated_key(db: Database, collection_name: str, model, payload: dict[str, Any]) -> dict:
    generated_key = payload.get("generated_key")
    existing = None
    if generated_key:
        existing = await db.collection(collection_name).find_one(
            {"agency_id": payload["agency_id"], "request_id": payload["request_id"], "generated_key": generated_key}
        )
    if existing:
        return await db.collection(collection_name).update_one({"id": existing["id"]}, payload)
    item = model(**payload)
    return await db.collection(collection_name).insert_one(item.model_dump(mode="json"))


def segment_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        return date.fromisoformat(value[:10])
    return None


async def service_catalogue_by_code(db: Database) -> dict[str, dict]:
    return {
        item["service_code"]: item
        for item in await db.collection("service_catalogue").find_many()
        if item.get("is_active", True)
    }


async def normalize_request_children(
    db: Database,
    agency_id: str,
    request_id: str,
    payload: Any | None = None,
    actor_user_id: str | None = None,
) -> dict[str, Any]:
    request = await db.collection("travel_requests").find_one({"agency_id": agency_id, "id": request_id})
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    payload_data = payload.model_dump(mode="json") if hasattr(payload, "model_dump") else (payload or request.get("builder_payload_snapshot") or {})
    workspace_id = request.get("workspace_id") or await workspace_id_for(db, agency_id)

    passengers = await db.collection("request_passengers").find_many({"agency_id": agency_id, "request_id": request_id})
    passengers = [item for item in passengers if item.get("status") == "active"]
    segments = await db.collection("request_segments").find_many({"agency_id": agency_id, "request_id": request_id})
    segments = [item for item in segments if item.get("status") == "active"]
    segments.sort(key=lambda item: item.get("sequence", 0))
    if not segments:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one request segment is required before normalization.")

    passenger_key_map: dict[str, dict] = {}
    for index, passenger in enumerate(passengers):
        passenger_key_map[f"inline-{index}"] = passenger
        if passenger.get("passenger_id"):
            passenger_key_map[passenger["passenger_id"]] = passenger
        passenger_key_map[passenger["id"]] = passenger
    for index, passenger_payload in enumerate(payload_data.get("passengers") or []):
        key = passenger_payload.get("request_passenger_key") or passenger_payload.get("passenger_id") or f"inline-{index}"
        if index < len(passengers):
            passenger_key_map[key] = passengers[index]

    segment_key_map: dict[str, dict] = {}
    for index, segment in enumerate(segments):
        segment_key_map[str(segment.get("sequence") or index + 1)] = segment
        segment_key_map[segment["id"]] = segment
    for index, segment_payload in enumerate(payload_data.get("segments") or []):
        key = segment_payload.get("segment_key") or str(segment_payload.get("sequence") or index + 1)
        if index < len(segments):
            segment_key_map[key] = segments[index]

    catalogue = await service_catalogue_by_code(db)
    created_service_rows = []
    requested_services = await db.collection("requested_services").find_many({"agency_id": agency_id, "request_id": request_id})
    requested_services_by_index = {index: service for index, service in enumerate(requested_services)}
    all_passengers = passengers
    all_segments = segments
    for index, service_payload in enumerate(payload_data.get("services") or []):
        category = service_payload.get("category") or "other"
        service_code = service_payload.get("service_code") or service_payload.get("details", {}).get("confirmed_ssr_code") or service_payload.get("details", {}).get("suggested_ssr_code") or category.upper()[:32]
        service_record = catalogue.get(service_code)
        family = service_payload.get("service_family_code") or (service_record.get("service_family_code") if service_record else None) or SERVICE_CATEGORY_TO_FAMILY.get(category)
        if family and family not in SERVICE_FAMILY_CODES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid service family: {family}")
        selected_passengers = all_passengers if service_payload.get("applies_to_all_passengers", True) else [passenger_key_map[key] for key in service_payload.get("passenger_ids", []) if key in passenger_key_map]
        selected_segments = all_segments if service_payload.get("applies_to_all_segments", True) else [segment_key_map[key] for key in service_payload.get("segment_ids", []) if key in segment_key_map]
        if not selected_passengers or not selected_segments:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service rows require at least one request passenger and one request segment.")
        requested_service = requested_services_by_index.get(index)
        for passenger in selected_passengers:
            for segment in selected_segments:
                generated_key = f"svc:{index}:{passenger['id']}:{segment['id']}:{service_code}"
                row = await upsert_by_generated_key(
                    db,
                    "request_passenger_segment_services",
                    RequestPassengerSegmentService,
                    {
                        "agency_id": agency_id,
                        "workspace_id": workspace_id,
                        "request_id": request_id,
                        "travel_request_id": request_id,
                        "requested_service_id": requested_service.get("id") if requested_service else None,
                        "request_passenger_id": passenger["id"],
                        "request_segment_id": segment["id"],
                        "passenger_id": passenger.get("passenger_id"),
                        "segment_id": segment["id"],
                        "service_catalogue_id": service_payload.get("service_catalogue_id") or (service_record.get("id") if service_record else None),
                        "service_family_code": family,
                        "service_code": service_code,
                        "service_label": service_record.get("service_label") if service_record else category.replace("_", " "),
                        "service_details_json": service_payload.get("details") or {},
                        "applicability_status": "requested" if service_record else "pending_information",
                        "generated_key": generated_key,
                        "notes": compact(service_payload.get("notes"), 1000),
                    },
                )
                created_service_rows.append(row)

    created_pets = []
    created_pet_transport = []
    for index, pet_payload in enumerate(payload_data.get("pets") or []):
        mode = pet_payload.get("requested_transport_mode") or "petc"
        if mode not in VALID_PET_TRANSPORT_MODES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid pet transport mode: {mode}")
        passenger = passenger_key_map.get(pet_payload.get("request_passenger_key") or pet_payload.get("request_passenger_id") or pet_payload.get("passenger_id") or "")
        pet = await upsert_by_generated_key(
            db,
            "request_pets",
            RequestPet,
            {
                "agency_id": agency_id,
                "workspace_id": workspace_id,
                "request_id": request_id,
                "travel_request_id": request_id,
                "request_passenger_id": passenger.get("id") if passenger else None,
                "passenger_id": passenger.get("passenger_id") if passenger else pet_payload.get("passenger_id"),
                "pet_name": pet_payload.get("pet_name"),
                "species": pet_payload.get("species") or "dog",
                "breed": pet_payload.get("breed"),
                "breed_free_text": pet_payload.get("breed_free_text"),
                "snub_nosed_flag": bool(pet_payload.get("snub_nosed_flag")),
                "age_months": pet_payload.get("age_months"),
                "pet_weight_kg": pet_payload.get("pet_weight_kg"),
                "container_weight_kg": pet_payload.get("container_weight_kg"),
                "combined_weight_kg": pet_payload.get("combined_weight_kg"),
                "requested_transport_mode": mode,
                "carrier_dimensions_cm": pet_payload.get("carrier_dimensions_cm") or {},
                "documentation_status": pet_payload.get("documentation_status"),
                "special_requirements": pet_payload.get("special_requirements"),
                "carrier_required": mode in {"petc", "avih"},
                "service_animal": mode == "svan",
                "generated_key": f"pet:{pet_payload.get('pet_key') or index}",
                "notes": compact(pet_payload.get("notes"), 1000),
                "status": "active",
            },
        )
        created_pets.append(pet)
        transports = pet_payload.get("segment_transports") or [{"segment_key": key, "requested_transport_mode": mode} for key in [str(segment.get("sequence")) for segment in segments]]
        for transport_index, transport_payload in enumerate(transports):
            segment = segment_key_map.get(transport_payload.get("segment_key") or transport_payload.get("request_segment_id") or "")
            if not segment:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pet segment transport requires a valid request segment.")
            transport_mode = transport_payload.get("requested_transport_mode") or mode
            if transport_mode not in VALID_PET_TRANSPORT_MODES:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid pet transport mode: {transport_mode}")
            created_pet_transport.append(
                await upsert_by_generated_key(
                    db,
                    "request_pet_segment_transport",
                    RequestPetSegmentTransport,
                    {
                        "agency_id": agency_id,
                        "workspace_id": workspace_id,
                        "request_id": request_id,
                        "travel_request_id": request_id,
                        "request_pet_id": pet["id"],
                        "request_segment_id": segment["id"],
                        "service_catalogue_id": transport_payload.get("service_catalogue_id"),
                        "requested_transport_mode": transport_mode,
                        "transport_mode": transport_mode,
                        "generated_key": f"petseg:{pet['id']}:{transport_index}:{segment['id']}",
                        "status": "requested",
                        "notes": compact(transport_payload.get("notes"), 1000),
                    },
                )
            )

    created_items = []
    created_item_segments = []
    for index, item_payload in enumerate(payload_data.get("special_items") or []):
        category = item_payload.get("item_category_code") or "other"
        if category not in VALID_ITEM_CATEGORY_CODES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid special item category: {category}")
        location = item_payload.get("transport_location") or "checked_baggage"
        if location not in VALID_TRANSPORT_LOCATIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid transport location: {location}")
        passenger = passenger_key_map.get(item_payload.get("request_passenger_key") or item_payload.get("request_passenger_id") or item_payload.get("owner_passenger_id") or "")
        item = await upsert_by_generated_key(
            db,
            "request_special_items",
            RequestSpecialItem,
            {
                "agency_id": agency_id,
                "workspace_id": workspace_id,
                "request_id": request_id,
                "travel_request_id": request_id,
                "request_passenger_id": passenger.get("id") if passenger else None,
                "owner_passenger_id": passenger.get("passenger_id") if passenger else item_payload.get("owner_passenger_id"),
                "item_type": category,
                "item_category_code": category,
                "item_name": item_payload.get("item_name") or category.replace("_", " "),
                "description": item_payload.get("description") or category.replace("_", " "),
                "quantity": item_payload.get("quantity") or 1,
                "weight_kg": item_payload.get("weight_kg"),
                "dimensions_cm": item_payload.get("dimensions_cm") or {},
                "battery_type": item_payload.get("battery_type"),
                "battery_wh": item_payload.get("battery_wh"),
                "transport_location": location,
                "usage_in_cabin_flag": bool(item_payload.get("usage_in_cabin_flag")),
                "special_handling_instructions": item_payload.get("special_handling_instructions"),
                "documentation_status": item_payload.get("documentation_status"),
                "dimensions_text": item_payload.get("dimensions_text"),
                "weight_text": str(item_payload.get("weight_kg")) if item_payload.get("weight_kg") else None,
                "requires_policy_check": True,
                "generated_key": f"item:{item_payload.get('item_key') or index}",
                "notes": compact(item_payload.get("notes"), 1000),
                "status": "active",
            },
        )
        created_items.append(item)
        transports = item_payload.get("segment_transports") or [{"segment_key": key, "transport_location": location} for key in [str(segment.get("sequence")) for segment in segments]]
        for segment_index, segment_payload in enumerate(transports):
            segment = segment_key_map.get(segment_payload.get("segment_key") or segment_payload.get("request_segment_id") or "")
            if not segment:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Special item segment transport requires a valid request segment.")
            segment_location = segment_payload.get("transport_location") or location
            if segment_location not in VALID_TRANSPORT_LOCATIONS:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid transport location: {segment_location}")
            created_item_segments.append(
                await upsert_by_generated_key(
                    db,
                    "request_special_item_segments",
                    RequestSpecialItemSegment,
                    {
                        "agency_id": agency_id,
                        "workspace_id": workspace_id,
                        "request_id": request_id,
                        "travel_request_id": request_id,
                        "request_special_item_id": item["id"],
                        "request_segment_id": segment["id"],
                        "transport_location": segment_location,
                        "applicability_status": "requested",
                        "generated_key": f"itemseg:{item['id']}:{segment_index}:{segment['id']}",
                        "notes": compact(segment_payload.get("notes"), 1000),
                    },
                )
            )

    flags = derive_case_flags(created_service_rows, created_pets, created_items)
    flag_rows = []
    for flag in flags:
        flag_rows.append(
            await upsert_by_generated_key(
                db,
                "request_case_flags",
                RequestCaseFlag,
                {
                    "agency_id": agency_id,
                    "workspace_id": workspace_id,
                    "request_id": request_id,
                    "travel_request_id": request_id,
                    "flag_code": flag["flag_code"],
                    "flag_label": flag["flag_label"],
                    "severity": flag["severity"],
                    "source": "normalization",
                    "details": flag.get("details"),
                    "status": "active",
                    "generated_key": f"flag:{flag['flag_code']}",
                },
            )
        )

    dates = [segment_date(segment.get("departure_date")) for segment in segments] + [segment_date(segment.get("arrival_date")) for segment in segments]
    dates = [item for item in dates if item]
    scoped_service_count = len([row for row in created_service_rows if row.get("applicability_status") != "cancelled"])
    requested_service_count = len([service for service in requested_services if service.get("status") != "cancelled"])
    updates = {
        "workspace_id": workspace_id,
        "passenger_count": len(passengers),
        "service_count": requested_service_count,
        "pet_count": len(created_pets),
        "special_service_count": scoped_service_count + len(created_pets) + len(created_items),
        "origin_summary": segments[0].get("origin_text") if segments else None,
        "destination_summary": segments[-1].get("destination_text") if segments else None,
        "route_summary": f"{segments[0].get('origin_text')} → {segments[-1].get('destination_text')}" if segments else request.get("route_summary"),
        "first_departure_date": min(dates).isoformat() if dates else None,
        "last_arrival_date": max(dates).isoformat() if dates else None,
        "requires_medical_review": any(row.get("service_family_code") in MEDICAL_FAMILIES or row.get("service_code") in {"MEDA", "STCR", "OXYG", "POC"} for row in created_service_rows),
        "requires_airline_policy_review": bool(created_service_rows or created_pets or created_items),
        "requires_document_followup": any(row.get("service_code") in DOCUMENT_SERVICE_CODES for row in created_service_rows) or any(pet.get("documentation_status") not in {None, "complete"} for pet in created_pets) or any(item.get("documentation_status") not in {None, "complete"} for item in created_items),
        "has_existing_passenger_links": any(passenger.get("passenger_link_mode") == "existing" and passenger.get("passenger_id") for passenger in passengers),
    }
    updated_request = await db.collection("travel_requests").update_one({"agency_id": agency_id, "id": request_id}, updates)
    await audit(db, agency_id, actor_user_id, "request_segments_normalized", request_id, len(segments))
    await audit(db, agency_id, actor_user_id, "request_passengers_normalized", request_id, len(passengers))
    await audit(db, agency_id, actor_user_id, "request_services_normalized", request_id, len(created_service_rows))
    await audit(db, agency_id, actor_user_id, "request_pets_normalized", request_id, len(created_pets))
    await audit(db, agency_id, actor_user_id, "request_special_items_normalized", request_id, len(created_items))
    await audit(db, agency_id, actor_user_id, "request_case_flags_updated", request_id, len(flag_rows))
    return {
        "request": updated_request,
        "passenger_segment_services": created_service_rows,
        "pets": created_pets,
        "pet_segment_transport": created_pet_transport,
        "special_items": created_items,
        "special_item_segments": created_item_segments,
        "case_flags": flag_rows,
    }


def derive_case_flags(service_rows: list[dict], pets: list[dict], items: list[dict]) -> list[dict[str, str]]:
    flags: dict[str, dict[str, str]] = {}
    if service_rows:
        flags["segment_scoped_services"] = {"flag_code": "segment_scoped_services", "flag_label": "Segment-scoped services", "severity": "info"}
    if any(row.get("service_family_code") in MEDICAL_FAMILIES or row.get("service_code") in {"MEDA", "STCR", "OXYG", "POC"} for row in service_rows):
        flags["medical_review"] = {"flag_code": "medical_review", "flag_label": "Medical review required", "severity": "high"}
    if any(row.get("service_code") in DOCUMENT_SERVICE_CODES for row in service_rows):
        flags["document_followup"] = {"flag_code": "document_followup", "flag_label": "Document follow-up required", "severity": "medium"}
    if pets:
        flags["pet_transport"] = {"flag_code": "pet_transport", "flag_label": "Pet transport requested", "severity": "medium"}
    if items:
        flags["special_items"] = {"flag_code": "special_items", "flag_label": "Special item transport requested", "severity": "medium"}
    return list(flags.values())
