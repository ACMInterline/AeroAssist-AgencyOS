from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    FeatureBundleRolloutSummaryPack,
    FeatureBundleRolloutSummaryPackCreate,
    FeatureBundleRolloutSummaryPackUpdate,
    new_id,
)
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService
from services.feature_bundle_dependency_service import DEPENDENCY_COLLECTION
from services.feature_bundle_rollout_approval_service import APPROVAL_COLLECTION
from services.feature_bundle_rollout_change_request_service import CHANGE_REQUEST_COLLECTION
from services.feature_bundle_rollout_decision_service import DECISION_COLLECTION
from services.feature_bundle_rollout_issue_service import ISSUE_COLLECTION
from services.feature_bundle_rollout_readiness_service import READINESS_COLLECTION
from services.feature_bundle_rollout_risk_service import RISK_COLLECTION
from services.feature_bundle_rollout_rollback_plan_service import ROLLBACK_PLAN_COLLECTION
from services.feature_bundle_rollout_schedule_service import SCHEDULE_COLLECTION
from services.feature_bundle_rollout_timeline_service import TIMELINE_COLLECTION
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_56_2_journey_option_fare_brand_composition_workspace_foundation"

SUMMARY_PACK_COLLECTION = "feature_bundle_rollout_summary_packs"
PLAN_COLLECTION = "agency_feature_bundle_rollout_plans"
PACK_STATUSES = ["draft", "assembled", "reviewing", "ready", "archived"]
PACK_AUDIENCES = ["platform", "agency", "operations", "compliance", "executive"]


class FeatureBundleRolloutSummaryPackService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_summary_packs(
        self,
        *,
        rollout_plan_id: str | None = None,
        status: str | None = None,
        audience: str | None = None,
        bundle_id: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if rollout_plan_id:
            filters["rollout_plan_id"] = rollout_plan_id
        if status:
            filters["pack_status"] = status
        if audience:
            filters["generated_for_audience"] = audience
        packs = await self.db.collection(SUMMARY_PACK_COLLECTION).find_many(filters or None)
        if bundle_id:
            packs = [item for item in packs if bundle_id in (item.get("covered_bundle_ids") or [])]
        if not include_archived:
            packs = [item for item in packs if not item.get("deleted_at")]
        packs.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in packs]

    async def list_agency_summary_packs(
        self,
        agency_id: str,
        *,
        rollout_plan_id: str | None = None,
        status: str | None = None,
        audience: str | None = None,
        bundle_id: str | None = None,
    ) -> list[dict[str, Any]]:
        packs = await self.list_platform_summary_packs(
            rollout_plan_id=rollout_plan_id,
            status=status,
            audience=audience,
            bundle_id=bundle_id,
        )
        return [self._agency_projection(item, agency_id) for item in packs if item.get("agency_id") == agency_id]

    async def platform_response(
        self,
        *,
        rollout_plan_id: str | None = None,
        status: str | None = None,
        audience: str | None = None,
        bundle_id: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_summary_packs(
            rollout_plan_id=rollout_plan_id,
            status=status,
            audience=audience,
            bundle_id=bundle_id,
            include_archived=include_archived,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "summary_pack_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Feature bundle rollout summary packs are metadata only. They do not execute rollouts, automate deployments, activate or deactivate features, enforce entitlements, bill, call providers or external APIs, use AI, run workers or schedulers, notify users, send email, execute webhooks, publish, switch runtime behavior, generate PDFs, export files, or trigger automation.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        rollout_plan_id: str | None = None,
        status: str | None = None,
        audience: str | None = None,
        bundle_id: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_summary_packs(
            agency_id,
            rollout_plan_id=rollout_plan_id,
            status=status,
            audience=audience,
            bundle_id=bundle_id,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "summary_pack_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Feature bundle rollout summary pack metadata is read-only for this agency. It does not execute rollouts, activate or deactivate features, enforce access, bill, call providers or external APIs, use AI, notify users, send email, publish, generate PDFs, export files, switch runtime behavior, or automate actions.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_summary_packs(include_archived=True)
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "summary_pack_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_summary_packs(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "summary_pack_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_summary_pack(self, pack_id: str) -> dict[str, Any]:
        pack = await self._require_summary_pack(pack_id)
        return await self._platform_projection(pack)

    async def get_agency_summary_pack(self, agency_id: str, pack_id: str) -> dict[str, Any]:
        projected = await self.get_platform_summary_pack(pack_id)
        if projected.get("agency_id") != agency_id:
            raise ValueError("Feature bundle rollout summary pack metadata was not found for this agency.")
        return self._agency_projection(projected, agency_id)

    async def create_summary_pack(
        self,
        payload: FeatureBundleRolloutSummaryPackCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        self._validate_dimension("status", data.get("pack_status") or "draft", PACK_STATUSES)
        self._validate_dimension("audience", data.get("generated_for_audience") or "platform", PACK_AUDIENCES)
        pack = FeatureBundleRolloutSummaryPack(
            id=data.get("id") or new_id(),
            rollout_plan_id=data["rollout_plan_id"],
            pack_title=data["pack_title"],
            pack_summary=data.get("pack_summary"),
            pack_status=data.get("pack_status") or "draft",
            generated_for_audience=data.get("generated_for_audience") or "platform",
            covered_bundle_ids=data.get("covered_bundle_ids") or [],
            readiness_reference_ids=data.get("readiness_reference_ids") or [],
            approval_reference_ids=data.get("approval_reference_ids") or [],
            schedule_reference_ids=data.get("schedule_reference_ids") or [],
            timeline_reference_ids=data.get("timeline_reference_ids") or [],
            dependency_reference_ids=data.get("dependency_reference_ids") or [],
            risk_reference_ids=data.get("risk_reference_ids") or [],
            issue_reference_ids=data.get("issue_reference_ids") or [],
            decision_reference_ids=data.get("decision_reference_ids") or [],
            change_request_reference_ids=data.get("change_request_reference_ids") or [],
            rollback_plan_reference_ids=data.get("rollback_plan_reference_ids") or [],
            evidence_notes=data.get("evidence_notes"),
            compliance_notes=data.get("compliance_notes"),
            created_by=actor_from_user(user),
            updated_by=actor_from_user(user),
            metadata=data.get("metadata") or {},
        )
        stored = await self.db.collection(SUMMARY_PACK_COLLECTION).insert_one(pack.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "summary_pack": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Feature bundle rollout summary pack metadata was saved only. No rollout execution, deployment automation, feature activation or deactivation, entitlement enforcement, billing, provider integration, AI, external API, worker, scheduler, notification, email, webhook, publishing, runtime switch, PDF generation, file export, or automation was triggered.",
            **self.safety_flags(),
        }

    async def update_summary_pack(
        self,
        pack_id: str,
        payload: FeatureBundleRolloutSummaryPackUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_summary_pack(pack_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        if "pack_status" in updates:
            self._validate_dimension("status", updates["pack_status"], PACK_STATUSES)
        if "generated_for_audience" in updates:
            self._validate_dimension("audience", updates["generated_for_audience"], PACK_AUDIENCES)
        updates.update(
            {
                "updated_at": self._now(),
                "updated_by": actor_from_user(user),
                "metadata_only": True,
                "summary_pack_metadata_only": True,
            }
        )
        updated = await self.db.collection(SUMMARY_PACK_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "summary_pack": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Feature bundle rollout summary pack metadata was updated only. No rollout execution, deployment automation, activation, deactivation, enforcement, billing, provider integration, AI, external API, worker, scheduler, notification, email, webhook, publishing, runtime switching, PDF generation, file export, or automation ran.",
            **self.safety_flags(),
        }

    async def delete_summary_pack(self, pack_id: str, user: dict | None = None) -> dict[str, Any]:
        existing = await self._require_summary_pack(pack_id)
        updates = {
            "pack_status": "archived",
            "deleted_at": self._now(),
            "deleted_by": actor_from_user(user),
            "updated_by": actor_from_user(user),
            "metadata_only": True,
            "summary_pack_metadata_only": True,
            "summary_pack_deleted_metadata_only": True,
        }
        updated = await self.db.collection(SUMMARY_PACK_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "summary_pack": await self._platform_projection(stored),
            "deleted": True,
            "metadata_only": True,
            "notice": "Feature bundle rollout summary pack metadata was archived only. No rollout, deployment, feature activation or deactivation, entitlement enforcement, billing, provider call, AI, external API, worker, scheduler, notification, email, webhook, publishing, runtime switch, PDF generation, file export, or automation ran.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in PACK_STATUSES}
        by_audience = {audience: 0 for audience in PACK_AUDIENCES}
        rollout_ids: set[str] = set()
        covered_bundle_ids: set[str] = set()
        reference_sets: dict[str, set[str]] = {
            "readiness_reference_count": set(),
            "approval_reference_count": set(),
            "schedule_reference_count": set(),
            "timeline_reference_count": set(),
            "dependency_reference_count": set(),
            "risk_reference_count": set(),
            "issue_reference_count": set(),
            "decision_reference_count": set(),
            "change_request_reference_count": set(),
            "rollback_plan_reference_count": set(),
        }
        for item in items:
            status = item.get("pack_status") or "draft"
            audience = item.get("generated_for_audience") or "platform"
            by_status[status] = by_status.get(status, 0) + 1
            by_audience[audience] = by_audience.get(audience, 0) + 1
            if item.get("rollout_plan_id"):
                rollout_ids.add(item["rollout_plan_id"])
            covered_bundle_ids.update(item.get("covered_bundle_ids") or [])
            reference_sets["readiness_reference_count"].update(item.get("readiness_reference_ids") or [])
            reference_sets["approval_reference_count"].update(item.get("approval_reference_ids") or [])
            reference_sets["schedule_reference_count"].update(item.get("schedule_reference_ids") or [])
            reference_sets["timeline_reference_count"].update(item.get("timeline_reference_ids") or [])
            reference_sets["dependency_reference_count"].update(item.get("dependency_reference_ids") or [])
            reference_sets["risk_reference_count"].update(item.get("risk_reference_ids") or [])
            reference_sets["issue_reference_count"].update(item.get("issue_reference_ids") or [])
            reference_sets["decision_reference_count"].update(item.get("decision_reference_ids") or [])
            reference_sets["change_request_reference_count"].update(item.get("change_request_reference_ids") or [])
            reference_sets["rollback_plan_reference_count"].update(item.get("rollback_plan_reference_ids") or [])
        return {
            "total_count": len(items),
            "by_status": by_status,
            "by_audience": by_audience,
            "rollout_count": len(rollout_ids),
            "covered_bundle_count": len(covered_bundle_ids),
            **{key: len(value) for key, value in reference_sets.items()},
            "archived_count": by_status.get("archived", 0),
            "metadata_only": True,
            "pdf_generation_disabled": True,
            "file_export_disabled": True,
            "automation_disabled": True,
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "statuses": PACK_STATUSES,
            "audiences": PACK_AUDIENCES,
            "supports_rollout_filter": True,
            "supports_status_filter": True,
            "supports_audience_filter": True,
            "supports_bundle_filter": True,
            "metadata_only": True,
            "pdf_generation_disabled": True,
            "file_export_disabled": True,
        }

    async def _require_summary_pack(self, pack_id: str) -> dict[str, Any]:
        pack = await self.db.collection(SUMMARY_PACK_COLLECTION).find_one({"id": pack_id})
        if not pack:
            raise ValueError("Feature bundle rollout summary pack metadata was not found.")
        return pack

    async def _platform_projection(self, pack: dict[str, Any]) -> dict[str, Any]:
        projected = dict(pack)
        projected["plan"] = await self._plan_context(projected.get("rollout_plan_id"))
        projected["plan_name"] = projected["plan"].get("plan_name")
        projected["agency_id"] = projected["plan"].get("agency_id")
        projected["agency_name"] = projected["plan"].get("agency_name")
        projected["bundle_id"] = projected["plan"].get("bundle_id")
        projected["bundle_name"] = projected["plan"].get("bundle_name")
        projected["bundle_key"] = projected["plan"].get("bundle_key")
        projected["covered_bundles"] = [await self._bundle_context(bundle_id) for bundle_id in projected.get("covered_bundle_ids") or []]
        projected["readiness_references"] = [await self._readiness_context(reference_id) for reference_id in projected.get("readiness_reference_ids") or []]
        projected["approval_references"] = [await self._approval_context(reference_id) for reference_id in projected.get("approval_reference_ids") or []]
        projected["schedule_references"] = [await self._schedule_context(reference_id) for reference_id in projected.get("schedule_reference_ids") or []]
        projected["timeline_references"] = [await self._timeline_context(reference_id) for reference_id in projected.get("timeline_reference_ids") or []]
        projected["dependency_references"] = [await self._dependency_context(reference_id) for reference_id in projected.get("dependency_reference_ids") or []]
        projected["risk_references"] = [await self._risk_context(reference_id) for reference_id in projected.get("risk_reference_ids") or []]
        projected["issue_references"] = [await self._issue_context(reference_id) for reference_id in projected.get("issue_reference_ids") or []]
        projected["decision_references"] = [await self._decision_context(reference_id) for reference_id in projected.get("decision_reference_ids") or []]
        projected["change_request_references"] = [await self._change_request_context(reference_id) for reference_id in projected.get("change_request_reference_ids") or []]
        projected["rollback_plan_references"] = [await self._rollback_plan_context(reference_id) for reference_id in projected.get("rollback_plan_reference_ids") or []]
        projected["read_only"] = False
        projected["metadata_only"] = True
        projected["summary_pack_metadata_only"] = True
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any], agency_id: str) -> dict[str, Any]:
        projected = dict(item)
        projected["agency_id"] = agency_id
        projected["read_only"] = True
        projected.update(self.safety_flags())
        return projected

    async def _plan_context(self, rollout_plan_id: str | None) -> dict[str, Any]:
        if not rollout_plan_id:
            return {"rollout_plan_id": None, "plan_name": None, "agency_id": None, "metadata_only": True}
        plan = await self.db.collection(PLAN_COLLECTION).find_one({"rollout_plan_id": rollout_plan_id})
        if not plan:
            plan = await self.db.collection(PLAN_COLLECTION).find_one({"id": rollout_plan_id})
        if not plan:
            return {"rollout_plan_id": rollout_plan_id, "plan_name": rollout_plan_id, "agency_id": None, "metadata_only": True}
        agency = await self._agency_context(plan.get("agency_id"))
        bundle = await self._bundle_context(plan.get("bundle_id"))
        return {
            "rollout_plan_id": plan.get("rollout_plan_id"),
            "plan_name": plan.get("plan_name"),
            "rollout_stage": plan.get("rollout_stage"),
            "agency_id": plan.get("agency_id"),
            "agency_name": agency.get("agency_name"),
            "bundle_id": plan.get("bundle_id"),
            "bundle_name": bundle.get("bundle_name"),
            "bundle_key": bundle.get("bundle_key"),
            "metadata_only": True,
        }

    async def _agency_context(self, agency_id: str | None) -> dict[str, Any]:
        if not agency_id:
            return {"agency_id": None, "agency_name": None, "agency_slug": None}
        agency = await self.db.collection("agencies").find_one({"id": agency_id})
        if not agency:
            return {"agency_id": agency_id, "agency_name": agency_id, "agency_slug": None}
        return {
            "agency_id": agency.get("id"),
            "agency_name": agency.get("name"),
            "agency_slug": agency.get("slug"),
        }

    async def _bundle_context(self, bundle_id: str | None) -> dict[str, Any]:
        if not bundle_id:
            return {"bundle_id": None, "bundle_key": None, "bundle_name": None, "metadata_only": True}
        bundle = await AgencyFeatureFlagBundleService(self.db).get_bundle(bundle_id)
        if not bundle:
            return {"bundle_id": bundle_id, "bundle_key": bundle_id, "bundle_name": bundle_id, "metadata_only": True}
        return {
            "bundle_id": bundle.get("bundle_id"),
            "bundle_key": bundle.get("bundle_key"),
            "bundle_name": bundle.get("bundle_name"),
            "category": bundle.get("category"),
            "metadata_only": True,
        }

    async def _readiness_context(self, reference_id: str | None) -> dict[str, Any]:
        if not reference_id:
            return {"readiness_id": None, "status": None, "metadata_only": True}
        readiness = await self.db.collection(READINESS_COLLECTION).find_one({"id": reference_id})
        if not readiness:
            readiness = await self.db.collection(READINESS_COLLECTION).find_one({"assignment_id": reference_id})
        if not readiness:
            return {"readiness_id": reference_id, "status": None, "metadata_only": True}
        return {
            "readiness_id": readiness.get("id"),
            "assignment_id": readiness.get("assignment_id"),
            "agency_id": readiness.get("agency_id"),
            "bundle_id": readiness.get("bundle_id"),
            "status": readiness.get("readiness_status"),
            "checklist_count": len(readiness.get("checklist_items") or []),
            "metadata_only": True,
        }

    async def _approval_context(self, reference_id: str | None) -> dict[str, Any]:
        if not reference_id:
            return {"approval_id": None, "status": None, "metadata_only": True}
        approval = await self.db.collection(APPROVAL_COLLECTION).find_one({"approval_id": reference_id})
        if not approval:
            approval = await self.db.collection(APPROVAL_COLLECTION).find_one({"id": reference_id})
        if not approval:
            return {"approval_id": reference_id, "status": None, "metadata_only": True}
        return {
            "approval_id": approval.get("approval_id"),
            "status": approval.get("status"),
            "reviewer": approval.get("reviewer"),
            "reviewed_by": approval.get("reviewed_by"),
            "metadata_only": True,
        }

    async def _schedule_context(self, reference_id: str | None) -> dict[str, Any]:
        if not reference_id:
            return {"schedule_id": None, "status": None, "metadata_only": True}
        schedule = await self.db.collection(SCHEDULE_COLLECTION).find_one({"schedule_id": reference_id})
        if not schedule:
            schedule = await self.db.collection(SCHEDULE_COLLECTION).find_one({"id": reference_id})
        if not schedule:
            return {"schedule_id": reference_id, "status": None, "metadata_only": True}
        return {
            "schedule_id": schedule.get("schedule_id"),
            "rollout_name": schedule.get("rollout_name"),
            "status": schedule.get("schedule_status"),
            "planned_start": schedule.get("planned_start"),
            "planned_finish": schedule.get("planned_finish"),
            "metadata_only": True,
        }

    async def _timeline_context(self, reference_id: str | None) -> dict[str, Any]:
        if not reference_id:
            return {"timeline_entry_id": None, "event_type": None, "metadata_only": True}
        entry = await self.db.collection(TIMELINE_COLLECTION).find_one({"timeline_entry_id": reference_id})
        if not entry:
            entry = await self.db.collection(TIMELINE_COLLECTION).find_one({"entry_id": reference_id})
        if not entry:
            entry = await self.db.collection(TIMELINE_COLLECTION).find_one({"id": reference_id})
        if not entry:
            return {"timeline_entry_id": reference_id, "event_type": None, "metadata_only": True}
        return {
            "timeline_entry_id": entry.get("timeline_entry_id") or entry.get("entry_id") or entry.get("id"),
            "event_type": entry.get("event_type"),
            "event_label": entry.get("event_label"),
            "occurred_at": entry.get("occurred_at"),
            "description": entry.get("description"),
            "metadata_only": True,
        }

    async def _dependency_context(self, reference_id: str | None) -> dict[str, Any]:
        if not reference_id:
            return {"dependency_id": None, "label": None, "metadata_only": True}
        dependency = await self.db.collection(DEPENDENCY_COLLECTION).find_one({"dependency_id": reference_id})
        if not dependency:
            dependency = await self.db.collection(DEPENDENCY_COLLECTION).find_one({"id": reference_id})
        if not dependency:
            return {"dependency_id": reference_id, "label": reference_id, "metadata_only": True}
        depends_on = dependency.get("depends_on") or {}
        return {
            "dependency_id": dependency.get("dependency_id"),
            "dependency_type": dependency.get("dependency_type"),
            "label": depends_on.get("label") or depends_on.get("reference_id") or dependency.get("dependency_id"),
            "status": dependency.get("status"),
            "metadata_only": True,
        }

    async def _risk_context(self, reference_id: str | None) -> dict[str, Any]:
        if not reference_id:
            return {"risk_id": None, "title": None, "metadata_only": True}
        risk = await self.db.collection(RISK_COLLECTION).find_one({"risk_id": reference_id})
        if not risk:
            risk = await self.db.collection(RISK_COLLECTION).find_one({"id": reference_id})
        if not risk:
            return {"risk_id": reference_id, "title": reference_id, "metadata_only": True}
        return {
            "risk_id": risk.get("risk_id"),
            "title": risk.get("title"),
            "impact": risk.get("impact"),
            "likelihood": risk.get("likelihood"),
            "status": risk.get("status"),
            "metadata_only": True,
        }

    async def _issue_context(self, reference_id: str | None) -> dict[str, Any]:
        if not reference_id:
            return {"issue_id": None, "title": None, "metadata_only": True}
        issue = await self.db.collection(ISSUE_COLLECTION).find_one({"issue_id": reference_id})
        if not issue:
            issue = await self.db.collection(ISSUE_COLLECTION).find_one({"id": reference_id})
        if not issue:
            return {"issue_id": reference_id, "title": reference_id, "metadata_only": True}
        return {
            "issue_id": issue.get("issue_id"),
            "title": issue.get("title"),
            "severity": issue.get("severity"),
            "status": issue.get("status"),
            "metadata_only": True,
        }

    async def _decision_context(self, reference_id: str | None) -> dict[str, Any]:
        if not reference_id:
            return {"decision_id": None, "title": None, "metadata_only": True}
        decision = await self.db.collection(DECISION_COLLECTION).find_one({"id": reference_id})
        if not decision:
            return {"decision_id": reference_id, "title": reference_id, "metadata_only": True}
        return {
            "decision_id": decision.get("id"),
            "title": decision.get("decision_title"),
            "status": decision.get("decision_status"),
            "category": decision.get("decision_category"),
            "metadata_only": True,
        }

    async def _change_request_context(self, reference_id: str | None) -> dict[str, Any]:
        if not reference_id:
            return {"change_request_id": None, "title": None, "metadata_only": True}
        change_request = await self.db.collection(CHANGE_REQUEST_COLLECTION).find_one({"id": reference_id})
        if not change_request:
            return {"change_request_id": reference_id, "title": reference_id, "metadata_only": True}
        return {
            "change_request_id": change_request.get("id"),
            "title": change_request.get("change_title"),
            "status": change_request.get("change_status"),
            "type": change_request.get("change_type"),
            "priority": change_request.get("priority"),
            "metadata_only": True,
        }

    async def _rollback_plan_context(self, reference_id: str | None) -> dict[str, Any]:
        if not reference_id:
            return {"rollback_plan_id": None, "title": None, "metadata_only": True}
        rollback_plan = await self.db.collection(ROLLBACK_PLAN_COLLECTION).find_one({"id": reference_id})
        if not rollback_plan:
            return {"rollback_plan_id": reference_id, "title": reference_id, "metadata_only": True}
        return {
            "rollback_plan_id": rollback_plan.get("id"),
            "title": rollback_plan.get("rollback_title"),
            "status": rollback_plan.get("rollback_status"),
            "scope": rollback_plan.get("rollback_scope"),
            "priority": rollback_plan.get("rollback_priority"),
            "metadata_only": True,
        }

    def _validate_dimension(self, label: str, value: str, allowed: list[str]) -> None:
        if value not in allowed:
            raise ValueError(f"Unsupported feature bundle rollout summary pack {label}.")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "summary_pack_metadata_only": True,
            "rollout_execution_disabled": True,
            "deployment_automation_disabled": True,
            "feature_activation_disabled": True,
            "feature_deactivation_disabled": True,
            "feature_bundle_activation_disabled": True,
            "feature_bundle_deactivation_disabled": True,
            "entitlement_enforcement_disabled": True,
            "billing_disabled": True,
            "provider_integrations_disabled": True,
            "provider_calls_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "ai_execution_disabled": True,
            "external_ai_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "notification_sending_disabled": True,
            "notifications_disabled": True,
            "email_sending_disabled": True,
            "webhook_execution_disabled": True,
            "publishing_disabled": True,
            "runtime_switching_disabled": True,
            "pdf_generation_disabled": True,
            "file_export_disabled": True,
            "automation_disabled": True,
        }
