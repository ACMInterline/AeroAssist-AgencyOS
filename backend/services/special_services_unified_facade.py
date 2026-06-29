from __future__ import annotations

from typing import Any

from database import Database
from services.exception_engine_service import ExceptionEngineService
from services.rules_and_services_registry import normalize_code
from services.special_services_service import SpecialServicesService, category_for_service_type
from services.ssr_osi_generator_service import SsrOsiGeneratorService


class SpecialServicesUnifiedFacade:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.special_services = SpecialServicesService(db)
        self.exception_engine = ExceptionEngineService(db)
        self.ssr_osi_generator = SsrOsiGeneratorService(db)

    async def list_services_for_trip(self, agency_id: str, trip_id: str) -> dict[str, Any]:
        passenger_services = await self.special_services.list_services_for_trip(agency_id, trip_id)
        trip_services = await self.db.collection("trip_service_items").find_many(
            {"agency_id": agency_id, "trip_id": trip_id}
        )
        return {
            "agency_id": agency_id,
            "trip_id": trip_id,
            "items": [
                *[self.normalize_service_context(item) for item in passenger_services],
                *[self.normalize_service_context(item) for item in trip_services],
            ],
            "source": "special_services_unified_facade",
        }

    async def list_services_for_booking(self, agency_id: str, booking_record_id: str) -> dict[str, Any]:
        booking_record = await self.db.collection("booking_records").find_one(
            {"agency_id": agency_id, "id": booking_record_id}
        )
        passenger_services = await self.special_services.list_services_for_booking(agency_id, booking_record_id)
        snapshot_services = self._flatten_service_snapshot((booking_record or {}).get("services_json") or {})
        return {
            "agency_id": agency_id,
            "booking_record_id": booking_record_id,
            "items": [
                *[self.normalize_service_context(item) for item in passenger_services],
                *[self.normalize_service_context(item) for item in snapshot_services],
            ],
            "booking_record_found": booking_record is not None,
            "source": "special_services_unified_facade",
        }

    def normalize_service_context(self, payload: dict[str, Any]) -> dict[str, Any]:
        catalogue = payload.get("service_catalogue_snapshot_json") or {}
        service_type = normalize_code(
            payload.get("service_type")
            or payload.get("service_key")
            or payload.get("service_code")
            or payload.get("ssr_code")
            or catalogue.get("service_key")
            or catalogue.get("ssr_code")
        )
        return {
            "service_id": payload.get("id"),
            "service_type": service_type,
            "service_key": normalize_code(payload.get("service_key") or catalogue.get("service_key")) or service_type,
            "service_label": payload.get("service_label") or payload.get("service_name") or catalogue.get("label"),
            "service_category": payload.get("service_catalogue_category") or payload.get("category") or category_for_service_type(service_type),
            "request_id": payload.get("request_id"),
            "trip_id": payload.get("trip_id"),
            "booking_id": payload.get("booking_id"),
            "passenger_id": payload.get("passenger_id"),
            "segment_id": payload.get("segment_id"),
            "airline_id": payload.get("airline_id") or (payload.get("metadata_json") or {}).get("airline_id"),
            "iata_code": payload.get("iata_code") or (payload.get("metadata_json") or {}).get("iata_code"),
            "route_origin": payload.get("origin_airport_code") or payload.get("route_origin"),
            "route_destination": payload.get("destination_airport_code") or payload.get("route_destination"),
            "service_payload_json": payload.get("metadata_json") or payload.get("payload_json") or payload,
            "service_catalogue_snapshot_json": catalogue,
        }

    async def generate_ssr_osi_preview(self, context: dict[str, Any]) -> dict[str, Any]:
        normalized = self.normalize_service_context(context)
        return await self.ssr_osi_generator.generate(normalized)

    async def evaluate_service_context(self, context: dict[str, Any]) -> dict[str, Any]:
        normalized = self.normalize_service_context(context)
        return await self.exception_engine.evaluate(normalized)

    def _flatten_service_snapshot(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for value in (snapshot or {}).values():
            if isinstance(value, list):
                items.extend([item for item in value if isinstance(item, dict)])
        return items
