from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    AirlinePolicyApprovedKnowledgeRecord,
    AirlinePolicyApprovedKnowledgeStatus,
    AirlinePolicyCandidateStatus,
    AirlinePolicyCommunicationType,
    AirlinePolicyCorrectionType,
    AirlinePolicyDirectConnecting,
    AirlinePolicyEmdType,
    AirlinePolicyExceptionType,
    AirlinePolicyExtractedCommunicationRule,
    AirlinePolicyExtractedEmdRule,
    AirlinePolicyExtractedException,
    AirlinePolicyExtractedPrice,
    AirlinePolicyExtractedRule,
    AirlinePolicyExtractionRun,
    AirlinePolicyExtractionStatus,
    AirlinePolicyGdsSystem,
    AirlinePolicyIngestionStatus,
    AirlinePolicyKnowledgeType,
    AirlinePolicyMandatoryOptional,
    AirlinePolicyPriceBasis,
    AirlinePolicyPriceType,
    AirlinePolicyRedactionStatus,
    AirlinePolicyReviewCorrection,
    AirlinePolicyReviewTargetType,
    AirlinePolicyRuleType,
    AirlinePolicyScope,
    AirlinePolicySection,
    AirlinePolicySectionCategory,
    AirlinePolicySource,
    AirlinePolicySourceType,
)


PHASE_LABEL = "phase_36_7_airline_policy_ingestion_foundation"
EXTRACTOR_VERSION = "phase_36_7_deterministic_v1"

RULE_COLLECTIONS = {
    AirlinePolicyReviewTargetType.RULE.value: "airline_policy_extracted_rules",
    AirlinePolicyReviewTargetType.PRICE.value: "airline_policy_extracted_prices",
    AirlinePolicyReviewTargetType.COMMUNICATION_RULE.value: "airline_policy_extracted_communication_rules",
    AirlinePolicyReviewTargetType.EMD_RULE.value: "airline_policy_extracted_emd_rules",
    AirlinePolicyReviewTargetType.EXCEPTION.value: "airline_policy_extracted_exceptions",
}

KNOWLEDGE_TYPE_BY_TARGET = {
    AirlinePolicyReviewTargetType.RULE.value: AirlinePolicyKnowledgeType.APPLICABILITY_RULE.value,
    AirlinePolicyReviewTargetType.PRICE.value: AirlinePolicyKnowledgeType.PRICING_RULE.value,
    AirlinePolicyReviewTargetType.COMMUNICATION_RULE.value: AirlinePolicyKnowledgeType.COMMUNICATION_RULE.value,
    AirlinePolicyReviewTargetType.EMD_RULE.value: AirlinePolicyKnowledgeType.EMD_RULE.value,
    AirlinePolicyReviewTargetType.EXCEPTION.value: AirlinePolicyKnowledgeType.EXCEPTION_RULE.value,
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get(payload: Any, key: str, default: Any = None) -> Any:
    if hasattr(payload, key):
        return getattr(payload, key)
    if isinstance(payload, dict):
        return payload.get(key, default)
    return default


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _warning(code: str, message: str, severity: str = "warning") -> dict[str, str]:
    return {"code": code, "message": message, "severity": severity}


def _compact(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if value is not None and value != "" and value != [] and value != {}}


def _raw_hash(raw_text: str) -> str:
    return hashlib.sha256((raw_text or "").encode("utf-8")).hexdigest()


def _line_excerpt(line: str, limit: int = 420) -> str:
    text = re.sub(r"\s+", " ", line or "").strip()
    return text[:limit]


def _line_has(line: str, *keywords: str) -> bool:
    upper = (line or "").upper()
    return any(keyword.upper() in upper for keyword in keywords)


def _float_amount(value: str) -> float | None:
    try:
        return float(value.replace(",", "."))
    except (TypeError, ValueError):
        return None


def _provider_from_text(text: str) -> str:
    upper = text.upper()
    if "AMADEUS" in upper or " SR " in f" {upper} ":
        return AirlinePolicyGdsSystem.AMADEUS.value
    if "SABRE" in upper or "3SSR" in upper:
        return AirlinePolicyGdsSystem.SABRE.value
    if "TRAVELPORT" in upper or "GALILEO" in upper:
        return AirlinePolicyGdsSystem.TRAVELPORT.value
    if "GDS" in upper or re.search(r"\bSSR\s+[A-Z0-9]{3,4}\b", upper):
        return AirlinePolicyGdsSystem.GENERIC.value
    return AirlinePolicyGdsSystem.UNKNOWN.value


def _category_for_text(title: str, text: str) -> str:
    haystack = f"{title}\n{text}".upper()
    if _line_has(haystack, "PRICE", "PRICING", "FEE", "EUR", "USD", "GBP", "COST", "CHARGE"):
        return AirlinePolicySectionCategory.PRICING.value
    if _line_has(haystack, "SSR", "OSI", "OTHS", "HOW TO BOOK", "BOOKING", "GDS ENTRY", "REQUEST"):
        return AirlinePolicySectionCategory.SSR_OSI.value
    if _line_has(haystack, "EMD", "RFIC", "RFISC", "ASVC", "PAYMENT", "ICW"):
        return AirlinePolicySectionCategory.EMD_PAYMENT.value
    if _line_has(haystack, "EMBARGO", "FORBIDDEN", "NOT PERMITTED", "RESTRICT", "NO CONNECTION", "TRANSFER", "OVERNIGHT"):
        return AirlinePolicySectionCategory.EXCEPTIONS.value
    if _line_has(haystack, "AGE", "YEARS", "CHILD", "MINOR", "UMNR", "ADOLESCENT", "YOUNG PASSENGER", "ELIGIBLE"):
        return AirlinePolicySectionCategory.APPLICABILITY.value
    if _line_has(haystack, "DOCUMENT", "FORM", "PASSPORT", "VISA", "CONSENT"):
        return AirlinePolicySectionCategory.DOCUMENTS.value
    if _line_has(haystack, "NDC", "DISTRIBUTION", "PORTAL"):
        return AirlinePolicySectionCategory.DISTRIBUTION.value
    if _line_has(haystack, "CHANGE", "REFUND", "VOID", "REISSUE"):
        return AirlinePolicySectionCategory.CHANGES_REFUNDS.value
    if _line_has(haystack, "AIRPORT", "ARRIVAL", "HANDOVER", "GUARDIAN"):
        return AirlinePolicySectionCategory.AIRPORT_HANDLING.value
    if _line_has(haystack, "SERVICE", "OPTIONAL", "MANDATORY"):
        return AirlinePolicySectionCategory.SERVICES.value
    return AirlinePolicySectionCategory.GENERAL.value


def _service_family(source: dict[str, Any], payload: Any = None) -> str:
    family = _get(payload, "service_family") if payload is not None else None
    if family:
        return str(family).strip()
    if source.get("service_family"):
        return str(source["service_family"]).strip()
    upper = str(source.get("raw_text") or "").upper()
    if any(token in upper for token in ["UMNR", "UNACCOMPANIED MINOR", "KIDS SOLO", "YOUNG PASSENGER", "ADOLESCENT"]):
        return "unaccompanied_minor"
    if any(token in upper for token in ["WCHR", "WCHS", "WCHC", "PRM", "WHEELCHAIR"]):
        return "mobility_assistance"
    if any(token in upper for token in ["PETC", "AVIH", "PET"]):
        return "pet_travel"
    return "general"


def _service_domain(source: dict[str, Any], payload: Any = None) -> str:
    domain = _get(payload, "service_domain") if payload is not None else None
    return str(domain or source.get("service_domain") or "special_services")


def _service_variant(text: str) -> str | None:
    upper = text.upper()
    if "UMNR" in upper:
        return "UMNR"
    if "KIDS SOLO" in upper:
        return "Kids Solo"
    if "YOUNG PASSENGER" in upper:
        return "Young Passenger"
    for code in ["WCHR", "WCHS", "WCHC", "PETC", "AVIH", "MEDA", "BLND", "DEAF"]:
        if code in upper:
            return code
    return None


def _confidence_for_line(line: str, base: float = 0.68) -> float:
    value = base
    if re.search(r"\b(?:SSR|OSI|EMD|RFIC|RFISC|EUR|USD|GBP|UMNR)\b", line.upper()):
        value += 0.12
    if len(line.strip()) > 16:
        value += 0.04
    return min(value, 0.92)


class AirlinePolicyIngestionService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def create_policy_source(self, payload: Any, user: dict) -> dict[str, Any]:
        raw_text = str(_get(payload, "raw_text") or "").strip()
        scope = _enum_value(_get(payload, "scope", AirlinePolicyScope.PLATFORM.value))
        agency_id = _get(payload, "agency_id")
        warnings: list[dict[str, str]] = []
        if len(raw_text) < 40:
            warnings.append(_warning("short_policy_text", "Policy text is short; extraction will likely require manual review."))
        if not (_get(payload, "airline_id") or _get(payload, "airline_iata_code") or _get(payload, "airline_name_snapshot")):
            warnings.append(_warning("airline_context_missing", "Airline identity is not fully linked; keep source under review."))

        source = AirlinePolicySource(
            scope=scope,
            agency_id=agency_id,
            airline_id=_get(payload, "airline_id"),
            airline_iata_code=(str(_get(payload, "airline_iata_code") or "").upper() or None),
            airline_name_snapshot=_get(payload, "airline_name_snapshot"),
            service_domain=_get(payload, "service_domain"),
            service_family=_get(payload, "service_family"),
            source_type=_enum_value(_get(payload, "source_type", AirlinePolicySourceType.PASTED_TEXT.value)),
            source_title=_get(payload, "source_title"),
            source_url=_get(payload, "source_url"),
            source_date=_get(payload, "source_date"),
            effective_from=_get(payload, "effective_from"),
            effective_to=_get(payload, "effective_to"),
            raw_text=raw_text,
            raw_text_hash=_raw_hash(raw_text),
            language=_get(payload, "language", "en") or "en",
            redaction_status=AirlinePolicyRedactionStatus.NOT_REQUIRED,
            ingestion_status=AirlinePolicyIngestionStatus.DRAFT,
            warnings_json=warnings,
            created_by_user_id=user.get("id"),
        )
        created = await self.db.collection("airline_policy_sources").insert_one(source.model_dump(mode="json"))
        return {
            "policy_source": created,
            "external_ai_policy_extraction_disabled": True,
            "auto_promotion_disabled": True,
            "platform_review_required_for_global_knowledge": True,
        }

    async def list_policy_sources(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        items = await self.db.collection("airline_policy_sources").find_many()
        for key, value in (filters or {}).items():
            if value not in {None, ""}:
                items = [item for item in items if item.get(key) == value]
        items.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return {"items": items}

    async def get_policy_source(self, policy_source_id: str) -> dict[str, Any] | None:
        return await self.db.collection("airline_policy_sources").find_one({"id": policy_source_id})

    async def detect_sections(self, policy_source_id: str, user: dict) -> dict[str, Any] | None:
        source = await self.get_policy_source(policy_source_id)
        if not source:
            return None
        existing = await self.db.collection("airline_policy_sections").find_many({"policy_source_id": policy_source_id})
        if existing:
            existing.sort(key=lambda item: item.get("section_order", 0))
            return {"policy_source": source, "sections": existing, "created_count": 0}

        sections = self._detect_section_payloads(source)
        created = []
        for index, item in enumerate(sections, start=1):
            section = AirlinePolicySection(
                policy_source_id=policy_source_id,
                airline_id=source.get("airline_id"),
                section_key=item["section_key"],
                section_title=item["section_title"],
                section_order=index,
                section_text=item["section_text"],
                detected_category=item["detected_category"],
                confidence=item["confidence"],
                warnings_json=item.get("warnings_json") or [],
            )
            created.append(await self.db.collection("airline_policy_sections").insert_one(section.model_dump(mode="json")))
        return {"policy_source": source, "sections": created, "created_count": len(created)}

    def _detect_section_payloads(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        raw_text = source.get("raw_text") or ""
        lines = [line.rstrip() for line in raw_text.splitlines()]
        chunks: list[dict[str, Any]] = []
        current_title = "Policy text"
        current_lines: list[str] = []

        def flush() -> None:
            text = "\n".join(line for line in current_lines if line.strip()).strip()
            if not text:
                return
            key = re.sub(r"[^a-z0-9]+", "_", current_title.lower()).strip("_") or f"section_{len(chunks) + 1}"
            category = _category_for_text(current_title, text)
            chunks.append(
                {
                    "section_key": key,
                    "section_title": current_title,
                    "section_text": text,
                    "detected_category": category,
                    "confidence": 0.76 if current_title != "Policy text" else 0.62,
                    "warnings_json": [] if current_title != "Policy text" else [_warning("implicit_section", "No explicit section heading was detected for this block.")],
                }
            )

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            heading_like = (
                len(stripped) <= 80
                and (
                    stripped.endswith(":")
                    or re.match(r"^\d+[\).]\s+[A-Za-z]", stripped)
                    or stripped.upper() in {
                        "GENERAL",
                        "APPLICABILITY",
                        "HOW TO BOOK",
                        "PRICING",
                        "SSR/OSI",
                        "SSR / OSI",
                        "EMD",
                        "PAYMENT",
                        "EXCEPTIONS",
                        "CHANGES/REFUNDS",
                        "DOCUMENTS",
                    }
                )
            )
            if heading_like and current_lines:
                flush()
                current_lines = []
                current_title = re.sub(r"^\d+[\).]\s*", "", stripped).rstrip(":")
            elif heading_like and not current_lines:
                current_title = re.sub(r"^\d+[\).]\s*", "", stripped).rstrip(":")
            else:
                current_lines.append(stripped)
        flush()
        if not chunks and raw_text.strip():
            chunks.append(
                {
                    "section_key": "policy_text",
                    "section_title": "Policy text",
                    "section_text": raw_text.strip(),
                    "detected_category": _category_for_text("Policy text", raw_text),
                    "confidence": 0.58,
                    "warnings_json": [_warning("no_section_boundaries", "No section boundaries were detected.")],
                }
            )
        return chunks

    async def run_extraction(self, policy_source_id: str, payload: Any, user: dict) -> dict[str, Any] | None:
        source = await self.get_policy_source(policy_source_id)
        if not source:
            return None
        section_result = await self.detect_sections(policy_source_id, user)
        sections = (section_result or {}).get("sections") or []
        service_domain = _service_domain(source, payload)
        service_family = _service_family(source, payload)
        run = AirlinePolicyExtractionRun(
            policy_source_id=policy_source_id,
            airline_id=source.get("airline_id"),
            extractor_version=_get(payload, "extractor_version") or EXTRACTOR_VERSION,
            warnings_json=[_warning("manual_review_required", "Extracted policy candidates require human review before approval.")],
            extraction_summary_json={
                "phase": PHASE_LABEL,
                "service_domain": service_domain,
                "service_family": service_family,
                "external_ai_used": False,
                "auto_promotion": False,
            },
            created_by_user_id=user.get("id"),
        )
        created_run = await self.db.collection("airline_policy_extraction_runs").insert_one(run.model_dump(mode="json"))

        candidates = await self._extract_candidates(created_run, source, sections, service_domain, service_family)
        warnings = list(created_run.get("warnings_json") or [])
        warnings.extend(candidates["warnings"])
        confidence_values = [
            item.get("confidence")
            for group in ["rules", "prices", "communication_rules", "emd_rules", "exceptions"]
            for item in candidates[group]
            if isinstance(item.get("confidence"), (int, float))
        ]
        overall_confidence = round(sum(confidence_values) / len(confidence_values), 2) if confidence_values else 0.0
        status_value = AirlinePolicyExtractionStatus.EXTRACTED.value if confidence_values and overall_confidence >= 0.68 else AirlinePolicyExtractionStatus.MANUAL_REVIEW_REQUIRED.value
        if warnings and status_value == AirlinePolicyExtractionStatus.EXTRACTED.value:
            status_value = AirlinePolicyExtractionStatus.PARTIAL.value
        updated_run = await self.db.collection("airline_policy_extraction_runs").update_one(
            {"id": created_run["id"]},
            {
                "extraction_status": status_value,
                "overall_confidence": overall_confidence,
                "extracted_rule_count": len(candidates["rules"]),
                "extracted_price_count": len(candidates["prices"]),
                "extracted_exception_count": len(candidates["exceptions"]),
                "extracted_ssr_osi_count": len(candidates["communication_rules"]),
                "extracted_emd_rule_count": len(candidates["emd_rules"]),
                "extracted_distribution_count": len([item for item in candidates["communication_rules"] if item.get("communication_type") in {"ndc", "gds_entry"}]),
                "warnings_json": warnings,
                "extraction_summary_json": {
                    **(created_run.get("extraction_summary_json") or {}),
                    "section_count": len(sections),
                    "candidate_counts": {
                        "rules": len(candidates["rules"]),
                        "prices": len(candidates["prices"]),
                        "communication_rules": len(candidates["communication_rules"]),
                        "emd_rules": len(candidates["emd_rules"]),
                        "exceptions": len(candidates["exceptions"]),
                    },
                },
            },
        )
        await self.db.collection("airline_policy_sources").update_one(
            {"id": policy_source_id},
            {"ingestion_status": AirlinePolicyIngestionStatus.EXTRACTED.value, "confidence_overall": overall_confidence},
        )
        return {
            "policy_source": await self.get_policy_source(policy_source_id),
            "extraction_run": updated_run,
            "sections": sections,
            "candidates": {key: candidates[key] for key in ["rules", "prices", "communication_rules", "emd_rules", "exceptions"]},
            "external_ai_policy_extraction_disabled": True,
            "auto_promotion_disabled": True,
            "platform_review_required_for_global_knowledge": True,
        }

    async def _extract_candidates(
        self,
        run: dict[str, Any],
        source: dict[str, Any],
        sections: list[dict[str, Any]],
        service_domain: str,
        service_family: str,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {"rules": [], "prices": [], "communication_rules": [], "emd_rules": [], "exceptions": [], "warnings": []}
        for section in sections:
            lines = [line.strip() for line in (section.get("section_text") or "").splitlines() if line.strip()]
            for line in lines:
                await self._maybe_rule_candidate(result, run, source, section, line, service_domain, service_family)
                await self._maybe_price_candidates(result, run, source, section, line, service_domain, service_family)
                await self._maybe_communication_candidate(result, run, source, section, line, service_domain, service_family)
                await self._maybe_emd_candidate(result, run, source, section, line, service_domain, service_family)
                await self._maybe_exception_candidate(result, run, source, section, line, service_domain, service_family)
        if not result["rules"]:
            result["warnings"].append(_warning("no_rule_candidates", "No rule candidates were detected from the source text."))
        if not result["prices"]:
            result["warnings"].append(_warning("no_price_candidates", "No obvious currency and amount rows were detected."))
        if not result["communication_rules"]:
            result["warnings"].append(_warning("no_ssr_osi_candidates", "No SSR, OSI, GDS, or NDC communication rows were detected."))
        if not result["emd_rules"]:
            result["warnings"].append(_warning("no_emd_terms", "No EMD/RFIC/RFISC payment terms were detected; keep EMD handling under manual review."))
        return result

    async def _maybe_rule_candidate(
        self,
        result: dict[str, Any],
        run: dict[str, Any],
        source: dict[str, Any],
        section: dict[str, Any],
        line: str,
        service_domain: str,
        service_family: str,
    ) -> None:
        upper = line.upper()
        rule_type: str | None = None
        condition: dict[str, Any] = {}
        action: dict[str, Any] = {}
        age_match = re.search(r"\b(?:AGE|AGED|CHILDREN?|MINORS?)?\s*(\d{1,2})\s*(?:-|TO|THROUGH)\s*(\d{1,2})\s*(?:YEARS|YRS|YO)?\b", upper)
        deadline_match = re.search(r"\b(\d{1,3})\s*(HOURS?|DAYS?)\s+(?:BEFORE|PRIOR|IN ADVANCE)", upper)
        if age_match:
            rule_type = AirlinePolicyRuleType.PASSENGER_AGE.value
            condition = {"age_min": int(age_match.group(1)), "age_max": int(age_match.group(2))}
            action = {"applies": True}
        elif deadline_match:
            rule_type = AirlinePolicyRuleType.BOOKING_DEADLINE.value
            action = {"booking_lead_time": f"{deadline_match.group(1)} {deadline_match.group(2).lower()}"}
        elif _line_has(upper, "MANDATORY", "MUST BE REQUESTED", "REQUIRED"):
            rule_type = AirlinePolicyRuleType.MANDATORY_OPTIONAL.value
            action = {"mandatory": True}
        elif _line_has(upper, "OPTIONAL", "MAY BE REQUESTED"):
            rule_type = AirlinePolicyRuleType.MANDATORY_OPTIONAL.value
            action = {"mandatory": False}
        elif _line_has(upper, "DIRECT", "CONNECTING", "CONNECTION", "TRANSFER"):
            rule_type = AirlinePolicyRuleType.CONNECTION_RESTRICTION.value
            condition = {"direct_connecting": "connecting" if "CONNECT" in upper or "TRANSFER" in upper else "direct"}
        elif _line_has(upper, "FORM", "DOCUMENT", "CONSENT", "PASSPORT", "VISA"):
            rule_type = AirlinePolicyRuleType.REQUIRED_DOCUMENT.value
            action = {"document_required": True}
        elif _line_has(upper, "GUARDIAN", "HANDOVER", "ARRIVAL", "CONTACT"):
            rule_type = AirlinePolicyRuleType.OPERATIONAL_REQUIREMENT.value
            action = {"manual_operational_requirement": True}
        elif _line_has(upper, "CHANGE", "REFUND"):
            rule_type = AirlinePolicyRuleType.REFUND_CHANGE.value
            action = {"lifecycle_note": _line_excerpt(line)}

        if not rule_type:
            return
        candidate = AirlinePolicyExtractedRule(
            extraction_run_id=run["id"],
            policy_source_id=source["id"],
            section_id=section.get("id"),
            airline_id=source.get("airline_id"),
            service_domain=service_domain,
            service_family=service_family,
            service_variant=_service_variant(line),
            rule_type=rule_type,
            normalized_condition_json=condition,
            normalized_action_json=action,
            source_excerpt=_line_excerpt(line),
            confidence=_confidence_for_line(line, 0.62),
        )
        created = await self.db.collection("airline_policy_extracted_rules").insert_one(candidate.model_dump(mode="json"))
        result["rules"].append(created)

    async def _maybe_price_candidates(
        self,
        result: dict[str, Any],
        run: dict[str, Any],
        source: dict[str, Any],
        section: dict[str, Any],
        line: str,
        service_domain: str,
        service_family: str,
    ) -> None:
        matches = []
        matches.extend((match.group(1), match.group(2)) for match in re.finditer(r"\b(EUR|USD|GBP|CHF)\s*([0-9]+(?:[.,][0-9]{1,2})?)\b", line, re.IGNORECASE))
        matches.extend((match.group(2), match.group(1)) for match in re.finditer(r"\b([0-9]+(?:[.,][0-9]{1,2})?)\s*(EUR|USD|GBP|CHF)\b", line, re.IGNORECASE))
        for currency, amount_text in matches:
            amount = _float_amount(amount_text)
            if amount is None:
                continue
            upper = line.upper()
            basis = AirlinePolicyPriceBasis.UNKNOWN.value
            if "PER PASSENGER" in upper or "PAX" in upper:
                basis = AirlinePolicyPriceBasis.PER_PASSENGER.value
            elif "PER DIRECTION" in upper or "ONE WAY" in upper:
                basis = AirlinePolicyPriceBasis.PER_DIRECTION.value
            elif "PER SEGMENT" in upper:
                basis = AirlinePolicyPriceBasis.PER_SEGMENT.value
            elif "ROUNDTRIP" in upper or "ROUND TRIP" in upper:
                basis = AirlinePolicyPriceBasis.ROUNDTRIP_DOUBLED.value
            mandatory_optional = AirlinePolicyMandatoryOptional.UNKNOWN.value
            if "MANDATORY" in upper or "REQUIRED" in upper:
                mandatory_optional = AirlinePolicyMandatoryOptional.MANDATORY.value
            elif "OPTIONAL" in upper:
                mandatory_optional = AirlinePolicyMandatoryOptional.OPTIONAL.value
            direct_connecting = AirlinePolicyDirectConnecting.UNKNOWN.value
            if "DIRECT" in upper and "CONNECT" in upper:
                direct_connecting = AirlinePolicyDirectConnecting.BOTH.value
            elif "DIRECT" in upper:
                direct_connecting = AirlinePolicyDirectConnecting.DIRECT.value
            elif "CONNECT" in upper:
                direct_connecting = AirlinePolicyDirectConnecting.CONNECTING.value
            candidate = AirlinePolicyExtractedPrice(
                extraction_run_id=run["id"],
                policy_source_id=source["id"],
                section_id=section.get("id"),
                airline_id=source.get("airline_id"),
                service_domain=service_domain,
                service_family=service_family,
                service_variant=_service_variant(line),
                mandatory_optional=mandatory_optional,
                price_type=AirlinePolicyPriceType.EMD_FEE if "EMD" in upper else AirlinePolicyPriceType.SERVICE_FEE,
                currency=str(currency).upper(),
                amount=amount,
                price_basis=basis,
                direct_connecting=direct_connecting,
                emd_required=True if "EMD" in upper else None,
                source_excerpt=_line_excerpt(line),
                confidence=_confidence_for_line(line, 0.74),
            )
            created = await self.db.collection("airline_policy_extracted_prices").insert_one(candidate.model_dump(mode="json"))
            result["prices"].append(created)

    async def _maybe_communication_candidate(
        self,
        result: dict[str, Any],
        run: dict[str, Any],
        source: dict[str, Any],
        section: dict[str, Any],
        line: str,
        service_domain: str,
        service_family: str,
    ) -> None:
        upper = line.upper()
        communication_type: str | None = None
        ssr_code = None
        osi_keyword = None
        ndc_supported = None
        ssr_match = re.search(r"\bSSR\s+([A-Z0-9]{3,4})\b", upper)
        if ssr_match:
            communication_type = AirlinePolicyCommunicationType.SSR.value
            ssr_code = ssr_match.group(1)
        elif "OSI" in upper:
            communication_type = AirlinePolicyCommunicationType.OSI.value
            keyword_match = re.search(r"\bOSI\s+([A-Z0-9]{2,4})?\b", upper)
            osi_keyword = keyword_match.group(1) if keyword_match else None
        elif "OTHS" in upper:
            communication_type = AirlinePolicyCommunicationType.OTHS.value
        elif "NDC" in upper:
            communication_type = AirlinePolicyCommunicationType.NDC.value
            ndc_supported = not _line_has(upper, "NOT AVAILABLE", "NOT SUPPORTED", "NO NDC", "NDC NOT")
        elif "GDS" in upper or re.search(r"\bSR\s+[A-Z0-9]{3,4}\b", upper):
            communication_type = AirlinePolicyCommunicationType.GDS_ENTRY.value
        if not communication_type:
            return
        candidate = AirlinePolicyExtractedCommunicationRule(
            extraction_run_id=run["id"],
            policy_source_id=source["id"],
            section_id=section.get("id"),
            airline_id=source.get("airline_id"),
            service_domain=service_domain,
            service_family=service_family,
            service_variant=_service_variant(line) or ssr_code,
            communication_type=communication_type,
            ssr_code=ssr_code,
            osi_keyword=osi_keyword,
            gds_system=_provider_from_text(line),
            input_template=_line_excerpt(line) if communication_type in {AirlinePolicyCommunicationType.SSR.value, AirlinePolicyCommunicationType.GDS_ENTRY.value} else None,
            example_text=_line_excerpt(line),
            passenger_association_required=True if "PASSENGER" in upper or "PAX" in upper else None,
            segment_association_required=True if "SEGMENT" in upper or "SECTOR" in upper else None,
            airline_confirmation_required=True if _line_has(upper, "CONFIRM", "HK", "NN") else None,
            ndc_supported=ndc_supported,
            source_excerpt=_line_excerpt(line),
            confidence=_confidence_for_line(line, 0.72),
        )
        created = await self.db.collection("airline_policy_extracted_communication_rules").insert_one(candidate.model_dump(mode="json"))
        result["communication_rules"].append(created)

    async def _maybe_emd_candidate(
        self,
        result: dict[str, Any],
        run: dict[str, Any],
        source: dict[str, Any],
        section: dict[str, Any],
        line: str,
        service_domain: str,
        service_family: str,
    ) -> None:
        upper = line.upper()
        if not _line_has(upper, "EMD", "RFIC", "RFISC", "ASVC", "ICW"):
            return
        emd_type = AirlinePolicyEmdType.UNKNOWN.value
        if "EMD-A" in upper or "EMD A" in upper:
            emd_type = AirlinePolicyEmdType.EMD_A.value
        elif "EMD-S" in upper or "EMD S" in upper:
            emd_type = AirlinePolicyEmdType.EMD_S.value
        elif "EMD" in upper:
            emd_type = AirlinePolicyEmdType.EITHER.value if "EITHER" in upper else AirlinePolicyEmdType.UNKNOWN.value
        rfic_match = re.search(r"\bRFIC\s*[:\-]?\s*([A-Z0-9])\b", upper)
        rfisc_match = re.search(r"\bRFISC\s*[:\-]?\s*([A-Z0-9]{2,4})\b", upper)
        service_subcode_match = re.search(r"\b(?:SUBCODE|SERVICE SUBCODE)\s*[:\-]?\s*([A-Z0-9]{2,4})\b", upper)
        candidate = AirlinePolicyExtractedEmdRule(
            extraction_run_id=run["id"],
            policy_source_id=source["id"],
            section_id=section.get("id"),
            airline_id=source.get("airline_id"),
            service_domain=service_domain,
            service_family=service_family,
            service_variant=_service_variant(line),
            emd_required=False if _line_has(upper, "NO EMD", "EMD NOT REQUIRED") else True,
            fee_included_in_fare=True if _line_has(upper, "INCLUDED IN FARE", "FARE INCLUDED") else None,
            emd_type=emd_type,
            rfic=rfic_match.group(1) if rfic_match else None,
            rfisc=rfisc_match.group(1) if rfisc_match else None,
            service_subcode=service_subcode_match.group(1) if service_subcode_match else None,
            asvc_available=True if "ASVC" in upper else None,
            icw_ticket_required=True if "ICW" in upper and "TICKET" in upper else None,
            associated_ssr_code=_service_variant(line),
            refundable=False if "NON-REFUND" in upper or "NOT REFUND" in upper else (True if "REFUND" in upper else None),
            exchangeable=False if "NOT EXCHANGE" in upper else (True if "EXCHANGE" in upper else None),
            issuance_channel_json={"gds_system": _provider_from_text(line)} if _provider_from_text(line) != AirlinePolicyGdsSystem.UNKNOWN.value else {},
            gds_command_examples_json=[{"example": _line_excerpt(line)}] if "GDS" in upper or "SR " in upper else [],
            source_excerpt=_line_excerpt(line),
            confidence=_confidence_for_line(line, 0.72),
        )
        created = await self.db.collection("airline_policy_extracted_emd_rules").insert_one(candidate.model_dump(mode="json"))
        result["emd_rules"].append(created)

    async def _maybe_exception_candidate(
        self,
        result: dict[str, Any],
        run: dict[str, Any],
        source: dict[str, Any],
        section: dict[str, Any],
        line: str,
        service_domain: str,
        service_family: str,
    ) -> None:
        upper = line.upper()
        exception_type: str | None = None
        if "EMBARGO" in upper:
            exception_type = AirlinePolicyExceptionType.EMBARGO.value
        elif _line_has(upper, "NO CONNECTION", "CONNECTING NOT", "CONNECTION NOT", "TRANSFER NOT"):
            exception_type = AirlinePolicyExceptionType.CONNECTION_BLOCK.value
        elif "OVERNIGHT" in upper and _line_has(upper, "NO", "NOT", "FORBIDDEN"):
            exception_type = AirlinePolicyExceptionType.OVERNIGHT_FORBIDDEN.value
        elif _line_has(upper, "AIRPORT CHANGE", "CHANGE OF AIRPORT"):
            exception_type = AirlinePolicyExceptionType.AIRPORT_CHANGE_FORBIDDEN.value
        elif _line_has(upper, "TRAIN", "BUS") and _line_has(upper, "NO", "NOT", "FORBIDDEN"):
            exception_type = AirlinePolicyExceptionType.TRAIN_BUS_FORBIDDEN.value
        elif _line_has(upper, "PARTNER", "INTERLINE", "OPERATED BY"):
            exception_type = AirlinePolicyExceptionType.PARTNER_AIRLINE_LIMITATION.value
        elif _line_has(upper, "COUNTRY", "VISA", "DOCUMENT"):
            exception_type = AirlinePolicyExceptionType.COUNTRY_DOCUMENT_RULE.value
        elif _line_has(upper, "NOT PERMITTED", "FORBIDDEN", "RESTRICTED", "MANUAL REVIEW"):
            exception_type = AirlinePolicyExceptionType.MANUAL_REVIEW_REQUIRED.value
        if not exception_type:
            return
        candidate = AirlinePolicyExtractedException(
            extraction_run_id=run["id"],
            policy_source_id=source["id"],
            section_id=section.get("id"),
            airline_id=source.get("airline_id"),
            service_domain=service_domain,
            service_family=service_family,
            exception_type=exception_type,
            normalized_condition_json={"text_signal": exception_type},
            normalized_action_json={"manual_review_required": True, "policy_action": "warn_or_block"},
            source_excerpt=_line_excerpt(line),
            confidence=_confidence_for_line(line, 0.66),
        )
        created = await self.db.collection("airline_policy_extracted_exceptions").insert_one(candidate.model_dump(mode="json"))
        result["exceptions"].append(created)

    async def get_extraction_run(self, extraction_run_id: str) -> dict[str, Any] | None:
        return await self.db.collection("airline_policy_extraction_runs").find_one({"id": extraction_run_id})

    async def list_extraction_runs(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        items = await self.db.collection("airline_policy_extraction_runs").find_many()
        for key, value in (filters or {}).items():
            if value not in {None, ""}:
                items = [item for item in items if item.get(key) == value]
        items.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return {"items": items}

    async def list_extracted_candidates(self, policy_source_id: str, extraction_run_id: str | None = None) -> dict[str, Any]:
        query = {"policy_source_id": policy_source_id}
        if extraction_run_id:
            query["extraction_run_id"] = extraction_run_id
        rules = await self.db.collection("airline_policy_extracted_rules").find_many(query)
        prices = await self.db.collection("airline_policy_extracted_prices").find_many(query)
        communication_rules = await self.db.collection("airline_policy_extracted_communication_rules").find_many(query)
        emd_rules = await self.db.collection("airline_policy_extracted_emd_rules").find_many(query)
        exceptions = await self.db.collection("airline_policy_extracted_exceptions").find_many(query)
        return {
            "rules": rules,
            "prices": prices,
            "communication_rules": communication_rules,
            "emd_rules": emd_rules,
            "exceptions": exceptions,
            "counts": {
                "rules": len(rules),
                "prices": len(prices),
                "communication_rules": len(communication_rules),
                "emd_rules": len(emd_rules),
                "exceptions": len(exceptions),
            },
        }

    async def apply_review_correction(self, payload: Any, user: dict) -> dict[str, Any] | None:
        target_type = _enum_value(_get(payload, "target_type"))
        correction_type = _enum_value(_get(payload, "correction_type"))
        target_id = _get(payload, "target_id")
        target = None
        if target_type in RULE_COLLECTIONS and target_id:
            collection_name = RULE_COLLECTIONS[target_type]
            target = await self.db.collection(collection_name).find_one({"id": target_id, "policy_source_id": _get(payload, "policy_source_id")})
            if not target:
                return None
            status_value = {
                AirlinePolicyCorrectionType.ACCEPT.value: AirlinePolicyCandidateStatus.ACCEPTED.value,
                AirlinePolicyCorrectionType.CORRECT.value: AirlinePolicyCandidateStatus.CORRECTED.value,
                AirlinePolicyCorrectionType.REJECT.value: AirlinePolicyCandidateStatus.REJECTED.value,
                AirlinePolicyCorrectionType.PROMOTE.value: AirlinePolicyCandidateStatus.PROMOTED.value,
                AirlinePolicyCorrectionType.ARCHIVE.value: AirlinePolicyCandidateStatus.REJECTED.value,
            }.get(correction_type, target.get("status"))
            target = await self.db.collection(collection_name).update_one(
                {"id": target_id, "policy_source_id": _get(payload, "policy_source_id")},
                {
                    "status": status_value,
                    "correction_json": _get(payload, "after_json", {}) or {},
                    "reviewed_by_user_id": user.get("id"),
                    "reviewed_at": _now(),
                },
            )
        elif target_type == AirlinePolicyReviewTargetType.SOURCE.value:
            status_value = {
                AirlinePolicyCorrectionType.ACCEPT.value: AirlinePolicyIngestionStatus.REVIEWED.value,
                AirlinePolicyCorrectionType.REJECT.value: AirlinePolicyIngestionStatus.REJECTED.value,
                AirlinePolicyCorrectionType.ARCHIVE.value: AirlinePolicyIngestionStatus.ARCHIVED.value,
            }.get(correction_type, AirlinePolicyIngestionStatus.REVIEWED.value)
            target = await self.db.collection("airline_policy_sources").update_one(
                {"id": _get(payload, "policy_source_id")},
                {"ingestion_status": status_value},
            )

        correction = AirlinePolicyReviewCorrection(
            policy_source_id=_get(payload, "policy_source_id"),
            extraction_run_id=_get(payload, "extraction_run_id"),
            target_type=target_type,
            target_id=target_id,
            correction_type=correction_type,
            before_json=_get(payload, "before_json", {}) or {},
            after_json=_get(payload, "after_json", {}) or {},
            correction_reason=_get(payload, "correction_reason"),
            created_by_user_id=user.get("id"),
        )
        created = await self.db.collection("airline_policy_review_corrections").insert_one(correction.model_dump(mode="json"))
        await self.db.collection("airline_policy_sources").update_one(
            {"id": _get(payload, "policy_source_id")},
            {"ingestion_status": AirlinePolicyIngestionStatus.REVIEWED.value},
        )
        return {"correction": created, "target": target, "auto_promotion_disabled": True}

    async def promote_candidate(self, payload: Any, user: dict) -> dict[str, Any] | None:
        target_type = _enum_value(_get(payload, "target_type"))
        target_id = _get(payload, "target_id")
        if target_type not in RULE_COLLECTIONS or not target_id:
            return None
        collection_name = RULE_COLLECTIONS[target_type]
        candidate = await self.db.collection(collection_name).find_one({"id": target_id, "policy_source_id": _get(payload, "policy_source_id")})
        if not candidate or candidate.get("status") not in {AirlinePolicyCandidateStatus.ACCEPTED.value, AirlinePolicyCandidateStatus.CORRECTED.value}:
            return None
        knowledge = await self._create_approved_knowledge_from_candidate(target_type, candidate, _get(payload, "knowledge_type"), user)
        updated = await self.db.collection(collection_name).update_one(
            {"id": target_id},
            {"status": AirlinePolicyCandidateStatus.PROMOTED.value, "reviewed_by_user_id": user.get("id"), "reviewed_at": _now()},
        )
        await self.db.collection("airline_policy_sources").update_one(
            {"id": candidate["policy_source_id"]},
            {"ingestion_status": AirlinePolicyIngestionStatus.APPROVED.value},
        )
        return {"approved_knowledge": knowledge, "candidate": updated, "auto_promotion_disabled": True}

    async def promote_accepted_candidates(self, policy_source_id: str, extraction_run_id: str, user: dict) -> dict[str, Any]:
        promoted = []
        for target_type, collection_name in RULE_COLLECTIONS.items():
            items = await self.db.collection(collection_name).find_many({"policy_source_id": policy_source_id, "extraction_run_id": extraction_run_id})
            for item in items:
                if item.get("status") not in {AirlinePolicyCandidateStatus.ACCEPTED.value, AirlinePolicyCandidateStatus.CORRECTED.value}:
                    continue
                knowledge = await self._create_approved_knowledge_from_candidate(target_type, item, None, user)
                await self.db.collection(collection_name).update_one(
                    {"id": item["id"]},
                    {"status": AirlinePolicyCandidateStatus.PROMOTED.value, "reviewed_by_user_id": user.get("id"), "reviewed_at": _now()},
                )
                promoted.append(knowledge)
        if promoted:
            await self.db.collection("airline_policy_sources").update_one(
                {"id": policy_source_id},
                {"ingestion_status": AirlinePolicyIngestionStatus.APPROVED.value},
            )
        return {"items": promoted, "promoted_count": len(promoted), "auto_promotion_disabled": True}

    async def _create_approved_knowledge_from_candidate(
        self,
        target_type: str,
        candidate: dict[str, Any],
        knowledge_type: str | None,
        user: dict,
    ) -> dict[str, Any]:
        source = await self.get_policy_source(candidate["policy_source_id"]) or {}
        payload = {
            "target_type": target_type,
            "candidate_id": candidate.get("id"),
            "rule_type": candidate.get("rule_type"),
            "price_type": candidate.get("price_type"),
            "communication_type": candidate.get("communication_type"),
            "exception_type": candidate.get("exception_type"),
            "normalized_condition_json": candidate.get("normalized_condition_json") or {},
            "normalized_action_json": candidate.get("normalized_action_json") or {},
            "currency": candidate.get("currency"),
            "amount": candidate.get("amount"),
            "price_basis": candidate.get("price_basis"),
            "ssr_code": candidate.get("ssr_code"),
            "osi_keyword": candidate.get("osi_keyword"),
            "emd_type": candidate.get("emd_type"),
            "rfic": candidate.get("rfic"),
            "rfisc": candidate.get("rfisc"),
            "status_before_promotion": candidate.get("status"),
            "platform_review_required": True,
        }
        record = AirlinePolicyApprovedKnowledgeRecord(
            policy_source_id=candidate["policy_source_id"],
            extraction_run_id=candidate.get("extraction_run_id"),
            airline_id=candidate.get("airline_id"),
            service_domain=candidate.get("service_domain") or source.get("service_domain") or "special_services",
            service_family=candidate.get("service_family") or source.get("service_family") or "general",
            service_variant=candidate.get("service_variant"),
            knowledge_type=_enum_value(knowledge_type) or KNOWLEDGE_TYPE_BY_TARGET.get(target_type, AirlinePolicyKnowledgeType.OPERATIONAL_REQUIREMENT.value),
            normalized_payload_json=_compact(payload),
            source_excerpt=candidate.get("source_excerpt") or "",
            source_section_id=candidate.get("section_id"),
            confidence=candidate.get("confidence") or 0.0,
            status=AirlinePolicyApprovedKnowledgeStatus.APPROVED,
            effective_from=source.get("effective_from"),
            effective_to=source.get("effective_to"),
            approved_by_user_id=user.get("id"),
            approved_at=_now(),
        )
        return await self.db.collection("airline_policy_approved_knowledge_records").insert_one(record.model_dump(mode="json"))

    async def list_approved_knowledge(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        items = await self.db.collection("airline_policy_approved_knowledge_records").find_many()
        for key, value in (filters or {}).items():
            if value not in {None, ""}:
                items = [item for item in items if item.get(key) == value]
        items.sort(key=lambda item: str(item.get("approved_at") or item.get("created_at") or ""), reverse=True)
        return {"items": items}

    async def submit_for_platform_review(self, policy_source_id: str, user: dict) -> dict[str, Any] | None:
        source = await self.get_policy_source(policy_source_id)
        if not source:
            return None
        warnings = list(source.get("warnings_json") or [])
        warnings.append(_warning("submitted_for_platform_review", "Agency source is marked for platform review; no global promotion occurred."))
        updated = await self.db.collection("airline_policy_sources").update_one(
            {"id": policy_source_id},
            {"ingestion_status": AirlinePolicyIngestionStatus.REVIEWED.value, "warnings_json": warnings},
        )
        return {"policy_source": updated, "global_knowledge_created": False, "platform_review_required_for_global_knowledge": True}
