from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import (
    AirlineIntelligencePopulationWave,
    AirlineIntelligenceReadinessAssessment,
    AirlineIntelligenceReadinessCheck,
    AirlineIntelligenceReadinessProfile,
    AirlineIntelligenceReleaseCandidate,
    AirlineIntelligenceReleaseDecision,
    AirlineIntelligenceReleaseGate,
    AirlineIntelligenceScaleIssue,
    AuditEvent,
)


PHASE_LABEL = "phase_55_9_airline_intelligence_scale_release_readiness_foundation"

READINESS_PROFILE_COLLECTION = "airline_intelligence_readiness_profiles"
READINESS_ASSESSMENT_COLLECTION = "airline_intelligence_readiness_assessments"
READINESS_CHECK_COLLECTION = "airline_intelligence_readiness_checks"
RELEASE_CANDIDATE_COLLECTION = "airline_intelligence_release_candidates"
RELEASE_GATE_COLLECTION = "airline_intelligence_release_gates"
RELEASE_DECISION_COLLECTION = "airline_intelligence_release_decisions"
POPULATION_WAVE_COLLECTION = "airline_intelligence_population_waves"
SCALE_ISSUE_COLLECTION = "airline_intelligence_scale_issues"

SCALE_READINESS_COLLECTIONS = [
    READINESS_PROFILE_COLLECTION,
    READINESS_ASSESSMENT_COLLECTION,
    READINESS_CHECK_COLLECTION,
    RELEASE_CANDIDATE_COLLECTION,
    RELEASE_GATE_COLLECTION,
    RELEASE_DECISION_COLLECTION,
    POPULATION_WAVE_COLLECTION,
    SCALE_ISSUE_COLLECTION,
]

ASSESSMENT_STATUSES = [
    "not_started",
    "incomplete",
    "blocked",
    "needs_review",
    "conditionally_ready",
    "release_ready",
    "released",
    "suspended",
    "archived",
]
CHECK_STATUSES = ["passed", "warning", "blocked", "unknown", "not_applicable"]
GATE_STATUSES = ["pending", "passed", "warning", "blocked", "waived"]
DECISION_STATUSES = ["approved", "rejected", "released", "suspended", "rollback_required", "archived"]
WAVE_STATUSES = ["not_started", "planning", "in_progress", "blocked", "complete", "archived"]
ISSUE_STATUSES = ["open", "under_review", "resolved", "waived", "archived"]
ISSUE_SEVERITIES = ["low", "medium", "high", "critical"]

DIMENSION_CONFIG: list[dict[str, Any]] = [
    {"code": "master_profile", "label": "Airline master profile completeness", "critical": True, "weight": 8, "route": "/platform/airline-master-profiles", "agency_route": "/agency/airline-profiles"},
    {"code": "identity_aliases", "label": "Identity and alias integrity", "critical": True, "weight": 5, "route": "/platform/airline-master-profiles", "agency_route": "/agency/airline-profiles"},
    {"code": "evidence_coverage", "label": "Source and evidence coverage", "critical": True, "weight": 8, "route": "/platform/airline-evidence", "agency_route": "/agency/airline-evidence"},
    {"code": "conflict_status", "label": "Evidence conflict status", "critical": True, "weight": 7, "route": "/platform/airline-evidence", "agency_route": "/agency/airline-evidence"},
    {"code": "evidence_freshness", "label": "Evidence freshness", "critical": False, "weight": 5, "route": "/platform/airline-evidence", "agency_route": "/agency/airline-evidence"},
    {"code": "version_governance", "label": "Version and change governance", "critical": True, "weight": 6, "route": "/platform/knowledge-versions", "agency_route": "/agency/knowledge-updates"},
    {"code": "service_coverage", "label": "Required service-family coverage", "critical": True, "weight": 9, "route": "/platform/airline-service-coverage", "agency_route": "/agency/airline-service-coverage"},
    {"code": "pricing_coverage", "label": "Pricing coverage", "critical": False, "weight": 5, "route": "/platform/pricing-formula-builder", "agency_route": "/agency/pricing-formula-builder"},
    {"code": "operational_rule_coverage", "label": "Operational-rule coverage", "critical": False, "weight": 5, "route": "/platform/operational-rule-composer", "agency_route": "/agency/rule-composer"},
    {"code": "scenario_test_coverage", "label": "Scenario-test coverage", "critical": True, "weight": 7, "route": "/platform/operational-scenario-testing", "agency_route": "/agency/scenario-testing"},
    {"code": "distribution_capability", "label": "Distribution capability coverage", "critical": False, "weight": 5, "route": "/platform/airline-distribution-capabilities", "agency_route": "/agency/distribution-capabilities"},
    {"code": "interline_responsibility", "label": "Interline and codeshare responsibility coverage", "critical": False, "weight": 5, "route": "/platform/interline-codeshare-intelligence", "agency_route": "/agency/interline-codeshare-advisor"},
    {"code": "fare_brand_baggage", "label": "Fare-brand and baggage coverage", "critical": False, "weight": 5, "route": "/platform/fare-brand-intelligence", "agency_route": "/agency/fare-brand-library"},
    {"code": "contact_directory", "label": "Contact-directory coverage", "critical": False, "weight": 4, "route": "/platform/airline-contact-intelligence", "agency_route": "/agency/airline-contact-directory"},
    {"code": "qa_state", "label": "Knowledge QA state", "critical": True, "weight": 7, "route": "/platform/knowledge-quality-assurance", "agency_route": "/agency/knowledge-quality-assurance"},
    {"code": "publishing_state", "label": "Publishing state", "critical": False, "weight": 5, "route": "/platform/knowledge-publishing", "agency_route": "/agency/published-knowledge"},
    {"code": "agency_assignment", "label": "Agency assignment readiness", "critical": False, "weight": 3, "route": "/platform/airline-intelligence-agency-consumption", "agency_route": "/agency/airline-intelligence-consumption"},
    {"code": "operational_consumption", "label": "Operational consumption readiness", "critical": False, "weight": 6, "route": "/platform/airline-intelligence-agency-consumption", "agency_route": "/agency/airline-intelligence-consumption"},
]

RELEASE_GATE_CONFIG: list[dict[str, Any]] = [
    {"code": "canonical_identity_valid", "label": "Canonical identity valid", "dimension": "master_profile"},
    {"code": "evidence_minimum_met", "label": "Evidence minimum met", "dimension": "evidence_coverage"},
    {"code": "no_unresolved_critical_conflict", "label": "No unresolved critical conflict", "dimension": "conflict_status"},
    {"code": "required_service_coverage_met", "label": "Required service-family coverage met", "dimension": "service_coverage"},
    {"code": "qa_passed", "label": "QA passed", "dimension": "qa_state"},
    {"code": "scenario_tests_passed", "label": "Scenario tests passed", "dimension": "scenario_test_coverage"},
    {"code": "version_snapshot_created", "label": "Version snapshot created", "candidate_field": "version_snapshot_id"},
    {"code": "effective_dates_valid", "label": "Effective dates valid", "candidate_method": "effective_dates"},
    {"code": "client_internal_messages_separated", "label": "Published client and internal messages separated", "candidate_method": "message_separation"},
    {"code": "agency_consumption_payload_valid", "label": "Agency consumption payload valid", "candidate_method": "agency_payload"},
    {"code": "rollback_reference_available", "label": "Rollback reference available", "candidate_field": "rollback_reference"},
]

SOURCE_COLLECTIONS = {
    "airlines": "airline_profiles",
    "master_profiles": "airline_master_profiles",
    "aliases": "airline_identity_aliases",
    "assertions": "airline_evidence_assertions",
    "conflicts": "airline_evidence_conflicts",
    "freshness": "airline_evidence_freshness_assessments",
    "versions": "airline_knowledge_versions",
    "changes": "airline_knowledge_change_sets",
    "coverage": "airline_service_coverage_cells",
    "pricing": "pricing_formula_builders",
    "rules": "operational_rule_composer_rules",
    "scenarios": "operational_scenario_tests",
    "distribution": "airline_distribution_capabilities",
    "interline": "airline_service_responsibility_rules",
    "fare_families": "airline_fare_families",
    "baggage": "airline_baggage_allowance_rules",
    "contacts": "airline_contacts",
    "qa": "knowledge_quality_assurance_reviews",
    "publications": "airline_knowledge_publications",
    "assignments": "airline_intelligence_agency_consumption_profiles",
    "consumption": "airline_intelligence_agency_usage_readiness",
}

ASSESSMENT_TEMPLATES = [
    {"template_code": "fully_ready_petc_wchc_umnr", "name": "Fully ready airline with PETC, WCHC, and UMNR coverage", "expected_status": "release_ready", "service_families": ["PETC", "WCHC", "UMNR"]},
    {"template_code": "missing_evidence", "name": "Airline blocked by missing evidence", "expected_status": "blocked", "blocked_dimension": "evidence_coverage"},
    {"template_code": "unresolved_policy_conflict", "name": "Airline blocked by unresolved policy conflict", "expected_status": "blocked", "blocked_dimension": "conflict_status"},
    {"template_code": "profile_policy_no_pricing", "name": "Airline with profile and policy but no pricing", "expected_status": "conditionally_ready", "warning_dimension": "pricing_coverage"},
    {"template_code": "stale_contact", "name": "Airline with stale contact information", "expected_status": "conditionally_ready", "warning_dimension": "contact_directory"},
    {"template_code": "untested_interline", "name": "Airline with untested interline responsibility", "expected_status": "conditionally_ready", "warning_dimension": "interline_responsibility"},
    {"template_code": "approved_unpublished", "name": "Airline with unpublished approved knowledge", "expected_status": "conditionally_ready", "warning_dimension": "publishing_state"},
    {"template_code": "incomplete_fare_brand", "name": "Airline with incomplete fare-brand data but otherwise usable", "expected_status": "conditionally_ready", "warning_dimension": "fare_brand_baggage"},
    {"template_code": "multi_airline_population_wave", "name": "Multi-airline population wave", "expected_status": "planning", "record_type": "population_wave"},
    {"template_code": "rollback_required_candidate", "name": "Rollback-required release candidate", "expected_status": "blocked", "blocked_gate": "rollback_reference_available"},
]

AGENCY_RESTRICTED_FIELDS = {
    "internal_summary",
    "internal_release_notes",
    "source_snapshot",
    "source_reference_ids",
    "gate_ids",
    "decision_ids",
    "issue_ids",
    "metadata",
    "reviewer",
    "review_reason",
    "decision_by",
    "gate_snapshot",
    "blocker_snapshot",
    "assigned_agency_ids",
}


class AirlineIntelligenceScaleReadinessError(ValueError):
    pass


class AirlineIntelligenceScaleReadinessService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "epic_55_sources_reused": True,
            "parallel_intelligence_subsystem_disabled": True,
            "deterministic_scoring_enabled": True,
            "critical_release_gate_enforcement_enabled": True,
            "automatic_publication_disabled": True,
            "automatic_production_seeding_disabled": True,
            "historical_snapshot_mutation_disabled": True,
            "provider_connectivity_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "agency_draft_visibility_disabled": True,
            "client_internal_message_separation_enabled": True,
            "human_release_authority_final": True,
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "assessment_statuses": ASSESSMENT_STATUSES,
            "check_statuses": CHECK_STATUSES,
            "gate_statuses": GATE_STATUSES,
            "decision_statuses": DECISION_STATUSES,
            "wave_statuses": WAVE_STATUSES,
            "issue_statuses": ISSUE_STATUSES,
            "issue_severities": ISSUE_SEVERITIES,
            "dimensions": DIMENSION_CONFIG,
            "release_gates": RELEASE_GATE_CONFIG,
        }

    def assessment_templates(self) -> list[dict[str, Any]]:
        return [{**item, "isolated_metadata_template": True, "automatic_seed": False} for item in ASSESSMENT_TEMPLATES]

    async def coverage(self) -> dict[str, Any]:
        counts = {name: await self.db.collection(collection).count() for name, collection in {
            "readiness_profile_count": READINESS_PROFILE_COLLECTION,
            "readiness_assessment_count": READINESS_ASSESSMENT_COLLECTION,
            "readiness_check_count": READINESS_CHECK_COLLECTION,
            "release_candidate_count": RELEASE_CANDIDATE_COLLECTION,
            "release_gate_count": RELEASE_GATE_COLLECTION,
            "release_decision_count": RELEASE_DECISION_COLLECTION,
            "population_wave_count": POPULATION_WAVE_COLLECTION,
            "scale_issue_count": SCALE_ISSUE_COLLECTION,
        }.items()}
        released = await self.db.collection(RELEASE_CANDIDATE_COLLECTION).find_many({"candidate_status": "released"})
        blockers = await self.db.collection(SCALE_ISSUE_COLLECTION).find_many({"issue_status": "open"})
        return {
            **counts,
            "released_candidate_count": len(released),
            "open_critical_issue_count": sum(bool(item.get("critical")) for item in blockers),
        }

    async def create_profile(self, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = dict(payload or {})
        data.setdefault("profile_reference", self._reference("AIRP"))
        data.setdefault("required_dimension_codes", [item["code"] for item in DIMENSION_CONFIG])
        data.setdefault("critical_dimension_codes", [item["code"] for item in DIMENSION_CONFIG if item["critical"]])
        data.setdefault("required_release_gate_codes", [item["code"] for item in RELEASE_GATE_CONFIG])
        data["airline_codes"] = self._airlines(data.get("airline_codes"))
        data["required_service_families"] = self._tokens(data.get("required_service_families"), upper=True)
        profile = AirlineIntelligenceReadinessProfile(**data).model_dump(mode="json")
        created = await self.db.collection(READINESS_PROFILE_COLLECTION).insert_one(profile)
        await self._audit("airline_intelligence_readiness.profile_created", created, user)
        return self._response("profile", created)

    async def update_profile(self, profile_id: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require(READINESS_PROFILE_COLLECTION, profile_id, "Readiness profile")
        values = {**existing, **dict(payload or {})}
        validated = AirlineIntelligenceReadinessProfile(**values).model_dump(mode="json")
        updated = await self.db.collection(READINESS_PROFILE_COLLECTION).update_one(
            {"id": profile_id},
            {key: value for key, value in validated.items() if key not in {"id", "created_at", "updated_at", "profile_reference", "agency_id"}},
        )
        if not updated:
            raise AirlineIntelligenceScaleReadinessError("Readiness profile could not be updated.")
        await self._audit("airline_intelligence_readiness.profile_updated", updated, user)
        return self._response("profile", updated)

    async def run_assessment(self, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = dict(payload or {})
        airline_code = self._airline(data.get("airline_code"))
        if not airline_code:
            raise AirlineIntelligenceScaleReadinessError("airline_code is required.")
        profile = None
        if data.get("profile_id"):
            profile = await self._require(READINESS_PROFILE_COLLECTION, str(data["profile_id"]), "Readiness profile")
        service_families = self._tokens(
            data.get("required_service_families") or (profile or {}).get("required_service_families"),
            upper=True,
        )
        source_records = await self._source_records(airline_code, data.get("agency_id"))
        derived = self._derive_signals(airline_code, service_families, source_records, data)
        overrides = dict(data.get("signal_overrides") or {})
        assessment = AirlineIntelligenceReadinessAssessment(
            assessment_reference=data.get("assessment_reference") or self._reference("AIRA"),
            profile_id=(profile or {}).get("id"),
            agency_id=data.get("agency_id"),
            airline_code=airline_code,
            generated_at=datetime.now(timezone.utc),
            generated_by=self._actor(user),
            metadata={"isolated_template_code": data.get("template_code"), "signal_overrides_used": bool(overrides)},
        ).model_dump(mode="json")
        created_assessment = await self.db.collection(READINESS_ASSESSMENT_COLLECTION).insert_one(assessment)

        checks: list[dict[str, Any]] = []
        issues: list[dict[str, Any]] = []
        for config in DIMENSION_CONFIG:
            signal = {**derived[config["code"]], **dict(overrides.get(config["code"]) or {})}
            status = self._check_status(signal.get("status"))
            score = self._score(signal.get("score"), status)
            check = AirlineIntelligenceReadinessCheck(
                check_reference=self._reference("AIRC"),
                assessment_id=created_assessment["id"],
                agency_id=data.get("agency_id"),
                airline_code=airline_code,
                dimension_code=config["code"],
                label=config["label"],
                status=status,
                severity="critical" if config["critical"] and status == "blocked" else "high" if status == "blocked" else "medium" if status in {"warning", "unknown"} else "low",
                critical=bool(config["critical"]),
                score=score,
                weight=int(config["weight"]),
                expected_signal=signal.get("expected") or "Governed current metadata is available and reviewable.",
                observed_signal=signal.get("observed"),
                source_collection=signal.get("source_collection"),
                source_reference_ids=self._tokens(signal.get("source_reference_ids")),
                blockers=self._tokens(signal.get("blockers")),
                warnings=self._tokens(signal.get("warnings")),
                remediation_route=config["route"],
                agency_remediation_route=config["agency_route"],
                calculated_at=datetime.now(timezone.utc),
                metadata={"source_count": int(signal.get("source_count") or 0)},
            ).model_dump(mode="json")
            stored_check = await self.db.collection(READINESS_CHECK_COLLECTION).insert_one(check)
            checks.append(stored_check)
            if status in {"blocked", "warning", "unknown"}:
                issue = AirlineIntelligenceScaleIssue(
                    issue_reference=self._reference("AISI"),
                    agency_id=data.get("agency_id"),
                    airline_code=airline_code,
                    assessment_id=created_assessment["id"],
                    dimension_code=config["code"],
                    severity=stored_check["severity"],
                    critical=bool(config["critical"] and status == "blocked"),
                    title=f"{config['label']}: {status.replace('_', ' ')}",
                    description=signal.get("observed") or f"{config['label']} requires review.",
                    remediation_guidance=f"Review {config['label'].lower()} at {config['route']}.",
                    source_reference_ids=stored_check.get("source_reference_ids") or [],
                ).model_dump(mode="json")
                issues.append(await self.db.collection(SCALE_ISSUE_COLLECTION).insert_one(issue))

        score = self._weighted_score(checks)
        critical = [item for item in checks if item.get("critical") and item.get("status") == "blocked"]
        warnings = [item for item in checks if item.get("status") in {"warning", "unknown"}]
        blockers = [item for item in checks if item.get("status") == "blocked"]
        minimum = int(data.get("minimum_readiness_score") or (profile or {}).get("minimum_readiness_score") or 85)
        status = self._assessment_status(score, minimum, critical, blockers, warnings)
        dimension_scores = {item["dimension_code"]: int(item["score"]) for item in checks}
        summary = self._assessment_summary(airline_code, status, score, len(critical), len(warnings))
        source_snapshot = {
            key: {"count": len(records), "references": [self._record_reference(item) for item in records[:25]]}
            for key, records in source_records.items()
        }
        recent_changes = [self._record_reference(item) for item in source_records["changes"][:10]]
        coverage_records = source_records["coverage"]
        coverage_snapshot = {
            "required_service_families": service_families,
            "covered_service_families": sorted({str(item.get("service_family") or "").upper() for item in coverage_records if item.get("operational_ready")}),
            "record_count": len(coverage_records),
        }
        updated = await self.db.collection(READINESS_ASSESSMENT_COLLECTION).update_one(
            {"id": created_assessment["id"]},
            {
                "assessment_status": status,
                "readiness_score": score,
                "dimension_scores": dimension_scores,
                "confidence_score": self._average([dimension_scores["evidence_coverage"], dimension_scores["conflict_status"]]),
                "freshness_score": dimension_scores["evidence_freshness"],
                "service_coverage_score": dimension_scores["service_coverage"],
                "critical_blocker_count": len(critical),
                "blocker_count": len(blockers),
                "warning_count": len(warnings),
                "check_ids": [item["id"] for item in checks],
                "issue_ids": [item["id"] for item in issues],
                "source_snapshot": source_snapshot,
                "recent_change_references": recent_changes,
                "coverage_snapshot": coverage_snapshot,
                "client_summary": summary,
                "internal_summary": f"{summary} Source snapshot includes {sum(len(value) for value in source_records.values())} canonical metadata records.",
            },
        )
        if not updated:
            raise AirlineIntelligenceScaleReadinessError("Assessment could not be finalized.")
        await self._audit("airline_intelligence_readiness.assessment_run", updated, user)
        return {
            "phase": PHASE_LABEL,
            "assessment": updated,
            "checks": checks,
            "issues": issues,
            **self.safety_flags(),
        }

    async def create_release_candidate(self, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = dict(payload or {})
        assessment = await self._require(READINESS_ASSESSMENT_COLLECTION, str(data.get("readiness_assessment_id") or ""), "Readiness assessment")
        if assessment.get("critical_blocker_count"):
            initial_status = "blocked"
        else:
            initial_status = "needs_review"
        candidate = AirlineIntelligenceReleaseCandidate(
            candidate_reference=data.get("candidate_reference") or self._reference("AIRCAND"),
            candidate_name=data.get("candidate_name") or f"{assessment['airline_code']} intelligence release candidate",
            agency_id=data.get("agency_id") or assessment.get("agency_id"),
            airline_code=assessment["airline_code"],
            candidate_status=initial_status,
            readiness_assessment_id=assessment["id"],
            publication_id=data.get("publication_id"),
            knowledge_version_id=data.get("knowledge_version_id"),
            version_snapshot_id=data.get("version_snapshot_id"),
            release_reference=data.get("release_reference"),
            service_family_scope=self._tokens(data.get("service_family_scope") or (assessment.get("coverage_snapshot") or {}).get("required_service_families"), upper=True),
            market_scope=self._tokens(data.get("market_scope"), upper=True),
            route_scope=self._tokens(data.get("route_scope"), upper=True),
            assigned_agency_ids=self._tokens(data.get("assigned_agency_ids")),
            usable_modules=self._tokens(data.get("usable_modules")),
            readiness_score=int(assessment.get("readiness_score") or 0),
            confidence_score=int(assessment.get("confidence_score") or 0),
            freshness_score=int(assessment.get("freshness_score") or 0),
            effective_from=self._date(data.get("effective_from")),
            effective_until=self._date(data.get("effective_until")),
            rollback_reference=data.get("rollback_reference"),
            client_facing_summary=data.get("client_facing_summary"),
            internal_release_notes=data.get("internal_release_notes"),
            blockers=self._tokens(data.get("blockers")),
            warnings=self._tokens(data.get("warnings")),
            metadata={"release_is_manual": True, "source_publication_not_mutated": True},
        ).model_dump(mode="json")
        created = await self.db.collection(RELEASE_CANDIDATE_COLLECTION).insert_one(candidate)
        result = await self.evaluate_release_gates(created["id"], user)
        await self._audit("airline_intelligence_readiness.release_candidate_created", result["candidate"], user)
        return result

    async def evaluate_release_gates(self, candidate_id: str, user: dict[str, Any]) -> dict[str, Any]:
        candidate = await self._require(RELEASE_CANDIDATE_COLLECTION, candidate_id, "Release candidate")
        assessment = await self._require(READINESS_ASSESSMENT_COLLECTION, candidate["readiness_assessment_id"], "Readiness assessment")
        checks = await self.db.collection(READINESS_CHECK_COLLECTION).find_many({"assessment_id": assessment["id"]})
        by_dimension = {item["dimension_code"]: item for item in checks}
        existing = await self.db.collection(RELEASE_GATE_COLLECTION).find_many({"candidate_id": candidate_id})
        existing_by_code = {item["gate_code"]: item for item in existing}
        gates: list[dict[str, Any]] = []
        for config in RELEASE_GATE_CONFIG:
            gate_status, observed, references = self._gate_result(config, candidate, by_dimension)
            values = {
                "gate_reference": (existing_by_code.get(config["code"]) or {}).get("gate_reference") or self._reference("AIRG"),
                "candidate_id": candidate_id,
                "agency_id": candidate.get("agency_id"),
                "airline_code": candidate["airline_code"],
                "gate_code": config["code"],
                "label": config["label"],
                "gate_status": gate_status,
                "critical": True,
                "expected_signal": "The deterministic release requirement is satisfied.",
                "observed_signal": observed,
                "source_reference_ids": references,
                "metadata": {"deterministic": True},
            }
            if config["code"] in existing_by_code:
                current = existing_by_code[config["code"]]
                gate = await self.db.collection(RELEASE_GATE_COLLECTION).update_one({"id": current["id"]}, values)
            else:
                gate = await self.db.collection(RELEASE_GATE_COLLECTION).insert_one(AirlineIntelligenceReleaseGate(**values).model_dump(mode="json"))
            if gate:
                gates.append(gate)
        blocked = [item for item in gates if item.get("critical") and item.get("gate_status") != "passed"]
        gate_warnings = [item for item in gates if item.get("gate_status") == "warning"]
        candidate_status = "blocked" if blocked else "conditionally_ready" if gate_warnings or assessment.get("assessment_status") == "conditionally_ready" else "release_ready"
        blockers = self._tokens([*candidate.get("blockers", []), *[item["label"] for item in blocked]])
        warnings = self._tokens([*candidate.get("warnings", []), *[item["label"] for item in gate_warnings]])
        updated = await self.db.collection(RELEASE_CANDIDATE_COLLECTION).update_one(
            {"id": candidate_id},
            {"candidate_status": candidate_status, "gate_ids": [item["id"] for item in gates], "blockers": blockers, "warnings": warnings},
        )
        if not updated:
            raise AirlineIntelligenceScaleReadinessError("Release candidate gates could not be evaluated.")
        await self._audit("airline_intelligence_readiness.gates_evaluated", updated, user)
        return {"phase": PHASE_LABEL, "candidate": updated, "gates": gates, **self.safety_flags()}

    async def decide_release(self, candidate_id: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        candidate = await self._require(RELEASE_CANDIDATE_COLLECTION, candidate_id, "Release candidate")
        decision_status = self._token(payload.get("decision_status"))
        if decision_status not in DECISION_STATUSES:
            raise AirlineIntelligenceScaleReadinessError("A valid release decision status is required.")
        reason = str(payload.get("decision_reason") or "").strip()
        if not reason:
            raise AirlineIntelligenceScaleReadinessError("decision_reason is required.")
        gates = await self.db.collection(RELEASE_GATE_COLLECTION).find_many({"candidate_id": candidate_id})
        unresolved = [item for item in gates if item.get("critical") and item.get("gate_status") != "passed"]
        if decision_status in {"approved", "released"} and unresolved:
            raise AirlineIntelligenceScaleReadinessError("Release is blocked while critical gates remain unresolved.")
        if decision_status in {"approved", "released"} and not candidate.get("rollback_reference"):
            raise AirlineIntelligenceScaleReadinessError("A rollback reference is required before release approval.")
        resulting = {
            "approved": "release_ready",
            "released": "released",
            "rejected": "blocked",
            "suspended": "suspended",
            "rollback_required": "blocked",
            "archived": "archived",
        }[decision_status]
        actor = self._actor(user)
        decision = AirlineIntelligenceReleaseDecision(
            decision_reference=self._reference("AIRD"),
            candidate_id=candidate_id,
            agency_id=candidate.get("agency_id"),
            airline_code=candidate["airline_code"],
            decision_status=decision_status,
            decision_reason=reason,
            decision_by=actor,
            prior_candidate_status=candidate["candidate_status"],
            resulting_candidate_status=resulting,
            gate_snapshot=[self._gate_snapshot(item) for item in gates],
            blocker_snapshot=list(candidate.get("blockers") or []),
            assigned_agency_ids=list(candidate.get("assigned_agency_ids") or []),
            rollback_reference=candidate.get("rollback_reference"),
            notes=payload.get("notes"),
            metadata={"publication_mutated": False, "manual_human_decision": True},
        ).model_dump(mode="json")
        stored = await self.db.collection(RELEASE_DECISION_COLLECTION).insert_one(decision)
        updates: dict[str, Any] = {
            "candidate_status": resulting,
            "decision_ids": [*candidate.get("decision_ids", []), stored["id"]],
        }
        if decision_status == "released":
            updates.update({"released_at": datetime.now(timezone.utc), "released_by": actor})
        updated = await self.db.collection(RELEASE_CANDIDATE_COLLECTION).update_one({"id": candidate_id}, updates)
        if not updated:
            raise AirlineIntelligenceScaleReadinessError("Release decision could not update its candidate metadata.")
        await self._audit("airline_intelligence_readiness.release_decided", updated, user, {"decision_id": stored["id"], "publication_mutated": False})
        return {"phase": PHASE_LABEL, "candidate": updated, "decision": stored, "publication_mutated": False, **self.safety_flags()}

    async def create_population_wave(self, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = dict(payload or {})
        data.setdefault("wave_reference", self._reference("AIRW"))
        data["airline_codes"] = self._airlines(data.get("airline_codes"))
        if not data["airline_codes"]:
            raise AirlineIntelligenceScaleReadinessError("A population wave requires at least one airline.")
        data["service_family_targets"] = self._tokens(data.get("service_family_targets"), upper=True)
        wave = AirlineIntelligencePopulationWave(**data).model_dump(mode="json")
        created = await self.db.collection(POPULATION_WAVE_COLLECTION).insert_one(wave)
        await self._audit("airline_intelligence_readiness.population_wave_created", created, user)
        return self._response("population_wave", created)

    async def update_population_wave(self, wave_id: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require(POPULATION_WAVE_COLLECTION, wave_id, "Population wave")
        values = {**existing, **dict(payload or {})}
        if self._token(values.get("wave_status")) not in WAVE_STATUSES:
            raise AirlineIntelligenceScaleReadinessError("A valid population wave status is required.")
        values["completion_percentage"] = max(0, min(100, int(values.get("completion_percentage") or 0)))
        validated = AirlineIntelligencePopulationWave(**values).model_dump(mode="json")
        updated = await self.db.collection(POPULATION_WAVE_COLLECTION).update_one(
            {"id": wave_id},
            {key: value for key, value in validated.items() if key not in {"id", "created_at", "updated_at", "wave_reference", "agency_id"}},
        )
        if not updated:
            raise AirlineIntelligenceScaleReadinessError("Population wave could not be updated.")
        await self._audit("airline_intelligence_readiness.population_wave_updated", updated, user, {"automatic_publication": False})
        return {**self._response("population_wave", updated), "release_candidates_automatically_published": False}

    async def update_issue(self, issue_id: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        existing = await self._require(SCALE_ISSUE_COLLECTION, issue_id, "Scale issue")
        status = self._token(payload.get("issue_status") or existing.get("issue_status"))
        if status not in ISSUE_STATUSES:
            raise AirlineIntelligenceScaleReadinessError("A valid issue status is required.")
        updates = {key: value for key, value in dict(payload or {}).items() if key in {"issue_status", "owner", "resolution_notes"}}
        if status in {"resolved", "waived", "archived"}:
            updates.update({"resolved_by": self._actor(user), "resolved_at": datetime.now(timezone.utc)})
        updated = await self.db.collection(SCALE_ISSUE_COLLECTION).update_one({"id": issue_id}, updates)
        if not updated:
            raise AirlineIntelligenceScaleReadinessError("Scale issue could not be updated.")
        await self._audit("airline_intelligence_readiness.issue_updated", updated, user)
        return self._response("issue", updated)

    async def platform_dashboard(self, **filters: Any) -> dict[str, Any]:
        profiles = await self._list(READINESS_PROFILE_COLLECTION, filters, {"agency_id": "agency_id", "profile_status": "status"})
        assessments = await self._list(READINESS_ASSESSMENT_COLLECTION, filters, {"agency_id": "agency_id", "airline_code": "airline_code", "assessment_status": "status"})
        candidates = await self._list(RELEASE_CANDIDATE_COLLECTION, filters, {"agency_id": "agency_id", "airline_code": "airline_code", "candidate_status": "status"})
        waves = await self._list(POPULATION_WAVE_COLLECTION, filters, {"agency_id": "agency_id", "wave_status": "status"})
        issues = await self._list(SCALE_ISSUE_COLLECTION, filters, {"agency_id": "agency_id", "airline_code": "airline_code", "issue_status": "issue_status", "severity": "severity"})
        candidate_ids = {item["id"] for item in candidates}
        gates = [item for item in await self.db.collection(RELEASE_GATE_COLLECTION).find_many() if item.get("candidate_id") in candidate_ids]
        decisions = [item for item in await self.db.collection(RELEASE_DECISION_COLLECTION).find_many() if item.get("candidate_id") in candidate_ids]
        return {
            "phase": PHASE_LABEL,
            "summary": self._summary(assessments, candidates, gates, waves, issues),
            "readiness_matrix": self._readiness_matrix(assessments),
            "profiles": profiles,
            "assessments": assessments,
            "release_candidates": candidates,
            "release_gates": gates,
            "release_decisions": decisions,
            "population_waves": waves,
            "blockers": [item for item in issues if item.get("issue_status") in {"open", "under_review"}],
            "assessment_templates": self.assessment_templates(),
            "filters": self.filter_metadata(),
            **self.safety_flags(),
        }

    async def agency_dashboard(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        candidates = await self.db.collection(RELEASE_CANDIDATE_COLLECTION).find_many({"candidate_status": "released"})
        candidates = [item for item in candidates if agency_id in (item.get("assigned_agency_ids") or [])]
        if filters.get("airline_code"):
            candidates = [item for item in candidates if item.get("airline_code") == self._airline(filters["airline_code"])]
        publications = {item["id"]: item for item in await self.db.collection("airline_knowledge_publications").find_many()}
        published_candidates = []
        for item in candidates:
            publication = publications.get(item.get("publication_id"))
            if item.get("publication_id") and (not publication or publication.get("publication_status") != "published"):
                continue
            published_candidates.append(self._agency_projection(item))
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": {
                "released_airline_count": len({item.get("airline_code") for item in published_candidates}),
                "released_candidate_count": len(published_candidates),
                "conditional_or_stale_count": sum(bool(item.get("warnings")) or int(item.get("freshness_score") or 0) < 70 for item in published_candidates),
                "usable_module_count": len({module for item in published_candidates for module in item.get("usable_modules", [])}),
            },
            "released_coverage": published_candidates,
            "warnings": [
                {"candidate_reference": item.get("candidate_reference"), "airline_code": item.get("airline_code"), "warnings": item.get("warnings") or [], "stale_or_conditional": bool(item.get("warnings")) or int(item.get("freshness_score") or 0) < 70}
                for item in published_candidates
                if item.get("warnings") or int(item.get("freshness_score") or 0) < 70
            ],
            "draft_governance_hidden": True,
            "read_only": True,
            **self.safety_flags(),
        }

    async def get_candidate(self, candidate_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        candidate = await self._require(RELEASE_CANDIDATE_COLLECTION, candidate_id, "Release candidate")
        if agency_id:
            if candidate.get("candidate_status") != "released" or agency_id not in (candidate.get("assigned_agency_ids") or []):
                raise AirlineIntelligenceScaleReadinessError("Released airline intelligence was not found for this agency.")
            if candidate.get("publication_id"):
                publication = await self.db.collection("airline_knowledge_publications").find_one({"id": candidate["publication_id"]})
                if not publication or publication.get("publication_status") != "published":
                    raise AirlineIntelligenceScaleReadinessError("Published airline intelligence was not found for this agency.")
            return {"phase": PHASE_LABEL, "candidate": self._agency_projection(candidate), "read_only": True, **self.safety_flags()}
        gates = await self.db.collection(RELEASE_GATE_COLLECTION).find_many({"candidate_id": candidate_id})
        decisions = await self.db.collection(RELEASE_DECISION_COLLECTION).find_many({"candidate_id": candidate_id})
        return {"phase": PHASE_LABEL, "candidate": candidate, "gates": gates, "decisions": decisions, **self.safety_flags()}

    async def list_assessments(self, **filters: Any) -> list[dict[str, Any]]:
        return await self._list(READINESS_ASSESSMENT_COLLECTION, filters, {"agency_id": "agency_id", "airline_code": "airline_code", "assessment_status": "status"})

    async def list_candidates(self, **filters: Any) -> list[dict[str, Any]]:
        return await self._list(RELEASE_CANDIDATE_COLLECTION, filters, {"agency_id": "agency_id", "airline_code": "airline_code", "candidate_status": "status"})

    async def list_waves(self, **filters: Any) -> list[dict[str, Any]]:
        return await self._list(POPULATION_WAVE_COLLECTION, filters, {"agency_id": "agency_id", "wave_status": "status"})

    async def list_issues(self, **filters: Any) -> list[dict[str, Any]]:
        return await self._list(SCALE_ISSUE_COLLECTION, filters, {"agency_id": "agency_id", "airline_code": "airline_code", "issue_status": "issue_status", "severity": "severity"})

    async def _source_records(self, airline_code: str, agency_id: str | None) -> dict[str, list[dict[str, Any]]]:
        raw: dict[str, list[dict[str, Any]]] = {}
        for key, collection in SOURCE_COLLECTIONS.items():
            records = await self.db.collection(collection).find_many()
            raw[key] = [item for item in records if not item.get("archived") and self._agency_source_visible(item, agency_id)]

        result = {
            key: [item for item in records if self._airline_matches(item, airline_code, key)]
            for key, records in raw.items()
        }
        canonical_ids = {str(item.get("id")) for item in result["airlines"] if item.get("id")}
        if canonical_ids:
            for key in ["master_profiles", "aliases"]:
                result[key] = [
                    item
                    for item in raw[key]
                    if self._airline_matches(item, airline_code, key)
                    or str(item.get("canonical_airline_id") or "") in canonical_ids
                ]

        assertion_ids = {str(item.get("id")) for item in result["assertions"] if item.get("id")}
        evidence_source_ids = {str(item.get("source_id")) for item in result["assertions"] if item.get("source_id")}
        result["conflicts"] = [
            item
            for item in raw["conflicts"]
            if self._airline_matches(item, airline_code, "conflicts")
            or bool(assertion_ids & {
                str(value)
                for value in [
                    *(item.get("assertion_ids") or []),
                    item.get("left_assertion_id"),
                    item.get("right_assertion_id"),
                    item.get("primary_assertion_id"),
                    item.get("conflicting_assertion_id"),
                ]
                if value
            })
        ]
        result["freshness"] = [
            item
            for item in raw["freshness"]
            if self._airline_matches(item, airline_code, "freshness")
            or str(item.get("assertion_id") or "") in assertion_ids
            or str(item.get("source_id") or "") in evidence_source_ids
        ]

        version_ids = {str(item.get("id")) for item in result["versions"] if item.get("id")}
        result["assignments"] = [
            item
            for item in raw["assignments"]
            if self._airline_matches(item, airline_code, "assignments")
            or str(item.get("knowledge_version_id") or "") in version_ids
        ]
        assignment_ids = {str(item.get("id")) for item in result["assignments"] if item.get("id")}
        result["consumption"] = [
            item
            for item in raw["consumption"]
            if self._airline_matches(item, airline_code, "consumption")
            or str(item.get("profile_id") or "") in assignment_ids
        ]
        return result

    def _derive_signals(self, airline_code: str, service_families: list[str], sources: dict[str, list[dict[str, Any]]], data: dict[str, Any]) -> dict[str, dict[str, Any]]:
        airline = sources["airlines"][0] if sources["airlines"] else None
        master = sources["master_profiles"]
        aliases = sources["aliases"]
        assertions = sources["assertions"]
        conflicts = [item for item in sources["conflicts"] if self._token(item.get("status") or item.get("conflict_status")) in {"detected", "under_review", "unresolved"}]
        freshness = sources["freshness"]
        stale_freshness = [item for item in freshness if self._token(item.get("freshness_status") or item.get("status")) in {"stale", "expired", "review_due"}]
        versions = sources["versions"]
        coverage = sources["coverage"]
        covered = {self._airline(item.get("service_family")) for item in coverage if item.get("operational_ready")}
        missing_services = [item for item in service_families if item not in covered]
        scenarios = sources["scenarios"]
        approved_scenarios = [item for item in scenarios if self._token(item.get("test_status")) in {"reviewed", "approved"}]
        qa = sources["qa"]
        qa_failed = [item for item in qa if self._token(item.get("qa_status")) in {"blocked", "changes_requested"} or self._token(item.get("severity")) in {"critical", "blocking"}]
        qa_passed = [item for item in qa if self._token(item.get("qa_status")) in {"resolved", "recommended_for_approval"} or self._token(item.get("approval_recommendation")) == "ready_for_human_approval"]
        publications = sources["publications"]
        published = [item for item in publications if self._token(item.get("publication_status")) == "published"]
        approved = [item for item in publications if self._token(item.get("publication_status")) in {"qa_approved", "approved", "scheduled"}]
        contacts = sources["contacts"]
        stale_contacts = [item for item in contacts if self._token(item.get("freshness_status")) in {"stale", "expired", "review_due"} or self._token(item.get("verification_status")) not in {"verified"}]
        assignments = [item for item in sources["assignments"] if item.get("visible_to_agency") and self._token(item.get("status")) == "visible"]
        consumption = [item for item in sources["consumption"] if self._token(item.get("status")) == "ready" or item.get("safe_for_usage")]
        return {
            "master_profile": self._signal(bool(airline and master), bool(airline or master), "airline_master_profiles", [*master, *([airline] if airline else [])], "Canonical profile is approved and complete."),
            "identity_aliases": self._signal(bool(airline and aliases), bool(airline), "airline_identity_aliases", aliases, "Canonical identity and aliases are internally consistent.", missing_is_warning=True),
            "evidence_coverage": self._signal(len(assertions) >= int(data.get("minimum_evidence_assertions") or 1), bool(assertions), "airline_evidence_assertions", assertions, f"{len(assertions)} governed evidence assertions found."),
            "conflict_status": self._signal(not conflicts, True, "airline_evidence_conflicts", conflicts, "No unresolved evidence conflicts." if not conflicts else f"{len(conflicts)} unresolved evidence conflicts remain."),
            "evidence_freshness": self._signal(bool(freshness) and not stale_freshness, bool(freshness), "airline_evidence_freshness_assessments", freshness, "Evidence is current." if freshness and not stale_freshness else f"{len(stale_freshness)} evidence records are stale or due for review.", missing_is_warning=True),
            "version_governance": self._signal(any(self._token(item.get("version_status") or item.get("status")) in {"approved", "published", "frozen"} for item in versions), bool(versions), "airline_knowledge_versions", versions, f"{len(versions)} governed versions found."),
            "service_coverage": self._signal(bool(coverage) and not missing_services, bool(coverage), "airline_service_coverage_cells", coverage, "Required service-family coverage is operationally ready." if not missing_services and coverage else f"Missing operational coverage for: {', '.join(missing_services) if missing_services else 'required scope'}."),
            "pricing_coverage": self._signal(bool(sources["pricing"]), bool(sources["pricing"]), "pricing_formula_builders", sources["pricing"], f"{len(sources['pricing'])} pricing records found.", missing_is_warning=True),
            "operational_rule_coverage": self._signal(bool(sources["rules"]), bool(sources["rules"]), "operational_rule_composer_rules", sources["rules"], f"{len(sources['rules'])} operational rules found.", missing_is_warning=True),
            "scenario_test_coverage": self._signal(bool(approved_scenarios), bool(scenarios), "operational_scenario_tests", scenarios, f"{len(approved_scenarios)} approved or reviewed scenarios found."),
            "distribution_capability": self._signal(bool(sources["distribution"]), bool(sources["distribution"]), "airline_distribution_capabilities", sources["distribution"], f"{len(sources['distribution'])} distribution capability records found.", missing_is_warning=True),
            "interline_responsibility": self._signal(bool(sources["interline"]), bool(sources["interline"]), "airline_service_responsibility_rules", sources["interline"], f"{len(sources['interline'])} interline responsibility rules found.", missing_is_warning=True),
            "fare_brand_baggage": self._signal(bool(sources["fare_families"] and sources["baggage"]), bool(sources["fare_families"] or sources["baggage"]), "airline_fare_families", [*sources["fare_families"], *sources["baggage"]], f"{len(sources['fare_families'])} fare families and {len(sources['baggage'])} baggage rules found.", missing_is_warning=True),
            "contact_directory": self._signal(bool(contacts) and not stale_contacts, bool(contacts), "airline_contacts", contacts, "Current verified contact coverage is available." if contacts and not stale_contacts else f"{len(stale_contacts)} contacts are stale or unverified.", missing_is_warning=True),
            "qa_state": self._signal(bool(qa_passed) and not qa_failed, bool(qa), "knowledge_quality_assurance_reviews", qa, "QA passed." if qa_passed and not qa_failed else f"{len(qa_failed)} blocking QA reviews remain."),
            "publishing_state": self._signal(bool(published), bool(published or approved), "airline_knowledge_publications", publications, "Knowledge is published." if published else "Knowledge is approved but not published." if approved else "No approved publication is available.", missing_is_warning=True),
            "agency_assignment": self._signal(bool(assignments), bool(assignments), "airline_intelligence_agency_consumption_profiles", assignments, f"{len(assignments)} visible agency assignments found.", missing_is_warning=True),
            "operational_consumption": self._signal(bool(consumption), bool(consumption), "airline_intelligence_agency_usage_readiness", consumption, f"{len(consumption)} operational usage areas are ready.", missing_is_warning=True),
        }

    def _signal(self, passed: bool, present: bool, collection: str, records: list[dict[str, Any]], observed: str, *, missing_is_warning: bool = False) -> dict[str, Any]:
        if passed:
            status = "passed"
        elif present or missing_is_warning:
            status = "warning"
        else:
            status = "blocked"
        return {
            "status": status,
            "score": {"passed": 100, "warning": 60, "blocked": 0}[status],
            "observed": observed,
            "source_collection": collection,
            "source_count": len(records),
            "source_reference_ids": [self._record_reference(item) for item in records[:50]],
            "blockers": [observed] if status == "blocked" else [],
            "warnings": [observed] if status == "warning" else [],
        }

    def _gate_result(self, config: dict[str, Any], candidate: dict[str, Any], checks: dict[str, dict[str, Any]]) -> tuple[str, str, list[str]]:
        if config.get("dimension"):
            check = checks.get(config["dimension"])
            passed = bool(check and check.get("status") == "passed")
            return ("passed" if passed else "blocked", (check or {}).get("observed_signal") or "Required readiness dimension is not passed.", list((check or {}).get("source_reference_ids") or []))
        if config.get("candidate_field"):
            value = candidate.get(config["candidate_field"])
            return ("passed" if value else "blocked", f"{config['candidate_field']} is {'available' if value else 'missing'}.", [str(value)] if value else [])
        method = config.get("candidate_method")
        if method == "effective_dates":
            start = self._date(candidate.get("effective_from"))
            end = self._date(candidate.get("effective_until"))
            valid = bool(start and (not end or end >= start))
            return ("passed" if valid else "blocked", "Effective-date window is valid." if valid else "A valid effective-from date and non-inverted window are required.", [])
        if method == "message_separation":
            client = str(candidate.get("client_facing_summary") or "").strip()
            internal = str(candidate.get("internal_release_notes") or "").strip()
            valid = bool(client and internal and client != internal)
            return ("passed" if valid else "blocked", "Client and internal messages are present and separate." if valid else "Distinct client-facing and internal release messages are required.", [])
        if method == "agency_payload":
            valid = bool(candidate.get("assigned_agency_ids") and candidate.get("usable_modules"))
            return ("passed" if valid else "blocked", "Agency assignments and usable modules are defined." if valid else "At least one assigned agency and one usable module are required.", list(candidate.get("assigned_agency_ids") or []))
        return "blocked", "Unknown release gate configuration.", []

    def _summary(self, assessments: list[dict[str, Any]], candidates: list[dict[str, Any]], gates: list[dict[str, Any]], waves: list[dict[str, Any]], issues: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "assessment_count": len(assessments),
            "average_readiness_score": self._average([int(item.get("readiness_score") or 0) for item in assessments]),
            "release_ready_count": sum(item.get("assessment_status") == "release_ready" for item in assessments),
            "blocked_assessment_count": sum(item.get("assessment_status") == "blocked" for item in assessments),
            "release_candidate_count": len(candidates),
            "released_candidate_count": sum(item.get("candidate_status") == "released" for item in candidates),
            "blocked_gate_count": sum(item.get("gate_status") == "blocked" for item in gates),
            "population_wave_count": len(waves),
            "open_issue_count": sum(item.get("issue_status") in {"open", "under_review"} for item in issues),
            "critical_issue_count": sum(item.get("critical") and item.get("issue_status") in {"open", "under_review"} for item in issues),
            "assessment_status_counts": self._counts(assessments, "assessment_status"),
            "candidate_status_counts": self._counts(candidates, "candidate_status"),
            "wave_status_counts": self._counts(waves, "wave_status"),
        }

    def _readiness_matrix(self, assessments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        latest: dict[tuple[str, str | None], dict[str, Any]] = {}
        for item in sorted(assessments, key=lambda value: str(value.get("generated_at") or value.get("created_at") or "")):
            latest[(item.get("airline_code"), item.get("agency_id"))] = item
        return [
            {
                "airline_code": item.get("airline_code"),
                "agency_id": item.get("agency_id"),
                "assessment_id": item.get("id"),
                "status": item.get("assessment_status"),
                "score": item.get("readiness_score"),
                "confidence": item.get("confidence_score"),
                "freshness": item.get("freshness_score"),
                "service_coverage": item.get("service_coverage_score"),
                "critical_blockers": item.get("critical_blocker_count"),
                "warnings": item.get("warning_count"),
                "recent_changes": item.get("recent_change_references") or [],
            }
            for item in latest.values()
        ]

    async def _list(self, collection: str, filters: dict[str, Any], mapping: dict[str, str]) -> list[dict[str, Any]]:
        items = await self.db.collection(collection).find_many()
        for field, filter_key in mapping.items():
            value = filters.get(filter_key)
            if value is not None and value != "":
                expected = self._airline(value) if field == "airline_code" else self._token(value) if field.endswith("status") else str(value)
                items = [item for item in items if (self._airline(item.get(field)) if field == "airline_code" else self._token(item.get(field)) if field.endswith("status") else str(item.get(field) or "")) == expected]
        return sorted(items, key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)

    async def _require(self, collection: str, record_id: str, label: str) -> dict[str, Any]:
        item = await self.db.collection(collection).find_one({"id": record_id}) if record_id else None
        if not item:
            raise AirlineIntelligenceScaleReadinessError(f"{label} was not found.")
        return item

    def _agency_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = {key: value for key, value in item.items() if key not in AGENCY_RESTRICTED_FIELDS}
        projected["assigned_release_version"] = item.get("release_reference") or item.get("knowledge_version_id") or item.get("version_snapshot_id")
        projected["read_only"] = True
        projected["draft_governance_hidden"] = True
        return projected

    def _agency_source_visible(self, item: dict[str, Any], agency_id: str | None) -> bool:
        item_agency = item.get("agency_id")
        return item_agency in {None, "", agency_id} if agency_id else True

    def _airline_matches(self, item: dict[str, Any], airline_code: str, source_key: str) -> bool:
        values: list[Any] = [
            item.get("airline_code"), item.get("iata_code"), item.get("marketing_carrier_code"),
            item.get("operating_carrier_code"), item.get("validating_carrier_code"),
            (item.get("airline_context") or {}).get("airline_code") if isinstance(item.get("airline_context"), dict) else None,
        ]
        values.extend(item.get("airline_codes") or [])
        if source_key == "airlines":
            values.extend([item.get("id"), item.get("icao_code")])
        if any(self._airline(value) == airline_code for value in values if value):
            return True
        if source_key in {"master_profiles", "aliases"}:
            return self._airline(item.get("canonical_airline_code")) == airline_code
        return False

    def _assessment_status(self, score: int, minimum: int, critical: list[dict[str, Any]], blockers: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> str:
        if critical:
            return "blocked"
        if blockers or score < max(60, minimum - 20):
            return "incomplete"
        if score >= minimum and not warnings:
            return "release_ready"
        if score >= max(70, minimum - 15):
            return "conditionally_ready"
        return "needs_review"

    def _assessment_summary(self, airline_code: str, status: str, score: int, critical: int, warnings: int) -> str:
        return f"{airline_code} readiness is {status.replace('_', ' ')} at {score}/100 with {critical} critical blockers and {warnings} warnings. Human release authority remains final."

    def _weighted_score(self, checks: list[dict[str, Any]]) -> int:
        total_weight = sum(int(item.get("weight") or 0) for item in checks)
        if not total_weight:
            return 0
        return round(sum(int(item.get("score") or 0) * int(item.get("weight") or 0) for item in checks) / total_weight)

    def _check_status(self, value: Any) -> str:
        status = self._token(value)
        return status if status in CHECK_STATUSES else "unknown"

    def _score(self, value: Any, status: str) -> int:
        default = {"passed": 100, "warning": 60, "blocked": 0, "unknown": 25, "not_applicable": 100}[status]
        try:
            return max(0, min(100, int(value)))
        except (TypeError, ValueError):
            return default

    def _gate_snapshot(self, item: dict[str, Any]) -> dict[str, Any]:
        return {key: item.get(key) for key in ["gate_code", "label", "gate_status", "critical", "observed_signal"]}

    def _response(self, key: str, value: Any) -> dict[str, Any]:
        return {"phase": PHASE_LABEL, key: value, **self.safety_flags()}

    async def _audit(self, event_type: str, item: dict[str, Any], user: dict[str, Any], metadata: dict[str, Any] | None = None) -> None:
        event = AuditEvent(
            agency_id=item.get("agency_id"),
            actor_user_id=user.get("id"),
            event_type=event_type,
            entity_type="airline_intelligence_scale_readiness",
            entity_id=item["id"],
            summary=event_type.replace(".", " ").replace("_", " ").title(),
            metadata={"airline_code": item.get("airline_code"), "metadata_only": True, **(metadata or {})},
        )
        await self.db.collection("audit_events").insert_one(event.model_dump(mode="json"))

    def _record_reference(self, item: dict[str, Any]) -> str:
        for key in ["id", "assessment_reference", "version_reference", "publication_reference", "coverage_cell_reference", "scenario_reference", "contact_reference", "review_reference", "formula_reference", "rule_reference"]:
            if item.get(key):
                return str(item[key])
        return "unknown"

    def _actor(self, user: dict[str, Any]) -> str:
        return str(user.get("id") or user.get("email") or "platform-reviewer")

    def _reference(self, prefix: str) -> str:
        return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

    def _token(self, value: Any) -> str:
        return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")

    def _tokens(self, values: Any, *, upper: bool = False) -> list[str]:
        if values is None:
            return []
        if not isinstance(values, (list, tuple, set)):
            values = [values]
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            text = str(value or "").strip()
            normalized = text.upper() if upper else text
            key = normalized.lower()
            if normalized and key not in seen:
                seen.add(key)
                result.append(normalized)
        return result

    def _airline(self, value: Any) -> str:
        return str(value or "").strip().upper()

    def _airlines(self, values: Any) -> list[str]:
        return self._tokens(values, upper=True)

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

    def _average(self, values: list[int]) -> int:
        return round(sum(values) / len(values)) if values else 0

    def _counts(self, items: list[dict[str, Any]], field: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            value = str(item.get(field) or "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts
