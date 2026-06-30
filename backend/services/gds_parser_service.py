from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    BookingImportParserStatus,
    GdsInputFormat,
    GdsParsedEntity,
    GdsParsedEntityStatus,
    GdsParsedEntityType,
    GdsParseCorrection,
    GdsParseCorrectionType,
    GdsParserEvaluationRun,
    GdsParserEvaluationStatus,
    GdsParserProfile,
    GdsParserRun,
    GdsParserRunStatus,
    GdsParserStrategy,
    GdsParserVersion,
    GdsParserVersionStatus,
    GdsParseSample,
    GdsParseSampleDifficulty,
    GdsParseSampleMode,
    GdsParseSampleRedactionStatus,
    GdsParseSampleScope,
    GdsParseSampleSource,
    GdsParseSampleStatus,
    GdsProviderFamily,
)


PHASE_LABEL = "phase_36_6_gds_parser_foundation"


DEFAULT_PROFILE_DEFINITIONS = [
    {
        "profile_key": "generic_gds_cryptic_pnr",
        "title": "Generic GDS cryptic PNR",
        "description": "Conservative regex and section rules for Amadeus/Sabre/Travelport-like PNR text.",
        "provider_family": GdsProviderFamily.GENERIC_GDS.value,
        "input_format": GdsInputFormat.CRYPTIC_PNR.value,
        "default_for_provider_family": True,
        "parser_strategy": GdsParserStrategy.HYBRID_RULES.value,
    },
    {
        "profile_key": "amadeus_cryptic_pnr",
        "title": "Amadeus cryptic PNR",
        "description": "Rules for RP/ and numbered Amadeus itinerary displays.",
        "provider_family": GdsProviderFamily.AMADEUS.value,
        "input_format": GdsInputFormat.CRYPTIC_PNR.value,
        "default_for_provider_family": True,
        "parser_strategy": GdsParserStrategy.HYBRID_RULES.value,
    },
    {
        "profile_key": "sabre_itinerary_text",
        "title": "Sabre itinerary text",
        "description": "Conservative rules for Sabre-like passenger, itinerary, SSR, and ticket displays.",
        "provider_family": GdsProviderFamily.SABRE.value,
        "input_format": GdsInputFormat.ITINERARY_TEXT.value,
        "default_for_provider_family": True,
        "parser_strategy": GdsParserStrategy.SECTION_RULES.value,
    },
    {
        "profile_key": "travelport_itinerary_text",
        "title": "Travelport itinerary text",
        "description": "Conservative rules for Travelport/Galileo-like itinerary and ticket text.",
        "provider_family": GdsProviderFamily.TRAVELPORT.value,
        "input_format": GdsInputFormat.ITINERARY_TEXT.value,
        "default_for_provider_family": True,
        "parser_strategy": GdsParserStrategy.SECTION_RULES.value,
    },
    {
        "profile_key": "airline_confirmation_email",
        "title": "Airline confirmation or agency itinerary",
        "description": "Low-risk extraction for itinerary confirmation email/plain text without GDS grammar assumptions.",
        "provider_family": GdsProviderFamily.AIRLINE_CONFIRMATION.value,
        "input_format": GdsInputFormat.EMAIL_CONFIRMATION.value,
        "default_for_provider_family": True,
        "parser_strategy": GdsParserStrategy.REGEX_RULES.value,
    },
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get(payload: Any, key: str, default: Any = None) -> Any:
    if hasattr(payload, key):
        return getattr(payload, key)
    if isinstance(payload, dict):
        return payload.get(key, default)
    return default


def _enum_value(value: Any) -> str:
    return getattr(value, "value", value)


def _warning(code: str, message: str, severity: str = "warning") -> dict[str, str]:
    return {"code": code, "message": message, "severity": severity}


def _compact(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if value is not None and value != ""}


def _display_name(passenger: dict[str, Any]) -> str:
    return (
        passenger.get("display_name")
        or " ".join([str(passenger.get("first_name") or "").strip(), str(passenger.get("last_name") or "").strip()]).strip()
        or passenger.get("raw_line")
        or "Passenger"
    )


def _summary_for_entity(entity_type: str, value: dict[str, Any]) -> str:
    if entity_type == GdsParsedEntityType.PASSENGER.value:
        return _display_name(value)
    if entity_type == GdsParsedEntityType.SEGMENT.value:
        return " ".join(
            [
                str(value.get("marketing_airline_code") or ""),
                str(value.get("flight_number") or ""),
                f"{value.get('origin_airport_code') or '?'}-{value.get('destination_airport_code') or '?'}",
            ]
        ).strip()
    if entity_type in {GdsParsedEntityType.TICKET.value, GdsParsedEntityType.EMD.value}:
        return str(value.get("number") or value.get("ticket_number") or value.get("emd_number") or "")
    if entity_type in {GdsParsedEntityType.SSR.value, GdsParsedEntityType.OSI.value}:
        return str(value.get("line") or value.get("free_text") or value.get("text") or "")
    return ", ".join(f"{key}: {item}" for key, item in value.items() if item not in {None, ""})[:120]


class GdsParserService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def seed_default_parser_profiles(self) -> dict[str, Any]:
        created_profiles: list[dict[str, Any]] = []
        created_versions: list[dict[str, Any]] = []
        existing_profiles = 0
        existing_versions = 0

        for definition in DEFAULT_PROFILE_DEFINITIONS:
            existing = await self.db.collection("gds_parser_profiles").find_one({"profile_key": definition["profile_key"]})
            if existing:
                existing_profiles += 1
                profile = existing
            else:
                profile_model = GdsParserProfile(
                    **definition,
                    active=True,
                    confidence_threshold_import=0.80,
                    confidence_threshold_warning=0.60,
                )
                profile = await self.db.collection("gds_parser_profiles").insert_one(profile_model.model_dump(mode="json"))
                created_profiles.append(profile)

            versions = await self.db.collection("gds_parser_versions").find_many({"parser_profile_id": profile["id"]})
            if versions:
                existing_versions += len(versions)
                continue

            version = GdsParserVersion(
                parser_profile_id=profile["id"],
                version_label="v1.0-foundation",
                status=GdsParserVersionStatus.ACTIVE,
                rules_json={
                    "phase": PHASE_LABEL,
                    "rules": [
                        "record_locator_regex",
                        "passenger_name_regex",
                        "flight_segment_regex",
                        "ticket_emd_number_regex",
                        "ssr_osi_line_capture",
                        "obvious_pricing_capture",
                    ],
                    "external_services": False,
                },
                extraction_schema_json={
                    "entities": [
                        "passenger",
                        "segment",
                        "ticket",
                        "emd",
                        "ssr",
                        "osi",
                        "pricing",
                        "fare_basis",
                        "contact",
                        "remark",
                    ]
                },
                known_limitations_json=[
                    {"code": "not_full_gds_grammar", "message": "Foundation parser does not implement complete host grammar."},
                    {"code": "manual_review_required", "message": "Low-confidence parses require staff review before mirror import."},
                ],
                change_notes="Initial deterministic parser foundation rules.",
                activated_at=_now(),
            )
            created_versions.append(await self.db.collection("gds_parser_versions").insert_one(version.model_dump(mode="json")))

        return {
            "created_profile_count": len(created_profiles),
            "existing_profile_count": existing_profiles,
            "created_version_count": len(created_versions),
            "existing_version_count": existing_versions,
            "profiles": created_profiles,
            "versions": created_versions,
            "live_gds_connection_disabled": True,
            "external_ai_parser_disabled": True,
        }

    async def list_parser_profiles(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        await self.seed_default_parser_profiles()
        items = await self.db.collection("gds_parser_profiles").find_many()
        for key, value in (filters or {}).items():
            if value not in {None, ""}:
                items = [item for item in items if item.get(key) == value]
        items.sort(key=lambda item: (str(item.get("provider_family") or ""), str(item.get("profile_key") or "")))
        return {"items": items}

    async def get_parser_profile(self, profile_id: str) -> dict[str, Any] | None:
        await self.seed_default_parser_profiles()
        return await self.db.collection("gds_parser_profiles").find_one({"id": profile_id})

    async def list_parser_versions(self, profile_id: str) -> dict[str, Any]:
        items = await self.db.collection("gds_parser_versions").find_many({"parser_profile_id": profile_id})
        items.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return {"items": items}

    async def create_parser_version(self, profile_id: str, payload: Any, user: dict) -> dict[str, Any] | None:
        profile = await self.get_parser_profile(profile_id)
        if not profile:
            return None
        version = GdsParserVersion(
            parser_profile_id=profile_id,
            version_label=_get(payload, "version_label"),
            status=GdsParserVersionStatus.DRAFT,
            rules_json=_get(payload, "rules_json", {}) or {},
            extraction_schema_json=_get(payload, "extraction_schema_json", {}) or {},
            known_limitations_json=_get(payload, "known_limitations_json", []) or [],
            change_notes=_get(payload, "change_notes"),
            created_by_user_id=user.get("id"),
        )
        created = await self.db.collection("gds_parser_versions").insert_one(version.model_dump(mode="json"))
        return {"version": created}

    async def activate_parser_version(self, profile_id: str, version_id: str, user: dict) -> dict[str, Any] | None:
        profile = await self.get_parser_profile(profile_id)
        version = await self.db.collection("gds_parser_versions").find_one({"parser_profile_id": profile_id, "id": version_id})
        if not profile or not version:
            return None
        versions = await self.db.collection("gds_parser_versions").find_many({"parser_profile_id": profile_id})
        for item in versions:
            if item["id"] != version_id and item.get("status") == GdsParserVersionStatus.ACTIVE.value:
                await self.db.collection("gds_parser_versions").update_one(
                    {"id": item["id"]},
                    {"status": GdsParserVersionStatus.ARCHIVED.value},
                )
        activated = await self.db.collection("gds_parser_versions").update_one(
            {"parser_profile_id": profile_id, "id": version_id},
            {"status": GdsParserVersionStatus.ACTIVE.value, "activated_at": _now(), "created_by_user_id": version.get("created_by_user_id") or user.get("id")},
        )
        return {"profile": profile, "version": activated, "live_provider_execution_disabled": True}

    def detect_input(self, raw_text: str) -> dict[str, str]:
        text = raw_text or ""
        upper = text.upper()
        provider_family = GdsProviderFamily.UNKNOWN.value
        if "RP/" in upper or re.search(r"\bAPE\b|\bAPM\b|\bTKOK\b", upper):
            provider_family = GdsProviderFamily.AMADEUS.value
        elif re.search(r"\b(?:1\.1|0[A-Z]{2}\d{2,4}|TJR|WETR)\b", upper):
            provider_family = GdsProviderFamily.SABRE.value
        elif "GALILEO" in upper or "TRAVELPORT" in upper or re.search(r"\b(?:\*R|SI\.|VENDOR LOCATOR)\b", upper):
            provider_family = GdsProviderFamily.TRAVELPORT.value
        elif "CONFIRMATION" in upper or "ITINERARY" in upper or "E-TICKET" in upper:
            provider_family = GdsProviderFamily.AIRLINE_CONFIRMATION.value
        elif upper.strip():
            provider_family = GdsProviderFamily.GENERIC_GDS.value

        input_format = GdsInputFormat.UNKNOWN.value
        has_ticket = bool(re.search(r"\b(?:TKT|TK|ETKT|E-TICKET|TICKET)[\s:/#-]*\d{3}[- ]?\d{10}\b", upper))
        has_emd = bool(re.search(r"\b(?:EMD|EMDS)[\s:/#-]*\d{3}[- ]?\d{10}\b", upper))
        has_price = bool(re.search(r"\b(?:FARE|TAX|TOTAL|TTL|GRAND TOTAL)\b", upper))
        has_segment = bool(re.search(r"\b[A-Z0-9]{2}\s?\d{2,4}\s+[A-Z]?\s*\d{0,2}[A-Z]{3}?\s*[A-Z]{3}[A-Z]{3}\b", upper))
        if has_emd and has_ticket:
            input_format = GdsInputFormat.MIXED_TEXT.value
        elif has_emd:
            input_format = GdsInputFormat.EMD_TEXT.value
        elif has_ticket:
            input_format = GdsInputFormat.TICKET_TEXT.value
        elif has_price and not has_segment:
            input_format = GdsInputFormat.PRICING_TEXT.value
        elif "QUEUE" in upper or re.search(r"\bQ/[A-Z0-9]", upper):
            input_format = GdsInputFormat.QUEUE_MESSAGE.value
        elif "@" in text and ("CONFIRMATION" in upper or "ITINERARY" in upper):
            input_format = GdsInputFormat.EMAIL_CONFIRMATION.value
        elif has_segment or "RP/" in upper:
            input_format = GdsInputFormat.CRYPTIC_PNR.value
        elif upper.strip():
            input_format = GdsInputFormat.ITINERARY_TEXT.value
        return {"provider_family": provider_family, "input_format": input_format}

    async def parse_text(self, agency_id: str, payload: Any, user: dict) -> dict[str, Any]:
        await self.seed_default_parser_profiles()
        raw_text = str(_get(payload, "raw_text", "") or "")
        booking_import_draft_id = _get(payload, "booking_import_draft_id")
        detection = self.detect_input(raw_text)
        profile = await self._select_profile(detection["provider_family"], _get(payload, "parser_profile_id"))
        version = await self._select_version(profile, _get(payload, "parser_version_id"))
        parsed = self._parse_core(raw_text, profile or {}, version or {})

        run_model = GdsParserRun(
            agency_id=agency_id,
            booking_import_draft_id=booking_import_draft_id,
            parser_profile_id=(profile or {}).get("id"),
            parser_version_id=(version or {}).get("id"),
            input_hash=hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
            input_excerpt=raw_text[:1200],
            provider_family_detected=detection["provider_family"],
            input_format_detected=detection["input_format"],
            parse_status=parsed["parse_status"],
            overall_confidence=parsed["overall_confidence"],
            extracted_passenger_count=len(parsed["preview"].get("passengers") or []),
            extracted_segment_count=len(parsed["preview"].get("segments") or []),
            extracted_ticket_count=len(parsed["preview"].get("ticket_numbers") or []),
            extracted_emd_count=len(parsed["preview"].get("emd_numbers") or []),
            extracted_ssr_count=len(parsed["preview"].get("ssr") or []),
            extracted_osi_count=len(parsed["preview"].get("osi") or []),
            warnings_json=parsed["warnings"],
            errors_json=parsed["errors"],
            extracted_payload_json=parsed["extracted_payload"],
            normalized_preview_json=parsed["preview"],
            created_by_user_id=user.get("id"),
        )
        parsed["preview"]["parser_run_id"] = run_model.id
        parsed["preview"]["parser_profile_id"] = run_model.parser_profile_id
        parsed["preview"]["parser_version_id"] = run_model.parser_version_id
        parsed["preview"]["provider_family_detected"] = detection["provider_family"]
        parsed["preview"]["input_format_detected"] = detection["input_format"]
        run_model.normalized_preview_json = parsed["preview"]
        run = await self.db.collection("gds_parser_runs").insert_one(run_model.model_dump(mode="json"))

        entities: list[dict[str, Any]] = []
        for entity in parsed["entities"]:
            model = GdsParsedEntity(
                agency_id=agency_id,
                parser_run_id=run["id"],
                booking_import_draft_id=booking_import_draft_id,
                entity_type=entity["entity_type"],
                entity_key=entity.get("entity_key"),
                source_text=entity.get("source_text") or "",
                normalized_json=entity.get("normalized_json") or {},
                confidence=entity.get("confidence") or 0.0,
            )
            entities.append(await self.db.collection("gds_parsed_entities").insert_one(model.model_dump(mode="json")))

        return {
            "parser_run": run,
            "entities": entities,
            "normalized_preview": run["normalized_preview_json"],
            "warnings": run.get("warnings_json") or [],
            "explicit_import_required": True,
            "live_gds_connection_disabled": True,
            "live_provider_execution_disabled": True,
            "external_ai_parser_disabled": True,
        }

    async def parse_booking_import_draft(self, agency_id: str, booking_import_draft_id: str, payload: Any, user: dict) -> dict[str, Any] | None:
        draft = await self.db.collection("booking_import_drafts").find_one({"agency_id": agency_id, "id": booking_import_draft_id})
        if not draft:
            return None
        result = await self.parse_text(
            agency_id,
            {
                "raw_text": draft.get("raw_text") or "",
                "booking_import_draft_id": booking_import_draft_id,
                "parser_profile_id": _get(payload, "parser_profile_id"),
                "parser_version_id": _get(payload, "parser_version_id"),
            },
            user,
        )
        run = result["parser_run"]
        preview = result["normalized_preview"]
        parser_status = BookingImportParserStatus.PARSED.value
        if run.get("parse_status") in {GdsParserRunStatus.PARTIAL.value, GdsParserRunStatus.MANUAL_REVIEW_REQUIRED.value}:
            parser_status = BookingImportParserStatus.NEEDS_REVIEW.value
        if run.get("parse_status") == GdsParserRunStatus.FAILED.value:
            parser_status = BookingImportParserStatus.FAILED.value

        counts = {
            "passengers": run.get("extracted_passenger_count", 0),
            "segments": run.get("extracted_segment_count", 0),
            "tickets": run.get("extracted_ticket_count", 0),
            "emds": run.get("extracted_emd_count", 0),
            "ssr": run.get("extracted_ssr_count", 0),
            "osi": run.get("extracted_osi_count", 0),
        }
        updated = await self.db.collection("booking_import_drafts").update_one(
            {"agency_id": agency_id, "id": booking_import_draft_id},
            {
                "parsed_json": preview,
                "parser_status": parser_status,
                "latest_parser_run_id": run["id"],
                "parser_profile_id": run.get("parser_profile_id"),
                "parser_version_id": run.get("parser_version_id"),
                "overall_confidence": run.get("overall_confidence"),
                "parsed_entity_counts_json": counts,
                "normalized_preview_json": preview,
                "warnings_json": run.get("warnings_json") or [],
                "error_json": {"errors": run.get("errors_json") or []} if run.get("errors_json") else {},
            },
        )
        return {**result, "draft": updated, "parsed": preview}

    async def get_parser_run(self, agency_id: str, parser_run_id: str) -> dict[str, Any] | None:
        return await self.db.collection("gds_parser_runs").find_one({"agency_id": agency_id, "id": parser_run_id})

    async def list_parser_runs(self, agency_id: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        items = await self.db.collection("gds_parser_runs").find_many({"agency_id": agency_id})
        for key, value in (filters or {}).items():
            if value not in {None, ""}:
                items = [item for item in items if item.get(key) == value]
        items.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return {"items": items}

    async def list_parsed_entities(self, agency_id: str, parser_run_id: str) -> dict[str, Any]:
        items = await self.db.collection("gds_parsed_entities").find_many({"agency_id": agency_id, "parser_run_id": parser_run_id})
        items.sort(key=lambda item: (str(item.get("entity_type") or ""), str(item.get("entity_key") or "")))
        return {"items": items}

    async def apply_entity_correction(self, agency_id: str, payload: Any, user: dict) -> dict[str, Any] | None:
        parser_run_id = _get(payload, "parser_run_id")
        run = await self.get_parser_run(agency_id, parser_run_id)
        if not run:
            return None
        entity_id = _get(payload, "parsed_entity_id")
        entity = await self.db.collection("gds_parsed_entities").find_one({"agency_id": agency_id, "id": entity_id}) if entity_id else None
        entity_type = _get(payload, "entity_type") or (entity or {}).get("entity_type") or GdsParsedEntityType.UNKNOWN.value
        before = _get(payload, "before_json", {}) or (entity or {}).get("normalized_json") or {}
        after = _get(payload, "after_json", {}) or {}
        correction_type = _enum_value(_get(payload, "correction_type"))
        correction = GdsParseCorrection(
            agency_id=agency_id,
            parser_run_id=parser_run_id,
            parsed_entity_id=entity_id,
            booking_import_draft_id=_get(payload, "booking_import_draft_id") or run.get("booking_import_draft_id"),
            correction_type=correction_type,
            entity_type=entity_type,
            before_json=before,
            after_json=after,
            correction_reason=_get(payload, "correction_reason"),
            created_by_user_id=user.get("id"),
        )
        created = await self.db.collection("gds_parse_corrections").insert_one(correction.model_dump(mode="json"))

        updated_entity = None
        if entity:
            status_map = {
                GdsParseCorrectionType.ACCEPT.value: GdsParsedEntityStatus.ACCEPTED.value,
                GdsParseCorrectionType.CORRECT.value: GdsParsedEntityStatus.CORRECTED.value,
                GdsParseCorrectionType.REJECT.value: GdsParsedEntityStatus.REJECTED.value,
                GdsParseCorrectionType.IGNORE.value: GdsParsedEntityStatus.IGNORED.value,
            }
            updates = {
                "status": status_map.get(correction_type, entity.get("status")),
                "correction_json": after or before,
                "corrected_by_user_id": user.get("id"),
                "corrected_at": _now(),
            }
            if correction_type == GdsParseCorrectionType.CORRECT.value and after:
                updates["normalized_json"] = after
            updated_entity = await self.db.collection("gds_parsed_entities").update_one({"agency_id": agency_id, "id": entity_id}, updates)

        return {"correction": created, "entity": updated_entity, "manual_review_required_for_low_confidence": True}

    async def create_training_sample_from_run(self, agency_id: str, parser_run_id: str, payload: Any, user: dict) -> dict[str, Any] | None:
        run = await self.get_parser_run(agency_id, parser_run_id)
        if not run:
            return None
        scope = _enum_value(_get(payload, "scope", GdsParseSampleScope.AGENCY.value)) or GdsParseSampleScope.AGENCY.value
        if scope == GdsParseSampleScope.PLATFORM.value and user.get("global_role") not in {"platform_owner", "platform_admin"}:
            scope = GdsParseSampleScope.AGENCY.value
        expected = _get(payload, "expected_payload_json", {}) or run.get("normalized_preview_json") or {}
        sample = GdsParseSample(
            agency_id=agency_id if scope == GdsParseSampleScope.AGENCY.value else None,
            created_by_user_id=user.get("id"),
            scope=scope,
            booking_import_draft_id=run.get("booking_import_draft_id"),
            parser_run_id=parser_run_id,
            provider_family=run.get("provider_family_detected") or GdsProviderFamily.UNKNOWN.value,
            input_format=run.get("input_format_detected") or GdsInputFormat.UNKNOWN.value,
            sample_title=_get(payload, "sample_title") or f"Parser run {parser_run_id}",
            mode=GdsParseSampleMode.PNR,
            raw_text=run.get("input_excerpt") or "",
            parsed_json=run.get("normalized_preview_json") or {},
            expected_payload_json=expected,
            corrected_payload_json=_get(payload, "corrected_payload_json"),
            sample_status=GdsParseSampleStatus.DRAFT,
            difficulty=_enum_value(_get(payload, "difficulty", GdsParseSampleDifficulty.MEDIUM.value)),
            tags=_get(payload, "tags", []) or [],
            redaction_status=_enum_value(_get(payload, "redaction_status", GdsParseSampleRedactionStatus.NOT_REQUIRED.value)),
            source=GdsParseSampleSource.PARSER_RUN,
            notes="Created from governed parser run.",
        )
        created = await self.db.collection("gds_parse_training_samples").insert_one(sample.model_dump(mode="json"))
        return {"sample": created}

    async def list_training_samples(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        items = await self.db.collection("gds_parse_training_samples").find_many()
        for key, value in (filters or {}).items():
            if value not in {None, ""}:
                items = [item for item in items if item.get(key) == value]
        items.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return {"items": items}

    async def review_training_sample(self, sample_id: str, payload: Any, user: dict) -> dict[str, Any] | None:
        sample = await self.db.collection("gds_parse_training_samples").find_one({"id": sample_id})
        if not sample:
            return None
        updates = {
            "sample_status": _enum_value(_get(payload, "sample_status")),
            "reviewed_by_user_id": user.get("id"),
            "reviewed_at": _now(),
        }
        if _get(payload, "corrected_payload_json") is not None:
            updates["corrected_payload_json"] = _get(payload, "corrected_payload_json")
        if _get(payload, "redaction_status") is not None:
            updates["redaction_status"] = _enum_value(_get(payload, "redaction_status"))
        if _get(payload, "review_notes") is not None:
            updates["notes"] = _get(payload, "review_notes")
        updated = await self.db.collection("gds_parse_training_samples").update_one({"id": sample_id}, updates)
        return {"sample": updated}

    async def evaluate_parser_version(self, payload: Any, user: dict) -> dict[str, Any]:
        parser_profile_id = _get(payload, "parser_profile_id")
        parser_version_id = _get(payload, "parser_version_id")
        requested_sample_ids = _get(payload, "sample_ids", []) or []
        profile = await self.db.collection("gds_parser_profiles").find_one({"id": parser_profile_id})
        version = await self.db.collection("gds_parser_versions").find_one({"id": parser_version_id, "parser_profile_id": parser_profile_id})
        samples = await self.db.collection("gds_parse_training_samples").find_many()
        if requested_sample_ids:
            samples = [item for item in samples if item.get("id") in set(requested_sample_ids)]
        else:
            samples = [item for item in samples if item.get("sample_status") in {GdsParseSampleStatus.APPROVED.value, GdsParseSampleStatus.PROMOTED.value}]

        results: list[dict[str, Any]] = []
        confidence_total = 0.0
        exact = 0
        partial = 0
        failed = 0
        warnings: list[dict[str, Any]] = []
        if not profile or not version:
            warnings.append(_warning("parser_version_missing", "Parser profile or version was not found.", "error"))

        for sample in samples:
            parsed = self._parse_core(sample.get("raw_text") or "", profile or {}, version or {})
            expected = sample.get("corrected_payload_json") or sample.get("expected_payload_json") or sample.get("parsed_json") or {}
            score = self._match_score(parsed["preview"], expected)
            confidence_total += parsed["overall_confidence"]
            if score >= 1.0:
                exact += 1
                match_status = "exact"
            elif score > 0:
                partial += 1
                match_status = "partial"
            else:
                failed += 1
                match_status = "failed"
            results.append(
                {
                    "sample_id": sample.get("id"),
                    "match_status": match_status,
                    "match_score": score,
                    "confidence": parsed["overall_confidence"],
                    "warnings": parsed["warnings"],
                }
            )

        sample_count = len(samples)
        average = confidence_total / sample_count if sample_count else 0.0
        evaluation = GdsParserEvaluationRun(
            parser_profile_id=parser_profile_id,
            parser_version_id=parser_version_id,
            sample_ids=[item.get("id") for item in samples if item.get("id")],
            evaluation_status=GdsParserEvaluationStatus.COMPLETED if profile and version else GdsParserEvaluationStatus.FAILED,
            sample_count=sample_count,
            exact_match_count=exact,
            partial_match_count=partial,
            failed_count=failed,
            average_confidence=round(average, 3),
            passenger_accuracy=self._ratio(results, "passengers"),
            segment_accuracy=self._ratio(results, "segments"),
            ticket_accuracy=self._ratio(results, "tickets"),
            emd_accuracy=self._ratio(results, "emds"),
            ssr_osi_accuracy=self._ratio(results, "ssr_osi"),
            pricing_accuracy=self._ratio(results, "pricing"),
            warnings_json=warnings,
            results_json=results,
            created_by_user_id=user.get("id"),
        )
        created = await self.db.collection("gds_parser_evaluation_runs").insert_one(evaluation.model_dump(mode="json"))
        return {"evaluation": created, "external_ai_parser_disabled": True}

    async def list_evaluation_runs(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        items = await self.db.collection("gds_parser_evaluation_runs").find_many()
        for key, value in (filters or {}).items():
            if value not in {None, ""}:
                items = [item for item in items if item.get(key) == value]
        items.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return {"items": items}

    async def _select_profile(self, detected_provider_family: str, parser_profile_id: str | None = None) -> dict[str, Any] | None:
        if parser_profile_id:
            return await self.db.collection("gds_parser_profiles").find_one({"id": parser_profile_id})
        profiles = await self.db.collection("gds_parser_profiles").find_many()
        active = [item for item in profiles if item.get("active", True)]
        preferred = [
            item
            for item in active
            if item.get("provider_family") == detected_provider_family and item.get("default_for_provider_family")
        ]
        if preferred:
            return preferred[0]
        generic = [item for item in active if item.get("provider_family") == GdsProviderFamily.GENERIC_GDS.value]
        return generic[0] if generic else (active[0] if active else None)

    async def _select_version(self, profile: dict[str, Any] | None, parser_version_id: str | None = None) -> dict[str, Any] | None:
        if parser_version_id:
            return await self.db.collection("gds_parser_versions").find_one({"id": parser_version_id})
        if not profile:
            return None
        versions = await self.db.collection("gds_parser_versions").find_many({"parser_profile_id": profile["id"]})
        active = [item for item in versions if item.get("status") == GdsParserVersionStatus.ACTIVE.value]
        if active:
            return active[0]
        return versions[0] if versions else None

    def _parse_core(self, raw_text: str, profile: dict[str, Any], version: dict[str, Any]) -> dict[str, Any]:
        lines = [line.rstrip() for line in (raw_text or "").splitlines()]
        joined = "\n".join(lines)
        warnings: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        entities: list[dict[str, Any]] = []

        if not raw_text.strip():
            errors.append(_warning("empty_input", "No input text was supplied.", "error"))
            preview = self._preview(None, [], [], [], [], [], [], {}, [], [], warnings, 0.0, GdsParserRunStatus.FAILED.value)
            return {"preview": preview, "entities": entities, "warnings": warnings, "errors": errors, "overall_confidence": 0.0, "parse_status": GdsParserRunStatus.FAILED.value, "extracted_payload": {}}

        locator = self._record_locator(joined)
        passengers = self._passengers(lines)
        segments = self._segments(lines)
        ticket_numbers = self._number_matches(joined, r"\b(?:TKT|TK|ETKT|E-TICKET|TICKET)[\s:/#-]*(\d{3}[- ]?\d{10})\b")
        emd_numbers = self._number_matches(joined, r"\b(?:EMD|EMDS)[\s:/#-]*(\d{3}[- ]?\d{10})\b")
        ssr = self._ssr(lines)
        osi = self._osi(lines)
        pricing = self._pricing(joined)
        fare_basis = self._fare_basis(lines)
        contacts = self._contacts(lines)
        remarks = self._remarks(lines)

        if not locator:
            warnings.append(_warning("locator_not_found", "No obvious PNR/record locator was found."))
        if not passengers:
            warnings.append(_warning("passengers_not_found", "No obvious passenger names were found."))
        if not segments:
            warnings.append(_warning("segments_not_found", "No obvious flight segments were found."))
        if not ticket_numbers and "TICKET" in joined.upper():
            warnings.append(_warning("ticket_number_ambiguous", "Ticket text was present but no full ticket number was extracted."))
        if not emd_numbers and "EMD" in joined.upper():
            warnings.append(_warning("emd_number_ambiguous", "EMD text was present but no full EMD number was extracted."))

        for index, passenger in enumerate(passengers, start=1):
            entities.append(self._entity(GdsParsedEntityType.PASSENGER.value, f"passenger-{index}", passenger.get("raw_line"), passenger, passenger.get("confidence", 0.82)))
        for index, segment in enumerate(segments, start=1):
            entities.append(self._entity(GdsParsedEntityType.SEGMENT.value, f"segment-{index}", segment.get("raw_line"), segment, segment.get("confidence", 0.78)))
        for index, number in enumerate(ticket_numbers, start=1):
            entities.append(self._entity(GdsParsedEntityType.TICKET.value, f"ticket-{index}", number, {"ticket_number": number, "number": number}, 0.93))
        for index, number in enumerate(emd_numbers, start=1):
            entities.append(self._entity(GdsParsedEntityType.EMD.value, f"emd-{index}", number, {"emd_number": number, "number": number}, 0.93))
        for index, item in enumerate(ssr, start=1):
            entities.append(self._entity(GdsParsedEntityType.SSR.value, f"ssr-{index}", item.get("line"), item, item.get("confidence", 0.76)))
        for index, item in enumerate(osi, start=1):
            entities.append(self._entity(GdsParsedEntityType.OSI.value, f"osi-{index}", item.get("line"), item, item.get("confidence", 0.76)))
        if pricing:
            entities.append(self._entity(GdsParsedEntityType.PRICING.value, "pricing-1", pricing.get("raw_text") or "", pricing, pricing.get("confidence", 0.68)))
        for index, item in enumerate(fare_basis, start=1):
            entities.append(self._entity(GdsParsedEntityType.FARE_BASIS.value, f"fare-basis-{index}", item.get("line"), item, 0.7))
        for index, item in enumerate(contacts, start=1):
            entities.append(self._entity(GdsParsedEntityType.CONTACT.value, f"contact-{index}", item.get("line"), item, 0.64))
        for index, item in enumerate(remarks, start=1):
            entities.append(self._entity(GdsParsedEntityType.REMARK.value, f"remark-{index}", item.get("line"), item, 0.62))

        confidence = self._overall_confidence(locator, passengers, segments, ticket_numbers, emd_numbers, ssr, osi, pricing, warnings)
        warning_threshold = float(profile.get("confidence_threshold_warning") or 0.60)
        import_threshold = float(profile.get("confidence_threshold_import") or 0.80)
        if confidence < warning_threshold:
            parse_status = GdsParserRunStatus.MANUAL_REVIEW_REQUIRED.value
            warnings.append(_warning("low_confidence_manual_review", "Low-confidence parse requires manual review before import."))
        elif confidence < import_threshold or warnings:
            parse_status = GdsParserRunStatus.PARTIAL.value
            warnings.append(_warning("partial_parse_review_required", "Parsed data should be reviewed before any internal mirror import."))
        else:
            parse_status = GdsParserRunStatus.PARSED.value

        preview = self._preview(locator, passengers, segments, ticket_numbers, emd_numbers, ssr, osi, pricing, fare_basis, contacts + remarks, warnings, confidence, parse_status)
        extracted_payload = {
            "record_locator": locator,
            "passengers": passengers,
            "segments": segments,
            "ticket_numbers": ticket_numbers,
            "emd_numbers": emd_numbers,
            "ssr": ssr,
            "osi": osi,
            "pricing": pricing,
            "fare_basis": fare_basis,
            "contacts": contacts,
            "remarks": remarks,
            "parser": PHASE_LABEL,
            "profile_key": profile.get("profile_key"),
            "version_label": version.get("version_label"),
        }
        return {
            "preview": preview,
            "entities": entities,
            "warnings": warnings,
            "errors": errors,
            "overall_confidence": confidence,
            "parse_status": parse_status,
            "extracted_payload": extracted_payload,
        }

    def _record_locator(self, text: str) -> str | None:
        for pattern in [
            r"\b(?:PNR|LOCATOR|RECORD\s+LOCATOR|CONFIRMATION)[\s:#-]*([A-Z0-9]{5,8})\b",
            r"\b([A-Z0-9]{6})\s+(?:PNR|LOCATOR)\b",
            r"\bRL[\s:/-]*([A-Z0-9]{5,8})\b",
        ]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None

    def _passengers(self, lines: list[str]) -> list[dict[str, Any]]:
        passengers: list[dict[str, Any]] = []
        patterns = [
            r"(?:PAX|PASSENGER|NM\d*|\d+\.)\s*([A-Z][A-Z'\-]+)/([A-Z][A-Z'\- ]+)",
            r"\b\d+\.\d+\s*([A-Z][A-Z'\-]+)/([A-Z][A-Z'\- ]+)",
            r"\bNAME[\s:-]+([A-Z][A-Z'\-]+)/([A-Z][A-Z'\- ]+)",
        ]
        for line in lines:
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if not match:
                    continue
                last_name = match.group(1).upper()
                first_name = match.group(2).strip().upper()
                passenger = {
                    "id": f"import-pax-{len(passengers) + 1}",
                    "first_name": first_name.title(),
                    "last_name": last_name.title(),
                    "display_name": f"{first_name.title()} {last_name.title()}",
                    "raw_line": line.strip(),
                    "confidence": 0.84 if "/" in line else 0.72,
                }
                passengers.append(passenger)
                break
        return passengers

    def _segments(self, lines: list[str]) -> list[dict[str, Any]]:
        segments: list[dict[str, Any]] = []
        patterns = [
            re.compile(
                r"\b(?P<airline>[A-Z0-9]{2})\s?(?P<flight>\d{2,4})\s+(?P<rbd>[A-Z])?\s*(?P<date>\d{1,2}[A-Z]{3})?\s+(?P<origin>[A-Z]{3})(?P<destination>[A-Z]{3})\s*(?P<status>HK|HL|KK|RR|TK|UN|UC|SS|NN)?\d?\s*(?P<depart>\d{3,4})?\s*(?P<arrive>\d{3,4})?",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(?P<airline>[A-Z0-9]{2})\s+(?P<flight>\d{2,4})\s+(?P<origin>[A-Z]{3})\s+(?P<destination>[A-Z]{3})\s+(?P<date>\d{1,2}[A-Z]{3})?\s*(?P<depart>\d{3,4})?\s*(?P<arrive>\d{3,4})?",
                re.IGNORECASE,
            ),
        ]
        for line in lines:
            for pattern in patterns:
                match = pattern.search(line)
                if not match:
                    continue
                groups = match.groupdict()
                segment = _compact(
                    {
                        "id": f"import-seg-{len(segments) + 1}",
                        "sequence": len(segments) + 1,
                        "marketing_airline_code": (groups.get("airline") or "").upper(),
                        "flight_number": groups.get("flight"),
                        "booking_class": (groups.get("rbd") or "").upper() or None,
                        "departure_date": (groups.get("date") or "").upper() or None,
                        "departure_time": groups.get("depart"),
                        "arrival_time": groups.get("arrive"),
                        "origin_airport_code": (groups.get("origin") or "").upper(),
                        "destination_airport_code": (groups.get("destination") or "").upper(),
                        "status": (groups.get("status") or "").upper() or None,
                        "raw_line": line.strip(),
                        "confidence": 0.86 if groups.get("date") and groups.get("status") else 0.74,
                    }
                )
                segments.append(segment)
                break
        return segments

    def _number_matches(self, text: str, pattern: str) -> list[str]:
        return sorted({match.replace(" ", "-") for match in re.findall(pattern, text, re.IGNORECASE)})

    def _ssr(self, lines: list[str]) -> list[dict[str, Any]]:
        rows = []
        for line in lines:
            if not line.strip().upper().startswith("SSR"):
                continue
            match = re.match(r"SSR\s+([A-Z0-9]{2,4})\s*([A-Z0-9]{0,3})?\s*(.*)", line.strip(), re.IGNORECASE)
            rows.append(
                _compact(
                    {
                        "line": line.strip(),
                        "ssr_code": (match.group(1).upper() if match else None),
                        "airline_code": (match.group(2).upper() if match and match.group(2) else None),
                        "free_text": (match.group(3).strip() if match else line.strip()),
                        "confidence": 0.78 if match else 0.62,
                    }
                )
            )
        return rows

    def _osi(self, lines: list[str]) -> list[dict[str, Any]]:
        rows = []
        for line in lines:
            if not line.strip().upper().startswith("OSI"):
                continue
            match = re.match(r"OSI\s+([A-Z0-9]{0,3})?\s*(.*)", line.strip(), re.IGNORECASE)
            rows.append(
                _compact(
                    {
                        "line": line.strip(),
                        "airline_code": (match.group(1).upper() if match and match.group(1) else None),
                        "text": (match.group(2).strip() if match else line.strip()),
                        "confidence": 0.76 if match else 0.62,
                    }
                )
            )
        return rows

    def _pricing(self, text: str) -> dict[str, Any]:
        upper = text.upper()
        match = re.search(r"\b(?:TOTAL|TTL|GRAND TOTAL)\s*([A-Z]{3})?\s*([0-9]+(?:\.[0-9]{2})?)\b", upper)
        if not match:
            match = re.search(r"\b([A-Z]{3})\s*([0-9]+(?:\.[0-9]{2})?)\s*(?:TOTAL|TTL)\b", upper)
        if not match:
            return {}
        currency = match.group(1) if match.group(1) and match.group(1).isalpha() else None
        amount = match.group(2)
        return _compact({"currency": currency, "total_amount": amount, "raw_text": match.group(0), "confidence": 0.68})

    def _fare_basis(self, lines: list[str]) -> list[dict[str, Any]]:
        rows = []
        for line in lines:
            match = re.search(r"\b(?:FARE\s*BASIS|FB)\s*[:/-]?\s*([A-Z0-9]{3,15})\b", line, re.IGNORECASE)
            if match:
                rows.append({"fare_basis": match.group(1).upper(), "line": line.strip()})
        return rows

    def _contacts(self, lines: list[str]) -> list[dict[str, Any]]:
        rows = []
        for line in lines:
            upper = line.strip().upper()
            if upper.startswith(("AP ", "APE", "APM", "PHONE", "EMAIL")) or "@" in line:
                rows.append({"line": line.strip(), "contact_text": line.strip()})
        return rows

    def _remarks(self, lines: list[str]) -> list[dict[str, Any]]:
        rows = []
        for line in lines:
            upper = line.strip().upper()
            if upper.startswith(("RM ", "RMK", "REMARK", "RC ")):
                rows.append({"line": line.strip(), "remark_text": line.strip()})
        return rows

    def _entity(self, entity_type: str, entity_key: str, source_text: str | None, normalized_json: dict[str, Any], confidence: float) -> dict[str, Any]:
        normalized_json = dict(normalized_json or {})
        normalized_json["summary"] = _summary_for_entity(entity_type, normalized_json)
        return {
            "entity_type": entity_type,
            "entity_key": entity_key,
            "source_text": source_text or "",
            "normalized_json": normalized_json,
            "confidence": round(float(confidence or 0.0), 3),
        }

    def _overall_confidence(
        self,
        locator: str | None,
        passengers: list[dict[str, Any]],
        segments: list[dict[str, Any]],
        ticket_numbers: list[str],
        emd_numbers: list[str],
        ssr: list[dict[str, Any]],
        osi: list[dict[str, Any]],
        pricing: dict[str, Any],
        warnings: list[dict[str, Any]],
    ) -> float:
        scores = []
        if locator:
            scores.append(0.86)
        scores.extend(item.get("confidence", 0.72) for item in passengers)
        scores.extend(item.get("confidence", 0.74) for item in segments)
        scores.extend([0.93] * (len(ticket_numbers) + len(emd_numbers)))
        scores.extend(item.get("confidence", 0.72) for item in ssr + osi)
        if pricing:
            scores.append(pricing.get("confidence", 0.68))
        if not scores:
            return 0.18
        confidence = sum(scores) / len(scores)
        if warnings:
            confidence -= min(0.18, len(warnings) * 0.035)
        return round(max(0.0, min(confidence, 0.98)), 3)

    def _preview(
        self,
        locator: str | None,
        passengers: list[dict[str, Any]],
        segments: list[dict[str, Any]],
        ticket_numbers: list[str],
        emd_numbers: list[str],
        ssr: list[dict[str, Any]],
        osi: list[dict[str, Any]],
        pricing: dict[str, Any],
        fare_basis: list[dict[str, Any]],
        contacts_and_remarks: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        confidence: float,
        parse_status: str,
    ) -> dict[str, Any]:
        return {
            "record_locator": locator,
            "passengers": passengers,
            "segments": segments,
            "ticket_numbers": ticket_numbers,
            "emd_numbers": emd_numbers,
            "ssr": ssr,
            "osi": osi,
            "pricing": pricing,
            "fare_basis": fare_basis,
            "contacts_and_remarks": contacts_and_remarks,
            "warnings": warnings,
            "confidence": "high" if confidence >= 0.8 else ("medium" if confidence >= 0.6 else "low"),
            "overall_confidence": confidence,
            "parse_status": parse_status,
            "parser": PHASE_LABEL,
            "manual_review_required": parse_status in {GdsParserRunStatus.PARTIAL.value, GdsParserRunStatus.MANUAL_REVIEW_REQUIRED.value},
            "explicit_import_required": True,
        }

    def _match_score(self, parsed: dict[str, Any], expected: dict[str, Any]) -> float:
        checks = [
            (parsed.get("record_locator"), expected.get("record_locator")),
            (len(parsed.get("passengers") or []), len(expected.get("passengers") or [])),
            (len(parsed.get("segments") or []), len(expected.get("segments") or [])),
            (len(parsed.get("ticket_numbers") or []), len(expected.get("ticket_numbers") or [])),
            (len(parsed.get("emd_numbers") or []), len(expected.get("emd_numbers") or [])),
        ]
        if not checks:
            return 0.0
        matches = 0
        considered = 0
        for actual, wanted in checks:
            if wanted in {None, "", 0}:
                continue
            considered += 1
            if actual == wanted:
                matches += 1
        return round(matches / considered, 3) if considered else 0.0

    def _ratio(self, results: list[dict[str, Any]], key: str) -> float | None:
        if not results:
            return None
        successful = len([item for item in results if item.get("match_status") in {"exact", "partial"}])
        return round(successful / len(results), 3)
