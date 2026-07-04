from __future__ import annotations

from typing import Any

from database import Database
from models import (
    AirlineIntelligenceAgencyConsumptionNote,
    AirlineIntelligenceAgencyConsumptionNoteCreateRequest,
    AirlineIntelligenceAgencyConsumptionProfile,
    AirlineIntelligenceAgencyConsumptionProfileCreateRequest,
    AirlineIntelligenceAgencyConsumptionProfileUpdateRequest,
    AirlineIntelligenceAgencyConsumptionSnapshot,
    AirlineIntelligenceAgencyConsumptionSnapshotCreateRequest,
    AirlineIntelligenceAgencyKnowledgeAssignmentView,
    AirlineIntelligenceAgencyUsageReadiness,
    AirlineIntelligenceAgencyUsageReadinessRequest,
    now_utc,
)
from services.airline_intelligence_knowledge_version_service import (
    RELEASE_ASSIGNMENT_COLLECTION,
    RELEASE_CHANNEL_COLLECTION,
    VERSION_COLLECTION,
    AirlineIntelligenceKnowledgeVersionService,
)
from services.offer_decision_export_delivery_service import actor_from_user, enum_value, payload_dict


PHASE_LABEL = "phase_40_0_feature_bundle_assignment_foundation"

CONSUMPTION_PROFILE_COLLECTION = "airline_intelligence_agency_consumption_profiles"
ASSIGNMENT_VIEW_COLLECTION = "airline_intelligence_agency_knowledge_assignment_views"
USAGE_READINESS_COLLECTION = "airline_intelligence_agency_usage_readiness"
CONSUMPTION_NOTE_COLLECTION = "airline_intelligence_agency_consumption_notes"
CONSUMPTION_SNAPSHOT_COLLECTION = "airline_intelligence_agency_consumption_snapshots"

USAGE_AREAS = ["crm", "cms", "client_portal", "offer_builder"]


class AirlineIntelligenceAgencyConsumptionService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.version_service = AirlineIntelligenceKnowledgeVersionService(db)

    async def platform_summary(self) -> dict[str, Any]:
        profiles = await self.list_profiles()
        readiness = await self.list_usage_readiness()
        notes = await self.list_notes()
        snapshots = await self.list_snapshots()
        views = await self.db.collection(ASSIGNMENT_VIEW_COLLECTION).find_many()
        return {
            "phase": PHASE_LABEL,
            "profile_count": len(profiles),
            "assignment_view_count": len(views),
            "usage_readiness_count": len(readiness),
            "note_count": len(notes),
            "snapshot_count": len(snapshots),
            "agency_visible_profile_count": len([item for item in profiles if item.get("visible_to_agency") and item.get("status") == "visible"]),
            "ready_crm_count": len([item for item in readiness if item.get("usage_area") == "crm" and item.get("status") == "ready"]),
            "ready_cms_count": len([item for item in readiness if item.get("usage_area") == "cms" and item.get("status") == "ready"]),
            "ready_client_portal_count": len([item for item in readiness if item.get("usage_area") == "client_portal" and item.get("status") == "ready"]),
            "ready_offer_builder_count": len([item for item in readiness if item.get("usage_area") == "offer_builder" and item.get("status") == "ready"]),
            "platform_governance_ui_enabled": True,
            "agency_plain_language_ui_enabled": True,
            **self._safety_flags(),
            "diagnostic": "Phase 39.3 bridges governed airline intelligence knowledge versions into agency-visible consumption metadata. It does not publish, recommend, execute providers, book, mutate PNRs, ticket, issue EMDs, charge, invoice, settle, scrape, call external APIs, or call external AI.",
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        profiles = await self.list_profiles(agency_id=agency_id, agency_view=True)
        assignments = await self.list_agency_visible_assignments(agency_id)
        readiness = await self.list_usage_readiness(agency_id=agency_id, agency_view=True)
        notes = await self.list_notes(agency_id=agency_id, visible_to_agency=True, agency_view=True)
        return {
            "phase": PHASE_LABEL,
            "profile_count": len(profiles),
            "assigned_knowledge_count": len(assignments),
            "usage_readiness_count": len(readiness),
            "note_count": len(notes),
            "usage_cards": [self._usage_card(area, profiles, readiness) for area in USAGE_AREAS],
            "read_only": True,
            "payloads_hidden": True,
            "plain_language_overview": "Airline intelligence usage shows which platform-reviewed knowledge is safe for agency work areas. It is read-only and does not publish content, recommend airlines, price, book, ticket, or change PNRs.",
            **self._safety_flags(),
        }

    async def create_profile(self, payload: AirlineIntelligenceAgencyConsumptionProfileCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        version = await self._require_version(data["knowledge_version_id"])
        if data.get("release_channel_id"):
            await self._require_release_channel(data["release_channel_id"])
        actor = data.get("created_by") or actor_from_user(user)
        status = enum_value(data.get("status") or "draft")
        profile = AirlineIntelligenceAgencyConsumptionProfile(
            agency_id=data["agency_id"],
            knowledge_version_id=version["id"],
            release_channel_id=data.get("release_channel_id"),
            status=status,
            crm_safe=self._coalesce_bool(data.get("crm_safe"), version.get("crm_safe", False)),
            cms_safe=self._coalesce_bool(data.get("cms_safe"), version.get("cms_safe", False)),
            client_portal_safe=self._coalesce_bool(data.get("client_portal_safe"), version.get("client_portal_safe", False)),
            offer_builder_safe=self._coalesce_bool(data.get("offer_builder_safe"), version.get("offer_builder_safe", False)),
            plain_language_summary=data.get("plain_language_summary") or version.get("coverage_summary") or "Airline intelligence coverage is available for agency review.",
            allowed_usage_notes=data.get("allowed_usage_notes") or self._allowed_notes_from_version(version),
            blocked_usage_notes=data.get("blocked_usage_notes") or self._blocked_notes_from_version(version),
            internal_owner_notes=data.get("internal_owner_notes"),
            visible_to_agency=self._coalesce_bool(data.get("visible_to_agency"), status == "visible"),
            created_by=actor,
        )
        stored = await self.db.collection(CONSUMPTION_PROFILE_COLLECTION).insert_one(profile.model_dump(mode="json"))
        await self._upsert_assignment_view(stored)
        await self._create_snapshot(
            stored["agency_id"],
            stored.get("knowledge_version_id"),
            stored.get("id"),
            "profile_created",
            actor,
            {"profile": stored, "metadata_only": True},
        )
        return {"profile": stored, "assignment_view": await self._assignment_view_for_profile(stored), **self._safety_flags()}

    async def update_profile(self, profile_id: str, payload: AirlineIntelligenceAgencyConsumptionProfileUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        profile = await self._require_profile(profile_id)
        data = payload_dict(payload)
        if data.get("release_channel_id"):
            await self._require_release_channel(data["release_channel_id"])
        updates = {key: enum_value(value) for key, value in data.items()}
        updates["updated_by"] = updates.get("updated_by") or actor_from_user(user)
        updated = await self.db.collection(CONSUMPTION_PROFILE_COLLECTION).update_one({"id": profile_id}, updates)
        result = updated or profile
        await self._upsert_assignment_view(result)
        await self._create_snapshot(
            result["agency_id"],
            result.get("knowledge_version_id"),
            result.get("id"),
            "profile_updated",
            updates["updated_by"],
            {"profile": result, "metadata_only": True},
        )
        return {"profile": result, "assignment_view": await self._assignment_view_for_profile(result), **self._safety_flags()}

    async def list_profiles(
        self,
        *,
        agency_id: str | None = None,
        knowledge_version_id: str | None = None,
        status: str | None = None,
        agency_view: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if knowledge_version_id:
            filters["knowledge_version_id"] = knowledge_version_id
        if status:
            filters["status"] = status
        profiles = await self.db.collection(CONSUMPTION_PROFILE_COLLECTION).find_many(filters or None)
        profiles.sort(key=lambda item: self._timestamp_sort_value(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [self._profile_projection(item, agency_view=agency_view) for item in profiles]

    async def get_profile(self, profile_id: str, *, agency_view: bool = False) -> dict[str, Any] | None:
        profile = await self.db.collection(CONSUMPTION_PROFILE_COLLECTION).find_one({"id": profile_id})
        if not profile:
            return None
        return self._profile_projection(profile, agency_view=agency_view)

    async def list_agency_visible_assignments(self, agency_id: str) -> list[dict[str, Any]]:
        profile_views = await self.db.collection(ASSIGNMENT_VIEW_COLLECTION).find_many({"agency_id": agency_id})
        profile_views = [self._assignment_projection(item) for item in profile_views if item.get("status") != "disabled"]
        known_pairs = {(item.get("knowledge_version_id"), item.get("release_channel_id")) for item in profile_views}
        version_summaries = await self.version_service.agency_versions(agency_id)
        assignment_views: list[dict[str, Any]] = list(profile_views)
        for version in version_summaries:
            pair = (version.get("id"), None)
            if pair in known_pairs:
                continue
            assignment_views.append(
                {
                    "id": f"derived-{version.get('id')}",
                    "agency_id": agency_id,
                    "knowledge_version_id": version.get("id"),
                    "release_channel_id": None,
                    "release_assignment_id": None,
                    "profile_id": None,
                    "status": "visible" if version.get("agency_visibility_mode") == "visible" else "review",
                    "crm_safe": version.get("crm_safe", False),
                    "cms_safe": version.get("cms_safe", False),
                    "client_portal_safe": version.get("client_portal_safe", False),
                    "offer_builder_safe": version.get("offer_builder_safe", False),
                    "plain_language_summary": version.get("coverage_summary") or version.get("title"),
                    "allowed_usage_notes": "Platform-visible knowledge version can be reviewed for safe agency use.",
                    "blocked_usage_notes": self._blocked_notes_from_version(version),
                    "metadata_only": True,
                    "payloads_hidden": True,
                }
            )
        assignment_views.sort(key=lambda item: (item.get("status") != "visible", item.get("plain_language_summary") or ""))
        return assignment_views

    async def calculate_usage_readiness(self, agency_id: str, payload: AirlineIntelligenceAgencyUsageReadinessRequest | dict[str, Any] | None = None, user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload or {})
        profiles = await self.list_profiles(
            agency_id=agency_id,
            knowledge_version_id=data.get("knowledge_version_id"),
            agency_view=False,
        )
        if data.get("profile_id"):
            profiles = [profile for profile in profiles if profile.get("id") == data["profile_id"]]
        if not profiles:
            raise ValueError("No agency consumption profiles found for readiness calculation.")
        areas = [enum_value(data["usage_area"])] if data.get("usage_area") else USAGE_AREAS
        actor = data.get("calculated_by") or actor_from_user(user)
        records: list[dict[str, Any]] = []
        for profile in profiles:
            for area in areas:
                record = AirlineIntelligenceAgencyUsageReadiness(
                    agency_id=agency_id,
                    knowledge_version_id=profile["knowledge_version_id"],
                    release_channel_id=profile.get("release_channel_id"),
                    profile_id=profile["id"],
                    usage_area=area,
                    status=self._readiness_status(profile, area),
                    safe_for_usage=self._usage_area_safe(profile, area) and profile.get("status") == "visible",
                    plain_language_summary=self._readiness_summary(profile, area),
                    allowed_usage_notes=profile.get("allowed_usage_notes"),
                    blocked_usage_notes=self._readiness_blocked_notes(profile, area),
                    calculated_by=actor,
                    calculated_at=now_utc(),
                )
                existing = await self.db.collection(USAGE_READINESS_COLLECTION).find_one({"profile_id": profile["id"], "usage_area": area})
                if existing:
                    stored = await self.db.collection(USAGE_READINESS_COLLECTION).update_one({"id": existing["id"]}, record.model_dump(mode="json"))
                else:
                    stored = await self.db.collection(USAGE_READINESS_COLLECTION).insert_one(record.model_dump(mode="json"))
                records.append(stored or record.model_dump(mode="json"))
        await self._create_snapshot(
            agency_id,
            data.get("knowledge_version_id"),
            data.get("profile_id"),
            "usage_readiness_calculated",
            actor,
            {"usage_readiness": records, "metadata_only": True},
        )
        return {"items": [self._readiness_projection(item, agency_view=False) for item in records], **self._safety_flags()}

    async def list_usage_readiness(
        self,
        *,
        agency_id: str | None = None,
        profile_id: str | None = None,
        usage_area: str | None = None,
        agency_view: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if profile_id:
            filters["profile_id"] = profile_id
        if usage_area:
            filters["usage_area"] = usage_area
        records = await self.db.collection(USAGE_READINESS_COLLECTION).find_many(filters or None)
        records.sort(key=lambda item: (item.get("usage_area") or "", self._timestamp_sort_value(item.get("updated_at") or item.get("created_at"))), reverse=True)
        return [self._readiness_projection(item, agency_view=agency_view) for item in records]

    async def create_note(self, payload: AirlineIntelligenceAgencyConsumptionNoteCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_version(data["knowledge_version_id"])
        if data.get("profile_id"):
            await self._require_profile(data["profile_id"])
        note = AirlineIntelligenceAgencyConsumptionNote(
            agency_id=data["agency_id"],
            knowledge_version_id=data["knowledge_version_id"],
            release_channel_id=data.get("release_channel_id"),
            profile_id=data.get("profile_id"),
            note_type=data.get("note_type", "agency_guidance"),
            note=data["note"],
            created_by=data.get("created_by") or actor_from_user(user),
            visible_to_agency=bool(data.get("visible_to_agency", False)),
        )
        stored = await self.db.collection(CONSUMPTION_NOTE_COLLECTION).insert_one(note.model_dump(mode="json"))
        await self._create_snapshot(
            stored["agency_id"],
            stored.get("knowledge_version_id"),
            stored.get("profile_id"),
            "note_created",
            stored.get("created_by"),
            {"note_id": stored["id"], "visible_to_agency": stored.get("visible_to_agency"), "metadata_only": True},
        )
        return {"note": stored, **self._safety_flags()}

    async def list_notes(
        self,
        *,
        agency_id: str | None = None,
        profile_id: str | None = None,
        visible_to_agency: bool | None = None,
        agency_view: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if profile_id:
            filters["profile_id"] = profile_id
        if visible_to_agency is not None:
            filters["visible_to_agency"] = visible_to_agency
        notes = await self.db.collection(CONSUMPTION_NOTE_COLLECTION).find_many(filters or None)
        notes.sort(key=lambda item: self._timestamp_sort_value(item.get("created_at")), reverse=True)
        return [self._note_projection(item, agency_view=agency_view) for item in notes if not agency_view or item.get("visible_to_agency")]

    async def create_snapshot(self, payload: AirlineIntelligenceAgencyConsumptionSnapshotCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        if data.get("knowledge_version_id"):
            await self._require_version(data["knowledge_version_id"])
        if data.get("profile_id"):
            await self._require_profile(data["profile_id"])
        snapshot = await self._create_snapshot(
            data["agency_id"],
            data.get("knowledge_version_id"),
            data.get("profile_id"),
            data.get("snapshot_type") or "manual",
            data.get("created_by") or actor_from_user(user),
            data.get("snapshot_json") or {},
        )
        return {"snapshot": snapshot, **self._safety_flags()}

    async def list_snapshots(
        self,
        *,
        agency_id: str | None = None,
        profile_id: str | None = None,
        agency_view: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if profile_id:
            filters["profile_id"] = profile_id
        snapshots = await self.db.collection(CONSUMPTION_SNAPSHOT_COLLECTION).find_many(filters or None)
        snapshots.sort(key=lambda item: self._timestamp_sort_value(item.get("created_at")), reverse=True)
        return [self._snapshot_projection(item, agency_view=agency_view) for item in snapshots]

    async def _upsert_assignment_view(self, profile: dict[str, Any]) -> None:
        existing = await self.db.collection(ASSIGNMENT_VIEW_COLLECTION).find_one({"profile_id": profile["id"]})
        view = AirlineIntelligenceAgencyKnowledgeAssignmentView(
            agency_id=profile["agency_id"],
            knowledge_version_id=profile["knowledge_version_id"],
            release_channel_id=profile.get("release_channel_id"),
            profile_id=profile["id"],
            status=profile.get("status", "draft"),
            crm_safe=profile.get("crm_safe", False),
            cms_safe=profile.get("cms_safe", False),
            client_portal_safe=profile.get("client_portal_safe", False),
            offer_builder_safe=profile.get("offer_builder_safe", False),
            plain_language_summary=profile.get("plain_language_summary"),
            allowed_usage_notes=profile.get("allowed_usage_notes"),
            blocked_usage_notes=profile.get("blocked_usage_notes"),
        )
        data = view.model_dump(mode="json")
        if existing:
            await self.db.collection(ASSIGNMENT_VIEW_COLLECTION).update_one({"id": existing["id"]}, data)
        else:
            await self.db.collection(ASSIGNMENT_VIEW_COLLECTION).insert_one(data)

    async def _assignment_view_for_profile(self, profile: dict[str, Any]) -> dict[str, Any] | None:
        view = await self.db.collection(ASSIGNMENT_VIEW_COLLECTION).find_one({"profile_id": profile["id"]})
        return self._assignment_projection(view) if view else None

    async def _create_snapshot(
        self,
        agency_id: str,
        knowledge_version_id: str | None,
        profile_id: str | None,
        snapshot_type: str,
        created_by: str | None,
        snapshot_json: dict[str, Any],
    ) -> dict[str, Any]:
        snapshot = AirlineIntelligenceAgencyConsumptionSnapshot(
            agency_id=agency_id,
            knowledge_version_id=knowledge_version_id,
            profile_id=profile_id,
            snapshot_type=snapshot_type,
            snapshot_json=snapshot_json,
            created_by=created_by,
        )
        return await self.db.collection(CONSUMPTION_SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))

    async def _require_version(self, version_id: str) -> dict[str, Any]:
        version = await self.db.collection(VERSION_COLLECTION).find_one({"id": version_id})
        if not version:
            raise ValueError("Airline intelligence knowledge version not found.")
        return version

    async def _require_release_channel(self, channel_id: str) -> dict[str, Any]:
        channel = await self.db.collection(RELEASE_CHANNEL_COLLECTION).find_one({"id": channel_id})
        if not channel:
            raise ValueError("Airline intelligence release channel not found.")
        return channel

    async def _require_profile(self, profile_id: str) -> dict[str, Any]:
        profile = await self.db.collection(CONSUMPTION_PROFILE_COLLECTION).find_one({"id": profile_id})
        if not profile:
            raise ValueError("Airline intelligence agency consumption profile not found.")
        return profile

    def _profile_projection(self, profile: dict[str, Any], *, agency_view: bool) -> dict[str, Any]:
        projection = dict(profile)
        if agency_view:
            projection.pop("internal_owner_notes", None)
            projection["read_only"] = True
            projection["payloads_hidden"] = True
        projection["metadata_only"] = True
        return projection

    def _assignment_projection(self, view: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": view.get("id"),
            "agency_id": view.get("agency_id"),
            "knowledge_version_id": view.get("knowledge_version_id"),
            "release_channel_id": view.get("release_channel_id"),
            "release_assignment_id": view.get("release_assignment_id"),
            "profile_id": view.get("profile_id"),
            "status": view.get("status"),
            "crm_safe": view.get("crm_safe", False),
            "cms_safe": view.get("cms_safe", False),
            "client_portal_safe": view.get("client_portal_safe", False),
            "offer_builder_safe": view.get("offer_builder_safe", False),
            "plain_language_summary": view.get("plain_language_summary"),
            "allowed_usage_notes": view.get("allowed_usage_notes"),
            "blocked_usage_notes": view.get("blocked_usage_notes"),
            "metadata_only": True,
            "payloads_hidden": True,
        }

    def _readiness_projection(self, record: dict[str, Any], *, agency_view: bool) -> dict[str, Any]:
        projection = dict(record)
        projection["metadata_only"] = True
        if agency_view:
            projection["read_only"] = True
            projection["payloads_hidden"] = True
        return projection

    def _note_projection(self, note: dict[str, Any], *, agency_view: bool) -> dict[str, Any]:
        projection = dict(note)
        if agency_view:
            projection = {
                "id": note.get("id"),
                "agency_id": note.get("agency_id"),
                "knowledge_version_id": note.get("knowledge_version_id"),
                "profile_id": note.get("profile_id"),
                "note_type": note.get("note_type"),
                "note": note.get("note"),
                "created_at": note.get("created_at"),
                "visible_to_agency": note.get("visible_to_agency"),
                "metadata_only": True,
                "read_only": True,
                "payloads_hidden": True,
            }
        return projection

    def _snapshot_projection(self, snapshot: dict[str, Any], *, agency_view: bool) -> dict[str, Any]:
        if not agency_view:
            return {**snapshot, "metadata_only": True}
        summary = snapshot.get("snapshot_json", {}).get("plain_language_summary") or "Immutable agency consumption metadata snapshot."
        return {
            "id": snapshot.get("id"),
            "agency_id": snapshot.get("agency_id"),
            "knowledge_version_id": snapshot.get("knowledge_version_id"),
            "profile_id": snapshot.get("profile_id"),
            "snapshot_type": snapshot.get("snapshot_type"),
            "plain_language_summary": summary,
            "created_at": snapshot.get("created_at"),
            "immutable": True,
            "metadata_only": True,
            "read_only": True,
            "payloads_hidden": True,
        }

    def _usage_card(self, area: str, profiles: list[dict[str, Any]], readiness: list[dict[str, Any]]) -> dict[str, Any]:
        area_readiness = [item for item in readiness if item.get("usage_area") == area]
        ready = any(item.get("status") == "ready" for item in area_readiness)
        available_profiles = [profile for profile in profiles if self._usage_area_safe(profile, area) and profile.get("status") == "visible"]
        return {
            "usage_area": area,
            "label": self._usage_area_label(area),
            "available": ready or bool(available_profiles),
            "status": "ready" if ready or available_profiles else "needs_review",
            "plain_language_summary": (
                f"{self._usage_area_label(area)} can use visible platform-governed airline intelligence metadata."
                if ready or available_profiles
                else f"{self._usage_area_label(area)} is not active until platform review marks safe usage."
            ),
            "profile_count": len(available_profiles),
            "metadata_only": True,
        }

    def _readiness_status(self, profile: dict[str, Any], area: str) -> str:
        if profile.get("status") == "disabled":
            return "blocked"
        if not self._usage_area_safe(profile, area):
            return "not_available"
        if profile.get("status") != "visible" or not profile.get("visible_to_agency"):
            return "needs_review"
        return "ready"

    def _readiness_summary(self, profile: dict[str, Any], area: str) -> str:
        label = self._usage_area_label(area)
        status = self._readiness_status(profile, area)
        if status == "ready":
            return f"{label} can consume this visible airline intelligence metadata."
        if status == "needs_review":
            return f"{label} has safe metadata flags but the profile is still under platform review."
        if status == "blocked":
            return f"{label} consumption is disabled for this profile."
        return f"{label} consumption is not available for this knowledge version."

    def _readiness_blocked_notes(self, profile: dict[str, Any], area: str) -> str | None:
        if self._usage_area_safe(profile, area):
            return profile.get("blocked_usage_notes")
        return profile.get("blocked_usage_notes") or f"{self._usage_area_label(area)} safe-use flag is off."

    def _usage_area_safe(self, profile: dict[str, Any], area: str) -> bool:
        return bool(
            {
                "crm": profile.get("crm_safe"),
                "cms": profile.get("cms_safe"),
                "client_portal": profile.get("client_portal_safe"),
                "offer_builder": profile.get("offer_builder_safe"),
            }.get(area)
        )

    def _usage_area_label(self, area: str) -> str:
        return {
            "crm": "Available for CRM",
            "cms": "Available for agency website",
            "client_portal": "Available for client portal",
            "offer_builder": "Available for offer builder",
        }.get(area, area.replace("_", " ").title())

    def _allowed_notes_from_version(self, version: dict[str, Any]) -> str:
        enabled = []
        if version.get("crm_safe"):
            enabled.append("CRM")
        if version.get("cms_safe"):
            enabled.append("agency website")
        if version.get("client_portal_safe"):
            enabled.append("client portal")
        if version.get("offer_builder_safe"):
            enabled.append("offer builder")
        return f"Safe-use metadata enabled for: {', '.join(enabled) if enabled else 'none yet'}."

    def _blocked_notes_from_version(self, version: dict[str, Any]) -> str:
        blocked = []
        if not version.get("crm_safe"):
            blocked.append("CRM")
        if not version.get("cms_safe"):
            blocked.append("agency website")
        if not version.get("client_portal_safe"):
            blocked.append("client portal")
        if not version.get("offer_builder_safe"):
            blocked.append("offer builder")
        return f"Not active for: {', '.join(blocked) if blocked else 'no usage area'}."

    def _timestamp_sort_value(self, value: Any) -> str:
        return value.isoformat() if hasattr(value, "isoformat") else str(value or "")

    def _coalesce_bool(self, value: Any, fallback: bool) -> bool:
        return bool(fallback if value is None else value)

    def _safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only_consumption_enabled": True,
            "consumption_profiles_enabled": True,
            "agency_assignment_visibility_enabled": True,
            "crm_readiness_metadata_enabled": True,
            "cms_readiness_metadata_enabled": True,
            "client_portal_readiness_metadata_enabled": True,
            "offer_builder_readiness_metadata_enabled": True,
            "automatic_publishing_disabled": True,
            "cms_publishing_disabled": True,
            "client_portal_publishing_disabled": True,
            "recommendations_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "external_ai_disabled": True,
            "external_api_calls_disabled": True,
            "scraping_disabled": True,
            "automatic_sending_disabled": True,
        }
