from __future__ import annotations

from typing import Any

from database import Database
from models import AuditEvent, PassengerServiceRequest, PassengerServiceRequestCreate
from services.exception_engine_service import ExceptionEngineService
from services.rules_and_services_registry import normalize_code
from services.ssr_osi_generator_service import SsrOsiGeneratorService


def category_for_service_type(service_type: str | None, fallback: str = "OTHER") -> str:
    code = normalize_code(service_type)
    if code == "UMNR":
        return "UMNR"
    if code in {"WCHR", "WCHS", "WCHC", "WCHP", "WCHD", "BLND", "DEAF"}:
        return "PRM"
    if code in {"MEDA", "MEDIF", "OXYG", "STCR"}:
        return "MEDICAL"
    if code in {"PETC", "AVIH"}:
        return "PETS"
    if code == "SVAN":
        return "SERVICE_ANIMAL"
    if code in {"SPEQ", "WEAP"}:
        return "CARGO"
    if code in {"VIP", "VVIP", "DIPB", "DIPLOMAT"}:
        return "VIP"
    if code == "EXST":
        return "SEATING"
    if code == "SPML":
        return "MEAL"
    return fallback


def json_warnings(warnings: list[str]) -> list[dict[str, Any]]:
    return [{"message": warning} for warning in warnings if warning]


async def write_service_audit(
    db: Database,
    agency_id: str,
    actor_user_id: str | None,
    event_type: str,
    entity_id: str,
    summary: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    event = AuditEvent(
        agency_id=agency_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type="passenger_service_request",
        entity_id=entity_id,
        summary=summary,
        metadata=metadata or {},
    )
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


class SpecialServicesService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.exception_engine = ExceptionEngineService(db)
        self.ssr_osi_generator = SsrOsiGeneratorService(db)

    async def add_service_request(
        self,
        agency_id: str,
        payload: PassengerServiceRequestCreate,
        actor_user_id: str | None = None,
        request_id: str | None = None,
        trip_id: str | None = None,
        booking_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json")
        data["service_type"] = normalize_code(data.get("service_type")) or data.get("service_type")
        data["category"] = category_for_service_type(data.get("service_type"), data.get("category") or "OTHER")
        if request_id:
            data["request_id"] = request_id
        if trip_id:
            data["trip_id"] = trip_id
        if booking_id:
            data["booking_id"] = booking_id
        service_request = PassengerServiceRequest(agency_id=agency_id, **data)
        created = await self.db.collection("passenger_service_requests").insert_one(service_request.model_dump(mode="json"))
        await write_service_audit(
            self.db,
            agency_id,
            actor_user_id,
            "passenger_service_request.created",
            created["id"],
            f"Created special service request {created.get('service_type')}.",
        )
        return created

    async def list_services_for_request(self, agency_id: str, request_id: str) -> list[dict[str, Any]]:
        items = await self.db.collection("passenger_service_requests").find_many({"agency_id": agency_id, "request_id": request_id})
        return sorted(items, key=lambda item: str(item.get("created_at") or ""))

    async def list_services_for_trip(self, agency_id: str, trip_id: str) -> list[dict[str, Any]]:
        items = await self.db.collection("passenger_service_requests").find_many({"agency_id": agency_id, "trip_id": trip_id})
        return sorted(items, key=lambda item: str(item.get("created_at") or ""))

    async def list_services_for_booking(self, agency_id: str, booking_id: str) -> list[dict[str, Any]]:
        items = await self.db.collection("passenger_service_requests").find_many({"agency_id": agency_id, "booking_id": booking_id})
        return sorted(items, key=lambda item: str(item.get("created_at") or ""))

    async def get_service_or_none(self, agency_id: str, service_request_id: str) -> dict[str, Any] | None:
        return await self.db.collection("passenger_service_requests").find_one({"agency_id": agency_id, "id": service_request_id})

    async def segment_context(self, service_request: dict[str, Any]) -> dict[str, Any]:
        agency_id = service_request["agency_id"]
        segment_id = service_request.get("segment_id")
        metadata = service_request.get("metadata_json") or {}
        context: dict[str, Any] = {
            "route_origin": metadata.get("route_origin"),
            "route_destination": metadata.get("route_destination"),
            "aircraft_type": metadata.get("aircraft_type"),
            "iata_code": metadata.get("iata_code") or metadata.get("airline_code"),
            "airline_id": metadata.get("airline_id"),
            "segment_refs_json": metadata.get("segment_refs_json") or [],
        }
        segment = None
        if segment_id:
            segment = await self.db.collection("request_segments").find_one({"agency_id": agency_id, "id": segment_id})
            if segment is None:
                segment = await self.db.collection("trip_segments").find_one({"agency_id": agency_id, "id": segment_id})
        elif service_request.get("request_id"):
            segments = await self.db.collection("request_segments").find_many({"agency_id": agency_id, "request_id": service_request["request_id"]})
            segment = segments[0] if segments else None
        elif service_request.get("trip_id"):
            segments = await self.db.collection("trip_segments").find_many({"agency_id": agency_id, "trip_id": service_request["trip_id"]})
            segment = segments[0] if segments else None
        if segment:
            context["route_origin"] = (
                context.get("route_origin")
                or segment.get("origin_airport_code")
                or segment.get("origin_text")
            )
            context["route_destination"] = (
                context.get("route_destination")
                or segment.get("destination_airport_code")
                or segment.get("destination_text")
            )
            context["iata_code"] = (
                context.get("iata_code")
                or segment.get("preferred_airline_code")
                or segment.get("marketing_airline_code")
                or segment.get("marketing_airline")
                or segment.get("operating_airline_code")
                or segment.get("operating_airline")
            )
            context["aircraft_type"] = context.get("aircraft_type") or segment.get("aircraft_type")
            context["segment_refs_json"] = context.get("segment_refs_json") or [{"segment_id": segment.get("id")}]
        return context

    async def evaluation_context(self, service_request: dict[str, Any]) -> dict[str, Any]:
        metadata = service_request.get("metadata_json") or {}
        segment = await self.segment_context(service_request)
        return {
            "airline_id": segment.get("airline_id"),
            "iata_code": normalize_code(segment.get("iata_code")),
            "route_origin": normalize_code(segment.get("route_origin")),
            "route_destination": normalize_code(segment.get("route_destination")),
            "aircraft_type": normalize_code(segment.get("aircraft_type")),
            "passenger_summary_json": metadata.get("passenger_summary_json") or {},
            "service_category": service_request.get("category") or category_for_service_type(service_request.get("service_type")),
            "service_type": service_request.get("service_type"),
            "service_payload_json": metadata,
            "segment_refs_json": segment.get("segment_refs_json") or [],
        }

    async def evaluate_service_request(self, agency_id: str, service_request_id: str, actor_user_id: str | None = None) -> dict[str, Any] | None:
        service_request = await self.get_service_or_none(agency_id, service_request_id)
        if service_request is None:
            return None
        context = await self.evaluation_context(service_request)
        result = await self.exception_engine.evaluate(context)
        status_value = "validated" if result.get("allowed") else "blocked"
        updates = {
            "evaluation_result_json": result,
            "warnings_json": json_warnings(result.get("warnings") or []),
            "required_documents_json": result.get("required_documents") or [],
            "policy_violations_json": result.get("policy_violations") or [],
            "status": status_value,
        }
        updated = await self.db.collection("passenger_service_requests").update_one({"agency_id": agency_id, "id": service_request_id}, updates)
        await write_service_audit(
            self.db,
            agency_id,
            actor_user_id,
            "passenger_service_request.evaluated",
            service_request_id,
            f"Evaluated special service request {service_request.get('service_type')}.",
            {"allowed": result.get("allowed"), "rules_fired": len(result.get("rules_fired") or [])},
        )
        return {"service": updated, "result": result, "context": context}

    async def generate_ssr_osi_for_service(self, agency_id: str, service_request_id: str, actor_user_id: str | None = None) -> dict[str, Any] | None:
        service_request = await self.get_service_or_none(agency_id, service_request_id)
        if service_request is None:
            return None
        context = await self.evaluation_context(service_request)
        evaluation = await self.exception_engine.evaluate(context)
        generated = await self.ssr_osi_generator.generate(context, evaluation)
        gds_text = "\n".join([*(item.get("text", "") for item in generated.get("ssr") or []), *(item.get("text", "") for item in generated.get("osi") or [])]).strip() or None
        updates = {
            "evaluation_result_json": evaluation,
            "generated_ssr_json": generated.get("ssr") or [],
            "generated_osi_json": generated.get("osi") or [],
            "warnings_json": json_warnings(generated.get("warnings") or []),
            "required_documents_json": generated.get("required_documents") or [],
            "policy_violations_json": evaluation.get("policy_violations") or [],
            "gds_text": gds_text,
            "status": "blocked" if generated.get("blocked") else "validated",
        }
        updated = await self.db.collection("passenger_service_requests").update_one({"agency_id": agency_id, "id": service_request_id}, updates)
        await write_service_audit(
            self.db,
            agency_id,
            actor_user_id,
            "passenger_service_request.ssr_osi_generated",
            service_request_id,
            f"Generated SSR/OSI preview for {service_request.get('service_type')}.",
            {"blocked": generated.get("blocked"), "ssr_count": len(generated.get("ssr") or []), "osi_count": len(generated.get("osi") or [])},
        )
        return {"service": updated, "result": generated, "context": context}

    async def generate_ssr_osi_for_trip(self, agency_id: str, trip_id: str, actor_user_id: str | None = None) -> dict[str, Any]:
        services = await self.list_services_for_trip(agency_id, trip_id)
        generated = []
        for service in services:
            result = await self.generate_ssr_osi_for_service(agency_id, service["id"], actor_user_id)
            if result:
                generated.append(result)
        return {"trip_id": trip_id, "items": generated}

    async def from_parsed_pnr(self, agency_id: str, trip_id: str, booking_id: str | None, parsed_pnr: dict[str, Any], actor_user_id: str | None = None) -> dict[str, Any]:
        created = []
        for entry in parsed_pnr.get("ssr") or parsed_pnr.get("ssrs") or []:
            code = normalize_code(entry.get("code") or entry.get("ssr_code"))
            if not code:
                continue
            payload = PassengerServiceRequestCreate(
                trip_id=trip_id,
                booking_id=booking_id,
                passenger_id=entry.get("passenger_id"),
                segment_id=entry.get("segment_id"),
                category=category_for_service_type(code),
                service_type=code,
                ssr_code=code,
                metadata_json={"parsed_pnr_entry": entry, "source": "parsed_pnr"},
                generated_ssr_json=[entry],
            )
            created.append(await self.add_service_request(agency_id, payload, actor_user_id))
        for entry in parsed_pnr.get("osi") or parsed_pnr.get("osis") or []:
            payload = PassengerServiceRequestCreate(
                trip_id=trip_id,
                booking_id=booking_id,
                category="OTHER",
                service_type=normalize_code(entry.get("service_type")) or "OTHER",
                osi_code=entry.get("code") or entry.get("osi_code"),
                metadata_json={"parsed_pnr_entry": entry, "source": "parsed_pnr"},
                generated_osi_json=[entry],
            )
            created.append(await self.add_service_request(agency_id, payload, actor_user_id))
        return {"created": created, "message": "Parsed PNR SSR/OSI stubs imported into passenger service requests."}
