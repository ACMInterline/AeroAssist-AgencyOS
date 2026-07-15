from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import (
    AirlineCoverageAssessment,
    AirlineCoverageRemediationPlan,
    AirlineCoverageTarget,
    AirlineKnowledgeGap,
    AirlineServiceCoverageCell,
    AirlineServiceCoverageProfile,
    AuditEvent,
    KnowledgePopulationToolkitUpdate,
    new_id,
)
from services.knowledge_population_toolkit_service import KnowledgePopulationToolkitService


PHASE_LABEL = "phase_56_2_journey_option_fare_brand_composition_workspace_foundation"

COVERAGE_PROFILE_COLLECTION = "airline_service_coverage_profiles"
COVERAGE_CELL_COLLECTION = "airline_service_coverage_cells"
KNOWLEDGE_GAP_COLLECTION = "airline_knowledge_gaps"
COVERAGE_TARGET_COLLECTION = "airline_coverage_targets"
COVERAGE_ASSESSMENT_COLLECTION = "airline_coverage_assessments"
REMEDIATION_PLAN_COLLECTION = "airline_coverage_remediation_plans"

COVERAGE_COLLECTIONS = [
    COVERAGE_PROFILE_COLLECTION,
    COVERAGE_CELL_COLLECTION,
    KNOWLEDGE_GAP_COLLECTION,
    COVERAGE_TARGET_COLLECTION,
    COVERAGE_ASSESSMENT_COLLECTION,
    REMEDIATION_PLAN_COLLECTION,
]

COVERAGE_STATUSES = [
    "complete_published_knowledge",
    "partial_knowledge",
    "stale_knowledge",
    "conflicting_knowledge",
    "no_knowledge",
    "policy_without_pricing",
    "pricing_without_policy",
    "rules_without_evidence",
    "evidence_without_normalized_knowledge",
    "knowledge_without_scenario_tests",
    "failed_qa",
    "unpublished_approved_knowledge",
]

GAP_TYPES = [
    "missing_policy",
    "missing_pricing",
    "missing_rule",
    "missing_evidence",
    "stale_evidence",
    "unresolved_conflict",
    "missing_effective_date",
    "missing_documents",
    "missing_approval_requirements",
    "missing_client_message",
    "missing_internal_instruction",
    "missing_scenario_test",
    "failed_qa",
    "unpublished",
    "unknown_distribution_scope",
]

CRITICAL_GAP_TYPES = {
    "missing_policy",
    "missing_pricing",
    "missing_rule",
    "missing_evidence",
    "stale_evidence",
    "unresolved_conflict",
    "missing_effective_date",
    "missing_documents",
    "missing_approval_requirements",
    "missing_scenario_test",
    "failed_qa",
    "unpublished",
    "unknown_distribution_scope",
}

SERVICE_COVERAGE_CATALOG = [
    {"service_family": "wheelchair_assistance", "service_codes": ["WCHR", "WCHS", "WCHC"], "aliases": ["wheelchair", "mobility_assistance"]},
    {"service_family": "mobility_devices_batteries", "service_codes": ["WCBD", "WCBW", "WCLB"], "aliases": ["mobility_device", "battery", "wheelchair_battery"]},
    {"service_family": "meda_medif", "service_codes": ["MEDA", "MEDIF"], "aliases": ["medical", "medical_clearance"]},
    {"service_family": "oxygen_poc", "service_codes": ["OXYG", "POC"], "aliases": ["oxygen", "portable_oxygen_concentrator"]},
    {"service_family": "umnr_young_passenger", "service_codes": ["UMNR"], "aliases": ["umnr", "young_passenger"]},
    {"service_family": "petc", "service_codes": ["PETC"], "aliases": ["pets_animals", "pet_in_cabin"]},
    {"service_family": "avih", "service_codes": ["AVIH"], "aliases": ["pets_animals", "animal_in_hold"]},
    {"service_family": "svan", "service_codes": ["SVAN"], "aliases": ["pets_animals", "service_animal"]},
    {"service_family": "esan", "service_codes": ["ESAN"], "aliases": ["pets_animals", "emotional_support_animal"]},
    {"service_family": "exst", "service_codes": ["EXST"], "aliases": ["passenger_of_size", "extra_seat"]},
    {"service_family": "cbbg", "service_codes": ["CBBG"], "aliases": ["cabin_baggage", "extra_seat"]},
    {"service_family": "sports_equipment", "service_codes": [], "aliases": ["sports", "special_baggage"]},
    {"service_family": "musical_instruments", "service_codes": [], "aliases": ["musical_instrument", "special_baggage"]},
    {"service_family": "fragile_valuable", "service_codes": [], "aliases": ["fragile", "valuable", "special_baggage"]},
    {"service_family": "special_baggage", "service_codes": [], "aliases": ["restricted_equipment", "oversize_baggage"]},
    {"service_family": "documents_compliance", "service_codes": [], "aliases": ["documents", "compliance"]},
    {"service_family": "emd_payment_handling", "service_codes": [], "aliases": ["emd", "payment", "rfic", "rfisc"]},
]

COVERAGE_DIMENSIONS = [
    "airline_code",
    "service_family",
    "service_code",
    "route_type",
    "flight_type",
    "cabin",
    "fare_bundle",
    "operating_carrier",
    "marketing_carrier",
    "aircraft_family",
    "country_scope",
    "airport_scope",
    "distribution_channel",
    "effective_date",
    "evidence_freshness",
]

DEFAULT_MINIMUM_SCORES = {
    "completeness": 85,
    "confidence": 70,
    "freshness": 70,
    "test_coverage": 80,
    "publication_readiness": 90,
    "operational_usability": 80,
}

SOURCE_COLLECTIONS = {
    "policies": "visual_policy_editor_cards",
    "pricing": "pricing_formula_builders",
    "rules": "operational_rule_composer_rules",
    "normalisations": "airline_knowledge_normalisations",
    "capabilities": "airline_capability_matrix",
    "evidence_assertions": "airline_evidence_assertions",
    "evidence_sources": "airline_evidence_sources",
    "evidence_freshness": "airline_evidence_freshness_assessments",
    "evidence_conflicts": "airline_evidence_conflicts",
    "qa_reviews": "knowledge_quality_assurance_reviews",
    "publications": "airline_knowledge_publications",
    "scenarios": "operational_scenario_tests",
    "toolkits": "knowledge_population_toolkits",
    "pilot_profiles": "pilot_readiness_profiles",
    "pilot_assessments": "pilot_readiness_assessments",
    "distribution": "airline_distribution_summaries",
    "distribution_channels": "airline_distribution_channels",
    "distribution_capabilities": "airline_distribution_capabilities",
    "recommendations": "airline_recommendations",
    "service_instructions": "airline_policy_extracted_communication_rules",
}

CONFIDENCE_SCORES = {
    "official_source": 95,
    "official": 95,
    "very_high": 95,
    "high": 85,
    "medium": 60,
    "low": 35,
    "unknown": 20,
}

FRESHNESS_SCORES = {
    "current": 100,
    "fresh": 100,
    "reviewed": 90,
    "review_due": 55,
    "due_soon": 55,
    "unknown": 40,
    "stale": 20,
    "expired": 0,
}

DOCUMENT_SENSITIVE_FAMILIES = {
    "mobility_devices_batteries",
    "meda_medif",
    "oxygen_poc",
    "umnr_young_passenger",
    "petc",
    "avih",
    "svan",
    "esan",
    "documents_compliance",
}

APPROVAL_SENSITIVE_FAMILIES = DOCUMENT_SENSITIVE_FAMILIES | {"exst", "cbbg"}

GAP_GUIDANCE = {
    "missing_policy": "Create and review a structured policy card for this airline and service scope.",
    "missing_pricing": "Add governed pricing behavior or explicitly record that manual pricing applies.",
    "missing_rule": "Compose an operational rule with conditions, outcomes, and human-readable instructions.",
    "missing_evidence": "Link an approved evidence assertion to the governing knowledge records.",
    "stale_evidence": "Review or replace stale evidence while preserving the prior source history.",
    "unresolved_conflict": "Resolve the evidence conflict through governance without deleting either source.",
    "missing_effective_date": "Define the effective window for the applicable knowledge.",
    "missing_documents": "Define required documents or explicitly record that none are required.",
    "missing_approval_requirements": "Define approval requirements or explicitly record that approval is not required.",
    "missing_client_message": "Add an approved client-facing explanation separate from internal instructions.",
    "missing_internal_instruction": "Add an internal operational instruction for agency staff.",
    "missing_scenario_test": "Create and human-review an operational scenario test for this scope.",
    "failed_qa": "Resolve blocking QA findings and obtain a new human review decision.",
    "unpublished": "Complete approval and publish through the existing controlled publishing workflow.",
    "unknown_distribution_scope": "Record applicable distribution, operating-carrier, and marketing-carrier scope.",
}


class AirlineServiceCoverageGapError(ValueError):
    pass


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_none=True, exclude_unset=True)
    return {key: value for key, value in dict(payload or {}).items() if value is not None}


class AirlineServiceCoverageGapService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "deterministic_coverage_scoring_enabled": True,
            "critical_gap_operational_ready_guard_enabled": True,
            "canonical_knowledge_sources_reused": True,
            "knowledge_population_toolkit_integration_enabled": True,
            "pilot_readiness_integration_enabled": True,
            "knowledge_qa_integration_enabled": True,
            "publishing_integration_enabled": True,
            "scenario_testing_integration_enabled": True,
            "capability_matrix_integration_enabled": True,
            "recommendation_hint_integration_enabled": True,
            "offer_intelligence_mutation_disabled": True,
            "automatic_publication_disabled": True,
            "automatic_recommendation_disabled": True,
            "historical_snapshot_mutation_disabled": True,
            "agency_published_coverage_read_only": True,
            "unpublished_draft_agency_visibility_disabled": True,
            "restricted_evidence_protected": True,
            "external_api_calls_disabled": True,
            "provider_execution_disabled": True,
            "ai_disabled": True,
            "metadata_only": True,
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "coverage_statuses": COVERAGE_STATUSES,
            "gap_types": GAP_TYPES,
            "critical_gap_types": sorted(CRITICAL_GAP_TYPES),
            "service_catalog": SERVICE_COVERAGE_CATALOG,
            "coverage_dimensions": COVERAGE_DIMENSIONS,
            "minimum_scores": DEFAULT_MINIMUM_SCORES,
        }

    async def create_target(self, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        data.setdefault("target_reference", self._reference("ACT"))
        data.setdefault("target_name", data["target_reference"])
        data["airline_codes"] = self._unique(self._airline(value) for value in data.get("airline_codes") or [])
        data["service_families"] = self._canonical_families(data.get("service_families") or [])
        data["service_codes"] = self._unique(self._code(value).upper() for value in data.get("service_codes") or [])
        data["minimum_scores"] = {**DEFAULT_MINIMUM_SCORES, **(data.get("minimum_scores") or {})}
        data["required_gap_free_types"] = self._unique(data.get("required_gap_free_types") or sorted(CRITICAL_GAP_TYPES))
        if not data["airline_codes"]:
            raise AirlineServiceCoverageGapError("A coverage target requires at least one airline code.")
        target = AirlineCoverageTarget(**data)
        created = await self.db.collection(COVERAGE_TARGET_COLLECTION).insert_one(target.model_dump(mode="json"))
        await self._audit("airline_service_coverage.target_created", created["id"], user, {"airline_codes": created["airline_codes"]})
        return {"phase": PHASE_LABEL, "target": created, **self.safety_flags()}

    async def update_target(self, target_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require(COVERAGE_TARGET_COLLECTION, target_id, "Coverage target")
        updates = payload_dict(payload)
        if "airline_codes" in updates:
            updates["airline_codes"] = self._unique(self._airline(value) for value in updates["airline_codes"])
        if "service_families" in updates:
            updates["service_families"] = self._canonical_families(updates["service_families"])
        if "service_codes" in updates:
            updates["service_codes"] = self._unique(self._code(value).upper() for value in updates["service_codes"])
        if "minimum_scores" in updates:
            updates["minimum_scores"] = {**DEFAULT_MINIMUM_SCORES, **updates["minimum_scores"]}
        updated = await self.db.collection(COVERAGE_TARGET_COLLECTION).update_one({"id": existing["id"]}, updates)
        await self._audit("airline_service_coverage.target_updated", existing["id"], user, {"fields": sorted(updates)})
        return {"phase": PHASE_LABEL, "target": updated, **self.safety_flags()}

    async def list_targets(self, agency_id: str | None = None, target_status: str | None = None) -> list[dict[str, Any]]:
        items = await self.db.collection(COVERAGE_TARGET_COLLECTION).find_many()
        if agency_id is not None:
            items = [item for item in items if item.get("agency_id") in {None, agency_id}]
        if target_status:
            items = [item for item in items if item.get("target_status") == self._code(target_status)]
        return sorted(items, key=lambda item: self._sort_time(item.get("updated_at") or item.get("created_at")), reverse=True)

    async def create_assessment(self, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        reference = str(data.get("assessment_reference") or self._reference("ACA"))
        existing = await self.db.collection(COVERAGE_ASSESSMENT_COLLECTION).find_one({"assessment_reference": reference})
        if existing:
            return await self.get_assessment(existing["id"])

        target = None
        if data.get("target_id"):
            target = await self._require(COVERAGE_TARGET_COLLECTION, str(data["target_id"]), "Coverage target")
        agency_id = data.get("agency_id") if "agency_id" in data else (target or {}).get("agency_id")
        airline_codes = self._unique(self._airline(value) for value in (data.get("airline_codes") or (target or {}).get("airline_codes") or []))
        service_families = self._canonical_families(data.get("service_families") or (target or {}).get("service_families") or [item["service_family"] for item in SERVICE_COVERAGE_CATALOG])
        service_codes = self._unique(self._code(value).upper() for value in (data.get("service_codes") or (target or {}).get("service_codes") or []))
        dimensions = data.get("coverage_dimensions") or (target or {}).get("coverage_dimensions") or [{}]
        minimum_scores = {**DEFAULT_MINIMUM_SCORES, **((target or {}).get("minimum_scores") or {}), **(data.get("minimum_scores") or {})}
        required_gap_free = set((target or {}).get("required_gap_free_types") or CRITICAL_GAP_TYPES)
        if not airline_codes:
            raise AirlineServiceCoverageGapError("A coverage assessment requires at least one airline code.")
        if not service_families:
            raise AirlineServiceCoverageGapError("A coverage assessment requires at least one service family.")

        started = datetime.now(timezone.utc)
        assessment = AirlineCoverageAssessment(
            assessment_reference=reference,
            agency_id=agency_id,
            target_id=(target or {}).get("id"),
            assessment_status="assessing",
            airline_codes=airline_codes,
            service_families=service_families,
            service_codes=service_codes,
            coverage_dimensions=dimensions,
            assessed_by_user_id=user.get("id"),
            started_at=started,
            notes=data.get("notes"),
            metadata={"minimum_scores": minimum_scores, "required_gap_free_types": sorted(required_gap_free)},
        )
        stored_assessment = await self.db.collection(COVERAGE_ASSESSMENT_COLLECTION).insert_one(assessment.model_dump(mode="json"))
        sources = await self._load_sources(agency_id)

        all_cells: list[dict[str, Any]] = []
        all_gaps: list[dict[str, Any]] = []
        profiles: list[dict[str, Any]] = []
        remediation_plans: list[dict[str, Any]] = []
        toolkit_updates = 0

        for airline_code in airline_codes:
            airline_cells: list[dict[str, Any]] = []
            airline_gaps: list[dict[str, Any]] = []
            for family in service_families:
                codes = self._service_codes_for(family, service_codes)
                for service_code in codes:
                    for raw_dimension in dimensions:
                        dimension = self._normalize_dimension(raw_dimension)
                        cell_data, gap_specs = self._assess_cell(
                            assessment_id=stored_assessment["id"],
                            agency_id=agency_id,
                            airline_code=airline_code,
                            service_family=family,
                            service_code=service_code,
                            dimension=dimension,
                            sources=sources,
                            minimum_scores=minimum_scores,
                            required_gap_free=required_gap_free,
                        )
                        cell = await self.db.collection(COVERAGE_CELL_COLLECTION).insert_one(
                            AirlineServiceCoverageCell(**cell_data).model_dump(mode="json")
                        )
                        gaps: list[dict[str, Any]] = []
                        for spec in gap_specs:
                            spec.update({"coverage_cell_id": cell["id"]})
                            gap = await self.db.collection(KNOWLEDGE_GAP_COLLECTION).insert_one(
                                AirlineKnowledgeGap(**spec).model_dump(mode="json")
                            )
                            gaps.append(gap)
                        if gaps:
                            cell = await self.db.collection(COVERAGE_CELL_COLLECTION).update_one(
                                {"id": cell["id"]},
                                {"gap_ids": [gap["id"] for gap in gaps]},
                            ) or cell
                        airline_cells.append(cell)
                        airline_gaps.extend(gaps)
                        all_cells.append(cell)
                        all_gaps.extend(gaps)

            toolkit_ids = [item["id"] for item in sources["toolkits"] if self._airline(item.get("airline_code")) == airline_code]
            pilot_ids = self._pilot_assessment_ids(airline_code, sources)
            profile_data = self._profile_data(stored_assessment["id"], agency_id, airline_code, airline_cells, airline_gaps, toolkit_ids, pilot_ids)
            profile = await self.db.collection(COVERAGE_PROFILE_COLLECTION).insert_one(
                AirlineServiceCoverageProfile(**profile_data).model_dump(mode="json")
            )
            profiles.append(profile)
            for cell in airline_cells:
                await self.db.collection(COVERAGE_CELL_COLLECTION).update_one({"id": cell["id"]}, {"profile_id": profile["id"]})
            for gap in airline_gaps:
                await self.db.collection(KNOWLEDGE_GAP_COLLECTION).update_one({"id": gap["id"]}, {"profile_id": profile["id"]})

            if airline_gaps:
                plan = await self._create_generated_remediation_plan(stored_assessment, profile, airline_gaps, toolkit_ids, user)
                remediation_plans.append(plan)
            if data.get("sync_population_toolkit", True) and toolkit_ids:
                toolkit_updates += await self._sync_population_toolkits(profile, airline_cells, airline_gaps, sources["toolkits"], user)

        score_summary = self._aggregate_scores(all_cells)
        state_counts = self._counts(all_cells, "coverage_status")
        integration_summary = {
            "knowledge_population_toolkit_records": sum(len(profile.get("population_toolkit_ids") or []) for profile in profiles),
            "knowledge_population_toolkit_records_updated": toolkit_updates,
            "pilot_readiness_assessments": sum(len(profile.get("pilot_readiness_assessment_ids") or []) for profile in profiles),
            "qa_reviews_considered": len(sources["qa_reviews"]),
            "publications_considered": len(sources["publications"]),
            "scenario_tests_considered": len(sources["scenarios"]),
            "capability_rows_considered": len(sources["capabilities"]),
            "recommendation_records_available": len(sources["recommendations"]),
            "offer_intelligence_records_mutated": 0,
        }
        completed = await self.db.collection(COVERAGE_ASSESSMENT_COLLECTION).update_one(
            {"id": stored_assessment["id"]},
            {
                "assessment_status": "completed",
                "score_summary": score_summary,
                "coverage_state_counts": state_counts,
                "integration_summary": integration_summary,
                "profile_ids": [item["id"] for item in profiles],
                "coverage_cell_ids": [item["id"] for item in all_cells],
                "gap_ids": [item["id"] for item in all_gaps],
                "remediation_plan_ids": [item["id"] for item in remediation_plans],
                "operational_ready_cell_count": len([item for item in all_cells if item.get("operational_ready")]),
                "critical_gap_count": len([item for item in all_gaps if item.get("critical")]),
                "completed_at": datetime.now(timezone.utc),
            },
        )
        await self._audit(
            "airline_service_coverage.assessment_completed",
            stored_assessment["id"],
            user,
            {"cell_count": len(all_cells), "gap_count": len(all_gaps), "critical_gap_count": len([gap for gap in all_gaps if gap.get("critical")])},
        )
        return {
            "phase": PHASE_LABEL,
            "assessment": completed,
            "profiles": profiles,
            "cells": all_cells,
            "gaps": all_gaps,
            "remediation_plans": remediation_plans,
            **self.safety_flags(),
        }

    async def get_assessment(self, assessment_id: str) -> dict[str, Any]:
        assessment = await self._require(COVERAGE_ASSESSMENT_COLLECTION, assessment_id, "Coverage assessment")
        profiles = await self.db.collection(COVERAGE_PROFILE_COLLECTION).find_many({"assessment_id": assessment["id"]})
        cells = await self.db.collection(COVERAGE_CELL_COLLECTION).find_many({"assessment_id": assessment["id"]})
        gaps = await self.db.collection(KNOWLEDGE_GAP_COLLECTION).find_many({"assessment_id": assessment["id"]})
        plans = await self.db.collection(REMEDIATION_PLAN_COLLECTION).find_many({"assessment_id": assessment["id"]})
        return {
            "phase": PHASE_LABEL,
            "assessment": assessment,
            "profiles": profiles,
            "cells": cells,
            "gaps": gaps,
            "remediation_plans": plans,
            **self.safety_flags(),
        }

    async def list_assessments(self, agency_id: str | None = None, assessment_status: str | None = None) -> list[dict[str, Any]]:
        items = await self.db.collection(COVERAGE_ASSESSMENT_COLLECTION).find_many()
        if agency_id is not None:
            items = [item for item in items if item.get("agency_id") in {None, agency_id}]
        if assessment_status:
            items = [item for item in items if item.get("assessment_status") == self._code(assessment_status)]
        return sorted(items, key=lambda item: self._sort_time(item.get("completed_at") or item.get("created_at")), reverse=True)

    async def list_cells(self, **filters: Any) -> list[dict[str, Any]]:
        items = await self.db.collection(COVERAGE_CELL_COLLECTION).find_many()
        for key in [
            "assessment_id",
            "agency_id",
            "airline_code",
            "service_family",
            "service_code",
            "coverage_status",
            "route_type",
            "flight_type",
            "cabin",
            "fare_bundle",
            "operating_carrier",
            "marketing_carrier",
            "aircraft_family",
            "distribution_channel",
            "evidence_freshness",
        ]:
            value = filters.get(key)
            if value is None:
                continue
            if key in {"airline_code", "operating_carrier", "marketing_carrier"}:
                normalized = self._airline(value)
                items = [item for item in items if self._airline(item.get(key)) == normalized]
            else:
                normalized = self._code(value)
                items = [item for item in items if self._code(item.get(key)) == normalized]
        if filters.get("operational_ready") is not None:
            items = [item for item in items if item.get("operational_ready") is filters["operational_ready"]]
        if filters.get("critical_only"):
            items = [item for item in items if item.get("critical_gap_types")]
        return sorted(items, key=self._cell_priority_key)

    async def list_gaps(self, **filters: Any) -> list[dict[str, Any]]:
        items = await self.db.collection(KNOWLEDGE_GAP_COLLECTION).find_many()
        for key in ["assessment_id", "agency_id", "airline_code", "service_family", "service_code", "gap_type", "gap_status", "severity"]:
            value = filters.get(key)
            if value is None:
                continue
            if key == "airline_code":
                normalized = self._airline(value)
                items = [item for item in items if self._airline(item.get(key)) == normalized]
            else:
                normalized = self._code(value)
                items = [item for item in items if self._code(item.get(key)) == normalized]
        if filters.get("critical") is not None:
            items = [item for item in items if item.get("critical") is filters["critical"]]
        return sorted(items, key=lambda item: (not item.get("critical"), self._severity_rank(item.get("severity")), self._sort_time(item.get("created_at"))))

    async def update_gap(self, gap_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require(KNOWLEDGE_GAP_COLLECTION, gap_id, "Knowledge gap")
        allowed = {"gap_status", "owner", "due_date", "resolution_notes", "metadata"}
        updates = {key: value for key, value in payload_dict(payload).items() if key in allowed}
        if updates.get("gap_status") in {"resolved", "accepted_gap", "not_applicable"}:
            updates["resolved_at"] = datetime.now(timezone.utc)
        updated = await self.db.collection(KNOWLEDGE_GAP_COLLECTION).update_one({"id": existing["id"]}, updates)
        await self._audit("airline_service_coverage.gap_reviewed", existing["id"], user, {"gap_status": updates.get("gap_status")})
        return {"phase": PHASE_LABEL, "gap": updated, **self.safety_flags()}

    async def list_remediation_plans(self, agency_id: str | None = None, assessment_id: str | None = None, plan_status: str | None = None) -> list[dict[str, Any]]:
        items = await self.db.collection(REMEDIATION_PLAN_COLLECTION).find_many()
        if agency_id is not None:
            items = [item for item in items if item.get("agency_id") == agency_id]
        if assessment_id:
            items = [item for item in items if item.get("assessment_id") == assessment_id]
        if plan_status:
            items = [item for item in items if item.get("plan_status") == self._code(plan_status)]
        return sorted(items, key=lambda item: (self._priority_rank(item.get("priority")), self._sort_time(item.get("due_date"))))

    async def create_remediation_plan(self, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        assessment = await self._require(COVERAGE_ASSESSMENT_COLLECTION, str(data.get("assessment_id") or ""), "Coverage assessment")
        data.setdefault("agency_id", assessment.get("agency_id"))
        data.setdefault("remediation_plan_reference", self._reference("ACR"))
        plan = AirlineCoverageRemediationPlan(**data)
        created = await self.db.collection(REMEDIATION_PLAN_COLLECTION).insert_one(plan.model_dump(mode="json"))
        await self._audit("airline_service_coverage.remediation_plan_created", created["id"], user, {"gap_count": len(created.get("gap_ids") or [])})
        return {"phase": PHASE_LABEL, "remediation_plan": created, **self.safety_flags()}

    async def update_remediation_plan(self, plan_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require(REMEDIATION_PLAN_COLLECTION, plan_id, "Remediation plan")
        allowed = {"plan_status", "priority", "gap_ids", "remediation_actions", "owner", "due_date", "progress_percent", "blockers", "warnings", "notes", "metadata"}
        updates = {key: value for key, value in payload_dict(payload).items() if key in allowed}
        updated = await self.db.collection(REMEDIATION_PLAN_COLLECTION).update_one({"id": existing["id"]}, updates)
        await self._audit("airline_service_coverage.remediation_plan_updated", existing["id"], user, {"fields": sorted(updates)})
        return {"phase": PHASE_LABEL, "remediation_plan": updated, **self.safety_flags()}

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        assessment_id = filters.get("assessment_id")
        assessments = await self.list_assessments(filters.get("agency_id"))
        if not assessment_id and assessments:
            assessment_id = assessments[0]["id"]
        cell_filters = {**filters, "assessment_id": assessment_id} if assessment_id else filters
        cells = await self.list_cells(**cell_filters)
        gaps = await self.list_gaps(**{key: value for key, value in filters.items() if key in {"agency_id", "airline_code", "service_family", "service_code", "gap_type", "gap_status", "severity", "critical"}}, assessment_id=assessment_id)
        profiles = await self.db.collection(COVERAGE_PROFILE_COLLECTION).find_many({"assessment_id": assessment_id}) if assessment_id else []
        plans = await self.list_remediation_plans(filters.get("agency_id"), assessment_id)
        return {
            "phase": PHASE_LABEL,
            "assessment_id": assessment_id,
            "profiles": profiles,
            "cells": cells,
            "gaps": gaps,
            "remediation_plans": plans,
            "summary": self._summary(cells, gaps, profiles),
            "filters": self.filter_metadata(),
            "read_only": False,
            "notice": "Coverage is a deterministic governance projection over existing knowledge. It does not publish, execute rules, or alter recommendations or offers.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        cells = await self.list_cells(**{key: value for key, value in filters.items() if key in {"service_family", "service_code", "coverage_status", "route_type", "flight_type", "cabin", "fare_bundle", "distribution_channel", "evidence_freshness"}})
        scoped = [item for item in cells if item.get("agency_id") in {None, agency_id}]
        latest_all = self._latest_cells(scoped)
        visible_all = [self._agency_cell_projection(item) for item in latest_all if item.get("published") and self._cell_visible_to_agency(item, agency_id)]
        usable_all = [item for item in visible_all if item.get("operational_ready")]
        requested_airline = self._airline(filters.get("airline_code")) if filters.get("airline_code") else None
        latest = [item for item in latest_all if not requested_airline or self._airline(item.get("airline_code")) == requested_airline]
        visible = [item for item in visible_all if not requested_airline or self._airline(item.get("airline_code")) == requested_airline]
        usable = [item for item in usable_all if not requested_airline or self._airline(item.get("airline_code")) == requested_airline]
        warnings = [
            {
                "airline_code": item.get("airline_code"),
                "service_family": item.get("service_family"),
                "service_code": item.get("service_code"),
                "warning_status": "missing_or_unknown",
                "message": "Published operational coverage is unavailable or requires manual review for this scope.",
            }
            for item in latest
            if not (item.get("published") and item.get("operational_ready") and self._cell_visible_to_agency(item, agency_id))
        ]
        hints = await self._alternative_airline_hints(agency_id, usable_all, filters.get("service_family"), filters.get("airline_code"))
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "cells": visible,
            "usable_cells": usable,
            "warnings": warnings,
            "alternative_airline_hints": hints,
            "summary": {
                "published_cell_count": len(visible),
                "operationally_usable_cell_count": len(usable),
                "missing_or_unknown_warning_count": len(warnings),
                "airline_count": len({item.get("airline_code") for item in visible}),
                "service_family_count": len({item.get("service_family") for item in visible}),
            },
            "filters": self.filter_metadata(),
            "read_only": True,
            "notice": "Only published airline service coverage is shown. Missing or unknown scopes require human review; unpublished draft knowledge and restricted evidence are excluded.",
            **self.safety_flags(),
        }

    async def coverage(self) -> dict[str, Any]:
        profiles = await self.db.collection(COVERAGE_PROFILE_COLLECTION).find_many()
        cells = await self.db.collection(COVERAGE_CELL_COLLECTION).find_many()
        gaps = await self.db.collection(KNOWLEDGE_GAP_COLLECTION).find_many()
        assessments = await self.db.collection(COVERAGE_ASSESSMENT_COLLECTION).find_many()
        plans = await self.db.collection(REMEDIATION_PLAN_COLLECTION).find_many()
        return {
            "coverage_profile_count": len(profiles),
            "coverage_cell_count": len(cells),
            "coverage_assessment_count": len(assessments),
            "knowledge_gap_count": len(gaps),
            "critical_knowledge_gap_count": len([gap for gap in gaps if gap.get("critical")]),
            "operational_ready_coverage_cell_count": len([cell for cell in cells if cell.get("operational_ready")]),
            "published_coverage_cell_count": len([cell for cell in cells if cell.get("published")]),
            "remediation_plan_count": len(plans),
            "coverage_status_counts": self._counts(cells, "coverage_status"),
            "gap_type_counts": self._counts(gaps, "gap_type"),
        }

    async def _load_sources(self, agency_id: str | None) -> dict[str, list[dict[str, Any]]]:
        loaded: dict[str, list[dict[str, Any]]] = {}
        for key, collection in SOURCE_COLLECTIONS.items():
            records = await self.db.collection(collection).find_many()
            loaded[key] = [record for record in records if not record.get("archived") and self._agency_source_visible(record, agency_id)]
        loaded["distribution"] = [
            *loaded["distribution"],
            *loaded["distribution_channels"],
            *loaded["distribution_capabilities"],
        ]
        return loaded

    def _assess_cell(
        self,
        *,
        assessment_id: str,
        agency_id: str | None,
        airline_code: str,
        service_family: str,
        service_code: str | None,
        dimension: dict[str, Any],
        sources: dict[str, list[dict[str, Any]]],
        minimum_scores: dict[str, int],
        required_gap_free: set[str],
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        matched: dict[str, list[dict[str, Any]]] = {}
        for source_type in ["policies", "pricing", "rules", "normalisations", "capabilities", "evidence_assertions", "qa_reviews", "publications", "scenarios", "distribution", "service_instructions"]:
            matched[source_type] = [
                record
                for record in sources[source_type]
                if self._airline_matches(record, airline_code, source_type)
                and (source_type == "distribution" or self._service_matches(record, service_family, service_code, source_type))
                and self._dimension_matches(record, dimension, source_type)
            ]

        assertion_ids = {item["id"] for item in matched["evidence_assertions"]}
        source_ids = {item.get("source_id") for item in matched["evidence_assertions"] if item.get("source_id")}
        conflicts = [
            item
            for item in sources["evidence_conflicts"]
            if self._airline_matches(item, airline_code, "evidence_conflicts")
            and set(item.get("assertion_ids") or []) & assertion_ids
            and item.get("status") in {"detected", "under_review", "unresolved"}
        ]
        freshness_records = [
            item
            for item in sources["evidence_freshness"]
            if item.get("assertion_id") in assertion_ids or item.get("source_id") in source_ids
        ]
        evidence_sources = [item for item in sources["evidence_sources"] if item.get("id") in source_ids]

        policies = matched["policies"]
        pricing = matched["pricing"]
        rules = matched["rules"]
        normalisations = matched["normalisations"]
        capabilities = matched["capabilities"]
        assertions = matched["evidence_assertions"]
        qa_reviews = matched["qa_reviews"]
        publications = matched["publications"]
        scenarios = matched["scenarios"]
        instructions = matched["service_instructions"]

        policy_present = bool(policies)
        pricing_present = bool(pricing)
        rule_present = bool(rules)
        evidence_present = bool(assertions or any(item.get("evidence_links") for item in policies + pricing + rules) or any(item.get("evidence_reference_ids") for item in capabilities))
        normalized_present = bool(normalisations)
        scenario_present = bool(scenarios)
        scenario_passed = any(self._code(item.get("test_status")) in {"reviewed", "approved"} for item in scenarios)
        qa_failed = any(
            self._code(item.get("qa_status")) in {"blocked", "changes_requested"}
            or self._code(item.get("severity")) in {"critical", "blocking"}
            or any(self._code(issue.get("severity")) in {"critical", "blocking"} for issue in item.get("issues") or [])
            for item in qa_reviews
        )
        qa_passed = bool(qa_reviews) and not qa_failed and any(
            self._code(item.get("qa_status")) in {"resolved", "recommended_for_approval"}
            or self._code(item.get("approval_recommendation")) == "ready_for_human_approval"
            for item in qa_reviews
        )
        published_publications = [item for item in publications if self._code(item.get("publication_status")) == "published" and item.get("AOIE_ready") is True]
        approved_publications = [item for item in publications if self._code(item.get("publication_status")) in {"qa_approved", "approved", "scheduled"}]
        published = bool(published_publications)
        approved_knowledge = bool(approved_publications) or any(self._code(item.get("status") or item.get("formula_status") or item.get("lifecycle_status")) in {"approved", "qa_approved"} for item in policies + pricing + rules)
        visibility_status, visible_agencies = self._publication_visibility(published_publications)
        evidence_freshness, freshness_score = self._freshness(freshness_records, evidence_sources)
        unresolved_conflict = bool(conflicts)
        documents_defined = any(bool(item.get("required_documents")) for item in policies) or any(item.get("document_required") is not None for item in capabilities)
        approval_defined = any(bool(item.get("approval_requirements")) for item in policies) or any(item.get("approval_required") is not None for item in capabilities)
        client_message_defined = any(bool(item.get("client_messages")) for item in policies) or any(bool(item.get("client_message")) for item in rules)
        internal_instruction_defined = bool(instructions) or any(bool(item.get("internal_message")) for item in rules)
        distribution_known = bool(matched["distribution"]) or bool(dimension.get("distribution_channel")) or any(bool(item.get("distribution_channel")) for item in assertions)
        effective_from, effective_until = self._effective_window(policies + pricing + rules + assertions + capabilities + publications)
        effective_defined = bool(effective_from or effective_until)

        source_ids_by_type = {
            key: self._unique(self._reference(item) for item in values)
            for key, values in {
                **matched,
                "evidence_conflicts": conflicts,
                "evidence_freshness": freshness_records,
            }.items()
            if values
        }
        source_counts = {key: len(value) for key, value in source_ids_by_type.items()}

        gap_types: list[str] = []
        if not policy_present:
            gap_types.append("missing_policy")
        if not pricing_present:
            gap_types.append("missing_pricing")
        if not rule_present:
            gap_types.append("missing_rule")
        if not evidence_present:
            gap_types.append("missing_evidence")
        if evidence_freshness in {"stale", "expired"}:
            gap_types.append("stale_evidence")
        if unresolved_conflict:
            gap_types.append("unresolved_conflict")
        if (policy_present or pricing_present or rule_present or evidence_present) and not effective_defined:
            gap_types.append("missing_effective_date")
        if service_family in DOCUMENT_SENSITIVE_FAMILIES and not documents_defined:
            gap_types.append("missing_documents")
        if service_family in APPROVAL_SENSITIVE_FAMILIES and not approval_defined:
            gap_types.append("missing_approval_requirements")
        if not client_message_defined:
            gap_types.append("missing_client_message")
        if not internal_instruction_defined:
            gap_types.append("missing_internal_instruction")
        if not scenario_passed:
            gap_types.append("missing_scenario_test")
        if qa_failed:
            gap_types.append("failed_qa")
        if (policy_present or pricing_present or rule_present or normalized_present or evidence_present) and not published:
            gap_types.append("unpublished")
        if not distribution_known:
            gap_types.append("unknown_distribution_scope")
        gap_types = self._unique(gap_types)

        completeness_score = self._completeness_score(
            policy_present,
            pricing_present,
            rule_present,
            evidence_present,
            normalized_present,
            documents_defined or service_family not in DOCUMENT_SENSITIVE_FAMILIES,
            approval_defined or service_family not in APPROVAL_SENSITIVE_FAMILIES,
            client_message_defined,
            internal_instruction_defined,
            effective_defined,
            distribution_known,
        )
        confidence_score = self._confidence_score(assertions, capabilities, unresolved_conflict)
        test_score = self._test_score(scenarios)
        publication_score = self._publication_score(qa_passed, qa_failed, bool(approved_publications), published)
        usability = round(
            completeness_score * 0.35
            + confidence_score * 0.20
            + freshness_score * 0.15
            + test_score * 0.15
            + publication_score * 0.15
        )
        critical_gaps = [gap for gap in gap_types if gap in CRITICAL_GAP_TYPES or gap in required_gap_free]
        if critical_gaps:
            usability = min(usability, 49)
        scores = {
            "completeness": completeness_score,
            "confidence": confidence_score,
            "freshness": freshness_score,
            "test_coverage": test_score,
            "publication_readiness": publication_score,
            "operational_usability": usability,
        }
        operational_ready = not critical_gaps and all(scores[key] >= int(minimum_scores.get(key, 0)) for key in DEFAULT_MINIMUM_SCORES)
        coverage_status = self._coverage_status(
            policy_present=policy_present,
            pricing_present=pricing_present,
            rule_present=rule_present,
            evidence_present=evidence_present,
            normalized_present=normalized_present,
            scenario_passed=scenario_passed,
            qa_failed=qa_failed,
            unresolved_conflict=unresolved_conflict,
            evidence_freshness=evidence_freshness,
            published=published,
            approved_knowledge=approved_knowledge,
            operational_ready=operational_ready,
        )

        cell_reference = self._reference("ACC")
        cell_data = {
            "coverage_cell_reference": cell_reference,
            "agency_id": agency_id,
            "assessment_id": assessment_id,
            "canonical_airline_id": self._canonical_airline_id(airline_code, sources),
            "airline_code": airline_code,
            "service_family": service_family,
            "service_code": service_code,
            **dimension,
            "effective_from": effective_from,
            "effective_until": effective_until,
            "evidence_freshness": evidence_freshness,
            "coverage_status": coverage_status,
            "policy_present": policy_present,
            "pricing_present": pricing_present,
            "rule_present": rule_present,
            "evidence_present": evidence_present,
            "normalized_knowledge_present": normalized_present,
            "scenario_test_present": scenario_present,
            "scenario_test_passed": scenario_passed,
            "qa_passed": qa_passed,
            "published": published,
            "approved_unpublished": approved_knowledge and not published,
            "agency_visibility_status": visibility_status,
            "visible_agency_ids": visible_agencies,
            "unresolved_conflict": unresolved_conflict,
            "documents_defined": documents_defined,
            "approval_requirements_defined": approval_defined,
            "client_message_defined": client_message_defined,
            "internal_instruction_defined": internal_instruction_defined,
            "distribution_scope_known": distribution_known,
            "completeness_score": completeness_score,
            "confidence_score": confidence_score,
            "freshness_score": freshness_score,
            "test_coverage_score": test_score,
            "publication_readiness_score": publication_score,
            "operational_usability_score": usability,
            "operational_ready": operational_ready,
            "critical_gap_types": critical_gaps,
            "source_reference_counts": source_counts,
            "source_reference_ids": source_ids_by_type,
            "metadata": {"minimum_scores": minimum_scores, "critical_gap_guard_applied": bool(critical_gaps)},
        }
        gap_specs = [
            self._gap_spec(
                assessment_id=assessment_id,
                agency_id=agency_id,
                canonical_airline_id=cell_data["canonical_airline_id"],
                airline_code=airline_code,
                service_family=service_family,
                service_code=service_code,
                gap_type=gap_type,
                source_reference_ids=self._unique(value for values in source_ids_by_type.values() for value in values),
            )
            for gap_type in gap_types
        ]
        return cell_data, gap_specs

    def _gap_spec(self, **data: Any) -> dict[str, Any]:
        gap_type = data["gap_type"]
        critical = gap_type in CRITICAL_GAP_TYPES
        severity = "critical" if gap_type in {"unresolved_conflict", "failed_qa"} else "high" if critical else "medium"
        label = gap_type.replace("_", " ")
        return {
            **data,
            "gap_reference": self._reference("AKG"),
            "coverage_cell_id": "pending",
            "gap_status": "open",
            "severity": severity,
            "critical": critical,
            "title": label.title(),
            "description": f"{data['airline_code']} {data['service_family']} coverage has {label}.",
            "remediation_guidance": GAP_GUIDANCE[gap_type],
        }

    def _profile_data(
        self,
        assessment_id: str,
        agency_id: str | None,
        airline_code: str,
        cells: list[dict[str, Any]],
        gaps: list[dict[str, Any]],
        toolkit_ids: list[str],
        pilot_ids: list[str],
    ) -> dict[str, Any]:
        score_summary = self._aggregate_scores(cells)
        state_counts = self._counts(cells, "coverage_status")
        ready = len([cell for cell in cells if cell.get("operational_ready")])
        coverage_status = "complete_published_knowledge" if cells and ready == len(cells) else "no_knowledge" if all(cell.get("coverage_status") == "no_knowledge" for cell in cells) else "partial_knowledge"
        return {
            "coverage_profile_reference": self._reference("ACP"),
            "agency_id": agency_id,
            "assessment_id": assessment_id,
            "canonical_airline_id": next((cell.get("canonical_airline_id") for cell in cells if cell.get("canonical_airline_id")), None),
            "airline_code": airline_code,
            "coverage_status": coverage_status,
            "service_family_count": len({cell.get("service_family") for cell in cells}),
            "coverage_cell_count": len(cells),
            "operational_ready_cell_count": ready,
            "critical_gap_count": len([gap for gap in gaps if gap.get("critical")]),
            "gap_count": len(gaps),
            "coverage_state_counts": state_counts,
            "completeness_score": score_summary["completeness"],
            "confidence_score": score_summary["confidence"],
            "freshness_score": score_summary["freshness"],
            "test_coverage_score": score_summary["test_coverage"],
            "publication_readiness_score": score_summary["publication_readiness"],
            "operational_usability_score": score_summary["operational_usability"],
            "population_toolkit_ids": toolkit_ids,
            "pilot_readiness_assessment_ids": pilot_ids,
        }

    async def _create_generated_remediation_plan(
        self,
        assessment: dict[str, Any],
        profile: dict[str, Any],
        gaps: list[dict[str, Any]],
        toolkit_ids: list[str],
        user: dict[str, Any],
    ) -> dict[str, Any]:
        critical = [gap for gap in gaps if gap.get("critical")]
        actions = [
            {
                "gap_id": gap["id"],
                "gap_type": gap["gap_type"],
                "priority": gap["severity"],
                "action": gap.get("remediation_guidance"),
                "status": "not_started",
            }
            for gap in sorted(gaps, key=lambda item: (not item.get("critical"), self._severity_rank(item.get("severity"))))
        ]
        plan = AirlineCoverageRemediationPlan(
            remediation_plan_reference=self._reference("ACR"),
            agency_id=assessment.get("agency_id"),
            assessment_id=assessment["id"],
            profile_id=profile["id"],
            airline_code=profile["airline_code"],
            plan_status="open",
            priority="critical" if critical else "medium",
            gap_ids=[gap["id"] for gap in gaps],
            remediation_actions=actions,
            population_toolkit_id=toolkit_ids[0] if toolkit_ids else None,
            owner=user.get("email") or user.get("id"),
            blockers=[gap["title"] for gap in critical],
            warnings=[gap["title"] for gap in gaps if not gap.get("critical")],
        )
        return await self.db.collection(REMEDIATION_PLAN_COLLECTION).insert_one(plan.model_dump(mode="json"))

    async def _sync_population_toolkits(
        self,
        profile: dict[str, Any],
        cells: list[dict[str, Any]],
        gaps: list[dict[str, Any]],
        toolkits: list[dict[str, Any]],
        user: dict[str, Any],
    ) -> int:
        matched = [item for item in toolkits if item.get("id") in set(profile.get("population_toolkit_ids") or [])]
        updated_count = 0
        for toolkit in matched:
            critical = [gap for gap in gaps if gap.get("critical")]
            payload = KnowledgePopulationToolkitUpdate(
                coverage_summary={
                    "coverage_assessment_id": profile["assessment_id"],
                    "coverage_status": profile["coverage_status"],
                    "operational_usability_score": profile["operational_usability_score"],
                    "operational_ready_cells": profile["operational_ready_cell_count"],
                    "coverage_cells": profile["coverage_cell_count"],
                    "critical_gaps": profile["critical_gap_count"],
                },
                service_family_coverage=[
                    {
                        "service_family": family,
                        "cell_count": len([cell for cell in cells if cell.get("service_family") == family]),
                        "operational_ready_count": len([cell for cell in cells if cell.get("service_family") == family and cell.get("operational_ready")]),
                        "score": round(sum(cell.get("operational_usability_score", 0) for cell in cells if cell.get("service_family") == family) / max(1, len([cell for cell in cells if cell.get("service_family") == family]))),
                    }
                    for family in sorted({str(cell.get("service_family")) for cell in cells})
                ],
                evidence_coverage={"score": profile["confidence_score"], "freshness_score": profile["freshness_score"]},
                pricing_coverage={"covered_cells": len([cell for cell in cells if cell.get("pricing_present")]), "total_cells": len(cells)},
                capability_coverage={"covered_cells": len([cell for cell in cells if (cell.get("source_reference_counts") or {}).get("capabilities")]), "total_cells": len(cells)},
                QA_status="blocked" if any(gap.get("gap_type") == "failed_qa" for gap in critical) else "ready" if not critical else "needs_review",
                publishing_status="ready" if all(cell.get("published") for cell in cells) else "needs_review",
                scenario_test_status="ready" if all(cell.get("scenario_test_passed") for cell in cells) else "needs_review",
                population_progress={"coverage_score": profile["operational_usability_score"], "assessment_id": profile["assessment_id"]},
                missing_domains=sorted({gap["gap_type"] for gap in gaps}),
                blockers=[{"gap_id": gap["id"], "gap_type": gap["gap_type"], "title": gap["title"]} for gap in critical],
                warnings=[{"gap_id": gap["id"], "gap_type": gap["gap_type"], "title": gap["title"]} for gap in gaps if not gap.get("critical")],
                next_actions=[{"gap_id": gap["id"], "action": gap.get("remediation_guidance")} for gap in gaps[:20]],
            )
            await KnowledgePopulationToolkitService(self.db).update_toolkit(toolkit["id"], payload, user)
            updated_count += 1
        return updated_count

    async def _alternative_airline_hints(
        self,
        agency_id: str,
        usable_cells: list[dict[str, Any]],
        service_family: str | None,
        excluded_airline: str | None,
    ) -> list[dict[str, Any]]:
        target_family = self._code(service_family) if service_family else None
        excluded = self._airline(excluded_airline) if excluded_airline else None
        candidates = [
            cell
            for cell in usable_cells
            if (not target_family or self._code(cell.get("service_family")) == target_family)
            and (not excluded or self._airline(cell.get("airline_code")) != excluded)
        ]
        recommendations = await self.db.collection("airline_recommendations").find_many()
        recommendations = [
            item
            for item in recommendations
            if item.get("agency_id") in {None, agency_id}
            and self._code(item.get("recommendation_status")) == "ready"
            and item.get("recommendation_ready") is True
        ]
        hints: list[dict[str, Any]] = []
        for airline_code in sorted({str(item.get("airline_code")) for item in candidates}):
            cells = [item for item in candidates if item.get("airline_code") == airline_code]
            recommendation = next((item for item in recommendations if self._airline(item.get("airline_code")) == airline_code), None)
            hints.append(
                {
                    "airline_code": airline_code,
                    "service_families": sorted({str(item.get("service_family")) for item in cells}),
                    "operational_usability_score": max(item.get("operational_usability_score", 0) for item in cells),
                    "recommendation_reference": (recommendation or {}).get("recommendation_reference"),
                    "recommendation_level": (recommendation or {}).get("recommendation_level"),
                    "advisory_only": True,
                    "message": "Published coverage is available. Use the existing recommendation workflow for passenger-specific evaluation.",
                }
            )
        return sorted(hints, key=lambda item: item["operational_usability_score"], reverse=True)

    def _coverage_status(self, **signals: bool | str) -> str:
        any_knowledge = any(signals[key] for key in ["policy_present", "pricing_present", "rule_present", "evidence_present", "normalized_present"])
        if not any_knowledge:
            return "no_knowledge"
        if signals["qa_failed"]:
            return "failed_qa"
        if signals["unresolved_conflict"]:
            return "conflicting_knowledge"
        if signals["evidence_freshness"] in {"stale", "expired"}:
            return "stale_knowledge"
        if signals["policy_present"] and not signals["pricing_present"]:
            return "policy_without_pricing"
        if signals["pricing_present"] and not signals["policy_present"]:
            return "pricing_without_policy"
        if signals["rule_present"] and not signals["evidence_present"]:
            return "rules_without_evidence"
        if signals["evidence_present"] and not signals["normalized_present"]:
            return "evidence_without_normalized_knowledge"
        if any_knowledge and not signals["scenario_passed"]:
            return "knowledge_without_scenario_tests"
        if signals["approved_knowledge"] and not signals["published"]:
            return "unpublished_approved_knowledge"
        if signals["published"] and signals["operational_ready"]:
            return "complete_published_knowledge"
        return "partial_knowledge"

    def _completeness_score(self, *signals: bool) -> int:
        weights = [18, 12, 15, 15, 10, 5, 5, 5, 5, 5, 5]
        return sum(weight for weight, signal in zip(weights, signals) if signal)

    def _confidence_score(self, assertions: list[dict[str, Any]], capabilities: list[dict[str, Any]], conflict: bool) -> int:
        values = [CONFIDENCE_SCORES.get(self._code(item.get("confidence")), 20) for item in assertions]
        values.extend(CONFIDENCE_SCORES.get(self._code(item.get("capability_confidence") or item.get("evidence_confidence_level")), 20) for item in capabilities)
        score = round(sum(values) / len(values)) if values else 0
        return max(0, score - (30 if conflict else 0))

    def _freshness(self, assessments: list[dict[str, Any]], sources: list[dict[str, Any]]) -> tuple[str, int]:
        statuses = [self._code(item.get("freshness_status")) for item in assessments if item.get("freshness_status")]
        today = datetime.now(timezone.utc).date()
        for source in sources:
            expiry = self._date(source.get("expiry_date") or source.get("effective_to"))
            review_due = self._date(source.get("review_due_date"))
            if expiry and expiry < today:
                statuses.append("expired")
            elif review_due and review_due < today:
                statuses.append("stale")
        if not statuses:
            return "unknown", FRESHNESS_SCORES["unknown"]
        status = min(statuses, key=lambda value: FRESHNESS_SCORES.get(value, 40))
        return status, FRESHNESS_SCORES.get(status, 40)

    def _test_score(self, scenarios: list[dict[str, Any]]) -> int:
        statuses = {self._code(item.get("test_status")) for item in scenarios}
        if "approved" in statuses:
            return 100
        if "reviewed" in statuses:
            return 90
        if "ready_for_review" in statuses:
            return 60
        if "needs_update" in statuses:
            return 20
        return 10 if scenarios else 0

    def _publication_score(self, qa_passed: bool, qa_failed: bool, approved: bool, published: bool) -> int:
        if qa_failed:
            return 0
        return min(100, (30 if qa_passed else 0) + (30 if approved else 0) + (70 if published else 0))

    def _effective_window(self, records: list[dict[str, Any]]) -> tuple[date | None, date | None]:
        starts = [value for value in (self._date(item.get("effective_from")) for item in records) if value]
        ends = [value for value in (self._date(item.get("effective_to") or item.get("effective_until")) for item in records) if value]
        return (max(starts) if starts else None, min(ends) if ends else None)

    def _publication_visibility(self, publications: list[dict[str, Any]]) -> tuple[str, list[str]]:
        statuses: list[str] = []
        agency_ids: list[str] = []
        for item in publications:
            visibility = item.get("agency_visibility") or {}
            status = self._code(visibility.get("visibility_status") or visibility.get("status") or "platform_only")
            statuses.append(status)
            agency_ids.extend(visibility.get("agency_ids") or [])
        if "all_agencies" in statuses:
            return "all_agencies", []
        if "selected_agencies" in statuses:
            return "selected_agencies", self._unique(agency_ids)
        return (statuses[0] if statuses else "platform_only"), self._unique(agency_ids)

    def _cell_visible_to_agency(self, cell: dict[str, Any], agency_id: str) -> bool:
        if cell.get("agency_id") not in {None, agency_id}:
            return False
        status = self._code(cell.get("agency_visibility_status"))
        return status == "all_agencies" or (status == "selected_agencies" and agency_id in set(cell.get("visible_agency_ids") or []))

    def _agency_cell_projection(self, cell: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "id", "coverage_cell_reference", "airline_code", "service_family", "service_code", "route_type", "flight_type",
            "cabin", "fare_bundle", "operating_carrier", "marketing_carrier", "aircraft_family", "country_scope", "airport_scope",
            "distribution_channel", "effective_from", "effective_until", "evidence_freshness", "coverage_status", "completeness_score",
            "confidence_score", "freshness_score", "test_coverage_score", "publication_readiness_score", "operational_usability_score",
            "operational_ready", "documents_defined", "approval_requirements_defined", "updated_at", "assessed_at",
        }
        return {key: value for key, value in cell.items() if key in allowed}

    def _latest_cells(self, cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
        latest: dict[tuple[Any, ...], dict[str, Any]] = {}
        for cell in sorted(cells, key=lambda item: self._sort_time(item.get("assessed_at") or item.get("created_at"))):
            key = tuple(cell.get(field) for field in ["airline_code", "service_family", "service_code", "route_type", "flight_type", "cabin", "fare_bundle", "operating_carrier", "marketing_carrier", "aircraft_family", "distribution_channel"])
            latest[key] = cell
        return list(latest.values())

    def _service_codes_for(self, family: str, requested_codes: list[str]) -> list[str | None]:
        catalog = next((item for item in SERVICE_COVERAGE_CATALOG if item["service_family"] == family), None)
        defined = list((catalog or {}).get("service_codes") or [])
        if requested_codes:
            selected = [code for code in defined if code in requested_codes]
            if selected:
                return selected
            if family in {self._family_for_code(code) for code in requested_codes}:
                return [code for code in requested_codes if self._family_for_code(code) == family]
        return defined or [None]

    def _canonical_families(self, values: list[Any]) -> list[str]:
        if not values:
            return []
        families: list[str] = []
        for raw in values:
            value = self._code(raw)
            matched = [
                item["service_family"]
                for item in SERVICE_COVERAGE_CATALOG
                if value == item["service_family"]
                or value in {self._code(alias) for alias in item.get("aliases") or []}
                or value.upper() in set(item.get("service_codes") or [])
            ]
            families.extend(matched or [value])
        return self._unique(families)

    def _family_for_code(self, service_code: str) -> str | None:
        code = str(service_code or "").upper()
        return next((item["service_family"] for item in SERVICE_COVERAGE_CATALOG if code in item.get("service_codes") or []), None)

    def _service_aliases(self, service_family: str, service_code: str | None) -> set[str]:
        catalog = next((item for item in SERVICE_COVERAGE_CATALOG if item["service_family"] == service_family), {})
        values = [service_family, service_code, *(catalog.get("aliases") or []), *(catalog.get("service_codes") or [])]
        return {self._code(value) for value in values if value}

    def _service_matches(self, record: dict[str, Any], family: str, service_code: str | None, source_type: str) -> bool:
        aliases = self._service_aliases(family, service_code)
        values: list[Any] = [record.get("service_family"), record.get("policy_family"), record.get("rule_family"), record.get("service_domain"), record.get("service_variant"), record.get("scenario_family"), record.get("assertion_key"), record.get("assertion_type")]
        values.extend(record.get("service_codes") or [])
        values.extend(record.get("service_families") or [])
        values.extend([item.get("code") for item in record.get("service_requirements") or [] if isinstance(item, dict)])
        normalized = {self._code(value) for value in values if value}
        if normalized & aliases:
            return True
        return any(alias and any(alias in value or value in alias for value in normalized) for alias in aliases)

    def _airline_matches(self, record: dict[str, Any], airline_code: str, source_type: str) -> bool:
        values: list[Any] = [
            record.get("airline"), record.get("airline_code"), record.get("canonical_airline_id"), record.get("operating_carrier"),
            record.get("marketing_carrier"), record.get("validating_carrier"), record.get("carrier"),
        ]
        values.extend(record.get("airline_codes") or [])
        for nested_key in ["airline_context", "applies_to", "metadata"]:
            nested = record.get(nested_key) or {}
            if isinstance(nested, dict):
                values.extend([nested.get("airline"), nested.get("airline_code"), nested.get("canonical_airline_id")])
                values.extend(nested.get("airline_codes") or [])
                values.extend(nested.get("airlines") or [])
        return airline_code in {self._airline(value) for value in values if value}

    def _dimension_matches(self, record: dict[str, Any], dimension: dict[str, Any], source_type: str) -> bool:
        mappings = {
            "route_type": ["route_type"],
            "flight_type": ["flight_type"],
            "cabin": ["cabin", "cabin_family", "cabin_name"],
            "fare_bundle": ["fare_bundle"],
            "operating_carrier": ["operating_carrier"],
            "marketing_carrier": ["marketing_carrier"],
            "aircraft_family": ["aircraft_family"],
            "distribution_channel": ["distribution_channel"],
        }
        for dimension_key, record_keys in mappings.items():
            expected = dimension.get(dimension_key)
            if not expected:
                continue
            present = [record.get(key) for key in record_keys if record.get(key)]
            if present and self._code(expected) not in {self._code(value) for value in present}:
                return False
        return True

    def _normalize_dimension(self, dimension: Any) -> dict[str, Any]:
        source = dict(dimension or {})
        normalized: dict[str, Any] = {}
        for key in ["route_type", "flight_type", "cabin", "fare_bundle", "aircraft_family", "distribution_channel"]:
            if source.get(key):
                normalized[key] = self._code(source[key])
        for key in ["operating_carrier", "marketing_carrier"]:
            if source.get(key):
                normalized[key] = self._airline(source[key])
        for key in ["country_scope", "airport_scope"]:
            values = source.get(key) or []
            normalized[key] = self._unique(self._airline(value) for value in values)
        return normalized

    def _canonical_airline_id(self, airline_code: str, sources: dict[str, list[dict[str, Any]]]) -> str | None:
        for source_type in ["capabilities", "evidence_assertions"]:
            record = next((item for item in sources[source_type] if self._airline_matches(item, airline_code, source_type) and item.get("canonical_airline_id")), None)
            if record:
                return str(record["canonical_airline_id"])
        return airline_code

    def _pilot_assessment_ids(self, airline_code: str, sources: dict[str, list[dict[str, Any]]]) -> list[str]:
        profile_ids = {
            item["id"]
            for item in sources["pilot_profiles"]
            if airline_code in {self._airline(value) for value in item.get("target_airline_codes") or []}
        }
        return [item["id"] for item in sources["pilot_assessments"] if item.get("profile_id") in profile_ids]

    def _summary(self, cells: list[dict[str, Any]], gaps: list[dict[str, Any]], profiles: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "airline_count": len({item.get("airline_code") for item in cells}),
            "service_family_count": len({item.get("service_family") for item in cells}),
            "profile_count": len(profiles),
            "cell_count": len(cells),
            "operational_ready_cell_count": len([item for item in cells if item.get("operational_ready")]),
            "published_cell_count": len([item for item in cells if item.get("published")]),
            "gap_count": len(gaps),
            "critical_gap_count": len([item for item in gaps if item.get("critical")]),
            "coverage_status_counts": self._counts(cells, "coverage_status"),
            "gap_type_counts": self._counts(gaps, "gap_type"),
            "score_summary": self._aggregate_scores(cells),
        }

    def _aggregate_scores(self, cells: list[dict[str, Any]]) -> dict[str, int]:
        fields = {
            "completeness": "completeness_score",
            "confidence": "confidence_score",
            "freshness": "freshness_score",
            "test_coverage": "test_coverage_score",
            "publication_readiness": "publication_readiness_score",
            "operational_usability": "operational_usability_score",
        }
        return {
            label: round(sum(int(item.get(field) or 0) for item in cells) / len(cells)) if cells else 0
            for label, field in fields.items()
        }

    def _counts(self, items: list[dict[str, Any]], field: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            value = str(item.get(field) or "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts

    def _agency_source_visible(self, record: dict[str, Any], agency_id: str | None) -> bool:
        owner = record.get("agency_id")
        return owner is None or (agency_id is not None and owner == agency_id)

    def _reference(self, record_or_prefix: Any) -> str:
        if isinstance(record_or_prefix, str):
            return f"{record_or_prefix}-{new_id()[:10].upper()}"
        record = record_or_prefix
        for key in ["card_reference", "formula_reference", "rule_reference", "canonical_reference", "capability_reference", "assertion_reference", "review_reference", "publication_reference", "scenario_reference", "distribution_reference", "id"]:
            if record.get(key):
                return str(record[key])
        return "unknown"

    def _airline(self, value: Any) -> str:
        return "".join(str(value or "").strip().upper().split())

    def _code(self, value: Any) -> str:
        return "_".join(str(value or "").strip().lower().replace("/", " ").replace("-", " ").split())

    def _unique(self, values: Any) -> list[str]:
        return list(dict.fromkeys(str(value) for value in values if value not in {None, ""}))

    def _date(self, value: Any) -> date | None:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if value:
            try:
                return date.fromisoformat(str(value)[:10])
            except ValueError:
                return None
        return None

    def _sort_time(self, value: Any) -> str:
        return str(value or "")

    def _severity_rank(self, value: Any) -> int:
        return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(self._code(value), 4)

    def _priority_rank(self, value: Any) -> int:
        return {"critical": 0, "urgent": 1, "high": 2, "medium": 3, "low": 4}.get(self._code(value), 5)

    def _cell_priority_key(self, item: dict[str, Any]) -> tuple[Any, ...]:
        return (item.get("operational_ready") is True, int(item.get("operational_usability_score") or 0), item.get("airline_code") or "", item.get("service_family") or "")

    async def _require(self, collection: str, record_id: str, label: str) -> dict[str, Any]:
        record = await self.db.collection(collection).find_one({"id": record_id})
        if not record:
            raise AirlineServiceCoverageGapError(f"{label} was not found.")
        return record

    async def _audit(self, event_type: str, entity_id: str, user: dict[str, Any], metadata: dict[str, Any]) -> None:
        event = AuditEvent(
            actor_user_id=user.get("id"),
            event_type=event_type,
            entity_type="airline_service_coverage",
            entity_id=entity_id,
            summary=event_type.replace(".", " ").replace("_", " ").title(),
            metadata=metadata,
        )
        await self.db.collection("audit_events").insert_one(event.model_dump(mode="json"))
