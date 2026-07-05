from __future__ import annotations

from typing import Any

from database import Database
from models import BundleReadiness, FeatureFlagBundle, FeatureFlagBundleMember, FeatureFlagBundleReview, FeatureFlagBundleSummary


PHASE_LABEL = "phase_40_9_feature_bundle_rollout_issue_log_foundation"

BUNDLE_COLLECTION = "agency_feature_flag_bundles"
BUNDLE_REVIEW_COLLECTION = "agency_feature_flag_bundle_reviews"

DEFAULT_FEATURE_FLAG_BUNDLES: list[dict[str, Any]] = [
    {
        "bundle_key": "core_agency",
        "bundle_name": "Core Agency",
        "description": "Baseline workspace visibility for dashboards, requests, trips, and settings.",
        "category": "core",
        "review_status": "reviewed",
        "members": [
            {"module_key": "daily_work", "feature_key": "dashboard", "display_name": "Dashboard"},
            {"module_key": "daily_work", "feature_key": "requests", "display_name": "Requests"},
            {"module_key": "requests_trips", "feature_key": "trips", "display_name": "Trips"},
            {"module_key": "settings", "feature_key": "settings", "display_name": "Settings"},
        ],
    },
    {
        "bundle_key": "crm",
        "bundle_name": "CRM",
        "description": "Client, passenger, and relationship visibility metadata.",
        "category": "crm",
        "review_status": "draft",
        "members": [
            {"module_key": "crm", "feature_key": "clients", "display_name": "Clients"},
            {"module_key": "crm", "feature_key": "passengers", "display_name": "Passengers"},
            {"module_key": "crm", "feature_key": "client_portal", "display_name": "Client Portal"},
        ],
    },
    {
        "bundle_key": "ticketing",
        "bundle_name": "Ticketing",
        "description": "Ticket and EMD mirror visibility metadata without issuance.",
        "category": "operations",
        "review_status": "draft",
        "members": [
            {"module_key": "tickets_emds", "feature_key": "ticket_records", "display_name": "Ticket Records"},
            {"module_key": "tickets_emds", "feature_key": "emd_records", "display_name": "EMD Records"},
        ],
    },
    {
        "bundle_key": "booking",
        "bundle_name": "Booking",
        "description": "Internal booking workspace and import review visibility metadata.",
        "category": "operations",
        "review_status": "draft",
        "members": [
            {"module_key": "booking", "feature_key": "booking_workspaces", "display_name": "Booking Workspaces"},
            {"module_key": "booking", "feature_key": "booking_imports", "display_name": "Booking Imports"},
        ],
    },
    {
        "bundle_key": "airline_intelligence",
        "bundle_name": "Airline Intelligence",
        "description": "Platform-reviewed airline knowledge visibility metadata.",
        "category": "intelligence",
        "review_status": "review",
        "members": [
            {"module_key": "airline_intelligence", "feature_key": "policy_library", "display_name": "Policy Library"},
            {"module_key": "airline_intelligence", "feature_key": "airline_coverage", "display_name": "Airline Coverage"},
            {"module_key": "airline_intelligence", "feature_key": "knowledge_versions", "display_name": "Knowledge Versions"},
        ],
    },
    {
        "bundle_key": "gds",
        "bundle_name": "GDS",
        "description": "Parser and review metadata for GDS text, with no provider execution.",
        "category": "supplier",
        "review_status": "draft",
        "members": [
            {"module_key": "gds", "feature_key": "gds_parser", "display_name": "GDS Parser"},
            {"module_key": "gds", "feature_key": "gds_samples", "display_name": "GDS Samples"},
        ],
    },
    {
        "bundle_key": "finance",
        "bundle_name": "Finance",
        "description": "Invoice, payment, and refund visibility metadata only.",
        "category": "finance",
        "review_status": "draft",
        "members": [
            {"module_key": "finance", "feature_key": "invoices", "display_name": "Invoices"},
            {"module_key": "finance", "feature_key": "payments", "display_name": "Payments"},
            {"module_key": "finance", "feature_key": "refunds_exchanges", "display_name": "Refunds & Exchanges"},
        ],
    },
    {
        "bundle_key": "premium_operations",
        "bundle_name": "Premium Operations",
        "description": "Offer evidence, advisor, and manual delivery metadata for higher-touch teams.",
        "category": "premium",
        "review_status": "review",
        "members": [
            {"module_key": "offers", "feature_key": "offer_policy_advisor", "display_name": "Offer Advisor"},
            {"module_key": "offers", "feature_key": "offer_decision_evidence", "display_name": "Decision Evidence"},
            {"module_key": "documents", "feature_key": "manual_delivery", "display_name": "Manual Delivery"},
        ],
    },
    {
        "bundle_key": "beta_features",
        "bundle_name": "Beta Features",
        "description": "Beta feature visibility metadata for platform review.",
        "category": "beta",
        "review_status": "draft",
        "members": [
            {"module_key": "settings", "feature_key": "feature_availability", "display_name": "Feature Availability"},
            {"module_key": "settings", "feature_key": "feature_readiness", "display_name": "Feature Readiness"},
        ],
    },
    {
        "bundle_key": "internal_testing",
        "bundle_name": "Internal Testing",
        "description": "Internal smoke and audit visibility metadata for platform operators.",
        "category": "internal",
        "review_status": "draft",
        "visible_to_agencies": False,
        "members": [
            {"module_key": "platform", "feature_key": "internal_test_flags", "display_name": "Internal Test Flags"},
            {"module_key": "platform", "feature_key": "audit_history", "display_name": "Audit History"},
        ],
    },
]


class AgencyFeatureFlagBundleService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_bundles(self, *, agency_view: bool = False) -> list[dict[str, Any]]:
        stored = await self.db.collection(BUNDLE_COLLECTION).find_many()
        bundles_by_key = {item.get("bundle_key"): self._normalize_bundle(item) for item in stored if item.get("bundle_key")}
        for default_bundle in DEFAULT_FEATURE_FLAG_BUNDLES:
            bundles_by_key.setdefault(default_bundle["bundle_key"], self._normalize_bundle(default_bundle, default_bundle=True))
        bundles = list(bundles_by_key.values())
        if agency_view:
            bundles = [item for item in bundles if item.get("visible_to_agencies", True)]
        bundles.sort(key=lambda item: (item.get("category") or "", item.get("bundle_name") or ""))
        return [self._bundle_summary(item, agency_view=agency_view) for item in bundles]

    async def get_bundle(self, bundle_id: str, *, agency_view: bool = False) -> dict[str, Any] | None:
        bundles = await self._all_bundles(agency_view=agency_view)
        bundle = next(
            (
                item
                for item in bundles
                if bundle_id in {item.get("id"), item.get("bundle_id"), item.get("bundle_key")}
            ),
            None,
        )
        return self._bundle_projection(bundle, agency_view=agency_view) if bundle else None

    async def list_members(self, bundle_id: str) -> list[dict[str, Any]]:
        bundle = await self.get_bundle(bundle_id)
        if not bundle:
            return []
        return [self._member_projection(item) for item in bundle.get("members", [])]

    async def list_reviews(self, *, bundle_id: str | None = None, bundle_key: str | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if bundle_id:
            filters["bundle_id"] = bundle_id
        if bundle_key:
            filters["bundle_key"] = bundle_key
        reviews = await self.db.collection(BUNDLE_REVIEW_COLLECTION).find_many(filters or None)
        reviews.sort(key=lambda item: self._sort_timestamp(item.get("created_at")), reverse=True)
        return [self._review_projection(item) for item in reviews]

    async def platform_bundles_response(self) -> dict[str, Any]:
        items = await self.list_bundles()
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "bundle_count": len(items),
            "default_bundle_count": len(DEFAULT_FEATURE_FLAG_BUNDLES),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def platform_bundle_detail_response(self, bundle_id: str) -> dict[str, Any]:
        bundle = await self.get_bundle(bundle_id)
        return {
            "phase": PHASE_LABEL,
            "bundle": bundle,
            "found": bundle is not None,
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def platform_members_response(self, bundle_id: str) -> dict[str, Any]:
        members = await self.list_members(bundle_id)
        return {
            "phase": PHASE_LABEL,
            "bundle_id": bundle_id,
            "items": members,
            "member_count": len(members),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def platform_reviews_response(self, *, bundle_id: str | None = None, bundle_key: str | None = None) -> dict[str, Any]:
        reviews = await self.list_reviews(bundle_id=bundle_id, bundle_key=bundle_key)
        return {
            "phase": PHASE_LABEL,
            "items": reviews,
            "review_count": len(reviews),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_bundles_response(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_bundles(agency_view=True)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "bundle_count": len(items),
            "notice": "Feature bundles are informational only. They do not enable features or enforce access.",
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_bundle_detail_response(self, agency_id: str, bundle_id: str) -> dict[str, Any]:
        bundle = await self.get_bundle(bundle_id, agency_view=True)
        if bundle:
            bundle["agency_id"] = agency_id
            bundle["review_notes"] = "Platform bundle review metadata only."
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "bundle": bundle,
            "found": bundle is not None,
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def _all_bundles(self, *, agency_view: bool = False) -> list[dict[str, Any]]:
        stored = await self.db.collection(BUNDLE_COLLECTION).find_many()
        bundles_by_key = {item.get("bundle_key"): self._normalize_bundle(item) for item in stored if item.get("bundle_key")}
        for default_bundle in DEFAULT_FEATURE_FLAG_BUNDLES:
            bundles_by_key.setdefault(default_bundle["bundle_key"], self._normalize_bundle(default_bundle, default_bundle=True))
        bundles = list(bundles_by_key.values())
        if agency_view:
            bundles = [item for item in bundles if item.get("visible_to_agencies", True)]
        return bundles

    def _normalize_bundle(self, bundle: dict[str, Any], *, default_bundle: bool = False) -> dict[str, Any]:
        bundle_key = bundle.get("bundle_key") or bundle.get("key") or "bundle"
        readiness = self._readiness(bundle.get("readiness") or {})
        members = [self._member_projection(item) for item in bundle.get("members") or []]
        normalized = FeatureFlagBundle(
            id=bundle.get("id") or f"bundle_{bundle_key}",
            bundle_key=bundle_key,
            bundle_name=bundle.get("bundle_name") or bundle.get("name") or bundle_key.replace("_", " ").title(),
            description=bundle.get("description"),
            category=bundle.get("category") or "general",
            members=[FeatureFlagBundleMember(**item) for item in members],
            review_status=bundle.get("review_status") or "draft",
            readiness=readiness,
            visible_to_agencies=bundle.get("visible_to_agencies", True),
            metadata_only=True,
            runtime_enforcement_disabled=True,
            entitlement_checks_disabled=True,
            rollout_disabled=True,
        ).model_dump(mode="json")
        normalized["default_bundle"] = default_bundle
        return normalized

    def _bundle_projection(self, bundle: dict[str, Any] | None, *, agency_view: bool = False) -> dict[str, Any] | None:
        if not bundle:
            return None
        projected = dict(bundle)
        projected["bundle_id"] = projected.get("id")
        projected["flag_count"] = len(projected.get("members") or [])
        projected["members"] = [self._member_projection(item) for item in projected.get("members") or []]
        projected["contained_flags"] = [item["feature_key"] for item in projected["members"]]
        projected["readiness_status"] = self._readiness_status(projected.get("readiness") or {})
        projected["review_notes"] = "Platform review metadata only."
        projected["read_only"] = True
        projected.update(self.safety_flags())
        if agency_view:
            projected["payloads_hidden"] = True
        return projected

    def _bundle_summary(self, bundle: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        summary = FeatureFlagBundleSummary(
            bundle_id=bundle.get("id") or bundle.get("bundle_key") or "bundle",
            bundle_key=bundle.get("bundle_key") or "bundle",
            bundle_name=bundle.get("bundle_name") or "Feature Flag Bundle",
            description=bundle.get("description"),
            category=bundle.get("category") or "general",
            flag_count=len(bundle.get("members") or []),
            review_status=bundle.get("review_status") or "draft",
            readiness=self._readiness(bundle.get("readiness") or {}),
            last_updated=bundle.get("updated_at"),
            metadata_only=True,
        ).model_dump(mode="json")
        summary["members"] = [self._member_projection(item) for item in bundle.get("members") or []]
        summary["contained_flags"] = [item["feature_key"] for item in summary["members"]]
        summary["readiness_status"] = self._readiness_status(summary.get("readiness") or {})
        summary["review_notes"] = "Platform review metadata only."
        summary["read_only"] = True
        summary.update(self.safety_flags())
        if agency_view:
            summary["payloads_hidden"] = True
        return summary

    def _readiness(self, readiness: dict[str, Any]) -> BundleReadiness:
        allowed = set(BundleReadiness.model_fields.keys())
        data = {key: readiness.get(key) for key in allowed if key in readiness}
        return BundleReadiness(**data)

    def _member_projection(self, member: dict[str, Any]) -> dict[str, Any]:
        return FeatureFlagBundleMember(
            module_key=member.get("module_key") or "general",
            feature_key=member.get("feature_key") or "feature",
            display_name=member.get("display_name") or member.get("feature_key") or "Feature",
            description=member.get("description"),
            metadata_only=True,
        ).model_dump(mode="json")

    def _review_projection(self, review: dict[str, Any]) -> dict[str, Any]:
        projected = FeatureFlagBundleReview(
            id=review.get("id"),
            bundle_id=review.get("bundle_id"),
            bundle_key=review.get("bundle_key") or "bundle",
            reviewer=review.get("reviewer"),
            review_status=review.get("review_status") or "draft",
            notes=review.get("notes"),
            metadata_only=True,
        ).model_dump(mode="json")
        projected["read_only"] = True
        projected.update(self.safety_flags())
        return projected

    def _readiness_status(self, readiness: dict[str, Any]) -> str:
        if readiness.get("rollout_ready"):
            return "Rollout ready"
        if readiness.get("deployment_ready") or readiness.get("testing_complete"):
            return "Review ready"
        if readiness.get("bundle_review_complete"):
            return "Reviewed"
        return "Metadata draft"

    def _sort_timestamp(self, value: Any) -> str:
        if value is None:
            return ""
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "runtime_feature_enforcement_disabled": True,
            "entitlement_checks_disabled": True,
            "billing_disabled": True,
            "execution_logic_disabled": True,
            "module_hiding_disabled": True,
            "permission_decisions_disabled": True,
            "publishing_disabled": True,
            "rollout_disabled": True,
            "percentage_deployments_disabled": True,
            "provider_integrations_disabled": True,
            "external_ai_disabled": True,
            "scraping_disabled": True,
            "background_workers_disabled": True,
            "notifications_disabled": True,
            "email_sending_disabled": True,
            "api_integrations_disabled": True,
            "external_api_calls_disabled": True,
        }
