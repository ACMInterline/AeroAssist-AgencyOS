from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import PricingFormulaBuilder, PricingFormulaBuilderCreate, PricingFormulaBuilderUpdate
from services.service_parameter_taxonomy_service import (
    AMOUNT_TYPES,
    PRICING_CATEGORIES,
    PRICING_FARE_BUNDLES,
    PRICING_FLIGHT_TYPES,
    PRICING_ROUTE_TYPES,
    PRICING_UNITS,
    PRICING_WAY_VALUES,
)


PHASE_LABEL = "phase_54_2_agent_work_queue_assignment_foundation"
PRICING_FORMULA_BUILDERS_COLLECTION = "pricing_formula_builders"

FORMULA_STATUSES = ["draft", "in_review", "approved", "retired", "archived"]
CLIENT_VISIBILITY_OPTIONS = ["internal_only", "agent_visible", "client_visible", "client_hidden", "manual_review"]


class PricingFormulaBuilderError(ValueError):
    pass


class PricingFormulaBuilderService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        formulas = await self.list_formulas(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": formulas,
            "pricing_formulas": formulas,
            "summary": await self.summarize_counts(filters.get("agency_id")),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Pricing Formula Builder records store structured pricing metadata for human review. They do not calculate live prices, call providers, integrate payments, generate AI output, send client messages, or run background workers.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        formulas = await self.list_formulas(agency_id=agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": formulas,
            "pricing_formulas": formulas,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Agency Pricing Formula Builder shows metadata-only ancillary and service pricing formulas. Human authority remains final.",
            **self.safety_flags(),
        }

    async def platform_summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_formulas(
        self,
        *,
        agency_id: str | None = None,
        airline: str | None = None,
        service_family: str | None = None,
        service_code: str | None = None,
        pricing_unit: str | None = None,
        way: str | None = None,
        route_type: str | None = None,
        flight_type: str | None = None,
        fare_bundle: str | None = None,
        pricing_category: str | None = None,
        amount_type: str | None = None,
        currency: str | None = None,
        formula_status: str | None = None,
        manual_confirmation_required: bool | None = None,
        client_visibility: str | None = None,
        search: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if airline:
            filters["airline"] = self._normalize_airline(airline)
        if service_family:
            filters["service_family"] = self._normalize_code(service_family)
        if pricing_unit:
            filters["pricing_unit"] = self._normalize_code(pricing_unit)
        if way:
            filters["way"] = self._normalize_code(way)
        if route_type:
            filters["route_type"] = self._normalize_code(route_type)
        if flight_type:
            filters["flight_type"] = self._normalize_code(flight_type)
        if fare_bundle:
            filters["fare_bundle"] = self._normalize_code(fare_bundle)
        if pricing_category:
            filters["pricing_category"] = self._normalize_code(pricing_category)
        if amount_type:
            filters["amount_type"] = self._normalize_code(amount_type)
        if currency:
            filters["currency"] = self._normalize_currency(currency)
        if formula_status:
            filters["formula_status"] = self._normalize_code(formula_status)
        if manual_confirmation_required is not None:
            filters["manual_confirmation_required"] = manual_confirmation_required
        if client_visibility:
            filters["client_visibility"] = self._normalize_code(client_visibility)

        items = await self.db.collection(PRICING_FORMULA_BUILDERS_COLLECTION).find_many(filters or None)
        if service_code:
            code = self._normalize_service_code(service_code)
            items = [item for item in items if code in (item.get("service_codes") or [])]
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("formula_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(
                item,
                [
                    "formula_reference",
                    "formula_name",
                    "formula_status",
                    "airline",
                    "service_family",
                    "service_codes",
                    "pricing_unit",
                    "way",
                    "route_type",
                    "flight_type",
                    "fare_bundle",
                    "pricing_category",
                    "amount_type",
                    "currency",
                    "formula_components",
                    "multipliers",
                    "applicability",
                    "client_visibility",
                    "refund_exchange_condition_references",
                    "evidence_links",
                    "governance_links",
                    "service_parameter_taxonomy_links",
                    "visual_policy_editor_links",
                    "internal_notes",
                    "client_notes",
                    "metadata",
                ],
                search,
            )
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._formula_projection(item) for item in items]

    async def get_formula(self, formula_id: str, agency_id: str | None = None) -> dict[str, Any]:
        item = await self._require_formula(formula_id, agency_id=agency_id)
        return await self._formula_projection(item)

    async def create_formula(
        self,
        payload: PricingFormulaBuilderCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data = self._normalize_payload(data)
        data.setdefault("formula_reference", self._reference("PFB"))
        data.setdefault("formula_status", "draft")
        data.setdefault("manual_confirmation_required", True)
        data.setdefault("client_visibility", "internal_only")
        data.update(self.safety_flags())
        self._validate_payload(data)
        record = PricingFormulaBuilder(**data)
        created = await self.db.collection(PRICING_FORMULA_BUILDERS_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "pricing_formula_builder": await self._formula_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_formula(
        self,
        formula_id: str,
        payload: PricingFormulaBuilderUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_formula(formula_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if agency_id:
            updates.pop("agency_id", None)
        updates = self._normalize_payload(updates)
        updates.update(self.safety_flags())
        self._validate_payload(updates, partial=True)
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(PRICING_FORMULA_BUILDERS_COLLECTION).update_one(filters, updates)
        if not updated:
            raise PricingFormulaBuilderError("Pricing formula builder metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "pricing_formula_builder": await self._formula_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_formula(self, formula_id: str, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_formula(formula_id, agency_id=agency_id)
        updates = {
            "formula_status": "archived",
            "archived": True,
            "archived_at": self._now(),
            **self.safety_flags(),
        }
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(PRICING_FORMULA_BUILDERS_COLLECTION).update_one(filters, updates)
        if not updated:
            raise PricingFormulaBuilderError("Pricing formula builder metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "pricing_formula_builder": await self._formula_projection(updated),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def summarize_counts(self, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        formulas = await self.db.collection(PRICING_FORMULA_BUILDERS_COLLECTION).find_many(filters)
        covered_categories = {item.get("pricing_category") for item in formulas if item.get("pricing_category") in PRICING_CATEGORIES}
        return {
            "pricing_formula_builder_count": len(formulas),
            "active_formula_count": len([item for item in formulas if not item.get("archived") and item.get("formula_status") != "archived"]),
            "service_code_count": sum(len(item.get("service_codes") or []) for item in formulas),
            "formula_component_count": sum(len(item.get("formula_components") or []) for item in formulas),
            "multiplier_count": sum(len(item.get("multipliers") or []) for item in formulas),
            "refund_exchange_reference_count": sum(len(item.get("refund_exchange_condition_references") or []) for item in formulas),
            "evidence_link_count": sum(len(item.get("evidence_links") or []) for item in formulas),
            "governance_link_count": sum(len(item.get("governance_links") or []) for item in formulas),
            "service_parameter_taxonomy_link_count": sum(len(item.get("service_parameter_taxonomy_links") or []) for item in formulas),
            "visual_policy_editor_link_count": sum(len(item.get("visual_policy_editor_links") or []) for item in formulas),
            "manual_confirmation_required_count": len([item for item in formulas if item.get("manual_confirmation_required") is True]),
            "client_visible_count": len([item for item in formulas if item.get("client_visibility") == "client_visible"]),
            "by_status": self._counts(formulas, "formula_status", FORMULA_STATUSES),
            "by_amount_type": self._counts(formulas, "amount_type", AMOUNT_TYPES),
            "by_pricing_category": self._counts(formulas, "pricing_category", PRICING_CATEGORIES),
            "supported_pricing_category_count": len(PRICING_CATEGORIES),
            "covered_pricing_category_count": len(covered_categories),
            "missing_pricing_categories": [category for category in PRICING_CATEGORIES if category not in covered_categories],
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "airline": "IATA or carrier code text",
            "service_family": "service family code",
            "service_code": "SSR, OSI, or internal service code",
            "pricing_unit": PRICING_UNITS,
            "way": PRICING_WAY_VALUES,
            "route_type": PRICING_ROUTE_TYPES,
            "flight_type": PRICING_FLIGHT_TYPES,
            "fare_bundle": PRICING_FARE_BUNDLES,
            "pricing_category": PRICING_CATEGORIES,
            "amount_type": AMOUNT_TYPES,
            "currency": "ISO currency code",
            "formula_status": FORMULA_STATUSES,
            "manual_confirmation_required": "true or false",
            "client_visibility": CLIENT_VISIBILITY_OPTIONS,
            "search": "reference, name, airline, service, pricing vocabulary, components, multipliers, applicability, notes, or links",
            "metadata_only": True,
        }

    async def _formula_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["formula_display_name"] = " / ".join(
            part
            for part in [
                projected.get("airline"),
                projected.get("formula_name") or projected.get("formula_reference"),
                projected.get("pricing_category"),
            ]
            if part
        )
        projected["overview_section"] = {
            "formula_reference": projected.get("formula_reference"),
            "formula_name": projected.get("formula_name"),
            "formula_status": projected.get("formula_status"),
            "airline": projected.get("airline"),
            "service_family": projected.get("service_family"),
            "service_codes": projected.get("service_codes") or [],
        }
        projected["pricing_context_section"] = {
            "pricing_unit": projected.get("pricing_unit"),
            "way": projected.get("way"),
            "route_type": projected.get("route_type"),
            "flight_type": projected.get("flight_type"),
            "fare_bundle": projected.get("fare_bundle"),
            "pricing_category": projected.get("pricing_category"),
        }
        projected["amount_section"] = {
            "amount_type": projected.get("amount_type"),
            "currency": projected.get("currency"),
            "base_amount": projected.get("base_amount"),
            "amount_range": projected.get("amount_range") or {},
        }
        projected["formula_components_section"] = {
            "formula_components": projected.get("formula_components") or [],
            "formula_component_count": len(projected.get("formula_components") or []),
        }
        projected["multipliers_section"] = {
            "multipliers": projected.get("multipliers") or [],
            "multiplier_count": len(projected.get("multipliers") or []),
        }
        projected["applicability_section"] = projected.get("applicability") or {}
        projected["review_visibility_section"] = {
            "manual_confirmation_required": projected.get("manual_confirmation_required"),
            "client_visibility": projected.get("client_visibility"),
            "internal_notes": projected.get("internal_notes"),
            "client_notes": projected.get("client_notes"),
            "human_authority_final": True,
        }
        projected["refund_exchange_section"] = {
            "refund_exchange_condition_references": projected.get("refund_exchange_condition_references") or [],
            "refund_exchange_reference_count": len(projected.get("refund_exchange_condition_references") or []),
        }
        projected["evidence_governance_section"] = {
            "evidence_links": projected.get("evidence_links") or [],
            "governance_links": projected.get("governance_links") or [],
            "service_parameter_taxonomy_links": projected.get("service_parameter_taxonomy_links") or [],
            "visual_policy_editor_links": projected.get("visual_policy_editor_links") or [],
            "archived": projected.get("archived"),
            "archived_at": projected.get("archived_at"),
        }
        projected["no_code_sections"] = {
            "overview": projected["overview_section"],
            "pricing_context": projected["pricing_context_section"],
            "amount": projected["amount_section"],
            "formula_components": projected["formula_components_section"],
            "multipliers": projected["multipliers_section"],
            "applicability": projected["applicability_section"],
            "review_visibility": projected["review_visibility_section"],
            "refund_exchange": projected["refund_exchange_section"],
            "evidence_governance": projected["evidence_governance_section"],
        }
        projected["boundary_section"] = self.safety_flags()
        projected.update(self.safety_flags())
        return projected

    async def _require_formula(self, formula_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": formula_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(PRICING_FORMULA_BUILDERS_COLLECTION).find_one(filters)
        if not item:
            raise PricingFormulaBuilderError("Pricing formula builder metadata not found.")
        return item

    def _normalize_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(data)
        if "airline" in normalized and normalized["airline"] is not None:
            normalized["airline"] = self._normalize_airline(normalized["airline"])
        for field in ["service_family", "pricing_unit", "way", "route_type", "flight_type", "fare_bundle", "pricing_category", "amount_type", "formula_status", "client_visibility"]:
            if field in normalized and normalized[field] is not None:
                normalized[field] = self._normalize_code(normalized[field])
        if "service_codes" in normalized and normalized["service_codes"] is not None:
            normalized["service_codes"] = [self._normalize_service_code(code) for code in normalized.get("service_codes") or []]
        if "currency" in normalized and normalized["currency"] is not None:
            normalized["currency"] = self._normalize_currency(normalized["currency"])
        return normalized

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "formula_status", FORMULA_STATUSES)
        self._validate_choice(data, "pricing_unit", PRICING_UNITS)
        self._validate_choice(data, "way", PRICING_WAY_VALUES)
        self._validate_choice(data, "route_type", PRICING_ROUTE_TYPES)
        self._validate_choice(data, "flight_type", PRICING_FLIGHT_TYPES)
        self._validate_choice(data, "fare_bundle", PRICING_FARE_BUNDLES)
        self._validate_choice(data, "pricing_category", PRICING_CATEGORIES)
        self._validate_choice(data, "amount_type", AMOUNT_TYPES)
        self._validate_choice(data, "client_visibility", CLIENT_VISIBILITY_OPTIONS)
        self._reject_forbidden_metadata(data)
        if not partial:
            for field in ["formula_name", "pricing_category", "amount_type"]:
                if not data.get(field):
                    raise PricingFormulaBuilderError(f"{field} is required.")

    def _validate_choice(self, data: dict[str, Any], field: str, allowed: list[str]) -> None:
        if field not in data or data.get(field) is None:
            return
        if data[field] not in allowed:
            raise PricingFormulaBuilderError(f"Unsupported {field} metadata value: {data[field]}.")

    def _reject_forbidden_metadata(self, data: dict[str, Any]) -> None:
        forbidden = [
            "provider_client",
            "provider_payload",
            "payment_gateway",
            "payment_intent",
            "charge_customer",
            "collect_payment",
            "ai_prompt",
            "llm_prompt",
            "chatcompletion",
            "background_task",
            "backgroundtasks",
            "calculate_live_price",
            "calculate_price(",
            "pricing_formula_executor",
            "execute_formula",
            "quote_live",
            "issue_payment",
            "send_to_client",
        ]
        serialized = str(data).lower()
        for marker in forbidden:
            if marker in serialized:
                raise PricingFormulaBuilderError(f"Forbidden non-metadata implementation marker present: {marker}.")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "pricing_formula_builder_foundation": True,
            "live_price_calculation_disabled": True,
            "payment_integrations_disabled": True,
            "provider_integrations_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_client_sending_disabled": True,
            "human_authority_final": True,
        }

    def _normalize_airline(self, value: Any) -> str:
        return str(value or "").strip().upper()

    def _normalize_code(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("/", "_")

    def _normalize_currency(self, value: Any) -> str:
        return str(value or "").strip().upper()

    def _normalize_service_code(self, value: Any) -> str:
        raw = str(value or "").strip()
        return raw.upper() if len(raw) <= 6 else self._normalize_code(raw)

    def _reference(self, prefix: str) -> str:
        return f"{prefix}-{self._now().replace(':', '').replace('-', '').replace('.', '')}"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _sort_text(self, value: Any) -> str:
        return str(value or "")

    def _counts(self, items: list[dict[str, Any]], field: str, values: list[str]) -> dict[str, int]:
        return {value: len([item for item in items if item.get(field) == value]) for value in values}

    def _any_field_matches(self, item: dict[str, Any], fields: list[str], expected: Any) -> bool:
        if expected in (None, ""):
            return True
        expected_text = str(expected).lower()
        for field in fields:
            value = item.get(field)
            if isinstance(value, list):
                if any(expected_text in str(entry).lower() for entry in value):
                    return True
            elif isinstance(value, dict):
                if expected_text in str(value).lower():
                    return True
            elif value is not None and expected_text in str(value).lower():
                return True
        return False
