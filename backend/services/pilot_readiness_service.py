from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    PilotGoldenPathCase,
    PilotGoldenPathCaseCreate,
    PilotGoldenPathCaseUpdate,
    PilotGoldenPathRun,
    PilotGoldenPathRunCreateRequest,
    PilotReadinessAssessment,
    PilotReadinessAssessmentRunRequest,
    PilotReadinessCheck,
    PilotReadinessIssue,
    PilotReadinessIssueUpdate,
    PilotReadinessProfile,
    PilotReadinessProfileCreate,
    PilotReadinessProfileUpdate,
)


PHASE_LABEL = "phase_56_0_canonical_journey_itinerary_representation_foundation"

PILOT_READINESS_PROFILES_COLLECTION = "pilot_readiness_profiles"
PILOT_READINESS_ASSESSMENTS_COLLECTION = "pilot_readiness_assessments"
PILOT_READINESS_CHECKS_COLLECTION = "pilot_readiness_checks"
PILOT_GOLDEN_PATH_CASES_COLLECTION = "pilot_golden_path_cases"
PILOT_GOLDEN_PATH_RUNS_COLLECTION = "pilot_golden_path_runs"
PILOT_READINESS_ISSUES_COLLECTION = "pilot_readiness_issues"

READINESS_STATUSES = [
    "not_started",
    "assessing",
    "blocked",
    "needs_work",
    "conditionally_ready",
    "pilot_ready",
    "failed",
    "archived",
]

CHECK_FAMILIES = [
    "system_health",
    "reference_data",
    "knowledge_production",
    "airline_service_coverage",
    "operational_precision",
    "evaluation_recommendation",
    "offer_readiness",
    "pilot_operations",
]

CHECK_STATUSES = ["passed", "warning", "blocked", "failed", "skipped", "unknown"]
CHECK_SEVERITIES = ["critical", "high", "medium", "low"]
GOLDEN_PATH_STATUSES = ["passed", "warning", "blocked", "failed", "skipped", "unknown"]
ISSUE_STATUSES = ["open", "in_review", "resolved", "reopened", "waived"]

SEVERITY_DEDUCTIONS = {"critical": 30, "high": 15, "medium": 7, "low": 3}

REMEDIATION_LINKS: dict[str, dict[str, str]] = {
    "reference_data_engine": {"platform": "/platform/reference-data-engine", "agency": "/agency/reference-data-engine"},
    "knowledge_import_templates": {"platform": "/platform/knowledge-import-templates", "agency": "/agency/import-templates"},
    "knowledge_normalisation": {"platform": "/platform/airline-knowledge-normalisation", "agency": "/agency/knowledge-normalisation"},
    "visual_policy_editor": {"platform": "/platform/visual-policy-editor", "agency": "/agency/policy-editor"},
    "pricing_formula_builder": {"platform": "/platform/pricing-formula-builder", "agency": "/agency/pricing-formula-builder"},
    "operational_rule_composer": {"platform": "/platform/operational-rule-composer", "agency": "/agency/rule-composer"},
    "knowledge_quality_assurance": {"platform": "/platform/knowledge-quality-assurance", "agency": "/agency/knowledge-quality-assurance"},
    "airline_knowledge_publishing": {"platform": "/platform/knowledge-publishing", "agency": "/agency/published-knowledge"},
    "operational_scenario_testing": {"platform": "/platform/operational-scenario-testing", "agency": "/agency/scenario-testing"},
    "knowledge_population_toolkit": {"platform": "/platform/knowledge-population-toolkit", "agency": "/agency/knowledge-population-toolkit"},
    "airline_capability_matrix": {"platform": "/platform/airline-capability-matrix", "agency": "/agency/capability-matrix"},
    "airline_service_coverage": {"platform": "/platform/airline-service-coverage", "agency": "/agency/airline-service-coverage"},
    "service_parameter_taxonomies": {"platform": "/platform/service-parameter-taxonomies", "agency": "/agency/service-parameter-taxonomies"},
    "request_segment_services": {"platform": "/platform/request-segment-services", "agency": "/agency/request-segment-services"},
    "client_passenger_master": {"platform": "/platform/client-master", "agency": "/agency/clients"},
    "passenger_master": {"platform": "/platform/passenger-master", "agency": "/agency/passengers"},
    "passenger_service_feasibility": {"platform": "/platform/passenger-service-feasibility", "agency": "/agency/service-feasibility"},
    "airline_recommendations": {"platform": "/platform/airline-recommendations", "agency": "/agency/recommendations"},
    "intelligent_offer_builder": {"platform": "/platform/intelligent-offer-builder", "agency": "/agency/offer-intelligence"},
    "operational_intelligence_cases": {"platform": "/platform/operational-intelligence-cases", "agency": "/agency/intelligence-cases"},
    "operational_timelines": {"platform": "/platform/operational-timelines", "agency": "/agency/timeline"},
    "passenger_service_workflows": {"platform": "/platform/passenger-service-workflows", "agency": "/agency/workflow-engine"},
}

MODULE_COLLECTIONS: dict[str, str] = {
    "reference_data_engine": "reference_data_domains",
    "knowledge_import_templates": "knowledge_import_templates",
    "knowledge_normalisation": "airline_knowledge_normalisations",
    "visual_policy_editor": "visual_policy_editor_cards",
    "pricing_formula_builder": "pricing_formula_builders",
    "operational_rule_composer": "operational_rule_composer_rules",
    "knowledge_quality_assurance": "knowledge_quality_assurance_reviews",
    "airline_knowledge_publishing": "airline_knowledge_publications",
    "operational_scenario_testing": "operational_scenario_tests",
    "knowledge_population_toolkit": "knowledge_population_toolkits",
    "airline_capability_matrix": "airline_capability_matrix",
    "service_parameter_taxonomies": "service_parameter_taxonomies",
    "request_segment_services": "request_segment_service_scopes",
    "client_passenger_master": "client_master_records",
    "passenger_master": "passenger_master_records",
    "passenger_service_feasibility": "passenger_service_feasibilities",
    "airline_recommendations": "airline_recommendations",
    "intelligent_offer_builder": "intelligent_offer_builder_packages",
    "operational_intelligence_cases": "operational_intelligence_cases",
    "operational_timelines": "operational_timelines",
    "passenger_service_workflows": "passenger_service_workflows",
}

DEFAULT_REQUIRED_MODULES = [
    "reference_data_engine",
    "knowledge_import_templates",
    "knowledge_normalisation",
    "visual_policy_editor",
    "pricing_formula_builder",
    "operational_rule_composer",
    "knowledge_quality_assurance",
    "airline_knowledge_publishing",
    "operational_scenario_testing",
    "knowledge_population_toolkit",
    "request_segment_services",
    "passenger_service_feasibility",
    "airline_recommendations",
    "intelligent_offer_builder",
]

GOLDEN_PATH_STAGE_CODES = [
    "knowledge_source_ready",
    "import_template_ready",
    "normalisation_ready",
    "policy_rule_pricing_ready",
    "quality_assurance_ready",
    "publishing_ready",
    "scenario_expectation_ready",
    "request_segment_service_ready",
    "feasibility_ready",
    "recommendation_ready",
    "intelligent_offer_ready",
    "trip_booking_readiness",
    "operational_follow_up_ready",
]

GOLDEN_PATH_CASE_TEMPLATES: list[dict[str, Any]] = [
    {"case_reference": "GPT-WCHC", "case_name": "WCHC wheelchair assistance", "case_family": "WCHC", "scenario_type": "feasible_published_policy", "service_requirements": [{"service_code": "WCHC", "service_family": "mobility_assistance"}]},
    {"case_reference": "GPT-PETC", "case_name": "PETC in-cabin pet", "case_family": "PETC", "scenario_type": "conditional_policy", "service_requirements": [{"service_code": "PETC", "service_family": "pets_animals"}]},
    {"case_reference": "GPT-MEDIF-POC", "case_name": "MEDIF with portable oxygen concentrator", "case_family": "MEDIF", "scenario_type": "conditional_policy", "service_requirements": [{"service_code": "MEDIF", "service_family": "medical_clearance"}, {"service_code": "POC", "service_family": "medical_equipment"}]},
    {"case_reference": "GPT-UMNR", "case_name": "Unaccompanied minor journey", "case_family": "UMNR", "scenario_type": "feasible_published_policy", "service_requirements": [{"service_code": "UMNR", "service_family": "minor_assistance"}]},
    {"case_reference": "GPT-EXST-CBBG", "case_name": "Extra seat / cabin baggage seat", "case_family": "EXST_CBBG", "scenario_type": "conditional_policy", "service_requirements": [{"service_code": "EXST", "service_family": "seat_services"}, {"service_code": "CBBG", "service_family": "special_items"}]},
    {"case_reference": "GPT-SPORTS", "case_name": "Sports equipment handling", "case_family": "sports_equipment", "scenario_type": "feasible_published_policy", "service_requirements": [{"service_code": "SPORT", "service_family": "restricted_equipment"}]},
    {"case_reference": "GPT-UNKNOWN-POLICY", "case_name": "Unknown policy service", "case_family": "unknown_policy", "scenario_type": "unknown_policy", "service_requirements": [{"service_code": "ZZZZ", "service_family": "unknown"}]},
    {"case_reference": "GPT-BLOCKED-POLICY", "case_name": "Blocked policy service", "case_family": "blocked_policy", "scenario_type": "blocked_policy", "service_requirements": [{"service_code": "BLOCKED", "service_family": "restricted_equipment"}]},
    {"case_reference": "GPT-CONDITIONAL-POLICY", "case_name": "Conditional policy service", "case_family": "conditional_policy", "scenario_type": "conditional_policy", "service_requirements": [{"service_code": "AVIH", "service_family": "pets_animals"}]},
    {"case_reference": "GPT-PUBLISHED-FEASIBLE", "case_name": "Feasible published-policy journey", "case_family": "published_policy", "scenario_type": "feasible_published_policy", "service_requirements": [{"service_code": "BAG", "service_family": "baggage"}]},
]


class PilotReadinessError(ValueError):
    pass


class PilotReadinessService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_dashboard(self, **filters: Any) -> dict[str, Any]:
        return await self._dashboard_response(agency_id=filters.get("agency_id"), read_only=False)

    async def agency_dashboard(self, agency_id: str) -> dict[str, Any]:
        return await self._dashboard_response(agency_id=agency_id, read_only=True)

    async def _dashboard_response(self, agency_id: str | None = None, read_only: bool = False) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": await self.summary(agency_id),
            "profiles": await self.list_profiles(agency_id=agency_id),
            "assessments": await self.list_assessments(agency_id=agency_id),
            "golden_path_cases": await self.list_cases(agency_id=agency_id),
            "golden_path_runs": await self.list_runs(agency_id=agency_id),
            "issues": await self.list_issues(agency_id=agency_id),
            "module_readiness": await self.module_readiness_summary(agency_id),
            "airline_service_coverage": await self.airline_service_coverage_summary(agency_id),
            "sample_cases": self.sample_case_templates(),
            "remediation_links": REMEDIATION_LINKS,
            "read_only": read_only,
            "metadata_only": True,
            "notice": "Pilot Readiness stores diagnostic metadata only. It does not seed production records, reset data, execute providers, run AI, mutate operational records, or override human authority.",
            **self.safety_flags(),
        }

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        profiles = await self.list_profiles(agency_id=agency_id)
        assessments = await self.list_assessments(agency_id=agency_id)
        checks = await self._find(PILOT_READINESS_CHECKS_COLLECTION, agency_id=agency_id)
        runs = await self.list_runs(agency_id=agency_id)
        issues = await self.list_issues(agency_id=agency_id)
        latest_assessment = assessments[0] if assessments else None
        return {
            "profile_count": len(profiles),
            "assessment_count": len(assessments),
            "check_count": len(checks),
            "golden_path_case_count": len(await self.list_cases(agency_id=agency_id)),
            "golden_path_run_count": len(runs),
            "open_issue_count": len([item for item in issues if item.get("issue_status") in {"open", "reopened", "in_review"}]),
            "critical_blocker_count": len([item for item in issues if item.get("severity") == "critical" and item.get("issue_status") in {"open", "reopened", "in_review"}]),
            "assessment_status_counts": self._counts(assessments, "assessment_status", READINESS_STATUSES),
            "check_status_counts": self._counts(checks, "status", CHECK_STATUSES),
            "check_family_counts": self._counts(checks, "check_family", CHECK_FAMILIES),
            "run_status_counts": self._counts(runs, "run_status", GOLDEN_PATH_STATUSES),
            "issue_status_counts": self._counts(issues, "issue_status", ISSUE_STATUSES),
            "latest_readiness_score": latest_assessment.get("readiness_score") if latest_assessment else None,
            "latest_assessment_status": latest_assessment.get("assessment_status") if latest_assessment else None,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def sample_case_templates(self) -> list[dict[str, Any]]:
        return [
            {
                **template,
                "metadata_only": True,
                "sample_template_auto_seed_disabled": True,
                "production_record_mutation_disabled": True,
            }
            for template in GOLDEN_PATH_CASE_TEMPLATES
        ]

    async def list_profiles(
        self,
        *,
        agency_id: str | None = None,
        profile_status: str | None = None,
        search: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if profile_status:
            filters["profile_status"] = self._normalize_code(profile_status)
        profiles = await self.db.collection(PILOT_READINESS_PROFILES_COLLECTION).find_many(filters or None)
        if not include_archived:
            profiles = [item for item in profiles if not item.get("archived")]
        profiles = [item for item in profiles if self._matches_search(item, search)]
        profiles.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [self._profile_projection(item) for item in profiles]

    async def get_profile(self, profile_id: str, agency_id: str | None = None) -> dict[str, Any]:
        return self._profile_projection(await self._require_profile(profile_id, agency_id=agency_id))

    async def create_profile(
        self,
        payload: PilotReadinessProfileCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data = self._normalize_profile_payload(data)
        data.setdefault("profile_reference", self._reference("PILOT-PROFILE"))
        data.setdefault("profile_status", "draft")
        data.setdefault("required_modules", list(DEFAULT_REQUIRED_MODULES))
        data.update(self.safety_flags())
        self._validate_no_forbidden_marker(data)
        record = PilotReadinessProfile(**data)
        created = await self.db.collection(PILOT_READINESS_PROFILES_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "pilot_readiness_profile": self._profile_projection(created),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_profile(
        self,
        profile_id: str,
        payload: PilotReadinessProfileUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_profile(profile_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        updates = self._normalize_profile_payload(updates)
        updates.update(self.safety_flags())
        self._validate_no_forbidden_marker(updates)
        updated = await self.db.collection(PILOT_READINESS_PROFILES_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise PilotReadinessError("Pilot readiness profile metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "pilot_readiness_profile": self._profile_projection(updated),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def run_assessment(
        self,
        payload: PilotReadinessAssessmentRunRequest,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        request = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            request["agency_id"] = agency_id
        self._validate_no_forbidden_marker(request)
        profile = None
        if request.get("profile_id"):
            profile = await self._require_profile(request["profile_id"], agency_id=agency_id)
        context = self._assessment_context(profile, request)
        assessment = PilotReadinessAssessment(
            agency_id=context.get("agency_id"),
            profile_id=context.get("profile_id"),
            assessment_reference=self._reference("PILOT-ASSESS"),
            assessment_status="assessing",
            airline_code=context.get("airline_code"),
            service_family_codes=context.get("service_family_codes", []),
            service_codes=context.get("service_codes", []),
            generated_at=self._datetime_now(),
            generated_by=self._actor(user),
            summary="Pilot readiness assessment is a deterministic metadata diagnostic. It does not mutate production operational records.",
            metadata={"request": request, "profile_reference": (profile or {}).get("profile_reference")},
            **self.safety_flags(),
        )
        created = await self.db.collection(PILOT_READINESS_ASSESSMENTS_COLLECTION).insert_one(assessment.model_dump(mode="json"))
        checks = await self._build_assessment_checks(created["id"], context)
        created_checks = []
        for check in checks:
            created_checks.append(await self.db.collection(PILOT_READINESS_CHECKS_COLLECTION).insert_one(check.model_dump(mode="json")))
        score, component_scores, critical_count, high_count, warning_count = self._score_checks(created_checks)
        status = self._assessment_status(score, critical_count, high_count, context.get("minimum_score", 85))
        issues = []
        for check in created_checks:
            if check.get("status") in {"warning", "blocked", "failed", "unknown"}:
                issue = await self._create_issue_from_check(created, check, user)
                issues.append(issue)
        updated = await self.db.collection(PILOT_READINESS_ASSESSMENTS_COLLECTION).update_one(
            {"id": created["id"]},
            {
                "assessment_status": status,
                "readiness_score": score,
                "component_scores": component_scores,
                "critical_blocker_count": critical_count,
                "high_issue_count": high_count,
                "warning_count": warning_count,
                "check_ids": [check["id"] for check in created_checks],
                "issue_ids": [issue["id"] for issue in issues],
                "next_actions": self._next_actions(created_checks),
                "metadata": {
                    **created.get("metadata", {}),
                    "deterministic_scoring": True,
                    "severity_deductions": SEVERITY_DEDUCTIONS,
                    "critical_blockers_prevent_pilot_ready": True,
                },
                **self.safety_flags(),
            },
        )
        if not updated:
            raise PilotReadinessError("Pilot readiness assessment metadata could not be finalized.")
        return {
            "phase": PHASE_LABEL,
            "pilot_readiness_assessment": await self._assessment_projection(updated),
            "checks": [self._check_projection(check) for check in created_checks],
            "issues": [self._issue_projection(issue) for issue in issues],
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_assessments(
        self,
        *,
        agency_id: str | None = None,
        assessment_status: str | None = None,
        profile_id: str | None = None,
        airline_code: str | None = None,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if assessment_status:
            filters["assessment_status"] = self._normalize_code(assessment_status)
        if profile_id:
            filters["profile_id"] = profile_id
        if airline_code:
            filters["airline_code"] = self._normalize_airline(airline_code)
        assessments = await self.db.collection(PILOT_READINESS_ASSESSMENTS_COLLECTION).find_many(filters or None)
        assessments.sort(key=lambda item: self._sort_text(item.get("generated_at") or item.get("created_at")), reverse=True)
        return [await self._assessment_projection(item, include_children=False) for item in assessments]

    async def get_assessment(self, assessment_id: str, agency_id: str | None = None) -> dict[str, Any]:
        return await self._assessment_projection(await self._require_assessment(assessment_id, agency_id=agency_id))

    async def list_cases(
        self,
        *,
        agency_id: str | None = None,
        case_family: str | None = None,
        scenario_type: str | None = None,
        case_status: str | None = None,
        search: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if case_family:
            filters["case_family"] = self._normalize_code(case_family)
        if scenario_type:
            filters["scenario_type"] = self._normalize_code(scenario_type)
        if case_status:
            filters["case_status"] = self._normalize_code(case_status)
        cases = await self.db.collection(PILOT_GOLDEN_PATH_CASES_COLLECTION).find_many(filters or None)
        if not include_archived:
            cases = [item for item in cases if not item.get("archived")]
        cases = [item for item in cases if self._matches_search(item, search)]
        cases.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [self._case_projection(item) for item in cases]

    async def get_case(self, case_id: str, agency_id: str | None = None) -> dict[str, Any]:
        return self._case_projection(await self._require_case(case_id, agency_id=agency_id))

    async def create_case(
        self,
        payload: PilotGoldenPathCaseCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data = self._normalize_case_payload(data)
        data.setdefault("case_reference", self._reference("PILOT-GP"))
        data.setdefault("case_status", "draft")
        data.update(self.safety_flags())
        data["sample_template_auto_seed_disabled"] = True
        self._validate_no_forbidden_marker(data)
        record = PilotGoldenPathCase(**data)
        created = await self.db.collection(PILOT_GOLDEN_PATH_CASES_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "pilot_golden_path_case": self._case_projection(created),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_case(
        self,
        case_id: str,
        payload: PilotGoldenPathCaseUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_case(case_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        updates = self._normalize_case_payload(updates)
        updates.update(self.safety_flags())
        self._validate_no_forbidden_marker(updates)
        updated = await self.db.collection(PILOT_GOLDEN_PATH_CASES_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise PilotReadinessError("Pilot golden-path case metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "pilot_golden_path_case": self._case_projection(updated),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def run_golden_path_case(
        self,
        case_id: str,
        payload: PilotGoldenPathRunCreateRequest,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        case = await self._require_case(case_id, agency_id=agency_id)
        request = payload.model_dump(mode="json", exclude_none=True)
        self._validate_no_forbidden_marker(request)
        stage_results = await self._build_golden_path_stage_results(case)
        status = self._worst_stage_status(stage_results)
        score = self._score_stages(stage_results)
        blocking_stage = next((stage["stage_code"] for stage in stage_results if stage.get("status") in {"blocked", "failed"}), None)
        run = PilotGoldenPathRun(
            agency_id=case.get("agency_id"),
            case_id=case["id"],
            case_reference=case.get("case_reference"),
            run_reference=self._reference("PILOT-RUN"),
            run_status=status,
            readiness_score=score,
            stage_results=stage_results,
            blocking_stage=blocking_stage,
            client_message=self._client_message_for_run(case, status),
            internal_trace=[
                {
                    "trace_key": "metadata_diagnostic",
                    "summary": "Golden-path run evaluated stored metadata snapshots only.",
                    "stage_count": len(stage_results),
                }
            ],
            started_at=self._datetime_now(),
            completed_at=self._datetime_now(),
            created_by=self._actor(user),
            metadata={"request": request, "scenario_type": case.get("scenario_type")},
            **self.safety_flags(),
        )
        created = await self.db.collection(PILOT_GOLDEN_PATH_RUNS_COLLECTION).insert_one(run.model_dump(mode="json"))
        issues = []
        for stage in stage_results:
            if stage.get("status") in {"warning", "blocked", "failed", "unknown"}:
                issues.append(await self._create_issue_from_stage(created, case, stage, user))
        updated = await self.db.collection(PILOT_GOLDEN_PATH_RUNS_COLLECTION).update_one(
            {"id": created["id"]},
            {"issue_ids": [issue["id"] for issue in issues], **self.safety_flags()},
        )
        if not updated:
            raise PilotReadinessError("Pilot golden-path run metadata could not be finalized.")
        return {
            "phase": PHASE_LABEL,
            "pilot_golden_path_run": self._run_projection(updated),
            "issues": [self._issue_projection(issue) for issue in issues],
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_runs(
        self,
        *,
        agency_id: str | None = None,
        case_id: str | None = None,
        run_status: str | None = None,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if case_id:
            filters["case_id"] = case_id
        if run_status:
            filters["run_status"] = self._normalize_code(run_status)
        runs = await self.db.collection(PILOT_GOLDEN_PATH_RUNS_COLLECTION).find_many(filters or None)
        runs.sort(key=lambda item: self._sort_text(item.get("started_at") or item.get("created_at")), reverse=True)
        return [self._run_projection(item) for item in runs]

    async def list_issues(
        self,
        *,
        agency_id: str | None = None,
        assessment_id: str | None = None,
        golden_path_run_id: str | None = None,
        issue_status: str | None = None,
        severity: str | None = None,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if assessment_id:
            filters["assessment_id"] = assessment_id
        if golden_path_run_id:
            filters["golden_path_run_id"] = golden_path_run_id
        if issue_status:
            filters["issue_status"] = self._normalize_code(issue_status)
        if severity:
            filters["severity"] = self._normalize_code(severity)
        issues = await self.db.collection(PILOT_READINESS_ISSUES_COLLECTION).find_many(filters or None)
        issues.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [self._issue_projection(item) for item in issues]

    async def update_issue(
        self,
        issue_id: str,
        payload: PilotReadinessIssueUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_issue(issue_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if updates.get("issue_status"):
            updates["issue_status"] = self._normalize_code(updates["issue_status"])
            if updates["issue_status"] not in ISSUE_STATUSES:
                raise PilotReadinessError(f"Unsupported issue_status metadata value: {updates['issue_status']}.")
        updates.update(self.safety_flags())
        self._validate_no_forbidden_marker(updates)
        updated = await self.db.collection(PILOT_READINESS_ISSUES_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise PilotReadinessError("Pilot readiness issue metadata could not be updated.")
        return {"phase": PHASE_LABEL, "pilot_readiness_issue": self._issue_projection(updated), "metadata_only": True, **self.safety_flags()}

    async def resolve_issue(
        self,
        issue_id: str,
        payload: PilotReadinessIssueUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_issue(issue_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        updates.update(
            {
                "issue_status": "resolved",
                "resolved_by": self._actor(user),
                "resolved_at": self._now(),
                **self.safety_flags(),
            }
        )
        updated = await self.db.collection(PILOT_READINESS_ISSUES_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise PilotReadinessError("Pilot readiness issue metadata could not be resolved.")
        return {"phase": PHASE_LABEL, "pilot_readiness_issue": self._issue_projection(updated), "metadata_only": True, **self.safety_flags()}

    async def reopen_issue(
        self,
        issue_id: str,
        payload: PilotReadinessIssueUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_issue(issue_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        updates.update(
            {
                "issue_status": "reopened",
                "reopened_at": self._now(),
                **self.safety_flags(),
            }
        )
        updated = await self.db.collection(PILOT_READINESS_ISSUES_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise PilotReadinessError("Pilot readiness issue metadata could not be reopened.")
        return {"phase": PHASE_LABEL, "pilot_readiness_issue": self._issue_projection(updated), "metadata_only": True, **self.safety_flags()}

    async def module_readiness_summary(self, agency_id: str | None = None) -> list[dict[str, Any]]:
        modules = []
        for module_code, collection in MODULE_COLLECTIONS.items():
            count = await self._count(collection, agency_id=agency_id)
            links = REMEDIATION_LINKS.get(module_code, {})
            modules.append(
                {
                    "module_code": module_code,
                    "module_name": self._label(module_code),
                    "collection": collection,
                    "metadata_record_count": count,
                    "status": "passed" if count else "warning",
                    "platform_route": links.get("platform"),
                    "agency_route": links.get("agency"),
                    "metadata_only": True,
                }
            )
        return modules

    async def airline_service_coverage_summary(self, agency_id: str | None = None) -> dict[str, Any]:
        coverage_profiles = await self._find("airline_service_coverage_profiles", agency_id=agency_id)
        coverage_cells = await self._find("airline_service_coverage_cells", agency_id=agency_id)
        coverage_gaps = await self._find("airline_knowledge_gaps", agency_id=agency_id)
        policies = await self._find("visual_policy_editor_cards", agency_id=agency_id)
        capabilities = await self._find("airline_capability_matrix", agency_id=agency_id)
        publications = await self._find("airline_knowledge_publications", agency_id=agency_id)
        service_families = sorted({str(item.get("service_family") or item.get("capability_family") or "") for item in policies + capabilities if item.get("service_family") or item.get("capability_family")})
        airlines = sorted({str(item.get("airline") or item.get("airline_code") or "") for item in policies + capabilities + publications if item.get("airline") or item.get("airline_code")})
        return {
            "airline_count": len(airlines),
            "service_family_count": len(service_families),
            "airlines": airlines,
            "service_families": service_families,
            "policy_record_count": len(policies),
            "capability_record_count": len(capabilities),
            "publication_record_count": len(publications),
            "coverage_profile_count": len(coverage_profiles),
            "coverage_cell_count": len(coverage_cells),
            "operational_ready_cell_count": len([item for item in coverage_cells if item.get("operational_ready")]),
            "critical_gap_count": len([item for item in coverage_gaps if item.get("critical")]),
            "deterministic_coverage_assessment_available": bool(coverage_cells),
            "coverage_remediation_route": REMEDIATION_LINKS["airline_service_coverage"],
            "metadata_only": True,
        }

    async def _build_assessment_checks(self, assessment_id: str, context: dict[str, Any]) -> list[PilotReadinessCheck]:
        checks: list[PilotReadinessCheck] = []

        def add(
            check_family: str,
            check_code: str,
            label: str,
            status: str,
            severity: str,
            module_code: str | None = None,
            expected_signal: str | None = None,
            observed_signal: str | None = None,
            blockers: list[dict[str, Any]] | None = None,
            warnings: list[dict[str, Any]] | None = None,
            details: dict[str, Any] | None = None,
        ) -> None:
            links = REMEDIATION_LINKS.get(module_code or "", {})
            checks.append(
                PilotReadinessCheck(
                    agency_id=context.get("agency_id"),
                    assessment_id=assessment_id,
                    check_reference=self._reference("PILOT-CHECK"),
                    check_code=check_code,
                    check_family=check_family,
                    label=label,
                    status=status,
                    severity=severity,
                    module_code=module_code,
                    module_name=self._label(module_code) if module_code else None,
                    expected_signal=expected_signal,
                    observed_signal=observed_signal,
                    remediation_route=links.get("platform"),
                    agency_remediation_route=links.get("agency"),
                    blockers=blockers or [],
                    warnings=warnings or [],
                    details=details or {},
                    computed_at=self._datetime_now(),
                    **self.safety_flags(),
                )
            )

        add("system_health", "active_phase_marker", "Active phase marker registered", "passed", "critical", expected_signal=PHASE_LABEL, observed_signal=PHASE_LABEL)
        add("system_health", "safety_boundaries", "Metadata-only safety boundaries present", "passed", "critical", expected_signal="no automation/provider/AI/destructive reset", observed_signal="disabled flags are present")

        required_domains = context.get("required_reference_domains") or []
        existing_domains = await self._reference_domains()
        missing_domains = [domain for domain in required_domains if domain not in existing_domains]
        if required_domains and missing_domains:
            add(
                "reference_data",
                "required_reference_domains",
                "Required reference domains are available",
                "blocked",
                "critical",
                "reference_data_engine",
                expected_signal=", ".join(required_domains),
                observed_signal=f"missing: {', '.join(missing_domains)}",
                blockers=[{"missing_reference_domains": missing_domains}],
            )
        else:
            add(
                "reference_data",
                "required_reference_domains",
                "Required reference domains are available",
                "passed" if required_domains else "warning",
                "medium",
                "reference_data_engine",
                expected_signal=", ".join(required_domains) if required_domains else "profile-specific reference domain list",
                observed_signal=", ".join(existing_domains) if existing_domains else "no required domains specified",
                warnings=[] if required_domains else [{"warning_key": "no_domain_scope", "label": "No pilot-specific reference domain scope was supplied."}],
            )

        required_modules = context.get("required_modules") or list(DEFAULT_REQUIRED_MODULES)
        module_summaries = await self.module_readiness_summary(context.get("agency_id"))
        module_by_code = {item["module_code"]: item for item in module_summaries}
        for module_code in required_modules:
            module = module_by_code.get(module_code)
            if not module:
                add(
                    "knowledge_production",
                    f"module_registered_{module_code}",
                    f"{self._label(module_code)} module is registered",
                    "blocked",
                    "critical",
                    module_code,
                    expected_signal="registered module and route",
                    observed_signal="module not in pilot readiness map",
                    blockers=[{"module_code": module_code, "reason": "module_not_registered"}],
                )
                continue
            family = self._family_for_module(module_code)
            if module["metadata_record_count"] > 0:
                add(family, f"metadata_present_{module_code}", f"{module['module_name']} has metadata records", "passed", "medium", module_code, "at least one metadata record", f"{module['metadata_record_count']} records")
            else:
                severity = "high" if module_code in {"visual_policy_editor", "knowledge_quality_assurance", "airline_knowledge_publishing", "passenger_service_feasibility", "airline_recommendations", "intelligent_offer_builder"} else "medium"
                add(
                    family,
                    f"metadata_present_{module_code}",
                    f"{module['module_name']} has metadata records",
                    "warning",
                    severity,
                    module_code,
                    "at least one metadata record",
                    "0 records",
                    warnings=[{"module_code": module_code, "reason": "metadata_gap"}],
                )

        add("pilot_operations", "production_seed_disabled", "Production auto-seeding is disabled", "passed", "critical", expected_signal="sample cases remain templates", observed_signal="sample templates are exposed without database insertion")
        add("pilot_operations", "destructive_reset_disabled", "Destructive reset is disabled", "passed", "critical", expected_signal="no reset endpoint", observed_signal="diagnostic records are additive only")
        return checks

    async def _build_golden_path_stage_results(self, case: dict[str, Any]) -> list[dict[str, Any]]:
        scenario_type = self._normalize_code(case.get("scenario_type"))
        counts = {module: await self._count(collection, agency_id=case.get("agency_id")) for module, collection in MODULE_COLLECTIONS.items()}
        stage_to_module = {
            "knowledge_source_ready": "reference_data_engine",
            "import_template_ready": "knowledge_import_templates",
            "normalisation_ready": "knowledge_normalisation",
            "policy_rule_pricing_ready": "visual_policy_editor",
            "quality_assurance_ready": "knowledge_quality_assurance",
            "publishing_ready": "airline_knowledge_publishing",
            "scenario_expectation_ready": "operational_scenario_testing",
            "request_segment_service_ready": "request_segment_services",
            "feasibility_ready": "passenger_service_feasibility",
            "recommendation_ready": "airline_recommendations",
            "intelligent_offer_ready": "intelligent_offer_builder",
            "trip_booking_readiness": "passenger_service_workflows",
            "operational_follow_up_ready": "operational_timelines",
        }
        results: list[dict[str, Any]] = []
        for stage_code in GOLDEN_PATH_STAGE_CODES:
            module_code = stage_to_module.get(stage_code)
            status = "passed" if counts.get(module_code or "", 0) else "warning"
            summary = f"{self._label(stage_code)} metadata check completed."
            warnings: list[dict[str, Any]] = []
            blockers: list[dict[str, Any]] = []
            if status == "warning":
                warnings.append({"warning_key": "metadata_absent", "module_code": module_code, "label": "No existing metadata records were found for this stage."})
            if stage_code == "policy_rule_pricing_ready" and scenario_type == "unknown_policy":
                status = "warning"
                summary = "Unknown policy case did not crash; human review remains required."
                warnings.append({"warning_key": "unknown_policy", "label": "No operational truth was invented for an unknown policy."})
            if stage_code == "policy_rule_pricing_ready" and scenario_type == "blocked_policy":
                status = "blocked"
                summary = "Blocked policy case remained informational and did not execute a rollout or offer action."
                blockers.append({"blocker_key": "blocked_policy", "label": "Policy outcome blocks pilot readiness for this case."})
            if stage_code in {"feasibility_ready", "recommendation_ready"} and scenario_type == "conditional_policy":
                status = "warning"
                warnings.append({"warning_key": "conditional_review", "label": "Conditional policy requires human operational review."})
            links = REMEDIATION_LINKS.get(module_code or "", {})
            results.append(
                {
                    "stage_code": stage_code,
                    "stage_label": self._label(stage_code),
                    "status": status,
                    "module_code": module_code,
                    "platform_route": links.get("platform"),
                    "agency_route": links.get("agency"),
                    "summary": summary,
                    "warnings": warnings,
                    "blockers": blockers,
                    "evidence": case.get("evidence_links") or [],
                    "output_references": [],
                    "client_message": self._client_stage_message(stage_code, status),
                    "internal_trace": {
                        "metadata_record_count": counts.get(module_code or "", 0),
                        "scenario_type": scenario_type,
                        "no_provider_execution": True,
                    },
                }
            )
        return results

    async def _create_issue_from_check(self, assessment: dict[str, Any], check: dict[str, Any], user: dict) -> dict[str, Any]:
        issue = PilotReadinessIssue(
            agency_id=assessment.get("agency_id"),
            assessment_id=assessment.get("id"),
            issue_reference=self._reference("PILOT-ISSUE"),
            issue_family=check.get("check_family") or "pilot_operations",
            severity=check.get("severity") or "medium",
            issue_status="open",
            title=f"{check.get('label') or check.get('check_code')} is {check.get('status')}",
            description=check.get("observed_signal"),
            related_module=check.get("module_code"),
            remediation_route=check.get("remediation_route"),
            agency_remediation_route=check.get("agency_remediation_route"),
            created_by=self._actor(user),
            metadata={"source": "assessment_check", "check_id": check.get("id"), "check_status": check.get("status")},
            **self.safety_flags(),
        )
        return await self.db.collection(PILOT_READINESS_ISSUES_COLLECTION).insert_one(issue.model_dump(mode="json"))

    async def _create_issue_from_stage(self, run: dict[str, Any], case: dict[str, Any], stage: dict[str, Any], user: dict) -> dict[str, Any]:
        severity = "critical" if stage.get("status") in {"blocked", "failed"} else "medium"
        issue = PilotReadinessIssue(
            agency_id=run.get("agency_id"),
            golden_path_run_id=run.get("id"),
            issue_reference=self._reference("PILOT-ISSUE"),
            issue_family="golden_path",
            severity=severity,
            issue_status="open",
            title=f"{stage.get('stage_label')} is {stage.get('status')}",
            description=stage.get("summary"),
            related_module=stage.get("module_code"),
            remediation_route=stage.get("platform_route"),
            agency_remediation_route=stage.get("agency_route"),
            created_by=self._actor(user),
            metadata={"source": "golden_path_stage", "case_id": case.get("id"), "stage_code": stage.get("stage_code")},
            **self.safety_flags(),
        )
        return await self.db.collection(PILOT_READINESS_ISSUES_COLLECTION).insert_one(issue.model_dump(mode="json"))

    def _score_checks(self, checks: list[dict[str, Any]]) -> tuple[int, dict[str, Any], int, int, int]:
        penalty = 0
        family_penalties = {family: 0 for family in CHECK_FAMILIES}
        critical_count = 0
        high_count = 0
        warning_count = 0
        for check in checks:
            if check.get("status") not in {"warning", "blocked", "failed", "unknown"}:
                continue
            severity = check.get("severity") or "low"
            deduction = SEVERITY_DEDUCTIONS.get(severity, 3)
            penalty += deduction
            family_penalties[check.get("check_family") or "pilot_operations"] = family_penalties.get(check.get("check_family") or "pilot_operations", 0) + deduction
            if severity == "critical" and check.get("status") in {"blocked", "failed"}:
                critical_count += 1
            if severity == "high":
                high_count += 1
            if check.get("status") == "warning":
                warning_count += 1
        score = max(0, 100 - penalty)
        component_scores = {family: max(0, 100 - family_penalties.get(family, 0)) for family in CHECK_FAMILIES}
        return score, component_scores, critical_count, high_count, warning_count

    def _assessment_status(self, score: int, critical_count: int, high_count: int, minimum_score: int) -> str:
        if critical_count:
            return "blocked"
        if score >= minimum_score and high_count == 0:
            return "pilot_ready"
        if score >= 70:
            return "conditionally_ready"
        if score >= 50:
            return "needs_work"
        return "blocked"

    def _score_stages(self, stages: list[dict[str, Any]]) -> int:
        penalty = 0
        for stage in stages:
            if stage.get("status") == "warning":
                penalty += 5
            elif stage.get("status") == "unknown":
                penalty += 7
            elif stage.get("status") == "blocked":
                penalty += 25
            elif stage.get("status") == "failed":
                penalty += 40
        return max(0, 100 - penalty)

    def _worst_stage_status(self, stages: list[dict[str, Any]]) -> str:
        if any(stage.get("status") == "failed" for stage in stages):
            return "failed"
        if any(stage.get("status") == "blocked" for stage in stages):
            return "blocked"
        if any(stage.get("status") == "warning" for stage in stages):
            return "warning"
        if any(stage.get("status") == "unknown" for stage in stages):
            return "unknown"
        return "passed"

    def _assessment_context(self, profile: dict[str, Any] | None, request: dict[str, Any]) -> dict[str, Any]:
        profile = profile or {}
        service_family_codes = request.get("service_family_codes") or profile.get("target_service_families") or []
        service_codes = request.get("service_codes") or profile.get("target_service_codes") or []
        airline_code = request.get("airline_code") or ((profile.get("target_airline_codes") or [None])[0])
        return {
            "agency_id": request.get("agency_id") or profile.get("agency_id"),
            "profile_id": profile.get("id") or request.get("profile_id"),
            "airline_code": self._normalize_airline(airline_code) if airline_code else None,
            "service_family_codes": [self._normalize_code(value) for value in service_family_codes],
            "service_codes": [str(value).strip().upper() for value in service_codes],
            "required_reference_domains": [self._normalize_code(value) for value in (request.get("required_reference_domains") or profile.get("required_reference_domains") or [])],
            "required_modules": [self._normalize_code(value) for value in (request.get("required_modules") or profile.get("required_modules") or DEFAULT_REQUIRED_MODULES)],
            "minimum_score": int(request.get("minimum_score") or profile.get("minimum_score") or 85),
        }

    def _next_actions(self, checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        actions = []
        for check in checks:
            if check.get("status") in {"warning", "blocked", "failed", "unknown"}:
                actions.append(
                    {
                        "action_key": check.get("check_code"),
                        "label": check.get("label"),
                        "severity": check.get("severity"),
                        "platform_route": check.get("remediation_route"),
                        "agency_route": check.get("agency_remediation_route"),
                    }
                )
        return actions

    async def _assessment_projection(self, item: dict[str, Any], *, include_children: bool = True) -> dict[str, Any]:
        projected = dict(item)
        if include_children:
            checks = await self.db.collection(PILOT_READINESS_CHECKS_COLLECTION).find_many({"assessment_id": item["id"]})
            issues = await self.db.collection(PILOT_READINESS_ISSUES_COLLECTION).find_many({"assessment_id": item["id"]})
            projected["checks"] = [self._check_projection(check) for check in checks]
            projected["issues"] = [self._issue_projection(issue) for issue in issues]
        projected["score_section"] = {
            "readiness_score": projected.get("readiness_score"),
            "assessment_status": projected.get("assessment_status"),
            "component_scores": projected.get("component_scores") or {},
            "critical_blocker_count": projected.get("critical_blocker_count") or 0,
            "high_issue_count": projected.get("high_issue_count") or 0,
            "warning_count": projected.get("warning_count") or 0,
        }
        projected["scope_section"] = {
            "agency_id": projected.get("agency_id"),
            "profile_id": projected.get("profile_id"),
            "airline_code": projected.get("airline_code"),
            "service_family_codes": projected.get("service_family_codes") or [],
            "service_codes": projected.get("service_codes") or [],
        }
        projected["boundary_section"] = self.safety_flags()
        projected.update(self.safety_flags())
        return projected

    def _profile_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["scope_section"] = {
            "target_airline_codes": projected.get("target_airline_codes") or [],
            "target_service_families": projected.get("target_service_families") or [],
            "target_service_codes": projected.get("target_service_codes") or [],
            "required_reference_domains": projected.get("required_reference_domains") or [],
            "required_modules": projected.get("required_modules") or [],
            "minimum_score": projected.get("minimum_score"),
        }
        projected["boundary_section"] = self.safety_flags()
        projected.update(self.safety_flags())
        return projected

    def _check_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["route_section"] = {"platform_route": projected.get("remediation_route"), "agency_route": projected.get("agency_remediation_route")}
        projected.update(self.safety_flags())
        return projected

    def _case_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["case_section"] = {
            "case_reference": projected.get("case_reference"),
            "case_family": projected.get("case_family"),
            "scenario_type": projected.get("scenario_type"),
            "case_status": projected.get("case_status"),
        }
        projected["boundary_section"] = self.safety_flags()
        projected.update(self.safety_flags())
        return projected

    def _run_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["stage_count"] = len(projected.get("stage_results") or [])
        projected["client_internal_message_separated"] = bool(projected.get("client_message") is not None and projected.get("internal_trace") is not None)
        projected["boundary_section"] = self.safety_flags()
        projected.update(self.safety_flags())
        return projected

    def _issue_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["route_section"] = {"platform_route": projected.get("remediation_route"), "agency_route": projected.get("agency_remediation_route")}
        projected.update(self.safety_flags())
        return projected

    async def _reference_domains(self) -> list[str]:
        records = await self.db.collection("reference_data_domains").find_many()
        domains = []
        for item in records:
            for key in ["domain_code", "code", "slug", "name"]:
                if item.get(key):
                    domains.append(self._normalize_code(item[key]))
                    break
        return sorted(set(domains))

    async def _count(self, collection: str, agency_id: str | None = None) -> int:
        return len(await self._find(collection, agency_id=agency_id))

    async def _find(self, collection: str, agency_id: str | None = None) -> list[dict[str, Any]]:
        if agency_id:
            scoped = await self.db.collection(collection).find_many({"agency_id": agency_id})
            global_items = await self.db.collection(collection).find_many({"agency_id": None})
            return scoped + global_items
        return await self.db.collection(collection).find_many()

    async def _require_profile(self, profile_id: str, agency_id: str | None = None) -> dict[str, Any]:
        return await self._require(PILOT_READINESS_PROFILES_COLLECTION, profile_id, "profile_reference", "Pilot readiness profile metadata not found.", agency_id)

    async def _require_assessment(self, assessment_id: str, agency_id: str | None = None) -> dict[str, Any]:
        return await self._require(PILOT_READINESS_ASSESSMENTS_COLLECTION, assessment_id, "assessment_reference", "Pilot readiness assessment metadata not found.", agency_id)

    async def _require_case(self, case_id: str, agency_id: str | None = None) -> dict[str, Any]:
        return await self._require(PILOT_GOLDEN_PATH_CASES_COLLECTION, case_id, "case_reference", "Pilot golden-path case metadata not found.", agency_id)

    async def _require_issue(self, issue_id: str, agency_id: str | None = None) -> dict[str, Any]:
        return await self._require(PILOT_READINESS_ISSUES_COLLECTION, issue_id, "issue_reference", "Pilot readiness issue metadata not found.", agency_id)

    async def _require(self, collection: str, record_id: str, reference_field: str, message: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": record_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(collection).find_one(filters)
        if not item:
            filters = {reference_field: record_id}
            if agency_id:
                filters["agency_id"] = agency_id
            item = await self.db.collection(collection).find_one(filters)
        if not item:
            raise PilotReadinessError(message)
        return item

    def _normalize_profile_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(data)
        for key in ["profile_status"]:
            if key in normalized and normalized[key] is not None:
                normalized[key] = self._normalize_code(normalized[key])
        for key in ["target_service_families", "required_reference_domains", "required_modules"]:
            if key in normalized and normalized[key] is not None:
                normalized[key] = [self._normalize_code(value) for value in normalized[key]]
        if "target_airline_codes" in normalized and normalized["target_airline_codes"] is not None:
            normalized["target_airline_codes"] = [self._normalize_airline(value) for value in normalized["target_airline_codes"]]
        if "target_service_codes" in normalized and normalized["target_service_codes"] is not None:
            normalized["target_service_codes"] = [str(value).strip().upper() for value in normalized["target_service_codes"]]
        return normalized

    def _normalize_case_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(data)
        for key in ["case_family", "scenario_type", "case_status"]:
            if key in normalized and normalized[key] is not None:
                normalized[key] = self._normalize_code(normalized[key])
        if "airline_code" in normalized and normalized["airline_code"] is not None:
            normalized["airline_code"] = self._normalize_airline(normalized["airline_code"])
        return normalized

    def _family_for_module(self, module_code: str) -> str:
        if module_code in {"reference_data_engine"}:
            return "reference_data"
        if module_code in {"airline_capability_matrix", "service_parameter_taxonomies"}:
            return "airline_service_coverage"
        if module_code in {"request_segment_services", "client_passenger_master", "passenger_master"}:
            return "operational_precision"
        if module_code in {"passenger_service_feasibility", "airline_recommendations", "operational_intelligence_cases"}:
            return "evaluation_recommendation"
        if module_code in {"intelligent_offer_builder"}:
            return "offer_readiness"
        if module_code in {"operational_timelines", "passenger_service_workflows"}:
            return "pilot_operations"
        return "knowledge_production"

    def _client_message_for_run(self, case: dict[str, Any], status: str) -> str:
        if status in {"blocked", "failed"}:
            return "This passenger service case needs manual review before it can be considered pilot-ready."
        if status == "warning":
            return "This passenger service case is reviewable, but some operational metadata needs human confirmation."
        return "This passenger service case has enough stored metadata for pilot review."

    def _client_stage_message(self, stage_code: str, status: str) -> str:
        if status in {"blocked", "failed"}:
            return f"{self._label(stage_code)} needs human review."
        if status == "warning":
            return f"{self._label(stage_code)} has a metadata warning."
        return f"{self._label(stage_code)} passed metadata review."

    def _validate_no_forbidden_marker(self, data: dict[str, Any]) -> None:
        forbidden = [
            "provider_enabled",
            "gds_connect",
            "ndc_connect",
            "openai",
            "llm_prompt",
            "background_task_enabled",
            "schedule_job",
            "auto_seed_enabled",
            "destructive_reset_enabled",
            "mutate_production_records_enabled",
            "execute_booking",
            "send_email",
            "send_sms",
            "webhook_execute",
            "scrape_enabled",
        ]
        serialized = str(data).lower()
        for marker in forbidden:
            if marker in serialized:
                raise PilotReadinessError(f"Forbidden non-metadata implementation marker present: {marker}.")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "end_to_end_stabilization_pilot_readiness_foundation": True,
            "production_seed_disabled": True,
            "production_record_mutation_disabled": True,
            "automation_disabled": True,
            "provider_integrations_disabled": True,
            "ai_disabled": True,
            "destructive_reset_disabled": True,
            "human_authority_final": True,
        }

    def _counts(self, items: list[dict[str, Any]], field: str, values: list[str]) -> dict[str, int]:
        return {value: len([item for item in items if item.get(field) == value]) for value in values}

    def _matches_search(self, item: dict[str, Any], search: str | None) -> bool:
        if not search:
            return True
        return search.lower() in str(item).lower()

    def _normalize_code(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_")

    def _normalize_airline(self, value: Any) -> str:
        return str(value or "").strip().upper()

    def _label(self, value: Any) -> str:
        return str(value or "").replace("_", " ").title()

    def _actor(self, user: dict) -> str:
        return str(user.get("email") or user.get("sub") or user.get("id") or "system")

    def _reference(self, prefix: str) -> str:
        return f"{prefix}-{self._now().replace(':', '').replace('-', '').replace('.', '')}"

    def _datetime_now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _now(self) -> str:
        return self._datetime_now().isoformat()

    def _sort_text(self, value: Any) -> str:
        return str(value or "")
