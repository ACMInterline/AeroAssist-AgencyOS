from typing import Any

from database import Database
from models import AuditEvent, GlobalReferenceRecord, ServiceCatalogueRecord


REFERENCE_DOMAINS = {
    "countries": "Countries",
    "cities": "Cities",
    "airports": "Airports",
    "airlines": "Airlines",
    "currencies": "Currencies",
    "timezones": "Time zones",
    "languages": "Languages",
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
        {"code": "BG", "label": "Bulgaria", "aliases": ["Republic of Bulgaria"], "sort_order": 10},
        {"code": "US", "label": "United States", "aliases": ["USA", "United States of America"], "sort_order": 20},
        {"code": "GB", "label": "United Kingdom", "aliases": ["UK", "Great Britain"], "sort_order": 30},
    ],
    "cities": [
        {"code": "SOFIA", "label": "Sofia", "metadata_json": {"country_code": "BG"}, "sort_order": 10},
        {"code": "NEW_YORK", "label": "New York", "aliases": ["NYC"], "metadata_json": {"country_code": "US"}, "sort_order": 20},
        {"code": "LONDON", "label": "London", "metadata_json": {"country_code": "GB"}, "sort_order": 30},
    ],
    "airports": [
        {"code": "SOF", "label": "Sofia Airport", "metadata_json": {"city_code": "SOFIA", "country_code": "BG"}, "sort_order": 10},
        {"code": "JFK", "label": "John F. Kennedy International Airport", "metadata_json": {"city_code": "NEW_YORK", "country_code": "US"}, "sort_order": 20},
        {"code": "LHR", "label": "London Heathrow Airport", "metadata_json": {"city_code": "LONDON", "country_code": "GB"}, "sort_order": 30},
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


async def upsert_reference_record(db: Database, domain: str, payload: dict[str, Any], actor_user_id: str | None = None) -> str:
    code = normalize_reference_code(payload["code"])
    existing = await db.collection("global_reference_records").find_one({"domain": domain, "key": code})
    record_payload = {
        "domain": domain,
        "code": code,
        "key": code,
        "label": payload["label"],
        "description": payload.get("description"),
        "aliases": payload.get("aliases", []),
        "sort_order": payload.get("sort_order", 100),
        "metadata_json": payload.get("metadata_json", {}),
        "metadata": payload.get("metadata_json", {}),
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
    return {
        "reference_records": reference_counts,
        "service_catalogue_records": service_counts,
        "domains": len(REFERENCE_DOMAINS),
        "service_families": len(SERVICE_FAMILIES),
    }
