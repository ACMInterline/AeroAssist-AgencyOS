from __future__ import annotations

from typing import Any

from database import Database
from models import AgencyFeatureFlagAudit, AgencyFeatureFlagReadiness, now_utc


PHASE_LABEL = "phase_54_5_request_to_trip_operational_conversion_foundation"

AUDIT_COLLECTION = "agency_feature_flag_audits"
READINESS_COLLECTION = "agency_feature_flag_readiness"

READINESS_CHECKLIST_KEYS = [
    "documentation_complete",
    "backend_complete",
    "api_complete",
    "ui_complete",
    "testing_complete",
    "deployment_ready",
    "rollout_ready",
]


class AgencyFeatureFlagAuditService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_audits(
        self,
        *,
        agency_id: str | None = None,
        feature_key: str | None = None,
        agency_view: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if feature_key:
            filters["feature_key"] = feature_key
        audits = await self.db.collection(AUDIT_COLLECTION).find_many(filters or None)
        audits.sort(key=lambda item: self._timestamp_sort_value(item.get("changed_at") or item.get("created_at")), reverse=True)
        return [self._audit_projection(item, agency_view=agency_view) for item in audits]

    async def list_readiness(
        self,
        *,
        agency_id: str | None = None,
        feature_key: str | None = None,
        agency_view: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if feature_key:
            filters["feature_key"] = feature_key
        readiness = await self.db.collection(READINESS_COLLECTION).find_many(filters or None)
        readiness.sort(key=lambda item: (item.get("feature_key") or "", item.get("agency_id") or ""))
        return [self._readiness_projection(item, agency_view=agency_view) for item in readiness]

    async def platform_audits_response(self, *, agency_id: str | None = None, feature_key: str | None = None) -> dict[str, Any]:
        items = await self.list_audits(agency_id=agency_id, feature_key=feature_key)
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "audit_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def platform_readiness_response(self, *, agency_id: str | None = None, feature_key: str | None = None) -> dict[str, Any]:
        items = await self.list_readiness(agency_id=agency_id, feature_key=feature_key)
        return {
            "phase": PHASE_LABEL,
            "feature_key": feature_key,
            "items": items,
            "readiness_count": len(items),
            "readiness_checklist_keys": READINESS_CHECKLIST_KEYS,
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_readiness_response(self, agency_id: str, *, feature_key: str | None = None) -> dict[str, Any]:
        items = await self.list_readiness(agency_id=agency_id, feature_key=feature_key, agency_view=True)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "feature_key": feature_key,
            "item": items[0] if feature_key and items else None,
            "items": items,
            "readiness_count": len(items),
            "readiness_checklist_keys": READINESS_CHECKLIST_KEYS,
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def record_audit(
        self,
        *,
        agency_id: str,
        feature_key: str,
        previous_state: str | None = None,
        proposed_state: str = "disabled",
        changed_by: str | None = None,
        reason: str | None = None,
        notes: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        audit = AgencyFeatureFlagAudit(
            agency_id=agency_id,
            feature_key=feature_key,
            previous_state=previous_state,
            proposed_state=proposed_state,
            changed_by=changed_by,
            changed_at=now_utc(),
            reason=reason,
            notes=notes,
            metadata=metadata or {},
        )
        stored = await self.db.collection(AUDIT_COLLECTION).insert_one(audit.model_dump(mode="json"))
        return self._audit_projection(stored)

    async def ensure_readiness(self, *, agency_id: str, feature_key: str, reviewed_by: str | None = None) -> dict[str, Any]:
        existing = await self.db.collection(READINESS_COLLECTION).find_one({"agency_id": agency_id, "feature_key": feature_key})
        if existing:
            return self._readiness_projection(existing)
        readiness = AgencyFeatureFlagReadiness(
            agency_id=agency_id,
            feature_key=feature_key,
            reviewed_by=reviewed_by,
            last_reviewed=now_utc() if reviewed_by else None,
        )
        stored = await self.db.collection(READINESS_COLLECTION).insert_one(readiness.model_dump(mode="json"))
        return self._readiness_projection(stored)

    def _audit_projection(self, audit: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        projected = dict(audit)
        projected.update(
            {
                "metadata_only": True,
                "read_only": True,
                "automatic_enforcement_disabled": True,
                "feature_blocking_disabled": True,
            }
        )
        if agency_view:
            projected["metadata"] = {"metadata_only": True, "payloads_hidden": True}
        return projected

    def _readiness_projection(self, readiness: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        projected = dict(readiness)
        checklist = {key: bool(projected.get(key)) for key in READINESS_CHECKLIST_KEYS}
        projected.update(
            {
                "metadata_only": True,
                "read_only": True,
                "checklist": checklist,
                "automatic_enforcement_disabled": True,
                "feature_blocking_disabled": True,
                "deployment_ready": bool(projected.get("deployment_ready")),
                "rollout_ready": bool(projected.get("rollout_ready")),
            }
        )
        if agency_view:
            projected["payloads_hidden"] = True
        return projected

    def _timestamp_sort_value(self, value: Any) -> str:
        if value is None:
            return ""
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "automatic_enforcement_disabled": True,
            "route_blocking_disabled": True,
            "permission_changes_disabled": True,
            "subscription_changes_disabled": True,
            "billing_disabled": True,
            "payments_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "cms_publishing_disabled": True,
            "client_portal_publishing_disabled": True,
            "external_api_calls_disabled": True,
            "external_ai_disabled": True,
            "scraping_disabled": True,
            "automatic_sending_disabled": True,
            "feature_blocking_disabled": True,
            "operational_enforcement_enabled": False,
        }


def readiness_label(key: str) -> str:
    return key.replace("_complete", "").replace("_ready", "").replace("_", " ").title()
