#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from models import (
    AirlineDistributionSummary,
    AirlineGroupRelationship,
    AirlineHubAssignment,
    AirlineIdentityAlias,
    AirlineMasterProfile,
    AirlineOperationalClassification,
    AirlineProfileEvidenceLink,
    AirlineProfileRevision,
    AirlineServiceDeskSummary,
)
from services.airline_master_profile_intelligence_service import (
    PHASE_LABEL,
    PROFILE_COLLECTIONS,
    AirlineMasterProfileIntelligenceService,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_55_2_airline_policy_evidence_source_governance_foundation"
ROOT = Path(__file__).resolve().parents[2]
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def require_text(path: Path, text: str) -> None:
    if text not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    if text.lower() in path.read_text(encoding="utf-8").lower():
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def verify_models_and_collections() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected Phase 55.1 label: {PHASE_LABEL}")
    expected_collections = {
        "airline_master_profiles",
        "airline_identity_aliases",
        "airline_group_relationships",
        "airline_hub_assignments",
        "airline_operational_classifications",
        "airline_distribution_summaries",
        "airline_service_desk_summaries",
        "airline_profile_evidence_links",
        "airline_profile_revisions",
    }
    if set(PROFILE_COLLECTIONS) != expected_collections:
        raise AssertionError(f"Profile collection registration is incomplete: {PROFILE_COLLECTIONS}")

    profile = AirlineMasterProfile(canonical_airline_id="canonical-airline", commercial_name="Example", review_status="approved")
    if profile.canonical_airline_id != "canonical-airline":
        raise AssertionError("Airline master profile did not preserve canonical identity linkage.")
    records = [
        AirlineIdentityAlias(canonical_airline_id="canonical-airline", alias="Example Air", normalized_alias="EXAMPLE AIR"),
        AirlineGroupRelationship(canonical_airline_id="canonical-airline", relationship_type="parent"),
        AirlineHubAssignment(canonical_airline_id="canonical-airline", airport_code="FRA"),
        AirlineOperationalClassification(canonical_airline_id="canonical-airline", classifications=["full_service"]),
        AirlineDistributionSummary(canonical_airline_id="canonical-airline", gds_participation=["AMADEUS"]),
        AirlineServiceDeskSummary(canonical_airline_id="canonical-airline", desk_type="medical"),
        AirlineProfileEvidenceLink(canonical_airline_id="canonical-airline", source_collection="airline_knowledge_sources", source_record_id="source-1"),
        AirlineProfileRevision(canonical_airline_id="canonical-airline", profile_id=profile.id, version=1, change_type="created"),
    ]
    if any(record.canonical_airline_id != profile.canonical_airline_id for record in records):
        raise AssertionError("Related profile models do not reuse canonical airline identity.")

    database_text = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "airline_master_profiles_canonical_unique",
        "airline_identity_aliases_normalized_unique",
        "airline_group_relationships_canonical_airline_id_1_relationship_type_1",
        "airline_hub_assignments_canonical_airline_id_1_assignment_type_1",
        "airline_profile_revisions_canonical_airline_id_1_version_1",
    ]:
        if index_name not in database_text and index_name.replace("_canonical_airline_id_1_relationship_type_1", "") not in database_text and index_name.replace("_canonical_airline_id_1_assignment_type_1", "") not in database_text and index_name.replace("_canonical_airline_id_1_version_1", "") not in database_text:
            raise AssertionError(f"Mongo index registration missing {index_name}")


def verify_scoring_and_safety() -> None:
    service = AirlineMasterProfileIntelligenceService(None)  # type: ignore[arg-type]
    identity = {
        "legal_name": "Example Airways Ltd",
        "commercial_name": "Example Airways",
        "iata_code": "EA",
        "icao_code": "EXA",
        "accounting_prefix_code": "999",
        "country_of_registration": "Example",
        "operating_status": "active",
        "airline_type": "full_service",
    }
    profile = {"review_status": "approved", "effective_from": "2026-01-01", "last_verified_at": "2026-06-01T00:00:00Z", "source_reference_ids": ["source-1"], "confidence": "high"}
    complete = service.calculate_completeness(identity, profile, [{}], [{}], [{}], [{}], [{}], [{}], [{"evidence_status": "verified", "conflict_status": "none"}])
    incomplete = service.calculate_completeness({**identity, "icao_code": None}, None, [], [], [], [], [], [], [])
    if complete["score"] <= incomplete["score"] or "icao_code" not in incomplete["missing_fields"]:
        raise AssertionError("Profile completeness scoring is not deterministic or does not expose unknown fields.")
    high = service.calculate_confidence(profile, [{"evidence_status": "verified", "conflict_status": "none"}], complete["score"])
    conflict = service.calculate_confidence(profile, [{"evidence_status": "verified", "conflict_status": "unresolved"}], complete["score"])
    if high["score"] <= conflict["score"] or conflict["conflicting_evidence_count"] != 1:
        raise AssertionError("Profile confidence does not retain and penalize conflicting evidence.")
    flags = service.safety_flags()
    for key in ["canonical_airline_identity_reused", "duplicate_airline_catalogue_disabled", "raw_source_truth_preserved", "conflicting_evidence_preserved", "agency_read_only", "internal_notes_restricted", "automatic_production_seeding_disabled", "metadata_only"]:
        if flags.get(key) is not True:
            raise AssertionError(f"Missing Phase 55.1 safety flag: {key}")

    service_path = ROOT / "backend/services/airline_master_profile_intelligence_service.py"
    for forbidden in ["seed_core_data", "requests.get(", "requests.post(", "httpx.", "openai", "backgroundtasks", "asyncio.create_task", ".delete_one(", ".delete_many("]:
        reject_text(service_path, forbidden)


def verify_routes_ui_docs(paths: dict) -> None:
    expected = {
        "/api/platform/airline-master-profiles": {"get", "post"},
        "/api/platform/airline-master-profiles/coverage": {"get"},
        "/api/platform/airline-master-profiles/duplicate-candidates": {"get"},
        "/api/platform/airline-master-profiles/{airline_id}": {"get", "put"},
        "/api/platform/airline-master-profiles/{airline_id}/aliases": {"post"},
        "/api/platform/airline-master-profiles/{airline_id}/relationships": {"post"},
        "/api/platform/airline-master-profiles/{airline_id}/evidence": {"post"},
        "/api/platform/airline-master-profiles/{airline_id}/revisions": {"get"},
        "/api/agencies/{agency_id}/airline-master-profiles": {"get"},
        "/api/agencies/{agency_id}/airline-master-profiles/{airline_id}": {"get"},
        "/api/agencies/{agency_id}/airline-master-profiles/{airline_id}/client-safe": {"get"},
    }
    for path, methods in expected.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")

    checks = [
        ("frontend/src/App.jsx", "/platform/airline-master-profiles"),
        ("frontend/src/App.jsx", "/agency/airline-profiles"),
        ("frontend/src/lib/moduleCatalog.js", "Airline Master Profiles"),
        ("frontend/src/lib/moduleCatalog.js", "Airline Profiles"),
        ("frontend/src/pages/platform/AirlineMasterProfilesPage.jsx", "does not create a second airline catalogue"),
        ("frontend/src/pages/agency/AirlineProfilesPage.jsx", "Approved and published operational profile metadata"),
        ("docs/architecture/airline-master-profile-intelligence-foundation.md", "canonical identity remains the existing `airline_profiles` record"),
        ("BUILD_PHASES.md", "Implemented Phase 55.1"),
        ("README.md", "Phase 55.1 Airline Master Profile Intelligence"),
        ("docs/architecture/current-model-inventory.md", "airline_profile_revisions"),
        ("docs/architecture/canonical-route-policy.md", "/api/platform/airline-master-profiles"),
        ("docs/architecture/foundations/GLOSSARY.md", "Airline Master Profile"),
        ("docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 55.1 Profile Context"),
        ("docs/architecture/supplementary-blueprint-adoption-map.md", "Phase 55.1 Airline Master Profile Intelligence"),
        ("docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Phase 55.1 Alignment"),
        ("backend/services/blueprint_adoption_service.py", "Airline Master Profile Intelligence"),
    ]
    for relative, text in checks:
        require_text(ROOT / relative, text)
    require_text(ROOT / "backend/routers/agency_airline_master_profiles.py", "assert_agency_access")


def assert_no_internal_material(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"internal_notes", "before_snapshot", "after_snapshot", "actor_user_id", "source_collection", "source_record_id"}:
                raise AssertionError(f"Agency response leaked restricted field {key}")
            assert_no_internal_material(child)
    elif isinstance(value, list):
        for item in value:
            assert_no_internal_material(item)


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("airline_master_profile_intelligence_foundation") or {}
    for key in ["airline_master_profile_intelligence_enabled", "canonical_airline_identity_reused", "duplicate_airline_catalogue_disabled", "platform_profile_governance_enabled", "agency_approved_published_read_only_enabled", "alias_resolution_enabled", "profile_completeness_scoring_enabled", "profile_confidence_scoring_enabled", "effective_dating_enabled", "revision_history_enabled", "conflicting_evidence_preserved", "internal_notes_restricted", "automatic_production_seeding_disabled", "metadata_only"]:
        if section.get(key) is not True:
            raise AssertionError(f"Readiness missing Phase 55.1 flag {key}: {section}")
    for key in ["canonical_airline_count", "enriched_profile_count", "evidence_link_count", "duplicate_candidate_count"]:
        if key not in section:
            raise AssertionError(f"Readiness missing Phase 55.1 counter {key}")


def verify_live_api(paths: dict) -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    platform = get("/api/platform/airline-master-profiles", OWNER_HEADERS)
    if platform.get("canonical_airline_identity_reused") is not True or not platform.get("items"):
        raise AssertionError(f"Platform airline directory did not compose canonical identities: {platform}")
    target = next((item for item in platform["items"] if not item.get("profile")), platform["items"][0])
    airline_id = target["identity"]["canonical_airline_id"]
    if target.get("profile"):
        put(f"/api/platform/airline-master-profiles/{airline_id}?reason=Phase%2055.1%20smoke", {"review_status": "approved", "internal_notes": "restricted smoke notes"}, OWNER_HEADERS)
    else:
        post(
            "/api/platform/airline-master-profiles",
            {
                "canonical_airline_id": airline_id,
                "commercial_name": target["identity"]["commercial_name"],
                "accounting_prefix_code": "999",
                "airline_type": "full_service",
                "active_status": "active",
                "source_reference_ids": ["smoke-source"],
                "evidence_status": "verified",
                "confidence": "high",
                "effective_from": "2026-01-01",
                "review_status": "approved",
                "last_verified_at": "2026-07-14T00:00:00Z",
                "internal_notes": "restricted smoke notes",
            },
            OWNER_HEADERS,
        )

    alias = f"{target['identity']['commercial_name']} Phase 55 Alias"
    created_alias = post(f"/api/platform/airline-master-profiles/{airline_id}/aliases", {"alias": alias, "alias_type": "commercial_name", "confidence": "high", "review_status": "approved", "effective_from": "2026-01-01"}, OWNER_HEADERS)["item"]
    if created_alias.get("canonical_airline_id") != airline_id:
        raise AssertionError("Alias did not retain canonical airline mapping.")
    post(f"/api/platform/airline-master-profiles/{airline_id}/relationships", {"relationship_type": "alliance_member", "related_airline_name": "Smoke Partner", "review_status": "approved", "confidence": "medium", "effective_from": "2026-01-01"}, OWNER_HEADERS)
    post(f"/api/platform/airline-master-profiles/{airline_id}/hubs", {"airport_code": "FRA", "assignment_type": "primary_hub", "review_status": "approved", "effective_from": "2026-01-01"}, OWNER_HEADERS)
    post(f"/api/platform/airline-master-profiles/{airline_id}/classifications", {"classifications": ["full_service"], "route_regions": ["Europe"], "international_operation": True, "long_haul": True, "operation_profile": "passenger", "review_status": "approved", "effective_from": "2026-01-01"}, OWNER_HEADERS)
    post(f"/api/platform/airline-master-profiles/{airline_id}/distribution", {"gds_participation": ["AMADEUS"], "ndc_available": True, "agency_support_available": True, "validating_carrier_capability": True, "emd_support_summary": "Known support requires operational confirmation.", "review_status": "approved", "effective_from": "2026-01-01"}, OWNER_HEADERS)
    post(f"/api/platform/airline-master-profiles/{airline_id}/service-desks", {"desk_type": "medical", "available": True, "service_summary": "Medical desk metadata", "internal_notes": "restricted desk notes", "review_status": "approved", "effective_from": "2026-01-01"}, OWNER_HEADERS)
    post(f"/api/platform/airline-master-profiles/{airline_id}/evidence", {"source_collection": "airline_knowledge_sources", "source_record_id": "smoke-source", "evidence_status": "verified", "confidence": "high", "review_status": "approved", "conflict_status": "unresolved", "field_paths": ["distribution.ndc_available"], "effective_from": "2026-01-01", "last_verified_at": "2026-07-14T00:00:00Z", "internal_notes": "restricted evidence notes"}, OWNER_HEADERS)
    updated = put(f"/api/platform/airline-master-profiles/{airline_id}?reason=Evidence%20review", {"last_verified_at": "2026-07-14T01:00:00Z"}, OWNER_HEADERS)["item"]
    if len(updated.get("revision_history") or []) < 2:
        raise AssertionError("Airline profile revision history was not preserved.")
    if updated.get("confidence", {}).get("conflicting_evidence_count") != 1:
        raise AssertionError("Conflicting profile evidence was not retained.")
    resolved = get(f"/api/platform/airline-master-profiles/{created_alias['normalized_alias'].replace(' ', '%20')}", OWNER_HEADERS)["item"]
    if resolved["identity"]["canonical_airline_id"] != airline_id:
        raise AssertionError("Alias resolution did not return canonical airline identity.")

    request("GET", "/api/platform/airline-master-profiles", None, AGENCY_AGENT_HEADERS, 403)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("No agency available for agency-safe profile smoke.")
    agency_id = agencies[0]["id"]
    agency = get(f"/api/agencies/{agency_id}/airline-master-profiles/{airline_id}", AGENCY_AGENT_HEADERS)
    if agency.get("agency_read_only") is not True or agency.get("item", {}).get("profile", {}).get("review_status") not in {"approved", "published"}:
        raise AssertionError(f"Agency profile is not approved/published read-only metadata: {agency}")
    assert_no_internal_material(agency)
    agency_list = get(f"/api/agencies/{agency_id}/airline-master-profiles", AGENCY_AGENT_HEADERS)
    if set(agency_list.get("coverage") or {}) != {"visible_profile_count", "approved_or_published_count"}:
        raise AssertionError(f"Agency profile coverage leaked platform governance totals: {agency_list.get('coverage')}")
    client_safe = get(f"/api/agencies/{agency_id}/airline-master-profiles/{airline_id}/client-safe", AGENCY_AGENT_HEADERS)
    if set(client_safe.get("identity") or {}) - {"canonical_airline_id", "commercial_name", "iata_code", "icao_code", "country_of_registration", "operating_status", "alliance", "evidence_freshness"}:
        raise AssertionError(f"Client-safe identity contains non-minimal fields: {client_safe}")
    request("POST", f"/api/agencies/{agency_id}/airline-master-profiles", {}, AGENCY_AGENT_HEADERS, 405)


def main() -> int:
    verify_models_and_collections()
    verify_scoring_and_safety()
    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    verify_routes_ui_docs(paths)
    verify_readiness()
    verify_live_api(paths)
    print("Phase 55.1 airline master profile intelligence foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
