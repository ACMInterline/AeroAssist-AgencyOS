from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import KnowledgeQualityAssuranceReview, KnowledgeQualityAssuranceReviewCreate, KnowledgeQualityAssuranceReviewUpdate


PHASE_LABEL = "phase_55_2_airline_policy_evidence_source_governance_foundation"
KNOWLEDGE_QUALITY_ASSURANCE_REVIEWS_COLLECTION = "knowledge_quality_assurance_reviews"

QA_CHECKS = [
    "missing_evidence",
    "missing_effective_dates",
    "missing_pricing_applicability",
    "conflicting_support_status",
    "incomplete_service_parameters",
    "missing_documents",
    "unsupported_reference_values",
    "stale_review",
    "low_confidence",
    "operational_validation_pending",
    "duplicate_policy_card",
    "conflicting_rule",
    "incomplete_pricing_formula",
]
TARGET_TYPES = [
    "knowledge_acquisition",
    "reference_data_domain",
    "knowledge_import_template",
    "visual_policy_card",
    "pricing_formula",
    "operational_rule",
    "service_parameter_taxonomy",
    "capability_matrix",
    "operational_evaluation",
    "passenger_service_feasibility",
    "airline_recommendation",
    "offer_intelligence_package",
    "operational_intelligence_case",
]
QA_STATUSES = ["open", "in_review", "changes_requested", "recommended_for_approval", "blocked", "resolved", "archived"]
SEVERITY_LEVELS = ["info", "low", "medium", "high", "critical", "blocking"]
APPROVAL_RECOMMENDATIONS = ["no_recommendation", "ready_for_human_approval", "approve_after_changes", "hold", "reject"]


class KnowledgeQualityAssuranceError(ValueError):
    pass


class KnowledgeQualityAssuranceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        reviews = await self.list_reviews(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": reviews,
            "reviews": reviews,
            "summary": await self.summarize_counts(filters.get("agency_id")),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Knowledge QA stores review metadata and requested changes only. It does not auto-approve, publish, execute rules, use AI, call providers, or run background workers.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        reviews = await self.list_reviews(agency_id=agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": reviews,
            "reviews": reviews,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Agency Knowledge QA shows metadata-only review findings. Human authority remains final.",
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

    async def list_reviews(
        self,
        *,
        agency_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        airline_code: str | None = None,
        service_family: str | None = None,
        service_code: str | None = None,
        qa_status: str | None = None,
        severity: str | None = None,
        issue_check: str | None = None,
        approval_recommendation: str | None = None,
        search: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if target_type:
            filters["target_type"] = self._normalize_code(target_type)
        if target_id:
            filters["target_id"] = target_id
        if airline_code:
            filters["airline_code"] = self._normalize_airline(airline_code)
        if service_family:
            filters["service_family"] = self._normalize_code(service_family)
        if service_code:
            filters["service_code"] = self._normalize_service_code(service_code)
        if qa_status:
            filters["qa_status"] = self._normalize_code(qa_status)
        if severity:
            filters["severity"] = self._normalize_code(severity)
        if approval_recommendation:
            filters["approval_recommendation"] = self._normalize_code(approval_recommendation)

        items = await self.db.collection(KNOWLEDGE_QUALITY_ASSURANCE_REVIEWS_COLLECTION).find_many(filters or None)
        if issue_check:
            normalized_check = self._normalize_code(issue_check)
            items = [item for item in items if normalized_check in self._issue_checks(item.get("issues") or [])]
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("qa_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(
                item,
                [
                    "review_reference",
                    "target_type",
                    "target_id",
                    "airline_code",
                    "service_family",
                    "service_code",
                    "qa_status",
                    "issues",
                    "severity",
                    "reviewer",
                    "requested_changes",
                    "approval_recommendation",
                    "governance_links",
                    "metadata",
                ],
                search,
            )
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._review_projection(item) for item in items]

    async def get_review(self, review_id: str, agency_id: str | None = None) -> dict[str, Any]:
        item = await self._require_review(review_id, agency_id=agency_id)
        return await self._review_projection(item)

    async def create_review(
        self,
        payload: KnowledgeQualityAssuranceReviewCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data = self._normalize_payload(data)
        data.setdefault("review_reference", self._reference("KQA"))
        data.setdefault("qa_status", "open")
        data.setdefault("severity", "medium")
        data.setdefault("approval_recommendation", "no_recommendation")
        data.update(self.safety_flags())
        self._validate_payload(data)
        record = KnowledgeQualityAssuranceReview(**data)
        created = await self.db.collection(KNOWLEDGE_QUALITY_ASSURANCE_REVIEWS_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "knowledge_quality_assurance_review": await self._review_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_review(
        self,
        review_id: str,
        payload: KnowledgeQualityAssuranceReviewUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_review(review_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if agency_id:
            updates.pop("agency_id", None)
        updates = self._normalize_payload(updates)
        updates.update(self.safety_flags())
        self._validate_payload(updates, partial=True)
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(KNOWLEDGE_QUALITY_ASSURANCE_REVIEWS_COLLECTION).update_one(filters, updates)
        if not updated:
            raise KnowledgeQualityAssuranceError("Knowledge QA review metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "knowledge_quality_assurance_review": await self._review_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_review(self, review_id: str, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_review(review_id, agency_id=agency_id)
        updates = {
            "qa_status": "archived",
            "archived": True,
            "archived_at": self._now(),
            **self.safety_flags(),
        }
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(KNOWLEDGE_QUALITY_ASSURANCE_REVIEWS_COLLECTION).update_one(filters, updates)
        if not updated:
            raise KnowledgeQualityAssuranceError("Knowledge QA review metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "knowledge_quality_assurance_review": await self._review_projection(updated),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def summarize_counts(self, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        reviews = await self.db.collection(KNOWLEDGE_QUALITY_ASSURANCE_REVIEWS_COLLECTION).find_many(filters)
        active_reviews = [item for item in reviews if not item.get("archived") and item.get("qa_status") != "archived"]
        issue_count = sum(len(item.get("issues") or []) for item in reviews)
        requested_change_count = sum(len(item.get("requested_changes") or []) for item in reviews)
        governance_link_count = sum(len(item.get("governance_links") or []) for item in reviews)
        return {
            "knowledge_quality_assurance_review_count": len(reviews),
            "active_review_count": len(active_reviews),
            "issue_count": issue_count,
            "requested_change_count": requested_change_count,
            "governance_link_count": governance_link_count,
            "by_qa_status": self._counts(reviews, "qa_status", QA_STATUSES),
            "by_severity": self._counts(reviews, "severity", SEVERITY_LEVELS),
            "by_target_type": self._counts(reviews, "target_type", TARGET_TYPES),
            "by_approval_recommendation": self._counts(reviews, "approval_recommendation", APPROVAL_RECOMMENDATIONS),
            "by_issue_check": {check: len([item for item in reviews if check in self._issue_checks(item.get("issues") or [])]) for check in QA_CHECKS},
            "supported_check_count": len(QA_CHECKS),
            "supported_target_type_count": len(TARGET_TYPES),
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "target_type": TARGET_TYPES,
            "qa_status": QA_STATUSES,
            "severity": SEVERITY_LEVELS,
            "issue_check": QA_CHECKS,
            "approval_recommendation": APPROVAL_RECOMMENDATIONS,
            "airline_code": "IATA or internal airline code",
            "service_family": "service family code",
            "service_code": "SSR, OSI, or internal service code",
            "search": "reference, target, airline, service, issue, reviewer, requested change, recommendation, governance, or metadata",
            "metadata_only": True,
        }

    async def _review_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        issues = projected.get("issues") or []
        requested_changes = projected.get("requested_changes") or []
        projected["review_display_name"] = " / ".join(
            part
            for part in [
                projected.get("review_reference"),
                projected.get("target_type"),
                projected.get("qa_status"),
                projected.get("severity"),
            ]
            if part
        )
        projected["overview_section"] = {
            "review_reference": projected.get("review_reference"),
            "target_type": projected.get("target_type"),
            "target_id": projected.get("target_id"),
            "airline_code": projected.get("airline_code"),
            "service_family": projected.get("service_family"),
            "service_code": projected.get("service_code"),
            "qa_status": projected.get("qa_status"),
            "severity": projected.get("severity"),
        }
        projected["issues_section"] = {
            "issues": issues,
            "issue_count": len(issues),
            "supported_checks": QA_CHECKS,
        }
        projected["requested_changes_section"] = {
            "requested_changes": requested_changes,
            "requested_change_count": len(requested_changes),
        }
        projected["reviewer_section"] = {
            "reviewer": projected.get("reviewer") or {},
            "approval_recommendation": projected.get("approval_recommendation"),
            "auto_approval_disabled": True,
            "human_authority_final": True,
        }
        projected["governance_section"] = {
            "governance_links": projected.get("governance_links") or [],
            "approval_recommendation": projected.get("approval_recommendation"),
            "publishing_disabled": True,
        }
        projected["lifecycle_section"] = {
            "created_at": projected.get("created_at"),
            "updated_at": projected.get("updated_at"),
            "archived": projected.get("archived"),
            "archived_at": projected.get("archived_at"),
        }
        projected["boundary_section"] = self.safety_flags()
        projected.update(self.safety_flags())
        return projected

    async def _require_review(self, review_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": review_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(KNOWLEDGE_QUALITY_ASSURANCE_REVIEWS_COLLECTION).find_one(filters)
        if not item:
            raise KnowledgeQualityAssuranceError("Knowledge QA review metadata not found.")
        return item

    def _normalize_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(data)
        for field in ["target_type", "service_family", "qa_status", "severity", "approval_recommendation"]:
            if field in normalized and normalized[field] is not None:
                normalized[field] = self._normalize_code(normalized[field])
        if "airline_code" in normalized and normalized["airline_code"] is not None:
            normalized["airline_code"] = self._normalize_airline(normalized["airline_code"])
        if "service_code" in normalized and normalized["service_code"] is not None:
            normalized["service_code"] = self._normalize_service_code(normalized["service_code"])
        if "issues" in normalized and normalized["issues"] is not None:
            normalized["issues"] = self._normalize_issues(normalized.get("issues") or [])
        return normalized

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "target_type", TARGET_TYPES)
        self._validate_choice(data, "qa_status", QA_STATUSES)
        self._validate_choice(data, "severity", SEVERITY_LEVELS)
        self._validate_choice(data, "approval_recommendation", APPROVAL_RECOMMENDATIONS)
        self._validate_issues(data.get("issues") or [])
        self._reject_forbidden_metadata(data)
        if not partial:
            for field in ["target_type", "target_id"]:
                if not data.get(field):
                    raise KnowledgeQualityAssuranceError(f"{field} is required.")

    def _validate_choice(self, data: dict[str, Any], field: str, allowed: list[str]) -> None:
        if field not in data or data.get(field) is None:
            return
        if data[field] not in allowed:
            raise KnowledgeQualityAssuranceError(f"Unsupported {field} metadata value: {data[field]}.")

    def _validate_issues(self, issues: list[dict[str, Any]]) -> None:
        for check in self._issue_checks(issues):
            if check not in QA_CHECKS:
                raise KnowledgeQualityAssuranceError(f"Unsupported QA check metadata value: {check}.")

    def _normalize_issues(self, issues: list[Any]) -> list[Any]:
        normalized_issues = []
        for issue in issues:
            if not isinstance(issue, dict):
                normalized_issues.append(issue)
                continue
            normalized = dict(issue)
            if "check" in normalized and normalized["check"] is not None:
                normalized["check"] = self._normalize_code(normalized["check"])
            normalized_issues.append(normalized)
        return normalized_issues

    def _issue_checks(self, issues: list[Any]) -> list[str]:
        checks: list[str] = []
        for issue in issues:
            if isinstance(issue, dict) and issue.get("check") is not None:
                checks.append(str(issue.get("check")))
        return checks

    def _reject_forbidden_metadata(self, data: dict[str, Any]) -> None:
        forbidden = [
            "auto_" + "approval_enabled",
            "auto_approve",
            "auto_publish",
            "publish_approved",
            "execute_rule",
            "evaluate_rule",
            "ai_prompt",
            "llm_prompt",
            "chatcompletion",
            "provider_client",
            "background_task",
            "backgroundtasks",
        ]
        serialized = str(data).lower()
        for marker in forbidden:
            if marker in serialized:
                raise KnowledgeQualityAssuranceError(f"Forbidden non-metadata implementation marker present: {marker}.")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "knowledge_quality_assurance_foundation": True,
            "auto_approval_disabled": True,
            "publishing_disabled": True,
            "rule_execution_disabled": True,
            "ai_disabled": True,
            "provider_integrations_disabled": True,
            "background_workers_disabled": True,
            "human_authority_final": True,
        }

    def _normalize_code(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_")

    def _normalize_airline(self, value: Any) -> str:
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
