from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import OperationalRuleComposerRule, OperationalRuleComposerRuleCreate, OperationalRuleComposerRuleUpdate


PHASE_LABEL = "phase_54_9_end_to_end_operational_workflow_maturity_foundation"
OPERATIONAL_RULE_COMPOSER_RULES_COLLECTION = "operational_rule_composer_rules"

SUPPORTED_OPERATORS = [
    "=",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
    "in",
    "not_in",
    "contains",
    "exists",
    "not_exists",
    "between",
    "between_month_day",
    "date_before",
    "date_after",
    "route_includes_country",
    "route_crosses_border",
    "outside_range",
]
RULE_FAMILIES = [
    "passenger_assistance",
    "pets_animals",
    "medical",
    "documents",
    "seating_baggage",
    "special_items",
    "route_aircraft_cabin",
    "pricing",
    "refund_exchange",
    "after_sales",
]
SEVERITY_LEVELS = ["info", "advisory", "warning", "conditional", "blocking", "manual_review"]
LIFECYCLE_STATUSES = ["draft", "in_review", "approved", "retired", "archived"]


class OperationalRuleComposerError(ValueError):
    pass


class OperationalRuleComposerService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        rules = await self.list_rules(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": rules,
            "rules": rules,
            "summary": await self.summarize_counts(filters.get("agency_id")),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Operational Rule Composer records store compound rule metadata for human review. They do not execute rules, evaluate passenger cases, call providers, generate AI output, or run background workers.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        rules = await self.list_rules(agency_id=agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": rules,
            "rules": rules,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Agency Rule Composer shows metadata-only operational compound rules. Human authority remains final.",
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

    async def list_rules(
        self,
        *,
        agency_id: str | None = None,
        rule_family: str | None = None,
        service_family: str | None = None,
        service_code: str | None = None,
        lifecycle_status: str | None = None,
        severity: str | None = None,
        operator: str | None = None,
        search: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if rule_family:
            filters["rule_family"] = self._normalize_code(rule_family)
        if service_family:
            filters["service_family"] = self._normalize_code(service_family)
        if lifecycle_status:
            filters["lifecycle_status"] = self._normalize_code(lifecycle_status)
        if severity:
            filters["severity"] = self._normalize_code(severity)

        items = await self.db.collection(OPERATIONAL_RULE_COMPOSER_RULES_COLLECTION).find_many(filters or None)
        if service_code:
            code = self._normalize_service_code(service_code)
            items = [item for item in items if code in (item.get("service_codes") or [])]
        if operator:
            normalized_operator = self._normalize_operator(operator)
            items = [
                item
                for item in items
                if normalized_operator
                in self._operators_from_conditions((item.get("conditions") or []) + (item.get("any_conditions") or []))
            ]
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("lifecycle_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(
                item,
                [
                    "rule_reference",
                    "rule_name",
                    "rule_family",
                    "service_family",
                    "service_codes",
                    "applies_to",
                    "conditions",
                    "any_conditions",
                    "result",
                    "severity",
                    "client_message",
                    "internal_message",
                    "evidence_links",
                    "governance_links",
                    "parameter_taxonomy_links",
                    "lifecycle_status",
                    "metadata",
                ],
                search,
            )
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._rule_projection(item) for item in items]

    async def get_rule(self, rule_id: str, agency_id: str | None = None) -> dict[str, Any]:
        item = await self._require_rule(rule_id, agency_id=agency_id)
        return await self._rule_projection(item)

    async def create_rule(
        self,
        payload: OperationalRuleComposerRuleCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data = self._normalize_payload(data)
        data.setdefault("rule_reference", self._reference("ORC"))
        data.setdefault("lifecycle_status", "draft")
        data.setdefault("severity", "advisory")
        data.update(self.safety_flags())
        self._validate_payload(data)
        record = OperationalRuleComposerRule(**data)
        created = await self.db.collection(OPERATIONAL_RULE_COMPOSER_RULES_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "operational_rule_composer_rule": await self._rule_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_rule(
        self,
        rule_id: str,
        payload: OperationalRuleComposerRuleUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_rule(rule_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if agency_id:
            updates.pop("agency_id", None)
        updates = self._normalize_payload(updates)
        updates.update(self.safety_flags())
        self._validate_payload(updates, partial=True)
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(OPERATIONAL_RULE_COMPOSER_RULES_COLLECTION).update_one(filters, updates)
        if not updated:
            raise OperationalRuleComposerError("Operational rule composer metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "operational_rule_composer_rule": await self._rule_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_rule(self, rule_id: str, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_rule(rule_id, agency_id=agency_id)
        updates = {
            "lifecycle_status": "archived",
            "archived": True,
            "archived_at": self._now(),
            **self.safety_flags(),
        }
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(OPERATIONAL_RULE_COMPOSER_RULES_COLLECTION).update_one(filters, updates)
        if not updated:
            raise OperationalRuleComposerError("Operational rule composer metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "operational_rule_composer_rule": await self._rule_projection(updated),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def summarize_counts(self, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        rules = await self.db.collection(OPERATIONAL_RULE_COMPOSER_RULES_COLLECTION).find_many(filters)
        covered_families = {item.get("rule_family") for item in rules if item.get("rule_family") in RULE_FAMILIES}
        condition_count = sum(len(item.get("conditions") or []) for item in rules)
        any_condition_count = sum(len(item.get("any_conditions") or []) for item in rules)
        return {
            "operational_rule_composer_rule_count": len(rules),
            "active_rule_count": len([item for item in rules if not item.get("archived") and item.get("lifecycle_status") != "archived"]),
            "service_code_count": sum(len(item.get("service_codes") or []) for item in rules),
            "condition_count": condition_count,
            "any_condition_count": any_condition_count,
            "total_condition_count": condition_count + any_condition_count,
            "evidence_link_count": sum(len(item.get("evidence_links") or []) for item in rules),
            "governance_link_count": sum(len(item.get("governance_links") or []) for item in rules),
            "parameter_taxonomy_link_count": sum(len(item.get("parameter_taxonomy_links") or []) for item in rules),
            "client_message_count": len([item for item in rules if item.get("client_message")]),
            "internal_message_count": len([item for item in rules if item.get("internal_message")]),
            "by_lifecycle_status": self._counts(rules, "lifecycle_status", LIFECYCLE_STATUSES),
            "by_severity": self._counts(rules, "severity", SEVERITY_LEVELS),
            "by_rule_family": self._counts(rules, "rule_family", RULE_FAMILIES),
            "supported_operator_count": len(SUPPORTED_OPERATORS),
            "supported_rule_family_count": len(RULE_FAMILIES),
            "covered_rule_family_count": len(covered_families),
            "missing_rule_families": [family for family in RULE_FAMILIES if family not in covered_families],
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "rule_family": RULE_FAMILIES,
            "service_family": "service family code",
            "service_code": "SSR, OSI, or internal service code",
            "lifecycle_status": LIFECYCLE_STATUSES,
            "severity": SEVERITY_LEVELS,
            "operator": SUPPORTED_OPERATORS,
            "search": "reference, name, family, service, conditions, result, messages, evidence, governance, taxonomy, or metadata",
            "metadata_only": True,
        }

    async def _rule_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        conditions = projected.get("conditions") or []
        any_conditions = projected.get("any_conditions") or []
        projected["rule_display_name"] = " / ".join(
            part
            for part in [
                projected.get("rule_name") or projected.get("rule_reference"),
                projected.get("rule_family"),
                projected.get("severity"),
            ]
            if part
        )
        projected["overview_section"] = {
            "rule_reference": projected.get("rule_reference"),
            "rule_name": projected.get("rule_name"),
            "rule_family": projected.get("rule_family"),
            "service_family": projected.get("service_family"),
            "service_codes": projected.get("service_codes") or [],
            "severity": projected.get("severity"),
        }
        projected["applicability_section"] = projected.get("applies_to") or {}
        projected["conditions_section"] = {
            "all_conditions": conditions,
            "condition_count": len(conditions),
            "supported_operators": SUPPORTED_OPERATORS,
        }
        projected["any_conditions_section"] = {
            "any_conditions": any_conditions,
            "any_condition_count": len(any_conditions),
            "supported_operators": SUPPORTED_OPERATORS,
        }
        projected["result_section"] = projected.get("result") or {}
        projected["messaging_section"] = {
            "client_message": projected.get("client_message"),
            "internal_message": projected.get("internal_message"),
            "human_authority_final": True,
        }
        projected["evidence_governance_section"] = {
            "evidence_links": projected.get("evidence_links") or [],
            "governance_links": projected.get("governance_links") or [],
            "parameter_taxonomy_links": projected.get("parameter_taxonomy_links") or [],
        }
        projected["lifecycle_section"] = {
            "effective_from": projected.get("effective_from"),
            "effective_to": projected.get("effective_to"),
            "lifecycle_status": projected.get("lifecycle_status"),
            "archived": projected.get("archived"),
            "archived_at": projected.get("archived_at"),
        }
        projected["no_code_sections"] = {
            "overview": projected["overview_section"],
            "applicability": projected["applicability_section"],
            "conditions": projected["conditions_section"],
            "any_conditions": projected["any_conditions_section"],
            "result": projected["result_section"],
            "messaging": projected["messaging_section"],
            "evidence_governance": projected["evidence_governance_section"],
            "lifecycle": projected["lifecycle_section"],
        }
        projected["boundary_section"] = self.safety_flags()
        projected.update(self.safety_flags())
        return projected

    async def _require_rule(self, rule_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": rule_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(OPERATIONAL_RULE_COMPOSER_RULES_COLLECTION).find_one(filters)
        if not item:
            raise OperationalRuleComposerError("Operational rule composer metadata not found.")
        return item

    def _normalize_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(data)
        for field in ["rule_family", "service_family", "lifecycle_status", "severity"]:
            if field in normalized and normalized[field] is not None:
                normalized[field] = self._normalize_code(normalized[field])
        if "service_codes" in normalized and normalized["service_codes"] is not None:
            normalized["service_codes"] = [self._normalize_service_code(code) for code in normalized.get("service_codes") or []]
        if "conditions" in normalized and normalized["conditions"] is not None:
            normalized["conditions"] = self._normalize_conditions(normalized.get("conditions") or [])
        if "any_conditions" in normalized and normalized["any_conditions"] is not None:
            normalized["any_conditions"] = self._normalize_conditions(normalized.get("any_conditions") or [])
        return normalized

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "rule_family", RULE_FAMILIES)
        self._validate_choice(data, "lifecycle_status", LIFECYCLE_STATUSES)
        self._validate_choice(data, "severity", SEVERITY_LEVELS)
        self._validate_conditions(data.get("conditions") or [])
        self._validate_conditions(data.get("any_conditions") or [])
        self._reject_forbidden_metadata(data)
        if not partial:
            for field in ["rule_name", "rule_family"]:
                if not data.get(field):
                    raise OperationalRuleComposerError(f"{field} is required.")

    def _validate_choice(self, data: dict[str, Any], field: str, allowed: list[str]) -> None:
        if field not in data or data.get(field) is None:
            return
        if data[field] not in allowed:
            raise OperationalRuleComposerError(f"Unsupported {field} metadata value: {data[field]}.")

    def _validate_conditions(self, conditions: list[dict[str, Any]]) -> None:
        for operator in self._operators_from_conditions(conditions):
            if operator not in SUPPORTED_OPERATORS:
                raise OperationalRuleComposerError(f"Unsupported condition operator metadata value: {operator}.")

    def _normalize_conditions(self, conditions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized_conditions = []
        for condition in conditions:
            if not isinstance(condition, dict):
                normalized_conditions.append(condition)
                continue
            normalized = dict(condition)
            if "operator" in normalized:
                normalized["operator"] = self._normalize_operator(normalized.get("operator"))
            normalized_conditions.append(normalized)
        return normalized_conditions

    def _operators_from_conditions(self, conditions: list[Any]) -> list[str]:
        operators: list[str] = []
        for condition in conditions:
            if isinstance(condition, dict):
                if condition.get("operator") is not None:
                    operators.append(str(condition.get("operator")))
                nested = condition.get("conditions") or condition.get("any_conditions")
                if isinstance(nested, list):
                    operators.extend(self._operators_from_conditions(nested))
        return operators

    def _reject_forbidden_metadata(self, data: dict[str, Any]) -> None:
        forbidden = [
            "provider_client",
            "provider_payload",
            "ai_prompt",
            "llm_prompt",
            "chatcompletion",
            "background_task",
            "backgroundtasks",
            "execute_rule",
            "evaluate_rule",
            "rule_engine_executor",
            "live_rule_evaluation_enabled",
            "automatic_decision_enabled",
            "calculate_price(",
        ]
        serialized = str(data).lower()
        for marker in forbidden:
            if marker in serialized:
                raise OperationalRuleComposerError(f"Forbidden non-metadata implementation marker present: {marker}.")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "operational_rule_composer_foundation": True,
            "rule_execution_disabled": True,
            "live_rule_evaluation_disabled": True,
            "provider_integrations_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_decisioning_disabled": True,
            "human_authority_final": True,
        }

    def _normalize_code(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("/", "_")

    def _normalize_operator(self, value: Any) -> str:
        raw = str(value or "").strip()
        aliases = {
            "==": "=",
            "not in": "not_in",
            "not-in": "not_in",
            "not exists": "not_exists",
            "not-exists": "not_exists",
        }
        return aliases.get(raw.lower(), raw if raw in {"=", "!=", ">", ">=", "<", "<="} else self._normalize_code(raw))

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
