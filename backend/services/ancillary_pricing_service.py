from __future__ import annotations

import re
from typing import Any

from database import Database
from models import (
    AirlineAncillaryPriceComponent,
    AirlineAncillaryPricingApplicability,
    AirlineAncillaryPricingMatrix,
    AirlineAncillaryPricingMatrixRow,
    AirlineAncillaryPricingRule,
    AirlineServiceExceptionOutcome,
    AirlineServiceExceptionRule,
    AirlineServicePriceQuoteEvaluationStatus,
    AirlineServicePriceQuoteResult,
    AirlineServicePriceQuoteScenario,
    AncillaryAmountType,
    AncillaryApplicabilityAppliesAs,
    AncillaryApplicabilityOperator,
    AncillaryAppliesPer,
    AncillaryPricingScope,
    AncillaryPricingStatus,
    PolicyCandidatePricingLink,
    ServiceMechanicsSeverity,
)


PHASE_LABEL = "phase_37_0_ancillary_pricing_exception_foundation"

PRICING_RULE_COLLECTION = "airline_ancillary_pricing_rules"
PRICE_COMPONENT_COLLECTION = "airline_ancillary_price_components"
APPLICABILITY_COLLECTION = "airline_ancillary_pricing_applicability"
PRICING_MATRIX_COLLECTION = "airline_ancillary_pricing_matrices"
PRICING_MATRIX_ROW_COLLECTION = "airline_ancillary_pricing_matrix_rows"
EXCEPTION_RULE_COLLECTION = "airline_service_exception_rules"
QUOTE_SCENARIO_COLLECTION = "airline_service_price_quote_scenarios"
QUOTE_RESULT_COLLECTION = "airline_service_price_quote_results"
CANDIDATE_PRICING_LINK_COLLECTION = "policy_candidate_pricing_links"

RESOURCE_SPECS: dict[str, dict[str, Any]] = {
    "pricing_rules": {"collection": PRICING_RULE_COLLECTION, "model": AirlineAncillaryPricingRule, "singular": "pricing_rule", "archive_field": "pricing_status"},
    "price_components": {"collection": PRICE_COMPONENT_COLLECTION, "model": AirlineAncillaryPriceComponent, "singular": "price_component", "archive_field": "status"},
    "applicability": {"collection": APPLICABILITY_COLLECTION, "model": AirlineAncillaryPricingApplicability, "singular": "applicability", "archive_field": "status"},
    "pricing_matrices": {"collection": PRICING_MATRIX_COLLECTION, "model": AirlineAncillaryPricingMatrix, "singular": "pricing_matrix", "archive_field": "status"},
    "pricing_matrix_rows": {"collection": PRICING_MATRIX_ROW_COLLECTION, "model": AirlineAncillaryPricingMatrixRow, "singular": "pricing_matrix_row", "archive_field": "status"},
    "exception_rules": {"collection": EXCEPTION_RULE_COLLECTION, "model": AirlineServiceExceptionRule, "singular": "exception_rule", "archive_field": "status"},
    "quote_scenarios": {"collection": QUOTE_SCENARIO_COLLECTION, "model": AirlineServicePriceQuoteScenario, "singular": "quote_scenario"},
    "quote_results": {"collection": QUOTE_RESULT_COLLECTION, "model": AirlineServicePriceQuoteResult, "singular": "quote_result"},
    "candidate_pricing_links": {"collection": CANDIDATE_PRICING_LINK_COLLECTION, "model": PolicyCandidatePricingLink, "singular": "link"},
}

PRICING_RESOURCES = [
    "pricing_rules",
    "price_components",
    "applicability",
    "pricing_matrices",
    "pricing_matrix_rows",
]

EXCEPTION_RESOURCES = ["exception_rules"]


def normalize_taxonomy_code(value: Any) -> str | None:
    text = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return text or None


def normalize_airline_code(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    return text or None


def normalize_currency(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    return text or None


def enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_unset=True)
    return dict(payload or {})


def clean_updates(payload: Any) -> dict[str, Any]:
    return {key: value for key, value in payload_dict(payload).items() if value is not None}


def visible_scoped(item: dict[str, Any], agency_id: str | None) -> bool:
    if item.get("is_global", item.get("agency_id") is None):
        return True
    return bool(agency_id and item.get("agency_id") == agency_id)


def active_status(item: dict[str, Any]) -> bool:
    status = item.get("pricing_status", item.get("status", AncillaryPricingStatus.ACTIVE.value))
    return status == AncillaryPricingStatus.ACTIVE.value


def resource_spec(resource: str) -> dict[str, Any]:
    if resource not in RESOURCE_SPECS:
        raise ValueError(f"Unknown ancillary pricing resource: {resource}")
    return RESOURCE_SPECS[resource]


class AncillaryPricingService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "pricing_rule_count": len(await self.list_records("pricing_rules", agency_id=agency_id)),
            "price_component_count": len(await self.list_records("price_components", agency_id=agency_id)),
            "pricing_applicability_count": len(await self.list_records("applicability", agency_id=agency_id)),
            "pricing_matrix_count": len(await self.list_records("pricing_matrices", agency_id=agency_id)),
            "pricing_matrix_row_count": len(await self.list_records("pricing_matrix_rows", agency_id=agency_id)),
            "service_exception_rule_count": len(await self.list_records("exception_rules", agency_id=agency_id)),
            "quote_scenario_count": len(await self.list_records("quote_scenarios", agency_id=agency_id)),
            "quote_result_count": len(await self.list_records("quote_results", agency_id=agency_id)),
            "candidate_pricing_link_count": len(await self.list_records("candidate_pricing_links", agency_id=agency_id)),
            "deterministic_quote_evaluation_enabled": True,
            "exception_engine_expansion_enabled": True,
            "pricing_mechanics_reference_enabled": True,
            "invoice_payment_settlement_disabled": True,
            "emd_issuance_disabled": True,
            "provider_execution_disabled": True,
            "agency_auto_promotion_disabled": True,
            "diagnostic": "Ancillary pricing estimates and exception rules are metadata-only; no invoices, payments, settlement, EMD issuance, or provider execution are performed.",
        }

    async def list_records(
        self,
        resource: str,
        *,
        agency_id: str | None = None,
        airline_code: str | None = None,
        domain_code: str | None = None,
        family_code: str | None = None,
        variant_code: str | None = None,
        pricing_rule_id: str | None = None,
        matrix_id: str | None = None,
        scenario_id: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        spec = resource_spec(resource)
        items = await self.db.collection(spec["collection"]).find_many()
        airline_code = normalize_airline_code(airline_code)
        domain_code = normalize_taxonomy_code(domain_code)
        family_code = normalize_taxonomy_code(family_code)
        variant_code = normalize_taxonomy_code(variant_code)

        if resource == "quote_results" and agency_id:
            visible_scenarios = await self.list_records("quote_scenarios", agency_id=agency_id)
            visible_scenario_ids = {item["id"] for item in visible_scenarios}
            items = [item for item in items if item.get("scenario_id") in visible_scenario_ids]
        else:
            items = [item for item in items if self._visible_for_resource(resource, item, agency_id)]
        if airline_code:
            items = [item for item in items if item.get("airline_code") in {None, airline_code}]
        if domain_code:
            items = [item for item in items if item.get("domain_code") in {None, domain_code}]
        if family_code:
            items = [item for item in items if item.get("family_code") in {None, family_code}]
        if variant_code:
            items = [item for item in items if item.get("variant_code") in {None, variant_code}]
        if pricing_rule_id:
            items = [item for item in items if item.get("pricing_rule_id") == pricing_rule_id]
        if matrix_id:
            items = [item for item in items if item.get("matrix_id") == matrix_id]
        if scenario_id:
            items = [item for item in items if item.get("scenario_id") == scenario_id]
        if not include_archived:
            items = [
                item
                for item in items
                if item.get("pricing_status", item.get("status")) != AncillaryPricingStatus.ARCHIVED.value
            ]
        return sorted(items, key=lambda item: (item.get("sort_order", item.get("sequence", 100)), str(item.get("created_at") or "")), reverse=False)

    async def create_record(self, resource: str, payload: Any, user: dict | None = None, agency_id: str | None = None) -> dict[str, Any]:
        spec = resource_spec(resource)
        data = self._normalize_payload(payload_dict(payload), resource)
        if agency_id:
            data["agency_id"] = agency_id
            if "is_global" in spec["model"].model_fields:
                data["is_global"] = False
            if resource == "pricing_matrices":
                data["scope"] = AncillaryPricingScope.AGENCY.value
        record = spec["model"](**data)
        return await self.db.collection(spec["collection"]).insert_one(record.model_dump(mode="json"))

    async def update_record(self, resource: str, record_id: str, payload: Any, agency_id: str | None = None) -> dict[str, Any] | None:
        spec = resource_spec(resource)
        existing = await self.db.collection(spec["collection"]).find_one({"id": record_id})
        if not existing:
            return None
        if agency_id and existing.get("agency_id") != agency_id:
            return None
        updates = self._normalize_payload(clean_updates(payload), resource)
        return await self.db.collection(spec["collection"]).update_one({"id": record_id}, updates)

    async def archive_record(self, resource: str, record_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        archive_field = resource_spec(resource).get("archive_field", "status")
        return await self.update_record(resource, record_id, {archive_field: AncillaryPricingStatus.ARCHIVED.value}, agency_id=agency_id)

    async def lookup(
        self,
        *,
        airline_code: str,
        domain_code: str,
        family_code: str,
        variant_code: str | None = None,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        airline_code = normalize_airline_code(airline_code) or ""
        domain_code = normalize_taxonomy_code(domain_code) or ""
        family_code = normalize_taxonomy_code(family_code) or ""
        variant_code = normalize_taxonomy_code(variant_code)
        pricing_rules = await self._matching_pricing_rules(airline_code, domain_code, family_code, variant_code, agency_id)
        rule_ids = {item["id"] for item in pricing_rules}
        components = [
            item
            for item in await self.list_records("price_components", agency_id=agency_id)
            if item.get("pricing_rule_id") in rule_ids and active_status(item)
        ]
        applicability = [
            item
            for item in await self.list_records("applicability", agency_id=agency_id)
            if item.get("pricing_rule_id") in rule_ids and active_status(item)
        ]
        matrices = await self._matching_records("pricing_matrices", airline_code, domain_code, family_code, variant_code, agency_id)
        matrix_ids = {item["id"] for item in matrices}
        matrix_rows = [
            item
            for item in await self.list_records("pricing_matrix_rows", agency_id=agency_id)
            if item.get("matrix_id") in matrix_ids and active_status(item)
        ]
        exceptions = await self._matching_exception_rules(airline_code, domain_code, family_code, variant_code, agency_id)
        warnings = []
        if not pricing_rules:
            warnings.append("No active ancillary pricing rule matched this airline and canonical service.")
        if not exceptions:
            warnings.append("No active exception rule matched this airline and canonical service.")
        return {
            "input": {
                "airline_code": airline_code,
                "domain_code": domain_code,
                "family_code": family_code,
                "variant_code": variant_code,
            },
            "pricing": {
                "pricing_rules": pricing_rules,
                "price_components": components,
                "applicability": applicability,
                "pricing_matrices": matrices,
                "pricing_matrix_rows": matrix_rows,
            },
            "exceptions": {
                "exception_rules": exceptions,
            },
            "warnings": warnings,
            "deterministic_quote_evaluation_enabled": True,
            "invoice_payment_settlement_disabled": True,
            "emd_issuance_disabled": True,
            "provider_execution_disabled": True,
            "agency_auto_promotion_disabled": True,
        }

    async def evaluate(self, payload: Any, user: dict | None = None, agency_id: str | None = None) -> dict[str, Any]:
        data = self._normalize_payload(payload_dict(payload), "quote_scenarios")
        scenario = await self._resolve_scenario(data, agency_id)
        airline_code = normalize_airline_code(scenario.get("airline_code")) or ""
        domain_code = normalize_taxonomy_code(scenario.get("domain_code")) or ""
        family_code = normalize_taxonomy_code(scenario.get("family_code")) or ""
        variant_code = normalize_taxonomy_code(scenario.get("variant_code"))
        pricing_rules = await self._matching_pricing_rules(airline_code, domain_code, family_code, variant_code, agency_id)
        exceptions = await self._applicable_exceptions(airline_code, domain_code, family_code, variant_code, scenario, agency_id)

        warnings: list[str] = []
        breakdown: list[dict[str, Any]] = []
        status = AirlineServicePriceQuoteEvaluationStatus.PRICED.value
        estimated_amount = 0.0
        currency = normalize_currency(scenario.get("currency"))
        matched_rule_ids: list[str] = []

        blocker_exceptions = [
            item
            for item in exceptions
            if item.get("severity") == ServiceMechanicsSeverity.BLOCKER.value
            or item.get("outcome") == AirlineServiceExceptionOutcome.NOT_PERMITTED.value
        ]
        if blocker_exceptions:
            status = AirlineServicePriceQuoteEvaluationStatus.BLOCKED.value
            warnings.append("A blocker exception applies to this pricing scenario.")

        if not pricing_rules and status != AirlineServicePriceQuoteEvaluationStatus.BLOCKED.value:
            status = AirlineServicePriceQuoteEvaluationStatus.NO_PRICE_FOUND.value
            warnings.append("No active pricing rule matched this airline and canonical service.")

        for rule in pricing_rules:
            applicability = [
                item
                for item in await self.list_records("applicability", agency_id=agency_id, pricing_rule_id=rule["id"])
                if active_status(item)
            ]
            applicability_state = self._applicability_state(applicability, scenario)
            warnings.extend(applicability_state["warnings"])
            if applicability_state["excluded"]:
                continue
            if applicability_state["manual_review"] and status == AirlineServicePriceQuoteEvaluationStatus.PRICED.value:
                status = AirlineServicePriceQuoteEvaluationStatus.MANUAL_REVIEW.value
            matched_rule_ids.append(rule["id"])
            components = [
                item
                for item in await self.list_records("price_components", agency_id=agency_id, pricing_rule_id=rule["id"])
                if active_status(item)
            ]
            for component in components:
                component_result = self._evaluate_component(component, scenario)
                breakdown.append({"pricing_rule_id": rule["id"], **component_result})
                warnings.extend(component_result["warnings"])
                if component_result["manual_review"] and status == AirlineServicePriceQuoteEvaluationStatus.PRICED.value:
                    status = AirlineServicePriceQuoteEvaluationStatus.MANUAL_REVIEW.value
                if component_result["amount"] is not None:
                    estimated_amount += component_result["amount"]
                component_currency = normalize_currency(component.get("currency"))
                if component_currency:
                    if currency and currency != component_currency:
                        warnings.append("Multiple currencies matched this scenario; manual review is required.")
                        if status == AirlineServicePriceQuoteEvaluationStatus.PRICED.value:
                            status = AirlineServicePriceQuoteEvaluationStatus.MANUAL_REVIEW.value
                    currency = currency or component_currency

        if status == AirlineServicePriceQuoteEvaluationStatus.PRICED.value and not matched_rule_ids:
            status = AirlineServicePriceQuoteEvaluationStatus.NO_PRICE_FOUND.value
            warnings.append("Pricing rules existed but none passed applicability filters.")

        if status == AirlineServicePriceQuoteEvaluationStatus.BLOCKED.value:
            estimated_value: float | None = None
        elif matched_rule_ids and estimated_amount:
            estimated_value = round(estimated_amount, 2)
        else:
            estimated_value = None

        result = AirlineServicePriceQuoteResult(
            scenario_id=scenario["id"],
            pricing_rule_ids=matched_rule_ids,
            exception_rule_ids=[item["id"] for item in exceptions],
            estimated_amount=estimated_value,
            currency=currency,
            amount_breakdown_json=breakdown,
            evaluation_status=status,
            warnings=warnings,
            explanation=self._quote_explanation(status, matched_rule_ids, exceptions, estimated_value, currency),
        )
        stored_result = await self.db.collection(QUOTE_RESULT_COLLECTION).insert_one(result.model_dump(mode="json"))
        return {
            "scenario": scenario,
            "result": stored_result,
            "pricing": {
                "pricing_rules": [item for item in pricing_rules if item["id"] in matched_rule_ids],
                "amount_breakdown": breakdown,
            },
            "exceptions": {
                "exception_rules": exceptions,
            },
            "invoice_payment_settlement_disabled": True,
            "emd_issuance_disabled": True,
            "provider_execution_disabled": True,
            "agency_auto_promotion_disabled": True,
        }

    async def _resolve_scenario(self, data: dict[str, Any], agency_id: str | None) -> dict[str, Any]:
        scenario_id = data.get("scenario_id")
        if scenario_id:
            existing = await self.db.collection(QUOTE_SCENARIO_COLLECTION).find_one({"id": scenario_id})
            if existing and self._visible_for_resource("quote_scenarios", existing, agency_id):
                return existing
        create_data = {key: value for key, value in data.items() if key not in {"scenario_id", "store_result"}}
        if agency_id:
            create_data["agency_id"] = agency_id
        scenario = AirlineServicePriceQuoteScenario(**create_data)
        return await self.db.collection(QUOTE_SCENARIO_COLLECTION).insert_one(scenario.model_dump(mode="json"))

    async def _matching_pricing_rules(
        self,
        airline_code: str,
        domain_code: str,
        family_code: str,
        variant_code: str | None,
        agency_id: str | None,
    ) -> list[dict[str, Any]]:
        return await self._matching_records("pricing_rules", airline_code, domain_code, family_code, variant_code, agency_id, status_field="pricing_status")

    async def _matching_exception_rules(
        self,
        airline_code: str,
        domain_code: str,
        family_code: str,
        variant_code: str | None,
        agency_id: str | None,
    ) -> list[dict[str, Any]]:
        return await self._matching_records("exception_rules", airline_code, domain_code, family_code, variant_code, agency_id)

    async def _matching_records(
        self,
        resource: str,
        airline_code: str,
        domain_code: str,
        family_code: str,
        variant_code: str | None,
        agency_id: str | None,
        *,
        status_field: str = "status",
    ) -> list[dict[str, Any]]:
        items = await self.list_records(
            resource,
            agency_id=agency_id,
            airline_code=airline_code,
            domain_code=domain_code,
            family_code=family_code,
            include_archived=False,
        )
        return [
            item
            for item in items
            if (not item.get("variant_code") or item.get("variant_code") == variant_code)
            and item.get(status_field, AncillaryPricingStatus.ACTIVE.value) == AncillaryPricingStatus.ACTIVE.value
        ]

    async def _applicable_exceptions(
        self,
        airline_code: str,
        domain_code: str,
        family_code: str,
        variant_code: str | None,
        scenario: dict[str, Any],
        agency_id: str | None,
    ) -> list[dict[str, Any]]:
        exceptions = await self._matching_exception_rules(airline_code, domain_code, family_code, variant_code, agency_id)
        return [item for item in exceptions if self._condition_matches(item.get("condition_json") or {}, scenario)]

    def _applicability_state(self, applicability: list[dict[str, Any]], scenario: dict[str, Any]) -> dict[str, Any]:
        warnings: list[str] = []
        excluded = False
        manual_review = False
        for item in applicability:
            matches = self._operator_matches(item.get("operator"), scenario.get(item.get("dimension_code")), item.get("value"), item.get("value_json") or {})
            applies_as = item.get("applies_as")
            if applies_as == AncillaryApplicabilityAppliesAs.CONDITION.value and not matches:
                excluded = True
            elif applies_as == AncillaryApplicabilityAppliesAs.EXCLUSION.value and matches:
                excluded = True
                warnings.append(f"Pricing rule excluded by {item.get('dimension_code')} applicability.")
            elif applies_as == AncillaryApplicabilityAppliesAs.MANUAL_REVIEW.value and matches:
                manual_review = True
                warnings.append(f"{item.get('dimension_code')} requires manual review.")
            elif applies_as in {AncillaryApplicabilityAppliesAs.SURCHARGE.value, AncillaryApplicabilityAppliesAs.DISCOUNT.value} and matches:
                manual_review = True
                warnings.append(f"{item.get('dimension_code')} may change price; manual review is required.")
        return {"excluded": excluded, "manual_review": manual_review, "warnings": warnings}

    def _operator_matches(self, operator: Any, actual: Any, value: Any, value_json: dict[str, Any]) -> bool:
        operator = enum_value(operator) or AncillaryApplicabilityOperator.ANY.value
        values = value_json.get("values")
        if values is None and value_json:
            values = list(value_json.values())
        expected = value if value not in {None, ""} else value_json.get("value")
        if operator == AncillaryApplicabilityOperator.ANY.value:
            return True
        if operator == AncillaryApplicabilityOperator.EXISTS.value:
            return actual not in {None, ""}
        if operator == AncillaryApplicabilityOperator.NOT_EXISTS.value:
            return actual in {None, ""}
        if operator == AncillaryApplicabilityOperator.EQUALS.value:
            return self._text(actual) == self._text(expected)
        if operator == AncillaryApplicabilityOperator.NOT_EQUALS.value:
            return self._text(actual) != self._text(expected)
        if operator == AncillaryApplicabilityOperator.IN.value:
            return self._text(actual) in {self._text(item) for item in values or []}
        if operator == AncillaryApplicabilityOperator.NOT_IN.value:
            return self._text(actual) not in {self._text(item) for item in values or []}
        if operator == AncillaryApplicabilityOperator.CONTAINS.value:
            return self._text(expected) in self._text(actual)
        if operator in {
            AncillaryApplicabilityOperator.MIN.value,
            AncillaryApplicabilityOperator.MAX.value,
            AncillaryApplicabilityOperator.BETWEEN.value,
        }:
            try:
                number = float(actual)
            except (TypeError, ValueError):
                return False
            if operator == AncillaryApplicabilityOperator.MIN.value:
                return number >= float(expected)
            if operator == AncillaryApplicabilityOperator.MAX.value:
                return number <= float(expected)
            lower = value_json.get("min", values[0] if values else None)
            upper = value_json.get("max", values[1] if values and len(values) > 1 else None)
            if lower is None or upper is None:
                return False
            return float(lower) <= number <= float(upper)
        return False

    def _condition_matches(self, condition_json: dict[str, Any], scenario: dict[str, Any]) -> bool:
        if not condition_json:
            return True
        for key, expected in condition_json.items():
            if isinstance(expected, dict):
                if not self._operator_matches(expected.get("operator"), scenario.get(key), expected.get("value"), expected):
                    return False
            elif isinstance(expected, list):
                if self._text(scenario.get(key)) not in {self._text(item) for item in expected}:
                    return False
            elif self._text(scenario.get(key)) != self._text(expected):
                return False
        return True

    def _evaluate_component(self, component: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
        warnings: list[str] = []
        amount_type = component.get("amount_type")
        if amount_type == AncillaryAmountType.INCLUDED.value:
            return {"component": component, "amount": 0.0, "multiplier": 1, "manual_review": False, "warnings": warnings}
        if amount_type != AncillaryAmountType.FIXED.value or component.get("amount") is None:
            warnings.append(f"{component.get('component_type')} uses {amount_type or 'unknown'} amount logic; manual review is required.")
            return {"component": component, "amount": None, "multiplier": 1, "manual_review": True, "warnings": warnings}
        multiplier = self._component_multiplier(component, scenario)
        amount = float(component["amount"]) * multiplier
        return {"component": component, "amount": round(amount, 2), "multiplier": multiplier, "manual_review": False, "warnings": warnings}

    def _component_multiplier(self, component: dict[str, Any], scenario: dict[str, Any]) -> int:
        applies_per = component.get("applies_per")
        if applies_per == AncillaryAppliesPer.SEGMENT.value:
            multiplier = int(scenario.get("segment_count") or 1)
        elif applies_per == AncillaryAppliesPer.DIRECTION.value:
            multiplier = int(scenario.get("direction_count") or 1)
        else:
            multiplier = 1
        if component.get("roundtrip_doubling_rule") and int(scenario.get("direction_count") or 1) > 1:
            multiplier *= 2
        return max(multiplier, 1)

    def _quote_explanation(self, status: str, rule_ids: list[str], exceptions: list[dict[str, Any]], amount: float | None, currency: str | None) -> str:
        if status == AirlineServicePriceQuoteEvaluationStatus.BLOCKED.value:
            return "A blocker exception applies; no non-binding price estimate is produced."
        if status == AirlineServicePriceQuoteEvaluationStatus.NO_PRICE_FOUND.value:
            return "No matching active pricing rule was found; manual review is required before quoting."
        if status == AirlineServicePriceQuoteEvaluationStatus.MANUAL_REVIEW.value:
            return "A non-binding estimate was evaluated but one or more components or conditions require manual review."
        if amount is not None:
            return f"Non-binding estimate from {len(rule_ids)} pricing rule(s): {amount:.2f} {currency or ''}".strip()
        if exceptions:
            return "Only exception metadata matched; no amount was calculated."
        return "No deterministic pricing amount was calculated."

    def _visible_for_resource(self, resource: str, item: dict[str, Any], agency_id: str | None) -> bool:
        if resource == "quote_scenarios":
            return item.get("agency_id") in {None, agency_id}
        if resource == "quote_results":
            return True
        return visible_scoped(item, agency_id)

    def _normalize_payload(self, data: dict[str, Any], resource: str) -> dict[str, Any]:
        normalized = dict(data)
        if "airline_code" in normalized:
            normalized["airline_code"] = normalize_airline_code(normalized.get("airline_code"))
        if "currency" in normalized:
            normalized["currency"] = normalize_currency(normalized.get("currency"))
        for key in ["domain_code", "family_code", "variant_code"]:
            if key in normalized:
                normalized[key] = normalize_taxonomy_code(normalized.get(key))
        if "dimension_code" in normalized:
            normalized["dimension_code"] = normalize_taxonomy_code(normalized.get("dimension_code")) or ""
        for key in ["origin_country", "destination_country"]:
            if key in normalized and normalized.get(key) is not None:
                normalized[key] = str(normalized[key]).strip().upper() or None
        for key in ["origin_airport", "destination_airport"]:
            if key in normalized and normalized.get(key) is not None:
                normalized[key] = str(normalized[key]).strip().upper() or None
        if resource == "pricing_matrices" and normalized.get("scope") == AncillaryPricingScope.GLOBAL.value:
            normalized["agency_id"] = None
        for key, value in list(normalized.items()):
            normalized[key] = enum_value(value)
        return normalized

    def _text(self, value: Any) -> str:
        return str(value or "").strip().lower()
