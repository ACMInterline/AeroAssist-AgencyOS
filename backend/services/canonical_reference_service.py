from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Any, Iterable

from fastapi import HTTPException, status

from database import Database
from persistence_query import MAXIMUM_QUERY_LIMIT


PUBLIC_REFERENCE_DOMAINS = frozenset(
    {
        "airlines",
        "airports",
        "cabin_classes",
        "countries",
        "currencies",
        "document_types",
        "languages",
        "passenger_types",
        "pet_breeds",
        "pet_species",
        "special_item_categories",
        "vaccination_types",
        "container_types",
    }
)

REFERENCE_DOMAIN_ALIASES = {
    "passenger_type_codes": "passenger_types",
    "species": "pet_species",
    "breeds": "pet_breeds",
    "pricing_formula_components": "formula_components",
}

REFERENCE_DOMAIN_INVENTORY: dict[str, dict[str, str]] = {
    "airlines": {"classification": "already_canonical_and_complete", "stable_domain": "airlines"},
    "airports": {"classification": "already_canonical_and_complete", "stable_domain": "airports"},
    "aircraft_types": {"classification": "already_canonical_and_complete", "stable_domain": "aircraft_types"},
    "cabin_classes": {"classification": "canonical_but_incomplete", "stable_domain": "cabin_classes"},
    "fare_bundles": {"classification": "canonical_but_incomplete", "stable_domain": "fare_bundles"},
    "flight_types": {"classification": "canonical_but_incomplete", "stable_domain": "flight_types"},
    "route_types": {"classification": "canonical_but_incomplete", "stable_domain": "route_types"},
    "countries": {"classification": "already_canonical_and_complete", "stable_domain": "countries"},
    "cities": {"classification": "already_canonical_and_complete", "stable_domain": "cities"},
    "temperature_zones": {"classification": "canonical_but_incomplete", "stable_domain": "temperature_zones"},
    "languages": {"classification": "already_canonical_and_complete", "stable_domain": "languages"},
    "currencies": {"classification": "already_canonical_and_complete", "stable_domain": "currencies"},
    "client_types": {"classification": "already_canonical_and_complete", "stable_domain": "client_types"},
    "contact_channels": {"classification": "already_canonical_and_complete", "stable_domain": "contact_channels"},
    "guardian_relationships": {"classification": "already_canonical_and_complete", "stable_domain": "guardian_relationships"},
    "passenger_type_codes": {"classification": "represented_under_different_stable_domain_key", "stable_domain": "passenger_types"},
    "document_types": {"classification": "already_canonical_and_complete", "stable_domain": "document_types"},
    "vaccination_types": {"classification": "canonical_but_incomplete", "stable_domain": "vaccination_types"},
    "species": {"classification": "represented_under_different_stable_domain_key", "stable_domain": "pet_species"},
    "breeds": {"classification": "represented_under_different_stable_domain_key", "stable_domain": "pet_breeds"},
    "breed_risk_flags": {"classification": "canonical_but_incomplete", "stable_domain": "breed_risk_flags"},
    "container_types": {"classification": "canonical_but_incomplete", "stable_domain": "container_types"},
    "service_codes": {"classification": "represented_under_different_stable_domain_key", "stable_domain": "service_catalogue"},
    "assistance_types": {"classification": "canonical_but_incomplete", "stable_domain": "assistance_types"},
    "condition_types": {"classification": "canonical_but_incomplete", "stable_domain": "condition_types"},
    "special_item_categories": {"classification": "already_canonical_and_complete", "stable_domain": "special_item_categories"},
    "policy_statuses": {"classification": "canonical_but_incomplete", "stable_domain": "policy_statuses"},
    "policy_result_statuses": {"classification": "canonical_but_incomplete", "stable_domain": "policy_result_statuses"},
    "seasonal_restriction_types": {"classification": "canonical_but_incomplete", "stable_domain": "seasonal_restriction_types"},
    "pricing_categories": {"classification": "canonical_but_incomplete", "stable_domain": "pricing_categories"},
    "pricing_units": {"classification": "canonical_but_incomplete", "stable_domain": "pricing_units"},
    "pricing_formula_components": {"classification": "represented_under_different_stable_domain_key", "stable_domain": "formula_components"},
    "payment_methods": {"classification": "already_canonical_and_complete", "stable_domain": "payment_methods"},
    "tax_types": {"classification": "already_canonical_and_complete", "stable_domain": "tax_types"},
    "task_types": {"classification": "canonical_but_incomplete", "stable_domain": "task_types"},
    "communication_channels": {"classification": "represented_under_different_stable_domain_key", "stable_domain": "contact_channels"},
    "priority_levels": {"classification": "canonical_but_incomplete", "stable_domain": "priority_levels"},
    "statuses": {"classification": "decision_required", "stable_domain": "statuses"},
}

_PUBLIC_METADATA_FIELDS: dict[str, frozenset[str]] = {
    "airlines": frozenset({"iata_code", "icao_code", "country_code"}),
    "airports": frozenset({"iata_code", "icao_code", "city_code", "country_code", "timezone"}),
    "countries": frozenset({"iso2_code", "iso3_code", "continent", "currency_iso_code"}),
    "currencies": frozenset({"currency_iso_code", "numeric_code", "minor_unit", "symbol"}),
    "languages": frozenset({"iso639_1", "iso639_2", "native_name"}),
    "passenger_types": frozenset(
        {
            "iata_ptc_code",
            "passenger_category",
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
        }
    ),
    "pet_breeds": frozenset({"species_code", "breed_group", "snub_nosed", "size_category"}),
}

_PTC_FLAG_BY_CATEGORY = {
    "adult": "is_adult",
    "child": "is_child",
    "infant": "is_infant",
    "senior": "is_senior",
}

_PTC_CATEGORY_COMPATIBILITY_CODES = {
    "adult": "ADT",
    "child": "CHD",
    "infant": "INF",
    "youth": "YTH",
    "senior": "SRC",
    "student": "STU",
    "seaman": "SEA",
    "military": "MIL",
    "group": "GRP",
}

_ACTIVE_STATUSES = frozenset(
    {
        "active",
        "draft",
        "new",
        "open",
        "triage",
        "waiting_for_client",
        "in_progress",
        "ready_for_offer",
        "offer_created",
        "confirmed",
        "pending",
    }
)

_REFERENCE_CONSUMERS: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "passenger_types": (
        ("passenger_profiles", ("passenger_type_code_id", "passenger_type_code", "passenger_type")),
        ("request_passengers", ("passenger_type_code_id", "snapshot_passenger_type")),
    ),
    "airports": (
        ("request_segments", ("origin_airport_id", "destination_airport_id", "origin_airport_code", "destination_airport_code")),
        ("trip_segments", ("origin_airport_id", "destination_airport_id", "origin_airport_code", "destination_airport_code")),
        ("offer_builder_segments", ("origin_airport_id", "destination_airport_id", "origin_airport", "destination_airport")),
    ),
    "airlines": (
        ("request_segments", ("marketing_airline_id", "operating_airline_id", "marketing_airline", "operating_airline")),
        ("trip_segments", ("marketing_airline_id", "operating_airline_id", "marketing_airline_code", "operating_airline_code")),
        ("offer_options", ("main_airline_id", "main_airline_code")),
    ),
    "countries": (
        ("passenger_profiles", ("nationality_reference_id", "nationality", "residence_country_reference_id", "residence_country", "passport_country_reference_id", "passport_country")),
        ("request_passengers", ("nationality_reference_id", "nationality_code")),
    ),
    "currencies": (
        ("offer_workspaces", ("currency_reference_id", "currency")),
        ("offer_pricing_lines", ("currency_reference_id", "currency")),
        ("invoices", ("currency_reference_id", "currency")),
    ),
    "pet_species": (("request_pets", ("species_reference_id", "species_key")),),
    "pet_breeds": (("request_pets", ("breed_reference_id", "breed_key")),),
    "special_item_categories": (("request_special_items", ("item_category_reference_id", "item_category_code", "item_type")),),
}


def canonical_domain(domain: str) -> str:
    normalized = str(domain or "").strip().lower()
    return REFERENCE_DOMAIN_ALIASES.get(normalized, normalized)


def normalize_domain_code(domain: str, value: Any) -> str:
    normalized = str(value or "").strip()
    return normalized.upper() if canonical_domain(domain) == "passenger_types" else normalized


def reference_match_key(domain: str, value: Any) -> str:
    return normalize_domain_code(domain, value).casefold()


def validate_ptc_metadata(metadata: dict[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    normalized = dict(metadata or {})
    errors: list[str] = []
    category = str(normalized.get("passenger_category") or "").strip().lower()
    if category not in {"adult", "child", "infant", "youth", "senior", "student", "seaman", "military", "group"}:
        errors.append("passenger_category must be one of adult, child, infant, youth, senior, student, seaman, military, or group.")
    for field in ("age_min_years", "age_max_years"):
        value = normalized.get(field)
        if value in (None, ""):
            normalized[field] = None
            continue
        if isinstance(value, bool):
            errors.append(f"{field} must be a whole number.")
            continue
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            errors.append(f"{field} must be a whole number.")
            continue
        if parsed < 0 or parsed > 130:
            errors.append(f"{field} must be between 0 and 130.")
        normalized[field] = parsed
    minimum = normalized.get("age_min_years")
    maximum = normalized.get("age_max_years")
    if minimum is not None and maximum is not None and minimum > maximum:
        errors.append("age_min_years cannot exceed age_max_years.")
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
        normalized[field] = bool(normalized.get(field, False))
    expected_flag = _PTC_FLAG_BY_CATEGORY.get(category)
    category_flags = ("is_infant", "is_child", "is_adult", "is_senior")
    active_flags = [field for field in category_flags if normalized.get(field)]
    if expected_flag and active_flags != [expected_flag]:
        errors.append(f"{category} PTC metadata must set only {expected_flag} among category flags.")
    if not expected_flag and active_flags:
        errors.append(f"{category or 'This'} PTC category cannot set infant, child, adult, or senior classification flags.")
    iata_code = normalize_domain_code("passenger_types", normalized.get("iata_ptc_code"))
    if not iata_code or len(iata_code) > 8:
        errors.append("iata_ptc_code is required and must be at most 8 characters.")
    normalized["iata_ptc_code"] = iata_code
    return normalized, errors


def safe_reference_option(record: dict[str, Any]) -> dict[str, Any]:
    domain = canonical_domain(record.get("domain") or "")
    code = record.get("code") or record.get("key") or ""
    if domain == "passenger_types" and not str(code).isupper():
        legacy_alias = next(
            (
                str(alias).upper()
                for alias in record.get("aliases") or []
                if str(alias).upper() in {"ADT", "CHD", "INF"}
            ),
            None,
        )
        code = legacy_alias or code
    key = record.get("key") or code
    metadata = record.get("metadata_json") or record.get("metadata") or {}
    allowed_metadata = _PUBLIC_METADATA_FIELDS.get(domain, frozenset())
    public_metadata = {
        field: metadata[field]
        for field in sorted(allowed_metadata)
        if field in metadata and metadata[field] is not None
    }
    return {
        "id": str(record.get("id") or ""),
        "value": str(record.get("id") or ""),
        "label": str(record.get("label") or code),
        "code": str(code),
        "key": str(key),
        "raw": {
            "domain": domain,
            "scope": str(record.get("scope") or "global"),
            "is_active": bool(record.get("is_active", True)),
            "description": record.get("description"),
            "aliases": list(record.get("aliases") or []),
            "sort_order": int(record.get("sort_order") or 100),
            "metadata": public_metadata,
        },
    }


def _sort_key(record: dict[str, Any]) -> tuple[int, str, str, str]:
    return (
        int(record.get("sort_order") or 100),
        str(record.get("label") or "").casefold(),
        reference_match_key(record.get("domain") or "", record.get("code") or record.get("key")),
        str(record.get("id") or ""),
    )


def _matches_query(record: dict[str, Any], query: str) -> bool:
    needle = query.strip().casefold()
    if not needle:
        return True
    values = [
        record.get("code"),
        record.get("key"),
        record.get("label"),
        record.get("description"),
        *(record.get("aliases") or []),
    ]
    return any(needle in str(value).casefold() for value in values if value)


async def user_agency_ids(db: Database, user: dict[str, Any] | None) -> set[str]:
    if not user or not user.get("id"):
        return set()
    memberships = await db.collection("agency_staff_memberships").find_many(
        {"user_id": user["id"], "status": "active"},
        sort=[("agency_id", 1), ("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT,
    )
    return {str(item["agency_id"]) for item in memberships if item.get("agency_id")}


async def list_visible_reference_records(
    db: Database,
    domain: str,
    *,
    user: dict[str, Any] | None = None,
    public: bool = False,
    include_inactive: bool = False,
    query: str = "",
    limit: int = 100,
) -> list[dict[str, Any]]:
    domain = canonical_domain(domain)
    if public and domain not in PUBLIC_REFERENCE_DOMAINS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference domain is not public.")
    platform = bool(user and user.get("global_role") in {"platform_owner", "platform_admin"})
    agency_ids = await user_agency_ids(db, user) if user and not platform else set()
    records = await db.collection("global_reference_records").find_many(
        {"domain": domain},
        sort=[("sort_order", 1), ("label", 1), ("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT,
    )
    visible: list[dict[str, Any]] = []
    for record in records:
        scope = str(record.get("scope") or "global")
        if scope != "global":
            if public:
                continue
            if not platform and record.get("agency_id") not in agency_ids:
                continue
        if not include_inactive and not record.get("is_active", True):
            continue
        if _matches_query(record, query):
            visible.append(record)
    return sorted(visible, key=_sort_key)[:limit]


async def list_reference_options(
    db: Database,
    domain: str,
    *,
    user: dict[str, Any] | None = None,
    public: bool = False,
    include_inactive: bool = False,
    query: str = "",
    limit: int = 100,
) -> list[dict[str, Any]]:
    records = await list_visible_reference_records(
        db,
        domain,
        user=user,
        public=public,
        include_inactive=include_inactive,
        query=query,
        limit=limit,
    )
    if canonical_domain(domain) == "passenger_types":
        records = sorted(
            records,
            key=lambda item: (
                not bool((item.get("metadata_json") or item.get("metadata") or {}).get("passenger_category")),
                _sort_key(item),
            ),
        )
        options_by_code: dict[str, dict[str, Any]] = {}
        for item in records:
            option = safe_reference_option(item)
            options_by_code.setdefault(reference_match_key(domain, option["code"]), option)
        return sorted(
            options_by_code.values(),
            key=lambda item: (
                int((item.get("raw") or {}).get("sort_order") or 100),
                str(item.get("label") or "").casefold(),
                str(item.get("code") or "").casefold(),
            ),
        )[:limit]
    return [safe_reference_option(item) for item in records]


async def get_visible_reference(
    db: Database,
    domain: str,
    record_id: str,
    *,
    user: dict[str, Any] | None = None,
    public: bool = False,
) -> dict[str, Any]:
    domain = canonical_domain(domain)
    record = await db.collection("global_reference_records").find_one({"domain": domain, "id": record_id})
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference record not found.")
    if public and domain not in PUBLIC_REFERENCE_DOMAINS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference record not found.")
    scope = str(record.get("scope") or "global")
    if scope != "global":
        platform = bool(user and user.get("global_role") in {"platform_owner", "platform_admin"})
        if public or not platform and record.get("agency_id") not in await user_agency_ids(db, user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference record not found.")
    return record


async def resolve_reference(
    db: Database,
    domain: str,
    *,
    reference_id: str | None = None,
    code: str | None = None,
    agency_id: str | None = None,
    active_required: bool = True,
    allow_uninitialized_legacy: bool = False,
) -> tuple[dict[str, Any] | None, str]:
    domain = canonical_domain(domain)
    record = None
    if reference_id:
        record = await db.collection("global_reference_records").find_one({"domain": domain, "id": reference_id})
        if not record:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{domain} reference ID is invalid.")
    elif code:
        normalized = reference_match_key(domain, code)
        records = await db.collection("global_reference_records").find_many(
            {"domain": domain},
            sort=[("sort_order", 1), ("id", 1)],
            limit=MAXIMUM_QUERY_LIMIT,
        )
        matches = [
            item
            for item in records
            if reference_match_key(domain, item.get("code") or item.get("key")) == normalized
            or normalized in {
                reference_match_key(domain, alias)
                for alias in item.get("aliases") or []
            }
        ]
        if domain == "passenger_types":
            matches.sort(
                key=lambda item: (
                    not bool((item.get("metadata_json") or item.get("metadata") or {}).get("passenger_category")),
                    _sort_key(item),
                )
            )
        record = matches[0] if matches else None
        if not record:
            if allow_uninitialized_legacy and not records:
                return None, "reference_catalogue_uninitialized"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{domain} reference code is unknown.")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{domain} reference ID is required.")
    if str(record.get("scope") or "global") != "global" and record.get("agency_id") != agency_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{domain} reference is outside this agency scope.")
    if active_required and not record.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{domain} reference is inactive and cannot be selected.")
    return record, "resolved"


def reference_snapshot(record: dict[str, Any]) -> dict[str, str]:
    return {
        "id": str(record.get("id") or ""),
        "code": str(record.get("code") or record.get("key") or ""),
        "label": str(record.get("label") or record.get("code") or record.get("key") or ""),
    }


def age_on_date(date_of_birth: date, travel_date: date) -> int:
    age = travel_date.year - date_of_birth.year
    if (travel_date.month, travel_date.day) < (date_of_birth.month, date_of_birth.day):
        age -= 1
    return age


def validate_ptc_for_date(
    record: dict[str, Any],
    *,
    date_of_birth: date | None,
    travel_date: date,
) -> dict[str, Any]:
    metadata, metadata_errors = validate_ptc_metadata(record.get("metadata_json") or record.get("metadata") or {})
    errors = list(metadata_errors)
    warnings: list[str] = []
    age = age_on_date(date_of_birth, travel_date) if date_of_birth else None
    if metadata.get("requires_date_of_birth") and not date_of_birth:
        errors.append(f"{record.get('code') or record.get('key')} requires date of birth.")
    if age is not None:
        if age < 0 or age > 130:
            errors.append("Passenger date of birth is not valid for the first departure.")
        minimum = metadata.get("age_min_years")
        maximum = metadata.get("age_max_years")
        if minimum is not None and age < minimum:
            errors.append(f"Passenger age {age} is below the configured minimum {minimum} for {record.get('code') or record.get('key')}.")
        if maximum is not None and age > maximum:
            errors.append(f"Passenger age {age} exceeds the configured maximum {maximum} for {record.get('code') or record.get('key')}.")
    if metadata.get("requires_guardian"):
        warnings.append("Guardian or accompanying adult details require operational review.")
    if metadata.get("manual_review_required"):
        warnings.append("Passenger type eligibility requires manual airline or documentation review.")
    return {
        "valid": not errors,
        "age": age,
        "errors": errors,
        "warnings": warnings,
        "metadata": metadata,
    }


def passenger_type_compatibility_code(record: dict[str, Any], selected_code: str) -> str:
    metadata = record.get("metadata_json") or record.get("metadata") or {}
    category = str(metadata.get("passenger_category") or "").strip().lower()
    canonical_code = normalize_domain_code("passenger_types", record.get("code") or record.get("key"))
    supported_codes = set(_PTC_CATEGORY_COMPATIBILITY_CODES.values()) | {"UMNR"}
    if canonical_code in supported_codes:
        return canonical_code
    selected = normalize_domain_code("passenger_types", selected_code)
    if selected in supported_codes:
        return selected
    return _PTC_CATEGORY_COMPATIBILITY_CODES.get(category, "ADT")


async def find_active_scope_conflict(
    db: Database,
    *,
    domain: str,
    code: str,
    key: str,
    scope: str,
    agency_id: str | None,
    exclude_id: str | None = None,
) -> dict[str, Any] | None:
    domain = canonical_domain(domain)
    normalized_code = reference_match_key(domain, code)
    normalized_key = reference_match_key(domain, key)
    records = await db.collection("global_reference_records").find_many(
        {"domain": domain},
        sort=[("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT,
    )
    for record in records:
        if exclude_id and record.get("id") == exclude_id:
            continue
        if not record.get("is_active", True):
            continue
        record_scope = str(record.get("scope") or "global")
        if scope == "agency":
            if record_scope == "agency" and record.get("agency_id") != agency_id:
                continue
            if record_scope not in {"global", "agency"}:
                continue
        record_code = reference_match_key(domain, record.get("code") or record.get("key"))
        record_key = reference_match_key(domain, record.get("key") or record.get("code"))
        if normalized_code in {record_code, record_key} or normalized_key in {record_code, record_key}:
            return record
    return None


async def reference_record_usage(db: Database, record: dict[str, Any]) -> dict[str, Any]:
    domain = canonical_domain(record.get("domain") or "")
    identifiers = {
        str(record.get("id") or ""),
        reference_match_key(domain, record.get("code") or record.get("key")),
        reference_match_key(domain, record.get("key") or record.get("code")),
        *{
            reference_match_key(domain, alias)
            for alias in record.get("aliases") or []
        },
    }
    consumers: list[dict[str, Any]] = []
    active_total = 0
    historical_total = 0
    for collection_name, fields in _REFERENCE_CONSUMERS.get(domain, ()):
        rows = await db.collection(collection_name).find_many(
            sort=[("updated_at", -1), ("id", 1)],
            limit=MAXIMUM_QUERY_LIMIT,
        )
        active = 0
        historical = 0
        for row in rows:
            matched_fields = []
            for field in fields:
                raw = row.get(field)
                if raw is None:
                    continue
                values: Iterable[Any] = raw if isinstance(raw, list) else (raw,)
                if any(
                    str(value) == str(record.get("id"))
                    or reference_match_key(domain, value) in identifiers
                    for value in values
                ):
                    matched_fields.append(field)
            if not matched_fields:
                continue
            row_status = str(row.get("status") or "active").lower()
            if row_status in _ACTIVE_STATUSES and not row.get("archived", False):
                active += 1
            else:
                historical += 1
        if active or historical:
            consumers.append(
                {
                    "collection": collection_name,
                    "fields": list(fields),
                    "active_record_count": active,
                    "historical_record_count": historical,
                }
            )
            active_total += active
            historical_total += historical
    return {
        "record_id": record.get("id"),
        "domain": domain,
        "code": record.get("code") or record.get("key"),
        "active_record_count": active_total,
        "historical_record_count": historical_total,
        "used_by_active_records": active_total > 0,
        "deactivation_risk": "high" if active_total else "historical_only" if historical_total else "none",
        "consumers": sorted(consumers, key=lambda item: item["collection"]),
        "bounded_query_limit": MAXIMUM_QUERY_LIMIT,
    }


async def governed_deactivate_reference(
    db: Database,
    record: dict[str, Any],
    *,
    actor_user_id: str,
    force: bool = False,
    reason: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    usage = await reference_record_usage(db, record)
    if usage["used_by_active_records"] and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Reference record is used by active operational records.",
                "usage": usage,
                "override_available": True,
                "override_requires_reason": True,
            },
        )
    normalized_reason = " ".join(str(reason or "").split())
    if force and len(normalized_reason) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Forced deactivation requires a reason of at least three characters.",
        )
    updated = await db.collection("global_reference_records").update_one(
        {"id": record["id"]},
        {
            "is_active": False,
            "updated_by_user_id": actor_user_id,
            "deactivation_reason": normalized_reason or None,
            "deactivation_forced": bool(force),
        },
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference record not found.")
    return updated, usage


async def analyze_reference_wiring(db: Database) -> dict[str, Any]:
    scanned_collections = (
        "passenger_profiles",
        "request_passengers",
        "travel_requests",
        "request_segments",
        "request_pets",
        "request_special_items",
        "global_reference_records",
    )
    before_counts = {
        name: await db.collection(name).count()
        for name in scanned_collections
    }
    references = await db.collection("global_reference_records").find_many(
        sort=[("domain", 1), ("key", 1), ("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT,
    )
    references_by_id = {str(record.get("id")): record for record in references if record.get("id")}
    active_by_domain_code: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    duplicate_scope_keys: Counter[tuple[str, str, str, str]] = Counter()
    for record in references:
        domain = canonical_domain(record.get("domain") or "")
        identifiers = {
            reference_match_key(domain, record.get("code")),
            reference_match_key(domain, record.get("key")),
            *{
                reference_match_key(domain, alias)
                for alias in record.get("aliases") or []
            },
        }
        identifiers.discard("")
        if record.get("is_active", True):
            for identifier in identifiers:
                active_by_domain_code[domain][identifier].append(record)
            for identifier in {
                reference_match_key(domain, record.get("code")),
                reference_match_key(domain, record.get("key")),
            }:
                if identifier:
                    duplicate_scope_keys[
                        (
                            domain,
                            str(record.get("scope") or "global"),
                            str(record.get("agency_id") or ""),
                            identifier,
                        )
                    ] += 1
    by_agency: dict[str, Counter[str]] = defaultdict(Counter)
    by_domain: dict[str, Counter[str]] = defaultdict(Counter)
    candidates: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    manual_review: list[dict[str, Any]] = []

    def increment(agency_id: str, domain: str, issue: str) -> None:
        by_agency[agency_id][issue] += 1
        by_domain[domain][issue] += 1

    def visible_matches(domain: str, code: str, agency_id: str) -> list[dict[str, Any]]:
        return [
            record
            for record in active_by_domain_code[domain].get(code, [])
            if str(record.get("scope") or "global") == "global"
            or str(record.get("agency_id") or "") == agency_id
        ]

    def analyze_value(
        *,
        agency_id: str,
        collection: str,
        record_id: Any,
        domain: str,
        reference_id: Any,
        legacy_value: Any,
        field: str,
    ) -> dict[str, Any] | None:
        canonical = canonical_domain(domain)
        code = normalize_domain_code(canonical, legacy_value)
        match_code = reference_match_key(canonical, legacy_value)
        base = {
            "agency_id": agency_id,
            "collection": collection,
            "record_id": record_id,
            "field": field,
            "domain": canonical,
            "legacy_value": code,
        }
        if reference_id:
            linked = references_by_id.get(str(reference_id))
            if not linked:
                increment(agency_id, canonical, f"{canonical}_missing_reference_id")
                manual_review.append({**base, "reference_id": reference_id, "reason": "missing_reference_id"})
                return None
            if canonical_domain(linked.get("domain") or "") != canonical:
                increment(agency_id, canonical, f"{canonical}_wrong_domain_reference")
                manual_review.append({**base, "reference_id": reference_id, "reason": "wrong_domain_reference"})
                return linked
            if str(linked.get("scope") or "global") == "agency" and str(linked.get("agency_id") or "") != agency_id:
                increment(agency_id, canonical, f"{canonical}_cross_scope_reference")
                manual_review.append({**base, "reference_id": reference_id, "reason": "cross_scope_reference"})
            if not linked.get("is_active", True):
                increment(agency_id, canonical, f"{canonical}_inactive_reference")
                manual_review.append({**base, "reference_id": reference_id, "reason": "inactive_reference_historical"})
            return linked
        if not code:
            return None
        increment(agency_id, canonical, f"{canonical}_legacy_value_without_id")
        matches = visible_matches(canonical, match_code, agency_id)
        if len(matches) == 1:
            candidates.append({**base, "candidate_reference_id": matches[0].get("id")})
            return matches[0]
        if len(matches) > 1:
            ambiguous.append({**base, "candidate_reference_ids": sorted(str(match.get("id")) for match in matches)})
            return None
        manual_review.append({**base, "reason": f"unknown_{canonical}_value"})
        return None

    def parsed_date(value: Any) -> date | None:
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value:
            try:
                return date.fromisoformat(value[:10])
            except ValueError:
                return None
        return None

    passengers = await db.collection("passenger_profiles").find_many(
        sort=[("agency_id", 1), ("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT,
    )
    for passenger in passengers:
        agency_id = str(passenger.get("agency_id") or "unscoped")
        code = normalize_domain_code(
            "passenger_types",
            passenger.get("passenger_type_code") or passenger.get("passenger_type"),
        )
        ptc = analyze_value(
            agency_id=agency_id,
            collection="passenger_profiles",
            record_id=passenger.get("id"),
            domain="passenger_types",
            reference_id=passenger.get("passenger_type_code_id"),
            legacy_value=code,
            field="passenger_type_code",
        )
        if ptc and (ptc.get("metadata_json") or ptc.get("metadata") or {}).get("passenger_category"):
            validation = validate_ptc_for_date(
                ptc,
                date_of_birth=parsed_date(passenger.get("date_of_birth")),
                travel_date=date.today(),
            )
            if validation["errors"]:
                increment(agency_id, "passenger_types", "passenger_profile_ptc_age_or_dob_contradiction")
                manual_review.append(
                    {
                        "agency_id": agency_id,
                        "collection": "passenger_profiles",
                        "record_id": passenger.get("id"),
                        "domain": "passenger_types",
                        "reason": "ptc_age_or_dob_contradiction",
                        "messages": validation["errors"],
                        "evaluation_date": date.today().isoformat(),
                    }
                )
        for domain, id_field, code_field in (
            ("countries", "nationality_reference_id", "nationality"),
            ("countries", "residence_country_reference_id", "residence_country"),
            ("countries", "passport_country_reference_id", "passport_country"),
            ("languages", "primary_language_reference_id", "primary_language"),
            ("document_types", "travel_document_type_id", "travel_document_type_code"),
        ):
            analyze_value(
                agency_id=agency_id,
                collection="passenger_profiles",
                record_id=passenger.get("id"),
                domain=domain,
                reference_id=passenger.get(id_field),
                legacy_value=passenger.get(code_field),
                field=code_field,
            )

    requests = await db.collection("travel_requests").find_many(
        sort=[("agency_id", 1), ("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT,
    )
    first_departure_by_request = {
        str(request.get("id")): parsed_date(
            request.get("first_departure_date") or request.get("requested_departure_date")
        )
        for request in requests
    }

    request_passengers = await db.collection("request_passengers").find_many(
        sort=[("agency_id", 1), ("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT,
    )
    for passenger in request_passengers:
        agency_id = str(passenger.get("agency_id") or "unscoped")
        ptc = analyze_value(
            agency_id=agency_id,
            collection="request_passengers",
            record_id=passenger.get("id"),
            domain="passenger_types",
            reference_id=passenger.get("passenger_type_code_id"),
            legacy_value=passenger.get("passenger_type_code") or passenger.get("snapshot_passenger_type"),
            field="passenger_type_code",
        )
        travel_date = first_departure_by_request.get(str(passenger.get("request_id")))
        if ptc and travel_date and (ptc.get("metadata_json") or ptc.get("metadata") or {}).get("passenger_category"):
            validation = validate_ptc_for_date(
                ptc,
                date_of_birth=parsed_date(passenger.get("snapshot_date_of_birth")),
                travel_date=travel_date,
            )
            if validation["errors"]:
                increment(agency_id, "passenger_types", "request_passenger_ptc_age_or_dob_contradiction")
                manual_review.append(
                    {
                        "agency_id": agency_id,
                        "collection": "request_passengers",
                        "record_id": passenger.get("id"),
                        "domain": "passenger_types",
                        "reason": "ptc_age_or_dob_contradiction",
                        "messages": validation["errors"],
                        "first_segment_date": travel_date.isoformat(),
                    }
                )
        analyze_value(
            agency_id=agency_id,
            collection="request_passengers",
            record_id=passenger.get("id"),
            domain="countries",
            reference_id=passenger.get("nationality_reference_id"),
            legacy_value=passenger.get("nationality_code"),
            field="nationality_code",
        )

    for segment in await db.collection("request_segments").find_many(
        sort=[("agency_id", 1), ("request_id", 1), ("sequence", 1), ("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT,
    ):
        agency_id = str(segment.get("agency_id") or "unscoped")
        for domain, id_field, code_field in (
            ("airports", "origin_airport_id", "origin_airport_code"),
            ("airports", "destination_airport_id", "destination_airport_code"),
            ("airlines", "marketing_airline_id", "marketing_airline"),
            ("airlines", "operating_airline_id", "operating_airline"),
            ("cabin_classes", "cabin_reference_id", "cabin_preference"),
        ):
            analyze_value(
                agency_id=agency_id,
                collection="request_segments",
                record_id=segment.get("id"),
                domain=domain,
                reference_id=segment.get(id_field),
                legacy_value=segment.get(code_field),
                field=code_field,
            )

    for pet in await db.collection("request_pets").find_many(
        sort=[("agency_id", 1), ("request_id", 1), ("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT,
    ):
        agency_id = str(pet.get("agency_id") or "unscoped")
        for domain, id_field, legacy_value, field in (
            ("pet_species", "species_reference_id", pet.get("species_key") or pet.get("species"), "species"),
            ("pet_breeds", "breed_reference_id", pet.get("breed_key") or pet.get("breed") or pet.get("breed_free_text"), "breed"),
            ("container_types", "container_type_reference_id", pet.get("crate_type"), "crate_type"),
        ):
            analyze_value(
                agency_id=agency_id,
                collection="request_pets",
                record_id=pet.get("id"),
                domain=domain,
                reference_id=pet.get(id_field),
                legacy_value=legacy_value,
                field=field,
            )

    for item in await db.collection("request_special_items").find_many(
        sort=[("agency_id", 1), ("request_id", 1), ("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT,
    ):
        agency_id = str(item.get("agency_id") or "unscoped")
        analyze_value(
            agency_id=agency_id,
            collection="request_special_items",
            record_id=item.get("id"),
            domain="special_item_categories",
            reference_id=item.get("item_category_reference_id"),
            legacy_value=item.get("item_category_code") or item.get("item_type"),
            field="item_category_code",
        )
        details = item.get("canonical_details") or {}
        analyze_value(
            agency_id=agency_id,
            collection="request_special_items",
            record_id=item.get("id"),
            domain="currencies",
            reference_id=item.get("declared_value_currency_id"),
            legacy_value=details.get("currency"),
            field="declared_value_currency",
        )

    duplicate_records = [
        {
            "domain": domain,
            "scope": scope,
            "agency_id": agency_id or None,
            "code_or_key": code,
            "active_record_count": count,
        }
        for (domain, scope, agency_id, code), count in sorted(duplicate_scope_keys.items())
        if count > 1
    ]
    cross_scope_conflicts = []
    for domain, codes in sorted(active_by_domain_code.items()):
        for code, records in sorted(codes.items()):
            unique_records = {str(record.get("id")): record for record in records}
            global_ids = sorted(
                record_id
                for record_id, record in unique_records.items()
                if str(record.get("scope") or "global") == "global"
            )
            agency_records = sorted(
                (
                    str(record.get("agency_id") or ""),
                    record_id,
                )
                for record_id, record in unique_records.items()
                if str(record.get("scope") or "global") == "agency"
            )
            if global_ids and agency_records:
                cross_scope_conflicts.append(
                    {
                        "domain": domain,
                        "code_or_key": code,
                        "global_reference_ids": global_ids,
                        "agency_references": [
                            {"agency_id": agency_id or None, "reference_id": record_id}
                            for agency_id, record_id in agency_records
                        ],
                    }
                )
    after_counts = {
        name: await db.collection(name).count()
        for name in scanned_collections
    }
    if before_counts != after_counts:
        raise RuntimeError("Reference migration analysis changed persisted records.")
    return {
        "dry_run": True,
        "writes_performed": 0,
        "bounded_query_limit": MAXIMUM_QUERY_LIMIT,
        "counts_by_agency": {
            agency_id: dict(sorted(counts.items()))
            for agency_id, counts in sorted(by_agency.items())
        },
        "counts_by_domain": {
            domain: dict(sorted(counts.items()))
            for domain, counts in sorted(by_domain.items())
        },
        "candidate_mappings": sorted(
            candidates,
            key=lambda item: (item["agency_id"], item["collection"], str(item["record_id"]), item["field"]),
        ),
        "ambiguous_mappings": sorted(
            ambiguous,
            key=lambda item: (item["agency_id"], item["collection"], str(item["record_id"]), item["field"]),
        ),
        "manual_review_cases": sorted(
            manual_review,
            key=lambda item: (
                item["agency_id"],
                item["collection"],
                str(item["record_id"]),
                item.get("field") or "",
                item["reason"],
            ),
        ),
        "duplicate_active_scope_codes": duplicate_records,
        "cross_scope_conflicts": cross_scope_conflicts,
        "scanned_collections": list(scanned_collections),
        "before_counts": before_counts,
        "after_counts": after_counts,
        "write_mode_available": False,
    }


def canonical_reference_readiness_metadata() -> dict[str, Any]:
    return {
        "canonical_owner": "GlobalReferenceRecord",
        "normalized_option_contract_enabled": True,
        "passenger_type_reference_metadata_enabled": True,
        "request_v4_reference_snapshots_enabled": True,
        "passenger_profile_reference_snapshots_enabled": True,
        "historical_snapshot_relabeling_disabled": True,
        "active_selection_enforced": True,
        "bounded_usage_registry_enabled": True,
        "governed_deactivation_enabled": True,
        "dry_run_reconciliation_analysis_enabled": True,
        "production_migration_enabled": False,
        "public_domain_allowlist_enabled": True,
        "readiness_required": False,
    }


async def resolve_passenger_profile_references(
    db: Database,
    agency_id: str,
    data: dict[str, Any],
    *,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved = dict(data)
    ptc_fields = {
        "passenger_type",
        "passenger_type_code_id",
        "passenger_type_code",
        "passenger_type_label",
    }
    ptc_fields_supplied = bool(ptc_fields.intersection(data))
    existing_reference_id = str((existing or {}).get("passenger_type_code_id") or "")
    existing_code = str(
        (existing or {}).get("passenger_type_code")
        or (existing or {}).get("passenger_type")
        or ""
    )
    supplied_reference_id = str(
        (
            data.get("passenger_type_code_id")
            if "passenger_type_code_id" in data
            else existing_reference_id
        )
        or ""
    )
    supplied_code = str(
        data.get("passenger_type_code")
        or data.get("passenger_type")
        or existing_code
        or "ADT"
    )
    same_reference = bool(existing) and (
        (existing_reference_id and supplied_reference_id == existing_reference_id)
        or (
            not existing_reference_id
            and not supplied_reference_id
            and normalize_domain_code("passenger_types", supplied_code)
            == normalize_domain_code("passenger_types", existing_code)
        )
    )
    selection_changed = not existing or (ptc_fields_supplied and not same_reference)
    existing_birth_date = (existing or {}).get("date_of_birth")
    submitted_birth_date = data.get("date_of_birth", existing_birth_date)
    date_changed = not existing or str(submitted_birth_date or "") != str(existing_birth_date or "")
    should_validate = selection_changed or date_changed
    record: dict[str, Any] | None = None
    if selection_changed:
        record, resolution = await resolve_reference(
            db,
            "passenger_types",
            reference_id=supplied_reference_id or None,
            code=supplied_code,
            agency_id=agency_id,
            active_required=True,
            allow_uninitialized_legacy=True,
        )
        if record:
            snapshot = reference_snapshot(record)
            legacy_alias = next(
                (
                    str(alias).upper()
                    for alias in record.get("aliases") or []
                    if str(alias).upper() == supplied_code.upper()
                ),
                None,
            )
            compatibility_code = passenger_type_compatibility_code(
                record,
                legacy_alias or supplied_code,
            )
            resolved.update(
                {
                    "passenger_type_code_id": snapshot["id"],
                    "passenger_type_code": legacy_alias or snapshot["code"],
                    "passenger_type_label": snapshot["label"],
                    "passenger_type": compatibility_code,
                    "passenger_type_reconciliation_status": (
                        "resolved"
                        if (record.get("metadata_json") or record.get("metadata") or {}).get("passenger_category")
                        else "legacy_reference_incomplete"
                    ),
                }
            )
        else:
            resolved.update(
                {
                    "passenger_type_code_id": None,
                    "passenger_type_code": supplied_code.upper(),
                    "passenger_type_label": data.get("passenger_type_label") or supplied_code.upper(),
                    "passenger_type": data.get("passenger_type") or supplied_code.upper(),
                    "passenger_type_reconciliation_status": resolution,
                }
            )
    elif existing:
        for field in (
            "passenger_type",
            "passenger_type_code_id",
            "passenger_type_code",
            "passenger_type_label",
            "passenger_type_reconciliation_status",
        ):
            if field in existing:
                resolved[field] = existing[field]
        if existing_reference_id and (date_changed or ptc_fields_supplied):
            record = await db.collection("global_reference_records").find_one(
                {
                    "domain": "passenger_types",
                    "id": existing_reference_id,
                }
            )
            if not record:
                resolved["passenger_type_reconciliation_status"] = "missing_reference_historical"
                should_validate = False
            elif (
                str(record.get("scope") or "global") != "global"
                and record.get("agency_id") != agency_id
            ):
                resolved["passenger_type_reconciliation_status"] = "cross_scope_reference_historical"
                record = None
                should_validate = False
            elif not record.get("is_active", True):
                resolved["passenger_type_reconciliation_status"] = "resolved_inactive_historical"

    if (
        should_validate
        and record
        and (record.get("metadata_json") or record.get("metadata") or {}).get("passenger_category")
    ):
        date_of_birth = resolved.get("date_of_birth") or (existing or {}).get("date_of_birth")
        if isinstance(date_of_birth, str):
            date_of_birth = date.fromisoformat(date_of_birth)
        validation = validate_ptc_for_date(
            record,
            date_of_birth=date_of_birth,
            travel_date=date.today(),
        )
        if validation["errors"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "field": "passenger_type_code_id",
                    "messages": validation["errors"],
                },
            )

    for domain, id_field, code_field, label_field in (
        ("countries", "nationality_reference_id", "nationality", "nationality_label"),
        ("countries", "residence_country_reference_id", "residence_country", "residence_country_label"),
        ("countries", "passport_country_reference_id", "passport_country", "passport_country_label"),
        ("languages", "primary_language_reference_id", "primary_language", "primary_language_label"),
        ("document_types", "travel_document_type_id", "travel_document_type_code", "travel_document_type_label"),
    ):
        reference_id = data.get(id_field)
        code = data.get(code_field)
        if reference_id:
            reference, _ = await resolve_reference(
                db,
                domain,
                reference_id=reference_id,
                agency_id=agency_id,
                active_required=True,
            )
            snapshot = reference_snapshot(reference)
            resolved[id_field] = snapshot["id"]
            resolved[code_field] = snapshot["code"]
            resolved[label_field] = snapshot["label"]
        elif existing and id_field not in data and code_field not in data:
            for field in (id_field, code_field, label_field):
                if field in existing:
                    resolved[field] = existing[field]
    return resolved
