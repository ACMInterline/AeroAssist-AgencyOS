from __future__ import annotations

import re
from typing import Any

from database import Database
from models import (
    AirlinePolicyComparisonProfile,
    AirlinePolicyComparisonRow,
    AirlinePolicyComparisonSavedView,
    AirlinePolicyComparisonSnapshot,
    AirlineServiceAdvisorResult,
    AirlineServiceAdvisorScenario,
    PolicyComparisonGeneratedFrom,
    PolicyComparisonStatus,
    PolicyComparisonWarningLevel,
    ServiceAdvisorResultStatus,
)
from services.ancillary_pricing_service import AncillaryPricingService
from services.service_mechanics_service import ServiceMechanicsService


PHASE_LABEL = "phase_37_1_policy_comparison_service_advisor_foundation"

PROFILE_COLLECTION = "airline_policy_comparison_profiles"
SNAPSHOT_COLLECTION = "airline_policy_comparison_snapshots"
ROW_COLLECTION = "airline_policy_comparison_rows"
ADVISOR_SCENARIO_COLLECTION = "airline_service_advisor_scenarios"
ADVISOR_RESULT_COLLECTION = "airline_service_advisor_results"
SAVED_VIEW_COLLECTION = "airline_policy_comparison_saved_views"


def normalize_taxonomy_code(value: Any) -> str | None:
    text = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return text or None


def normalize_airline_code(value: Any) -> str | None:
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


def compact_unique(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def visible_scoped(item: dict[str, Any], agency_id: str | None) -> bool:
    if item.get("is_global", item.get("agency_id") is None):
        return True
    return bool(agency_id and item.get("agency_id") == agency_id)


class PolicyComparisonService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "comparison_profile_count": len(await self.list_profiles(agency_id=agency_id)),
            "comparison_snapshot_count": len(await self.list_snapshots(agency_id=agency_id)),
            "comparison_row_count": len(await self.list_rows(agency_id=agency_id)),
            "advisor_scenario_count": len(await self.list_advisor_scenarios(agency_id=agency_id)),
            "advisor_result_count": len(await self.list_advisor_results(agency_id=agency_id)),
            "saved_view_count": len(await self.list_saved_views(agency_id=agency_id)),
            "deterministic_service_advisor_enabled": True,
            "operational_complexity_scoring_enabled": True,
            "recommendations_disabled": True,
            "provider_execution_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "agency_global_mutation_blocked": True,
            "diagnostic": "Policy comparison and service advisor records are metadata-only and do not book, issue, charge, contact providers, or recommend airlines automatically.",
        }

    async def list_profiles(
        self,
        *,
        agency_id: str | None = None,
        airline_code: str | None = None,
        domain_code: str | None = None,
        family_code: str | None = None,
        variant_code: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        items = await self.db.collection(PROFILE_COLLECTION).find_many()
        items = [item for item in items if visible_scoped(item, agency_id)]
        return self._filter_common(items, airline_code, domain_code, family_code, variant_code, include_archived=include_archived)

    async def create_profile(self, payload: Any, agency_id: str | None = None) -> dict[str, Any]:
        data = self._normalize_payload(payload_dict(payload))
        data["display_name"] = data.get("display_name") or self._display_name(data)
        if agency_id:
            data["agency_id"] = agency_id
            data["is_global"] = False
        profile = AirlinePolicyComparisonProfile(**data)
        return await self.db.collection(PROFILE_COLLECTION).insert_one(profile.model_dump(mode="json"))

    async def update_profile(self, profile_id: str, payload: Any, agency_id: str | None = None) -> dict[str, Any] | None:
        existing = await self.db.collection(PROFILE_COLLECTION).find_one({"id": profile_id})
        if not existing:
            return None
        if agency_id and existing.get("is_global", existing.get("agency_id") is None):
            raise PermissionError("Agency users cannot mutate global comparison profiles.")
        if agency_id and existing.get("agency_id") != agency_id:
            return None
        updates = self._normalize_payload(clean_updates(payload))
        if "display_name" not in updates and any(key in updates for key in ["airline_code", "domain_code", "family_code", "variant_code"]):
            merged = {**existing, **updates}
            updates["display_name"] = self._display_name(merged)
        return await self.db.collection(PROFILE_COLLECTION).update_one({"id": profile_id}, updates)

    async def build_profile(self, payload: Any, user: dict | None = None, agency_id: str | None = None, persist: bool = True) -> dict[str, Any]:
        data = self._normalize_payload(payload_dict(payload))
        if agency_id:
            data["agency_id"] = agency_id
            data["is_global"] = False
        profile_data = await self._profile_data(data, agency_id=agency_id)
        profile = AirlinePolicyComparisonProfile(**profile_data)
        if persist:
            return await self.db.collection(PROFILE_COLLECTION).insert_one(profile.model_dump(mode="json"))
        return profile.model_dump(mode="json")

    async def compare(self, payload: Any, user: dict | None = None, agency_id: str | None = None) -> dict[str, Any]:
        data = self._normalize_payload(payload_dict(payload))
        airline_codes = compact_unique([normalize_airline_code(item) for item in data.get("airline_codes") or []])
        if not airline_codes:
            airline_codes = ["UNKNOWN"]
        domain_code = normalize_taxonomy_code(data.get("domain_code")) or "other"
        family_code = normalize_taxonomy_code(data.get("family_code")) or "unknown"
        variant_code = normalize_taxonomy_code(data.get("variant_code"))
        route_context = data.get("route_context_json") or {}
        passenger_context = data.get("passenger_context_json") or {}
        service_context = data.get("service_context_json") or {}
        generated_from = enum_value(data.get("generated_from")) or PolicyComparisonGeneratedFrom.MANUAL.value

        row_inputs = []
        warnings: list[str] = []
        for airline_code in airline_codes:
            profile = await self.build_profile(
                {
                    "airline_code": airline_code,
                    "domain_code": domain_code,
                    "family_code": family_code,
                    "variant_code": variant_code,
                    "is_global": agency_id is None,
                },
                user,
                agency_id=agency_id,
                persist=False,
            )
            row_inputs.append(self._comparison_row_from_profile(profile, route_context, passenger_context, service_context))
            if self._profile_has_no_data(profile):
                warnings.append(f"No comparison facts found for {airline_code} {domain_code}/{family_code}.")

        snapshot = AirlinePolicyComparisonSnapshot(
            agency_id=agency_id,
            snapshot_name=data.get("snapshot_name") or f"{domain_code}/{family_code} comparison",
            airline_codes=airline_codes,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
            route_context_json=route_context,
            passenger_context_json=passenger_context,
            service_context_json=service_context,
            comparison_rows_json=row_inputs,
            warnings=warnings,
            generated_from=generated_from,
        )
        stored_snapshot = await self.db.collection(SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))
        rows = []
        for row_data in row_inputs:
            row = AirlinePolicyComparisonRow(snapshot_id=stored_snapshot["id"], **row_data)
            rows.append(await self.db.collection(ROW_COLLECTION).insert_one(row.model_dump(mode="json")))
        return {
            "snapshot": stored_snapshot,
            "rows": rows,
            "warnings": warnings,
            "recommendations_disabled": True,
            "provider_execution_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
        }

    async def create_snapshot(self, payload: Any, agency_id: str | None = None) -> dict[str, Any]:
        data = self._normalize_payload(payload_dict(payload))
        if agency_id:
            data["agency_id"] = agency_id
        snapshot = AirlinePolicyComparisonSnapshot(**data)
        return await self.db.collection(SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))

    async def list_snapshots(
        self,
        *,
        agency_id: str | None = None,
        domain_code: str | None = None,
        family_code: str | None = None,
        variant_code: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self.db.collection(SNAPSHOT_COLLECTION).find_many()
        items = [item for item in items if item.get("agency_id") in {None, agency_id}]
        return self._filter_common(items, None, domain_code, family_code, variant_code, include_archived=True)

    async def list_rows(
        self,
        *,
        agency_id: str | None = None,
        snapshot_id: str | None = None,
        airline_code: str | None = None,
        domain_code: str | None = None,
        family_code: str | None = None,
        variant_code: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self.db.collection(ROW_COLLECTION).find_many()
        if snapshot_id:
            items = [item for item in items if item.get("snapshot_id") == snapshot_id]
        if agency_id:
            snapshots = await self.list_snapshots(agency_id=agency_id)
            visible_snapshot_ids = {item["id"] for item in snapshots}
            items = [item for item in items if item.get("snapshot_id") in visible_snapshot_ids or item.get("snapshot_id") is None]
        return self._filter_common(items, airline_code, domain_code, family_code, variant_code, include_archived=True)

    async def create_advisor_scenario(self, payload: Any, user: dict | None = None, agency_id: str | None = None) -> dict[str, Any]:
        data = self._normalize_payload(payload_dict(payload))
        if agency_id:
            data["agency_id"] = agency_id
        data["created_by"] = data.get("created_by") or (user or {}).get("id")
        scenario = AirlineServiceAdvisorScenario(**data)
        return await self.db.collection(ADVISOR_SCENARIO_COLLECTION).insert_one(scenario.model_dump(mode="json"))

    async def list_advisor_scenarios(
        self,
        *,
        agency_id: str | None = None,
        domain_code: str | None = None,
        family_code: str | None = None,
        variant_code: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self.db.collection(ADVISOR_SCENARIO_COLLECTION).find_many()
        items = [item for item in items if item.get("agency_id") in {None, agency_id}]
        return self._filter_common(items, None, domain_code, family_code, variant_code, include_archived=True)

    async def evaluate_advisor(self, payload: Any, user: dict | None = None, agency_id: str | None = None) -> dict[str, Any]:
        data = self._normalize_payload(payload_dict(payload))
        scenario = await self._resolve_advisor_scenario(data, user, agency_id)
        passenger_context = {
            key: scenario.get(key)
            for key in ["passenger_age", "passenger_type", "cabin"]
            if scenario.get(key) not in {None, ""}
        }
        route_context = {
            key: scenario.get(key)
            for key in [
                "route_type",
                "direct_vs_connecting",
                "origin_airport",
                "destination_airport",
                "origin_country",
                "destination_country",
                "segment_count",
                "direction_count",
            ]
            if scenario.get(key) not in {None, ""}
        }
        comparison = await self.compare(
            {
                "snapshot_name": f"{scenario.get('scenario_name')} comparison",
                "airline_codes": scenario.get("airline_codes") or [],
                "domain_code": scenario.get("domain_code"),
                "family_code": scenario.get("family_code"),
                "variant_code": scenario.get("variant_code"),
                "route_context_json": route_context,
                "passenger_context_json": passenger_context,
                "service_context_json": scenario.get("requested_service_context_json") or {},
                "generated_from": PolicyComparisonGeneratedFrom.REQUEST_CONTEXT.value,
            },
            user,
            agency_id=agency_id,
        )
        rows = comparison.get("rows") or []
        counts = self._advisor_counts(rows)
        result_status = self._advisor_status(rows, counts)
        operational_warnings = compact_unique(
            [warning for row in rows for warning in (row.get("row_json") or {}).get("warnings", [])]
            + comparison.get("warnings", [])
        )
        result = AirlineServiceAdvisorResult(
            scenario_id=scenario["id"],
            result_status=result_status,
            advisory_rows_json=rows,
            comparison_snapshot_id=(comparison.get("snapshot") or {}).get("id"),
            operational_warnings=operational_warnings,
            blocker_count=counts["blocker_count"],
            warning_count=counts["warning_count"],
            advisory_count=counts["advisory_count"],
            manual_contact_required_count=counts["manual_contact_required_count"],
            emd_required_count=counts["emd_required_count"],
            estimated_price_available_count=counts["estimated_price_available_count"],
            explanation=self._advisor_explanation(result_status, counts),
        )
        stored_result = await self.db.collection(ADVISOR_RESULT_COLLECTION).insert_one(result.model_dump(mode="json"))
        return {
            "scenario": scenario,
            "result": stored_result,
            "comparison_snapshot": comparison.get("snapshot"),
            "advisory_rows": rows,
            "recommendations_disabled": True,
            "provider_execution_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
        }

    async def list_advisor_results(self, *, agency_id: str | None = None, scenario_id: str | None = None) -> list[dict[str, Any]]:
        items = await self.db.collection(ADVISOR_RESULT_COLLECTION).find_many()
        if scenario_id:
            items = [item for item in items if item.get("scenario_id") == scenario_id]
        if agency_id:
            scenarios = await self.list_advisor_scenarios(agency_id=agency_id)
            visible_scenario_ids = {item["id"] for item in scenarios}
            items = [item for item in items if item.get("scenario_id") in visible_scenario_ids]
        return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def list_saved_views(
        self,
        *,
        agency_id: str | None = None,
        domain_code: str | None = None,
        family_code: str | None = None,
        variant_code: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        items = await self.db.collection(SAVED_VIEW_COLLECTION).find_many()
        items = [item for item in items if visible_scoped(item, agency_id)]
        return self._filter_common(items, None, domain_code, family_code, variant_code, include_archived=include_archived)

    async def create_saved_view(self, payload: Any, agency_id: str | None = None) -> dict[str, Any]:
        data = self._normalize_payload(payload_dict(payload))
        if agency_id:
            data["agency_id"] = agency_id
            data["is_global"] = False
        view = AirlinePolicyComparisonSavedView(**data)
        return await self.db.collection(SAVED_VIEW_COLLECTION).insert_one(view.model_dump(mode="json"))

    async def update_saved_view(self, view_id: str, payload: Any, agency_id: str | None = None) -> dict[str, Any] | None:
        existing = await self.db.collection(SAVED_VIEW_COLLECTION).find_one({"id": view_id})
        if not existing:
            return None
        if agency_id and existing.get("is_global", existing.get("agency_id") is None):
            raise PermissionError("Agency users cannot mutate global saved views.")
        if agency_id and existing.get("agency_id") != agency_id:
            return None
        updates = self._normalize_payload(clean_updates(payload))
        return await self.db.collection(SAVED_VIEW_COLLECTION).update_one({"id": view_id}, updates)

    async def _resolve_advisor_scenario(self, data: dict[str, Any], user: dict | None, agency_id: str | None) -> dict[str, Any]:
        scenario_id = data.get("scenario_id")
        if scenario_id:
            existing = await self.db.collection(ADVISOR_SCENARIO_COLLECTION).find_one({"id": scenario_id})
            if existing and existing.get("agency_id") in {None, agency_id}:
                return existing
        create_data = {key: value for key, value in data.items() if key != "scenario_id"}
        return await self.create_advisor_scenario(create_data, user, agency_id)

    async def _profile_data(self, data: dict[str, Any], agency_id: str | None) -> dict[str, Any]:
        airline_code = normalize_airline_code(data.get("airline_code")) or "UNKNOWN"
        domain_code = normalize_taxonomy_code(data.get("domain_code")) or "other"
        family_code = normalize_taxonomy_code(data.get("family_code")) or "unknown"
        variant_code = normalize_taxonomy_code(data.get("variant_code"))
        taxonomy = await self._taxonomy_summary(airline_code, domain_code, family_code, variant_code, agency_id)
        mechanics = await ServiceMechanicsService(self.db).lookup(
            airline_code=airline_code,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
            agency_id=agency_id,
        )
        pricing = await AncillaryPricingService(self.db).lookup(
            airline_code=airline_code,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
            agency_id=agency_id,
        )
        approved_knowledge = await self._approved_knowledge_summary(airline_code, domain_code, family_code, variant_code)
        communication_summary = self._communication_summary(mechanics.get("communication") or {})
        payment_summary = self._payment_summary(mechanics.get("payment") or {})
        pricing_summary = self._pricing_summary(pricing.get("pricing") or {})
        exception_summary = self._exception_summary(pricing.get("exceptions") or {})
        source_policy_ids = compact_unique(
            approved_knowledge.get("source_policy_ids", [])
            + self._collect_values(mechanics, "source_policy_id")
            + self._collect_values(pricing, "source_policy_id")
        )
        approved_ids = compact_unique(
            approved_knowledge.get("approved_knowledge_record_ids", [])
            + self._collect_values(mechanics, "approved_knowledge_record_id")
            + self._collect_values(pricing, "approved_knowledge_record_id")
        )
        confidence_score = self._average(
            approved_knowledge.get("confidence_values", [])
            + self._collect_values(mechanics, "confidence_score")
            + self._collect_values(pricing, "confidence_score")
            + taxonomy.get("confidence_values", [])
        )
        commercial_names = compact_unique(
            taxonomy.get("commercial_names", [])
            + payment_summary.get("commercial_names", [])
            + pricing_summary.get("commercial_names", [])
        )
        return {
            "airline_code": airline_code,
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "display_name": data.get("display_name") or self._display_name(data),
            "commercial_names": commercial_names,
            "taxonomy_summary_json": taxonomy,
            "communication_summary_json": communication_summary,
            "payment_summary_json": payment_summary,
            "pricing_summary_json": pricing_summary,
            "exception_summary_json": exception_summary,
            "source_policy_ids": source_policy_ids,
            "approved_knowledge_record_ids": approved_ids,
            "confidence_score": confidence_score,
            "review_status": enum_value(data.get("review_status")) or "suggested",
            "status": enum_value(data.get("status")) or PolicyComparisonStatus.ACTIVE.value,
            "is_global": data.get("is_global", agency_id is None),
            "agency_id": data.get("agency_id") if not agency_id else agency_id,
            "notes": data.get("notes"),
        }

    async def _taxonomy_summary(
        self,
        airline_code: str,
        domain_code: str,
        family_code: str,
        variant_code: str | None,
        agency_id: str | None,
    ) -> dict[str, Any]:
        domain = await self.db.collection("canonical_service_domains").find_one({"code": domain_code})
        family = await self.db.collection("canonical_service_families").find_one({"domain_code": domain_code, "code": family_code})
        variant = None
        if variant_code:
            variant = await self.db.collection("canonical_service_variants").find_one({"domain_code": domain_code, "family_code": family_code, "code": variant_code})
        aliases = [
            item
            for item in await self.db.collection("airline_service_aliases").find_many()
            if visible_scoped(item, agency_id)
            and item.get("airline_code") in {None, airline_code}
            and item.get("domain_code") == domain_code
            and item.get("family_code") == family_code
            and (not variant_code or item.get("variant_code") in {None, variant_code})
            and item.get("status", "active") != "archived"
        ]
        return {
            "domain": self._summary_record(domain, ["code", "name", "description"]),
            "family": self._summary_record(family, ["code", "name", "description"]),
            "variant": self._summary_record(variant, ["code", "name", "ssr_code", "description"]),
            "alias_count": len(aliases),
            "commercial_names": compact_unique([item.get("alias_text") for item in aliases if item.get("alias_type") == "commercial_name"]),
            "ssr_aliases": compact_unique([item.get("alias_text") for item in aliases if item.get("alias_type") == "ssr_code"]),
            "confidence_values": [item.get("confidence_score") for item in aliases if item.get("confidence_score") is not None],
        }

    async def _approved_knowledge_summary(self, airline_code: str, domain_code: str, family_code: str, variant_code: str | None) -> dict[str, Any]:
        sources = [
            item
            for item in await self.db.collection("airline_policy_sources").find_many()
            if item.get("airline_iata_code") in {None, airline_code}
            and item.get("service_domain") in {None, domain_code}
            and item.get("service_family") in {None, family_code}
        ]
        source_ids = {item["id"] for item in sources}
        records = [
            item
            for item in await self.db.collection("airline_policy_approved_knowledge_records").find_many()
            if item.get("service_domain") == domain_code
            and item.get("service_family") == family_code
            and (not variant_code or item.get("service_variant") in {None, variant_code})
            and (not source_ids or item.get("policy_source_id") in source_ids)
            and item.get("status", "approved") == "approved"
        ]
        return {
            "source_policy_ids": compact_unique([item.get("policy_source_id") for item in records] + list(source_ids)),
            "approved_knowledge_record_ids": compact_unique([item.get("id") for item in records]),
            "confidence_values": [item.get("confidence") for item in records if item.get("confidence") is not None],
            "knowledge_type_counts": self._counts_by(records, "knowledge_type"),
        }

    def _communication_summary(self, communication: dict[str, Any]) -> dict[str, Any]:
        rules = communication.get("communication_rules") or []
        templates = communication.get("ssr_osi_templates") or []
        requirements = communication.get("requirements") or []
        return {
            "communication_rule_count": len(rules),
            "template_count": len(templates),
            "requirement_count": len(requirements),
            "ssr_codes": compact_unique([item.get("ssr_code") for item in rules + templates]),
            "request_methods": compact_unique([item.get("request_method") for item in rules]),
            "osi_required": any(item.get("osi_required") or item.get("template_type") == "osi" for item in rules + templates),
            "oths_required": any(item.get("oths_required") for item in rules),
            "airline_confirmation_required": any(item.get("airline_confirmation_required") for item in rules),
            "manual_contact_required": any(item.get("manual_contact_required") for item in rules),
            "ndc_supported": self._any_bool(rules, "ndc_supported"),
            "gds_supported": self._any_bool(rules, "gds_supported"),
            "unknown_mechanics": not any([rules, templates, requirements]),
        }

    def _payment_summary(self, payment: dict[str, Any]) -> dict[str, Any]:
        payment_rules = payment.get("payment_rules") or []
        emd_rules = payment.get("emd_issuance_rules") or []
        rfic = payment.get("rfic_rfisc_mappings") or []
        lifecycle = payment.get("emd_lifecycle_rules") or []
        return {
            "payment_rule_count": len(payment_rules),
            "emd_issuance_rule_count": len(emd_rules),
            "rfic_rfisc_mapping_count": len(rfic),
            "payment_required": any(item.get("payment_required") for item in payment_rules),
            "separate_emd_required": any(item.get("separate_emd_required") for item in payment_rules) or bool(emd_rules),
            "payment_timing": compact_unique([item.get("payment_timing") for item in payment_rules]),
            "emd_types": compact_unique([item.get("emd_type") for item in emd_rules + rfic]),
            "rfic": compact_unique([item.get("rfic") for item in rfic]),
            "rfisc": compact_unique([item.get("rfisc") for item in rfic]),
            "commercial_names": compact_unique([item.get("commercial_name") for item in rfic]),
            "refund_change_summary": self._refund_change_summary(lifecycle),
            "unknown_mechanics": not any([payment_rules, emd_rules, rfic, lifecycle]),
        }

    def _pricing_summary(self, pricing: dict[str, Any]) -> dict[str, Any]:
        rules = pricing.get("pricing_rules") or []
        components = pricing.get("price_components") or []
        matrices = pricing.get("pricing_matrices") or []
        matrix_rows = pricing.get("pricing_matrix_rows") or []
        amounts = [item for item in components + matrix_rows if item.get("amount") is not None]
        return {
            "pricing_rule_count": len(rules),
            "price_component_count": len(components),
            "pricing_matrix_count": len(matrices),
            "pricing_matrix_row_count": len(matrix_rows),
            "mandatory_service": any(item.get("mandatory_service") for item in rules),
            "optional_service": any(item.get("optional_service") for item in rules),
            "fee_included_in_fare": any(item.get("fee_included_in_fare") for item in rules),
            "separate_fee_required": any(item.get("separate_fee_required") for item in rules),
            "emd_required": any(item.get("emd_required") for item in rules + matrix_rows),
            "currencies": compact_unique([item.get("currency") for item in components + matrices + matrix_rows]),
            "amounts": [item.get("amount") for item in amounts],
            "estimated_price_available": bool(amounts),
            "commercial_names": compact_unique([item.get("pricing_rule_name") for item in rules] + [item.get("row_label") for item in matrix_rows]),
            "missing_pricing": not any([rules, components, matrices, matrix_rows]),
        }

    def _exception_summary(self, exceptions: dict[str, Any]) -> dict[str, Any]:
        rules = exceptions.get("exception_rules") or []
        severity_counts = self._counts_by(rules, "severity")
        type_counts = self._counts_by(rules, "exception_type")
        outcome_counts = self._counts_by(rules, "outcome")
        return {
            "exception_rule_count": len(rules),
            "severity_counts": severity_counts,
            "type_counts": type_counts,
            "outcome_counts": outcome_counts,
            "blocker_count": severity_counts.get("blocker", 0),
            "warning_count": severity_counts.get("warning", 0),
            "advisory_count": severity_counts.get("advisory", 0),
            "manual_contact_required": type_counts.get("manual_contact_required", 0) > 0 or outcome_counts.get("manual_review", 0) > 0,
            "documents_required": type_counts.get("document_required", 0) > 0 or outcome_counts.get("document_required", 0) > 0,
            "deadline_restriction": type_counts.get("deadline_restriction", 0) > 0,
            "route_restriction": type_counts.get("route_restriction", 0) > 0,
            "connection_restriction": type_counts.get("connection_restriction", 0) > 0,
            "age_restriction": type_counts.get("age_restriction", 0) > 0,
            "exception_names": compact_unique([item.get("exception_name") for item in rules]),
            "explanations": compact_unique([item.get("explanation") for item in rules]),
        }

    def _comparison_row_from_profile(
        self,
        profile: dict[str, Any],
        route_context: dict[str, Any],
        passenger_context: dict[str, Any],
        service_context: dict[str, Any],
    ) -> dict[str, Any]:
        communication = profile.get("communication_summary_json") or {}
        payment = profile.get("payment_summary_json") or {}
        pricing = profile.get("pricing_summary_json") or {}
        exceptions = profile.get("exception_summary_json") or {}
        warning_level = self._warning_level(communication, payment, exceptions)
        complexity = self._complexity_score(communication, payment, pricing, exceptions)
        warnings = self._row_warnings(communication, payment, pricing, exceptions)
        emd_required = bool(payment.get("separate_emd_required") or pricing.get("emd_required"))
        row_json = {
            "profile_id": profile.get("id"),
            "facts": {
                "taxonomy": profile.get("taxonomy_summary_json") or {},
                "communication": communication,
                "payment": payment,
                "pricing": pricing,
                "exceptions": exceptions,
            },
            "contexts": {
                "route": route_context,
                "passenger": passenger_context,
                "service": service_context,
            },
            "warnings": warnings,
            "metadata_only": True,
            "recommendation": None,
        }
        return {
            "airline_code": profile.get("airline_code") or "UNKNOWN",
            "domain_code": profile.get("domain_code") or "other",
            "family_code": profile.get("family_code") or "unknown",
            "variant_code": profile.get("variant_code"),
            "commercial_name": (profile.get("commercial_names") or [None])[0],
            "mandatory_optional_summary": self._mandatory_optional_summary(pricing),
            "age_rules_summary": "Age restriction metadata present." if exceptions.get("age_restriction") else "No age restriction metadata found.",
            "route_restrictions_summary": "Route restriction metadata present." if exceptions.get("route_restriction") else "No route restriction metadata found.",
            "connection_restrictions_summary": "Connection restriction metadata present." if exceptions.get("connection_restriction") else "No connection restriction metadata found.",
            "documents_required_summary": "Document requirement metadata present." if exceptions.get("documents_required") else "No document requirement metadata found.",
            "deadline_summary": "Deadline restriction metadata present." if exceptions.get("deadline_restriction") else "No deadline metadata found.",
            "ssr_osi_summary": self._ssr_osi_summary(communication),
            "confirmation_summary": "Airline confirmation required." if communication.get("airline_confirmation_required") else "No airline confirmation requirement metadata found.",
            "emd_required": emd_required,
            "emd_type": ", ".join(payment.get("emd_types") or []) or None,
            "rfic": ", ".join(payment.get("rfic") or []) or None,
            "rfisc": ", ".join(payment.get("rfisc") or []) or None,
            "pricing_summary": self._pricing_text(pricing),
            "refund_change_summary": payment.get("refund_change_summary") or "No refund/change mechanics metadata found.",
            "ndc_gds_support_summary": self._support_summary(communication),
            "manual_contact_required": bool(communication.get("manual_contact_required") or exceptions.get("manual_contact_required")),
            "warning_level": warning_level,
            "operational_complexity_score": complexity,
            "confidence_score": profile.get("confidence_score"),
            "source_summary": f"{len(profile.get('source_policy_ids') or [])} policy source(s), {len(profile.get('approved_knowledge_record_ids') or [])} approved knowledge record(s).",
            "row_json": row_json,
        }

    def _complexity_score(
        self,
        communication: dict[str, Any],
        payment: dict[str, Any],
        pricing: dict[str, Any],
        exceptions: dict[str, Any],
    ) -> int:
        score = 0
        if communication.get("manual_contact_required") or exceptions.get("manual_contact_required"):
            score += 25
        if exceptions.get("blocker_count", 0) > 0:
            score += 40
        if exceptions.get("warning_count", 0) > 0:
            score += 20
        if exceptions.get("advisory_count", 0) > 0:
            score += 10
        if payment.get("separate_emd_required") or pricing.get("emd_required"):
            score += 15
        if communication.get("airline_confirmation_required"):
            score += 10
        if pricing.get("missing_pricing"):
            score += 10
        if communication.get("unknown_mechanics") and payment.get("unknown_mechanics"):
            score += 10
        return min(score, 100)

    def _warning_level(self, communication: dict[str, Any], payment: dict[str, Any], exceptions: dict[str, Any]) -> str:
        if exceptions.get("blocker_count", 0) > 0:
            return PolicyComparisonWarningLevel.BLOCKER.value
        if exceptions.get("warning_count", 0) > 0 or communication.get("manual_contact_required") or payment.get("payment_required"):
            return PolicyComparisonWarningLevel.WARNING.value
        if exceptions.get("advisory_count", 0) > 0 or communication.get("airline_confirmation_required") or payment.get("separate_emd_required"):
            return PolicyComparisonWarningLevel.ADVISORY.value
        if communication.get("unknown_mechanics") and payment.get("unknown_mechanics"):
            return PolicyComparisonWarningLevel.INFO.value
        return PolicyComparisonWarningLevel.NONE.value

    def _row_warnings(
        self,
        communication: dict[str, Any],
        payment: dict[str, Any],
        pricing: dict[str, Any],
        exceptions: dict[str, Any],
    ) -> list[str]:
        warnings = []
        if exceptions.get("blocker_count", 0) > 0:
            warnings.append("Blocker exception metadata exists for this service.")
        if communication.get("manual_contact_required") or exceptions.get("manual_contact_required"):
            warnings.append("Manual airline contact metadata is present.")
        if communication.get("airline_confirmation_required"):
            warnings.append("Airline confirmation metadata is present.")
        if payment.get("separate_emd_required") or pricing.get("emd_required"):
            warnings.append("EMD requirement metadata is present; issuance remains disabled.")
        if pricing.get("missing_pricing"):
            warnings.append("No deterministic pricing metadata was found.")
        if communication.get("unknown_mechanics") and payment.get("unknown_mechanics"):
            warnings.append("No service mechanics metadata was found.")
        return warnings

    def _advisor_counts(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        return {
            "blocker_count": len([row for row in rows if row.get("warning_level") == "blocker"]),
            "warning_count": len([row for row in rows if row.get("warning_level") == "warning"]),
            "advisory_count": len([row for row in rows if row.get("warning_level") == "advisory"]),
            "manual_contact_required_count": len([row for row in rows if row.get("manual_contact_required")]),
            "emd_required_count": len([row for row in rows if row.get("emd_required")]),
            "estimated_price_available_count": len([row for row in rows if ((row.get("row_json") or {}).get("facts") or {}).get("pricing", {}).get("estimated_price_available")]),
        }

    def _advisor_status(self, rows: list[dict[str, Any]], counts: dict[str, int]) -> str:
        if not rows:
            return ServiceAdvisorResultStatus.NO_DATA.value
        if counts["blocker_count"]:
            return ServiceAdvisorResultStatus.BLOCKED.value
        if counts["warning_count"] or counts["manual_contact_required_count"]:
            return ServiceAdvisorResultStatus.MANUAL_REVIEW.value
        no_data_rows = [
            row
            for row in rows
            if "No comparison facts found" in " ".join((row.get("row_json") or {}).get("warnings", []))
            or ((row.get("row_json") or {}).get("facts") or {}).get("pricing", {}).get("missing_pricing")
        ]
        if len(no_data_rows) == len(rows):
            return ServiceAdvisorResultStatus.NO_DATA.value
        return ServiceAdvisorResultStatus.EVALUATED.value

    def _advisor_explanation(self, result_status: str, counts: dict[str, int]) -> str:
        if result_status == ServiceAdvisorResultStatus.BLOCKED.value:
            return "One or more blocker metadata rows were found; manual review is required."
        if result_status == ServiceAdvisorResultStatus.MANUAL_REVIEW.value:
            return "Operational metadata indicates warning or manual-contact handling."
        if result_status == ServiceAdvisorResultStatus.NO_DATA.value:
            return "No sufficient comparison metadata was found for the requested context."
        return "Operational guidance metadata was evaluated deterministically without booking, issuing, charging, contacting providers, or recommending airlines."

    def _filter_common(
        self,
        items: list[dict[str, Any]],
        airline_code: str | None,
        domain_code: str | None,
        family_code: str | None,
        variant_code: str | None,
        *,
        include_archived: bool,
    ) -> list[dict[str, Any]]:
        airline_code = normalize_airline_code(airline_code)
        domain_code = normalize_taxonomy_code(domain_code)
        family_code = normalize_taxonomy_code(family_code)
        variant_code = normalize_taxonomy_code(variant_code)
        if airline_code:
            items = [item for item in items if item.get("airline_code") in {None, airline_code} or airline_code in (item.get("airline_codes") or [])]
        if domain_code:
            items = [item for item in items if item.get("domain_code") == domain_code]
        if family_code:
            items = [item for item in items if item.get("family_code") == family_code]
        if variant_code:
            items = [item for item in items if item.get("variant_code") in {None, variant_code}]
        if not include_archived:
            items = [item for item in items if item.get("status", "active") != PolicyComparisonStatus.ARCHIVED.value]
        return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    def _normalize_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(data)
        if "airline_code" in normalized:
            normalized["airline_code"] = normalize_airline_code(normalized.get("airline_code"))
        if "airline_codes" in normalized:
            normalized["airline_codes"] = compact_unique([normalize_airline_code(item) for item in normalized.get("airline_codes") or []])
        for key in ["domain_code", "family_code", "variant_code"]:
            if key in normalized:
                normalized[key] = normalize_taxonomy_code(normalized.get(key))
        for key in ["origin_country", "destination_country", "origin_airport", "destination_airport"]:
            if key in normalized and normalized.get(key) is not None:
                normalized[key] = str(normalized[key]).strip().upper() or None
        for key, value in list(normalized.items()):
            normalized[key] = enum_value(value)
        return normalized

    def _display_name(self, data: dict[str, Any]) -> str:
        pieces = [
            normalize_airline_code(data.get("airline_code")) or "UNKNOWN",
            normalize_taxonomy_code(data.get("domain_code")) or "other",
            normalize_taxonomy_code(data.get("family_code")) or "unknown",
            normalize_taxonomy_code(data.get("variant_code")),
        ]
        return " ".join(piece for piece in pieces if piece)

    def _profile_has_no_data(self, profile: dict[str, Any]) -> bool:
        return (
            (profile.get("taxonomy_summary_json") or {}).get("alias_count", 0) == 0
            and (profile.get("communication_summary_json") or {}).get("unknown_mechanics") is True
            and (profile.get("payment_summary_json") or {}).get("unknown_mechanics") is True
            and (profile.get("pricing_summary_json") or {}).get("missing_pricing") is True
            and (profile.get("exception_summary_json") or {}).get("exception_rule_count", 0) == 0
        )

    def _mandatory_optional_summary(self, pricing: dict[str, Any]) -> str:
        if pricing.get("mandatory_service") and pricing.get("optional_service"):
            return "Mandatory and optional pricing metadata both present."
        if pricing.get("mandatory_service"):
            return "Mandatory service metadata present."
        if pricing.get("optional_service"):
            return "Optional service metadata present."
        return "No mandatory/optional pricing metadata found."

    def _ssr_osi_summary(self, communication: dict[str, Any]) -> str:
        codes = communication.get("ssr_codes") or []
        parts = []
        if codes:
            parts.append(f"SSR {', '.join(codes)}")
        if communication.get("osi_required"):
            parts.append("OSI required")
        if communication.get("oths_required"):
            parts.append("OTHS required")
        return "; ".join(parts) or "No SSR/OSI mechanics metadata found."

    def _pricing_text(self, pricing: dict[str, Any]) -> str:
        amounts = pricing.get("amounts") or []
        currencies = pricing.get("currencies") or []
        if amounts:
            amount_text = ", ".join(f"{float(amount):.2f}" for amount in amounts[:3])
            currency_text = "/".join(currencies) if currencies else "currency unknown"
            return f"Non-binding pricing metadata available: {amount_text} {currency_text}."
        if pricing.get("fee_included_in_fare"):
            return "Fee included in fare metadata present."
        if pricing.get("missing_pricing"):
            return "No deterministic pricing metadata found."
        return "Pricing metadata present without deterministic amount."

    def _support_summary(self, communication: dict[str, Any]) -> str:
        ndc = communication.get("ndc_supported")
        gds = communication.get("gds_supported")
        parts = []
        if ndc is not None:
            parts.append(f"NDC {'supported' if ndc else 'not supported'}")
        if gds is not None:
            parts.append(f"GDS {'supported' if gds else 'not supported'}")
        return "; ".join(parts) or "No NDC/GDS support metadata found."

    def _refund_change_summary(self, lifecycle: list[dict[str, Any]]) -> str:
        if not lifecycle:
            return "No refund/change mechanics metadata found."
        refundable = any(item.get("refundable") for item in lifecycle)
        exchangeable = any(item.get("exchangeable") for item in lifecycle)
        voidable = any(item.get("voidable") for item in lifecycle)
        parts = []
        if refundable:
            parts.append("refundable")
        if exchangeable:
            parts.append("exchangeable")
        if voidable:
            parts.append("voidable")
        return ", ".join(parts) if parts else "Lifecycle metadata present; no positive refund/change flags found."

    def _summary_record(self, item: dict[str, Any] | None, keys: list[str]) -> dict[str, Any]:
        return {key: item.get(key) for key in keys if item and item.get(key) is not None}

    def _counts_by(self, items: list[dict[str, Any]], key: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            value = item.get(key)
            if value in {None, ""}:
                continue
            counts[str(value)] = counts.get(str(value), 0) + 1
        return counts

    def _any_bool(self, items: list[dict[str, Any]], key: str) -> bool | None:
        values = [item.get(key) for item in items if item.get(key) is not None]
        if not values:
            return None
        return any(values)

    def _collect_values(self, data: Any, key: str) -> list[Any]:
        values = []
        if isinstance(data, dict):
            for item_key, value in data.items():
                if item_key == key:
                    values.append(value)
                else:
                    values.extend(self._collect_values(value, key))
        elif isinstance(data, list):
            for item in data:
                values.extend(self._collect_values(item, key))
        return [value for value in values if value not in {None, ""}]

    def _average(self, values: list[Any]) -> float | None:
        numbers = []
        for value in values:
            try:
                numbers.append(float(value))
            except (TypeError, ValueError):
                continue
        if not numbers:
            return None
        return round(sum(numbers) / len(numbers), 4)
