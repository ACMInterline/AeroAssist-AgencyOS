from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import ServiceParameterTaxonomy, ServiceParameterTaxonomyCreate, ServiceParameterTaxonomyUpdate


PHASE_LABEL = "phase_54_5_request_to_trip_operational_conversion_foundation"
SERVICE_PARAMETER_TAXONOMIES_COLLECTION = "service_parameter_taxonomies"

SERVICE_PARAMETER_TAXONOMY_STATUSES = ["draft", "active", "in_review", "approved", "deprecated", "archived"]
TAXONOMY_REVIEW_STATUSES = ["not_reviewed", "in_review", "changes_requested", "reviewed", "approved", "rejected"]
TAXONOMY_APPROVAL_STATUSES = ["not_submitted", "pending", "approved", "rejected", "expired"]

SUPPORT_STATUS_OPTIONS = [
    "yes",
    "no",
    "conditional",
    "seasonal",
    "route_restricted",
    "aircraft_restricted",
    "manual_review",
    "restricted",
    "unknown",
]
EVALUATION_STATUS_OPTIONS = [
    "feasible",
    "conditional",
    "requires_approval",
    "requires_documents",
    "restricted",
    "blocked",
    "manual_review",
    "unknown",
]
RESTRICTION_STATUS_OPTIONS = [
    "none",
    "conditional",
    "restricted",
    "blocked",
    "seasonal",
    "route_restricted",
    "aircraft_restricted",
    "manual_review",
    "unknown",
]
APPROVAL_STATUS_OPTIONS = [
    "not_required",
    "required",
    "requested",
    "approved",
    "rejected",
    "expired",
    "manual_review",
    "unknown",
]

PRICING_UNITS = [
    "passenger",
    "passenger_per_segment",
    "pet",
    "pet_per_segment",
    "item",
    "item_per_segment",
    "booking",
    "trip",
    "request",
    "document",
    "hour",
    "case",
]
PRICING_WAY_VALUES = ["one_way", "round_trip", "per_direction", "open_jaw", "multi_city"]
PRICING_ROUTE_TYPES = ["domestic", "international", "regional_cross_border", "schengen", "non_schengen"]
PRICING_FLIGHT_TYPES = ["short", "regional", "mediumhaul", "longhaul", "ultra_longhaul", "interline", "connecting"]
PRICING_FARE_BUNDLES = ["basic", "standard", "flex", "premium", "business", "custom", "unknown"]
AMOUNT_TYPES = ["fixed", "range", "percentage", "manual_quote", "formula", "included", "not_applicable"]
PRICING_CATEGORIES = [
    "transport_core",
    "ancillary_airline",
    "ancillary_non_airline",
    "documentation",
    "service_coordination",
    "compliance_review",
    "manual_handling",
    "premium_support",
    "after_sales_change",
    "refund_processing",
    "claim_processing",
]

PASSENGER_ASSISTANCE_PARAMETER_FIELDS = [
    "wheelchair_mobility_parameters",
    "mobility_level_parameters",
    "wheelchair_device_parameters",
    "battery_type_parameters",
    "device_weight_dimension_parameters",
    "airport_assistance_parameters",
    "onboard_assistance_parameters",
    "medical_support_parameters",
    "medif_parameters",
    "fit_to_fly_parameters",
    "stretcher_parameters",
    "oxygen_poc_parameters",
    "battery_duration_parameters",
    "umnr_age_parameters",
    "umnr_route_parameters",
    "guardian_parameters",
    "extra_seat_parameters",
    "passenger_of_size_parameters",
    "cbbg_parameters",
    "adjacent_seat_parameters",
    "cabin_restriction_parameters",
    "extra_seat_refund_parameters",
]
PETS_ANIMALS_PARAMETER_FIELDS = [
    "petc_parameters",
    "avih_parameters",
    "svan_parameters",
    "esan_parameters",
    "species_parameters",
    "breed_parameters",
    "breed_risk_flag_parameters",
    "animal_age_parameters",
    "animal_weight_parameters",
    "container_dimension_parameters",
    "container_type_parameters",
    "pet_under_seat_parameters",
    "pet_on_adjacent_extra_seat_parameters",
    "animal_purpose_parameters",
    "temperature_parameters",
    "seasonal_restriction_parameters",
    "animal_document_parameters",
]
SPECIAL_ITEM_PARAMETER_FIELDS = [
    "sports_equipment_parameters",
    "musical_instrument_parameters",
    "fragile_valuable_parameters",
    "restricted_equipment_parameters",
    "special_baggage_parameters",
    "item_type_parameters",
    "item_weight_dimension_parameters",
    "packaging_parameters",
    "declared_value_parameters",
    "permit_document_parameters",
]
ROUTE_AIRCRAFT_CABIN_PARAMETER_FIELDS = [
    "route_type_parameters",
    "flight_type_parameters",
    "airport_parameters",
    "country_parameters",
    "aircraft_type_parameters",
    "aircraft_family_parameters",
    "cabin_parameters",
    "seat_type_parameters",
    "fixed_armrest_parameters",
    "under_seat_space_parameters",
    "accessible_lavatory_parameters",
]
PRICING_PARAMETER_FIELDS = [
    "pricing_units",
    "pricing_way_values",
    "pricing_route_types",
    "pricing_flight_types",
    "pricing_fare_bundles",
    "pricing_categories",
    "amount_types",
    "pricing_basis_parameters",
    "pricing_formula_components",
    "pricing_applicability_parameters",
    "refund_condition_parameters",
    "exchange_condition_parameters",
]
KNOWLEDGE_GRAPH_LINK_FIELDS = [
    "acquisition_ids",
    "normalisation_ids",
    "constraint_ids",
    "knowledge_version_ids",
    "capability_matrix_ids",
    "operational_evaluation_ids",
    "feasibility_ids",
    "recommendation_ids",
    "intelligent_offer_package_ids",
    "operational_intelligence_case_ids",
]

DEFAULT_SERVICE_PARAMETER_TAXONOMY_TEMPLATES: list[dict[str, Any]] = [
    {
        "parameter_group": "wheelchair_mobility",
        "service_family": "passenger_assistance",
        "service_codes": ["WCHR", "WCHS", "WCHC", "WCOB", "MAAS"],
        "parameter_fields": [
            "mobility_level",
            "wheelchair_type",
            "battery_type",
            "device_dimensions",
            "onboard_aisle_chair",
            "airport_assistance",
        ],
    },
    {
        "parameter_group": "medical_support",
        "service_family": "passenger_assistance",
        "service_codes": ["MEDA", "MEDIF", "STCR"],
        "parameter_fields": ["medical_clearance", "medif_required", "fit_to_fly", "stretcher", "escort_requirement"],
    },
    {
        "parameter_group": "oxygen_poc",
        "service_family": "passenger_assistance",
        "service_codes": ["OXYG", "POC"],
        "parameter_fields": ["battery_duration", "device_model", "approval_status", "documents", "inflight_use"],
    },
    {
        "parameter_group": "umnr",
        "service_family": "passenger_assistance",
        "service_codes": ["UMNR", "YP"],
        "parameter_fields": ["age", "route", "connection", "guardian", "handoff_documents"],
    },
    {
        "parameter_group": "extra_seat",
        "service_family": "passenger_assistance",
        "service_codes": ["EXST", "CBBG"],
        "parameter_fields": ["reason", "adjacent_seat", "cabin_restriction", "fixed_armrest", "refund_condition"],
    },
    {
        "parameter_group": "pet_transport",
        "service_family": "pets_animals",
        "service_codes": ["PETC", "AVIH"],
        "parameter_fields": ["species", "breed", "weight", "container_dimensions", "temperature", "documents"],
    },
    {
        "parameter_group": "service_animal",
        "service_family": "pets_animals",
        "service_codes": ["SVAN"],
        "parameter_fields": ["animal_purpose", "species", "documents", "route", "seat_space", "approval_status"],
    },
    {
        "parameter_group": "emotional_support_animal",
        "service_family": "pets_animals",
        "service_codes": ["ESAN"],
        "parameter_fields": ["animal_purpose", "legacy_acceptance", "documents", "route", "restriction_status"],
    },
    {
        "parameter_group": "sports_equipment",
        "service_family": "special_items_baggage",
        "service_codes": ["SPEQ", "BIKE", "SKI", "GOLF", "SURF", "DIVE"],
        "parameter_fields": ["item_type", "weight", "dimensions", "packaging", "permit_documents"],
    },
    {
        "parameter_group": "musical_instruments",
        "service_family": "special_items_baggage",
        "service_codes": ["MUSI", "CBBG", "EXST"],
        "parameter_fields": ["instrument_type", "seat_required", "case_dimensions", "declared_value", "cabin_restriction"],
    },
    {
        "parameter_group": "fragile_valuable",
        "service_family": "special_items_baggage",
        "service_codes": ["FRAGILE", "VALUABLE", "CBBG", "EXST"],
        "parameter_fields": ["item_type", "declared_value", "packaging", "seat_required", "acceptance_condition"],
    },
    {
        "parameter_group": "restricted_equipment",
        "service_family": "special_items_baggage",
        "service_codes": ["WEAP"],
        "parameter_fields": ["item_type", "permit_documents", "country", "airport", "handling_restriction"],
    },
    {
        "parameter_group": "special_baggage",
        "service_family": "special_items_baggage",
        "service_codes": [],
        "parameter_fields": ["item_type", "weight", "dimensions", "packaging", "manual_review"],
    },
    {
        "parameter_group": "pricing",
        "service_family": "pricing",
        "service_codes": [],
        "parameter_fields": ["unit", "way", "route_type", "flight_type", "fare_bundle", "amount_type", "formula_components"],
        "pricing_units": PRICING_UNITS,
        "way_values": PRICING_WAY_VALUES,
        "route_types": PRICING_ROUTE_TYPES,
        "flight_types": PRICING_FLIGHT_TYPES,
        "fare_bundles": PRICING_FARE_BUNDLES,
        "amount_types": AMOUNT_TYPES,
        "pricing_categories": PRICING_CATEGORIES,
    },
]


class ServiceParameterTaxonomyError(ValueError):
    pass


class ServiceParameterTaxonomyService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        taxonomies = await self.list_platform_taxonomies(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": taxonomies,
            "taxonomies": taxonomies,
            "summary": self.summarize_counts(taxonomies),
            "filters": self.filter_metadata(),
            "templates": DEFAULT_SERVICE_PARAMETER_TAXONOMY_TEMPLATES,
            "read_only": False,
            "metadata_only": True,
            "notice": "Service Parameter Taxonomies define reusable measurable metadata fields. They do not evaluate rules, calculate prices, call providers, run AI/LLM logic, execute recommendations, or run workers.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        taxonomies = await self.list_agency_taxonomies(agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": taxonomies,
            "taxonomies": taxonomies,
            "summary": self.summarize_counts(taxonomies),
            "filters": self.filter_metadata(),
            "templates": DEFAULT_SERVICE_PARAMETER_TAXONOMY_TEMPLATES,
            "read_only": False,
            "metadata_only": True,
            "notice": "Agency Service Parameter Taxonomies expose reusable measurable metadata fields for human-reviewed operations.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        taxonomies = await self.list_platform_taxonomies()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(taxonomies),
            "filters": self.filter_metadata(),
            "templates": DEFAULT_SERVICE_PARAMETER_TAXONOMY_TEMPLATES,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        taxonomies = await self.list_agency_taxonomies(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(taxonomies),
            "filters": self.filter_metadata(),
            "templates": DEFAULT_SERVICE_PARAMETER_TAXONOMY_TEMPLATES,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_platform_taxonomies(
        self,
        *,
        agency_id: str | None = None,
        taxonomy_status: str | None = None,
        policy_family: str | None = None,
        service_family: str | None = None,
        service_code: str | None = None,
        parameter_domain: str | None = None,
        parameter_group: str | None = None,
        parameter_scope: str | None = None,
        review_status: str | None = None,
        approval_status: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if taxonomy_status:
            filters["taxonomy_status"] = taxonomy_status
        if policy_family:
            filters["policy_family"] = policy_family
        if service_family:
            filters["service_family"] = service_family
        if parameter_domain:
            filters["parameter_domain"] = parameter_domain
        if parameter_group:
            filters["parameter_group"] = parameter_group
        if parameter_scope:
            filters["parameter_scope"] = parameter_scope
        if review_status:
            filters["review_status"] = review_status
        if approval_status:
            filters["approval_status"] = approval_status

        items = await self.db.collection(SERVICE_PARAMETER_TAXONOMIES_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("taxonomy_status") != "archived"]
        items = [item for item in items if self._service_code_matches(item, service_code)]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._taxonomy_projection(item, read_only=False) for item in items]

    async def list_agency_taxonomies(self, agency_id: str, **filters: Any) -> list[dict[str, Any]]:
        items = await self.list_platform_taxonomies(agency_id=agency_id, **filters)
        return [await self._taxonomy_projection(item, read_only=False) for item in items if item.get("agency_id") == agency_id]

    async def get_platform_taxonomy(self, taxonomy_id: str) -> dict[str, Any]:
        item = await self._require_taxonomy(taxonomy_id)
        return await self._taxonomy_projection(item, read_only=False)

    async def get_agency_taxonomy(self, agency_id: str, taxonomy_id: str) -> dict[str, Any]:
        item = await self._require_taxonomy(taxonomy_id, agency_id=agency_id)
        return await self._taxonomy_projection(item, read_only=False)

    async def create_taxonomy(
        self,
        payload: ServiceParameterTaxonomyCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data.setdefault("taxonomy_reference", self._taxonomy_reference())
        data.setdefault("taxonomy_status", "draft")
        data.setdefault("created_by", user.get("id"))
        self._apply_defaults(data)
        self._validate_payload(data)
        data.update(self.safety_flags())
        record = ServiceParameterTaxonomy(**data)
        created = await self.db.collection(SERVICE_PARAMETER_TAXONOMIES_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "service_parameter_taxonomy": await self._taxonomy_projection(created, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_taxonomy(
        self,
        taxonomy_id: str,
        payload: ServiceParameterTaxonomyUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_taxonomy(taxonomy_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if agency_id:
            updates.pop("agency_id", None)
        self._apply_defaults(updates, partial=True)
        self._validate_payload(updates, partial=True)
        updates.update(self.safety_flags())
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(SERVICE_PARAMETER_TAXONOMIES_COLLECTION).update_one(filters, updates)
        if not updated:
            raise ServiceParameterTaxonomyError("Service parameter taxonomy metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "service_parameter_taxonomy": await self._taxonomy_projection(updated, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_taxonomy(self, taxonomy_id: str, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_taxonomy(taxonomy_id, agency_id=agency_id)
        updates = {
            "taxonomy_status": "archived",
            "archived": True,
            "archived_at": self._now(),
            **self.safety_flags(),
        }
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(SERVICE_PARAMETER_TAXONOMIES_COLLECTION).update_one(filters, updates)
        if not updated:
            raise ServiceParameterTaxonomyError("Service parameter taxonomy metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "service_parameter_taxonomy": await self._taxonomy_projection(updated, read_only=False),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "taxonomy_count": len(items),
            "by_taxonomy_status": self._counts(items, "taxonomy_status", SERVICE_PARAMETER_TAXONOMY_STATUSES),
            "by_review_status": self._counts(items, "review_status", TAXONOMY_REVIEW_STATUSES),
            "by_approval_status": self._counts(items, "approval_status", TAXONOMY_APPROVAL_STATUSES),
            "service_code_count": sum(len(item.get("service_codes") or []) for item in items),
            "passenger_assistance_parameter_count": self._group_count(items, PASSENGER_ASSISTANCE_PARAMETER_FIELDS),
            "pets_animals_parameter_count": self._group_count(items, PETS_ANIMALS_PARAMETER_FIELDS),
            "special_item_parameter_count": self._group_count(items, SPECIAL_ITEM_PARAMETER_FIELDS),
            "route_aircraft_cabin_parameter_count": self._group_count(items, ROUTE_AIRCRAFT_CABIN_PARAMETER_FIELDS),
            "pricing_parameter_count": self._group_count(items, PRICING_PARAMETER_FIELDS),
            "reference_requirement_count": sum(
                len(item.get("required_reference_collections") or []) + len(item.get("required_reference_values") or [])
                for item in items
            ),
            "knowledge_graph_link_count": self._group_count(items, KNOWLEDGE_GRAPH_LINK_FIELDS),
            "template_count": len(DEFAULT_SERVICE_PARAMETER_TAXONOMY_TEMPLATES),
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "agency_id": "agency_id exact metadata match",
            "taxonomy_status": SERVICE_PARAMETER_TAXONOMY_STATUSES,
            "policy_family": "policy family exact metadata match",
            "service_family": "service family exact metadata match",
            "service_code": "service_codes metadata match",
            "parameter_domain": "parameter domain exact metadata match",
            "parameter_group": "parameter group exact metadata match",
            "parameter_scope": "parameter scope exact metadata match",
            "review_status": TAXONOMY_REVIEW_STATUSES,
            "approval_status": TAXONOMY_APPROVAL_STATUSES,
            "metadata_only": True,
        }

    async def _taxonomy_projection(self, item: dict[str, Any], *, read_only: bool) -> dict[str, Any]:
        projected = dict(item)
        projected["taxonomy_display_name"] = projected.get("taxonomy_name") or projected.get("taxonomy_reference") or projected.get("id")
        projected["parameter_summary"] = self._parameter_summary(projected)
        projected["vocabulary_summary"] = self._vocabulary_summary(projected)
        projected["knowledge_graph_link_summary"] = self._knowledge_graph_link_summary(projected)
        projected["governance_summary"] = self._governance_summary(projected)
        projected["template_matches"] = self._template_matches(projected)
        projected["read_only"] = read_only
        projected.update(self.safety_flags())
        return projected

    async def _require_taxonomy(self, taxonomy_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": taxonomy_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(SERVICE_PARAMETER_TAXONOMIES_COLLECTION).find_one(filters)
        if not item:
            raise ServiceParameterTaxonomyError("Service parameter taxonomy metadata not found.")
        return item

    def _apply_defaults(self, data: dict[str, Any], *, partial: bool = False) -> None:
        if partial:
            return
        if not data.get("support_status_options"):
            data["support_status_options"] = SUPPORT_STATUS_OPTIONS
        if not data.get("evaluation_status_options"):
            data["evaluation_status_options"] = EVALUATION_STATUS_OPTIONS
        if not data.get("restriction_status_options"):
            data["restriction_status_options"] = RESTRICTION_STATUS_OPTIONS
        if not data.get("approval_status_options"):
            data["approval_status_options"] = APPROVAL_STATUS_OPTIONS
        if data.get("parameter_group") == "pricing" or data.get("service_family") == "pricing":
            if not data.get("pricing_units"):
                data["pricing_units"] = PRICING_UNITS
            if not data.get("pricing_way_values"):
                data["pricing_way_values"] = PRICING_WAY_VALUES
            if not data.get("pricing_route_types"):
                data["pricing_route_types"] = PRICING_ROUTE_TYPES
            if not data.get("pricing_flight_types"):
                data["pricing_flight_types"] = PRICING_FLIGHT_TYPES
            if not data.get("pricing_fare_bundles"):
                data["pricing_fare_bundles"] = PRICING_FARE_BUNDLES
            if not data.get("pricing_categories"):
                data["pricing_categories"] = PRICING_CATEGORIES
            if not data.get("amount_types"):
                data["amount_types"] = AMOUNT_TYPES

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "taxonomy_status", SERVICE_PARAMETER_TAXONOMY_STATUSES, partial)
        self._validate_choice(data, "review_status", TAXONOMY_REVIEW_STATUSES, partial)
        self._validate_choice(data, "approval_status", TAXONOMY_APPROVAL_STATUSES, partial)

    def _validate_choice(self, data: dict[str, Any], field: str, allowed: list[str], partial: bool) -> None:
        if field not in data:
            return
        value = data.get(field)
        if value is None:
            return
        if value not in allowed:
            raise ServiceParameterTaxonomyError(f"Unsupported {field} metadata value: {value}.")

    def _parameter_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {
            "passenger_assistance": self._item_group_count(item, PASSENGER_ASSISTANCE_PARAMETER_FIELDS),
            "pets_animals": self._item_group_count(item, PETS_ANIMALS_PARAMETER_FIELDS),
            "special_items_baggage": self._item_group_count(item, SPECIAL_ITEM_PARAMETER_FIELDS),
            "route_aircraft_cabin": self._item_group_count(item, ROUTE_AIRCRAFT_CABIN_PARAMETER_FIELDS),
            "pricing": self._item_group_count(item, PRICING_PARAMETER_FIELDS),
        }

    def _vocabulary_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {
            "support_status_options": len(item.get("support_status_options") or []),
            "evaluation_status_options": len(item.get("evaluation_status_options") or []),
            "restriction_status_options": len(item.get("restriction_status_options") or []),
            "approval_status_options": len(item.get("approval_status_options") or []),
        }

    def _knowledge_graph_link_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {field: len(item.get(field) or []) for field in KNOWLEDGE_GRAPH_LINK_FIELDS}

    def _governance_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "review_status": item.get("review_status"),
            "approval_status": item.get("approval_status"),
            "reviewer": item.get("reviewer"),
            "approved_by": item.get("approved_by"),
            "approved_at": item.get("approved_at"),
        }

    def _template_matches(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        service_codes = set(item.get("service_codes") or [])
        parameter_group = item.get("parameter_group")
        service_family = item.get("service_family")
        matches: list[dict[str, Any]] = []
        for template in DEFAULT_SERVICE_PARAMETER_TAXONOMY_TEMPLATES:
            template_codes = set(template.get("service_codes") or [])
            if parameter_group and parameter_group == template.get("parameter_group"):
                matches.append(template)
            elif service_family and service_family == template.get("service_family") and service_codes.intersection(template_codes):
                matches.append(template)
            elif service_codes.intersection(template_codes):
                matches.append(template)
        return matches

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "service_parameter_taxonomy_integration_foundation": True,
            "measurable_service_parameters_enabled": True,
            "current_architecture_integrated": True,
            "parameter_taxonomies_reusable": True,
            "policy_pricing_capability_constraints_procedures_separate": True,
            "standalone_policy_engine_disabled": True,
            "legacy_pricing_engine_disabled": True,
            "pocketbase_logic_disabled": True,
            "duplicate_operational_models_disabled": True,
            "live_rule_evaluation_disabled": True,
            "live_pricing_calculation_disabled": True,
            "recommendation_execution_disabled": True,
            "provider_integrations_disabled": True,
            "no_ai_generation": True,
            "no_llm_generation": True,
            "background_workers_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "human_authority_final": True,
        }

    def _service_code_matches(self, item: dict[str, Any], expected: str | None) -> bool:
        if expected in (None, ""):
            return True
        expected_text = str(expected).lower()
        return any(expected_text == str(code).lower() for code in item.get("service_codes") or [])

    def _group_count(self, items: list[dict[str, Any]], fields: list[str]) -> int:
        return sum(self._item_group_count(item, fields) for item in items)

    def _item_group_count(self, item: dict[str, Any], fields: list[str]) -> int:
        return sum(len(item.get(field) or []) for field in fields)

    def _counts(self, items: list[dict[str, Any]], field: str, values: list[str]) -> dict[str, int]:
        return {value: len([item for item in items if item.get(field) == value]) for value in values}

    def _taxonomy_reference(self) -> str:
        return f"SPT-{self._now().replace(':', '').replace('-', '').replace('.', '')}"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _sort_text(self, value: Any) -> str:
        return str(value or "")
