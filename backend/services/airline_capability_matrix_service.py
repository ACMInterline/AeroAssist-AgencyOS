from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    AirlineCapabilityMatrixCreate,
    AirlineCapabilityMatrixRecord,
    AirlineCapabilityMatrixUpdate,
    new_id,
)


PHASE_LABEL = "phase_54_1_operational_workflow_orchestration_foundation"
AIRLINE_CAPABILITY_MATRIX_COLLECTION = "airline_capability_matrix"

CAPABILITY_STATUSES = ["draft", "under_review", "approved", "active", "superseded", "archived"]
CAPABILITY_STATUS_VALUES = ["available", "unavailable", "conditional", "restricted", "manual_review", "unknown"]
CAPABILITY_OUTCOMES = ["can_deliver", "cannot_deliver", "conditional_delivery", "requires_manual_review", "unknown"]
CAPABILITY_REVIEW_STATUSES = ["not_started", "under_review", "reviewed", "changes_requested", "rejected"]
OPERATIONAL_VALIDITY_STATUSES = ["valid", "warning", "restricted", "expired", "unknown"]
CONFIDENCE_LEVELS = ["official", "high", "medium", "low", "unknown"]
OPERATIONAL_RISK_LEVELS = ["low", "medium", "high", "critical", "unknown"]


class AirlineCapabilityMatrixError(ValueError):
    pass


class AirlineCapabilityMatrixService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        capabilities = await self.list_platform_capabilities(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": capabilities,
            "capabilities": capabilities,
            "summary": self.summarize_counts(capabilities),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "The Airline Capability Matrix records what an airline can operationally deliver. It does not evaluate passenger cases, score feasibility, rank airlines, reason with AI, execute parsers, calculate pricing, call providers, run workers, or automatically publish.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        capabilities = await self.list_agency_capabilities(agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": capabilities,
            "capabilities": capabilities,
            "summary": self.summarize_counts(capabilities),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Capability Matrix visibility is read-only operational capability inventory metadata. It does not evaluate passenger cases, score feasibility, rank airlines, reason with AI, execute parsers, calculate pricing, call providers, run workers, or automatically publish.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        capabilities = await self.list_platform_capabilities()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(capabilities),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        capabilities = await self.list_agency_capabilities(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(capabilities),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_platform_capabilities(
        self,
        *,
        agency_id: str | None = None,
        airline: str | None = None,
        service_domain: str | None = None,
        service_family: str | None = None,
        ssr_code: str | None = None,
        rfic: str | None = None,
        rfisc: str | None = None,
        aircraft_family: str | None = None,
        cabin: str | None = None,
        airport: str | None = None,
        route: str | None = None,
        country: str | None = None,
        season: str | None = None,
        capability_status: str | None = None,
        operational_risk: str | None = None,
        confidence_level: str | None = None,
        effective_date: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if service_domain:
            filters["service_domain"] = service_domain
        if service_family:
            filters["service_family"] = service_family
        if ssr_code:
            filters["ssr_code"] = ssr_code
        if rfic:
            filters["rfic"] = rfic
        if rfisc:
            filters["rfisc"] = rfisc

        items = await self.db.collection(AIRLINE_CAPABILITY_MATRIX_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if not item.get("deleted_at") and item.get("capability_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(item, ["airline_code", "airline_name", "validating_carrier", "operating_carrier", "marketing_carrier"], airline)
            and self._any_field_matches(item, ["aircraft_family", "aircraft_subtype", "aircraft_applicability"], aircraft_family)
            and self._any_field_matches(item, ["cabin_family", "cabin_name", "cabin_applicability"], cabin)
            and self._any_field_matches(
                item,
                [
                    "airport_applicability",
                    "station_applicability",
                    "origin_airport_applicability",
                    "destination_airport_applicability",
                    "transit_airport_applicability",
                ],
                airport,
            )
            and self._any_field_matches(item, ["route_applicability"], route)
            and self._any_field_matches(
                item,
                ["origin_country_applicability", "destination_country_applicability", "transit_country_applicability"],
                country,
            )
            and self._any_field_matches(item, ["seasonal_applicability"], season)
            and self._any_field_matches(item, ["capability_status", "capability_status_value"], capability_status)
            and self._any_field_matches(item, ["operational_risk_level"], operational_risk)
            and self._any_field_matches(
                item,
                ["capability_confidence", "operational_validity_confidence", "data_confidence_level", "evidence_confidence_level"],
                confidence_level,
            )
            and self._effective_on(item, effective_date)
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._capability_projection(item, read_only=False) for item in items]

    async def list_agency_capabilities(self, agency_id: str, **filters: Any) -> list[dict[str, Any]]:
        items = await self.list_platform_capabilities(agency_id=agency_id, **filters)
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def get_platform_capability(self, capability_id: str) -> dict[str, Any]:
        item = await self._require_capability(capability_id)
        return await self._capability_projection(item, read_only=False)

    async def get_agency_capability(self, agency_id: str, capability_id: str) -> dict[str, Any]:
        item = await self._require_capability(capability_id, agency_id=agency_id)
        return self._agency_projection(await self._capability_projection(item, read_only=True))

    async def create_capability(self, payload: AirlineCapabilityMatrixCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        data.setdefault("capability_reference", self._capability_reference())
        data.setdefault("capability_status", "draft")
        data.setdefault("capability_review_status", "not_started")
        self._validate_payload(data)
        data.setdefault("created_by", user.get("id"))
        data["updated_by"] = user.get("id")
        data.update(self.safety_flags())
        record = AirlineCapabilityMatrixRecord(**data)
        created = await self.db.collection(AIRLINE_CAPABILITY_MATRIX_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "airline_capability_matrix_record": await self._capability_projection(created, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_capability(self, capability_id: str, payload: AirlineCapabilityMatrixUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_capability(capability_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        self._validate_payload(updates, partial=True)
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(AIRLINE_CAPABILITY_MATRIX_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise AirlineCapabilityMatrixError("Airline capability matrix metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "airline_capability_matrix_record": await self._capability_projection(updated, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_capability(self, capability_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_capability(capability_id)
        now = self._now()
        updated = await self.db.collection(AIRLINE_CAPABILITY_MATRIX_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "capability_status": "archived",
                "archived_at": now,
                "deleted_at": now,
                "deleted_by": user.get("id"),
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise AirlineCapabilityMatrixError("Airline capability matrix metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "airline_capability_matrix_record": await self._capability_projection(updated, read_only=False),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "capability_count": len(items),
            "by_capability_status": self._counts(items, "capability_status", CAPABILITY_STATUSES),
            "by_capability_status_value": self._counts(items, "capability_status_value", CAPABILITY_STATUS_VALUES),
            "by_capability_outcome": self._counts(items, "capability_outcome", CAPABILITY_OUTCOMES),
            "by_review_status": self._counts(items, "capability_review_status", CAPABILITY_REVIEW_STATUSES),
            "by_operational_validity_status": self._counts(items, "operational_validity_status", OPERATIONAL_VALIDITY_STATUSES),
            "by_operational_risk_level": self._counts(items, "operational_risk_level", OPERATIONAL_RISK_LEVELS),
            "by_capability_confidence": self._counts(items, "capability_confidence", CONFIDENCE_LEVELS),
            "airline_count": len({item.get("airline_code") for item in items if item.get("airline_code")}),
            "service_domain_count": len({item.get("service_domain") for item in items if item.get("service_domain")}),
            "knowledge_governance_link_count": sum(
                len(item.get("knowledge_version_ids") or [])
                + len(item.get("knowledge_release_ids") or [])
                + len(item.get("acquisition_ids") or [])
                + len(item.get("normalisation_ids") or [])
                + len(item.get("constraint_ids") or [])
                + len(item.get("evidence_reference_ids") or [])
                for item in items
            ),
            "aircraft_cabin_capability_count": len([item for item in items if item.get("aircraft_family") or item.get("cabin_family") or item.get("cabin_name")]),
            "airport_station_capability_count": len([item for item in items if item.get("airport_applicability") or item.get("station_applicability")]),
            "route_country_season_capability_count": len([item for item in items if item.get("route_applicability") or item.get("seasonal_applicability")]),
            "animal_transport_capability_count": len([item for item in items if item.get("animal_transport_applicable") or item.get("petc_capability") or item.get("avih_capability")]),
            "extra_seat_capability_count": len([item for item in items if item.get("extra_seat_applicable") or item.get("extra_seat_available")]),
            "medical_accessibility_capability_count": len([item for item in items if item.get("wheelchair_capability") or item.get("medif_capability") or item.get("oxygen_capability")]),
            "manual_review_required_count": len([item for item in items if item.get("manual_review_required")]),
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "agency_id": "agency_id exact metadata match",
            "airline": "airline_code, airline_name, validating_carrier, operating_carrier, or marketing_carrier metadata match",
            "service_domain": "service_domain exact metadata match",
            "service_family": "service_family exact metadata match",
            "ssr_code": "ssr_code exact metadata match",
            "rfic": "rfic exact metadata match",
            "rfisc": "rfisc exact metadata match",
            "aircraft_family": "aircraft_family, aircraft_subtype, or aircraft_applicability metadata match",
            "cabin": "cabin_family, cabin_name, or cabin_applicability metadata match",
            "airport": "airport/station applicability metadata match",
            "route": "route_applicability metadata match",
            "country": "origin/destination/transit country applicability metadata match",
            "season": "seasonal_applicability metadata match",
            "capability_status": CAPABILITY_STATUSES + CAPABILITY_STATUS_VALUES,
            "operational_risk": OPERATIONAL_RISK_LEVELS,
            "confidence_level": CONFIDENCE_LEVELS,
            "effective_date": "metadata-only effective window filter",
            "metadata_only": True,
        }

    async def _capability_projection(self, item: dict[str, Any], *, read_only: bool) -> dict[str, Any]:
        projected = dict(item)
        projected["capability_display_name"] = projected.get("capability_name") or projected.get("capability_reference") or projected.get("id")
        projected["knowledge_governance_summary"] = self._knowledge_governance_summary(projected)
        projected["operational_dimension_summary"] = self._operational_dimension_summary(projected)
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["read_only"] = read_only
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["read_only"] = True
        projected.update(self.safety_flags())
        return projected

    async def _require_capability(self, capability_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": capability_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(AIRLINE_CAPABILITY_MATRIX_COLLECTION).find_one(filters)
        if not item:
            filters = {"capability_reference": capability_id}
            if agency_id:
                filters["agency_id"] = agency_id
            item = await self.db.collection(AIRLINE_CAPABILITY_MATRIX_COLLECTION).find_one(filters)
        if not item:
            raise AirlineCapabilityMatrixError("Airline capability matrix metadata was not found.")
        return item

    async def _agency_context(self, agency_id: str | None) -> dict[str, Any]:
        if not agency_id:
            return {"agency_id": None, "agency_name": None, "agency_slug": None, "metadata_only": True}
        agency = await self.db.collection("agencies").find_one({"id": agency_id})
        if not agency:
            return {"agency_id": agency_id, "agency_name": agency_id, "agency_slug": None, "metadata_only": True}
        return {
            "agency_id": agency.get("id"),
            "agency_name": agency.get("name"),
            "agency_slug": agency.get("slug"),
            "metadata_only": True,
        }

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        if data.get("capability_status") and data["capability_status"] not in CAPABILITY_STATUSES:
            raise AirlineCapabilityMatrixError("Capability status must be a known metadata status.")
        if data.get("capability_status_value") and data["capability_status_value"] not in CAPABILITY_STATUS_VALUES:
            raise AirlineCapabilityMatrixError("Capability status value must be known capability metadata.")
        if data.get("capability_outcome") and data["capability_outcome"] not in CAPABILITY_OUTCOMES:
            raise AirlineCapabilityMatrixError("Capability outcome must be known capability metadata.")
        if data.get("capability_review_status") and data["capability_review_status"] not in CAPABILITY_REVIEW_STATUSES:
            raise AirlineCapabilityMatrixError("Capability review status must be a known governance metadata status.")
        if data.get("operational_validity_status") and data["operational_validity_status"] not in OPERATIONAL_VALIDITY_STATUSES:
            raise AirlineCapabilityMatrixError("Operational validity status must be known validity metadata.")
        for field in ["capability_confidence", "operational_validity_confidence", "data_confidence_level", "evidence_confidence_level"]:
            if data.get(field) and data[field] not in CONFIDENCE_LEVELS:
                raise AirlineCapabilityMatrixError(f"{field} must be a known confidence level.")
        if data.get("operational_risk_level") and data["operational_risk_level"] not in OPERATIONAL_RISK_LEVELS:
            raise AirlineCapabilityMatrixError("Operational risk level must be known risk metadata.")
        if not partial and not (data.get("capability_name") or data.get("capability_reference")):
            raise AirlineCapabilityMatrixError("Capability name or reference is required for matrix metadata.")

    def _knowledge_governance_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {
            "knowledge_versions": len(item.get("knowledge_version_ids") or []),
            "knowledge_releases": len(item.get("knowledge_release_ids") or []),
            "acquisitions": len(item.get("acquisition_ids") or []),
            "normalisations": len(item.get("normalisation_ids") or []),
            "constraints": len(item.get("constraint_ids") or []),
            "evidence_references": len(item.get("evidence_reference_ids") or []),
        }

    def _operational_dimension_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "airline": item.get("airline_code") or item.get("airline_name"),
            "service": " / ".join([part for part in [item.get("service_domain"), item.get("service_family"), item.get("service_variant")] if part]),
            "aircraft": item.get("aircraft_family") or item.get("aircraft_subtype") or ", ".join(item.get("aircraft_applicability") or []),
            "cabin": item.get("cabin_family") or item.get("cabin_name") or ", ".join(item.get("cabin_applicability") or []),
            "airports": len(item.get("airport_applicability") or []) + len(item.get("station_applicability") or []),
            "routes": len(item.get("route_applicability") or []),
            "countries": len(item.get("origin_country_applicability") or []) + len(item.get("destination_country_applicability") or []) + len(item.get("transit_country_applicability") or []),
            "seasons": len(item.get("seasonal_applicability") or []),
            "metadata_only": True,
        }

    def _counts(self, items: list[dict[str, Any]], field: str, known: list[str]) -> dict[str, int]:
        counts = {value: 0 for value in known}
        for item in items:
            value = item.get(field)
            if value:
                counts[str(value)] = counts.get(str(value), 0) + 1
        return counts

    def _any_field_matches(self, item: dict[str, Any], fields: list[str], value: str | None) -> bool:
        if not value:
            return True
        return any(self._value_matches(item.get(field), value) for field in fields)

    def _value_matches(self, candidate: Any, value: str) -> bool:
        normalized = value.lower()
        if isinstance(candidate, list):
            return normalized in {str(item).lower() for item in candidate}
        if candidate is None:
            return False
        return normalized == str(candidate).lower()

    def _effective_on(self, item: dict[str, Any], effective_date: str | None) -> bool:
        if not effective_date:
            return True
        effective = effective_date[:10]
        start = self._date_text(item.get("effective_from"))
        end = self._date_text(item.get("effective_until"))
        if start and effective < start:
            return False
        if end and effective > end:
            return False
        return True

    def _date_text(self, value: Any) -> str | None:
        if not value:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()[:10]
        return str(value)[:10]

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def _capability_reference(self) -> str:
        return f"ACM-{new_id()[:8].upper()}"

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "capability_matrix_foundation": True,
            "live_rule_evaluation_disabled": True,
            "passenger_feasibility_scoring_disabled": True,
            "airline_recommendation_ranking_disabled": True,
            "ai_reasoning_disabled": True,
            "parser_execution_disabled": True,
            "pricing_calculation_disabled": True,
            "provider_integrations_disabled": True,
            "background_workers_disabled": True,
            "automatic_publication_disabled": True,
            "scraping_disabled": True,
        }
