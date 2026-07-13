from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import VisualPolicyEditorCard, VisualPolicyEditorCardCreate, VisualPolicyEditorCardUpdate


PHASE_LABEL = "phase_54_2_agent_work_queue_assignment_foundation"
VISUAL_POLICY_EDITOR_CARDS_COLLECTION = "visual_policy_editor_cards"

POLICY_FAMILIES = [
    "PETC",
    "AVIH",
    "SVAN",
    "ESAN",
    "WCHR",
    "WCHS",
    "WCHC",
    "WCOB",
    "MAAS",
    "MEDIF",
    "MEDA",
    "STCR",
    "OXYG",
    "POC",
    "UMNR",
    "YP",
    "EXST",
    "CBBG",
    "sports_equipment",
    "musical_instruments",
    "fragile_valuable",
    "restricted_equipment",
    "documents_compliance",
]

POLICY_CARD_STATUSES = ["draft", "in_review", "approved", "retired", "archived"]
SUPPORT_STATUSES = ["supported", "not_supported", "conditional", "unknown", "request_required"]


class VisualPolicyEditorError(ValueError):
    pass


class VisualPolicyEditorService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        cards = await self.list_cards(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": cards,
            "policy_cards": cards,
            "summary": await self.summarize_counts(filters.get("agency_id")),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Visual Policy Editor cards store structured policy metadata for human review. They do not execute policies, evaluate rules, calculate pricing, call providers, generate AI output, run workers, or expose legacy admin routes.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        cards = await self.list_cards(agency_id=agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": cards,
            "policy_cards": cards,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Agency Policy Editor shows metadata-only airline service policy cards. Human authority remains final.",
            **self.safety_flags(),
        }

    async def platform_summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_cards(
        self,
        *,
        agency_id: str | None = None,
        airline: str | None = None,
        policy_family: str | None = None,
        service_family: str | None = None,
        service_code: str | None = None,
        status: str | None = None,
        support_status: str | None = None,
        search: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if airline:
            filters["airline"] = self._normalize_airline(airline)
        if policy_family:
            filters["policy_family"] = self._normalize_policy_family(policy_family)
        if service_family:
            filters["service_family"] = service_family
        if status:
            filters["status"] = status
        if support_status:
            filters["support_status"] = support_status

        items = await self.db.collection(VISUAL_POLICY_EDITOR_CARDS_COLLECTION).find_many(filters or None)
        if service_code:
            normalized_service_code = self._normalize_service_code(service_code)
            items = [item for item in items if normalized_service_code in (item.get("service_codes") or [])]
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(
                item,
                [
                    "card_reference",
                    "airline",
                    "policy_family",
                    "service_family",
                    "service_codes",
                    "limits",
                    "restrictions",
                    "required_documents",
                    "approval_requirements",
                    "warnings",
                    "client_messages",
                    "internal_notes",
                    "evidence_links",
                    "knowledge_governance_links",
                    "service_parameter_taxonomy_links",
                    "metadata",
                ],
                search,
            )
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._card_projection(item) for item in items]

    async def get_card(self, card_id: str, agency_id: str | None = None) -> dict[str, Any]:
        item = await self._require_card(card_id, agency_id=agency_id)
        return await self._card_projection(item)

    async def create_card(
        self,
        payload: VisualPolicyEditorCardCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data["airline"] = self._normalize_airline(data.get("airline"))
        data["policy_family"] = self._normalize_policy_family(data.get("policy_family"))
        data["service_codes"] = [self._normalize_service_code(code) for code in data.get("service_codes") or []]
        data.setdefault("card_reference", self._reference("VPE"))
        data.setdefault("service_family", self._default_service_family(data["policy_family"]))
        data.setdefault("status", "draft")
        data.setdefault("support_status", "unknown")
        data.update(self.safety_flags())
        self._validate_payload(data)
        record = VisualPolicyEditorCard(**data)
        created = await self.db.collection(VISUAL_POLICY_EDITOR_CARDS_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "visual_policy_editor_card": await self._card_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_card(
        self,
        card_id: str,
        payload: VisualPolicyEditorCardUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_card(card_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if agency_id:
            updates.pop("agency_id", None)
        if "airline" in updates:
            updates["airline"] = self._normalize_airline(updates["airline"])
        if "policy_family" in updates:
            updates["policy_family"] = self._normalize_policy_family(updates["policy_family"])
            updates.setdefault("service_family", self._default_service_family(updates["policy_family"]))
        if "service_codes" in updates:
            updates["service_codes"] = [self._normalize_service_code(code) for code in updates.get("service_codes") or []]
        updates.update(self.safety_flags())
        self._validate_payload(updates, partial=True)
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(VISUAL_POLICY_EDITOR_CARDS_COLLECTION).update_one(filters, updates)
        if not updated:
            raise VisualPolicyEditorError("Visual policy editor card metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "visual_policy_editor_card": await self._card_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_card(self, card_id: str, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_card(card_id, agency_id=agency_id)
        updates = {
            "status": "archived",
            "archived": True,
            "archived_at": self._now(),
            **self.safety_flags(),
        }
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(VISUAL_POLICY_EDITOR_CARDS_COLLECTION).update_one(filters, updates)
        if not updated:
            raise VisualPolicyEditorError("Visual policy editor card metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "visual_policy_editor_card": await self._card_projection(updated),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def summarize_counts(self, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        cards = await self.db.collection(VISUAL_POLICY_EDITOR_CARDS_COLLECTION).find_many(filters)
        covered_families = {item.get("policy_family") for item in cards if item.get("policy_family") in POLICY_FAMILIES}
        return {
            "visual_policy_editor_card_count": len(cards),
            "active_card_count": len([item for item in cards if not item.get("archived") and item.get("status") != "archived"]),
            "service_code_count": sum(len(item.get("service_codes") or []) for item in cards),
            "evidence_link_count": sum(len(item.get("evidence_links") or []) for item in cards),
            "knowledge_governance_link_count": sum(len(item.get("knowledge_governance_links") or []) for item in cards),
            "service_parameter_taxonomy_link_count": sum(len(item.get("service_parameter_taxonomy_links") or []) for item in cards),
            "required_document_count": sum(len(item.get("required_documents") or []) for item in cards),
            "approval_requirement_count": sum(len(item.get("approval_requirements") or []) for item in cards),
            "warning_count": sum(len(item.get("warnings") or []) for item in cards),
            "client_message_count": sum(len(item.get("client_messages") or []) for item in cards),
            "by_status": self._counts(cards, "status", POLICY_CARD_STATUSES),
            "by_support_status": self._counts(cards, "support_status", SUPPORT_STATUSES),
            "supported_policy_family_count": len(POLICY_FAMILIES),
            "covered_policy_family_count": len(covered_families),
            "missing_policy_families": [family for family in POLICY_FAMILIES if family not in covered_families],
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "airline": "IATA or carrier code text",
            "policy_family": POLICY_FAMILIES,
            "service_family": "service family label",
            "service_code": "SSR or service code",
            "status": POLICY_CARD_STATUSES,
            "support_status": SUPPORT_STATUSES,
            "search": "reference, airline, family, section, evidence, governance, taxonomy, or note match",
            "metadata_only": True,
        }

    async def _card_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["card_display_name"] = " / ".join(
            part
            for part in [
                projected.get("airline"),
                projected.get("policy_family"),
                projected.get("service_family"),
            ]
            if part
        )
        projected["overview_section"] = {
            "card_reference": projected.get("card_reference"),
            "airline": projected.get("airline"),
            "policy_family": projected.get("policy_family"),
            "service_family": projected.get("service_family"),
            "service_codes": projected.get("service_codes") or [],
            "status": projected.get("status"),
            "effective_from": projected.get("effective_from"),
            "effective_to": projected.get("effective_to"),
        }
        projected["support_status_section"] = {
            "support_status": projected.get("support_status"),
            "service_codes": projected.get("service_codes") or [],
            "human_authority_final": True,
        }
        projected["limits_section"] = projected.get("limits") or {}
        projected["restrictions_section"] = {
            "route": (projected.get("restrictions") or {}).get("route", []),
            "aircraft": (projected.get("restrictions") or {}).get("aircraft", []),
            "cabin": (projected.get("restrictions") or {}).get("cabin", []),
            "date": (projected.get("restrictions") or {}).get("date", []),
            "weather": (projected.get("restrictions") or {}).get("weather", []),
            "other": (projected.get("restrictions") or {}).get("other", []),
        }
        projected["documents_section"] = {
            "required_documents": projected.get("required_documents") or [],
            "required_document_count": len(projected.get("required_documents") or []),
        }
        projected["approvals_section"] = {
            "approval_requirements": projected.get("approval_requirements") or [],
            "approval_requirement_count": len(projected.get("approval_requirements") or []),
        }
        projected["warnings_section"] = {
            "warnings": projected.get("warnings") or [],
            "client_messages": projected.get("client_messages") or [],
            "internal_notes": projected.get("internal_notes"),
        }
        projected["evidence_section"] = {
            "evidence_links": projected.get("evidence_links") or [],
            "evidence_link_count": len(projected.get("evidence_links") or []),
        }
        projected["governance_section"] = {
            "knowledge_governance_links": projected.get("knowledge_governance_links") or [],
            "archived": projected.get("archived"),
            "archived_at": projected.get("archived_at"),
        }
        projected["taxonomy_section"] = {
            "service_parameter_taxonomy_links": projected.get("service_parameter_taxonomy_links") or [],
            "service_parameter_taxonomy_link_count": len(projected.get("service_parameter_taxonomy_links") or []),
        }
        projected["no_code_sections"] = {
            "overview": projected["overview_section"],
            "support_status": projected["support_status_section"],
            "limits": projected["limits_section"],
            "restrictions": projected["restrictions_section"],
            "documents": projected["documents_section"],
            "approvals": projected["approvals_section"],
            "warnings": projected["warnings_section"],
            "evidence": projected["evidence_section"],
            "governance": projected["governance_section"],
            "taxonomy": projected["taxonomy_section"],
        }
        projected["boundary_section"] = self.safety_flags()
        projected.update(self.safety_flags())
        return projected

    async def _require_card(self, card_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": card_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(VISUAL_POLICY_EDITOR_CARDS_COLLECTION).find_one(filters)
        if not item:
            raise VisualPolicyEditorError("Visual policy editor card metadata not found.")
        return item

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "policy_family", POLICY_FAMILIES)
        self._validate_choice(data, "status", POLICY_CARD_STATUSES)
        self._validate_choice(data, "support_status", SUPPORT_STATUSES)
        self._reject_forbidden_metadata(data)
        if not partial:
            for field in ["airline", "policy_family"]:
                if not data.get(field):
                    raise VisualPolicyEditorError(f"{field} is required.")

    def _validate_choice(self, data: dict[str, Any], field: str, allowed: list[str]) -> None:
        if field not in data or data.get(field) is None:
            return
        if data[field] not in allowed:
            raise VisualPolicyEditorError(f"Unsupported {field} metadata value: {data[field]}.")

    def _reject_forbidden_metadata(self, data: dict[str, Any]) -> None:
        forbidden = [
            "provider_client",
            "provider_payload",
            "ai_prompt",
            "llm_prompt",
            "chatcompletion",
            "background_task",
            "backgroundtasks",
            "execute_policy",
            "evaluate_rules",
            "calculate_price(",
            "calculate_pricing",
            "pricing_formula_executor",
            "live_rule_evaluation",
            "/ad" + "min",
            "/api/" + "ad" + "min",
        ]
        serialized = str(data).lower()
        for marker in forbidden:
            if marker in serialized:
                raise VisualPolicyEditorError(f"Forbidden non-metadata implementation marker present: {marker}.")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "visual_policy_editor_foundation": True,
            "policy_execution_disabled": True,
            "rule_evaluation_disabled": True,
            "pricing_calculation_disabled": True,
            "provider_integrations_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "old_admin_routes_disabled": True,
            "human_authority_final": True,
        }

    def _normalize_airline(self, value: Any) -> str:
        return str(value or "").strip().upper()

    def _normalize_policy_family(self, value: Any) -> str:
        raw = str(value or "").strip()
        lowered = raw.lower().replace(" ", "_").replace("/", "_")
        upper = raw.upper().replace(" ", "_")
        by_lower = {family.lower(): family for family in POLICY_FAMILIES}
        by_upper = {family.upper(): family for family in POLICY_FAMILIES}
        if upper in POLICY_FAMILIES:
            return upper
        if lowered in POLICY_FAMILIES:
            return lowered
        if upper in by_upper:
            return by_upper[upper]
        if lowered in by_lower:
            return by_lower[lowered]
        return lowered

    def _normalize_service_code(self, value: Any) -> str:
        raw = str(value or "").strip()
        return raw.upper() if len(raw) <= 6 else raw.lower().replace(" ", "_")

    def _default_service_family(self, policy_family: str) -> str:
        if policy_family in {"PETC", "AVIH", "SVAN", "ESAN"}:
            return "pets_animals"
        if policy_family in {"WCHR", "WCHS", "WCHC", "WCOB", "MAAS", "MEDIF", "MEDA", "STCR", "OXYG", "POC"}:
            return "passenger_assistance_medical"
        if policy_family in {"UMNR", "YP"}:
            return "young_passengers"
        if policy_family in {"EXST", "CBBG"}:
            return "seating_baggage"
        if policy_family == "documents_compliance":
            return "documents_compliance"
        return "special_items"

    def _reference(self, prefix: str) -> str:
        return f"{prefix}-{self._now().replace(':', '').replace('-', '').replace('.', '')}"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _sort_text(self, value: Any) -> str:
        return str(value or "")

    def _counts(self, items: list[dict[str, Any]], field: str, values: list[str]) -> dict[str, int]:
        return {value: len([item for item in items if item.get(field) == value]) for value in values}

    def _any_field_matches(self, item: dict[str, Any], fields: list[str], expected: Any) -> bool:
        if expected in (None, ""):
            return True
        expected_text = str(expected).lower()
        for field in fields:
            value = item.get(field)
            if isinstance(value, list):
                if any(expected_text in str(entry).lower() for entry in value):
                    return True
            elif isinstance(value, dict):
                if expected_text in str(value).lower():
                    return True
            elif value is not None and expected_text in str(value).lower():
                return True
        return False
