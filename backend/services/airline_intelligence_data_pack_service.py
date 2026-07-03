from __future__ import annotations

import csv
import io
import json
import re
from collections import defaultdict
from datetime import date
from typing import Any

from database import Database
from models import (
    AirlineIntelligenceCoverageSnapshot,
    AirlineIntelligenceCoverageSnapshotCreateRequest,
    AirlineIntelligenceDataPack,
    AirlineIntelligenceDataPackCreateRequest,
    AirlineIntelligenceDataPackImportRun,
    AirlineIntelligenceDataPackImportRunCreateRequest,
    AirlineIntelligenceDataPackInlineCsvRequest,
    AirlineIntelligenceDataPackInlineJsonRequest,
    AirlineIntelligenceDataPackIssueStatus,
    AirlineIntelligenceDataPackItem,
    AirlineIntelligenceDataPackItemCreateRequest,
    AirlineIntelligenceDataPackItemUpdateRequest,
    AirlineIntelligenceDataPackReviewNote,
    AirlineIntelligenceDataPackReviewNoteCreateRequest,
    AirlineIntelligenceDataPackUpdateRequest,
    AirlineIntelligenceDataPackValidationIssue,
    AirlineIntelligenceDataPackValidationIssueAcknowledgeRequest,
    now_utc,
)
from services.offer_decision_export_delivery_service import actor_from_user, enum_value, payload_dict


PHASE_LABEL = "phase_39_0_airline_intelligence_data_pack_foundation"

PACK_COLLECTION = "airline_intelligence_data_packs"
ITEM_COLLECTION = "airline_intelligence_data_pack_items"
ISSUE_COLLECTION = "airline_intelligence_data_pack_validation_issues"
IMPORT_RUN_COLLECTION = "airline_intelligence_data_pack_import_runs"
REVIEW_NOTE_COLLECTION = "airline_intelligence_data_pack_review_notes"
COVERAGE_SNAPSHOT_COLLECTION = "airline_intelligence_coverage_snapshots"

TARGET_DOMAINS = {
    "airline_profile",
    "airline_contacts",
    "fleet",
    "tail_numbers",
    "aircraft_configurations",
    "seatmaps",
    "routes",
    "fare_families",
    "rbd_matrix",
    "fare_rules",
    "ancillaries",
    "interline",
    "distribution",
    "pss_parameters",
    "gds_parameters",
    "exception_rules",
    "brand_assets",
    "special_services_rules",
    "cms_content",
    "client_portal_display_metadata",
}


def slugify(value: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return clean or "airline-data-pack"


def normalize_code(value: Any) -> str | None:
    if value is None:
        return None
    clean = str(value).strip().upper()
    return clean or None


def normalize_codes(values: list[Any] | None) -> list[str]:
    return sorted({code for code in (normalize_code(value) for value in values or []) if code})


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def bool_value(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        clean = value.strip().lower()
        if clean in {"true", "yes", "1", "y"}:
            return True
        if clean in {"false", "no", "0", "n", ""}:
            return False
    return bool(value)


def parse_date_value(value: Any) -> Any:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return str(value)


class AirlineIntelligenceDataPackService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self) -> dict[str, Any]:
        packs = await self.list_packs()
        items = await self.list_pack_items()
        issues = await self.list_validation_issues()
        return {
            "phase": PHASE_LABEL,
            "data_pack_count": len(packs),
            "data_pack_item_count": len(items),
            "validation_issue_count": len(issues),
            "import_run_count": len(await self.list_import_runs()),
            "review_note_count": len(await self.list_review_notes()),
            "coverage_snapshot_count": len(await self.list_coverage_snapshots()),
            "packs_needing_review_count": len([pack for pack in packs if pack.get("verification_status") in {"draft", "needs_review"}]),
            "approved_pack_count": len([pack for pack in packs if pack.get("verification_status") == "approved"]),
            "demo_pack_count": len([pack for pack in packs if pack.get("is_demo_data")]),
            "agency_internal_crm_safe_pack_count": len([pack for pack in packs if pack.get("safe_for_agency_internal_crm")]),
            "agency_display_safe_pack_count": len([pack for pack in packs if pack.get("safe_for_agency_display")]),
            "cms_display_safe_pack_count": len([pack for pack in packs if pack.get("safe_for_cms_display")]),
            "client_portal_safe_pack_count": len([pack for pack in packs if pack.get("safe_for_client_portal_later")]),
            "offer_builder_safe_pack_count": len([pack for pack in packs if pack.get("safe_for_offer_builder")]),
            "data_packs_enabled": True,
            "data_pack_items_enabled": True,
            "data_pack_validation_enabled": True,
            "data_pack_dry_runs_enabled": True,
            "data_pack_review_notes_enabled": True,
            "coverage_snapshots_enabled": True,
            "platform_data_pack_ui_enabled": True,
            "agency_coverage_ui_enabled": True,
            "agency_read_only_consumption_enabled": True,
            "crm_alignment_metadata_enabled": True,
            "cms_alignment_metadata_enabled": True,
            "client_portal_alignment_metadata_enabled": True,
            "offer_builder_alignment_metadata_enabled": True,
            "metadata_only_staging_enabled": True,
            **self._safety_flags(),
            "diagnostic": "Phase 39.0 creates metadata-only airline intelligence data pack staging, validation, review, and coverage records. It does not scrape, call external APIs, use external AI, auto-promote records into operational airline tables, publish CMS/client portal content, recommend airlines, book, mutate PNRs, ticket, issue EMDs, charge, invoice, settle, send messages, or execute providers.",
        }

    async def create_pack(self, payload: AirlineIntelligenceDataPackCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        slug = slugify(data.get("slug") or data["name"])
        if await self.db.collection(PACK_COLLECTION).find_one({"slug": slug}):
            raise ValueError("A data pack with this friendly URL slug already exists.")
        pack = AirlineIntelligenceDataPack(
            **{
                **data,
                "slug": slug,
                "airline_codes": normalize_codes(data.get("airline_codes")),
                "target_domains": [enum_value(value) for value in data.get("target_domains", [])],
                "created_by": data.get("created_by") or actor_from_user(user),
            }
        )
        stored = await self.db.collection(PACK_COLLECTION).insert_one(pack.model_dump(mode="json"))
        return {"pack": stored, **self._safety_flags()}

    async def update_pack(self, pack_id: str, payload: AirlineIntelligenceDataPackUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        pack = await self._require_pack(pack_id)
        data = payload_dict(payload)
        if not data:
            raise ValueError("No data pack changes were provided.")
        updates: dict[str, Any] = {}
        for key, value in data.items():
            if key == "airline_codes":
                updates[key] = normalize_codes(value)
            elif key == "target_domains":
                updates[key] = [enum_value(item) for item in value or []]
            elif key == "slug":
                updates[key] = slugify(value or pack.get("name") or pack_id)
            else:
                updates[key] = value
        if updates.get("slug") and updates["slug"] != pack.get("slug"):
            existing = await self.db.collection(PACK_COLLECTION).find_one({"slug": updates["slug"]})
            if existing and existing.get("id") != pack_id:
                raise ValueError("A data pack with this friendly URL slug already exists.")
        if updates.get("verification_status") in {"reviewed", "approved", "rejected", "retired"}:
            updates["reviewed_by"] = actor_from_user(user) or updates.get("reviewed_by") or pack.get("reviewed_by")
            updates["reviewed_at"] = now_utc()
        updated = await self.db.collection(PACK_COLLECTION).update_one({"id": pack_id}, updates)
        return {"pack": updated or pack, **self._safety_flags()}

    async def list_packs(
        self,
        *,
        verification_status: str | None = None,
        pack_type: str | None = None,
        safe_for_agency_display: bool | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if verification_status:
            filters["verification_status"] = verification_status
        if pack_type:
            filters["pack_type"] = pack_type
        if safe_for_agency_display is not None:
            filters["safe_for_agency_display"] = safe_for_agency_display
        items = await self.db.collection(PACK_COLLECTION).find_many(filters or None)
        items.sort(key=lambda item: (item.get("verification_status", ""), item.get("name", "")))
        return items

    async def get_pack(self, pack_id: str, *, include_items: bool = True, agency_view: bool = False) -> dict[str, Any] | None:
        pack = await self.db.collection(PACK_COLLECTION).find_one({"id": pack_id})
        if not pack:
            return None
        items = await self.list_pack_items(pack_id=pack_id) if include_items else []
        return {
            "pack": self._agency_pack(pack) if agency_view else pack,
            "items": [self._agency_item(item) for item in items] if agency_view else items,
            "validation_issues": [] if agency_view else await self.list_validation_issues(pack_id=pack_id),
            "review_notes": [] if agency_view else await self.list_review_notes(pack_id=pack_id),
            **self._safety_flags(),
        }

    async def add_pack_item(self, pack_id: str, payload: AirlineIntelligenceDataPackItemCreateRequest | dict[str, Any]) -> dict[str, Any]:
        pack = await self._require_pack(pack_id)
        data = self._normalize_item_data(payload_dict(payload), pack)
        item = AirlineIntelligenceDataPackItem(pack_id=pack_id, **data)
        stored = await self.db.collection(ITEM_COLLECTION).insert_one(item.model_dump(mode="json"))
        await self._sync_pack_lists(pack_id)
        return {"item": stored, **self._safety_flags()}

    async def update_pack_item(self, item_id: str, payload: AirlineIntelligenceDataPackItemUpdateRequest | dict[str, Any]) -> dict[str, Any]:
        item = await self._require_item(item_id)
        pack = await self._require_pack(item["pack_id"])
        data = self._normalize_item_data({**item, **payload_dict(payload)}, pack)
        updated = await self.db.collection(ITEM_COLLECTION).update_one({"id": item_id}, data)
        await self._sync_pack_lists(item["pack_id"])
        return {"item": updated or item, **self._safety_flags()}

    async def list_pack_items(
        self,
        *,
        pack_id: str | None = None,
        target_domain: str | None = None,
        airline_iata_code: str | None = None,
        safe_for_agency_display: bool | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if pack_id:
            filters["pack_id"] = pack_id
        if target_domain:
            filters["target_domain"] = target_domain
        if airline_iata_code:
            filters["airline_iata_code"] = normalize_code(airline_iata_code)
        if safe_for_agency_display is not None:
            filters["safe_for_agency_display"] = safe_for_agency_display
        items = await self.db.collection(ITEM_COLLECTION).find_many(filters or None)
        items.sort(key=lambda item: (item.get("airline_iata_code") or "", item.get("target_domain") or "", item.get("display_name") or ""))
        return items

    async def validate_pack(self, pack_id: str, user: dict | None = None) -> dict[str, Any]:
        pack = await self._require_pack(pack_id)
        items = await self.list_pack_items(pack_id=pack_id)
        issues: list[dict[str, Any]] = []
        for issue in self._validate_pack_record(pack):
            issues.append(await self._create_issue(pack_id, None, issue))
        for item in items:
            item_issues = self._validate_item_record(pack, item)
            for issue in item_issues:
                issues.append(await self._create_issue(pack_id, item["id"], issue))
            warning_count = len([issue for issue in item_issues if issue["severity"] == "warning"])
            error_count = len([issue for issue in item_issues if issue["severity"] == "error"])
            validation_status = "invalid" if error_count else "warning" if warning_count else "valid"
            await self.db.collection(ITEM_COLLECTION).update_one(
                {"id": item["id"]},
                {
                    "validation_status": validation_status,
                    "issue_count": error_count,
                    "warning_count": warning_count,
                },
            )
        run = await self.create_import_run(
            pack_id,
            {
                "run_type": "validation",
                "source_format": "manual",
                "created_by": actor_from_user(user),
                "summary": f"Checked {len(items)} staged data pack item(s).",
            },
            total_items=len(items),
            issues=issues,
        )
        return {
            "pack": await self._require_pack(pack_id),
            "issues": issues,
            "import_run": run["import_run"],
            "plain_language_summary": self._validation_summary(issues),
            **self._safety_flags(),
        }

    async def create_import_run(
        self,
        pack_id: str,
        payload: AirlineIntelligenceDataPackImportRunCreateRequest | dict[str, Any],
        *,
        total_items: int = 0,
        issues: list[dict[str, Any]] | None = None,
        inserted_proposals: int = 0,
        updated_proposals: int = 0,
        skipped_items: int = 0,
        status: str = "completed",
    ) -> dict[str, Any]:
        await self._require_pack(pack_id)
        data = payload_dict(payload)
        issues = issues or []
        warning_items = len({issue.get("item_id") for issue in issues if issue.get("severity") == "warning" and issue.get("item_id")})
        invalid_items = len({issue.get("item_id") for issue in issues if issue.get("severity") == "error" and issue.get("item_id")})
        valid_items = max(total_items - warning_items - invalid_items - skipped_items, 0)
        run = AirlineIntelligenceDataPackImportRun(
            pack_id=pack_id,
            run_type=data.get("run_type") or "validation",
            status=status,
            source_format=data.get("source_format") or "manual",
            total_items=total_items,
            valid_items=valid_items,
            warning_items=warning_items,
            invalid_items=invalid_items,
            skipped_items=skipped_items,
            inserted_proposals=inserted_proposals,
            updated_proposals=updated_proposals,
            started_at=now_utc(),
            completed_at=now_utc(),
            created_by=data.get("created_by"),
            summary=data.get("summary"),
            warnings=data.get("warnings") or [],
            errors=data.get("errors") or [],
        )
        stored = await self.db.collection(IMPORT_RUN_COLLECTION).insert_one(run.model_dump(mode="json"))
        return {"import_run": stored, **self._safety_flags()}

    async def create_dry_run_from_inline_json(self, pack_id: str, payload: AirlineIntelligenceDataPackInlineJsonRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        await self._require_pack(pack_id)
        data = payload_dict(payload)
        try:
            parsed = json.loads(data.get("inline_json") or "[]")
            records = parsed.get("items") if isinstance(parsed, dict) else parsed
            if isinstance(records, dict):
                records = [records]
            if not isinstance(records, list):
                raise ValueError("JSON must be a list of items or an object with an items list.")
        except Exception as exc:
            run = await self.create_import_run(pack_id, {"run_type": "dry_run", "source_format": "json", "created_by": actor_from_user(user), "summary": "JSON dry run failed.", "errors": [str(exc)]}, status="failed")
            return {**run, "items": [], "issues": [], "plain_language_summary": "The JSON could not be read. Check that it is valid JSON and try again."}
        staged_items = [await self._stage_import_item(pack_id, record, "json") for record in records]
        validation = await self.validate_pack(pack_id, user)
        run = await self.create_import_run(
            pack_id,
            {"run_type": "dry_run", "source_format": "json", "created_by": data.get("created_by") or actor_from_user(user), "summary": f"JSON dry run staged {len(staged_items)} item(s) for review."},
            total_items=len(staged_items),
            issues=validation["issues"],
            inserted_proposals=len([item for item in staged_items if item.get("proposed_action") == "insert"]),
            updated_proposals=len([item for item in staged_items if item.get("proposed_action") == "update"]),
        )
        return {**run, "items": staged_items, "issues": validation["issues"], "plain_language_summary": "JSON dry run completed. Items were staged for review only."}

    async def create_dry_run_from_inline_csv(self, pack_id: str, payload: AirlineIntelligenceDataPackInlineCsvRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        await self._require_pack(pack_id)
        data = payload_dict(payload)
        try:
            reader = csv.DictReader(io.StringIO(data.get("inline_csv") or ""))
            records = [dict(row) for row in reader]
            if not reader.fieldnames:
                raise ValueError("CSV must include a header row.")
        except Exception as exc:
            run = await self.create_import_run(pack_id, {"run_type": "dry_run", "source_format": "csv", "created_by": actor_from_user(user), "summary": "CSV dry run failed.", "errors": [str(exc)]}, status="failed")
            return {**run, "items": [], "issues": [], "plain_language_summary": "The CSV could not be read. Check the header row and try again."}
        staged_items = [await self._stage_import_item(pack_id, record, "csv") for record in records]
        validation = await self.validate_pack(pack_id, user)
        run = await self.create_import_run(
            pack_id,
            {"run_type": "dry_run", "source_format": "csv", "created_by": data.get("created_by") or actor_from_user(user), "summary": f"CSV dry run staged {len(staged_items)} item(s) for review."},
            total_items=len(staged_items),
            issues=validation["issues"],
            inserted_proposals=len([item for item in staged_items if item.get("proposed_action") == "insert"]),
            updated_proposals=len([item for item in staged_items if item.get("proposed_action") == "update"]),
        )
        return {**run, "items": staged_items, "issues": validation["issues"], "plain_language_summary": "CSV dry run completed. Items were staged for review only."}

    async def list_import_runs(self, *, pack_id: str | None = None) -> list[dict[str, Any]]:
        filters = {"pack_id": pack_id} if pack_id else None
        items = await self.db.collection(IMPORT_RUN_COLLECTION).find_many(filters)
        items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return items

    async def list_validation_issues(
        self,
        *,
        pack_id: str | None = None,
        item_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if pack_id:
            filters["pack_id"] = pack_id
        if item_id:
            filters["item_id"] = item_id
        if status:
            filters["status"] = status
        if severity:
            filters["severity"] = severity
        items = await self.db.collection(ISSUE_COLLECTION).find_many(filters or None)
        items.sort(key=lambda item: (item.get("status", ""), item.get("severity", ""), item.get("created_at", "")))
        return items

    async def acknowledge_validation_issue(self, issue_id: str, payload: AirlineIntelligenceDataPackValidationIssueAcknowledgeRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        issue = await self.db.collection(ISSUE_COLLECTION).find_one({"id": issue_id})
        if not issue:
            raise ValueError("Validation issue not found.")
        data = payload_dict(payload)
        status_value = enum_value(data.get("status") or AirlineIntelligenceDataPackIssueStatus.ACKNOWLEDGED)
        updated = await self.db.collection(ISSUE_COLLECTION).update_one(
            {"id": issue_id},
            {
                "status": status_value,
                "resolved_by": data.get("resolved_by") or actor_from_user(user),
                "resolved_at": now_utc() if status_value in {"resolved", "ignored", "acknowledged"} else None,
            },
        )
        return {"issue": updated or issue, **self._safety_flags()}

    async def create_review_note(self, pack_id: str, payload: AirlineIntelligenceDataPackReviewNoteCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        await self._require_pack(pack_id)
        data = payload_dict(payload)
        if data.get("item_id"):
            await self._require_item(data["item_id"])
        note = AirlineIntelligenceDataPackReviewNote(
            pack_id=pack_id,
            item_id=data.get("item_id"),
            note_type=data.get("note_type") or "review",
            note=data["note"],
            created_by=data.get("created_by") or actor_from_user(user),
        )
        stored = await self.db.collection(REVIEW_NOTE_COLLECTION).insert_one(note.model_dump(mode="json"))
        return {"review_note": stored, **self._safety_flags()}

    async def list_review_notes(self, *, pack_id: str | None = None, item_id: str | None = None, note_type: str | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if pack_id:
            filters["pack_id"] = pack_id
        if item_id:
            filters["item_id"] = item_id
        if note_type:
            filters["note_type"] = note_type
        items = await self.db.collection(REVIEW_NOTE_COLLECTION).find_many(filters or None)
        items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return items

    async def create_coverage_snapshot(self, payload: AirlineIntelligenceCoverageSnapshotCreateRequest | dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        packs = await self.list_packs()
        items = await self.list_pack_items()
        coverage = self._coverage_counts(items)
        airline_profiles = await self.db.collection("airline_profiles").find_many()
        snapshot = AirlineIntelligenceCoverageSnapshot(
            snapshot_label=data.get("snapshot_label") or f"Airline data coverage {now_utc().date().isoformat()}",
            airline_count=max(len({item.get("airline_iata_code") for item in items if item.get("airline_iata_code")}), len(airline_profiles)),
            airlines_with_profiles=coverage["airline_profile"],
            airlines_with_contacts=coverage["airline_contacts"],
            airlines_with_fleet=coverage["fleet"],
            airlines_with_routes=coverage["routes"],
            airlines_with_fare_families=coverage["fare_families"],
            airlines_with_rbd_matrix=coverage["rbd_matrix"],
            airlines_with_fare_rules=coverage["fare_rules"],
            airlines_with_ancillaries=coverage["ancillaries"],
            airlines_with_interline=coverage["interline"],
            airlines_with_distribution=coverage["distribution"],
            airlines_with_pss_parameters=coverage["pss_parameters"],
            airlines_with_gds_parameters=coverage["gds_parameters"],
            airlines_with_exception_rules=coverage["exception_rules"],
            airlines_with_brand_assets=coverage["brand_assets"],
            airlines_with_special_services_rules=coverage["special_services_rules"],
            airlines_safe_for_agency_internal_crm=len({code for code in self._pack_codes(packs, items, "safe_for_agency_internal_crm") if code}),
            airlines_safe_for_agency_display=len({code for code in self._pack_codes(packs, items, "safe_for_agency_display") if code}),
            airlines_safe_for_cms_display=len({code for code in self._pack_codes(packs, items, "safe_for_cms_display") if code}),
            airlines_safe_for_client_portal_later=len({code for code in self._pack_codes(packs, items, "safe_for_client_portal_later") if code}),
            airlines_safe_for_offer_builder=len({code for code in self._pack_codes(packs, items, "safe_for_offer_builder") if code}),
            diagnostic="Metadata-only coverage snapshot for platform and agency review. No airline operational records were changed.",
        )
        stored = await self.db.collection(COVERAGE_SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))
        return {"coverage_snapshot": stored, **self._safety_flags()}

    async def list_coverage_snapshots(self) -> list[dict[str, Any]]:
        items = await self.db.collection(COVERAGE_SNAPSHOT_COLLECTION).find_many()
        items.sort(key=lambda item: item.get("generated_at", item.get("created_at", "")), reverse=True)
        return items

    async def agency_summary(self) -> dict[str, Any]:
        summary = await self.summary()
        latest = (await self.list_coverage_snapshots())[:1]
        return {
            **summary,
            "latest_coverage_snapshot": latest[0] if latest else None,
            "read_only": True,
            "plain_language_overview": "Airline data packs show which reviewed airline facts are available for agency work. They are guidance metadata only and do not create bookings, tickets, prices, or public content.",
        }

    async def agency_packs(self) -> list[dict[str, Any]]:
        packs = await self.list_packs()
        return [self._agency_pack(pack) for pack in packs]

    async def agency_items(self, pack_id: str) -> list[dict[str, Any]]:
        return [self._agency_item(item) for item in await self.list_pack_items(pack_id=pack_id)]

    def _normalize_item_data(self, data: dict[str, Any], pack: dict[str, Any]) -> dict[str, Any]:
        code = normalize_code(data.get("airline_iata_code")) or (pack.get("airline_codes") or [None])[0]
        domain = enum_value(data.get("target_domain"))
        if domain not in TARGET_DOMAINS:
            domain = None
        normalized_payload = data.get("normalized_payload") or self._normalize_payload(data.get("payload") or {}, code, domain)
        return {
            "airline_id": data.get("airline_id"),
            "airline_iata_code": code,
            "target_domain": domain,
            "target_record_key": data.get("target_record_key"),
            "display_name": data.get("display_name") or f"{code or 'Airline'} staged data",
            "plain_language_summary": data.get("plain_language_summary"),
            "proposed_action": enum_value(data.get("proposed_action") or "review_only"),
            "payload": data.get("payload") or {},
            "normalized_payload": normalized_payload,
            "validation_status": enum_value(data.get("validation_status") or "not_checked"),
            "verification_status": enum_value(data.get("verification_status") or "unverified"),
            "confidence_score": safe_float(data.get("confidence_score"), 0.0),
            "source_reference": data.get("source_reference") or pack.get("source_reference"),
            "effective_from": parse_date_value(data.get("effective_from") or pack.get("effective_from")),
            "effective_to": parse_date_value(data.get("effective_to") or pack.get("effective_to")),
            "is_demo_data": bool_value(data.get("is_demo_data"), pack.get("is_demo_data", False)),
            "is_operationally_verified": bool_value(data.get("is_operationally_verified"), pack.get("is_operationally_verified", False)),
            "safe_for_agency_internal_crm": bool_value(data.get("safe_for_agency_internal_crm"), pack.get("safe_for_agency_internal_crm", False)),
            "safe_for_agency_display": bool_value(data.get("safe_for_agency_display"), pack.get("safe_for_agency_display", False)),
            "safe_for_cms_display": bool_value(data.get("safe_for_cms_display"), pack.get("safe_for_cms_display", False)),
            "safe_for_client_portal_later": bool_value(data.get("safe_for_client_portal_later"), pack.get("safe_for_client_portal_later", False)),
            "safe_for_offer_builder": bool_value(data.get("safe_for_offer_builder"), pack.get("safe_for_offer_builder", False)),
        }

    def _normalize_payload(self, payload: dict[str, Any], airline_code: str | None, target_domain: str | None) -> dict[str, Any]:
        return {
            "airline_iata_code": airline_code,
            "target_domain": target_domain,
            "display_name": payload.get("display_name") or payload.get("name") or payload.get("title"),
            "summary": payload.get("plain_language_summary") or payload.get("summary") or payload.get("description"),
        }

    async def _stage_import_item(self, pack_id: str, record: dict[str, Any], source_format: str) -> dict[str, Any]:
        pack = await self._require_pack(pack_id)
        payload = {key: value for key, value in record.items() if key not in {"payload", "normalized_payload"}}
        raw_payload = record.get("payload") if isinstance(record.get("payload"), dict) else {**record}
        data = self._normalize_item_data(
            {
                "airline_iata_code": record.get("airline_iata_code") or record.get("airline_code") or record.get("iata"),
                "target_domain": record.get("target_domain") or record.get("domain"),
                "display_name": record.get("display_name") or record.get("name") or record.get("title") or "Imported airline data item",
                "plain_language_summary": record.get("plain_language_summary") or record.get("summary") or record.get("description"),
                "proposed_action": record.get("proposed_action") or "review_only",
                "payload": raw_payload,
                "source_reference": record.get("source_reference") or f"Inline {source_format.upper()} dry run",
                "is_demo_data": record.get("is_demo_data", pack.get("is_demo_data", False)),
                "is_operationally_verified": record.get("is_operationally_verified", False),
                "safe_for_agency_internal_crm": record.get("safe_for_agency_internal_crm", False),
                "safe_for_agency_display": record.get("safe_for_agency_display", False),
                "safe_for_cms_display": record.get("safe_for_cms_display", False),
                "safe_for_client_portal_later": record.get("safe_for_client_portal_later", False),
                "safe_for_offer_builder": record.get("safe_for_offer_builder", False),
                "confidence_score": record.get("confidence_score", 0.0),
                "normalized_payload": payload,
            },
            pack,
        )
        item = AirlineIntelligenceDataPackItem(pack_id=pack_id, **data)
        stored = await self.db.collection(ITEM_COLLECTION).insert_one(item.model_dump(mode="json"))
        await self._sync_pack_lists(pack_id)
        return stored

    def _validate_pack_record(self, pack: dict[str, Any]) -> list[dict[str, str]]:
        issues = []
        if not pack.get("source_reference"):
            issues.append(self._issue("warning", "missing_pack_source_reference", "This pack is missing a source reference.", "Add a clear source label before approving the pack.", "source_reference"))
        if pack.get("is_demo_data") and pack.get("is_operationally_verified"):
            issues.append(self._issue("error", "demo_pack_marked_verified", "Demo/sample data cannot be marked operationally verified.", "Turn off operationally verified or mark the pack as real reviewed data.", "is_operationally_verified"))
        if pack.get("effective_from") and pack.get("effective_to") and str(pack["effective_to"]) < str(pack["effective_from"]):
            issues.append(self._issue("error", "pack_effective_dates_reversed", "The pack end date is before the start date.", "Correct the effective date range.", "effective_to"))
        if self._has_safe_display_flags(pack) and not pack.get("is_operationally_verified"):
            issues.append(self._issue("warning", "safe_display_without_verification", "This pack is marked safe for display but is not operationally verified.", "Review the source before using this pack in agency-facing workflows.", "safe_for_agency_display"))
        return issues

    def _validate_item_record(self, pack: dict[str, Any], item: dict[str, Any]) -> list[dict[str, str]]:
        issues = []
        code = normalize_code(item.get("airline_iata_code"))
        if not code:
            issues.append(self._issue("error", "missing_airline_code", "This item is missing an airline code.", "Add a two-character airline code such as LH or BA.", "airline_iata_code"))
        elif len(code) != 2:
            issues.append(self._issue("error", "invalid_airline_code_length", "The airline code should be two characters.", "Use the airline IATA-style code, for example LH.", "airline_iata_code"))
        domain = enum_value(item.get("target_domain"))
        if not domain:
            issues.append(self._issue("error", "missing_target_domain", "This item is missing the type of airline data it belongs to.", "Choose a friendly data area such as routes, fleet, fare families, or special services.", "target_domain"))
        elif domain not in TARGET_DOMAINS:
            issues.append(self._issue("error", "unknown_target_domain", "This item uses a data area AgencyOS does not recognize yet.", "Choose one of the supported airline data areas.", "target_domain"))
        if not item.get("source_reference") and not pack.get("source_reference"):
            issues.append(self._issue("warning", "missing_source_reference", "This item is missing a source reference.", "Add where the information came from before approving it.", "source_reference"))
        if not item.get("plain_language_summary"):
            issues.append(self._issue("warning", "missing_display_summary", "This item needs a plain-language summary.", "Add a short summary that a travel agency operator can understand.", "plain_language_summary"))
        if not item.get("payload"):
            issues.append(self._issue("warning", "empty_payload", "This item has no staged detail payload.", "Add the supporting detail before relying on this item.", "payload"))
        if item.get("is_demo_data") and item.get("is_operationally_verified"):
            issues.append(self._issue("error", "demo_item_marked_verified", "Demo/sample item data cannot be marked operationally verified.", "Turn off operationally verified or replace this item with reviewed real data.", "is_operationally_verified"))
        if item.get("effective_from") and item.get("effective_to") and str(item["effective_to"]) < str(item["effective_from"]):
            issues.append(self._issue("error", "item_effective_dates_reversed", "The item end date is before the start date.", "Correct the item effective date range.", "effective_to"))
        if self._has_safe_display_flags(item) and (item.get("is_demo_data") or not item.get("is_operationally_verified")):
            issues.append(self._issue("warning", "unsafe_display_flag_conflict", "This item is marked safe for display before operational verification is complete.", "Use internal-only review until a platform owner verifies the source.", "safe_for_agency_display"))
        return issues

    def _issue(self, severity: str, code: str, message: str, resolution: str, field_path: str) -> dict[str, str]:
        return {
            "severity": severity,
            "issue_code": code,
            "technical_message": code,
            "user_friendly_message": message,
            "suggested_resolution": resolution,
            "field_path": field_path,
        }

    async def _create_issue(self, pack_id: str, item_id: str | None, issue: dict[str, str]) -> dict[str, Any]:
        record = AirlineIntelligenceDataPackValidationIssue(pack_id=pack_id, item_id=item_id, **issue)
        return await self.db.collection(ISSUE_COLLECTION).insert_one(record.model_dump(mode="json"))

    def _validation_summary(self, issues: list[dict[str, Any]]) -> str:
        errors = len([issue for issue in issues if issue.get("severity") == "error"])
        warnings = len([issue for issue in issues if issue.get("severity") == "warning"])
        if errors:
            return f"Needs verification: {errors} item(s) have required fixes and {warnings} warning(s) need review."
        if warnings:
            return f"Ready to review: no blocking errors, with {warnings} warning(s) to check."
        return "Ready to review: no validation issues found."

    def _has_safe_display_flags(self, record: dict[str, Any]) -> bool:
        return any(record.get(key) for key in ["safe_for_agency_display", "safe_for_cms_display", "safe_for_client_portal_later", "safe_for_offer_builder"])

    async def _sync_pack_lists(self, pack_id: str) -> None:
        items = await self.list_pack_items(pack_id=pack_id)
        domains = sorted({item.get("target_domain") for item in items if item.get("target_domain")})
        codes = sorted({item.get("airline_iata_code") for item in items if item.get("airline_iata_code")})
        await self.db.collection(PACK_COLLECTION).update_one({"id": pack_id}, {"target_domains": domains, "airline_codes": codes})

    def _coverage_counts(self, items: list[dict[str, Any]]) -> dict[str, int]:
        by_domain: dict[str, set[str]] = defaultdict(set)
        for item in items:
            domain = item.get("target_domain")
            code = item.get("airline_iata_code")
            if domain and code:
                by_domain[domain].add(code)
        return {domain: len(by_domain[domain]) for domain in TARGET_DOMAINS}

    def _pack_codes(self, packs: list[dict[str, Any]], items: list[dict[str, Any]], flag: str) -> set[str]:
        codes: set[str] = set()
        for pack in packs:
            if pack.get(flag):
                codes.update(pack.get("airline_codes") or [])
        for item in items:
            if item.get(flag) and item.get("airline_iata_code"):
                codes.add(item["airline_iata_code"])
        return codes

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

    def _agency_pack(self, pack: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": pack.get("id"),
            "name": pack.get("name"),
            "description": pack.get("description"),
            "pack_type": pack.get("pack_type"),
            "airline_codes": pack.get("airline_codes") or [],
            "verification_status": pack.get("verification_status"),
            "confidence_score": pack.get("confidence_score"),
            "is_demo_data": pack.get("is_demo_data"),
            "is_operationally_verified": pack.get("is_operationally_verified"),
            "safe_for_agency_internal_crm": pack.get("safe_for_agency_internal_crm"),
            "safe_for_agency_display": pack.get("safe_for_agency_display"),
            "safe_for_cms_display": pack.get("safe_for_cms_display"),
            "safe_for_client_portal_later": pack.get("safe_for_client_portal_later"),
            "safe_for_offer_builder": pack.get("safe_for_offer_builder"),
            "human_summary": pack.get("human_summary"),
            "operator_guidance": pack.get("operator_guidance"),
            "warnings": pack.get("warnings") or [],
            "friendly_status": self._friendly_status(pack),
        }

    def _agency_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item.get("id"),
            "pack_id": item.get("pack_id"),
            "airline_iata_code": item.get("airline_iata_code"),
            "target_domain": item.get("target_domain"),
            "display_name": item.get("display_name"),
            "plain_language_summary": item.get("plain_language_summary"),
            "validation_status": item.get("validation_status"),
            "verification_status": item.get("verification_status"),
            "confidence_score": item.get("confidence_score"),
            "issue_count": item.get("issue_count"),
            "warning_count": item.get("warning_count"),
            "source_reference": item.get("source_reference"),
            "is_demo_data": item.get("is_demo_data"),
            "is_operationally_verified": item.get("is_operationally_verified"),
            "safe_for_agency_internal_crm": item.get("safe_for_agency_internal_crm"),
            "safe_for_agency_display": item.get("safe_for_agency_display"),
            "safe_for_cms_display": item.get("safe_for_cms_display"),
            "safe_for_client_portal_later": item.get("safe_for_client_portal_later"),
            "safe_for_offer_builder": item.get("safe_for_offer_builder"),
            "warnings": self._agency_item_warnings(item),
        }

    def _friendly_status(self, pack: dict[str, Any]) -> str:
        if pack.get("is_demo_data"):
            return "Demo/sample data"
        if pack.get("verification_status") in {"draft", "needs_review"}:
            return "Needs verification"
        if pack.get("verification_status") == "approved" and pack.get("is_operationally_verified"):
            return "Ready to review"
        if pack.get("verification_status") == "rejected":
            return "Not operationally verified"
        return "Ready to review"

    def _agency_item_warnings(self, item: dict[str, Any]) -> list[str]:
        warnings = []
        if item.get("is_demo_data"):
            warnings.append("Demo/sample data")
        if not item.get("is_operationally_verified"):
            warnings.append("Not operationally verified")
        if item.get("validation_status") in {"warning", "invalid"}:
            warnings.append("Needs platform verification")
        return warnings

    def _safety_flags(self) -> dict[str, bool]:
        return {
            "automatic_promotion_disabled": True,
            "scraping_disabled": True,
            "external_ai_disabled": True,
            "external_api_calls_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "public_client_portal_disabled": True,
            "public_cms_publishing_disabled": True,
            "automatic_sending_disabled": True,
        }
