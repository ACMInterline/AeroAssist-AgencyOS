#!/usr/bin/env python3
import sys
from pathlib import Path
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    AirlineKnowledgeChangeReview,
    AirlineKnowledgeChangeSet,
    AirlineKnowledgeFieldChange,
    AirlineKnowledgeImpactAssessment,
    AirlineKnowledgeRevalidationRequest,
    AirlineKnowledgeVersion,
    AirlineKnowledgeVersionItem,
)
from services.airline_knowledge_versioning_service import (
    CHANGE_CATEGORIES,
    IMPACT_TARGET_COLLECTIONS,
    PHASE_LABEL,
    VERSIONED_OBJECT_COLLECTIONS,
    VERSIONING_COLLECTIONS,
    AirlineKnowledgeVersioningService,
)
from smoke_airline_knowledge_governance_foundation import release_payload
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request
from smoke_operational_scenario_testing_foundation import scenario_payload
from smoke_visual_policy_editor_foundation import card_payload


EXPECTED_PHASE = "phase_55_8_airline_contact_communication_intelligence_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/knowledge-versions"
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def require_text(path: Path, text: str) -> None:
    if text not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    if text.lower() in path.read_text(encoding="utf-8").lower():
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def assert_no_restricted_material(value: object) -> None:
    restricted = {
        "snapshot_json",
        "snapshot_hash",
        "machine_diff_json",
        "triggering_source_ids",
        "internal_notes",
        "review_notes",
        "reviewer_user_id",
        "before_value",
        "after_value",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if key in restricted:
                raise AssertionError(f"Agency update response leaked restricted field {key}")
            assert_no_restricted_material(child)
    elif isinstance(value, list):
        for item in value:
            assert_no_restricted_material(item)


def verify_models_collections_and_indexes() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected Phase 55.3 label: {PHASE_LABEL}")
    expected_collections = {
        "airline_knowledge_versions",
        "airline_knowledge_version_items",
        "airline_knowledge_change_sets",
        "airline_knowledge_field_changes",
        "airline_knowledge_impact_assessments",
        "airline_knowledge_change_reviews",
        "airline_knowledge_revalidation_requests",
    }
    if set(VERSIONING_COLLECTIONS) != expected_collections:
        raise AssertionError(f"Versioning collection registration is incomplete: {VERSIONING_COLLECTIONS}")
    if not expected_collections.issubset(AGENCY_OWNED_COLLECTIONS):
        raise AssertionError("Versioning metadata collections are not registered for tenant-aware persistence.")
    required_types = {
        "airline_profile",
        "airline_policy",
        "structured_policy_json",
        "operational_rule",
        "pricing_formula",
        "capability_row",
        "evidence_assertion",
        "service_instruction",
        "ssr_osi_template",
        "emd_rfic_rfisc_rule",
        "distribution_capability",
        "contact",
        "service_desk",
        "published_knowledge_package",
    }
    if set(VERSIONED_OBJECT_COLLECTIONS) != required_types:
        raise AssertionError("Canonical versioned-object registry is incomplete.")
    required_impacts = {
        "published_release",
        "scenario_test",
        "policy_comparison",
        "recommendation",
        "active_offer",
        "booking_readiness_package",
        "passenger_service_case",
        "agency_knowledge_assignment",
        "future_trip",
        "unresolved_case",
    }
    if set(IMPACT_TARGET_COLLECTIONS) != required_impacts:
        raise AssertionError("Operational impact registry is incomplete.")

    version = AirlineKnowledgeVersion(knowledge_version_reference="AKV-MODEL", historical_snapshot_immutable=True)
    item = AirlineKnowledgeVersionItem(
        version_id=version.id,
        object_type="airline_policy",
        source_collection="visual_policy_editor_cards",
        source_entity_id="policy-model",
        snapshot_json={"limits": {"max_weight_kg": 8}},
        snapshot_hash="hash-model",
    )
    change_set = AirlineKnowledgeChangeSet(
        change_set_reference="AKC-MODEL",
        base_version_id=version.id,
        target_version_id="target-model",
        change_summary="Model change",
    )
    records = [
        AirlineKnowledgeFieldChange(change_set_id=change_set.id, version_item_key="policy:model", object_type="airline_policy", field_path="limits.max_weight_kg", operation="modified", change_category="restriction_increased", human_summary="Limit changed."),
        AirlineKnowledgeImpactAssessment(change_set_id=change_set.id, impact_type="scenario_test", target_collection="operational_scenario_tests", target_id="scenario-model", impact_summary="Review scenario."),
        AirlineKnowledgeChangeReview(change_set_id=change_set.id),
        AirlineKnowledgeRevalidationRequest(change_set_id=change_set.id, request_type="re_qa", reason="Material change."),
    ]
    if not item.historical_snapshot_immutable or any(not record.id for record in records):
        raise AssertionError("Phase 55.3 models did not preserve immutable version relationships.")

    database_text = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "airline_knowledge_versions_airline_lifecycle_lookup",
        "airline_knowledge_version_items_version_object_unique",
        "airline_knowledge_change_sets_pair_unique",
        "airline_knowledge_field_changes_set_path_lookup",
        "airline_knowledge_impact_assessments_target_lookup",
        "airline_knowledge_change_reviews_set_created_lookup",
        "airline_knowledge_revalidation_requests_set_type_unique",
    ]:
        if index_name not in database_text:
            raise AssertionError(f"Mongo index registration missing {index_name}")


def verify_structured_diff_and_safety() -> None:
    service = AirlineKnowledgeVersioningService(None)  # type: ignore[arg-type]
    before = {
        "limits": {"max_weight_kg": 8, "container_count": 1},
        "rules": [{"rule_reference": "PETC-1", "outcome": "conditional", "severity": "medium"}],
        "pricing": {"formula": "base_fee + handling", "amount": 100},
        "effective_from": "2026-01-01",
        "warnings": ["Confirm aircraft"],
        "evidence_links": ["evidence-old"],
    }
    after = {
        "limits": {"max_weight_kg": 6, "container_count": 2},
        "rules": [{"rule_reference": "PETC-1", "outcome": "not_supported", "severity": "critical"}],
        "pricing": {"formula": "base_fee + handling + channel_fee", "amount": 125},
        "effective_from": "2026-03-01",
        "warnings": ["Confirm aircraft", "Manual approval required"],
        "evidence_links": ["evidence-new"],
    }
    changes = service.structured_diff(before, after)
    paths = {item["field_path"] for item in changes}
    for expected in [
        "limits.max_weight_kg",
        "limits.container_count",
        "rules[rule_reference=PETC-1].outcome",
        "rules[rule_reference=PETC-1].severity",
        "pricing.formula",
        "pricing.amount",
        "effective_from",
        "warnings[+]",
        "evidence_links[+]",
        "evidence_links[-]",
    ]:
        if expected not in paths:
            raise AssertionError(f"Structured comparison missing {expected}: {paths}")
    by_path = {item["field_path"]: item for item in changes}
    if by_path["limits.max_weight_kg"]["change_category"] != "restriction_increased" or by_path["limits.max_weight_kg"]["severity"] != "critical":
        raise AssertionError("Restriction direction and severity categorization are incorrect.")
    if by_path["pricing.amount"]["change_category"] != "pricing_increase":
        raise AssertionError("Pricing direction was not categorized.")
    if by_path["effective_from"]["change_category"] != "effective_date_change":
        raise AssertionError("Effective-date change was not categorized.")
    if not all(item.get("human_summary") and item.get("machine_diff_json") for item in changes):
        raise AssertionError("Structured comparison did not produce human and machine diffs.")
    if not set(CHANGE_CATEGORIES).issuperset({item["change_category"] for item in changes}):
        raise AssertionError("Structured comparison emitted an unknown change category.")
    for key, enabled in service.safety_flags().items():
        if enabled is not True:
            raise AssertionError(f"Versioning safety flag is disabled: {key}")

    service_path = ROOT / "backend/services/airline_knowledge_versioning_service.py"
    for forbidden in ["requests.get(", "requests.post(", "httpx.", "openai", "backgroundtasks", "asyncio.create_task", ".delete_one(", ".delete_many(", "seed_core_data"]:
        reject_text(service_path, forbidden)


def verify_routes_ui_and_docs(paths: dict) -> None:
    expected = {
        "/api/platform/knowledge-versions": {"get", "post"},
        "/api/platform/knowledge-versions/compare": {"post"},
        "/api/platform/knowledge-versions/change-sets": {"get"},
        "/api/platform/knowledge-versions/change-sets/{change_set_id}": {"get"},
        "/api/platform/knowledge-versions/change-sets/{change_set_id}/review": {"put"},
        "/api/platform/knowledge-versions/revalidation-requests/{request_id}": {"put"},
        "/api/platform/knowledge-versions/versions/{version_id}": {"get"},
        "/api/agencies/{agency_id}/knowledge-updates": {"get"},
        "/api/agencies/{agency_id}/knowledge-updates/{change_set_id}": {"get"},
    }
    for path, methods in expected.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/knowledge-updates",
        "/api/agencies/{agency_id}/knowledge-updates/{change_set_id}",
    ]:
        mutations = set(paths.get(path, {})) & {"post", "put", "patch", "delete"}
        if mutations:
            raise AssertionError(f"Agency knowledge update route is not read-only: {path} {mutations}")
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
        if path.startswith("/api/platform/knowledge-versions/version-items") and set(paths[path]) & {"put", "patch", "delete"}:
            raise AssertionError("Immutable version-item mutation route was registered.")

    checks = [
        ("frontend/src/App.jsx", "/platform/knowledge-versions"),
        ("frontend/src/App.jsx", "/agency/knowledge-updates"),
        ("frontend/src/lib/moduleCatalog.js", "Knowledge Updates"),
        ("frontend/src/pages/platform/AirlineKnowledgeVersionsPage.jsx", "Historical operational snapshots are never rewritten"),
        ("frontend/src/pages/agency/KnowledgeUpdatesPage.jsx", "Draft changes and restricted source details are not visible"),
        ("docs/architecture/airline-knowledge-versioning-change-detection-foundation.md", "Phase 50.4 `airline_knowledge_versions` governance envelope"),
        ("BUILD_PHASES.md", "Implemented Phase 55.3"),
        ("README.md", "Phase 55.3 Airline Knowledge Versioning And Change Detection"),
        ("docs/architecture/current-model-inventory.md", "airline_knowledge_change_sets"),
        ("docs/architecture/canonical-route-policy.md", "/api/platform/knowledge-versions"),
        ("docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Phase 55.3 Alignment"),
        ("docs/architecture/supplementary-blueprint-adoption-map.md", "Phase 55.3 Airline Knowledge Versioning"),
        ("docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 55.3 Versioning And Change Detection"),
        ("docs/architecture/foundations/GLOSSARY.md", "Knowledge Change Set"),
        ("backend/services/blueprint_adoption_service.py", "Airline Knowledge Versioning And Change Detection"),
    ]
    for relative, text in checks:
        require_text(ROOT / relative, text)
    require_text(ROOT / "backend/routers/agency_airline_knowledge_versioning.py", "assert_agency_access")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("airline_knowledge_versioning_change_detection_foundation") or {}
    for key in [
        "airline_knowledge_versioning_change_detection_enabled",
        "canonical_airline_knowledge_version_reused",
        "immutable_version_items_enabled",
        "structured_nested_diff_enabled",
        "formula_change_detection_enabled",
        "impact_assessment_enabled",
        "re_qa_request_enabled",
        "republish_request_enabled",
        "historical_snapshot_mutation_disabled",
        "agency_published_updates_read_only",
        "unpublished_draft_agency_visibility_disabled",
        "metadata_only",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Readiness missing Phase 55.3 flag {key}: {section}")
    for key in ["version_count", "immutable_version_item_count", "change_set_count", "field_change_count", "impact_assessment_count", "open_revalidation_count"]:
        if key not in section:
            raise AssertionError(f"Readiness missing Phase 55.3 counter {key}")


def version_payload(agency_id: str, reference: str, policy_id: str, source_id: str, lifecycle_status: str, previous_version_id: str | None = None) -> dict:
    return {
        "agency_id": agency_id,
        "knowledge_version_reference": reference,
        "version_label": reference,
        "semantic_version": reference.split("-")[-1],
        "lifecycle_status": lifecycle_status,
        "published_at": "2026-07-14T00:00:00Z" if lifecycle_status == "published" else None,
        "effective_from": "2026-08-01T00:00:00Z",
        "previous_version_id": previous_version_id,
        "triggering_source_ids": [source_id],
        "affected_airline_codes": ["LH"],
        "affected_service_families": ["pets_animals", "PETC"],
        "affected_route_scopes": ["SOF-FRA"],
        "detect_changes": False,
        "items": [
            {
                "object_type": "airline_policy",
                "source_entity_id": policy_id,
                "service_family": "PETC",
                "route_scope": "SOF-FRA",
                "triggering_source_ids": [source_id],
                "publication_status": lifecycle_status,
            }
        ],
    }


def verify_live_versioning() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Phase 55.3 smoke requires a seeded agency.")
    agency_id = agencies[0]["id"]
    token = uuid4().hex[:10]

    policy = post(
        "/api/platform/visual-policy-editor",
        card_payload(agency_id, f"VPE-VERSION-{token}"),
        OWNER_HEADERS,
        201,
    )["visual_policy_editor_card"]
    evidence_source = post(
        "/api/platform/airline-evidence/sources",
        {
            "scope": "agency",
            "agency_id": agency_id,
            "source_reference": f"AES-VERSION-{token}",
            "source_type": "airline_operational_bulletin",
            "title": "PETC operational policy change bulletin",
            "captured_at": "2026-07-14T00:00:00Z",
            "effective_from": "2026-08-01",
            "evidence_status": "approved",
            "accessibility": "internal_restricted",
            "internal_notes": "Restricted source detail for platform review.",
        },
        OWNER_HEADERS,
        201,
    )["source"]

    first = post(
        PLATFORM_BASE,
        version_payload(agency_id, f"AKV-{token}-1", policy["id"], evidence_source["id"], "published"),
        OWNER_HEADERS,
        201,
    )
    first_version = first["version"]
    first_item = first["items"][0]
    if first_item.get("snapshot_json", {}).get("limits", {}).get("max_weight_kg") != 8 or first_item.get("historical_snapshot_immutable") is not True:
        raise AssertionError("Initial canonical policy snapshot was not captured immutably.")

    scenario_data = scenario_payload(agency_id, f"OST-VERSION-{token}")
    scenario_data["evidence_links"] = [{"reference": policy["id"], "source": "version-impact-smoke"}]
    scenario = post("/api/platform/operational-scenario-testing", scenario_data, OWNER_HEADERS, 201)["operational_scenario_test"]

    updated_policy = put(
        f"/api/platform/visual-policy-editor/{policy['id']}",
        {
            "effective_from": "2026-08-01",
            "support_status": "request_required",
            "limits": {"max_weight_kg": 6, "container_count": 2},
            "required_documents": [
                {"document_type": "pet_passport", "required": True},
                {"document_type": "veterinary_certificate", "required": True},
            ],
            "warnings": policy["warnings"] + [{"audience": "agent", "message": "New six kilogram total limit."}],
            "evidence_links": [{"reference": evidence_source["id"], "source": "airline_operational_bulletin"}],
        },
        OWNER_HEADERS,
    )["visual_policy_editor_card"]
    if updated_policy.get("limits", {}).get("max_weight_kg") != 6:
        raise AssertionError("Canonical policy update required for version comparison did not persist.")

    second = post(
        PLATFORM_BASE,
        version_payload(agency_id, f"AKV-{token}-2", policy["id"], evidence_source["id"], "published", first_version["id"]),
        OWNER_HEADERS,
        201,
    )
    second_version = second["version"]
    release_data = release_payload(agency_id, second_version["id"], f"AKR-VERSION-{token}")
    release_data.update({"release_status": "published", "airline_codes": ["LH"], "service_domains": ["PETC", "pets_animals"]})
    release = post("/api/platform/airline-knowledge-governance/releases", release_data, OWNER_HEADERS, 201)["airline_knowledge_release"]

    compared = post(
        f"{PLATFORM_BASE}/compare",
        {"base_version_id": first_version["id"], "target_version_id": second_version["id"]},
        OWNER_HEADERS,
        201,
    )
    change_set = compared["change_set"]
    field_changes = compared.get("field_changes") or []
    if change_set.get("re_qa_required") is not True or change_set.get("republish_required") is not True:
        raise AssertionError(f"Material published change did not create revalidation requirements: {change_set}")
    if release["id"] not in (change_set.get("published_release_ids") or []) or evidence_source["id"] not in (change_set.get("triggering_source_ids") or []):
        raise AssertionError("Change set did not preserve source cause and published release trace.")
    paths = {item.get("field_path") for item in field_changes}
    for path in ["limits.max_weight_kg", "support_status", "effective_from", "required_documents[document_type=veterinary_certificate]"]:
        if path not in paths:
            raise AssertionError(f"Live structured change set missing {path}: {paths}")
    if not any(item.get("change_category") == "restriction_increased" and item.get("severity") == "critical" for item in field_changes):
        raise AssertionError("Live restriction increase was not categorized as critical.")
    impact_types = {item.get("impact_type") for item in compared.get("impact_assessments") or []}
    if not {"published_release", "scenario_test"}.issubset(impact_types):
        raise AssertionError(f"Published release and scenario impacts were not detected: {impact_types}")
    if not all(item.get("historical_snapshot_mutation_prohibited") is True for item in compared.get("impact_assessments") or []):
        raise AssertionError("Impact assessment did not protect historical snapshots.")
    request_types = {item.get("request_type") for item in compared.get("revalidation_requests") or []}
    if request_types != {"re_qa", "republish"}:
        raise AssertionError(f"Expected explicit QA and republish requests: {request_types}")

    retained_first = get(f"{PLATFORM_BASE}/versions/{first_version['id']}", OWNER_HEADERS)
    retained_snapshot = retained_first["items"][0]["snapshot_json"]
    if retained_snapshot.get("limits", {}).get("max_weight_kg") != 8 or retained_first["items"][0].get("snapshot_hash") != first_item.get("snapshot_hash"):
        raise AssertionError("Historical knowledge snapshot changed after its canonical source was updated.")
    if retained_snapshot.get("updated_at") == updated_policy.get("updated_at"):
        raise AssertionError("Historical snapshot was silently replaced with the mutable source record.")

    detail = get(f"{PLATFORM_BASE}/change-sets/{change_set['id']}", OWNER_HEADERS)
    if len(detail.get("field_changes") or []) != change_set.get("field_change_count"):
        raise AssertionError("Change-set detail did not preserve deterministic field changes.")
    reviewed = put(
        f"{PLATFORM_BASE}/change-sets/{change_set['id']}/review",
        {"review_status": "accepted", "review_decision": "revalidate", "review_notes": "Human review retained both historical versions."},
        OWNER_HEADERS,
    )
    if reviewed.get("change_set", {}).get("review_status") != "accepted":
        raise AssertionError("Change review metadata was not persisted.")
    first_revalidation = detail["revalidation_requests"][0]
    completed = put(
        f"{PLATFORM_BASE}/revalidation-requests/{first_revalidation['id']}",
        {"request_status": "in_progress", "completion_notes": "Assigned to QA."},
        OWNER_HEADERS,
    )
    if completed.get("revalidation_request", {}).get("request_status") != "in_progress":
        raise AssertionError("Revalidation status metadata was not updated.")

    draft = post(
        PLATFORM_BASE,
        version_payload(agency_id, f"AKV-{token}-3", policy["id"], evidence_source["id"], "draft", second_version["id"]),
        OWNER_HEADERS,
        201,
    )["version"]
    draft_compare = post(
        f"{PLATFORM_BASE}/compare",
        {"base_version_id": second_version["id"], "target_version_id": draft["id"]},
        OWNER_HEADERS,
        201,
    )["change_set"]
    if draft_compare.get("agency_visible") is not False:
        raise AssertionError("Draft version change was marked agency-visible.")

    agency_updates = get(f"/api/agencies/{agency_id}/knowledge-updates", OWNER_HEADERS)
    visible_ids = {item.get("id") for item in agency_updates.get("updates") or []}
    if change_set["id"] not in visible_ids or draft_compare["id"] in visible_ids or agency_updates.get("read_only") is not True:
        raise AssertionError(f"Agency published/draft update visibility is incorrect: {agency_updates}")
    assert_no_restricted_material(agency_updates)
    agency_detail = get(f"/api/agencies/{agency_id}/knowledge-updates/{change_set['id']}", OWNER_HEADERS)
    assert_no_restricted_material(agency_detail)
    request("POST", f"/api/agencies/{agency_id}/knowledge-updates", {}, OWNER_HEADERS, 405)
    request("GET", PLATFORM_BASE, None, AGENCY_AGENT_HEADERS, 403)
    if len(agencies) > 1:
        isolated = get(f"/api/agencies/{agencies[1]['id']}/knowledge-updates", OWNER_HEADERS)
        if change_set["id"] in {item.get("id") for item in isolated.get("updates") or []}:
            raise AssertionError("Agency-scoped knowledge update leaked to another agency.")

    filtered = get(f"{PLATFORM_BASE}/change-sets?category=restriction_increased&revalidation_required=true", OWNER_HEADERS)
    if change_set["id"] not in {item.get("id") for item in filtered.get("items") or []}:
        raise AssertionError("Change-set category and revalidation filters omitted the created change.")
    if scenario.get("id") not in {item.get("target_id") for item in compared.get("impact_assessments") or []}:
        raise AssertionError("Scenario impact did not retain its canonical target linkage.")


def main() -> int:
    verify_models_collections_and_indexes()
    verify_structured_diff_and_safety()
    paths = get("/openapi.json").get("paths") or {}
    verify_routes_ui_and_docs(paths)
    verify_readiness()
    verify_live_versioning()
    print("Phase 55.3 airline knowledge versioning and change detection foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
