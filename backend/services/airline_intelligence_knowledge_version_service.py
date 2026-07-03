from __future__ import annotations

from typing import Any

from database import Database
from models import (
    AirlineIntelligenceKnowledgeReleaseAssignment,
    AirlineIntelligenceKnowledgeReleaseAssignmentCreateRequest,
    AirlineIntelligenceKnowledgeReleaseAssignmentUpdateRequest,
    AirlineIntelligenceKnowledgeReleaseChannel,
    AirlineIntelligenceKnowledgeReleaseChannelCreateRequest,
    AirlineIntelligenceKnowledgeReleaseChannelUpdateRequest,
    AirlineIntelligenceKnowledgeRollbackPlan,
    AirlineIntelligenceKnowledgeRollbackPlanCreateRequest,
    AirlineIntelligenceKnowledgeRollbackPlanUpdateRequest,
    AirlineIntelligenceKnowledgeVersion,
    AirlineIntelligenceKnowledgeVersionComparison,
    AirlineIntelligenceKnowledgeVersionComparisonCreateRequest,
    AirlineIntelligenceKnowledgeVersionCreateRequest,
    AirlineIntelligenceKnowledgeVersionItem,
    AirlineIntelligenceKnowledgeVersionItemCreateRequest,
    AirlineIntelligenceKnowledgeVersionItemUpdateRequest,
    AirlineIntelligenceKnowledgeVersionSnapshot,
    AirlineIntelligenceKnowledgeVersionSnapshotCreateRequest,
    AirlineIntelligenceKnowledgeVersionUpdateRequest,
    now_utc,
)
from services.airline_intelligence_data_pack_review_service import (
    CONFLICT_COLLECTION,
    FIELD_MAPPING_COLLECTION,
    PROMOTION_READINESS_COLLECTION,
    REVIEW_COLLECTION,
)
from services.airline_intelligence_data_pack_service import ITEM_COLLECTION, PACK_COLLECTION
from services.offer_decision_export_delivery_service import actor_from_user, enum_value, payload_dict


PHASE_LABEL = "phase_39_2_airline_intelligence_knowledge_versioning_foundation"

VERSION_COLLECTION = "airline_intelligence_knowledge_versions"
VERSION_ITEM_COLLECTION = "airline_intelligence_knowledge_version_items"
RELEASE_CHANNEL_COLLECTION = "airline_intelligence_knowledge_release_channels"
RELEASE_ASSIGNMENT_COLLECTION = "airline_intelligence_knowledge_release_assignments"
COMPARISON_COLLECTION = "airline_intelligence_knowledge_version_comparisons"
ROLLBACK_PLAN_COLLECTION = "airline_intelligence_knowledge_rollback_plans"
SNAPSHOT_COLLECTION = "airline_intelligence_knowledge_version_snapshots"


class AirlineIntelligenceKnowledgeVersionService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self) -> dict[str, Any]:
        versions = await self.list_versions()
        items = await self.list_version_items()
        channels = await self.list_release_channels()
        assignments = await self.list_release_assignments()
        comparisons = await self.list_comparisons()
        rollback_plans = await self.list_rollback_plans()
        snapshots = await self.list_snapshots()
        return {
            "phase": PHASE_LABEL,
            "knowledge_version_count": len(versions),
            "version_item_count": len(items),
            "release_channel_count": len(channels),
            "release_assignment_count": len(assignments),
            "comparison_count": len(comparisons),
            "rollback_plan_count": len(rollback_plans),
            "snapshot_count": len(snapshots),
            "frozen_version_count": len([item for item in versions if item.get("status") == "frozen"]),
            "approved_version_count": len([item for item in versions if item.get("status") == "approved"]),
            "published_metadata_version_count": len([item for item in versions if item.get("status") == "published"]),
            "agency_visible_version_count": len([item for item in versions if item.get("agency_visibility_mode") == "visible"]),
            "platform_versioning_ui_enabled": True,
            "agency_version_visibility_ui_enabled": True,
            "release_channel_metadata_enabled": True,
            "rollback_plan_metadata_enabled": True,
            **self._safety_flags(),
            "diagnostic": "Phase 39.2 records governed airline intelligence knowledge versions, release-channel assignments, comparisons, rollback plans, and immutable snapshots as metadata only. It does not promote staged data into operational airline tables or perform external, publishing, recommendation, booking, ticketing, EMD, payment, invoice, settlement, or provider actions.",
        }

    async def create_version(self, payload: AirlineIntelligenceKnowledgeVersionCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        existing = await self.db.collection(VERSION_COLLECTION).find_one({"version_code": data["version_code"]})
        if existing:
            raise ValueError("Knowledge version code already exists.")
        await self._require_many(PACK_COLLECTION, data.get("source_pack_ids", []), "Airline intelligence data pack")
        await self._require_many(REVIEW_COLLECTION, data.get("source_review_ids", []), "Airline intelligence data pack review")
        await self._require_many(PROMOTION_READINESS_COLLECTION, data.get("source_promotion_readiness_ids", []), "Airline intelligence promotion readiness")
        version = AirlineIntelligenceKnowledgeVersion(
            version_code=data["version_code"],
            title=data["title"],
            description=data.get("description"),
            source_pack_ids=data.get("source_pack_ids", []),
            source_review_ids=data.get("source_review_ids", []),
            source_promotion_readiness_ids=data.get("source_promotion_readiness_ids", []),
            coverage_summary=data.get("coverage_summary") or await self._version_coverage_summary(data.get("source_pack_ids", []), []),
            publication_scope_metadata=data.get("publication_scope_metadata", {}),
            agency_visibility_mode=data.get("agency_visibility_mode", "hidden"),
            crm_safe=bool(data.get("crm_safe", False)),
            cms_safe=bool(data.get("cms_safe", False)),
            client_portal_safe=bool(data.get("client_portal_safe", False)),
            offer_builder_safe=bool(data.get("offer_builder_safe", False)),
            created_by=data.get("created_by") or actor_from_user(user),
        )
        stored = await self.db.collection(VERSION_COLLECTION).insert_one(version.model_dump(mode="json"))
        await self._create_snapshot(stored["id"], "version_created", actor_from_user(user), {"version": stored})
        return {"version": stored, **self._safety_flags()}

    async def update_version(self, version_id: str, payload: AirlineIntelligenceKnowledgeVersionUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        version = await self._require_version(version_id)
        data = payload_dict(payload)
        if not data:
            raise ValueError("No version changes were provided.")
        updates = {key: enum_value(value) for key, value in data.items()}
        status = updates.get("status")
        actor = actor_from_user(user)
        if status == "frozen":
            updates["frozen_at"] = now_utc()
        elif status == "approved":
            updates["approved_by"] = updates.get("approved_by") or actor
            updates["approved_at"] = now_utc()
        elif status == "published":
            updates["published_by"] = updates.get("published_by") or actor
            updates["published_at"] = now_utc()
        updated = await self.db.collection(VERSION_COLLECTION).update_one({"id": version_id}, updates)
        return {"version": updated or version, **self._safety_flags()}

    async def list_versions(self, *, status: str | None = None, agency_visibility_mode: str | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if agency_visibility_mode:
            filters["agency_visibility_mode"] = agency_visibility_mode
        versions = await self.db.collection(VERSION_COLLECTION).find_many(filters or None)
        versions.sort(key=lambda item: self._timestamp_sort_value(item.get("updated_at") or item.get("created_at")), reverse=True)
        return versions

    async def get_version(self, version_id: str, *, agency_view: bool = False) -> dict[str, Any] | None:
        version = await self.db.collection(VERSION_COLLECTION).find_one({"id": version_id})
        if not version:
            return None
        if agency_view:
            return await self._agency_version_detail(version)
        return {
            "version": version,
            "items": await self.list_version_items(version_id=version_id),
            "assignments": await self.list_release_assignments(version_id=version_id),
            "snapshots": await self.list_snapshots(version_id=version_id),
            "metadata_only": True,
            **self._safety_flags(),
        }

    async def add_version_item(self, version_id: str, payload: AirlineIntelligenceKnowledgeVersionItemCreateRequest | dict[str, Any]) -> dict[str, Any]:
        version = await self._require_editable_version(version_id)
        data = payload_dict(payload)
        source_item = await self._require_pack_item(data["source_pack_item_id"])
        if data.get("field_mapping_id"):
            await self._require_field_mapping(data["field_mapping_id"])
        await self._require_many(CONFLICT_COLLECTION, data.get("conflict_ids", []), "Airline intelligence data pack conflict")
        if data.get("readiness_id"):
            await self._require_readiness(data["readiness_id"])
        preview = data.get("normalized_payload_preview") or source_item.get("normalized_payload") or {}
        item = AirlineIntelligenceKnowledgeVersionItem(
            version_id=version_id,
            source_pack_item_id=source_item["id"],
            target_domain=data.get("target_domain") or enum_value(source_item.get("target_domain")),
            target_record_key=data.get("target_record_key") or source_item.get("target_record_key") or source_item.get("display_name"),
            target_airline_code=data.get("target_airline_code") or source_item.get("airline_iata_code"),
            field_mapping_id=data.get("field_mapping_id"),
            conflict_ids=data.get("conflict_ids", []),
            readiness_id=data.get("readiness_id"),
            inclusion_status=data.get("inclusion_status", "included"),
            inclusion_reason=data.get("inclusion_reason") or "Included for governed metadata version review.",
            normalized_payload_preview=preview,
            agency_plain_language_summary=data.get("agency_plain_language_summary") or source_item.get("plain_language_summary") or source_item.get("display_name"),
        )
        stored = await self.db.collection(VERSION_ITEM_COLLECTION).insert_one(item.model_dump(mode="json"))
        await self._refresh_version_coverage(version["id"])
        return {"version_item": stored, **self._safety_flags()}

    async def update_version_item(self, version_item_id: str, payload: AirlineIntelligenceKnowledgeVersionItemUpdateRequest | dict[str, Any]) -> dict[str, Any]:
        item = await self._require_version_item(version_item_id)
        await self._require_editable_version(item["version_id"])
        data = payload_dict(payload)
        updates = {key: enum_value(value) for key, value in data.items()}
        updated = await self.db.collection(VERSION_ITEM_COLLECTION).update_one({"id": version_item_id}, updates)
        await self._refresh_version_coverage(item["version_id"])
        return {"version_item": updated or item, **self._safety_flags()}

    async def remove_version_item(self, version_item_id: str, reason: str | None = None) -> dict[str, Any]:
        item = await self._require_version_item(version_item_id)
        await self._require_editable_version(item["version_id"])
        updated = await self.db.collection(VERSION_ITEM_COLLECTION).update_one(
            {"id": version_item_id},
            {"inclusion_status": "excluded", "inclusion_reason": reason or "Excluded from this metadata version."},
        )
        await self._refresh_version_coverage(item["version_id"])
        return {"version_item": updated or item, **self._safety_flags()}

    async def list_version_items(self, *, version_id: str | None = None, inclusion_status: str | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if version_id:
            filters["version_id"] = version_id
        if inclusion_status:
            filters["inclusion_status"] = inclusion_status
        items = await self.db.collection(VERSION_ITEM_COLLECTION).find_many(filters or None)
        items.sort(key=lambda item: (item.get("target_airline_code") or "", item.get("target_domain") or "", item.get("target_record_key") or ""))
        return items

    async def freeze_version(self, version_id: str, user: dict | None = None) -> dict[str, Any]:
        version = await self._require_editable_version(version_id)
        items = await self.list_version_items(version_id=version_id)
        if not items:
            raise ValueError("Add at least one version item before freezing the knowledge version.")
        updated = await self.db.collection(VERSION_COLLECTION).update_one({"id": version_id}, {"status": "frozen", "frozen_at": now_utc()})
        await self._create_snapshot(version_id, "version_frozen", actor_from_user(user), await self._version_snapshot_payload(version_id))
        return {"version": updated or version, **self._safety_flags()}

    async def approve_version(self, version_id: str, payload: AirlineIntelligenceKnowledgeVersionUpdateRequest | dict[str, Any] | None = None, user: dict | None = None) -> dict[str, Any]:
        version = await self._require_version(version_id)
        if version.get("status") not in {"frozen", "approved"}:
            raise ValueError("Freeze the knowledge version before approving it.")
        data = payload_dict(payload or {})
        actor = data.get("approved_by") or actor_from_user(user)
        updated = await self.db.collection(VERSION_COLLECTION).update_one({"id": version_id}, {"status": "approved", "approved_by": actor, "approved_at": now_utc()})
        await self._create_snapshot(version_id, "version_approved", actor, await self._version_snapshot_payload(version_id))
        return {"version": updated or version, **self._safety_flags()}

    async def mark_published_metadata(self, version_id: str, payload: AirlineIntelligenceKnowledgeVersionUpdateRequest | dict[str, Any] | None = None, user: dict | None = None) -> dict[str, Any]:
        version = await self._require_version(version_id)
        if version.get("status") not in {"approved", "published"}:
            raise ValueError("Approve the knowledge version before marking it published metadata-only.")
        data = payload_dict(payload or {})
        actor = data.get("published_by") or actor_from_user(user)
        visibility = data.get("agency_visibility_mode") or ("visible" if version.get("agency_visibility_mode") == "hidden" else version.get("agency_visibility_mode"))
        updates = {
            "status": "published",
            "published_by": actor,
            "published_at": now_utc(),
            "agency_visibility_mode": enum_value(visibility),
        }
        updated = await self.db.collection(VERSION_COLLECTION).update_one({"id": version_id}, updates)
        await self._create_snapshot(version_id, "version_published_metadata", actor, await self._version_snapshot_payload(version_id))
        return {"version": updated or version, **self._safety_flags()}

    async def create_release_channel(self, payload: AirlineIntelligenceKnowledgeReleaseChannelCreateRequest | dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        existing = await self.db.collection(RELEASE_CHANNEL_COLLECTION).find_one({"channel_code": data["channel_code"]})
        if existing:
            raise ValueError("Release channel code already exists.")
        channel = AirlineIntelligenceKnowledgeReleaseChannel(**data)
        stored = await self.db.collection(RELEASE_CHANNEL_COLLECTION).insert_one(channel.model_dump(mode="json"))
        return {"release_channel": stored, **self._safety_flags()}

    async def update_release_channel(self, channel_id: str, payload: AirlineIntelligenceKnowledgeReleaseChannelUpdateRequest | dict[str, Any]) -> dict[str, Any]:
        channel = await self._require_release_channel(channel_id)
        data = payload_dict(payload)
        updates = {key: enum_value(value) for key, value in data.items()}
        updated = await self.db.collection(RELEASE_CHANNEL_COLLECTION).update_one({"id": channel_id}, updates)
        return {"release_channel": updated or channel, **self._safety_flags()}

    async def list_release_channels(self, *, audience: str | None = None, is_active: bool | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if audience:
            filters["audience"] = audience
        if is_active is not None:
            filters["is_active"] = is_active
        channels = await self.db.collection(RELEASE_CHANNEL_COLLECTION).find_many(filters or None)
        channels.sort(key=lambda item: (not item.get("is_active", False), item.get("channel_code", "")))
        return channels

    async def create_release_assignment(self, payload: AirlineIntelligenceKnowledgeReleaseAssignmentCreateRequest | dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_release_channel(data["channel_id"])
        await self._require_version(data["version_id"])
        assignment = AirlineIntelligenceKnowledgeReleaseAssignment(**data)
        stored = await self.db.collection(RELEASE_ASSIGNMENT_COLLECTION).insert_one(assignment.model_dump(mode="json"))
        return {"release_assignment": stored, **self._safety_flags()}

    async def update_release_assignment(self, assignment_id: str, payload: AirlineIntelligenceKnowledgeReleaseAssignmentUpdateRequest | dict[str, Any]) -> dict[str, Any]:
        assignment = await self._require_release_assignment(assignment_id)
        data = payload_dict(payload)
        updates = {key: enum_value(value) for key, value in data.items()}
        updated = await self.db.collection(RELEASE_ASSIGNMENT_COLLECTION).update_one({"id": assignment_id}, updates)
        return {"release_assignment": updated or assignment, **self._safety_flags()}

    async def list_release_assignments(self, *, version_id: str | None = None, channel_id: str | None = None, agency_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if version_id:
            filters["version_id"] = version_id
        if channel_id:
            filters["channel_id"] = channel_id
        if agency_id:
            filters["agency_id"] = agency_id
        if status:
            filters["status"] = status
        assignments = await self.db.collection(RELEASE_ASSIGNMENT_COLLECTION).find_many(filters or None)
        assignments.sort(key=lambda item: self._timestamp_sort_value(item.get("updated_at") or item.get("created_at")), reverse=True)
        return assignments

    async def compare_versions(self, payload: AirlineIntelligenceKnowledgeVersionComparisonCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_version(data["base_version_id"])
        await self._require_version(data["compare_version_id"])
        base_items = await self.list_version_items(version_id=data["base_version_id"], inclusion_status="included")
        compare_items = await self.list_version_items(version_id=data["compare_version_id"], inclusion_status="included")
        base_map = {self._item_compare_key(item): item for item in base_items}
        compare_map = {self._item_compare_key(item): item for item in compare_items}
        added = [self._comparison_item(compare_map[key]) for key in sorted(compare_map.keys() - base_map.keys())]
        removed = [self._comparison_item(base_map[key]) for key in sorted(base_map.keys() - compare_map.keys())]
        changed = [
            self._comparison_item(compare_map[key])
            for key in sorted(base_map.keys() & compare_map.keys())
            if self._compare_payload_signature(base_map[key]) != self._compare_payload_signature(compare_map[key])
        ]
        comparison = AirlineIntelligenceKnowledgeVersionComparison(
            base_version_id=data["base_version_id"],
            compare_version_id=data["compare_version_id"],
            summary=f"{len(added)} added, {len(changed)} changed, {len(removed)} removed airline intelligence item(s).",
            added_items=added,
            changed_items=changed,
            removed_items=removed,
            conflict_summary="Comparison is metadata-only and did not mutate airline intelligence records.",
            agency_impact_summary=f"Agencies may see {len(added) + len(changed)} updated coverage summary item(s) when a visible version is assigned.",
            cms_impact_summary="CMS publication remains disabled.",
            client_portal_impact_summary="Client portal publication remains disabled.",
            offer_builder_impact_summary="Offer builder consumption remains controlled by safe-use flags.",
        )
        stored = await self.db.collection(COMPARISON_COLLECTION).insert_one(comparison.model_dump(mode="json"))
        await self._create_snapshot(data["compare_version_id"], "version_comparison", actor_from_user(user), {"comparison": stored})
        return {"comparison": stored, **self._safety_flags()}

    async def list_comparisons(self, *, base_version_id: str | None = None, compare_version_id: str | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if base_version_id:
            filters["base_version_id"] = base_version_id
        if compare_version_id:
            filters["compare_version_id"] = compare_version_id
        comparisons = await self.db.collection(COMPARISON_COLLECTION).find_many(filters or None)
        comparisons.sort(key=lambda item: self._timestamp_sort_value(item.get("created_at")), reverse=True)
        return comparisons

    async def create_rollback_plan(self, payload: AirlineIntelligenceKnowledgeRollbackPlanCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_version(data["from_version_id"])
        await self._require_version(data["to_version_id"])
        if data.get("channel_id"):
            await self._require_release_channel(data["channel_id"])
        checklist = data.get("checklist") or [
            {"label": "Confirm affected release channel", "status": "open"},
            {"label": "Confirm agency-visible impact summary", "status": "open"},
            {"label": "Confirm rollback is metadata-only", "status": "open"},
        ]
        plan = AirlineIntelligenceKnowledgeRollbackPlan(
            from_version_id=data["from_version_id"],
            to_version_id=data["to_version_id"],
            channel_id=data.get("channel_id"),
            reason=data["reason"],
            impact_summary=data.get("impact_summary") or "Rollback plan records metadata only; no operational airline tables are changed.",
            checklist=checklist,
            status=data.get("status", "draft"),
        )
        stored = await self.db.collection(ROLLBACK_PLAN_COLLECTION).insert_one(plan.model_dump(mode="json"))
        await self._create_snapshot(data["from_version_id"], "rollback_plan", actor_from_user(user), {"rollback_plan": stored})
        return {"rollback_plan": stored, **self._safety_flags()}

    async def update_rollback_plan(self, rollback_plan_id: str, payload: AirlineIntelligenceKnowledgeRollbackPlanUpdateRequest | dict[str, Any]) -> dict[str, Any]:
        plan = await self._require_rollback_plan(rollback_plan_id)
        data = payload_dict(payload)
        updates = {key: enum_value(value) for key, value in data.items()}
        updated = await self.db.collection(ROLLBACK_PLAN_COLLECTION).update_one({"id": rollback_plan_id}, updates)
        return {"rollback_plan": updated or plan, **self._safety_flags()}

    async def list_rollback_plans(self, *, from_version_id: str | None = None, to_version_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if from_version_id:
            filters["from_version_id"] = from_version_id
        if to_version_id:
            filters["to_version_id"] = to_version_id
        if status:
            filters["status"] = status
        plans = await self.db.collection(ROLLBACK_PLAN_COLLECTION).find_many(filters or None)
        plans.sort(key=lambda item: self._timestamp_sort_value(item.get("updated_at") or item.get("created_at")), reverse=True)
        return plans

    async def create_snapshot(self, version_id: str, payload: AirlineIntelligenceKnowledgeVersionSnapshotCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        await self._require_version(version_id)
        data = payload_dict(payload)
        snapshot = await self._create_snapshot(
            version_id,
            data.get("snapshot_type") or "manual",
            data.get("created_by") or actor_from_user(user),
            data.get("metadata_json") or await self._version_snapshot_payload(version_id),
        )
        return {"snapshot": snapshot, **self._safety_flags()}

    async def list_snapshots(self, *, version_id: str | None = None, snapshot_type: str | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if version_id:
            filters["version_id"] = version_id
        if snapshot_type:
            filters["snapshot_type"] = snapshot_type
        snapshots = await self.db.collection(SNAPSHOT_COLLECTION).find_many(filters or None)
        snapshots.sort(key=lambda item: self._timestamp_sort_value(item.get("created_at")), reverse=True)
        return snapshots

    async def agency_summary(self, agency_id: str | None = None) -> dict[str, Any]:
        versions = await self._agency_visible_versions(agency_id)
        current = await self.agency_current_version(agency_id)
        preview = await self.agency_preview_version(agency_id)
        return {
            **await self.summary(),
            "read_only": True,
            "payloads_hidden": True,
            "visible_versions": [self._agency_version_summary(item) for item in versions],
            "current_version": current.get("version") if current else None,
            "preview_version": preview.get("version") if preview else None,
            "plain_language_overview": "Airline intelligence knowledge versions show which reviewed airline coverage is visible or in preview for agency work. They do not publish CMS/client portal content, recommend airlines, price, book, ticket, or change PNRs.",
        }

    async def agency_current_version(self, agency_id: str | None = None) -> dict[str, Any] | None:
        versions = await self._agency_visible_versions(agency_id, current=True)
        if not versions:
            return None
        return await self._agency_version_detail(versions[0])

    async def agency_preview_version(self, agency_id: str | None = None) -> dict[str, Any] | None:
        versions = await self._agency_visible_versions(agency_id, preview=True)
        if not versions:
            return None
        return await self._agency_version_detail(versions[0])

    async def agency_versions(self, agency_id: str | None = None) -> list[dict[str, Any]]:
        return [self._agency_version_summary(item) for item in await self._agency_visible_versions(agency_id)]

    async def _agency_visible_versions(self, agency_id: str | None = None, *, current: bool = False, preview: bool = False) -> list[dict[str, Any]]:
        versions = await self.list_versions()
        channels = {channel["id"]: channel for channel in await self.list_release_channels(is_active=True)}
        assignments = await self.list_release_assignments()
        eligible_version_ids: set[str] = set()
        for assignment in assignments:
            channel = channels.get(assignment.get("channel_id"))
            if not channel:
                continue
            assigned_to_agency = not assignment.get("agency_id") or assignment.get("agency_id") == agency_id
            if not assigned_to_agency:
                continue
            if current and assignment.get("status") != "active":
                continue
            if preview and assignment.get("status") not in {"planned", "paused"}:
                continue
            if not current and not preview and assignment.get("status") not in {"active", "planned", "paused"}:
                continue
            if channel.get("audience") in {"all_agencies", "pilot_agencies"}:
                eligible_version_ids.add(assignment["version_id"])
        filtered: list[dict[str, Any]] = []
        for version in versions:
            if current and not (version.get("status") == "published" and version.get("agency_visibility_mode") == "visible"):
                continue
            if preview and version.get("agency_visibility_mode") not in {"preview", "visible"}:
                continue
            if version.get("id") in eligible_version_ids or (version.get("agency_visibility_mode") == "visible" and not preview) or version.get("agency_visibility_mode") == "preview":
                filtered.append(version)
        return filtered

    async def _refresh_version_coverage(self, version_id: str) -> None:
        version = await self._require_version(version_id)
        items = await self.list_version_items(version_id=version_id)
        summary = await self._version_coverage_summary(version.get("source_pack_ids", []), items)
        await self.db.collection(VERSION_COLLECTION).update_one({"id": version_id}, {"coverage_summary": summary})

    async def _version_coverage_summary(self, source_pack_ids: list[str], items: list[dict[str, Any]]) -> str:
        packs = [pack for pack_id in source_pack_ids if (pack := await self.db.collection(PACK_COLLECTION).find_one({"id": pack_id}))]
        airline_codes = sorted({item.get("target_airline_code") for item in items if item.get("target_airline_code")})
        domains = sorted({item.get("target_domain") for item in items if item.get("target_domain")})
        pack_names = [pack.get("name") for pack in packs if pack.get("name")]
        return (
            f"Knowledge version groups {len(items)} reviewed airline intelligence item(s)"
            f" from {len(source_pack_ids)} source pack(s)"
            f"{' including ' + ', '.join(pack_names[:3]) if pack_names else ''}."
            f" Airlines: {', '.join(airline_codes) if airline_codes else 'not specified'}."
            f" Domains: {', '.join(domains) if domains else 'not specified'}."
        )

    async def _version_snapshot_payload(self, version_id: str) -> dict[str, Any]:
        return {
            "version": await self._require_version(version_id),
            "items": await self.list_version_items(version_id=version_id),
            "assignments": await self.list_release_assignments(version_id=version_id),
            "metadata_only": True,
            **self._safety_flags(),
        }

    async def _create_snapshot(self, version_id: str, snapshot_type: str, created_by: str | None, frozen_payload: dict[str, Any] | None) -> dict[str, Any]:
        snapshot = AirlineIntelligenceKnowledgeVersionSnapshot(
            version_id=version_id,
            snapshot_type=snapshot_type,
            frozen_payload=frozen_payload or {},
            created_by=created_by,
        )
        return await self.db.collection(SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))

    async def _require_many(self, collection_name: str, ids: list[str], label: str) -> None:
        for item_id in ids:
            item = await self.db.collection(collection_name).find_one({"id": item_id})
            if not item:
                raise ValueError(f"{label} not found: {item_id}")

    async def _require_version(self, version_id: str) -> dict[str, Any]:
        version = await self.db.collection(VERSION_COLLECTION).find_one({"id": version_id})
        if not version:
            raise ValueError("Airline intelligence knowledge version not found.")
        return version

    async def _require_editable_version(self, version_id: str) -> dict[str, Any]:
        version = await self._require_version(version_id)
        if version.get("status") in {"published", "superseded", "rolled_back", "archived"}:
            raise ValueError("Published, superseded, rolled-back, or archived versions cannot be edited.")
        return version

    async def _require_version_item(self, version_item_id: str) -> dict[str, Any]:
        item = await self.db.collection(VERSION_ITEM_COLLECTION).find_one({"id": version_item_id})
        if not item:
            raise ValueError("Airline intelligence knowledge version item not found.")
        return item

    async def _require_pack_item(self, item_id: str) -> dict[str, Any]:
        item = await self.db.collection(ITEM_COLLECTION).find_one({"id": item_id})
        if not item:
            raise ValueError("Airline intelligence data pack item not found.")
        return item

    async def _require_field_mapping(self, mapping_id: str) -> dict[str, Any]:
        mapping = await self.db.collection(FIELD_MAPPING_COLLECTION).find_one({"id": mapping_id})
        if not mapping:
            raise ValueError("Airline intelligence data pack field mapping not found.")
        return mapping

    async def _require_readiness(self, readiness_id: str) -> dict[str, Any]:
        readiness = await self.db.collection(PROMOTION_READINESS_COLLECTION).find_one({"id": readiness_id})
        if not readiness:
            raise ValueError("Airline intelligence data pack promotion readiness not found.")
        return readiness

    async def _require_release_channel(self, channel_id: str) -> dict[str, Any]:
        channel = await self.db.collection(RELEASE_CHANNEL_COLLECTION).find_one({"id": channel_id})
        if not channel:
            raise ValueError("Airline intelligence release channel not found.")
        return channel

    async def _require_release_assignment(self, assignment_id: str) -> dict[str, Any]:
        assignment = await self.db.collection(RELEASE_ASSIGNMENT_COLLECTION).find_one({"id": assignment_id})
        if not assignment:
            raise ValueError("Airline intelligence release assignment not found.")
        return assignment

    async def _require_rollback_plan(self, rollback_plan_id: str) -> dict[str, Any]:
        plan = await self.db.collection(ROLLBACK_PLAN_COLLECTION).find_one({"id": rollback_plan_id})
        if not plan:
            raise ValueError("Airline intelligence rollback plan not found.")
        return plan

    def _item_compare_key(self, item: dict[str, Any]) -> tuple[str, str, str]:
        return (
            item.get("target_airline_code") or "",
            item.get("target_domain") or "",
            item.get("target_record_key") or item.get("source_pack_item_id") or "",
        )

    def _compare_payload_signature(self, item: dict[str, Any]) -> tuple[Any, ...]:
        return (
            item.get("field_mapping_id"),
            item.get("readiness_id"),
            item.get("normalized_payload_preview", {}),
            item.get("agency_plain_language_summary"),
        )

    def _comparison_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "version_item_id": item.get("id"),
            "target_airline_code": item.get("target_airline_code"),
            "target_domain": item.get("target_domain"),
            "target_record_key": item.get("target_record_key"),
            "agency_plain_language_summary": item.get("agency_plain_language_summary"),
        }

    def _timestamp_sort_value(self, value: Any) -> str:
        return value.isoformat() if hasattr(value, "isoformat") else str(value or "")

    async def _agency_version_detail(self, version: dict[str, Any]) -> dict[str, Any]:
        items = await self.list_version_items(version_id=version["id"], inclusion_status="included")
        return {
            "version": self._agency_version_summary(version),
            "items": [self._agency_item(item) for item in items],
            "what_changed": [item.get("agency_plain_language_summary") for item in items[:10] if item.get("agency_plain_language_summary")],
            "read_only": True,
            "payloads_hidden": True,
            **self._safety_flags(),
        }

    def _agency_version_summary(self, version: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": version.get("id"),
            "version_code": version.get("version_code"),
            "title": version.get("title"),
            "description": version.get("description"),
            "status": version.get("status"),
            "coverage_summary": version.get("coverage_summary"),
            "agency_visibility_mode": version.get("agency_visibility_mode"),
            "crm_safe": version.get("crm_safe", False),
            "cms_safe": version.get("cms_safe", False),
            "client_portal_safe": version.get("client_portal_safe", False),
            "offer_builder_safe": version.get("offer_builder_safe", False),
            "published_at": version.get("published_at"),
            "metadata_only": True,
            "operational_promotion_disabled": True,
        }

    def _agency_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item.get("id"),
            "target_domain": item.get("target_domain"),
            "target_record_key": item.get("target_record_key"),
            "target_airline_code": item.get("target_airline_code"),
            "inclusion_status": item.get("inclusion_status"),
            "agency_plain_language_summary": item.get("agency_plain_language_summary"),
            "metadata_only": True,
            "payload_hidden": True,
        }

    def _safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only_versioning_enabled": True,
            "metadata_only": True,
            "operational_promotion_disabled": True,
            "automatic_promotion_disabled": True,
            "scraping_disabled": True,
            "external_ai_disabled": True,
            "external_api_calls_disabled": True,
            "cms_publishing_disabled": True,
            "client_portal_publishing_disabled": True,
            "recommendations_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "automatic_sending_disabled": True,
        }
