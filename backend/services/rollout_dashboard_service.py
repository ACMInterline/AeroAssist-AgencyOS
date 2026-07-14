from __future__ import annotations

from typing import Any

from database import Database
from models import (
    RolloutDashboardCounts,
    RolloutDashboardFilters,
    RolloutDashboardSection,
    RolloutDashboardSummary,
)
from services.agency_feature_bundle_assignment_service import AgencyFeatureBundleAssignmentService
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService
from services.agency_feature_flag_service import FEATURE_FLAG_STATES, AgencyFeatureFlagService
from services.capability_catalog_service import CapabilityCatalogService
from services.feature_bundle_rollout_plan_service import PLAN_STAGES, FeatureBundleRolloutPlanService
from services.feature_bundle_rollout_readiness_service import READINESS_STATUSES, FeatureBundleRolloutReadinessService


PHASE_LABEL = "phase_54_6_offer_to_booking_handoff_readiness_foundation"

VIEW_COLLECTION = "rollout_dashboard_views"
SNAPSHOT_COLLECTION = "rollout_dashboard_snapshots"

DASHBOARD_SECTIONS = [
    {
        "section_key": "capability_catalog",
        "title": "Capability Catalog",
        "description": "Canonical capability metadata and informational availability.",
        "platform_route": "/platform/capabilities",
        "agency_route": "/agency/capabilities",
    },
    {
        "section_key": "feature_flags",
        "title": "Feature Flags",
        "description": "Agency feature visibility metadata.",
        "platform_route": "/platform/feature-flags",
        "agency_route": "/agency/feature-availability",
    },
    {
        "section_key": "feature_bundles",
        "title": "Feature Bundles",
        "description": "Reusable feature bundle metadata.",
        "platform_route": "/platform/feature-flag-bundles",
        "agency_route": "/agency/feature-bundles",
    },
    {
        "section_key": "assigned_bundles",
        "title": "Assigned Bundles",
        "description": "Agency bundle assignment metadata.",
        "platform_route": "/platform/feature-bundle-assignments",
        "agency_route": "/agency/assigned-bundles",
    },
    {
        "section_key": "rollout_readiness",
        "title": "Rollout Readiness",
        "description": "Assigned bundle readiness checklist metadata.",
        "platform_route": "/platform/feature-bundle-rollout-readiness",
        "agency_route": "/agency/bundle-rollout-readiness",
    },
    {
        "section_key": "rollout_plans",
        "title": "Rollout Plans",
        "description": "Feature bundle rollout plan metadata.",
        "platform_route": "/platform/feature-bundle-rollout-plans",
        "agency_route": "/agency/rollout-plans",
    },
]


class RolloutDashboardService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_dashboard(self, filters: RolloutDashboardFilters | dict[str, Any] | None = None) -> dict[str, Any]:
        normalized_filters = self._filters(filters)
        sections = await self._sections(filters=normalized_filters, agency_id=normalized_filters.agency_id, agency_view=False)
        summary = self._summary(sections, normalized_filters)
        return {
            "phase": PHASE_LABEL,
            "summary": summary.model_dump(mode="json"),
            "sections": [section.model_dump(mode="json") for section in sections],
            "counts": summary.counts.model_dump(mode="json"),
            "read_only": True,
            "metadata_only": True,
            "notice": "Rollout Dashboard is read-only metadata. It does not activate features, enforce access, bill, publish, send, call providers, call external APIs, use AI, schedule, or execute rollouts.",
            **self.safety_flags(),
        }

    async def agency_dashboard(self, agency_id: str, filters: RolloutDashboardFilters | dict[str, Any] | None = None) -> dict[str, Any]:
        normalized_filters = self._filters(filters)
        normalized_filters.agency_id = agency_id
        sections = await self._sections(filters=normalized_filters, agency_id=agency_id, agency_view=True)
        summary = self._summary(sections, normalized_filters, agency_id=agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": summary.model_dump(mode="json"),
            "sections": [section.model_dump(mode="json") for section in sections],
            "counts": summary.counts.model_dump(mode="json"),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Rollout Dashboard is read-only metadata scoped to this agency. It does not activate, block, bill, publish, send, schedule, or execute anything.",
            **self.safety_flags(),
        }

    async def platform_summary(self, filters: RolloutDashboardFilters | dict[str, Any] | None = None) -> dict[str, Any]:
        dashboard = await self.platform_dashboard(filters)
        return {
            "phase": PHASE_LABEL,
            "summary": dashboard["summary"],
            "counts": dashboard["counts"],
            "section_count": len(dashboard["sections"]),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str, filters: RolloutDashboardFilters | dict[str, Any] | None = None) -> dict[str, Any]:
        dashboard = await self.agency_dashboard(agency_id, filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": dashboard["summary"],
            "counts": dashboard["counts"],
            "section_count": len(dashboard["sections"]),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def platform_snapshots(self, *, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        snapshots = await self.db.collection(SNAPSHOT_COLLECTION).find_many(filters)
        snapshots.sort(key=lambda item: self._sort_timestamp(item.get("captured_at") or item.get("created_at")), reverse=True)
        return {
            "phase": PHASE_LABEL,
            "items": [self._snapshot_projection(item, agency_view=False) for item in snapshots],
            "snapshot_count": len(snapshots),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_snapshots(self, agency_id: str) -> dict[str, Any]:
        snapshots = await self.db.collection(SNAPSHOT_COLLECTION).find_many({"agency_id": agency_id})
        snapshots.sort(key=lambda item: self._sort_timestamp(item.get("captured_at") or item.get("created_at")), reverse=True)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": [self._snapshot_projection(item, agency_view=True) for item in snapshots],
            "snapshot_count": len(snapshots),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def platform_filters(self) -> dict[str, Any]:
        agencies = await self.db.collection("agencies").find_many()
        bundles = await AgencyFeatureFlagBundleService(self.db).list_bundles()
        capabilities = await CapabilityCatalogService(self.db).list_capabilities()
        categories = sorted({item.get("category") for item in capabilities if item.get("category")})
        modules = sorted({item.get("module") for item in capabilities if item.get("module")})
        return {
            "phase": PHASE_LABEL,
            "filters": {
                "agencies": [
                    {"agency_id": agency.get("id"), "agency_name": agency.get("name"), "agency_slug": agency.get("slug")}
                    for agency in agencies
                ],
                "bundle_ids": [item.get("bundle_id") for item in bundles if item.get("bundle_id")],
                "bundle_keys": [item.get("bundle_key") for item in bundles if item.get("bundle_key")],
                "feature_states": FEATURE_FLAG_STATES,
                "readiness_statuses": READINESS_STATUSES,
                "rollout_stages": PLAN_STAGES,
                "capability_categories": categories,
                "capability_modules": modules,
                "sections": [item["section_key"] for item in DASHBOARD_SECTIONS],
            },
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def _sections(
        self,
        *,
        filters: RolloutDashboardFilters,
        agency_id: str | None,
        agency_view: bool,
    ) -> list[RolloutDashboardSection]:
        sections = [
            await self._capability_section(filters, agency_id=agency_id, agency_view=agency_view),
            await self._feature_flag_section(filters, agency_id=agency_id),
            await self._feature_bundle_section(agency_view=agency_view),
            await self._assigned_bundle_section(agency_id=agency_id, agency_view=agency_view),
            await self._readiness_section(filters, agency_id=agency_id, agency_view=agency_view),
            await self._plan_section(filters, agency_id=agency_id, agency_view=agency_view),
        ]
        return sections

    async def _capability_section(
        self,
        filters: RolloutDashboardFilters,
        *,
        agency_id: str | None,
        agency_view: bool,
    ) -> RolloutDashboardSection:
        service = CapabilityCatalogService(self.db)
        if agency_view and agency_id:
            response = await service.agency_capabilities_response(agency_id)
            items = response.get("items") or []
            statuses = response.get("availability_counts") or self._count_by(items, "informational_availability")
        else:
            items = await service.list_capabilities(category=filters.capability_category)
            statuses = self._count_by(items, "status")
        return self._section("capability_catalog", items, statuses, agency_view=agency_view)

    async def _feature_flag_section(self, filters: RolloutDashboardFilters, *, agency_id: str | None) -> RolloutDashboardSection:
        flags = await AgencyFeatureFlagService(self.db).list_flags(
            agency_id=agency_id,
            state=filters.feature_state,
            agency_view=agency_id is not None,
        )
        return self._section("feature_flags", flags, self._count_by(flags, "state"), agency_view=agency_id is not None)

    async def _feature_bundle_section(self, *, agency_view: bool) -> RolloutDashboardSection:
        bundles = await AgencyFeatureFlagBundleService(self.db).list_bundles(agency_view=agency_view)
        return self._section("feature_bundles", bundles, self._count_by(bundles, "review_status"), agency_view=agency_view)

    async def _assigned_bundle_section(self, *, agency_id: str | None, agency_view: bool) -> RolloutDashboardSection:
        assignments = await AgencyFeatureBundleAssignmentService(self.db).list_assignments(
            agency_id=agency_id,
            agency_view=agency_view,
        )
        return self._section("assigned_bundles", assignments, self._count_by(assignments, "status"), agency_view=agency_view)

    async def _readiness_section(
        self,
        filters: RolloutDashboardFilters,
        *,
        agency_id: str | None,
        agency_view: bool,
    ) -> RolloutDashboardSection:
        service = FeatureBundleRolloutReadinessService(self.db)
        if agency_view and agency_id:
            items = await service.list_agency_readiness(agency_id, readiness_status=filters.readiness_status)
        else:
            items = await service.list_platform_readiness(agency_id=agency_id, readiness_status=filters.readiness_status)
        counts = service.summarize_counts(items)
        return self._section(
            "rollout_readiness",
            items,
            counts.get("by_readiness_status") or self._count_by(items, "readiness_status"),
            agency_view=agency_view,
            warning_count=counts.get("warning_count", 0),
            blocker_count=counts.get("blocker_count", 0),
        )

    async def _plan_section(
        self,
        filters: RolloutDashboardFilters,
        *,
        agency_id: str | None,
        agency_view: bool,
    ) -> RolloutDashboardSection:
        service = FeatureBundleRolloutPlanService(self.db)
        if agency_view and agency_id:
            items = await service.list_agency_plans(agency_id, rollout_stage=filters.rollout_stage)
        else:
            items = await service.list_platform_plans(agency_id=agency_id, rollout_stage=filters.rollout_stage)
        counts = service.summarize_counts(items)
        return self._section(
            "rollout_plans",
            items,
            counts.get("by_rollout_stage") or self._count_by(items, "rollout_stage"),
            agency_view=agency_view,
            warning_count=counts.get("warning_count", 0),
            blocker_count=counts.get("blocker_count", 0),
            by_stage=counts.get("by_rollout_stage") or {},
        )

    def _section(
        self,
        section_key: str,
        items: list[dict[str, Any]],
        statuses: dict[str, int],
        *,
        agency_view: bool,
        warning_count: int = 0,
        blocker_count: int = 0,
        by_stage: dict[str, int] | None = None,
    ) -> RolloutDashboardSection:
        definition = next(item for item in DASHBOARD_SECTIONS if item["section_key"] == section_key)
        counts = RolloutDashboardCounts(
            total_count=len(items),
            by_status=statuses,
            by_stage=by_stage or {},
            warning_count=warning_count,
            blocker_count=blocker_count,
            metadata_only=True,
        )
        return RolloutDashboardSection(
            section_key=section_key,
            title=definition["title"],
            description=definition["description"],
            count=len(items),
            counts=counts,
            statuses=statuses,
            route=definition["agency_route"] if agency_view else definition["platform_route"],
            last_updated=self._last_updated(items),
            read_only=True,
            metadata_only=True,
        )

    def _summary(
        self,
        sections: list[RolloutDashboardSection],
        filters: RolloutDashboardFilters,
        *,
        agency_id: str | None = None,
    ) -> RolloutDashboardSummary:
        total_count = sum(section.count for section in sections)
        warning_count = sum(section.counts.warning_count for section in sections)
        blocker_count = sum(section.counts.blocker_count for section in sections)
        counts = RolloutDashboardCounts(
            total_count=total_count,
            by_status={section.section_key: section.count for section in sections},
            warning_count=warning_count,
            blocker_count=blocker_count,
            metadata_only=True,
        )
        return RolloutDashboardSummary(
            agency_id=agency_id,
            sections=sections,
            counts=counts,
            filters=filters,
            read_only=True,
            metadata_only=True,
        )

    def _filters(self, filters: RolloutDashboardFilters | dict[str, Any] | None) -> RolloutDashboardFilters:
        if isinstance(filters, RolloutDashboardFilters):
            return filters
        return RolloutDashboardFilters(**{key: value for key, value in (filters or {}).items() if value is not None})

    def _snapshot_projection(self, snapshot: dict[str, Any], *, agency_view: bool) -> dict[str, Any]:
        projected = dict(snapshot)
        projected["read_only"] = True
        projected["metadata_only"] = True
        projected["payloads_hidden"] = agency_view
        projected.update(self.safety_flags())
        return projected

    def _count_by(self, items: list[dict[str, Any]], key: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            value = item.get(key) or "unknown"
            counts[value] = counts.get(value, 0) + 1
        return counts

    def _last_updated(self, items: list[dict[str, Any]]) -> Any:
        values = [item.get("updated_at") or item.get("created_at") or item.get("reviewed_at") for item in items]
        values = [value for value in values if value]
        if not values:
            return None
        return max(values, key=self._sort_timestamp)

    def _sort_timestamp(self, value: Any) -> str:
        if value is None:
            return ""
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "read_only": True,
            "automation_disabled": True,
            "rollout_automation_disabled": True,
            "rollout_execution_disabled": True,
            "execution_engines_disabled": True,
            "feature_activation_disabled": True,
            "permission_enforcement_disabled": True,
            "feature_access_enforcement_disabled": True,
            "route_blocking_disabled": True,
            "billing_disabled": True,
            "payments_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "ai_execution_disabled": True,
            "scraping_disabled": True,
            "publishing_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "cron_disabled": True,
            "webhook_execution_disabled": True,
            "email_sending_disabled": True,
            "sms_sending_disabled": True,
        }
