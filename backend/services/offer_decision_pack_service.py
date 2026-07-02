from __future__ import annotations

import re
from typing import Any

from database import Database
from models import (
    OfferDecisionPack,
    OfferDecisionPackAdvisorAttachmentRequest,
    OfferDecisionPackBuildRequest,
    OfferDecisionPackEvidence,
    OfferDecisionPackEvidenceType,
    OfferDecisionPackOption,
    OfferDecisionPackReviewNote,
    OfferDecisionPackReviewNoteStatus,
    OfferDecisionPackReviewNoteUpdate,
    OfferDecisionPackSnapshot,
    OfferDecisionPackSnapshotCreate,
    OfferDecisionPackStatus,
    OfferDecisionPackWarning,
    OfferDecisionPackWarningSource,
    PolicyComparisonWarningLevel,
)


PHASE_LABEL = "phase_37_3_offer_builder_advisor_consumption_decision_pack_foundation"

PACK_COLLECTION = "offer_decision_packs"
OPTION_COLLECTION = "offer_decision_pack_options"
EVIDENCE_COLLECTION = "offer_decision_pack_evidence"
WARNING_COLLECTION = "offer_decision_pack_warnings"
REVIEW_NOTE_COLLECTION = "offer_decision_pack_review_notes"
SNAPSHOT_COLLECTION = "offer_decision_pack_snapshots"

ADVISOR_CONTEXT_COLLECTION = "offer_policy_advisor_contexts"
ADVISOR_ROW_COLLECTION = "offer_policy_advisor_airline_rows"
ADVISOR_WARNING_COLLECTION = "offer_policy_advisor_warnings"
ADVISOR_SNAPSHOT_COLLECTION = "offer_policy_advisor_saved_snapshots"


WARNING_ORDER = {
    PolicyComparisonWarningLevel.NONE.value: 0,
    PolicyComparisonWarningLevel.INFO.value: 1,
    PolicyComparisonWarningLevel.ADVISORY.value: 2,
    PolicyComparisonWarningLevel.WARNING.value: 3,
    PolicyComparisonWarningLevel.BLOCKER.value: 4,
}


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_unset=True)
    return dict(payload or {})


def enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def compact_unique(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def normalize_airline_code(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    return text or None


def normalize_taxonomy_code(value: Any) -> str | None:
    text = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return text or None


def warning_level(value: Any) -> str:
    value = enum_value(value) or PolicyComparisonWarningLevel.NONE.value
    return value if value in WARNING_ORDER else PolicyComparisonWarningLevel.NONE.value


def worst_warning_level(values: list[Any]) -> str:
    if not values:
        return PolicyComparisonWarningLevel.NONE.value
    return max((warning_level(value) for value in values), key=lambda item: WARNING_ORDER.get(item, 0))


class OfferDecisionPackService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "decision_pack_count": len(await self.list_packs(agency_id=agency_id)),
            "option_evidence_count": len(await self.list_evidence(agency_id=agency_id)),
            "warning_count": len(await self.list_warnings(agency_id=agency_id)),
            "review_note_count": len(await self.list_review_notes(agency_id=agency_id)),
            "saved_snapshot_count": len(await self.list_snapshots(agency_id=agency_id)),
            "decision_packs_enabled": True,
            "advisor_snapshot_consumption_enabled": True,
            "offer_builder_consumption_enabled": True,
            "human_review_required_enabled": True,
            **self._safety_flags(),
            "diagnostic": "Offer decision packs consume advisor evidence as metadata-only human review context and never rank, price, book, issue, charge, invoice, settle, or execute providers.",
        }

    async def list_packs(
        self,
        *,
        agency_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if offer_workspace_id:
            filters["offer_workspace_id"] = offer_workspace_id
        items = await self.db.collection(PACK_COLLECTION).find_many(filters or None)
        return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def get_pack(self, pack_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        filters = {"id": pack_id}
        if agency_id:
            filters["agency_id"] = agency_id
        return await self.db.collection(PACK_COLLECTION).find_one(filters)

    async def get_pack_detail(self, pack_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        pack = await self.get_pack(pack_id, agency_id)
        if not pack:
            return None
        return {
            "pack": pack,
            "options": await self.list_options(agency_id=agency_id, decision_pack_id=pack_id),
            "evidence": await self.list_evidence(agency_id=agency_id, decision_pack_id=pack_id),
            "warnings": await self.list_warnings(agency_id=agency_id, decision_pack_id=pack_id),
            "review_notes": await self.list_review_notes(agency_id=agency_id, decision_pack_id=pack_id),
            "snapshots": await self.list_snapshots(agency_id=agency_id, decision_pack_id=pack_id),
            **self._safety_flags(),
        }

    async def build_pack(self, agency_id: str, payload: OfferDecisionPackBuildRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        workspace_id = data["offer_workspace_id"]
        workspace = await self.db.collection("offer_workspaces").find_one({"agency_id": agency_id, "id": workspace_id})
        if not workspace:
            raise ValueError("Offer workspace not found.")

        options = await self._workspace_options(agency_id, workspace_id)
        segments = await self._workspace_segments(agency_id, options)
        pricing_lines = await self._workspace_pricing_lines(agency_id, options)
        contexts = await self._advisor_contexts(agency_id, workspace_id, data.get("advisor_context_ids") or [])
        snapshots = await self._advisor_snapshots(agency_id, workspace_id, data.get("advisor_saved_snapshot_ids") or [])
        advisor_rows = await self._advisor_rows(agency_id, workspace_id, contexts)
        advisor_warnings = await self._advisor_warnings(agency_id, workspace_id, contexts)

        pack = OfferDecisionPack(
            agency_id=agency_id,
            offer_workspace_id=workspace_id,
            pack_name=data.get("pack_name") or f"Decision pack for {workspace.get('title') or workspace_id}",
            pack_status=OfferDecisionPackStatus.REBUILT if data.get("rebuild_from_pack_id") else OfferDecisionPackStatus.BUILT,
            rebuilt_from_pack_id=data.get("rebuild_from_pack_id"),
            offer_policy_advisor_context_ids=compact_unique([item.get("id") for item in contexts]),
            advisor_saved_snapshot_ids=compact_unique([item.get("id") for item in snapshots]),
            policy_comparison_snapshot_ids=compact_unique([item.get("policy_comparison_snapshot_id") for item in contexts + snapshots]),
            advisor_result_ids=compact_unique([item.get("advisor_result_id") for item in contexts + snapshots]),
            quote_result_ids=compact_unique([quote_id for item in contexts + snapshots for quote_id in item.get("quote_result_ids") or []]),
            airline_codes=self._airlines_from_options(options, segments, contexts),
            taxonomy_refs_json=self._taxonomy_refs(contexts, advisor_rows),
            offer_workspace_summary_json=self._workspace_summary(workspace),
            option_summary_json={"option_count": len(options), "options": [self._option_summary(option, pricing_lines, segments) for option in options]},
            passenger_context_json=self._first_context_json(contexts, "passenger_context_json"),
            request_context_json={"request_id": workspace.get("request_id"), "trip_id": workspace.get("trip_id")},
            service_context_json=self._first_context_json(contexts, "service_context_json"),
            option_count=len(options),
            manual_review_required=True,
            created_by_user_id=(user or {}).get("id"),
            metadata_json=data.get("metadata_json") or {},
        )
        stored_pack = await self.db.collection(PACK_COLLECTION).insert_one(pack.model_dump(mode="json"))

        created_options: list[dict[str, Any]] = []
        created_evidence: list[dict[str, Any]] = []
        created_warnings: list[dict[str, Any]] = []
        for option in options:
            option_result = await self._build_option_records(
                agency_id=agency_id,
                pack=stored_pack,
                option=option,
                segments=segments,
                pricing_lines=pricing_lines,
                contexts=contexts,
                snapshots=snapshots,
                advisor_rows=advisor_rows,
                advisor_warnings=advisor_warnings,
            )
            created_options.append(option_result["option"])
            created_evidence.extend(option_result["evidence"])
            created_warnings.extend(option_result["warnings"])

        if not options:
            created_warnings.append(
                await self._create_warning(
                    agency_id,
                    stored_pack,
                    {
                        "warning_level": PolicyComparisonWarningLevel.WARNING.value,
                        "warning_type": "offer_options_missing",
                        "message": "Decision pack has no offer options to review.",
                        "source": OfferDecisionPackWarningSource.OFFER_CONTEXT.value,
                    },
                )
            )

        refreshed_pack = await self._refresh_pack_counts(agency_id, stored_pack["id"])
        return {
            "pack": refreshed_pack or stored_pack,
            "options": created_options,
            "evidence": created_evidence,
            "warnings": created_warnings,
            **self._safety_flags(),
        }

    async def attach_advisor_evidence(
        self,
        agency_id: str,
        pack_id: str,
        payload: OfferDecisionPackAdvisorAttachmentRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any] | None:
        pack = await self.get_pack(pack_id, agency_id)
        if not pack:
            return None
        data = payload_dict(payload)
        airline_code = normalize_airline_code(data.get("airline_code"))
        context = None
        snapshot = None
        if data.get("advisor_context_id"):
            context = await self.db.collection(ADVISOR_CONTEXT_COLLECTION).find_one(
                {"agency_id": agency_id, "id": data["advisor_context_id"], "offer_workspace_id": pack["offer_workspace_id"]}
            )
            if not context:
                raise ValueError("Offer policy advisor context not found for this decision pack.")
        if data.get("advisor_saved_snapshot_id"):
            snapshot = await self.db.collection(ADVISOR_SNAPSHOT_COLLECTION).find_one(
                {"agency_id": agency_id, "id": data["advisor_saved_snapshot_id"], "offer_workspace_id": pack["offer_workspace_id"]}
            )
            if not snapshot:
                raise ValueError("Offer policy advisor saved snapshot not found for this decision pack.")

        option_id = data.get("offer_option_id") or (context or {}).get("offer_option_id") or (snapshot or {}).get("offer_option_id")
        pack_options = await self.list_options(agency_id=agency_id, decision_pack_id=pack_id)
        if not option_id and airline_code:
            option_id = next((item.get("offer_option_id") for item in pack_options if normalize_airline_code(item.get("airline_code")) == airline_code), None)
        if not airline_code and option_id:
            airline_code = normalize_airline_code(next((item.get("airline_code") for item in pack_options if item.get("offer_option_id") == option_id), None))

        evidence = []
        if context:
            evidence.append(
                await self._create_evidence(
                    agency_id,
                    pack,
                    {
                        "offer_option_id": option_id,
                        "airline_code": airline_code,
                        "evidence_type": OfferDecisionPackEvidenceType.ADVISOR_CONTEXT.value,
                        "evidence_title": "Attached offer policy advisor context",
                        "evidence_summary": context.get("context_name"),
                        "source_collection": ADVISOR_CONTEXT_COLLECTION,
                        "source_record_id": context["id"],
                        "advisor_context_id": context["id"],
                        "policy_comparison_snapshot_id": context.get("policy_comparison_snapshot_id"),
                        "advisor_result_id": context.get("advisor_result_id"),
                        "domain_code": context.get("domain_code"),
                        "family_code": context.get("family_code"),
                        "variant_code": context.get("variant_code"),
                        "passenger_context_json": context.get("passenger_context_json") or {},
                        "service_context_json": context.get("service_context_json") or {},
                        "evidence_json": {"context": context, "attachment_metadata_json": data.get("metadata_json") or {}},
                    },
                )
            )
        if snapshot:
            evidence.append(
                await self._create_evidence(
                    agency_id,
                    pack,
                    {
                        "offer_option_id": option_id,
                        "airline_code": airline_code,
                        "evidence_type": OfferDecisionPackEvidenceType.ADVISOR_SNAPSHOT.value,
                        "evidence_title": "Attached saved advisor snapshot",
                        "evidence_summary": snapshot.get("snapshot_name"),
                        "source_collection": ADVISOR_SNAPSHOT_COLLECTION,
                        "source_record_id": snapshot["id"],
                        "advisor_saved_snapshot_id": snapshot["id"],
                        "advisor_context_id": snapshot.get("context_id"),
                        "policy_comparison_snapshot_id": snapshot.get("policy_comparison_snapshot_id"),
                        "advisor_result_id": snapshot.get("advisor_result_id"),
                        "evidence_json": {"snapshot": snapshot, "attachment_metadata_json": data.get("metadata_json") or {}},
                    },
                )
            )

        if not evidence:
            raise ValueError("No advisor context or saved snapshot was provided.")

        updates = {
            "offer_policy_advisor_context_ids": compact_unique((pack.get("offer_policy_advisor_context_ids") or []) + [context.get("id") if context else None]),
            "advisor_saved_snapshot_ids": compact_unique((pack.get("advisor_saved_snapshot_ids") or []) + [snapshot.get("id") if snapshot else None]),
            "policy_comparison_snapshot_ids": compact_unique((pack.get("policy_comparison_snapshot_ids") or []) + [(context or snapshot or {}).get("policy_comparison_snapshot_id")]),
            "advisor_result_ids": compact_unique((pack.get("advisor_result_ids") or []) + [(context or snapshot or {}).get("advisor_result_id")]),
            "quote_result_ids": compact_unique((pack.get("quote_result_ids") or []) + [quote_id for quote_id in (context or snapshot or {}).get("quote_result_ids") or []]),
        }
        await self.db.collection(PACK_COLLECTION).update_one({"agency_id": agency_id, "id": pack_id}, updates)

        if option_id:
            option_update = {
                "advisor_context_id": context.get("id") if context else None,
                "advisor_saved_snapshot_id": snapshot.get("id") if snapshot else None,
                "policy_comparison_snapshot_id": (context or snapshot or {}).get("policy_comparison_snapshot_id"),
                "advisor_result_id": (context or snapshot or {}).get("advisor_result_id"),
                "quote_result_ids": (context or snapshot or {}).get("quote_result_ids") or [],
            }
            await self.db.collection(OPTION_COLLECTION).update_one(
                {"agency_id": agency_id, "decision_pack_id": pack_id, "offer_option_id": option_id},
                {key: value for key, value in option_update.items() if value is not None},
            )

        refreshed_pack = await self._refresh_pack_counts(agency_id, pack_id)
        return {
            "pack": refreshed_pack,
            "evidence": evidence,
            **self._safety_flags(),
        }

    async def create_review_note(self, agency_id: str, pack_id: str, payload: Any, user: dict | None = None) -> dict[str, Any] | None:
        pack = await self.get_pack(pack_id, agency_id)
        if not pack:
            return None
        data = payload_dict(payload)
        note = OfferDecisionPackReviewNote(
            agency_id=agency_id,
            decision_pack_id=pack_id,
            offer_workspace_id=pack["offer_workspace_id"],
            offer_option_id=data.get("offer_option_id"),
            airline_code=normalize_airline_code(data.get("airline_code")),
            note_title=data["note_title"],
            note_body=data["note_body"],
            note_status=enum_value(data.get("note_status")) or OfferDecisionPackReviewNoteStatus.RECORDED.value,
            created_by_user_id=(user or {}).get("id"),
            metadata_json=data.get("metadata_json") or {},
        )
        stored_note = await self.db.collection(REVIEW_NOTE_COLLECTION).insert_one(note.model_dump(mode="json"))
        await self._refresh_pack_counts(agency_id, pack_id)
        return {"review_note": stored_note, **self._safety_flags()}

    async def update_review_note(self, agency_id: str, pack_id: str, note_id: str, payload: OfferDecisionPackReviewNoteUpdate | dict[str, Any]) -> dict[str, Any] | None:
        pack = await self.get_pack(pack_id, agency_id)
        if not pack:
            return None
        current = await self.db.collection(REVIEW_NOTE_COLLECTION).find_one({"agency_id": agency_id, "decision_pack_id": pack_id, "id": note_id})
        if not current:
            return None
        data = payload_dict(payload)
        updates = {
            key: enum_value(value)
            for key, value in {
                "note_title": data.get("note_title"),
                "note_body": data.get("note_body"),
                "note_status": data.get("note_status"),
                "metadata_json": data.get("metadata_json"),
            }.items()
            if value is not None
        }
        updated_note = await self.db.collection(REVIEW_NOTE_COLLECTION).update_one(
            {"agency_id": agency_id, "decision_pack_id": pack_id, "id": note_id},
            updates,
        )
        await self._refresh_pack_counts(agency_id, pack_id)
        return {"review_note": updated_note, **self._safety_flags()}

    async def create_snapshot(self, agency_id: str, pack_id: str, payload: OfferDecisionPackSnapshotCreate | dict[str, Any]) -> dict[str, Any] | None:
        detail = await self.get_pack_detail(pack_id, agency_id)
        if not detail:
            return None
        pack = detail["pack"]
        data = payload_dict(payload)
        snapshot = OfferDecisionPackSnapshot(
            agency_id=agency_id,
            decision_pack_id=pack_id,
            offer_workspace_id=pack["offer_workspace_id"],
            snapshot_name=data.get("snapshot_name") or f"Decision pack snapshot {pack.get('pack_name') or pack_id}",
            option_ids=[item["id"] for item in detail["options"]],
            evidence_ids=[item["id"] for item in detail["evidence"]],
            warning_ids=[item["id"] for item in detail["warnings"]],
            review_note_ids=[item["id"] for item in detail["review_notes"]],
            source_advisor_snapshot_ids=pack.get("advisor_saved_snapshot_ids") or [],
            snapshot_json={
                "pack": pack,
                "options": detail["options"],
                "evidence": detail["evidence"],
                "warnings": detail["warnings"],
                "review_notes": detail["review_notes"],
                "metadata_json": data.get("metadata_json") or {},
                "metadata_only": True,
                "human_review_required": True,
            },
        )
        stored_snapshot = await self.db.collection(SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))
        await self.db.collection(PACK_COLLECTION).update_one(
            {"agency_id": agency_id, "id": pack_id},
            {"pack_status": OfferDecisionPackStatus.SNAPSHOTTED.value},
        )
        refreshed_pack = await self._refresh_pack_counts(agency_id, pack_id)
        return {"snapshot": stored_snapshot, "pack": refreshed_pack, **self._safety_flags()}

    async def list_options(
        self,
        *,
        agency_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(OPTION_COLLECTION, agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)

    async def list_evidence(
        self,
        *,
        agency_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(EVIDENCE_COLLECTION, agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)

    async def list_warnings(
        self,
        *,
        agency_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(WARNING_COLLECTION, agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)

    async def list_review_notes(
        self,
        *,
        agency_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(REVIEW_NOTE_COLLECTION, agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)

    async def list_snapshots(
        self,
        *,
        agency_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(SNAPSHOT_COLLECTION, agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)

    async def _list_records(
        self,
        collection_name: str,
        *,
        agency_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if decision_pack_id:
            filters["decision_pack_id"] = decision_pack_id
        if offer_workspace_id:
            filters["offer_workspace_id"] = offer_workspace_id
        items = await self.db.collection(collection_name).find_many(filters or None)
        return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def _build_option_records(
        self,
        *,
        agency_id: str,
        pack: dict[str, Any],
        option: dict[str, Any],
        segments: list[dict[str, Any]],
        pricing_lines: list[dict[str, Any]],
        contexts: list[dict[str, Any]],
        snapshots: list[dict[str, Any]],
        advisor_rows: list[dict[str, Any]],
        advisor_warnings: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]] | dict[str, Any]]:
        option_id = option["id"]
        airline_code = normalize_airline_code(option.get("main_airline_code")) or self._airline_from_segments(option_id, segments)
        matched_rows = [
            row
            for row in advisor_rows
            if (row.get("offer_option_id") in {None, option_id})
            and (not airline_code or normalize_airline_code(row.get("airline_code")) == airline_code)
        ]
        matched_context = self._match_context(contexts, option_id, airline_code, matched_rows)
        matched_snapshot = self._match_snapshot(snapshots, matched_context, matched_rows, option_id, airline_code)
        matched_warnings = self._match_advisor_warnings(advisor_warnings, matched_context, option_id, airline_code)

        evidence = []
        evidence.append(
            await self._create_evidence(
                agency_id,
                pack,
                {
                    "offer_option_id": option_id,
                    "airline_code": airline_code,
                    "evidence_type": OfferDecisionPackEvidenceType.OFFER_OPTION.value,
                    "evidence_title": "Offer option metadata",
                    "evidence_summary": option.get("label") or option_id,
                    "source_collection": "offer_options",
                    "source_record_id": option_id,
                    "evidence_json": self._option_summary(option, pricing_lines, segments),
                },
            )
        )
        if matched_context:
            evidence.append(
                await self._create_evidence(
                    agency_id,
                    pack,
                    {
                        "offer_option_id": option_id,
                        "airline_code": airline_code,
                        "evidence_type": OfferDecisionPackEvidenceType.ADVISOR_CONTEXT.value,
                        "evidence_title": "Offer policy advisor context",
                        "evidence_summary": matched_context.get("context_name"),
                        "source_collection": ADVISOR_CONTEXT_COLLECTION,
                        "source_record_id": matched_context["id"],
                        "advisor_context_id": matched_context["id"],
                        "policy_comparison_snapshot_id": matched_context.get("policy_comparison_snapshot_id"),
                        "advisor_result_id": matched_context.get("advisor_result_id"),
                        "domain_code": matched_context.get("domain_code"),
                        "family_code": matched_context.get("family_code"),
                        "variant_code": matched_context.get("variant_code"),
                        "passenger_context_json": matched_context.get("passenger_context_json") or {},
                        "service_context_json": matched_context.get("service_context_json") or {},
                        "evidence_json": matched_context,
                    },
                )
            )
        if matched_snapshot:
            evidence.append(
                await self._create_evidence(
                    agency_id,
                    pack,
                    {
                        "offer_option_id": option_id,
                        "airline_code": airline_code,
                        "evidence_type": OfferDecisionPackEvidenceType.ADVISOR_SNAPSHOT.value,
                        "evidence_title": "Saved offer advisor snapshot",
                        "evidence_summary": matched_snapshot.get("snapshot_name"),
                        "source_collection": ADVISOR_SNAPSHOT_COLLECTION,
                        "source_record_id": matched_snapshot["id"],
                        "advisor_saved_snapshot_id": matched_snapshot["id"],
                        "advisor_context_id": matched_snapshot.get("context_id"),
                        "policy_comparison_snapshot_id": matched_snapshot.get("policy_comparison_snapshot_id"),
                        "advisor_result_id": matched_snapshot.get("advisor_result_id"),
                        "evidence_json": matched_snapshot,
                    },
                )
            )
        for row in matched_rows:
            evidence.append(
                await self._create_evidence(
                    agency_id,
                    pack,
                    {
                        "offer_option_id": option_id,
                        "airline_code": normalize_airline_code(row.get("airline_code")) or airline_code,
                        "evidence_type": OfferDecisionPackEvidenceType.ADVISOR_AIRLINE_ROW.value,
                        "evidence_title": "Advisor airline comparison row",
                        "evidence_summary": row.get("advisor_summary") or row.get("pricing_summary"),
                        "source_collection": ADVISOR_ROW_COLLECTION,
                        "source_record_id": row["id"],
                        "advisor_context_id": row.get("context_id"),
                        "advisor_saved_snapshot_id": (matched_snapshot or {}).get("id"),
                        "policy_comparison_snapshot_id": row.get("policy_comparison_snapshot_id"),
                        "policy_comparison_row_id": row.get("policy_comparison_row_id"),
                        "advisor_result_id": row.get("advisor_result_id"),
                        "quote_result_id": row.get("quote_result_id"),
                        "domain_code": row.get("domain_code"),
                        "family_code": row.get("family_code"),
                        "variant_code": row.get("variant_code"),
                        "service_context_json": (matched_context or {}).get("service_context_json") or {},
                        "evidence_json": row,
                    },
                )
            )

        warnings = [
            await self._create_warning(
                agency_id,
                pack,
                {
                    "offer_option_id": option_id,
                    "airline_code": normalize_airline_code(item.get("airline_code")) or airline_code,
                    "warning_level": item.get("warning_level"),
                    "warning_type": item.get("warning_type") or "advisor_warning",
                    "message": item.get("message") or "Manual review required.",
                    "source": self._warning_source_from_advisor(item),
                    "source_record_id": item.get("id"),
                },
            )
            for item in matched_warnings
        ]
        if not matched_context and not matched_snapshot and len(evidence) == 1:
            warnings.append(
                await self._create_warning(
                    agency_id,
                    pack,
                    {
                        "offer_option_id": option_id,
                        "airline_code": airline_code,
                        "warning_level": PolicyComparisonWarningLevel.ADVISORY.value,
                        "warning_type": "advisor_evidence_missing",
                        "message": "No saved advisor evidence is attached to this offer option.",
                        "source": OfferDecisionPackWarningSource.OFFER_CONTEXT.value,
                    },
                )
            )

        score = max([int(row.get("operational_complexity_score") or 0) for row in matched_rows] or [0])
        option_record = OfferDecisionPackOption(
            agency_id=agency_id,
            decision_pack_id=pack["id"],
            offer_workspace_id=pack["offer_workspace_id"],
            offer_option_id=option_id,
            airline_code=airline_code,
            option_label=option.get("label"),
            option_status=option.get("status"),
            advisor_context_id=(matched_context or {}).get("id"),
            advisor_saved_snapshot_id=(matched_snapshot or {}).get("id"),
            policy_comparison_snapshot_id=(matched_context or matched_snapshot or {}).get("policy_comparison_snapshot_id"),
            advisor_result_id=(matched_context or matched_snapshot or {}).get("advisor_result_id"),
            quote_result_ids=compact_unique([row.get("quote_result_id") for row in matched_rows] + ((matched_context or matched_snapshot or {}).get("quote_result_ids") or [])),
            domain_code=(matched_context or (matched_rows[0] if matched_rows else {})).get("domain_code"),
            family_code=(matched_context or (matched_rows[0] if matched_rows else {})).get("family_code"),
            variant_code=(matched_context or (matched_rows[0] if matched_rows else {})).get("variant_code"),
            operational_complexity_score=score,
            warning_level=worst_warning_level([row.get("warning_level") for row in matched_rows] + [item.get("warning_level") for item in warnings]),
            evidence_count=len(evidence),
            unresolved_warning_count=len([item for item in warnings if not item.get("resolved")]),
            manual_review_required=True,
            pricing_summary_json=self._option_pricing_summary(option_id, pricing_lines),
            option_summary_json=self._option_summary(option, pricing_lines, segments),
        )
        stored_option = await self.db.collection(OPTION_COLLECTION).insert_one(option_record.model_dump(mode="json"))
        return {"option": stored_option, "evidence": evidence, "warnings": warnings}

    async def _create_evidence(self, agency_id: str, pack: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        evidence = OfferDecisionPackEvidence(
            agency_id=agency_id,
            decision_pack_id=pack["id"],
            offer_workspace_id=pack["offer_workspace_id"],
            offer_option_id=data.get("offer_option_id"),
            airline_code=normalize_airline_code(data.get("airline_code")),
            evidence_type=enum_value(data["evidence_type"]),
            evidence_title=data["evidence_title"],
            evidence_summary=data.get("evidence_summary"),
            source_collection=data.get("source_collection"),
            source_record_id=data.get("source_record_id"),
            advisor_context_id=data.get("advisor_context_id"),
            advisor_saved_snapshot_id=data.get("advisor_saved_snapshot_id"),
            policy_comparison_snapshot_id=data.get("policy_comparison_snapshot_id"),
            policy_comparison_row_id=data.get("policy_comparison_row_id"),
            advisor_result_id=data.get("advisor_result_id"),
            quote_result_id=data.get("quote_result_id"),
            service_mechanics_record_id=data.get("service_mechanics_record_id"),
            domain_code=normalize_taxonomy_code(data.get("domain_code")),
            family_code=normalize_taxonomy_code(data.get("family_code")),
            variant_code=normalize_taxonomy_code(data.get("variant_code")),
            passenger_context_json=data.get("passenger_context_json") or {},
            request_context_json=data.get("request_context_json") or {},
            service_context_json=data.get("service_context_json") or {},
            evidence_json=data.get("evidence_json") or {},
        )
        return await self.db.collection(EVIDENCE_COLLECTION).insert_one(evidence.model_dump(mode="json"))

    async def _create_warning(self, agency_id: str, pack: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        warning = OfferDecisionPackWarning(
            agency_id=agency_id,
            decision_pack_id=pack["id"],
            offer_workspace_id=pack["offer_workspace_id"],
            offer_option_id=data.get("offer_option_id"),
            airline_code=normalize_airline_code(data.get("airline_code")),
            warning_level=warning_level(data.get("warning_level") or PolicyComparisonWarningLevel.INFO.value),
            warning_type=data.get("warning_type") or "decision_pack_warning",
            message=data.get("message") or "Human review required.",
            source=enum_value(data.get("source")) or OfferDecisionPackWarningSource.OFFER_CONTEXT.value,
            source_record_id=data.get("source_record_id"),
            human_review_required=True,
            resolved=bool(data.get("resolved", False)),
        )
        return await self.db.collection(WARNING_COLLECTION).insert_one(warning.model_dump(mode="json"))

    async def _refresh_pack_counts(self, agency_id: str, pack_id: str) -> dict[str, Any] | None:
        options = await self.list_options(agency_id=agency_id, decision_pack_id=pack_id)
        evidence = await self.list_evidence(agency_id=agency_id, decision_pack_id=pack_id)
        warnings = await self.list_warnings(agency_id=agency_id, decision_pack_id=pack_id)
        notes = await self.list_review_notes(agency_id=agency_id, decision_pack_id=pack_id)
        snapshots = await self.list_snapshots(agency_id=agency_id, decision_pack_id=pack_id)
        return await self.db.collection(PACK_COLLECTION).update_one(
            {"agency_id": agency_id, "id": pack_id},
            {
                "option_count": len(options),
                "evidence_count": len(evidence),
                "unresolved_warning_count": len([item for item in warnings if not item.get("resolved")]),
                "review_note_count": len(notes),
                "saved_snapshot_count": len(snapshots),
                "operational_complexity_score": max([int(item.get("operational_complexity_score") or 0) for item in options] or [0]),
                "warning_level": worst_warning_level([item.get("warning_level") for item in warnings + options]),
                "manual_review_required": True,
                "human_review_required": True,
            },
        )

    async def _workspace_options(self, agency_id: str, workspace_id: str) -> list[dict[str, Any]]:
        return await self.db.collection("offer_options").find_many({"agency_id": agency_id, "workspace_id": workspace_id})

    async def _workspace_segments(self, agency_id: str, options: list[dict[str, Any]]) -> list[dict[str, Any]]:
        option_ids = {item["id"] for item in options}
        return [
            item
            for item in await self.db.collection("offer_builder_segments").find_many({"agency_id": agency_id})
            if item.get("option_id") in option_ids
        ]

    async def _workspace_pricing_lines(self, agency_id: str, options: list[dict[str, Any]]) -> list[dict[str, Any]]:
        option_ids = {item["id"] for item in options}
        return [
            item
            for item in await self.db.collection("offer_pricing_lines").find_many({"agency_id": agency_id})
            if item.get("option_id") in option_ids
        ]

    async def _advisor_contexts(self, agency_id: str, workspace_id: str, context_ids: list[str]) -> list[dict[str, Any]]:
        if context_ids:
            contexts = [
                item
                for item in await self.db.collection(ADVISOR_CONTEXT_COLLECTION).find_many({"agency_id": agency_id, "offer_workspace_id": workspace_id})
                if item.get("id") in set(context_ids)
            ]
        else:
            contexts = await self.db.collection(ADVISOR_CONTEXT_COLLECTION).find_many({"agency_id": agency_id, "offer_workspace_id": workspace_id})
        return sorted(contexts, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def _advisor_snapshots(self, agency_id: str, workspace_id: str, snapshot_ids: list[str]) -> list[dict[str, Any]]:
        if snapshot_ids:
            snapshots = [
                item
                for item in await self.db.collection(ADVISOR_SNAPSHOT_COLLECTION).find_many({"agency_id": agency_id, "offer_workspace_id": workspace_id})
                if item.get("id") in set(snapshot_ids)
            ]
        else:
            snapshots = await self.db.collection(ADVISOR_SNAPSHOT_COLLECTION).find_many({"agency_id": agency_id, "offer_workspace_id": workspace_id})
        return sorted(snapshots, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def _advisor_rows(self, agency_id: str, workspace_id: str, contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        context_ids = {item["id"] for item in contexts}
        rows = await self.db.collection(ADVISOR_ROW_COLLECTION).find_many({"agency_id": agency_id, "offer_workspace_id": workspace_id})
        if not context_ids:
            return rows
        return [item for item in rows if item.get("context_id") in context_ids]

    async def _advisor_warnings(self, agency_id: str, workspace_id: str, contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        context_ids = {item["id"] for item in contexts}
        warnings = await self.db.collection(ADVISOR_WARNING_COLLECTION).find_many({"agency_id": agency_id, "offer_workspace_id": workspace_id})
        if not context_ids:
            return warnings
        return [item for item in warnings if item.get("context_id") in context_ids]

    def _match_context(self, contexts: list[dict[str, Any]], option_id: str, airline_code: str | None, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        row_context_ids = {row.get("context_id") for row in rows}
        for context in contexts:
            if context.get("offer_option_id") == option_id:
                return context
        for context in contexts:
            if context.get("id") in row_context_ids:
                return context
        for context in contexts:
            if airline_code and airline_code in {normalize_airline_code(item) for item in context.get("airline_codes") or []}:
                return context
        return contexts[0] if len(contexts) == 1 else None

    def _match_snapshot(
        self,
        snapshots: list[dict[str, Any]],
        context: dict[str, Any] | None,
        rows: list[dict[str, Any]],
        option_id: str,
        airline_code: str | None,
    ) -> dict[str, Any] | None:
        row_ids = {row.get("id") for row in rows}
        for snapshot in snapshots:
            if snapshot.get("offer_option_id") == option_id:
                return snapshot
        for snapshot in snapshots:
            if context and snapshot.get("context_id") == context.get("id"):
                return snapshot
        for snapshot in snapshots:
            if row_ids.intersection(set(snapshot.get("airline_row_ids") or [])):
                return snapshot
        for snapshot in snapshots:
            rows_json = ((snapshot.get("snapshot_json") or {}).get("airline_rows") or [])
            if airline_code and any(normalize_airline_code(row.get("airline_code")) == airline_code for row in rows_json):
                return snapshot
        return snapshots[0] if len(snapshots) == 1 else None

    def _match_advisor_warnings(
        self,
        warnings: list[dict[str, Any]],
        context: dict[str, Any] | None,
        option_id: str,
        airline_code: str | None,
    ) -> list[dict[str, Any]]:
        context_id = (context or {}).get("id")
        matched = []
        for item in warnings:
            if context_id and item.get("context_id") not in {None, context_id}:
                continue
            item_option_id = item.get("offer_option_id")
            item_airline_code = normalize_airline_code(item.get("airline_code"))
            option_matches = item_option_id in {None, option_id}
            airline_matches = not item_airline_code or not airline_code or item_airline_code == airline_code
            if option_matches and airline_matches:
                matched.append(item)
        return matched

    def _warning_source_from_advisor(self, warning: dict[str, Any]) -> str:
        source = warning.get("source")
        if source == "policy_comparison":
            return OfferDecisionPackWarningSource.POLICY_COMPARISON.value
        if source == "ancillary_pricing":
            return OfferDecisionPackWarningSource.ANCILLARY_PRICING.value
        if source == "service_mechanics":
            return OfferDecisionPackWarningSource.SERVICE_MECHANICS.value
        return OfferDecisionPackWarningSource.ADVISOR_CONTEXT.value

    def _workspace_summary(self, workspace: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": workspace.get("id"),
            "title": workspace.get("title"),
            "request_id": workspace.get("request_id"),
            "trip_id": workspace.get("trip_id"),
            "status": workspace.get("status"),
            "currency": workspace.get("currency"),
            "client_summary_json": workspace.get("client_summary_json") or {},
        }

    def _option_summary(self, option: dict[str, Any], pricing_lines: list[dict[str, Any]], segments: list[dict[str, Any]]) -> dict[str, Any]:
        option_id = option["id"]
        option_segments = [item for item in segments if item.get("option_id") == option_id]
        return {
            "id": option_id,
            "label": option.get("label"),
            "status": option.get("status"),
            "main_airline_code": option.get("main_airline_code"),
            "provider_name": option.get("provider_name"),
            "pricing_summary_json": option.get("pricing_summary_json") or {},
            "pricing_lines": [item for item in pricing_lines if item.get("option_id") == option_id],
            "segments": option_segments,
        }

    def _option_pricing_summary(self, option_id: str, pricing_lines: list[dict[str, Any]]) -> dict[str, Any]:
        lines = [item for item in pricing_lines if item.get("option_id") == option_id]
        return {
            "line_count": len(lines),
            "total_amount": sum(float(item.get("amount") or 0) for item in lines),
            "currencies": compact_unique([item.get("currency") for item in lines]),
            "lines": lines,
        }

    def _airline_from_segments(self, option_id: str, segments: list[dict[str, Any]]) -> str | None:
        for segment in segments:
            if segment.get("option_id") == option_id:
                return normalize_airline_code(segment.get("marketing_airline_code") or segment.get("operating_airline_code"))
        return None

    def _airlines_from_options(self, options: list[dict[str, Any]], segments: list[dict[str, Any]], contexts: list[dict[str, Any]]) -> list[str]:
        values = [option.get("main_airline_code") for option in options]
        values.extend(segment.get("marketing_airline_code") for segment in segments)
        values.extend(airline for context in contexts for airline in context.get("airline_codes") or [])
        return compact_unique([normalize_airline_code(item) for item in values])

    def _taxonomy_refs(self, contexts: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
        refs = []
        for item in contexts + rows:
            domain_code = normalize_taxonomy_code(item.get("domain_code"))
            family_code = normalize_taxonomy_code(item.get("family_code"))
            variant_code = normalize_taxonomy_code(item.get("variant_code"))
            if domain_code or family_code or variant_code:
                refs.append({"domain_code": domain_code, "family_code": family_code, "variant_code": variant_code})
        unique = []
        seen = set()
        for item in refs:
            key = (item.get("domain_code"), item.get("family_code"), item.get("variant_code"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return {"refs": unique}

    def _first_context_json(self, contexts: list[dict[str, Any]], key: str) -> dict[str, Any]:
        for context in contexts:
            if context.get(key):
                return context.get(key) or {}
        return {}

    def _safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "human_review_required": True,
            "auto_recommendation_disabled": True,
            "recommendations_disabled": True,
            "offer_price_mutation_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "ticket_emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
        }
