from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import KnowledgeImportTemplate, KnowledgeImportTemplateCreate, KnowledgeImportTemplateUpdate


PHASE_LABEL = "phase_52_6_knowledge_quality_assurance_foundation"
FOUNDATION_PHASE_LABEL = "phase_52_2_knowledge_import_templates_foundation"
KNOWLEDGE_IMPORT_TEMPLATES_COLLECTION = "knowledge_import_templates"

TEMPLATE_TYPES = [
    "airline_manual",
    "operational_bulletin",
    "policy_update",
    "capability_table",
    "pricing_table",
    "service_parameter_table",
    "reference_data_table",
    "evidence_pack",
    "exception_rule_pack",
]

IMPORT_SCOPES = [
    "platform_governed",
    "agency_scoped",
    "airline_specific",
    "scenario_testing",
    "reference_population",
]

ACCEPTED_FILE_TYPES = ["csv", "xlsx", "json", "pdf", "txt", "md"]


class KnowledgeImportTemplateError(ValueError):
    pass


class KnowledgeImportTemplateService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        templates = await self.list_templates(**filters)
        return {
            "phase": PHASE_LABEL,
            "foundation_phase": FOUNDATION_PHASE_LABEL,
            "items": templates,
            "templates": templates,
            "summary": await self.summarize_counts(filters.get("agency_id")),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Knowledge Import Templates define reusable metadata for future airline knowledge population. They do not parse files, scrape, call providers, generate AI output, or run background workers.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        templates = await self.list_templates(agency_id=agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "foundation_phase": FOUNDATION_PHASE_LABEL,
            "agency_id": agency_id,
            "items": templates,
            "templates": templates,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Agency Import Templates show metadata-only schemas for future human-reviewed airline knowledge population.",
            **self.safety_flags(),
        }

    async def platform_summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "foundation_phase": FOUNDATION_PHASE_LABEL,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "foundation_phase": FOUNDATION_PHASE_LABEL,
            "agency_id": agency_id,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_templates(
        self,
        *,
        agency_id: str | None = None,
        template_type: str | None = None,
        target_knowledge_domain: str | None = None,
        target_collection: str | None = None,
        import_scope: str | None = None,
        review_required: bool | None = None,
        accepted_file_type: str | None = None,
        search: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if template_type:
            filters["template_type"] = self._normalize_code(template_type)
        if target_knowledge_domain:
            filters["target_knowledge_domain"] = self._normalize_code(target_knowledge_domain)
        if import_scope:
            filters["import_scope"] = self._normalize_code(import_scope)
        if review_required is not None:
            filters["review_required"] = review_required

        items = await self.db.collection(KNOWLEDGE_IMPORT_TEMPLATES_COLLECTION).find_many(filters or None)
        if target_collection:
            collection = self._normalize_code(target_collection)
            items = [item for item in items if collection in (item.get("target_collections") or [])]
        if accepted_file_type:
            file_type = self._normalize_file_type(accepted_file_type)
            items = [item for item in items if file_type in (item.get("accepted_file_types") or [])]
        if not include_archived:
            items = [item for item in items if not item.get("archived")]
        items = [
            item
            for item in items
            if self._any_field_matches(
                item,
                [
                    "template_reference",
                    "template_name",
                    "template_type",
                    "template_version",
                    "target_knowledge_domain",
                    "target_collections",
                    "required_columns",
                    "optional_columns",
                    "validation_rules",
                    "mapping_rules",
                    "sample_rows",
                    "accepted_file_types",
                    "import_scope",
                    "governance_links",
                    "metadata",
                ],
                search,
            )
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._template_projection(item) for item in items]

    async def get_template(self, template_id: str, agency_id: str | None = None) -> dict[str, Any]:
        item = await self._require_template(template_id, agency_id=agency_id)
        return await self._template_projection(item)

    async def create_template(
        self,
        payload: KnowledgeImportTemplateCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data["template_type"] = self._normalize_code(data.get("template_type"))
        data["target_knowledge_domain"] = self._normalize_code(data.get("target_knowledge_domain"))
        data["target_collections"] = [self._normalize_code(value) for value in data.get("target_collections") or []]
        data["accepted_file_types"] = [self._normalize_file_type(value) for value in data.get("accepted_file_types") or []]
        data["import_scope"] = self._normalize_code(data.get("import_scope") or "platform_governed")
        data.setdefault("template_reference", self._reference("KIT"))
        data.setdefault("template_version", "1.0")
        data.setdefault("review_required", True)
        data.update(self.safety_flags())
        self._validate_payload(data)
        record = KnowledgeImportTemplate(**data)
        created = await self.db.collection(KNOWLEDGE_IMPORT_TEMPLATES_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "foundation_phase": FOUNDATION_PHASE_LABEL,
            "knowledge_import_template": await self._template_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_template(
        self,
        template_id: str,
        payload: KnowledgeImportTemplateUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_template(template_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if agency_id:
            updates.pop("agency_id", None)
        if "template_type" in updates:
            updates["template_type"] = self._normalize_code(updates["template_type"])
        if "target_knowledge_domain" in updates:
            updates["target_knowledge_domain"] = self._normalize_code(updates["target_knowledge_domain"])
        if "target_collections" in updates:
            updates["target_collections"] = [self._normalize_code(value) for value in updates.get("target_collections") or []]
        if "accepted_file_types" in updates:
            updates["accepted_file_types"] = [self._normalize_file_type(value) for value in updates.get("accepted_file_types") or []]
        if "import_scope" in updates:
            updates["import_scope"] = self._normalize_code(updates["import_scope"])
        updates.update(self.safety_flags())
        self._validate_payload(updates, partial=True)
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(KNOWLEDGE_IMPORT_TEMPLATES_COLLECTION).update_one(filters, updates)
        if not updated:
            raise KnowledgeImportTemplateError("Knowledge import template metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "foundation_phase": FOUNDATION_PHASE_LABEL,
            "knowledge_import_template": await self._template_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_template(self, template_id: str, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_template(template_id, agency_id=agency_id)
        updates = {
            "archived": True,
            "archived_at": self._now(),
            **self.safety_flags(),
        }
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(KNOWLEDGE_IMPORT_TEMPLATES_COLLECTION).update_one(filters, updates)
        if not updated:
            raise KnowledgeImportTemplateError("Knowledge import template metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "foundation_phase": FOUNDATION_PHASE_LABEL,
            "knowledge_import_template": await self._template_projection(updated),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def summarize_counts(self, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        templates = await self.db.collection(KNOWLEDGE_IMPORT_TEMPLATES_COLLECTION).find_many(filters)
        covered_template_types = {item.get("template_type") for item in templates if item.get("template_type") in TEMPLATE_TYPES}
        return {
            "knowledge_import_template_count": len(templates),
            "active_template_count": len([item for item in templates if not item.get("archived")]),
            "required_column_count": sum(len(item.get("required_columns") or []) for item in templates),
            "optional_column_count": sum(len(item.get("optional_columns") or []) for item in templates),
            "validation_rule_count": sum(len(item.get("validation_rules") or []) for item in templates),
            "mapping_rule_count": sum(len(item.get("mapping_rules") or []) for item in templates),
            "sample_row_count": sum(len(item.get("sample_rows") or []) for item in templates),
            "target_collection_count": sum(len(item.get("target_collections") or []) for item in templates),
            "governance_link_count": sum(len(item.get("governance_links") or []) for item in templates),
            "review_required_count": len([item for item in templates if item.get("review_required") is True]),
            "by_template_type": self._counts(templates, "template_type", TEMPLATE_TYPES),
            "by_import_scope": self._counts(templates, "import_scope", IMPORT_SCOPES),
            "supported_template_type_count": len(TEMPLATE_TYPES),
            "covered_template_type_count": len(covered_template_types),
            "missing_template_types": [template_type for template_type in TEMPLATE_TYPES if template_type not in covered_template_types],
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "template_type": TEMPLATE_TYPES,
            "target_knowledge_domain": "knowledge graph domain code",
            "target_collection": "target collection name",
            "import_scope": IMPORT_SCOPES,
            "review_required": "true or false",
            "accepted_file_type": ACCEPTED_FILE_TYPES,
            "search": "reference, name, type, domain, columns, rules, mapping, samples, governance, or metadata match",
            "metadata_only": True,
        }

    async def _template_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        required_columns = projected.get("required_columns") or []
        optional_columns = projected.get("optional_columns") or []
        validation_rules = projected.get("validation_rules") or []
        mapping_rules = projected.get("mapping_rules") or []
        sample_rows = projected.get("sample_rows") or []
        target_collections = projected.get("target_collections") or []
        governance_links = projected.get("governance_links") or []
        projected["template_display_name"] = projected.get("template_name") or projected.get("template_reference")
        projected["template_overview_section"] = {
            "template_reference": projected.get("template_reference"),
            "template_name": projected.get("template_name"),
            "template_type": projected.get("template_type"),
            "template_version": projected.get("template_version"),
            "target_knowledge_domain": projected.get("target_knowledge_domain"),
            "target_collections": target_collections,
            "accepted_file_types": projected.get("accepted_file_types") or [],
            "import_scope": projected.get("import_scope"),
            "review_required": projected.get("review_required"),
        }
        projected["columns_section"] = {
            "required_columns": required_columns,
            "required_column_count": len(required_columns),
            "optional_columns": optional_columns,
            "optional_column_count": len(optional_columns),
        }
        projected["validation_section"] = {
            "validation_rules": validation_rules,
            "validation_rule_count": len(validation_rules),
        }
        projected["mapping_section"] = {
            "mapping_rules": mapping_rules,
            "mapping_rule_count": len(mapping_rules),
        }
        projected["sample_rows_section"] = {
            "sample_rows": sample_rows,
            "sample_row_count": len(sample_rows),
        }
        projected["governance_section"] = {
            "governance_links": governance_links,
            "governance_link_count": len(governance_links),
            "archived": projected.get("archived"),
            "archived_at": projected.get("archived_at"),
        }
        projected["readiness_section"] = {
            "template_schema_ready": bool(required_columns and target_collections),
            "review_required": projected.get("review_required"),
            "metadata_only": True,
            "human_authority_final": True,
        }
        projected["boundary_section"] = self.safety_flags()
        projected["foundation_phase"] = FOUNDATION_PHASE_LABEL
        projected.update(self.safety_flags())
        return projected

    async def _require_template(self, template_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": template_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(KNOWLEDGE_IMPORT_TEMPLATES_COLLECTION).find_one(filters)
        if not item:
            raise KnowledgeImportTemplateError("Knowledge import template metadata not found.")
        return item

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "template_type", TEMPLATE_TYPES)
        self._validate_choice(data, "import_scope", IMPORT_SCOPES)
        for file_type in data.get("accepted_file_types") or []:
            if file_type not in ACCEPTED_FILE_TYPES:
                raise KnowledgeImportTemplateError(f"Unsupported accepted_file_type metadata value: {file_type}.")
        self._reject_forbidden_metadata(data)
        if not partial:
            for field in ["template_name", "template_type", "target_knowledge_domain"]:
                if not data.get(field):
                    raise KnowledgeImportTemplateError(f"{field} is required.")

    def _validate_choice(self, data: dict[str, Any], field: str, allowed: list[str]) -> None:
        if field not in data or data.get(field) is None:
            return
        if data[field] not in allowed:
            raise KnowledgeImportTemplateError(f"Unsupported {field} metadata value: {data[field]}.")

    def _reject_forbidden_metadata(self, data: dict[str, Any]) -> None:
        forbidden = [
            "beautifulsoup",
            "scrapy",
            "selenium",
            "playwright",
            "requests.",
            "httpx",
            "provider_client",
            "provider_payload",
            "openai",
            "chatcompletion",
            "ai_prompt",
            "llm_prompt",
            "background_task",
            "backgroundtasks",
            "asyncio.create_task",
            "parse_file(",
            "execute_import",
            "run_import",
        ]
        serialized = str(data).lower()
        for marker in forbidden:
            if marker in serialized:
                raise KnowledgeImportTemplateError(f"Forbidden non-metadata implementation marker present: {marker}.")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "knowledge_import_templates_foundation": True,
            "parsing_execution_disabled": True,
            "scraping_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "provider_integrations_disabled": True,
            "human_authority_final": True,
        }

    def _normalize_code(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("/", "_")

    def _normalize_file_type(self, value: Any) -> str:
        return str(value or "").strip().lower().lstrip(".")

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
