from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    FeatureBundleRolloutRisk,
    FeatureBundleRolloutRiskCreate,
    FeatureBundleRolloutRiskUpdate,
    new_id,
)
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService
from services.feature_bundle_dependency_service import DEPENDENCY_COLLECTION
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_40_13_feature_bundle_rollout_summary_pack_foundation"

RISK_COLLECTION = "feature_bundle_rollout_risks"
PLAN_COLLECTION = "agency_feature_bundle_rollout_plans"
RISK_IMPACTS = ["low", "medium", "high", "critical"]
RISK_LIKELIHOODS = ["rare", "unlikely", "possible", "likely", "almost_certain"]
RISK_STATUSES = ["open", "reviewing", "mitigating", "mitigated", "accepted", "closed", "deleted"]


class FeatureBundleRolloutRiskService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_risks(
        self,
        *,
        agency_id: str | None = None,
        bundle_id: str | None = None,
        rollout_plan_id: str | None = None,
        status: str | None = None,
        impact: str | None = None,
        likelihood: str | None = None,
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if bundle_id:
            filters["bundle_id"] = bundle_id
        if rollout_plan_id:
            filters["rollout_plan_id"] = rollout_plan_id
        if status:
            filters["status"] = status
        if impact:
            filters["impact"] = impact
        if likelihood:
            filters["likelihood"] = likelihood
        risks = await self.db.collection(RISK_COLLECTION).find_many(filters or None)
        if not include_deleted:
            risks = [item for item in risks if item.get("status") != "deleted" and not item.get("deleted_at")]
        risks.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return [await self._platform_projection(item) for item in risks]

    async def list_agency_risks(
        self,
        agency_id: str,
        *,
        bundle_id: str | None = None,
        rollout_plan_id: str | None = None,
        status: str | None = None,
        impact: str | None = None,
        likelihood: str | None = None,
    ) -> list[dict[str, Any]]:
        risks = await self.list_platform_risks(
            agency_id=agency_id,
            bundle_id=bundle_id,
            rollout_plan_id=rollout_plan_id,
            status=status,
            impact=impact,
            likelihood=likelihood,
        )
        return [self._agency_projection(item, agency_id) for item in risks]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        bundle_id: str | None = None,
        rollout_plan_id: str | None = None,
        status: str | None = None,
        impact: str | None = None,
        likelihood: str | None = None,
        include_deleted: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_risks(
            agency_id=agency_id,
            bundle_id=bundle_id,
            rollout_plan_id=rollout_plan_id,
            status=status,
            impact=impact,
            likelihood=likelihood,
            include_deleted=include_deleted,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "risk_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Feature bundle rollout risks are metadata only. They do not execute rollouts, enforce risk decisions, block anything, send notifications, activate bundles, add automation, or call external providers.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        bundle_id: str | None = None,
        rollout_plan_id: str | None = None,
        status: str | None = None,
        impact: str | None = None,
        likelihood: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_risks(
            agency_id,
            bundle_id=bundle_id,
            rollout_plan_id=rollout_plan_id,
            status=status,
            impact=impact,
            likelihood=likelihood,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "risk_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Feature bundle rollout risk metadata is read-only for this agency. It does not enforce risk decisions, block rollouts, activate bundles, send notifications, automate actions, or call providers.",
            **self.safety_flags(),
        }

    async def platform_summary(self, *, agency_id: str | None = None) -> dict[str, Any]:
        items = await self.list_platform_risks(agency_id=agency_id, include_deleted=True)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "risk_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_risks(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "risk_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_risk(self, risk_id: str) -> dict[str, Any]:
        risk = await self._require_risk(risk_id)
        return await self._platform_projection(risk)

    async def get_agency_risk(self, agency_id: str, risk_id: str) -> dict[str, Any]:
        risk = await self._require_risk(risk_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(risk), agency_id)

    async def create_risk(
        self,
        payload: FeatureBundleRolloutRiskCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        self._validate_dimension("impact", data.get("impact") or "medium", RISK_IMPACTS)
        self._validate_dimension("likelihood", data.get("likelihood") or "possible", RISK_LIKELIHOODS)
        self._validate_dimension("status", data.get("status") or "open", RISK_STATUSES)
        risk = FeatureBundleRolloutRisk(
            risk_id=data.get("risk_id") or new_id(),
            agency_id=data.get("agency_id"),
            bundle_id=data.get("bundle_id"),
            rollout_plan_id=data.get("rollout_plan_id"),
            dependency_id=data.get("dependency_id"),
            title=data["title"],
            description=data.get("description"),
            impact=data.get("impact") or "medium",
            likelihood=data.get("likelihood") or "possible",
            status=data.get("status") or "open",
            mitigation_notes=data.get("mitigation_notes"),
            owner=data.get("owner"),
            review_notes=data.get("review_notes"),
            created_by=actor_from_user(user),
            updated_by=actor_from_user(user),
            metadata=data.get("metadata") or {},
        )
        stored = await self.db.collection(RISK_COLLECTION).insert_one(risk.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "risk": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Feature bundle rollout risk metadata was saved only. No rollout execution, risk decision enforcement, blocking, notification, bundle activation, automation, or provider call was triggered.",
            **self.safety_flags(),
        }

    async def update_risk(
        self,
        risk_id: str,
        payload: FeatureBundleRolloutRiskUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_risk(risk_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        if "impact" in updates:
            self._validate_dimension("impact", updates["impact"], RISK_IMPACTS)
        if "likelihood" in updates:
            self._validate_dimension("likelihood", updates["likelihood"], RISK_LIKELIHOODS)
        if "status" in updates:
            self._validate_dimension("status", updates["status"], RISK_STATUSES)
        updates.update(
            {
                "updated_at": self._now(),
                "updated_by": actor_from_user(user),
                "metadata_only": True,
                "risk_register_metadata_only": True,
            }
        )
        updated = await self.db.collection(RISK_COLLECTION).update_one({"risk_id": existing["risk_id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "risk": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Feature bundle rollout risk metadata was updated only. No risk enforcement, rollout blocking, rollout execution, notification, bundle activation, provider call, or automation was triggered.",
            **self.safety_flags(),
        }

    async def delete_risk(self, risk_id: str, user: dict | None = None) -> dict[str, Any]:
        existing = await self._require_risk(risk_id)
        updates = {
            "status": "deleted",
            "deleted_at": self._now(),
            "deleted_by": actor_from_user(user),
            "updated_by": actor_from_user(user),
            "metadata_only": True,
            "risk_register_metadata_only": True,
            "risk_deleted_metadata_only": True,
        }
        updated = await self.db.collection(RISK_COLLECTION).update_one({"risk_id": existing["risk_id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "risk": await self._platform_projection(stored),
            "deleted": True,
            "metadata_only": True,
            "notice": "Feature bundle rollout risk metadata was marked deleted only. No rollout was blocked and no rollout, notification, automation, or provider action was executed.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in RISK_STATUSES}
        by_impact = {impact: 0 for impact in RISK_IMPACTS}
        by_likelihood = {likelihood: 0 for likelihood in RISK_LIKELIHOODS}
        agency_ids: set[str] = set()
        bundle_ids: set[str] = set()
        plan_ids: set[str] = set()
        dependency_ids: set[str] = set()
        for item in items:
            status = item.get("status") or "open"
            impact = item.get("impact") or "medium"
            likelihood = item.get("likelihood") or "possible"
            by_status[status] = by_status.get(status, 0) + 1
            by_impact[impact] = by_impact.get(impact, 0) + 1
            by_likelihood[likelihood] = by_likelihood.get(likelihood, 0) + 1
            if item.get("agency_id"):
                agency_ids.add(item["agency_id"])
            if item.get("bundle_id"):
                bundle_ids.add(item["bundle_id"])
            if item.get("rollout_plan_id"):
                plan_ids.add(item["rollout_plan_id"])
            if item.get("dependency_id"):
                dependency_ids.add(item["dependency_id"])
        return {
            "total_count": len(items),
            "by_status": by_status,
            "by_impact": by_impact,
            "by_likelihood": by_likelihood,
            "agency_count": len(agency_ids),
            "bundle_count": len(bundle_ids),
            "plan_count": len(plan_ids),
            "dependency_count": len(dependency_ids),
            "deleted_count": by_status.get("deleted", 0),
            "metadata_only": True,
            "execution_disabled": True,
            "enforcement_disabled": True,
            "blocking_disabled": True,
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "statuses": RISK_STATUSES,
            "impacts": RISK_IMPACTS,
            "likelihoods": RISK_LIKELIHOODS,
            "supports_agency_filter": True,
            "supports_bundle_filter": True,
            "supports_rollout_plan_filter": True,
            "supports_status_filter": True,
            "supports_impact_filter": True,
            "supports_likelihood_filter": True,
            "metadata_only": True,
        }

    async def _require_risk(self, risk_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"risk_id": risk_id}
        if agency_id:
            filters["agency_id"] = agency_id
        risk = await self.db.collection(RISK_COLLECTION).find_one(filters)
        if not risk:
            filters = {"id": risk_id}
            if agency_id:
                filters["agency_id"] = agency_id
            risk = await self.db.collection(RISK_COLLECTION).find_one(filters)
        if not risk:
            raise ValueError("Feature bundle rollout risk metadata was not found.")
        return risk

    async def _platform_projection(self, risk: dict[str, Any]) -> dict[str, Any]:
        projected = dict(risk)
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["bundle"] = await self._bundle_context(projected.get("bundle_id"))
        projected["bundle_key"] = projected["bundle"].get("bundle_key")
        projected["bundle_name"] = projected["bundle"].get("bundle_name")
        projected["plan"] = await self._plan_context(projected.get("rollout_plan_id"))
        projected["plan_name"] = projected["plan"].get("plan_name")
        projected["dependency"] = await self._dependency_context(projected.get("dependency_id"))
        projected["dependency_label"] = projected["dependency"].get("dependency_label")
        projected["read_only"] = False
        projected["metadata_only"] = True
        projected["risk_register_metadata_only"] = True
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any], agency_id: str) -> dict[str, Any]:
        projected = dict(item)
        projected["agency_id"] = agency_id
        projected["read_only"] = True
        projected.update(self.safety_flags())
        return projected

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
            return {"bundle_id": None, "bundle_key": None, "bundle_name": None, "category": None}
        bundle = await AgencyFeatureFlagBundleService(self.db).get_bundle(bundle_id)
        if not bundle:
            return {"bundle_id": bundle_id, "bundle_key": bundle_id, "bundle_name": bundle_id, "category": None}
        return {
            "bundle_id": bundle.get("bundle_id"),
            "bundle_key": bundle.get("bundle_key"),
            "bundle_name": bundle.get("bundle_name"),
            "category": bundle.get("category"),
        }

    async def _plan_context(self, rollout_plan_id: str | None) -> dict[str, Any]:
        if not rollout_plan_id:
            return {"rollout_plan_id": None, "plan_name": None, "metadata_only": True}
        plan = await self.db.collection(PLAN_COLLECTION).find_one({"rollout_plan_id": rollout_plan_id})
        if not plan:
            plan = await self.db.collection(PLAN_COLLECTION).find_one({"id": rollout_plan_id})
        if not plan:
            return {"rollout_plan_id": rollout_plan_id, "plan_name": rollout_plan_id, "metadata_only": True}
        return {
            "rollout_plan_id": plan.get("rollout_plan_id"),
            "plan_name": plan.get("plan_name"),
            "agency_id": plan.get("agency_id"),
            "bundle_id": plan.get("bundle_id"),
            "rollout_stage": plan.get("rollout_stage"),
            "metadata_only": True,
        }

    async def _dependency_context(self, dependency_id: str | None) -> dict[str, Any]:
        if not dependency_id:
            return {"dependency_id": None, "dependency_label": None, "metadata_only": True}
        dependency = await self.db.collection(DEPENDENCY_COLLECTION).find_one({"dependency_id": dependency_id})
        if not dependency:
            dependency = await self.db.collection(DEPENDENCY_COLLECTION).find_one({"id": dependency_id})
        if not dependency:
            return {"dependency_id": dependency_id, "dependency_label": dependency_id, "metadata_only": True}
        depends_on = dependency.get("depends_on") or {}
        return {
            "dependency_id": dependency.get("dependency_id"),
            "dependency_type": dependency.get("dependency_type"),
            "dependency_label": depends_on.get("label") or depends_on.get("reference_id") or dependency.get("dependency_id"),
            "status": dependency.get("status"),
            "metadata_only": True,
        }

    def _validate_dimension(self, label: str, value: str, allowed: list[str]) -> None:
        if value not in allowed:
            raise ValueError(f"Unsupported feature bundle rollout risk {label}.")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "risk_register_metadata_only": True,
            "rollout_execution_disabled": True,
            "risk_decision_enforcement_disabled": True,
            "risk_enforcement_disabled": True,
            "risk_blocking_disabled": True,
            "rollout_blocking_disabled": True,
            "feature_bundle_activation_disabled": True,
            "feature_bundles_enablement_disabled": True,
            "notification_sending_disabled": True,
            "notifications_disabled": True,
            "external_provider_calls_disabled": True,
            "provider_calls_disabled": True,
            "provider_execution_disabled": True,
            "automation_disabled": True,
            "background_jobs_disabled": True,
        }
