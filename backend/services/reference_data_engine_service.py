from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import ReferenceDataDomain, ReferenceDataDomainCreate, ReferenceDataDomainUpdate


PHASE_LABEL = "phase_54_4_task_automation_dependency_orchestration_foundation"
REFERENCE_DATA_DOMAINS_COLLECTION = "reference_data_domains"

SUPPORTED_REFERENCE_DOMAIN_CODES = [
    "airlines",
    "airports",
    "countries",
    "cities",
    "currencies",
    "aircraft_types",
    "aircraft_families",
    "cabin_classes",
    "seat_types",
    "passenger_types",
    "service_codes",
    "service_families",
    "ssr_codes",
    "osi_templates",
    "rfic_rfisc",
    "pet_species",
    "pet_breeds",
    "breed_risk_flags",
    "container_types",
    "document_types",
    "vaccination_types",
    "mobility_levels",
    "wheelchair_device_types",
    "battery_types",
    "medical_equipment_types",
    "route_types",
    "flight_types",
    "fare_bundles",
    "pricing_units",
    "pricing_categories",
    "formula_components",
    "temperature_zones",
    "seasonal_restriction_types",
    "travel_purposes",
]

GOVERNANCE_STATUSES = ["draft", "in_review", "approved", "retired", "archived"]
REVIEW_STATUSES = ["needs_review", "approved", "rejected", "changes_requested", "not_required"]


class ReferenceDataEngineError(ValueError):
    pass


class ReferenceDataEngineService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        domains = await self.list_domains(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": domains,
            "domains": domains,
            "summary": await self.summarize_counts(filters.get("agency_id")),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Reference Data Engine domains store metadata used for airline operational knowledge production. They do not call providers, generate AI, evaluate live rules, calculate pricing, run workers, or expose old /admin routes.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        domains = await self.list_domains(agency_id=agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": domains,
            "domains": domains,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Agency Reference Data shows metadata-only domain records for review and airline knowledge production. Human authority remains final.",
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

    async def list_domains(
        self,
        *,
        agency_id: str | None = None,
        domain_code: str | None = None,
        governance_status: str | None = None,
        review_status: str | None = None,
        active: bool | None = None,
        search: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if domain_code:
            filters["domain_code"] = domain_code
        if governance_status:
            filters["governance_status"] = governance_status
        if review_status:
            filters["review_status"] = review_status
        if active is not None:
            filters["active"] = active

        items = await self.db.collection(REFERENCE_DATA_DOMAINS_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("governance_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(
                item,
                [
                    "domain_reference",
                    "domain_code",
                    "domain_label",
                    "domain_description",
                    "records",
                    "aliases",
                    "normalization_rules",
                    "validation_rules",
                    "metadata",
                ],
                search,
            )
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._domain_projection(item) for item in items]

    async def get_domain(self, domain_id: str, agency_id: str | None = None) -> dict[str, Any]:
        item = await self._require_domain(domain_id, agency_id=agency_id)
        return await self._domain_projection(item)

    async def create_domain(
        self,
        payload: ReferenceDataDomainCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        domain_code = self._normalize_code(data.get("domain_code"))
        data["domain_code"] = domain_code
        data.setdefault("domain_reference", self._reference("RDE"))
        data.setdefault("domain_label", self._label_from_code(domain_code))
        data.setdefault("governance_status", "draft")
        data.setdefault("review_status", "needs_review")
        data.setdefault("active", True)
        data.update(self.safety_flags())
        self._validate_payload(data)
        record = ReferenceDataDomain(**data)
        created = await self.db.collection(REFERENCE_DATA_DOMAINS_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "reference_data_domain": await self._domain_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_domain(
        self,
        domain_id: str,
        payload: ReferenceDataDomainUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_domain(domain_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if agency_id:
            updates.pop("agency_id", None)
        if "domain_code" in updates:
            updates["domain_code"] = self._normalize_code(updates["domain_code"])
            updates.setdefault("domain_label", self._label_from_code(updates["domain_code"]))
        updates.update(self.safety_flags())
        self._validate_payload(updates, partial=True)
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(REFERENCE_DATA_DOMAINS_COLLECTION).update_one(filters, updates)
        if not updated:
            raise ReferenceDataEngineError("Reference data domain metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "reference_data_domain": await self._domain_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_domain(self, domain_id: str, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_domain(domain_id, agency_id=agency_id)
        updates = {
            "governance_status": "archived",
            "review_status": "not_required",
            "active": False,
            "archived": True,
            "archived_at": self._now(),
            **self.safety_flags(),
        }
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(REFERENCE_DATA_DOMAINS_COLLECTION).update_one(filters, updates)
        if not updated:
            raise ReferenceDataEngineError("Reference data domain metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "reference_data_domain": await self._domain_projection(updated),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def summarize_counts(self, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        domains = await self.db.collection(REFERENCE_DATA_DOMAINS_COLLECTION).find_many(filters)
        covered_domain_codes = {item.get("domain_code") for item in domains if item.get("domain_code") in SUPPORTED_REFERENCE_DOMAIN_CODES}
        return {
            "reference_data_domain_count": len(domains),
            "active_domain_count": len([item for item in domains if item.get("active", True) and not item.get("archived")]),
            "record_count": sum(len(item.get("records") or []) for item in domains),
            "alias_count": sum(len(item.get("aliases") or []) for item in domains),
            "normalization_rule_count": sum(len(item.get("normalization_rules") or []) for item in domains),
            "validation_rule_count": sum(len(item.get("validation_rules") or []) for item in domains),
            "by_governance_status": self._counts(domains, "governance_status", GOVERNANCE_STATUSES),
            "by_review_status": self._counts(domains, "review_status", REVIEW_STATUSES),
            "supported_domain_count": len(SUPPORTED_REFERENCE_DOMAIN_CODES),
            "supported_domain_coverage_count": len(covered_domain_codes),
            "missing_supported_domain_codes": [
                domain_code for domain_code in SUPPORTED_REFERENCE_DOMAIN_CODES if domain_code not in covered_domain_codes
            ],
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "domain_code": SUPPORTED_REFERENCE_DOMAIN_CODES,
            "governance_status": GOVERNANCE_STATUSES,
            "review_status": REVIEW_STATUSES,
            "active": "true or false",
            "search": "reference, domain, record, alias, rule, or metadata match",
            "metadata_only": True,
        }

    async def _domain_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        records = projected.get("records") or []
        aliases = projected.get("aliases") or []
        normalization_rules = projected.get("normalization_rules") or []
        validation_rules = projected.get("validation_rules") or []
        projected["domain_display_name"] = projected.get("domain_label") or self._label_from_code(projected.get("domain_code"))
        projected["domain_summary"] = {
            "domain_reference": projected.get("domain_reference"),
            "domain_code": projected.get("domain_code"),
            "domain_label": projected.get("domain_label"),
            "domain_description": projected.get("domain_description"),
            "record_count": len(records),
            "alias_count": len(aliases),
            "normalization_rule_count": len(normalization_rules),
            "validation_rule_count": len(validation_rules),
        }
        projected["records_section"] = {
            "records": records,
            "record_count": len(records),
            "aliases": aliases,
            "alias_count": len(aliases),
        }
        projected["normalization_section"] = {
            "aliases": aliases,
            "normalization_rules": normalization_rules,
            "normalization_rule_count": len(normalization_rules),
        }
        projected["validation_section"] = {
            "validation_rules": validation_rules,
            "validation_rule_count": len(validation_rules),
        }
        projected["governance_section"] = {
            "governance_status": projected.get("governance_status"),
            "review_status": projected.get("review_status"),
            "active": projected.get("active"),
            "import_template_reference": projected.get("import_template_reference"),
            "archived": projected.get("archived"),
        }
        projected["production_readiness_section"] = {
            "supported_domain": projected.get("domain_code") in SUPPORTED_REFERENCE_DOMAIN_CODES,
            "airline_operational_knowledge_production_ready": True,
            "records_present": bool(records),
            "normalization_metadata_present": bool(aliases or normalization_rules),
            "validation_metadata_present": bool(validation_rules),
            "human_authority_final": True,
        }
        projected["boundary_section"] = self.safety_flags()
        projected.update(self.safety_flags())
        return projected

    async def _require_domain(self, domain_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": domain_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(REFERENCE_DATA_DOMAINS_COLLECTION).find_one(filters)
        if not item:
            raise ReferenceDataEngineError("Reference data domain metadata not found.")
        return item

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "domain_code", SUPPORTED_REFERENCE_DOMAIN_CODES)
        self._validate_choice(data, "governance_status", GOVERNANCE_STATUSES)
        self._validate_choice(data, "review_status", REVIEW_STATUSES)
        self._reject_forbidden_metadata(data)
        if not partial and not data.get("domain_code"):
            raise ReferenceDataEngineError("domain_code is required.")

    def _validate_choice(self, data: dict[str, Any], field: str, allowed: list[str]) -> None:
        if field not in data or data.get(field) is None:
            return
        if data[field] not in allowed:
            raise ReferenceDataEngineError(f"Unsupported {field} metadata value: {data[field]}.")

    def _reject_forbidden_metadata(self, data: dict[str, Any]) -> None:
        forbidden = [
            "provider_client",
            "provider_payload",
            "ai_prompt",
            "llm_prompt",
            "chatcompletion",
            "background_task",
            "backgroundtasks",
            "calculate_price(",
            "pricing_formula_executor",
            "live_rule_evaluation",
            "/admin",
            "/api/" + "admin",
        ]
        serialized = str(data).lower()
        for marker in forbidden:
            if marker in serialized:
                raise ReferenceDataEngineError(f"Forbidden non-metadata implementation marker present: {marker}.")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "reference_data_engine_foundation": True,
            "airline_operational_knowledge_production_ready": True,
            "provider_integrations_disabled": True,
            "ai_disabled": True,
            "live_evaluation_disabled": True,
            "pricing_calculation_disabled": True,
            "background_workers_disabled": True,
            "old_admin_routes_disabled": True,
            "human_authority_final": True,
        }

    def _normalize_code(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("/", "_")

    def _label_from_code(self, value: Any) -> str:
        return " ".join(part.upper() if part in {"ssr", "osi", "rfic", "rfisc"} else part.capitalize() for part in str(value or "").split("_"))

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
