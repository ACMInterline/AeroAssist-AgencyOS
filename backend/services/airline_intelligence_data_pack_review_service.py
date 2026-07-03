from __future__ import annotations

from collections import defaultdict
from typing import Any

from database import Database
from models import (
    AirlineIntelligenceDataPackChecklistItemCreateRequest,
    AirlineIntelligenceDataPackChecklistItemUpdateRequest,
    AirlineIntelligenceDataPackConflict,
    AirlineIntelligenceDataPackConflictUpdateRequest,
    AirlineIntelligenceDataPackFieldMapping,
    AirlineIntelligenceDataPackFieldMappingCreateRequest,
    AirlineIntelligenceDataPackFieldMappingUpdateRequest,
    AirlineIntelligenceDataPackPromotionReadiness,
    AirlineIntelligenceDataPackPromotionReadinessRequest,
    AirlineIntelligenceDataPackReview,
    AirlineIntelligenceDataPackReviewChecklistItem,
    AirlineIntelligenceDataPackReviewCreateRequest,
    AirlineIntelligenceDataPackReviewSnapshot,
    AirlineIntelligenceDataPackReviewSnapshotCreateRequest,
    AirlineIntelligenceDataPackReviewUpdateRequest,
    now_utc,
)
from services.airline_intelligence_data_pack_service import ITEM_COLLECTION, PACK_COLLECTION
from services.offer_decision_export_delivery_service import actor_from_user, enum_value, payload_dict


PHASE_LABEL = "phase_39_1_airline_intelligence_data_pack_review_foundation"

REVIEW_COLLECTION = "airline_intelligence_data_pack_reviews"
CHECKLIST_COLLECTION = "airline_intelligence_data_pack_review_checklist_items"
FIELD_MAPPING_COLLECTION = "airline_intelligence_data_pack_field_mappings"
CONFLICT_COLLECTION = "airline_intelligence_data_pack_conflicts"
PROMOTION_READINESS_COLLECTION = "airline_intelligence_data_pack_promotion_readiness"
SNAPSHOT_COLLECTION = "airline_intelligence_data_pack_review_snapshots"

TARGET_COLLECTION_BY_DOMAIN = {
    "airline_profile": "airline_intelligence_profiles",
    "airline_contacts": "airline_contacts",
    "fleet": "airline_fleet_types",
    "tail_numbers": "aircraft_tail_numbers",
    "aircraft_configurations": "aircraft_configurations",
    "seatmaps": "aircraft_seatmaps",
    "routes": "airline_routes",
    "fare_families": "airline_fare_families",
    "rbd_matrix": "airline_rbd_matrix_rows",
    "fare_rules": "airline_fare_rules",
    "ancillaries": "airline_ancillaries",
    "interline": "airline_interline_agreements",
    "distribution": "airline_distribution_profiles",
    "pss_parameters": "airline_pss_parameters",
    "gds_parameters": "airline_gds_parameters",
    "exception_rules": "airline_exception_rules",
    "brand_assets": "airline_brand_assets",
    "special_services_rules": "airline_exception_rules",
    "cms_content": "airline_brand_assets",
    "client_portal_display_metadata": "airline_intelligence_profiles",
}


class AirlineIntelligenceDataPackReviewService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self) -> dict[str, Any]:
        reviews = await self.list_reviews()
        checklist_items = await self.list_checklist_items()
        mappings = await self.list_field_mappings()
        conflicts = await self.list_conflicts()
        readiness = await self.list_promotion_readiness()
        snapshots = await self.list_snapshots()
        return {
            "phase": PHASE_LABEL,
            "review_count": len(reviews),
            "review_checklist_item_count": len(checklist_items),
            "field_mapping_count": len(mappings),
            "conflict_count": len(conflicts),
            "open_conflict_count": len([item for item in conflicts if item.get("status") == "open"]),
            "promotion_readiness_count": len(readiness),
            "promotion_ready_count": len([item for item in readiness if item.get("ready_for_promotion")]),
            "review_snapshot_count": len(snapshots),
            "agency_internal_crm_safe_count": len([item for item in readiness if item.get("safe_for_agency_internal_crm")]),
            "agency_display_safe_count": len([item for item in readiness if item.get("safe_for_agency_display")]),
            "cms_display_safe_count": len([item for item in readiness if item.get("safe_for_cms_display")]),
            "client_portal_safe_count": len([item for item in readiness if item.get("safe_for_client_portal_later")]),
            "offer_builder_safe_count": len([item for item in readiness if item.get("safe_for_offer_builder")]),
            "review_checklists_enabled": True,
            "field_mappings_enabled": True,
            "duplicate_conflict_detection_enabled": True,
            "promotion_readiness_metadata_enabled": True,
            "agency_plain_language_coverage_enabled": True,
            "platform_review_ui_enabled": True,
            "agency_review_coverage_ui_enabled": True,
            "metadata_only_review_enabled": True,
            **self._safety_flags(),
            "diagnostic": "Phase 39.1 records metadata-only airline intelligence data pack review, mapping, conflict, and promotion-readiness status. It does not promote staged data into operational airline tables or perform any external, publishing, recommendation, booking, ticketing, EMD, payment, invoice, settlement, or provider action.",
        }

    async def create_review(self, pack_id: str, payload: AirlineIntelligenceDataPackReviewCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        pack = await self._require_pack(pack_id)
        data = payload_dict(payload)
        review = AirlineIntelligenceDataPackReview(
            pack_id=pack_id,
            status="in_review",
            review_title=data.get("review_title") or f"Review for {pack.get('name', 'airline data pack')}",
            reviewed_by=data.get("reviewed_by") or actor_from_user(user),
            reviewed_at=now_utc(),
            plain_language_coverage_summary=data.get("plain_language_coverage_summary") or self._coverage_summary(pack, await self._pack_items(pack_id), None),
            decision_notes=data.get("decision_notes"),
            safe_for_agency_internal_crm=bool(data.get("safe_for_agency_internal_crm", pack.get("safe_for_agency_internal_crm", False))),
            safe_for_agency_display=bool(data.get("safe_for_agency_display", pack.get("safe_for_agency_display", False))),
            safe_for_cms_display=bool(data.get("safe_for_cms_display", pack.get("safe_for_cms_display", False))),
            safe_for_client_portal_later=bool(data.get("safe_for_client_portal_later", pack.get("safe_for_client_portal_later", False))),
            safe_for_offer_builder=bool(data.get("safe_for_offer_builder", pack.get("safe_for_offer_builder", False))),
        )
        stored = await self.db.collection(REVIEW_COLLECTION).insert_one(review.model_dump(mode="json"))
        await self._seed_default_checklist(stored["id"], pack_id)
        await self._create_snapshot(pack_id, stored["id"], "review_created", actor_from_user(user), {"review": stored})
        refreshed = await self._refresh_review_counts(stored["id"])
        return {"review": refreshed, **self._safety_flags()}

    async def update_review(self, review_id: str, payload: AirlineIntelligenceDataPackReviewUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        review = await self._require_review(review_id)
        data = payload_dict(payload)
        if not data:
            raise ValueError("No review changes were provided.")
        updates: dict[str, Any] = {}
        for key, value in data.items():
            updates[key] = enum_value(value)
        status = updates.get("status")
        actor = actor_from_user(user)
        if status == "approved":
            updates["approved_by"] = updates.get("approved_by") or actor
            updates["approved_at"] = now_utc()
            updates["promotion_ready"] = False
        elif status == "rejected":
            updates["rejected_by"] = updates.get("rejected_by") or actor
            updates["rejected_at"] = now_utc()
            updates["promotion_ready"] = False
        elif status == "promotion_ready":
            updates["promotion_ready"] = True
        updated = await self.db.collection(REVIEW_COLLECTION).update_one({"id": review_id}, updates)
        await self._create_snapshot(review["pack_id"], review_id, "status_changed", actor, {"updates": updates})
        refreshed = await self._refresh_review_counts(review_id)
        return {"review": refreshed or updated or review, **self._safety_flags()}

    async def list_reviews(self, *, pack_id: str | None = None, status: str | None = None, agency_view: bool = False) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if pack_id:
            filters["pack_id"] = pack_id
        if status:
            filters["status"] = status
        reviews = await self.db.collection(REVIEW_COLLECTION).find_many(filters or None)
        reviews.sort(key=lambda item: item.get("updated_at", item.get("created_at", "")), reverse=True)
        return [await self._agency_review(item) for item in reviews] if agency_view else reviews

    async def get_review(self, review_id: str, *, agency_view: bool = False) -> dict[str, Any] | None:
        review = await self.db.collection(REVIEW_COLLECTION).find_one({"id": review_id})
        if not review:
            return None
        pack = await self.db.collection(PACK_COLLECTION).find_one({"id": review["pack_id"]})
        items = await self._pack_items(review["pack_id"])
        checklist_items = await self.list_checklist_items(review_id=review_id)
        mappings = await self.list_field_mappings(pack_id=review["pack_id"])
        conflicts = await self.list_conflicts(pack_id=review["pack_id"])
        readiness = await self.list_promotion_readiness(pack_id=review["pack_id"])
        snapshots = await self.list_snapshots(pack_id=review["pack_id"], review_id=review_id)
        if agency_view:
            return {
                "review": await self._agency_review(review),
                "pack": self._agency_pack(pack) if pack else None,
                "promotion_readiness": [self._agency_readiness(item) for item in readiness],
                "coverage_summary": self._coverage_summary(pack or {}, items, readiness[0] if readiness else None),
                "read_only": True,
                "payloads_hidden": True,
                **self._safety_flags(),
            }
        return {
            "review": review,
            "pack": pack,
            "items": items,
            "checklist_items": checklist_items,
            "field_mappings": mappings,
            "conflicts": conflicts,
            "promotion_readiness": readiness,
            "snapshots": snapshots,
            **self._safety_flags(),
        }

    async def create_checklist_item(self, review_id: str, payload: AirlineIntelligenceDataPackChecklistItemCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        review = await self._require_review(review_id)
        data = payload_dict(payload)
        if data.get("item_id"):
            await self._require_item(data["item_id"])
        status = enum_value(data.get("status") or "open")
        item = AirlineIntelligenceDataPackReviewChecklistItem(
            review_id=review_id,
            pack_id=review["pack_id"],
            item_id=data.get("item_id"),
            scope=data.get("scope") or ("item" if data.get("item_id") else "pack"),
            label=data["label"],
            description=data.get("description"),
            status=status,
            required=data.get("required", True),
            completed_by=data.get("completed_by") or (actor_from_user(user) if status in {"passed", "failed", "waived"} else None),
            completed_at=now_utc() if status in {"passed", "failed", "waived"} else None,
            notes=data.get("notes"),
        )
        stored = await self.db.collection(CHECKLIST_COLLECTION).insert_one(item.model_dump(mode="json"))
        await self._refresh_review_counts(review_id)
        return {"checklist_item": stored, **self._safety_flags()}

    async def update_checklist_item(self, checklist_item_id: str, payload: AirlineIntelligenceDataPackChecklistItemUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        item = await self._require_checklist_item(checklist_item_id)
        data = payload_dict(payload)
        updates: dict[str, Any] = {}
        for key, value in data.items():
            updates[key] = enum_value(value)
        status = updates.get("status")
        if status in {"passed", "failed", "waived"}:
            updates["completed_by"] = updates.get("completed_by") or actor_from_user(user)
            updates["completed_at"] = now_utc()
        updated = await self.db.collection(CHECKLIST_COLLECTION).update_one({"id": checklist_item_id}, updates)
        await self._create_snapshot(item["pack_id"], item["review_id"], "checklist_updated", actor_from_user(user), {"checklist_item_id": checklist_item_id, "updates": updates})
        await self._refresh_review_counts(item["review_id"])
        return {"checklist_item": updated or item, **self._safety_flags()}

    async def list_checklist_items(self, *, review_id: str | None = None, pack_id: str | None = None, item_id: str | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if review_id:
            filters["review_id"] = review_id
        if pack_id:
            filters["pack_id"] = pack_id
        if item_id:
            filters["item_id"] = item_id
        items = await self.db.collection(CHECKLIST_COLLECTION).find_many(filters or None)
        items.sort(key=lambda item: (item.get("scope", ""), item.get("item_id") or "", item.get("label", "")))
        return items

    async def create_field_mapping(self, pack_id: str, payload: AirlineIntelligenceDataPackFieldMappingCreateRequest | dict[str, Any]) -> dict[str, Any]:
        await self._require_pack(pack_id)
        data = payload_dict(payload)
        if data.get("item_id"):
            await self._require_item(data["item_id"])
        mapping = AirlineIntelligenceDataPackFieldMapping(pack_id=pack_id, **data)
        stored = await self.db.collection(FIELD_MAPPING_COLLECTION).insert_one(mapping.model_dump(mode="json"))
        await self._refresh_pack_reviews(pack_id)
        return {"field_mapping": stored, **self._safety_flags()}

    async def update_field_mapping(self, mapping_id: str, payload: AirlineIntelligenceDataPackFieldMappingUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        mapping = await self._require_mapping(mapping_id)
        data = payload_dict(payload)
        updates = {key: enum_value(value) for key, value in data.items()}
        updated = await self.db.collection(FIELD_MAPPING_COLLECTION).update_one({"id": mapping_id}, updates)
        await self._create_snapshot(mapping["pack_id"], None, "field_mapping_updated", actor_from_user(user), {"mapping_id": mapping_id, "updates": updates})
        await self._refresh_pack_reviews(mapping["pack_id"])
        return {"field_mapping": updated or mapping, **self._safety_flags()}

    async def list_field_mappings(self, *, pack_id: str | None = None, item_id: str | None = None, mapping_status: str | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if pack_id:
            filters["pack_id"] = pack_id
        if item_id:
            filters["item_id"] = item_id
        if mapping_status:
            filters["mapping_status"] = mapping_status
        mappings = await self.db.collection(FIELD_MAPPING_COLLECTION).find_many(filters or None)
        mappings.sort(key=lambda item: (item.get("target_collection", ""), item.get("target_field_path", "")))
        return mappings

    async def detect_conflicts(self, pack_id: str, user: dict | None = None) -> dict[str, Any]:
        pack = await self._require_pack(pack_id)
        items = await self._pack_items(pack_id)
        mappings = await self.list_field_mappings(pack_id=pack_id)
        conflicts: list[dict[str, Any]] = []
        seen: dict[tuple[str | None, str | None, str | None], list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            key = (item.get("airline_iata_code"), enum_value(item.get("target_domain")), item.get("target_record_key") or item.get("display_name"))
            seen[key].append(item)
        for duplicate_items in seen.values():
            if len(duplicate_items) > 1:
                for item in duplicate_items:
                    conflicts.append(
                        await self._create_conflict(
                            pack_id,
                            item.get("id"),
                            {
                                "target_collection": TARGET_COLLECTION_BY_DOMAIN.get(enum_value(item.get("target_domain"))),
                                "target_record_key": item.get("target_record_key"),
                                "conflict_type": "duplicate_staged_item",
                                "severity": "warning",
                                "plain_language_summary": "More than one staged item appears to describe the same airline data.",
                                "technical_summary": "Duplicate staged item key within the same data pack.",
                                "suggested_resolution": "Review the duplicates and keep one reviewed mapping before marking the pack promotion-ready.",
                                "detected_by": actor_from_user(user),
                            },
                        )
                    )
        mapped_item_ids = {mapping.get("item_id") for mapping in mappings if mapping.get("item_id")}
        for item in items:
            if item.get("id") not in mapped_item_ids:
                conflicts.append(
                    await self._create_conflict(
                        pack_id,
                        item.get("id"),
                        {
                            "target_collection": TARGET_COLLECTION_BY_DOMAIN.get(enum_value(item.get("target_domain"))),
                            "target_record_key": item.get("target_record_key"),
                            "conflict_type": "missing_field_mapping",
                            "severity": "warning",
                            "plain_language_summary": "This staged item does not yet have a reviewed field mapping.",
                            "technical_summary": "No field mapping record exists for the staged item.",
                            "suggested_resolution": "Add a mapping from the staged payload to the intended operational collection and field.",
                            "detected_by": actor_from_user(user),
                        },
                    )
                )
        for mapping in mappings:
            if mapping.get("mapping_status") == "approved" and not mapping.get("target_collection"):
                conflicts.append(
                    await self._create_conflict(
                        pack_id,
                        mapping.get("item_id"),
                        {
                            "conflict_type": "missing_target_reference",
                            "severity": "error",
                            "plain_language_summary": "An approved mapping is missing its target collection.",
                            "technical_summary": "Approved field mapping has no target_collection.",
                            "suggested_resolution": "Choose the operational airline collection this staged field would map to.",
                            "detected_by": actor_from_user(user),
                        },
                    )
                )
        if pack.get("safe_for_client_portal_later") and pack.get("is_demo_data"):
            conflicts.append(
                await self._create_conflict(
                    pack_id,
                    None,
                    {
                        "conflict_type": "unsafe_surface_flag",
                        "severity": "error",
                        "plain_language_summary": "Demo/sample airline data is marked safe for future client portal display.",
                        "technical_summary": "Pack has safe_for_client_portal_later=true and is_demo_data=true.",
                        "suggested_resolution": "Turn off the client portal flag or replace this pack with reviewed real data.",
                        "detected_by": actor_from_user(user),
                    },
                )
            )
        await self._create_snapshot(pack_id, None, "conflicts_detected", actor_from_user(user), {"conflict_count": len(conflicts)})
        await self._refresh_pack_reviews(pack_id)
        return {
            "pack": pack,
            "conflicts": conflicts,
            "plain_language_summary": f"Detected {len(conflicts)} review issue(s). No operational airline records were changed.",
            **self._safety_flags(),
        }

    async def list_conflicts(self, *, pack_id: str | None = None, item_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if pack_id:
            filters["pack_id"] = pack_id
        if item_id:
            filters["item_id"] = item_id
        if status:
            filters["status"] = status
        conflicts = await self.db.collection(CONFLICT_COLLECTION).find_many(filters or None)
        conflicts.sort(key=lambda item: (item.get("status", ""), item.get("severity", ""), item.get("created_at", "")))
        return conflicts

    async def update_conflict(self, conflict_id: str, payload: AirlineIntelligenceDataPackConflictUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        conflict = await self.db.collection(CONFLICT_COLLECTION).find_one({"id": conflict_id})
        if not conflict:
            raise ValueError("Conflict not found.")
        data = payload_dict(payload)
        status = enum_value(data.get("status"))
        updates = {
            "status": status,
            "resolved_by": data.get("resolved_by") or actor_from_user(user),
            "resolution_notes": data.get("resolution_notes"),
            "resolved_at": now_utc() if status in {"acknowledged", "resolved", "ignored"} else None,
        }
        updated = await self.db.collection(CONFLICT_COLLECTION).update_one({"id": conflict_id}, updates)
        await self._refresh_pack_reviews(conflict["pack_id"])
        return {"conflict": updated or conflict, **self._safety_flags()}

    async def mark_promotion_readiness(self, pack_id: str, payload: AirlineIntelligenceDataPackPromotionReadinessRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        pack = await self._require_pack(pack_id)
        data = payload_dict(payload)
        review = await self._latest_review(pack_id, data.get("review_id"))
        checklist = await self.list_checklist_items(review_id=review.get("id") if review else None, pack_id=None if review else pack_id)
        required_items = [item for item in checklist if item.get("required")]
        checklist_complete = bool(required_items) and all(item.get("status") in {"passed", "waived"} for item in required_items)
        mappings = await self.list_field_mappings(pack_id=pack_id)
        approved_mapping_count = len([item for item in mappings if item.get("mapping_status") == "approved"])
        open_conflict_count = len(await self.list_conflicts(pack_id=pack_id, status="open"))
        inferred_ready = checklist_complete and approved_mapping_count > 0 and open_conflict_count == 0 and bool(review and review.get("status") in {"approved", "promotion_ready"})
        requested_status = enum_value(data.get("status")) if data.get("status") else None
        status = requested_status or ("ready" if inferred_ready else "blocked" if open_conflict_count else "needs_review")
        ready_for_promotion = status == "ready" and inferred_ready
        blocked_reason = data.get("blocked_reason")
        if not ready_for_promotion and not blocked_reason:
            blocked_reason = self._readiness_blocked_reason(checklist_complete, approved_mapping_count, open_conflict_count, review)
        readiness = AirlineIntelligenceDataPackPromotionReadiness(
            pack_id=pack_id,
            review_id=review.get("id") if review else data.get("review_id"),
            status=status,
            ready_for_promotion=ready_for_promotion,
            checklist_complete=checklist_complete,
            approved_mapping_count=approved_mapping_count,
            open_conflict_count=open_conflict_count,
            blocked_reason=blocked_reason,
            readiness_summary=data.get("readiness_summary") or self._coverage_summary(pack, await self._pack_items(pack_id), None),
            marked_by=data.get("marked_by") or actor_from_user(user),
            safe_for_agency_internal_crm=bool(data.get("safe_for_agency_internal_crm", pack.get("safe_for_agency_internal_crm", False))),
            safe_for_agency_display=bool(data.get("safe_for_agency_display", pack.get("safe_for_agency_display", False))),
            safe_for_cms_display=bool(data.get("safe_for_cms_display", pack.get("safe_for_cms_display", False))),
            safe_for_client_portal_later=bool(data.get("safe_for_client_portal_later", pack.get("safe_for_client_portal_later", False))),
            safe_for_offer_builder=bool(data.get("safe_for_offer_builder", pack.get("safe_for_offer_builder", False))),
        )
        stored = await self.db.collection(PROMOTION_READINESS_COLLECTION).insert_one(readiness.model_dump(mode="json"))
        if review:
            await self.db.collection(REVIEW_COLLECTION).update_one(
                {"id": review["id"]},
                {"promotion_ready": ready_for_promotion, "status": "promotion_ready" if ready_for_promotion else review.get("status")},
            )
        await self._create_snapshot(pack_id, review.get("id") if review else None, "readiness_marked", actor_from_user(user), {"promotion_readiness": stored})
        await self._refresh_pack_reviews(pack_id)
        return {"promotion_readiness": stored, **self._safety_flags()}

    async def list_promotion_readiness(self, *, pack_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if pack_id:
            filters["pack_id"] = pack_id
        if status:
            filters["status"] = status
        readiness = await self.db.collection(PROMOTION_READINESS_COLLECTION).find_many(filters or None)
        readiness.sort(key=lambda item: item.get("marked_at", item.get("created_at", "")), reverse=True)
        return readiness

    async def create_snapshot(self, review_id: str, payload: AirlineIntelligenceDataPackReviewSnapshotCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        review = await self._require_review(review_id)
        data = payload_dict(payload)
        snapshot = await self._create_snapshot(
            review["pack_id"],
            review_id,
            data.get("snapshot_type") or "review_created",
            data.get("created_by") or actor_from_user(user),
            data.get("metadata_json") or await self.get_review(review_id),
        )
        return {"snapshot": snapshot, **self._safety_flags()}

    async def list_snapshots(self, *, pack_id: str | None = None, review_id: str | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if pack_id:
            filters["pack_id"] = pack_id
        if review_id:
            filters["review_id"] = review_id
        snapshots = await self.db.collection(SNAPSHOT_COLLECTION).find_many(filters or None)
        snapshots.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return snapshots

    async def agency_summary(self) -> dict[str, Any]:
        summary = await self.summary()
        readiness = await self.list_promotion_readiness()
        return {
            **summary,
            "read_only": True,
            "payloads_hidden": True,
            "coverage_summaries": [self._agency_readiness(item) for item in readiness[:20]],
            "plain_language_overview": "Airline intelligence review coverage shows which staged airline facts have been reviewed and whether they are safe for agency work. It does not publish, recommend, price, book, ticket, or change PNRs.",
        }

    async def agency_coverage(self) -> dict[str, Any]:
        packs = await self.db.collection(PACK_COLLECTION).find_many()
        readiness = await self.list_promotion_readiness()
        reviews = await self.list_reviews()
        return {
            "packs": [self._agency_pack(pack) for pack in packs],
            "reviews": [await self._agency_review(review) for review in reviews],
            "promotion_readiness": [self._agency_readiness(item) for item in readiness],
            "read_only": True,
            "payloads_hidden": True,
            **self._safety_flags(),
        }

    async def _seed_default_checklist(self, review_id: str, pack_id: str) -> None:
        items = await self._pack_items(pack_id)
        default_pack_checks = [
            ("Source checked", "The pack has a source reference and reviewer notes."),
            ("Plain-language summary checked", "Agency-readable coverage is present."),
            ("Safe-use flags checked", "CRM, agency display, CMS, client portal, and offer-builder flags were reviewed."),
        ]
        for label, description in default_pack_checks:
            checklist_item = AirlineIntelligenceDataPackReviewChecklistItem(review_id=review_id, pack_id=pack_id, scope="pack", label=label, description=description)
            await self.db.collection(CHECKLIST_COLLECTION).insert_one(checklist_item.model_dump(mode="json"))
        for item in items:
            checklist_item = AirlineIntelligenceDataPackReviewChecklistItem(
                review_id=review_id,
                pack_id=pack_id,
                item_id=item["id"],
                scope="item",
                label=f"Review staged item: {item.get('display_name')}",
                description="Confirm source, target mapping, duplicates/conflicts, and safe-use flags for this staged item.",
            )
            await self.db.collection(CHECKLIST_COLLECTION).insert_one(checklist_item.model_dump(mode="json"))

    async def _create_conflict(self, pack_id: str, item_id: str | None, data: dict[str, Any]) -> dict[str, Any]:
        conflict = AirlineIntelligenceDataPackConflict(pack_id=pack_id, item_id=item_id, **data)
        return await self.db.collection(CONFLICT_COLLECTION).insert_one(conflict.model_dump(mode="json"))

    async def _create_snapshot(self, pack_id: str, review_id: str | None, snapshot_type: str, created_by: str | None, snapshot_json: dict[str, Any] | None) -> dict[str, Any]:
        snapshot = AirlineIntelligenceDataPackReviewSnapshot(
            pack_id=pack_id,
            review_id=review_id,
            snapshot_type=snapshot_type,
            snapshot_json=snapshot_json or {},
            created_by=created_by,
        )
        return await self.db.collection(SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))

    async def _refresh_pack_reviews(self, pack_id: str) -> None:
        for review in await self.list_reviews(pack_id=pack_id):
            await self._refresh_review_counts(review["id"])

    async def _refresh_review_counts(self, review_id: str) -> dict[str, Any]:
        review = await self._require_review(review_id)
        checklist = await self.list_checklist_items(review_id=review_id)
        mappings = await self.list_field_mappings(pack_id=review["pack_id"])
        conflicts = await self.list_conflicts(pack_id=review["pack_id"], status="open")
        updates = {
            "checklist_total_count": len(checklist),
            "checklist_passed_count": len([item for item in checklist if item.get("status") in {"passed", "waived"}]),
            "checklist_failed_count": len([item for item in checklist if item.get("status") == "failed"]),
            "field_mapping_count": len(mappings),
            "open_conflict_count": len(conflicts),
        }
        return await self.db.collection(REVIEW_COLLECTION).update_one({"id": review_id}, updates) or {**review, **updates}

    async def _latest_review(self, pack_id: str, review_id: str | None = None) -> dict[str, Any] | None:
        if review_id:
            return await self._require_review(review_id)
        reviews = await self.list_reviews(pack_id=pack_id)
        return reviews[0] if reviews else None

    async def _require_pack(self, pack_id: str) -> dict[str, Any]:
        pack = await self.db.collection(PACK_COLLECTION).find_one({"id": pack_id})
        if not pack:
            raise ValueError("Airline intelligence data pack not found.")
        return pack

    async def _require_item(self, item_id: str) -> dict[str, Any]:
        item = await self.db.collection(ITEM_COLLECTION).find_one({"id": item_id})
        if not item:
            raise ValueError("Airline intelligence data pack item not found.")
        return item

    async def _require_review(self, review_id: str) -> dict[str, Any]:
        review = await self.db.collection(REVIEW_COLLECTION).find_one({"id": review_id})
        if not review:
            raise ValueError("Airline intelligence data pack review not found.")
        return review

    async def _require_checklist_item(self, checklist_item_id: str) -> dict[str, Any]:
        item = await self.db.collection(CHECKLIST_COLLECTION).find_one({"id": checklist_item_id})
        if not item:
            raise ValueError("Checklist item not found.")
        return item

    async def _require_mapping(self, mapping_id: str) -> dict[str, Any]:
        mapping = await self.db.collection(FIELD_MAPPING_COLLECTION).find_one({"id": mapping_id})
        if not mapping:
            raise ValueError("Field mapping not found.")
        return mapping

    async def _pack_items(self, pack_id: str) -> list[dict[str, Any]]:
        return await self.db.collection(ITEM_COLLECTION).find_many({"pack_id": pack_id})

    def _coverage_summary(self, pack: dict[str, Any], items: list[dict[str, Any]], readiness: dict[str, Any] | None) -> str:
        domains = sorted({enum_value(item.get("target_domain")) for item in items if item.get("target_domain")})
        airline_codes = sorted({item.get("airline_iata_code") for item in items if item.get("airline_iata_code")})
        safety = []
        if pack.get("safe_for_agency_internal_crm") or (readiness and readiness.get("safe_for_agency_internal_crm")):
            safety.append("internal CRM")
        if pack.get("safe_for_agency_display") or (readiness and readiness.get("safe_for_agency_display")):
            safety.append("agency display")
        if pack.get("safe_for_cms_display") or (readiness and readiness.get("safe_for_cms_display")):
            safety.append("CMS website")
        if pack.get("safe_for_client_portal_later") or (readiness and readiness.get("safe_for_client_portal_later")):
            safety.append("client portal later")
        if pack.get("safe_for_offer_builder") or (readiness and readiness.get("safe_for_offer_builder")):
            safety.append("offer builder")
        ready_text = "Promotion-ready metadata has been marked." if readiness and readiness.get("ready_for_promotion") else "Promotion readiness still needs human review."
        return (
            f"{pack.get('name', 'This airline data pack')} covers {len(items)} staged item(s)"
            f" for {', '.join(airline_codes) if airline_codes else 'airline records'}"
            f" across {', '.join(domains) if domains else 'review areas'}."
            f" Safe-use flags: {', '.join(safety) if safety else 'none yet'}. {ready_text}"
        )

    def _readiness_blocked_reason(self, checklist_complete: bool, approved_mapping_count: int, open_conflict_count: int, review: dict[str, Any] | None) -> str:
        if not review:
            return "Create and approve a review before marking the pack promotion-ready."
        if review.get("status") not in {"approved", "promotion_ready"}:
            return "Approve the review before marking promotion readiness."
        if not checklist_complete:
            return "Complete or waive all required checklist items."
        if approved_mapping_count <= 0:
            return "Approve at least one field mapping before promotion readiness."
        if open_conflict_count:
            return "Resolve or acknowledge open duplicate/conflict metadata."
        return "Human review is still required."

    async def _agency_review(self, review: dict[str, Any]) -> dict[str, Any]:
        pack = await self.db.collection(PACK_COLLECTION).find_one({"id": review.get("pack_id")})
        return {
            "id": review.get("id"),
            "pack_id": review.get("pack_id"),
            "pack_name": pack.get("name") if pack else None,
            "status": review.get("status"),
            "promotion_ready": review.get("promotion_ready", False),
            "plain_language_coverage_summary": review.get("plain_language_coverage_summary"),
            "safe_for_agency_internal_crm": review.get("safe_for_agency_internal_crm", False),
            "safe_for_agency_display": review.get("safe_for_agency_display", False),
            "safe_for_cms_display": review.get("safe_for_cms_display", False),
            "safe_for_client_portal_later": review.get("safe_for_client_portal_later", False),
            "safe_for_offer_builder": review.get("safe_for_offer_builder", False),
            "metadata_only": True,
            "automatic_promotion_disabled": True,
        }

    def _agency_pack(self, pack: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": pack.get("id"),
            "name": pack.get("name"),
            "pack_type": pack.get("pack_type"),
            "airline_codes": pack.get("airline_codes", []),
            "target_domains": pack.get("target_domains", []),
            "verification_status": pack.get("verification_status"),
            "human_summary": pack.get("human_summary"),
            "operator_guidance": pack.get("operator_guidance"),
            "safe_for_agency_internal_crm": pack.get("safe_for_agency_internal_crm", False),
            "safe_for_agency_display": pack.get("safe_for_agency_display", False),
            "safe_for_cms_display": pack.get("safe_for_cms_display", False),
            "safe_for_client_portal_later": pack.get("safe_for_client_portal_later", False),
            "safe_for_offer_builder": pack.get("safe_for_offer_builder", False),
            "metadata_only": True,
        }

    def _agency_readiness(self, readiness: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": readiness.get("id"),
            "pack_id": readiness.get("pack_id"),
            "review_id": readiness.get("review_id"),
            "status": readiness.get("status"),
            "ready_for_promotion": readiness.get("ready_for_promotion", False),
            "checklist_complete": readiness.get("checklist_complete", False),
            "approved_mapping_count": readiness.get("approved_mapping_count", 0),
            "open_conflict_count": readiness.get("open_conflict_count", 0),
            "blocked_reason": readiness.get("blocked_reason"),
            "readiness_summary": readiness.get("readiness_summary"),
            "safe_for_agency_internal_crm": readiness.get("safe_for_agency_internal_crm", False),
            "safe_for_agency_display": readiness.get("safe_for_agency_display", False),
            "safe_for_cms_display": readiness.get("safe_for_cms_display", False),
            "safe_for_client_portal_later": readiness.get("safe_for_client_portal_later", False),
            "safe_for_offer_builder": readiness.get("safe_for_offer_builder", False),
            "metadata_only": True,
            "automatic_promotion_disabled": True,
        }

    def _safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "automatic_promotion_disabled": True,
            "scraping_disabled": True,
            "external_api_calls_disabled": True,
            "external_ai_disabled": True,
            "cms_publishing_disabled": True,
            "client_portal_publishing_disabled": True,
            "recommendations_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
        }
