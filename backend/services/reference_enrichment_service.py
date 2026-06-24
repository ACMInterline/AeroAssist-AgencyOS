import csv
import hashlib
import json
import re
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any

from database import Database
from models import GlobalReferenceRecord, ReferenceImportBatch, now_utc
from services.reference_data_service import audit_reference_event, normalize_country_metadata, parse_aliases, safe_reference_import_batch

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "data" / "reference_packs"

UPDATE_MODES = {"insert_only", "update_missing_only", "update_all_non_verified", "force_update"}

ENRICHMENT_TEMPLATES = {
    "countries_enriched": {"domain": "countries", "filename": "countries_enriched.csv", "label": "Countries Enriched"},
    "airports_core": {"domain": "airports", "filename": "airports_core.csv", "label": "Airports Core"},
    "airlines_core": {"domain": "airlines", "filename": "airlines_core.csv", "label": "Airlines Core"},
    "currencies_core": {"domain": "currencies", "filename": "currencies_core.csv", "label": "Currencies Core"},
    "languages_core": {"domain": "languages", "filename": "languages_core.csv", "label": "Languages Core"},
    "continents_regions": {"domain": "continents_regions", "filename": "continents_regions.csv", "label": "Continents / Regions"},
}


@dataclass
class NormalizedRow:
    row_number: int
    domain: str
    code: str
    label: str
    aliases: list[str]
    metadata_json: dict[str, Any]
    is_active: bool
    errors: list[str]
    warnings: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors


def template_path(template_name: str) -> Path:
    template = ENRICHMENT_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"Unsupported enrichment template: {template_name}")
    return TEMPLATE_DIR / template["filename"]


def read_template(template_name: str) -> str:
    path = template_path(template_name)
    return path.read_text(encoding="utf-8")


def list_templates() -> list[dict[str, str]]:
    return [
        {
            "template_name": name,
            "domain": item["domain"],
            "label": item["label"],
            "filename": item["filename"],
        }
        for name, item in ENRICHMENT_TEMPLATES.items()
    ]


def blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def uppercase(value: Any) -> str:
    return str(value or "").strip().upper()


def lowercase(value: Any) -> str:
    return str(value or "").strip().lower()


def optional_float(value: Any, field: str, row_number: int, errors: list[str]) -> float | None:
    if blank(value):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        errors.append(f"Row {row_number}: {field} must be numeric.")
        return None


def optional_int(value: Any, field: str, row_number: int, errors: list[str]) -> int | None:
    if blank(value):
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        errors.append(f"Row {row_number}: {field} must be an integer.")
        return None


def bool_value(value: Any, default: bool = True) -> bool:
    if blank(value):
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "active"}


def validate_pattern(value: str | None, pattern: str, field: str, row_number: int, errors: list[str], required: bool = False) -> str | None:
    if blank(value):
        if required:
            errors.append(f"Row {row_number}: {field} is required.")
        return None
    normalized = str(value).strip()
    if not re.fullmatch(pattern, normalized):
        errors.append(f"Row {row_number}: {field} is invalid.")
    return normalized


def quality_status(row: dict[str, Any]) -> str:
    value = str(row.get("data_quality_status") or "draft").strip().lower()
    return value if value in {"draft", "verified", "needs_review", "deprecated"} else "draft"


def common_metadata(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "data_quality_status": quality_status(row),
        "source_notes": (row.get("source_notes") or "").strip() or None,
    }


async def linked_record_sets(db: Database) -> dict[str, set[str]]:
    records = await db.collection("global_reference_records").find_many()
    result: dict[str, set[str]] = {}
    for domain in ["countries", "airports", "airlines", "currencies", "languages", "continents_regions"]:
        result[domain] = {
            str(item.get("code") or item.get("key") or "").upper()
            for item in records
            if item.get("domain") == domain and item.get("is_active", True)
        }
    return result


def normalize_country_row(row: dict[str, Any], row_number: int, links: dict[str, set[str]]) -> NormalizedRow:
    errors: list[str] = []
    warnings: list[str] = []
    enriched = dict(row)
    enriched["iso2_code"] = uppercase(row.get("iso2_code"))
    enriched["iso3_code"] = uppercase(row.get("iso3_code"))
    enriched["capital_iata_code"] = uppercase(row.get("capital_iata_code"))
    enriched["currency_iso_code"] = uppercase(row.get("currency_iso_code"))
    metadata = normalize_country_metadata(enriched, errors, row_number)
    if not metadata.get("region") and row.get("region"):
        metadata["region"] = row.get("region").strip()
    code = normalize_reference_code(row.get("code") or metadata.get("iso2_code"))
    label = (row.get("label") or "").strip()
    if not code:
        errors.append(f"Row {row_number}: code is required.")
    if not label:
        errors.append(f"Row {row_number}: label is required.")
    missing_links: list[str] = []
    for airport_code in metadata.get("major_airports") or []:
        if airport_code.upper() not in links.get("airports", set()):
            missing_links.append(f"airports:{airport_code}")
    if metadata.get("capital_iata_code") and metadata["capital_iata_code"].upper() not in links.get("airports", set()):
        missing_links.append(f"airports:{metadata['capital_iata_code']}")
    carrier = metadata.get("national_carrier") or {}
    if carrier.get("iata_code") and carrier["iata_code"].upper() not in links.get("airlines", set()):
        missing_links.append(f"airlines:{carrier['iata_code']}")
    for airline in metadata.get("major_airlines") or []:
        if airline.get("iata_code") and airline["iata_code"].upper() not in links.get("airlines", set()):
            missing_links.append(f"airlines:{airline['iata_code']}")
    if metadata.get("currency_iso_code") and metadata["currency_iso_code"].upper() not in links.get("currencies", set()):
        missing_links.append(f"currencies:{metadata['currency_iso_code']}")
    if missing_links:
        warnings.append(f"Missing linked records: {', '.join(sorted(set(missing_links)))}")
        metadata["missing_links"] = sorted(set(missing_links))
    metadata["major_airport_codes"] = metadata.get("major_airports") or []
    metadata["national_carrier_iata"] = carrier.get("iata_code")
    metadata["major_airline_iata_codes"] = [item.get("iata_code") for item in metadata.get("major_airlines") or [] if item.get("iata_code")]
    metadata["official_language_codes"] = [item for item in metadata.get("official_languages") or [] if len(str(item)) <= 3]
    metadata["official_language_names"] = metadata.get("official_languages") or []
    return NormalizedRow(row_number, "countries", code, label, parse_aliases(row.get("aliases")), metadata, True, errors, warnings)


def normalize_airport_row(row: dict[str, Any], row_number: int, links: dict[str, set[str]]) -> NormalizedRow:
    errors: list[str] = []
    warnings: list[str] = []
    iata = validate_pattern(uppercase(row.get("iata_code") or row.get("code")), r"[A-Z]{3}", "airport IATA", row_number, errors, True)
    icao = validate_pattern(uppercase(row.get("icao_code")), r"[A-Z]{4}", "airport ICAO", row_number, errors, False)
    country_iso2 = validate_pattern(uppercase(row.get("country_iso2")), r"[A-Z]{2}", "country ISO2", row_number, errors, False)
    country_iso3 = validate_pattern(uppercase(row.get("country_iso3")), r"[A-Z]{3}", "country ISO3", row_number, errors, False)
    label = (row.get("label") or "").strip()
    if not label:
        errors.append(f"Row {row_number}: label is required.")
    if country_iso2 and country_iso2 not in links.get("countries", set()) and uppercase(row.get("country_code")) not in links.get("countries", set()):
        warnings.append(f"Missing linked records: countries:{country_iso2}")
    latitude = optional_float(row.get("latitude"), "latitude", row_number, errors)
    longitude = optional_float(row.get("longitude"), "longitude", row_number, errors)
    metadata = {
        **common_metadata(row),
        "iata_code": iata,
        "icao_code": icao,
        "city": (row.get("city") or "").strip() or None,
        "country_iso2": country_iso2,
        "country_iso3": country_iso3,
        "country_code": uppercase(row.get("country_code")) or country_iso2,
        "timezone": (row.get("timezone") or "").strip() or None,
        "latitude": latitude,
        "longitude": longitude,
        "airport_type": (row.get("airport_type") or "").strip() or None,
        "is_major_airport": bool_value(row.get("is_major_airport"), False),
    }
    return NormalizedRow(row_number, "airports", iata or uppercase(row.get("code")), label, parse_aliases(row.get("aliases")), {k: v for k, v in metadata.items() if v is not None}, True, errors, warnings)


def normalize_airline_row(row: dict[str, Any], row_number: int, links: dict[str, set[str]]) -> NormalizedRow:
    errors: list[str] = []
    warnings: list[str] = []
    iata = validate_pattern(uppercase(row.get("iata_code")), r"[A-Z0-9]{2}", "airline IATA", row_number, errors, False)
    icao = validate_pattern(uppercase(row.get("icao_code")), r"[A-Z]{3}", "airline ICAO", row_number, errors, False)
    code = uppercase(row.get("code")) or iata or icao
    label = (row.get("label") or "").strip()
    if not code:
        errors.append(f"Row {row_number}: code, iata_code, or icao_code is required.")
    if not label:
        errors.append(f"Row {row_number}: label is required.")
    country_iso2 = validate_pattern(uppercase(row.get("country_iso2")), r"[A-Z]{2}", "country ISO2", row_number, errors, False)
    country_iso3 = validate_pattern(uppercase(row.get("country_iso3")), r"[A-Z]{3}", "country ISO3", row_number, errors, False)
    if country_iso2 and country_iso2 not in links.get("countries", set()) and uppercase(row.get("country_code")) not in links.get("countries", set()):
        warnings.append(f"Missing linked records: countries:{country_iso2}")
    metadata = {
        **common_metadata(row),
        "iata_code": iata,
        "icao_code": icao,
        "country_iso2": country_iso2,
        "country_iso3": country_iso3,
        "country_code": uppercase(row.get("country_code")) or country_iso2,
        "airline_type": (row.get("airline_type") or "").strip() or None,
        "is_national_carrier": bool_value(row.get("is_national_carrier"), False),
        "active": bool_value(row.get("active"), True),
    }
    return NormalizedRow(row_number, "airlines", code, label, parse_aliases(row.get("aliases")), {k: v for k, v in metadata.items() if v is not None}, bool_value(row.get("active"), True), errors, warnings)


def normalize_currency_row(row: dict[str, Any], row_number: int, links: dict[str, set[str]]) -> NormalizedRow:
    errors: list[str] = []
    currency_iso = validate_pattern(uppercase(row.get("currency_iso_code") or row.get("code")), r"[A-Z]{3}", "currency ISO", row_number, errors, True)
    label = (row.get("label") or row.get("currency_name") or "").strip()
    if not label:
        errors.append(f"Row {row_number}: label is required.")
    metadata = {
        **common_metadata(row),
        "currency_iso_code": currency_iso,
        "currency_name": (row.get("currency_name") or label).strip(),
        "numeric_code": optional_int(row.get("numeric_code"), "numeric_code", row_number, errors),
        "minor_unit": optional_int(row.get("minor_unit"), "minor_unit", row_number, errors),
        "symbol": (row.get("symbol") or "").strip() or None,
    }
    return NormalizedRow(row_number, "currencies", currency_iso or uppercase(row.get("code")), label, parse_aliases(row.get("aliases")), {k: v for k, v in metadata.items() if v is not None}, True, errors, [])


def normalize_language_row(row: dict[str, Any], row_number: int, links: dict[str, set[str]]) -> NormalizedRow:
    errors: list[str] = []
    iso1 = validate_pattern(lowercase(row.get("iso639_1") or row.get("code")), r"[a-z]{2}", "language ISO639-1", row_number, errors, False)
    iso2 = validate_pattern(lowercase(row.get("iso639_2")), r"[a-z]{3}", "language ISO639-2", row_number, errors, False)
    code = lowercase(row.get("code")) or iso1 or iso2
    label = (row.get("label") or row.get("name") or "").strip()
    if not code:
        errors.append(f"Row {row_number}: code or ISO language code is required.")
    if not label:
        errors.append(f"Row {row_number}: label is required.")
    metadata = {
        **common_metadata(row),
        "iso639_1": iso1,
        "iso639_2": iso2,
        "name": (row.get("name") or label).strip(),
        "native_name": (row.get("native_name") or "").strip() or None,
    }
    return NormalizedRow(row_number, "languages", code, label, parse_aliases(row.get("aliases")), {k: v for k, v in metadata.items() if v is not None}, True, errors, [])


def normalize_region_row(row: dict[str, Any], row_number: int, links: dict[str, set[str]]) -> NormalizedRow:
    errors: list[str] = []
    warnings: list[str] = []
    code = uppercase(row.get("code"))
    label = (row.get("label") or "").strip()
    parent = uppercase(row.get("parent_region_code"))
    if not code:
        errors.append(f"Row {row_number}: code is required.")
    if not label:
        errors.append(f"Row {row_number}: label is required.")
    if parent and parent not in links.get("continents_regions", set()):
        warnings.append(f"Missing linked records: continents_regions:{parent}")
    metadata = {
        **common_metadata(row),
        "parent_region_code": parent or None,
        "region_type": (row.get("region_type") or "region").strip(),
    }
    return NormalizedRow(row_number, "continents_regions", code, label, parse_aliases(row.get("aliases")), {k: v for k, v in metadata.items() if v is not None}, True, errors, warnings)


NORMALIZERS = {
    "countries": normalize_country_row,
    "airports": normalize_airport_row,
    "airlines": normalize_airline_row,
    "currencies": normalize_currency_row,
    "languages": normalize_language_row,
    "continents_regions": normalize_region_row,
}


def normalize_reference_code(value: Any) -> str:
    return str(value or "").strip()


def merge_missing(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key, value in incoming.items():
        if blank(value):
            continue
        if key not in merged or blank(merged.get(key)) or merged.get(key) == [] or merged.get(key) == {}:
            merged[key] = value
    return merged


def should_update(existing: dict[str, Any], update_mode: str) -> bool:
    if update_mode == "insert_only":
        return False
    if update_mode == "force_update":
        return True
    quality = (existing.get("metadata_json") or existing.get("metadata") or {}).get("data_quality_status")
    if quality == "verified":
        return False
    return update_mode in {"update_missing_only", "update_all_non_verified"}


def build_updates(existing: dict[str, Any], row: NormalizedRow, update_mode: str, actor_user_id: str) -> dict[str, Any]:
    existing_metadata = existing.get("metadata_json") or existing.get("metadata") or {}
    if update_mode == "update_missing_only":
        metadata = merge_missing(existing_metadata, row.metadata_json)
    else:
        metadata = dict(row.metadata_json)
    return {
        "label": row.label if update_mode in {"update_all_non_verified", "force_update"} or not existing.get("label") else existing.get("label"),
        "aliases": row.aliases if update_mode in {"update_all_non_verified", "force_update"} or not existing.get("aliases") else existing.get("aliases"),
        "metadata_json": metadata,
        "metadata": metadata,
        "is_active": row.is_active,
        "source_type": "import",
        "updated_by_user_id": actor_user_id,
    }


async def run_reference_enrichment_import(
    db: Database,
    domain: str,
    csv_text: str,
    actor_user_id: str,
    update_mode: str = "update_missing_only",
    dry_run: bool = True,
    source_label: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    if domain not in NORMALIZERS:
        raise ValueError(f"Unsupported enrichment domain: {domain}")
    if update_mode not in UPDATE_MODES:
        raise ValueError(f"Unsupported update mode: {update_mode}")
    links = await linked_record_sets(db)
    reader = csv.DictReader(StringIO(csv_text.strip()))
    rows: list[NormalizedRow] = []
    duplicate_codes: set[str] = set()
    seen_codes: set[str] = set()
    for row_number, row in enumerate(reader, start=2):
        normalized = NORMALIZERS[domain](row, row_number, links)
        if normalized.code in seen_codes:
            normalized.errors.append(f"Row {row_number}: duplicate code {normalized.code} within file.")
            duplicate_codes.add(normalized.code)
        seen_codes.add(normalized.code)
        rows.append(normalized)

    report: dict[str, Any] = {
        "domain": domain,
        "update_mode": update_mode,
        "dry_run": dry_run,
        "source_label": source_label,
        "notes": notes,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "warnings": [],
        "missing_links": [],
        "rows": [],
        "duplicate_codes": sorted(duplicate_codes),
    }

    for row in rows:
        row_report = {
            "row_number": row.row_number,
            "code": row.code,
            "label": row.label,
            "valid": row.valid,
            "errors": row.errors,
            "warnings": row.warnings,
            "action": "failed" if not row.valid else "pending",
        }
        if row.warnings:
            report["warnings"].extend(row.warnings)
            for warning in row.warnings:
                if "Missing linked records:" in warning:
                    report["missing_links"].extend([item.strip() for item in warning.split(":", 1)[1].split(",")])
        if not row.valid:
            report["failed"] += 1
            report["rows"].append(row_report)
            continue
        existing = await db.collection("global_reference_records").find_one({"domain": row.domain, "key": row.code})
        if existing and not should_update(existing, update_mode):
            report["skipped"] += 1
            row_report["action"] = "skipped"
            report["rows"].append(row_report)
            continue
        if existing:
            report["updated"] += 1
            row_report["action"] = "updated"
            if not dry_run:
                await db.collection("global_reference_records").update_one({"id": existing["id"]}, build_updates(existing, row, update_mode, actor_user_id))
        else:
            report["inserted"] += 1
            row_report["action"] = "inserted"
            if not dry_run:
                record = GlobalReferenceRecord(
                    domain=row.domain,
                    code=row.code,
                    key=row.code,
                    label=row.label,
                    aliases=row.aliases,
                    metadata_json=row.metadata_json,
                    metadata=row.metadata_json,
                    source_type="import",
                    is_active=row.is_active,
                    created_by_user_id=actor_user_id,
                    updated_by_user_id=actor_user_id,
                )
                await db.collection("global_reference_records").insert_one(record.model_dump(mode="json"))
        report["rows"].append(row_report)

    report["warnings"] = sorted(set(report["warnings"]))
    report["missing_links"] = sorted(set(item for item in report["missing_links"] if item))
    status = "validated" if report["failed"] == 0 else "partially_valid"
    if rows and report["failed"] == len(rows):
        status = "failed"
    batch = ReferenceImportBatch(
        uploaded_by_user_id=actor_user_id,
        scope="global",
        domain=domain,
        filename=f"{domain}_enrichment.csv",
        file_hash=hashlib.sha256(csv_text.encode("utf-8")).hexdigest(),
        status=status if dry_run else ("imported" if report["failed"] == 0 else "partially_valid"),
        total_rows=len(rows),
        valid_rows=len([row for row in rows if row.valid]),
        invalid_rows=len([row for row in rows if not row.valid]),
        inserted_count=0 if dry_run else report["inserted"],
        updated_count=0 if dry_run else report["updated"],
        skipped_count=report["skipped"],
        error_report_json={"enrichment": report},
        completed_at=None if dry_run else now_utc(),
    )
    created = await db.collection("reference_import_batches").insert_one(batch.model_dump(mode="json"))
    await audit_reference_event(
        db,
        "reference_enrichment_import_dry_run" if dry_run else "reference_enrichment_import_committed",
        "reference_import_batch",
        created["id"],
        f"Reference enrichment {'dry run' if dry_run else 'import'} for {domain}.",
        actor_user_id,
        {"domain": domain, "update_mode": update_mode, "inserted": report["inserted"], "updated": report["updated"], "failed": report["failed"]},
    )
    return {"batch": safe_reference_import_batch(created), "report": report}
