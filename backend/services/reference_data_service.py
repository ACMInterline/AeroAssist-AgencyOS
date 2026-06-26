import csv
import hashlib
import json
import re
from io import StringIO
from typing import Any

from database import Database
from models import AuditEvent, GlobalReferenceRecord, ReferenceImportBatch, ServiceCatalogueRecord, now_utc


REFERENCE_DOMAINS = {
    "countries": "Countries",
    "cities": "Cities",
    "airports": "Airports",
    "airlines": "Airlines",
    "currencies": "Currencies",
    "timezones": "Time zones",
    "languages": "Languages",
    "continents_regions": "Continents / regions",
    "payment_methods": "Payment methods",
    "client_types": "Client types",
    "contact_channels": "Contact channels",
    "document_types": "Document types",
    "cabin_classes": "Cabin classes",
    "passenger_types": "Passenger types",
    "guardian_relationships": "Guardian relationships",
    "mobility_levels": "Mobility levels",
    "wheelchair_device_types": "Wheelchair device types",
    "medical_equipment_types": "Medical equipment types",
    "battery_types": "Battery types",
    "pet_species": "Pet species",
    "pet_breeds": "Pet breeds",
    "special_item_categories": "Special item categories",
}

SERVICE_FAMILIES = [
    {"code": "wheelchair_mobility", "label": "Wheelchair and mobility assistance", "sort_order": 10},
    {"code": "sensory_assistance", "label": "Sensory assistance", "sort_order": 20},
    {"code": "medical_assistance", "label": "Medical assistance", "sort_order": 30},
    {"code": "seating_space", "label": "Seating and additional space", "sort_order": 40},
    {"code": "pets_animals", "label": "Pets and service animals", "sort_order": 50},
    {"code": "minor_assistance", "label": "Minor assistance", "sort_order": 60},
    {"code": "special_items", "label": "Special items and equipment", "sort_order": 70},
]

REFERENCE_BOOTSTRAP_RECORDS = {
    "countries": [
        {
            "code": "BG",
            "label": "Bulgaria",
            "aliases": ["Republic of Bulgaria"],
            "sort_order": 10,
            "metadata_json": {
                "iso2_code": "BG",
                "iso3_code": "BGR",
                "continent": "Europe",
                "capital_city": "Sofia",
                "capital_iata_code": "SOF",
                "major_airports": ["SOF", "VAR", "BOJ"],
                "official_languages": ["Bulgarian"],
                "currency_name": "Bulgarian lev",
                "currency_iso_code": "BGN",
                "national_carrier": {"name": "Bulgaria Air", "iata_code": "FB"},
                "major_airlines": [{"name": "Bulgaria Air", "iata_code": "FB"}],
                "data_quality_status": "draft",
                "source_notes": "Seed metadata for platform review.",
            },
        },
        {
            "code": "US",
            "label": "United States",
            "aliases": ["USA", "United States of America"],
            "sort_order": 20,
            "metadata_json": {
                "iso2_code": "US",
                "iso3_code": "USA",
                "continent": "North America",
                "capital_city": "Washington, D.C.",
                "capital_iata_code": "DCA",
                "major_airports": ["JFK", "LAX", "ORD"],
                "official_languages": ["English"],
                "currency_name": "US dollar",
                "currency_iso_code": "USD",
                "national_carrier": {"name": "No single designated national carrier"},
                "major_airlines": [
                    {"name": "American Airlines", "iata_code": "AA"},
                    {"name": "Delta Air Lines", "iata_code": "DL"},
                    {"name": "United Airlines", "iata_code": "UA"},
                ],
                "data_quality_status": "draft",
                "source_notes": "Seed metadata for platform review.",
            },
        },
        {
            "code": "GB",
            "label": "United Kingdom",
            "aliases": ["UK", "Great Britain"],
            "sort_order": 30,
            "metadata_json": {
                "iso2_code": "GB",
                "iso3_code": "GBR",
                "continent": "Europe",
                "capital_city": "London",
                "capital_iata_code": "LHR",
                "major_airports": ["LHR", "LGW", "MAN"],
                "official_languages": ["English"],
                "currency_name": "Pound sterling",
                "currency_iso_code": "GBP",
                "national_carrier": {"name": "British Airways", "iata_code": "BA"},
                "major_airlines": [
                    {"name": "British Airways", "iata_code": "BA"},
                    {"name": "Virgin Atlantic", "iata_code": "VS"},
                    {"name": "easyJet", "iata_code": "U2"},
                ],
                "data_quality_status": "draft",
                "source_notes": "Seed metadata for platform review.",
            },
        },
    ],
    "cities": [
        {"code": "SOF", "label": "Sofia", "aliases": ["SOFIA"], "metadata_json": {"country_code": "BG"}, "sort_order": 10},
        {"code": "NYC", "label": "New York", "aliases": ["NEW_YORK"], "metadata_json": {"country_code": "US"}, "sort_order": 20},
        {"code": "LON", "label": "London", "aliases": ["LONDON"], "metadata_json": {"country_code": "GB"}, "sort_order": 30},
    ],
    "airports": [
        {"code": "SOF", "label": "Sofia Airport", "metadata_json": {"city_code": "SOF", "country_code": "BG"}, "sort_order": 10},
        {"code": "JFK", "label": "John F. Kennedy International Airport", "metadata_json": {"city_code": "NYC", "country_code": "US"}, "sort_order": 20},
        {"code": "LHR", "label": "London Heathrow Airport", "metadata_json": {"city_code": "LON", "country_code": "GB"}, "sort_order": 30},
    ],
    "airlines": [
        {"code": "LH", "label": "Lufthansa", "aliases": ["Lufthansa German Airlines"], "sort_order": 10},
        {"code": "BA", "label": "British Airways", "sort_order": 20},
        {"code": "AA", "label": "American Airlines", "sort_order": 30},
    ],
    "currencies": [
        {"code": "EUR", "label": "Euro", "sort_order": 10},
        {"code": "USD", "label": "US Dollar", "sort_order": 20},
        {"code": "GBP", "label": "Pound Sterling", "sort_order": 30},
    ],
    "timezones": [
        {"code": "Europe/Sofia", "label": "Europe/Sofia", "sort_order": 10},
        {"code": "UTC", "label": "UTC", "sort_order": 20},
        {"code": "America/New_York", "label": "America/New York", "sort_order": 30},
    ],
    "languages": [
        {"code": "en", "label": "English", "sort_order": 10},
        {"code": "bg", "label": "Bulgarian", "sort_order": 20},
        {"code": "de", "label": "German", "sort_order": 30},
    ],
    "payment_methods": [
        {"code": "card", "label": "Card", "sort_order": 10},
        {"code": "bank_transfer", "label": "Bank transfer", "sort_order": 20},
        {"code": "cash", "label": "Cash", "sort_order": 30},
    ],
    "client_types": [
        {"code": "individual", "label": "Individual", "sort_order": 10},
        {"code": "corporate", "label": "Corporate", "sort_order": 20},
        {"code": "partner_agency", "label": "Partner agency", "sort_order": 30},
    ],
    "contact_channels": [
        {"code": "email", "label": "Email", "sort_order": 10},
        {"code": "phone", "label": "Phone", "sort_order": 20},
        {"code": "whatsapp", "label": "WhatsApp", "sort_order": 30},
    ],
    "document_types": [
        {"code": "passport", "label": "Passport", "sort_order": 10},
        {"code": "id_card", "label": "ID card", "sort_order": 20},
        {"code": "visa", "label": "Visa", "sort_order": 30},
        {"code": "medical_certificate", "label": "Medical certificate", "sort_order": 40},
    ],
    "cabin_classes": [
        {"code": "economy", "label": "Economy", "sort_order": 10},
        {"code": "premium_economy", "label": "Premium economy", "sort_order": 20},
        {"code": "business", "label": "Business", "sort_order": 30},
        {"code": "first", "label": "First", "sort_order": 40},
    ],
    "passenger_types": [
        {"code": "adult", "label": "Adult", "aliases": ["ADT"], "sort_order": 10},
        {"code": "child", "label": "Child", "aliases": ["CHD"], "sort_order": 20},
        {"code": "infant", "label": "Infant", "aliases": ["INF"], "sort_order": 30},
    ],
    "guardian_relationships": [
        {"code": "parent", "label": "Parent", "sort_order": 10},
        {"code": "legal_guardian", "label": "Legal guardian", "sort_order": 20},
        {"code": "authorized_companion", "label": "Authorized companion", "sort_order": 30},
    ],
    "mobility_levels": [
        {"code": "wchr", "label": "Can walk short distances and stairs", "aliases": ["WCHR"], "sort_order": 10},
        {"code": "wchs", "label": "Cannot use stairs", "aliases": ["WCHS"], "sort_order": 20},
        {"code": "wchc", "label": "Cannot walk to seat", "aliases": ["WCHC"], "sort_order": 30},
    ],
    "wheelchair_device_types": [
        {"code": "manual_wheelchair", "label": "Manual wheelchair", "sort_order": 10},
        {"code": "powered_wheelchair", "label": "Powered wheelchair", "sort_order": 20},
        {"code": "mobility_scooter", "label": "Mobility scooter", "sort_order": 30},
    ],
    "medical_equipment_types": [
        {"code": "oxygen", "label": "Oxygen", "sort_order": 10},
        {"code": "poc", "label": "Portable oxygen concentrator", "aliases": ["POC"], "sort_order": 20},
        {"code": "cpap", "label": "CPAP device", "sort_order": 30},
    ],
    "battery_types": [
        {"code": "dry_cell", "label": "Dry cell battery", "sort_order": 10},
        {"code": "wet_cell", "label": "Wet cell battery", "sort_order": 20},
        {"code": "lithium_ion", "label": "Lithium-ion battery", "sort_order": 30},
    ],
    "pet_species": [
        {"code": "dog", "label": "Dog", "sort_order": 10},
        {"code": "cat", "label": "Cat", "sort_order": 20},
    ],
    "pet_breeds": [
        {"code": "dog_other", "label": "Dog - other breed", "metadata_json": {"species_code": "dog"}, "sort_order": 10},
        {"code": "cat_other", "label": "Cat - other breed", "metadata_json": {"species_code": "cat"}, "sort_order": 20},
    ],
    "special_item_categories": [
        {"code": "sports_equipment", "label": "Sports equipment", "sort_order": 10},
        {"code": "musical_instrument", "label": "Musical instrument", "sort_order": 20},
        {"code": "fragile_valuable", "label": "Fragile or valuable item", "sort_order": 30},
    ],
}

CITY_CODE_MIGRATIONS = {
    "SOFIA": "SOF",
    "NEW_YORK": "NYC",
    "LONDON": "LON",
}

CITY_CANONICAL_METADATA_KEYS = {"record_type", "iata_city_code", "city_name", "legacy_codes", "country_code"}

SERVICE_CATALOGUE_BOOTSTRAP_RECORDS = [
    {"service_code": "WCHR", "service_label": "Wheelchair assistance to/from gate", "service_family_code": "wheelchair_mobility", "default_ssr_code": "WCHR", "sort_order": 10, "input_schema_json": {"mobility_level": "wchr"}},
    {"service_code": "WCHS", "service_label": "Wheelchair assistance including stairs", "service_family_code": "wheelchair_mobility", "default_ssr_code": "WCHS", "sort_order": 20, "input_schema_json": {"mobility_level": "wchs"}},
    {"service_code": "WCHC", "service_label": "Full wheelchair assistance to cabin seat", "service_family_code": "wheelchair_mobility", "default_ssr_code": "WCHC", "sort_order": 30, "input_schema_json": {"mobility_level": "wchc"}},
    {"service_code": "BLND", "service_label": "Blind or low-vision passenger assistance", "service_family_code": "sensory_assistance", "default_ssr_code": "BLND", "sort_order": 40},
    {"service_code": "DEAF", "service_label": "Deaf or hard-of-hearing passenger assistance", "service_family_code": "sensory_assistance", "default_ssr_code": "DEAF", "sort_order": 50},
    {"service_code": "DPNA", "service_label": "Developmental or intellectual disability assistance", "service_family_code": "sensory_assistance", "default_ssr_code": "DPNA", "sort_order": 60},
    {"service_code": "MEDA", "service_label": "Medical case requiring airline review", "service_family_code": "medical_assistance", "default_ssr_code": "MEDA", "requires_document_check": True, "sort_order": 70},
    {"service_code": "STCR", "service_label": "Stretcher assistance", "service_family_code": "medical_assistance", "default_ssr_code": "STCR", "requires_document_check": True, "requires_manual_pricing": True, "sort_order": 80},
    {"service_code": "OXYG", "service_label": "Medical oxygen request", "service_family_code": "medical_assistance", "default_ssr_code": "OXYG", "requires_document_check": True, "requires_manual_pricing": True, "sort_order": 90},
    {"service_code": "POC", "service_label": "Portable oxygen concentrator", "service_family_code": "medical_assistance", "default_ssr_code": "POC", "requires_document_check": True, "sort_order": 100},
    {"service_code": "EXST", "service_label": "Extra seat request", "service_family_code": "seating_space", "default_ssr_code": "EXST", "requires_manual_pricing": True, "sort_order": 110},
    {"service_code": "PETC", "service_label": "Pet in cabin", "service_family_code": "pets_animals", "default_ssr_code": "PETC", "beneficiary_type": "pet", "requires_manual_pricing": True, "sort_order": 120},
    {"service_code": "AVIH", "service_label": "Pet as checked baggage", "service_family_code": "pets_animals", "default_ssr_code": "AVIH", "beneficiary_type": "pet", "requires_manual_pricing": True, "sort_order": 130},
    {"service_code": "SVAN", "service_label": "Service animal", "service_family_code": "pets_animals", "default_ssr_code": "SVAN", "beneficiary_type": "pet", "requires_document_check": True, "sort_order": 140},
    {"service_code": "UMNR", "service_label": "Unaccompanied minor", "service_family_code": "minor_assistance", "default_ssr_code": "UMNR", "requires_document_check": True, "requires_manual_pricing": True, "sort_order": 150},
    {"service_code": "MOBILITY_DEVICE", "service_label": "Mobility device carriage", "service_family_code": "special_items", "default_ssr_code": "WCBD", "beneficiary_type": "special_item", "requires_document_check": True, "sort_order": 160},
    {"service_code": "SPORTS_EQUIPMENT", "service_label": "Sports equipment", "service_family_code": "special_items", "beneficiary_type": "special_item", "requires_manual_pricing": True, "sort_order": 170},
    {"service_code": "MUSICAL_INSTRUMENT", "service_label": "Musical instrument", "service_family_code": "special_items", "beneficiary_type": "special_item", "requires_manual_pricing": True, "sort_order": 180},
    {"service_code": "FRAGILE_VALUABLE", "service_label": "Fragile or valuable item", "service_family_code": "special_items", "beneficiary_type": "special_item", "requires_manual_pricing": True, "sort_order": 190},
]


def normalize_reference_code(value: str) -> str:
    return value.strip()


def normalize_city_reference_code(value: str) -> str:
    return normalize_reference_code(value).upper()


def normalize_city_reference_metadata(
    code: str,
    label: str,
    aliases: list[str] | None,
    metadata: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    normalized_code = normalize_city_reference_code(code)
    source = dict(metadata or {})
    record_type = source.get("record_type") or "city"
    if record_type == "city" and not re.fullmatch(r"[A-Z]{3}", normalized_code):
        errors.append("City reference code must be the canonical 3-letter IATA city code.")
    if source.get("iata_city_code") and normalize_city_reference_code(str(source["iata_city_code"])) != normalized_code:
        errors.append("City metadata iata_city_code must match the canonical city code.")
    if source.get("city_name") and str(source["city_name"]).strip() != str(label or "").strip():
        errors.append("City metadata city_name must match the city label.")
    extra = {key: value for key, value in source.items() if key not in CITY_CANONICAL_METADATA_KEYS}
    country_code = source.get("country_code")
    metadata_json = {
        **extra,
        "record_type": record_type,
        "iata_city_code": normalized_code,
        "city_name": str(label or "").strip(),
        "legacy_codes": [str(alias).strip().upper() for alias in (aliases or []) if str(alias).strip()],
    }
    if country_code:
        metadata_json["country_code"] = str(country_code).strip().upper()
    return metadata_json, errors


def sort_records(records: list[dict[str, Any]], code_field: str = "code", label_field: str = "label") -> list[dict[str, Any]]:
    return sorted(records, key=lambda item: (item.get("sort_order", 100), str(item.get(label_field) or ""), str(item.get(code_field) or "")))


def safe_reference_record(record: dict[str, Any]) -> dict[str, Any]:
    metadata_json = record.get("metadata_json") or record.get("metadata") or {}
    code = record.get("code") or record.get("key")
    return {
        **record,
        "code": code,
        "key": record.get("key") or code,
        "metadata_json": metadata_json,
        "metadata": record.get("metadata") or metadata_json,
    }


def safe_reference_suggestion(record: dict[str, Any]) -> dict[str, Any]:
    return {**record, "suggested_metadata_json": record.get("suggested_metadata_json") or {}}


def safe_reference_import_batch(record: dict[str, Any]) -> dict[str, Any]:
    return {**record, "error_report_json": record.get("error_report_json") or {}}


DATA_QUALITY_STATUSES = {"draft", "verified", "needs_review", "deprecated"}
COUNTRY_METADATA_FIELDS = [
    "iso2_code",
    "iso3_code",
    "continent",
    "region",
    "capital_city",
    "capital_iata_code",
    "major_airports",
    "official_languages",
    "currency_name",
    "currency_iso_code",
    "population_estimate",
    "population_estimate_year",
    "national_carrier",
    "major_airlines",
    "travel_notes",
    "data_quality_status",
    "source_notes",
    "updated_by_user_id",
    "reviewed_by_user_id",
    "reviewed_at",
]
COUNTRY_IMPORT_COLUMNS = {
    *COUNTRY_METADATA_FIELDS,
    "national_carrier_name",
    "national_carrier_iata_code",
    "major_airport_1",
    "major_airport_2",
    "major_airport_3",
    "official_language_1",
    "official_language_2",
    "official_language_3",
    "major_airline_1_name",
    "major_airline_1_iata_code",
    "major_airline_2_name",
    "major_airline_2_iata_code",
    "major_airline_3_name",
    "major_airline_3_iata_code",
}
REFERENCE_DOMAIN_METADATA_SCHEMAS = {
    "countries": {
        "label": "Country enrichment metadata",
        "fields": COUNTRY_METADATA_FIELDS,
        "array_max": 3,
        "quality_statuses": sorted(DATA_QUALITY_STATUSES),
    }
}


def _row_prefix(row_number: int | None) -> str:
    return f"Row {row_number}: " if row_number else ""


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _split_values(value: Any) -> list[str]:
    if _blank(value):
        return []
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            values.extend(_split_values(item))
        return values
    if isinstance(value, str):
        if value.strip().startswith("["):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if not _blank(item)]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in re.split(r"[|,;]", value) if item.strip()]
    return [str(value).strip()]


def _validate_max_three(values: list[Any], field: str, errors: list[str], row_number: int | None) -> list[Any]:
    if len(values) > 3:
        errors.append(f"{_row_prefix(row_number)}{field} supports at most 3 values.")
        return values[:3]
    return values


def _uppercase_code(value: Any, pattern: str, field: str, errors: list[str], row_number: int | None) -> str | None:
    if _blank(value):
        return None
    code = str(value).strip().upper()
    if not re.fullmatch(pattern, code):
        errors.append(f"{_row_prefix(row_number)}{field} must match {pattern}.")
    return code


def _parse_optional_int(value: Any, field: str, errors: list[str], row_number: int | None) -> int | None:
    if _blank(value):
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        errors.append(f"{_row_prefix(row_number)}{field} must be an integer.")
        return None


def _normalize_airport_list(value: Any, errors: list[str], row_number: int | None) -> list[str]:
    airports = [_uppercase_code(item, r"[A-Z]{3}", "airport IATA code", errors, row_number) for item in _split_values(value)]
    return _validate_max_three([item for item in airports if item], "major_airports", errors, row_number)


def _normalize_language_list(value: Any, errors: list[str], row_number: int | None) -> list[str]:
    return _validate_max_three(_split_values(value), "official_languages", errors, row_number)


def _normalize_airline(value: Any, errors: list[str], row_number: int | None) -> dict[str, Any] | None:
    if _blank(value):
        return None
    airline = value if isinstance(value, dict) else {"name": str(value).strip()}
    name = str(airline.get("name") or "").strip()
    iata = _uppercase_code(airline.get("iata_code"), r"[A-Z0-9]{2}", "airline IATA code", errors, row_number)
    if not name and not iata:
        return None
    return {"name": name or None, "iata_code": iata}


def _normalize_airline_list(value: Any, errors: list[str], row_number: int | None) -> list[dict[str, Any]]:
    if _blank(value):
        return []
    if isinstance(value, str) and value.strip().startswith("["):
        try:
            parsed = json.loads(value)
            value = parsed if isinstance(parsed, list) else value
        except json.JSONDecodeError:
            pass
    if isinstance(value, str):
        items = []
        for item in _split_values(value):
            if ":" in item:
                name, iata = item.rsplit(":", 1)
                items.append({"name": name.strip(), "iata_code": iata.strip()})
            else:
                items.append({"name": item})
    elif isinstance(value, list):
        items = []
        for item in value:
            if isinstance(item, list):
                items.extend(item)
            else:
                items.append(item)
    else:
        items = [value]
    airlines = [_normalize_airline(item, errors, row_number) for item in items]
    return _validate_max_three([item for item in airlines if item], "major_airlines", errors, row_number)


def country_enrichment_complete(metadata: dict[str, Any] | None) -> bool:
    metadata = metadata or {}
    return all(
        [
            metadata.get("iso3_code"),
            metadata.get("capital_iata_code"),
            metadata.get("currency_iso_code"),
            metadata.get("major_airports"),
            metadata.get("national_carrier"),
        ]
    )


def normalize_country_metadata(raw: dict[str, Any] | None, errors: list[str] | None = None, row_number: int | None = None) -> dict[str, Any]:
    errors = errors if errors is not None else []
    raw = raw or {}
    normalized = {
        key: value
        for key, value in raw.items()
        if key not in COUNTRY_IMPORT_COLUMNS and not _blank(value)
    }

    simple_fields = [
        "continent",
        "region",
        "capital_city",
        "currency_name",
        "travel_notes",
        "source_notes",
        "updated_by_user_id",
        "reviewed_by_user_id",
        "reviewed_at",
    ]
    for field in simple_fields:
        if not _blank(raw.get(field)):
            normalized[field] = str(raw[field]).strip()

    iso2 = _uppercase_code(raw.get("iso2_code"), r"[A-Z]{2}", "iso2_code", errors, row_number)
    iso3 = _uppercase_code(raw.get("iso3_code"), r"[A-Z]{3}", "iso3_code", errors, row_number)
    capital_iata = _uppercase_code(raw.get("capital_iata_code"), r"[A-Z]{3}", "capital_iata_code", errors, row_number)
    currency_iso = _uppercase_code(raw.get("currency_iso_code"), r"[A-Z]{3}", "currency_iso_code", errors, row_number)
    for key, value in {
        "iso2_code": iso2,
        "iso3_code": iso3,
        "capital_iata_code": capital_iata,
        "currency_iso_code": currency_iso,
    }.items():
        if value:
            normalized[key] = value

    population_estimate = _parse_optional_int(raw.get("population_estimate"), "population_estimate", errors, row_number)
    population_year = _parse_optional_int(raw.get("population_estimate_year"), "population_estimate_year", errors, row_number)
    if population_estimate is not None:
        normalized["population_estimate"] = population_estimate
    if population_year is not None:
        normalized["population_estimate_year"] = population_year

    data_quality_status = str(raw.get("data_quality_status") or "draft").strip().lower()
    if data_quality_status not in DATA_QUALITY_STATUSES:
        errors.append(f"{_row_prefix(row_number)}data_quality_status must be one of {', '.join(sorted(DATA_QUALITY_STATUSES))}.")
    normalized["data_quality_status"] = data_quality_status

    airport_values = [raw.get("major_airports")]
    airport_values.extend(raw.get(f"major_airport_{index}") for index in range(1, 4))
    major_airports = _normalize_airport_list([value for value in airport_values if not _blank(value)], errors, row_number)
    if major_airports:
        normalized["major_airports"] = major_airports

    language_values = [raw.get("official_languages")]
    language_values.extend(raw.get(f"official_language_{index}") for index in range(1, 4))
    languages = _normalize_language_list([value for value in language_values if not _blank(value)], errors, row_number)
    if languages:
        normalized["official_languages"] = languages

    national_carrier = raw.get("national_carrier")
    if _blank(national_carrier) and (not _blank(raw.get("national_carrier_name")) or not _blank(raw.get("national_carrier_iata_code"))):
        national_carrier = {
            "name": raw.get("national_carrier_name"),
            "iata_code": raw.get("national_carrier_iata_code"),
        }
    normalized_carrier = _normalize_airline(national_carrier, errors, row_number)
    if normalized_carrier:
        normalized["national_carrier"] = normalized_carrier

    airline_values = [raw.get("major_airlines")]
    for index in range(1, 4):
        if not _blank(raw.get(f"major_airline_{index}_name")) or not _blank(raw.get(f"major_airline_{index}_iata_code")):
            airline_values.append(
                {
                    "name": raw.get(f"major_airline_{index}_name"),
                    "iata_code": raw.get(f"major_airline_{index}_iata_code"),
                }
            )
    major_airlines = _normalize_airline_list([value for value in airline_values if not _blank(value)], errors, row_number)
    if major_airlines:
        normalized["major_airlines"] = major_airlines

    return normalized


def normalize_reference_metadata_for_domain(domain: str, metadata: dict[str, Any] | None, row_number: int | None = None) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if domain == "countries":
        return normalize_country_metadata(metadata, errors, row_number), errors
    return metadata or {}, errors


async def audit_reference_event(
    db: Database,
    event_type: str,
    entity_type: str,
    entity_id: str,
    summary: str,
    actor_user_id: str | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    event = AuditEvent(
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata=metadata or {},
    )
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


REQUIRED_IMPORT_COLUMNS = {"domain", "code", "label"}
OPTIONAL_IMPORT_COLUMNS = {"description", "aliases", "sort_order", "is_active", "metadata_json"}
SUPPORTED_IMPORT_COLUMNS = REQUIRED_IMPORT_COLUMNS | OPTIONAL_IMPORT_COLUMNS | COUNTRY_IMPORT_COLUMNS


def parse_bool(value: str | None, default: bool = True) -> bool:
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "active"}


def parse_aliases(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.replace("|", ",").split(",") if item.strip()]


def parse_metadata(value: str | None, row_number: int, errors: list[str]) -> dict[str, Any]:
    if not value or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        errors.append(f"Row {row_number}: metadata_json is not valid JSON.")
        return {}
    if not isinstance(parsed, dict):
        errors.append(f"Row {row_number}: metadata_json must be an object.")
        return {}
    return parsed


def extract_country_metadata_from_row(row: dict[str, Any], metadata_json: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(metadata_json)
    for column in COUNTRY_IMPORT_COLUMNS:
        if column in row and not _blank(row.get(column)):
            enriched[column] = row.get(column)
    return enriched


async def validate_reference_csv(db: Database, domain: str, csv_text: str) -> dict[str, Any]:
    ensure_domain = domain in REFERENCE_DOMAINS
    if not ensure_domain:
        return {"rows": [], "total_rows": 0, "valid_rows": 0, "invalid_rows": 0, "errors": [f"Unsupported reference domain: {domain}"], "duplicate_codes": []}

    reader = csv.DictReader(StringIO(csv_text.strip()))
    fieldnames = set(reader.fieldnames or [])
    missing = sorted(REQUIRED_IMPORT_COLUMNS - fieldnames)
    unsupported = sorted(fieldnames - SUPPORTED_IMPORT_COLUMNS)
    errors: list[str] = []
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}.")
    if unsupported:
        errors.append(f"Unsupported columns ignored: {', '.join(unsupported)}.")

    rows: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    duplicate_codes: list[str] = []
    for row_number, row in enumerate(reader, start=2):
        row_errors: list[str] = []
        row_domain = (row.get("domain") or "").strip()
        code = normalize_reference_code(row.get("code") or "")
        label = (row.get("label") or "").strip()
        if row_domain != domain:
            row_errors.append(f"Row {row_number}: domain must be {domain}.")
        if not code:
            row_errors.append(f"Row {row_number}: code is required.")
        if not label:
            row_errors.append(f"Row {row_number}: label is required.")
        if code in seen_codes:
            row_errors.append(f"Row {row_number}: duplicate code {code} within file.")
            duplicate_codes.append(code)
        seen_codes.add(code)
        metadata_json = parse_metadata(row.get("metadata_json"), row_number, row_errors)
        if domain == "countries":
            metadata_json, metadata_errors = normalize_reference_metadata_for_domain(domain, extract_country_metadata_from_row(row, metadata_json), row_number)
            row_errors.extend(metadata_errors)
        elif domain == "cities":
            code = normalize_city_reference_code(code)
            metadata_json, metadata_errors = normalize_city_reference_metadata(code, label, parse_aliases(row.get("aliases")), metadata_json)
            row_errors.extend([f"Row {row_number}: {error}" for error in metadata_errors])
        try:
            sort_order = int(row.get("sort_order") or 100)
        except ValueError:
            row_errors.append(f"Row {row_number}: sort_order must be an integer.")
            sort_order = 100
        rows.append(
            {
                "row_number": row_number,
                "valid": not row_errors,
                "errors": row_errors,
                "record": {
                    "domain": domain,
                    "code": code,
                    "label": label,
                    "description": (row.get("description") or "").strip() or None,
                    "aliases": parse_aliases(row.get("aliases")),
                    "sort_order": sort_order,
                    "is_active": parse_bool(row.get("is_active"), True),
                    "metadata_json": metadata_json,
                    "source_type": "import",
                },
            }
        )
        errors.extend(row_errors)

    valid_rows = len([row for row in rows if row["valid"]])
    return {
        "rows": rows,
        "total_rows": len(rows),
        "valid_rows": valid_rows,
        "invalid_rows": len(rows) - valid_rows,
        "errors": errors,
        "duplicate_codes": sorted(set(duplicate_codes)),
    }


async def create_reference_import_batch(
    db: Database,
    domain: str,
    filename: str,
    csv_text: str,
    scope: str,
    actor_user_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    validation = await validate_reference_csv(db, domain, csv_text)
    file_hash = hashlib.sha256(csv_text.encode("utf-8")).hexdigest()
    status = "validated" if validation["invalid_rows"] == 0 else "partially_valid"
    if validation["total_rows"] == 0 or validation["valid_rows"] == 0:
        status = "failed"
    batch = ReferenceImportBatch(
        uploaded_by_user_id=actor_user_id,
        scope=scope,
        domain=domain,
        filename=filename,
        file_hash=file_hash,
        status=status,
        total_rows=validation["total_rows"],
        valid_rows=validation["valid_rows"],
        invalid_rows=validation["invalid_rows"],
        error_report_json={"errors": validation["errors"], "duplicate_codes": validation["duplicate_codes"], "dry_run": dry_run},
    )
    created = await db.collection("reference_import_batches").insert_one(batch.model_dump(mode="json"))
    await audit_reference_event(db, "reference_import_batch_uploaded", "reference_import_batch", created["id"], f"Reference import batch uploaded for {domain}.", actor_user_id, {"domain": domain, "scope": scope, "filename": filename})
    await audit_reference_event(db, "reference_import_batch_validated", "reference_import_batch", created["id"], f"Reference import batch validated for {domain}.", actor_user_id, {"valid_rows": validation["valid_rows"], "invalid_rows": validation["invalid_rows"]})

    if dry_run or status == "failed":
        if status == "failed":
            await audit_reference_event(db, "reference_import_batch_failed", "reference_import_batch", created["id"], f"Reference import batch failed validation for {domain}.", actor_user_id, created["error_report_json"])
        return safe_reference_import_batch(created)

    inserted_count = 0
    updated_count = 0
    skipped_count = validation["invalid_rows"]
    for row in validation["rows"]:
        if not row["valid"]:
            continue
        result = await upsert_reference_record(db, domain, row["record"], actor_user_id)
        if result == "inserted":
            inserted_count += 1
        elif result == "updated":
            updated_count += 1
        else:
            skipped_count += 1
    imported = await db.collection("reference_import_batches").update_one(
        {"id": created["id"]},
        {
            "status": "imported",
            "inserted_count": inserted_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "completed_at": now_utc(),
        },
    )
    await audit_reference_event(db, "reference_import_batch_imported", "reference_import_batch", created["id"], f"Reference import batch imported for {domain}.", actor_user_id, {"inserted_count": inserted_count, "updated_count": updated_count, "skipped_count": skipped_count})
    return safe_reference_import_batch(imported or created)


async def upsert_reference_record(db: Database, domain: str, payload: dict[str, Any], actor_user_id: str | None = None) -> str:
    code = normalize_city_reference_code(payload["code"]) if domain == "cities" else normalize_reference_code(payload["code"])
    metadata_json = payload.get("metadata_json", {})
    if domain == "cities":
        metadata_json, metadata_errors = normalize_city_reference_metadata(code, payload["label"], payload.get("aliases", []), metadata_json)
        if metadata_errors:
            raise ValueError("; ".join(metadata_errors))
    existing = await db.collection("global_reference_records").find_one({"domain": domain, "key": code})
    record_payload = {
        "domain": domain,
        "code": code,
        "key": code,
        "label": payload["label"],
        "description": payload.get("description"),
        "aliases": payload.get("aliases", []),
        "sort_order": payload.get("sort_order", 100),
        "metadata_json": metadata_json,
        "metadata": metadata_json,
        "source_type": payload.get("source_type", "system"),
        "is_active": payload.get("is_active", True),
        "updated_by_user_id": actor_user_id,
    }
    if existing:
        await db.collection("global_reference_records").update_one({"id": existing["id"]}, record_payload)
        return "updated"
    record = GlobalReferenceRecord(**{**record_payload, "created_by_user_id": actor_user_id})
    await db.collection("global_reference_records").insert_one(record.model_dump(mode="json"))
    return "inserted"


async def upsert_service_catalogue_record(db: Database, payload: dict[str, Any], actor_user_id: str | None = None) -> str:
    service_code = normalize_reference_code(payload["service_code"])
    existing = await db.collection("service_catalogue").find_one({"service_code": service_code})
    record_payload = {
        **payload,
        "service_code": service_code,
        "updated_by_user_id": actor_user_id,
    }
    if existing:
        await db.collection("service_catalogue").update_one({"id": existing["id"]}, record_payload)
        return "updated"
    record = ServiceCatalogueRecord(**{**record_payload, "created_by_user_id": actor_user_id})
    await db.collection("service_catalogue").insert_one(record.model_dump(mode="json"))
    return "inserted"


def unique_values(*values: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        items = value if isinstance(value, list) else [value]
        for item in items:
            if item is None or item == "":
                continue
            text = str(item)
            marker = text.upper()
            if marker not in seen:
                result.append(text)
                seen.add(marker)
    return result


def merge_metadata(primary: dict[str, Any] | None, fallback: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(fallback or {})
    merged.update(primary or {})
    return merged


async def normalize_city_reference_codes(db: Database, actor_user_id: str | None = None, dry_run: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {
        "dry_run": dry_run,
        "renamed": [],
        "merged": [],
        "archived": [],
        "airport_city_codes_updated": [],
        "unchanged": [],
    }
    records = await db.collection("global_reference_records").find_many({"domain": "cities"})
    by_key = {normalize_reference_code(record.get("key") or record.get("code")): record for record in records}

    for legacy_code, target_code in CITY_CODE_MIGRATIONS.items():
        source = by_key.get(legacy_code)
        target = by_key.get(target_code)
        if not source:
            if target:
                aliases = unique_values(target.get("aliases", []), legacy_code)
                metadata_json, metadata_errors = normalize_city_reference_metadata(target_code, target.get("label") or "", aliases, target.get("metadata_json") or {})
                if metadata_errors:
                    report["unchanged"].append({"code": target_code, "errors": metadata_errors})
                    continue
                if aliases != (target.get("aliases") or []):
                    report["merged"].append({"from": legacy_code, "to": target_code, "action": "alias_or_metadata_synchronized"})
                    if not dry_run:
                        updated = await db.collection("global_reference_records").update_one(
                            {"id": target["id"]},
                            {"aliases": aliases, "metadata_json": metadata_json, "metadata": metadata_json, "updated_by_user_id": actor_user_id},
                        )
                        if updated:
                            by_key[target_code] = updated
                elif metadata_json != (target.get("metadata_json") or {}):
                    report["merged"].append({"from": legacy_code, "to": target_code, "action": "metadata_synchronized"})
                    if not dry_run:
                        updated = await db.collection("global_reference_records").update_one(
                            {"id": target["id"]},
                            {"metadata_json": metadata_json, "metadata": metadata_json, "updated_by_user_id": actor_user_id},
                        )
                        if updated:
                            by_key[target_code] = updated
                else:
                    report["unchanged"].append({"code": target_code})
            continue

        source_aliases = unique_values(source.get("aliases", []), legacy_code)
        if target and target["id"] != source["id"] and source.get("is_active") is False:
            aliases = unique_values(target.get("aliases", []), source_aliases)
            metadata_json, metadata_errors = normalize_city_reference_metadata(target_code, target.get("label") or source.get("label") or "", aliases, merge_metadata(target.get("metadata_json"), source.get("metadata_json")))
            if metadata_errors:
                report["unchanged"].append({"code": target_code, "legacy_code": legacy_code, "errors": metadata_errors})
                continue
            if aliases != (target.get("aliases") or []):
                report["merged"].append({"from": legacy_code, "to": target_code, "action": "alias_or_metadata_synchronized_from_archived_source"})
                if not dry_run:
                    updated = await db.collection("global_reference_records").update_one(
                        {"id": target["id"]},
                        {"aliases": aliases, "metadata_json": metadata_json, "metadata": metadata_json, "updated_by_user_id": actor_user_id},
                    )
                    if updated:
                        by_key[target_code] = updated
            elif metadata_json != (target.get("metadata_json") or {}):
                report["merged"].append({"from": legacy_code, "to": target_code, "action": "metadata_synchronized_from_archived_source"})
                if not dry_run:
                    updated = await db.collection("global_reference_records").update_one(
                        {"id": target["id"]},
                        {"metadata_json": metadata_json, "metadata": metadata_json, "updated_by_user_id": actor_user_id},
                    )
                    if updated:
                        by_key[target_code] = updated
            else:
                report["unchanged"].append({"code": target_code, "legacy_code": legacy_code})
            continue

        if target and target["id"] != source["id"]:
            target_metadata = merge_metadata(target.get("metadata_json"), source.get("metadata_json"))
            aliases = unique_values(target.get("aliases", []), source_aliases)
            target_metadata, metadata_errors = normalize_city_reference_metadata(target_code, target.get("label") or source.get("label") or "", aliases, target_metadata)
            if metadata_errors:
                report["unchanged"].append({"code": target_code, "legacy_code": legacy_code, "errors": metadata_errors})
                continue
            target_updates = {
                "label": target.get("label") or source.get("label"),
                "description": target.get("description") or source.get("description"),
                "aliases": aliases,
                "sort_order": target.get("sort_order") or source.get("sort_order", 100),
                "metadata_json": target_metadata,
                "metadata": target_metadata,
                "is_active": target.get("is_active", True) or source.get("is_active", True),
                "updated_by_user_id": actor_user_id,
            }
            report["merged"].append({"from": legacy_code, "to": target_code, "archived_source": True})
            if not dry_run:
                updated = await db.collection("global_reference_records").update_one({"id": target["id"]}, target_updates)
                archived = await db.collection("global_reference_records").update_one(
                    {"id": source["id"]},
                    {
                        "aliases": source_aliases,
                        "is_active": False,
                        "updated_by_user_id": actor_user_id,
                    },
                )
                if updated:
                    by_key[target_code] = updated
                if archived:
                    by_key[legacy_code] = archived
                    report["archived"].append(legacy_code)
            continue

        updates = {
            "code": target_code,
            "key": target_code,
            "aliases": source_aliases,
            "updated_by_user_id": actor_user_id,
        }
        metadata_json, metadata_errors = normalize_city_reference_metadata(target_code, source.get("label") or "", source_aliases, source.get("metadata_json") or {})
        if metadata_errors:
            report["unchanged"].append({"code": legacy_code, "errors": metadata_errors})
            continue
        updates["metadata_json"] = metadata_json
        updates["metadata"] = metadata_json
        report["renamed"].append({"from": legacy_code, "to": target_code})
        if not dry_run:
            updated = await db.collection("global_reference_records").update_one({"id": source["id"]}, updates)
            if updated:
                by_key[target_code] = updated
                by_key.pop(legacy_code, None)

    airport_records = await db.collection("global_reference_records").find_many({"domain": "airports"})
    for airport in airport_records:
        metadata = dict(airport.get("metadata_json") or {})
        legacy_city_code = metadata.get("city_code")
        target_city_code = CITY_CODE_MIGRATIONS.get(normalize_reference_code(legacy_city_code)) if legacy_city_code else None
        if not target_city_code:
            continue
        metadata["city_code"] = target_city_code
        report["airport_city_codes_updated"].append({"airport": airport.get("code") or airport.get("key"), "from": legacy_city_code, "to": target_city_code})
        if not dry_run:
            await db.collection("global_reference_records").update_one(
                {"id": airport["id"]},
                {"metadata_json": metadata, "metadata": metadata, "updated_by_user_id": actor_user_id},
            )

    return report


async def bootstrap_reference_data(db: Database, actor_user_id: str | None = None) -> dict[str, Any]:
    reference_counts = {"inserted": 0, "updated": 0}
    service_counts = {"inserted": 0, "updated": 0}
    for domain, records in REFERENCE_BOOTSTRAP_RECORDS.items():
        for record in records:
            result = await upsert_reference_record(db, domain, record, actor_user_id)
            reference_counts[result] += 1
    for record in SERVICE_CATALOGUE_BOOTSTRAP_RECORDS:
        result = await upsert_service_catalogue_record(db, record, actor_user_id)
        service_counts[result] += 1
    city_migration = await normalize_city_reference_codes(db, actor_user_id)
    return {
        "reference_records": reference_counts,
        "service_catalogue_records": service_counts,
        "domains": len(REFERENCE_DOMAINS),
        "service_families": len(SERVICE_FAMILIES),
        "city_code_migration": city_migration,
    }
