from __future__ import annotations

import csv
import hashlib
import json
from io import StringIO
from typing import Any

from database import Database
from models import GlobalReferenceRecord, ReferenceImportBatch, now_utc
from services.canonical_reference_service import find_active_scope_conflict
from services.reference_data_service import (
    audit_reference_event,
    normalize_city_reference_code,
    normalize_city_reference_metadata,
    normalize_reference_code,
    normalize_reference_metadata_for_domain,
    safe_reference_import_batch,
)
from services.service_catalogue_service import (
    insert_service_catalogue_record,
    normalize_service_catalogue_payload,
    normalize_service_key,
    update_service_catalogue_record,
)


def _template(
    domain_key: str,
    label: str,
    required_columns: list[str],
    optional_columns: list[str],
    code_normalization: str,
    metadata_mapping: dict[str, str],
    duplicate_handling: str = "mode-controlled",
) -> dict[str, Any]:
    return {
        "domain_key": domain_key,
        "label": label,
        "required_columns": required_columns,
        "optional_columns": optional_columns,
        "validation_rules": [
            "required columns must be present",
            "code values are normalized before duplicate checks",
            "duplicates inside one file are skipped as errors",
            "existing records require explicit apply mode",
        ],
        "duplicate_handling": duplicate_handling,
        "code_normalization": code_normalization,
        "metadata_mapping": metadata_mapping,
        "preview_behavior": "Preview reports create/update/skip/error without writing records.",
        "import_summary": "Apply returns created, updated, skipped, and error counts plus row-level actions.",
    }


IMPORT_TEMPLATES: dict[str, dict[str, Any]] = {
    "countries": _template("countries", "Countries", ["code", "label"], ["iso2_code", "iso3_code", "currency_iso_code", "metadata_json"], "uppercase ISO-style code", {"metadata_json": "metadata_json plus domain columns"}),
    "cities": _template("cities", "Cities", ["code", "label", "country_code"], ["aliases", "metadata_json"], "uppercase IATA city code", {"country_code": "metadata_json.country_code"}),
    "airports": _template("airports", "Airports", ["code", "label", "city_code", "country_code"], ["icao_code", "timezone", "latitude", "longitude", "metadata_json"], "uppercase IATA airport code", {"city_code": "metadata_json.city_code", "country_code": "metadata_json.country_code"}),
    "airlines": _template("airlines", "Airlines", ["code", "label"], ["iata_code", "icao_code", "country_code", "alliance_code", "metadata_json"], "uppercase airline code", {"iata_code": "metadata_json.iata_code", "icao_code": "metadata_json.icao_code"}),
    "passenger_types": _template(
        "passenger_types",
        "Passenger Type Codes",
        ["code", "label", "passenger_category"],
        [
            "description",
            "iata_ptc_code",
            "age_min_years",
            "age_max_years",
            "requires_date_of_birth",
            "requires_guardian",
            "is_infant",
            "is_child",
            "is_adult",
            "is_senior",
            "applies_to_pricing",
            "applies_to_ticketing",
            "applies_to_services",
            "manual_review_required",
            "metadata_json",
        ],
        "uppercase IATA-style passenger type code",
        {
            "passenger_category": "metadata_json.passenger_category",
            "iata_ptc_code": "metadata_json.iata_ptc_code",
            "age_min_years": "metadata_json.age_min_years",
            "age_max_years": "metadata_json.age_max_years",
        },
    ),
    "currencies": _template("currencies", "Currencies", ["code", "label"], ["currency_iso_code", "symbol", "minor_unit", "metadata_json"], "uppercase ISO currency code", {"currency_iso_code": "metadata_json.currency_iso_code"}),
    "languages": _template("languages", "Languages", ["code", "label"], ["iso639_1", "iso639_2", "native_name", "metadata_json"], "lowercase language code", {"iso639_1": "metadata_json.iso639_1", "iso639_2": "metadata_json.iso639_2"}),
    "service_catalogue": _template("service_catalogue", "Service Catalogue", ["service_key", "label", "category"], ["ssr_code", "rules_category", "emd_applicability", "required_documents_json", "metadata_json"], "uppercase service key", {"service_key": "service_code/service_key", "category": "service_family_code/category"}),
    "service_categories": _template("service_categories", "Service Categories", ["code", "label"], ["default_rules_category", "metadata_json"], "lowercase category key", {"default_rules_category": "metadata_json.default_rules_category"}),
    "ssr_osi_codes": _template("ssr_osi_codes", "SSR / OSI Codes", ["code", "label", "message_type"], ["template", "metadata_json"], "uppercase SSR/OSI code", {"message_type": "metadata_json.message_type"}),
    "document_types": _template("document_types", "Document Types", ["code", "label"], ["validity_rules", "metadata_json"], "lowercase document type key", {"validity_rules": "metadata_json.validity_rules"}),
    "pet_species": _template("pet_species", "Pet Species", ["code", "label"], ["iata_live_animal_category", "metadata_json"], "lowercase species key", {"iata_live_animal_category": "metadata_json.iata_live_animal_category"}),
    "pet_breeds": _template("pet_breeds", "Pet Breeds", ["code", "label", "species_code"], ["snub_nosed", "size_category", "metadata_json"], "lowercase breed key", {"species_code": "metadata_json.species_code"}),
    "special_item_categories": _template("special_item_categories", "Special Item Categories", ["code", "label"], ["fee_expected", "ssr_code", "metadata_json"], "lowercase special-item category key", {"fee_expected": "metadata_json.fee_expected"}),
    "aircraft_types": _template("aircraft_types", "Aircraft Types", ["code", "label"], ["iata_aircraft_code", "icao_aircraft_code", "manufacturer", "metadata_json"], "uppercase aircraft code", {"iata_aircraft_code": "metadata_json.iata_aircraft_code"}),
}


CORE_COLUMNS = {
    "domain",
    "code",
    "label",
    "description",
    "aliases",
    "sort_order",
    "is_active",
    "metadata_json",
    "service_key",
    "service_code",
    "service_label",
    "category",
    "service_family_code",
}


def list_import_templates() -> list[dict[str, Any]]:
    return list(IMPORT_TEMPLATES.values())


def get_import_template(domain_key: str) -> dict[str, Any] | None:
    return IMPORT_TEMPLATES.get(domain_key)


def parse_bool(value: Any, default: bool = True) -> bool:
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "active"}


def parse_int(value: Any, default: int = 100) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_json_object(value: Any, errors: list[str], row_number: int, field: str = "metadata_json") -> dict[str, Any]:
    if value in (None, ""):
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        errors.append(f"Row {row_number}: {field} must be valid JSON.")
        return {}
    if not isinstance(parsed, dict):
        errors.append(f"Row {row_number}: {field} must be a JSON object.")
        return {}
    return parsed


def parse_json_list(value: Any, errors: list[str], row_number: int, field: str) -> list[dict[str, Any]]:
    if value in (None, ""):
        return []
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        errors.append(f"Row {row_number}: {field} must be valid JSON.")
        return []
    if not isinstance(parsed, list):
        errors.append(f"Row {row_number}: {field} must be a JSON array.")
        return []
    return [item for item in parsed if isinstance(item, dict)]


def aliases(value: Any) -> list[str]:
    return [item.strip() for item in str(value or "").replace("|", ",").split(",") if item.strip()]


def normalize_import_code(domain: str, value: Any) -> str:
    if domain == "cities":
        return normalize_city_reference_code(str(value or ""))
    if domain in {"languages", "service_categories", "document_types", "pet_species", "pet_breeds", "special_item_categories"}:
        return normalize_reference_code(str(value or "")).lower()
    return normalize_reference_code(str(value or "")).upper()


def metadata_from_row(domain: str, row: dict[str, Any], row_number: int, errors: list[str]) -> dict[str, Any]:
    metadata = parse_json_object(row.get("metadata_json"), errors, row_number)
    template = IMPORT_TEMPLATES[domain]
    mapped_fields = {
        column
        for column in [*template["required_columns"], *template["optional_columns"]]
        if column not in CORE_COLUMNS and column != "required_documents_json"
    }
    for column in mapped_fields:
        if row.get(column) not in (None, ""):
            metadata[column] = row[column]
    if domain == "cities":
        city_metadata, city_errors = normalize_city_reference_metadata(
            normalize_import_code(domain, row.get("code")),
            row.get("label") or "",
            aliases(row.get("aliases")),
            metadata,
        )
        errors.extend([f"Row {row_number}: {error}" for error in city_errors])
        return city_metadata
    if domain == "passenger_types":
        for field in ("age_min_years", "age_max_years"):
            if metadata.get(field) not in (None, ""):
                try:
                    metadata[field] = int(str(metadata[field]).strip())
                except (TypeError, ValueError):
                    errors.append(f"Row {row_number}: {field} must be a whole number.")
        for field in (
            "requires_date_of_birth",
            "requires_guardian",
            "is_infant",
            "is_child",
            "is_adult",
            "is_senior",
            "applies_to_pricing",
            "applies_to_ticketing",
            "applies_to_services",
            "manual_review_required",
        ):
            if field in metadata:
                metadata[field] = parse_bool(metadata[field], False)
        normalized, metadata_errors = normalize_reference_metadata_for_domain(domain, metadata)
        errors.extend([f"Row {row_number}: {error}" for error in metadata_errors])
        return normalized
    return metadata


def record_payload_from_row(domain: str, row: dict[str, Any], row_number: int, errors: list[str]) -> dict[str, Any]:
    if domain == "service_catalogue":
        required_documents = parse_json_list(row.get("required_documents_json"), errors, row_number, "required_documents_json")
        metadata = parse_json_object(row.get("metadata_json"), errors, row_number)
        return normalize_service_catalogue_payload(
            {
                "service_key": row.get("service_key") or row.get("service_code"),
                "service_code": row.get("service_code") or row.get("service_key"),
                "label": row.get("label") or row.get("service_label"),
                "service_label": row.get("service_label") or row.get("label"),
                "category": row.get("category") or row.get("service_family_code"),
                "service_family_code": row.get("service_family_code") or row.get("category"),
                "description": row.get("description") or None,
                "ssr_code": row.get("ssr_code") or None,
                "default_ssr_code": row.get("ssr_code") or None,
                "rules_category": row.get("rules_category") or None,
                "emd_applicability": row.get("emd_applicability") or "none",
                "required_documents_json": required_documents,
                "sort_order": parse_int(row.get("sort_order")),
                "active": parse_bool(row.get("is_active"), True),
                "is_active": parse_bool(row.get("is_active"), True),
                "metadata_json": metadata,
                "source_type": "import",
            }
        )
    code = normalize_import_code(domain, row.get("code"))
    return {
        "domain": domain,
        "code": code,
        "key": code,
        "label": (row.get("label") or "").strip(),
        "description": (row.get("description") or "").strip() or None,
        "aliases": aliases(row.get("aliases")),
        "sort_order": parse_int(row.get("sort_order")),
        "is_active": parse_bool(row.get("is_active"), True),
        "metadata_json": metadata_from_row(domain, row, row_number, errors),
        "source_type": "import",
    }


async def existing_record(db: Database, domain: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    if domain == "service_catalogue":
        key = normalize_service_key(payload.get("service_key") or payload.get("service_code"))
        records = await db.collection("service_catalogue").find_many()
        for record in records:
            if normalize_service_key(record.get("service_key") or record.get("service_code")) == key:
                return record
        return None
    return await db.collection("global_reference_records").find_one({"domain": domain, "key": payload["key"]})


async def preview_reference_import(db: Database, domain: str, csv_text: str, mode: str = "upsert") -> dict[str, Any]:
    template = get_import_template(domain)
    if not template:
        return {"domain": domain, "valid": False, "rows": [], "summary": {"created": 0, "updated": 0, "skipped": 0, "errors": 1}, "errors": [f"Unsupported import domain: {domain}"]}
    if mode not in {"upsert", "create_only", "update_existing"}:
        return {"domain": domain, "valid": False, "rows": [], "summary": {"created": 0, "updated": 0, "skipped": 0, "errors": 1}, "errors": [f"Unsupported import mode: {mode}"]}

    reader = csv.DictReader(StringIO(csv_text.strip()))
    fieldnames = set(reader.fieldnames or [])
    missing_columns = [column for column in template["required_columns"] if column not in fieldnames]
    errors = [f"Missing required columns: {', '.join(missing_columns)}."] if missing_columns else []
    rows: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    summary = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

    for row_number, row in enumerate(reader, start=2):
        row_errors: list[str] = []
        for column in template["required_columns"]:
            if not str(row.get(column) or "").strip():
                row_errors.append(f"Row {row_number}: {column} is required.")
        payload = record_payload_from_row(domain, row, row_number, row_errors)
        code = normalize_service_key(payload.get("service_key") or payload.get("service_code")) if domain == "service_catalogue" else payload.get("key")
        if not code:
            row_errors.append(f"Row {row_number}: normalized code is blank.")
        if code in seen_codes:
            row_errors.append(f"Row {row_number}: duplicate code {code} within file.")
        seen_codes.add(code)
        found = await existing_record(db, domain, payload) if not row_errors else None
        if not row_errors and domain != "service_catalogue":
            conflict = await find_active_scope_conflict(
                db,
                domain=domain,
                code=payload["code"],
                key=payload["key"],
                scope="global",
                agency_id=None,
                exclude_id=found.get("id") if found else None,
            )
            if conflict:
                row_errors.append(
                    f"Row {row_number}: active code or key conflicts in the effective scope."
                )
            if found and bool(found.get("is_active", True)) != bool(payload.get("is_active", True)):
                row_errors.append(
                    f"Row {row_number}: status changes require the governed deactivate or reactivate action."
                )
        if row_errors:
            action = "error"
            summary["errors"] += 1
        elif found and mode == "create_only":
            action = "skip"
            summary["skipped"] += 1
        elif not found and mode == "update_existing":
            action = "skip"
            summary["skipped"] += 1
        elif found:
            action = "update"
            summary["updated"] += 1
        else:
            action = "create"
            summary["created"] += 1
        rows.append(
            {
                "row_number": row_number,
                "code": code,
                "label": payload.get("label") or payload.get("service_label"),
                "valid": not row_errors,
                "action": action,
                "errors": row_errors,
                "payload": payload,
                "existing_record_id": found.get("id") if found else None,
            }
        )
        errors.extend(row_errors)

    return {
        "domain": domain,
        "template": template,
        "mode": mode,
        "valid": not errors,
        "rows": rows,
        "summary": summary,
        "errors": errors,
    }


async def apply_reference_import(
    db: Database,
    domain: str,
    filename: str,
    csv_text: str,
    mode: str,
    actor_user_id: str,
) -> dict[str, Any]:
    preview = await preview_reference_import(db, domain, csv_text, mode)
    created = 0
    updated = 0
    skipped = 0
    for row in preview["rows"]:
        if not row["valid"] or row["action"] == "skip":
            skipped += 1
            continue
        payload = row["payload"]
        found = await existing_record(db, domain, payload)
        if domain == "service_catalogue":
            if found:
                await update_service_catalogue_record(db, found, payload, actor_user_id)
                updated += 1
            else:
                await insert_service_catalogue_record(db, payload, actor_user_id)
                created += 1
            continue
        if found:
            updates = {
                "label": payload["label"],
                "description": payload.get("description"),
                "aliases": payload.get("aliases") or [],
                "sort_order": payload.get("sort_order", 100),
                "is_active": payload.get("is_active", True),
                "metadata_json": payload.get("metadata_json") or {},
                "metadata": payload.get("metadata_json") or {},
                "source_type": "import",
                "updated_by_user_id": actor_user_id,
            }
            await db.collection("global_reference_records").update_one({"id": found["id"]}, updates)
            updated += 1
        else:
            record = GlobalReferenceRecord(
                **{
                    **payload,
                    "metadata": payload.get("metadata_json") or {},
                    "created_by_user_id": actor_user_id,
                    "updated_by_user_id": actor_user_id,
                }
            )
            await db.collection("global_reference_records").insert_one(record.model_dump(mode="json"))
            created += 1
    skipped += preview["summary"]["errors"]
    status = "imported" if preview["summary"]["errors"] == 0 else "partially_valid"
    batch = ReferenceImportBatch(
        uploaded_by_user_id=actor_user_id,
        scope="global",
        domain=domain,
        filename=filename,
        file_hash=hashlib.sha256(csv_text.encode("utf-8")).hexdigest(),
        status=status,
        total_rows=len(preview["rows"]),
        valid_rows=len([row for row in preview["rows"] if row["valid"]]),
        invalid_rows=len([row for row in preview["rows"] if not row["valid"]]),
        inserted_count=created,
        updated_count=updated,
        skipped_count=skipped,
        error_report_json={"domain_import": preview},
        completed_at=now_utc(),
    )
    import_batch = await db.collection("reference_import_batches").insert_one(batch.model_dump(mode="json"))
    await audit_reference_event(
        db,
        "reference_domain_aware_import_applied",
        "reference_import_batch",
        import_batch["id"],
        f"Domain-aware reference import applied for {domain}.",
        actor_user_id,
        {"domain": domain, "created": created, "updated": updated, "skipped": skipped, "errors": preview["summary"]["errors"]},
    )
    return {
        "batch": safe_reference_import_batch(import_batch),
        "preview": preview,
        "summary": {
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "errors": preview["summary"]["errors"],
        },
    }
