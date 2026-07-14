#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import AirlineKnowledgePublication, AirlineKnowledgePublicationCreate
from services.airline_knowledge_publishing_service import (
    AIRLINE_KNOWLEDGE_PUBLICATIONS_COLLECTION,
    PHASE_LABEL,
    PUBLICATION_STATUSES,
    RELEASE_CHANNELS,
    VISIBILITY_STATUSES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_55_6_interline_codeshare_operating_carrier_intelligence_foundation"
ROOT = Path(__file__).resolve().parents[2]


def run_ref(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def assert_safety_flags(payload: dict) -> None:
    for flag in [
        "metadata_only",
        "airline_knowledge_publishing_foundation",
        "automatic_publication_disabled",
        "recommendation_execution_disabled",
        "auto_approval_disabled",
        "provider_integrations_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing safety flag {flag}: {payload}")


def publication_payload(agency_id: str, reference: str, status: str = "approved") -> dict:
    return {
        "agency_id": agency_id,
        "publication_reference": reference,
        "publication_name": "Phase 52.7 LH PETC publication pack",
        "airline_codes": ["lh"],
        "service_families": ["pets_animals"],
        "included_knowledge_version_ids": ["AKV-SMOKE-527"],
        "included_policy_cards": ["VPC-SMOKE-527"],
        "included_pricing_formulas": ["PFB-SMOKE-527"],
        "included_rules": ["ORC-SMOKE-527"],
        "qa_review_ids": ["KQA-SMOKE-527"],
        "publication_status": status,
        "release_channel": "agency_reference",
        "effective_from": "2026-08-01",
        "effective_until": "2027-08-01",
        "supersedes_publication_ids": ["AKP-SMOKE-OLD"],
        "rollback_plan": {"owner": "platform_knowledge_editor", "steps": ["mark superseded", "restore previous publication metadata"]},
        "consumer_readiness": {"agency_workspace": "ready", "offer_builder": "ready", "scenario_testing": "ready"},
        "AOIE_ready": True,
        "agency_visibility": {"visibility_status": "selected_agencies", "agency_ids": [agency_id]},
        "approved_at": "2026-07-10T09:00:00+00:00",
        "published_at": "2026-07-11T09:00:00+00:00",
        "metadata": {"smoke": True, "human_authority_final": True},
    }


def verify_model_and_collection_registration() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")
    if AIRLINE_KNOWLEDGE_PUBLICATIONS_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("airline_knowledge_publications is not registered as agency-owned metadata.")
    for value in ["approved", "published", "archived"]:
        if value not in PUBLICATION_STATUSES:
            raise AssertionError(f"Missing publication status: {value}")
    for value in ["agency_reference", "scenario_testing", "production_reference"]:
        if value not in RELEASE_CHANNELS:
            raise AssertionError(f"Missing release channel: {value}")
    for value in ["selected_agencies", "all_agencies", "platform_only"]:
        if value not in VISIBILITY_STATUSES:
            raise AssertionError(f"Missing visibility status: {value}")

    create = AirlineKnowledgePublicationCreate(**publication_payload("agency-smoke", "AKP-SMOKE-MODEL"))
    record = AirlineKnowledgePublication(**create.model_dump(mode="json", exclude_none=True))
    if record.publication_reference != "AKP-SMOKE-MODEL" or not record.included_policy_cards:
        raise AssertionError("AirlineKnowledgePublication model did not preserve included knowledge metadata.")
    if record.airline_knowledge_publishing_foundation is not True or record.automatic_publication_disabled is not True:
        raise AssertionError("AirlineKnowledgePublication model did not preserve metadata-only flags.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        AIRLINE_KNOWLEDGE_PUBLICATIONS_COLLECTION,
        "airline_knowledge_publications_reference_unique",
        "airline_knowledge_publications_agency_status_lookup",
        "airline_knowledge_publications_status_lookup",
        "airline_knowledge_publications_release_channel_lookup",
        "airline_knowledge_publications_airline_lookup",
        "airline_knowledge_publications_service_family_lookup",
        "airline_knowledge_publications_knowledge_version_lookup",
        "airline_knowledge_publications_policy_card_lookup",
        "airline_knowledge_publications_pricing_formula_lookup",
        "airline_knowledge_publications_rule_lookup",
        "airline_knowledge_publications_qa_review_lookup",
        "airline_knowledge_publications_aoie_ready_lookup",
        "airline_knowledge_publications_visibility_status_lookup",
        "airline_knowledge_publications_archive_lookup",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/airline-knowledge-publishing", "get"),
        ("/api/platform/airline-knowledge-publishing", "post"),
        ("/api/platform/airline-knowledge-publishing/summary", "get"),
        ("/api/platform/airline-knowledge-publishing/{publication_id}", "get"),
        ("/api/platform/airline-knowledge-publishing/{publication_id}", "put"),
        ("/api/platform/airline-knowledge-publishing/{publication_id}", "delete"),
        ("/api/agencies/{agency_id}/published-knowledge", "get"),
        ("/api/agencies/{agency_id}/published-knowledge", "post"),
        ("/api/agencies/{agency_id}/published-knowledge/summary", "get"),
        ("/api/agencies/{agency_id}/published-knowledge/{publication_id}", "get"),
        ("/api/agencies/{agency_id}/published-knowledge/{publication_id}", "put"),
        ("/api/agencies/{agency_id}/published-knowledge/{publication_id}", "delete"),
    ]:
        assert_openapi_path(paths, path, method)
    for path in paths:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/admin"):
            raise AssertionError(f"Old admin route must not be registered: {path}")
        if "airline-knowledge-publishing" in lowered or "published-knowledge" in lowered:
            for marker in ["/publish-now", "/auto-publish", "/execute-recommendation", "/run-recommendation"]:
                if marker in lowered:
                    raise AssertionError(f"Forbidden publication execution route registered: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/knowledge-publishing"),
        (ROOT / "frontend/src/App.jsx", "/agency/published-knowledge"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Knowledge Publishing"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Published Knowledge"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgePublishingPage.jsx", "Included Knowledge"),
        (ROOT / "frontend/src/pages/agency/PublishedKnowledgePage.jsx", "Supersession / Rollback"),
        (ROOT / "backend/services/saas_subscription_service.py", "airline_knowledge_publishing"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Airline Knowledge Publishing"),
        (ROOT / "docs/architecture/airline-knowledge-publishing-foundation.md", "Phase 52.7"),
        (ROOT / "docs/architecture/current-model-inventory.md", "airline_knowledge_publications"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/platform/knowledge-publishing"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Airline Knowledge Publishing"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Airline knowledge publishing"),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "airline_knowledge_publications"),
        (ROOT / "docs/architecture/knowledge-quality-assurance-foundation.md", "Airline Knowledge Publishing Relationship"),
        (ROOT / "docs/architecture/reference-data-engine-foundation.md", "Airline Knowledge Publishing Relationship"),
        (ROOT / "docs/architecture/knowledge-import-templates-foundation.md", "airline_knowledge_publications"),
        (ROOT / "docs/architecture/visual-policy-editor-foundation.md", "Airline Knowledge Publishing"),
        (ROOT / "docs/architecture/pricing-formula-builder-foundation.md", "Airline Knowledge Publishing"),
        (ROOT / "docs/architecture/operational-rule-composer-foundation.md", "Airline Knowledge Publishing"),
        (ROOT / "docs/architecture/service-parameter-taxonomy-integration-foundation.md", "Airline Knowledge Publishing Alignment"),
        (ROOT / "docs/architecture/intelligent-offer-builder-integration-foundation.md", "Phase 52.7 Airline Knowledge Publishing"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 52.7"),
        (ROOT / "docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md", "Phase 52.7"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Airline Knowledge Publishing"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 52.7"),
        (ROOT / "README.md", "airline knowledge publication records"),
    ]:
        require_text(path, text)


def verify_crud_and_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")

    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires at least one seeded agency.")
    agency_id = agencies[0]["id"]

    platform_reference = run_ref("AKP-SMOKE-PLATFORM")
    created = post(
        "/api/platform/airline-knowledge-publishing",
        publication_payload(agency_id, platform_reference),
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(created)
    platform_publication = created["airline_knowledge_publication"]
    assert_safety_flags(platform_publication)
    if platform_publication.get("airline_codes") != ["LH"] or platform_publication.get("AOIE_ready") is not True:
        raise AssertionError("Platform publication did not preserve airline or AOIE readiness metadata.")
    for field in [
        "included_knowledge_version_ids",
        "included_policy_cards",
        "included_pricing_formulas",
        "included_rules",
        "qa_review_ids",
        "supersedes_publication_ids",
    ]:
        if not platform_publication.get(field):
            raise AssertionError(f"Platform publication missing persisted field {field}.")
    for section in [
        "overview_section",
        "included_knowledge_section",
        "readiness_section",
        "release_control_section",
        "supersession_section",
        "lifecycle_section",
        "boundary_section",
    ]:
        if section not in platform_publication:
            raise AssertionError(f"Projected publication missing section {section}.")

    filtered = get(
        "/api/platform/airline-knowledge-publishing?airline_code=LH&service_family=pets_animals&publication_status=approved&release_channel=agency_reference&agency_visibility=selected_agencies&AOIE_ready=true&search=PETC",
        OWNER_HEADERS,
    )
    if not any(item.get("publication_reference") == platform_reference for item in filtered.get("items", [])):
        raise AssertionError("Platform publication filters did not return created metadata.")

    summary = get("/api/platform/airline-knowledge-publishing/summary", OWNER_HEADERS).get("summary") or {}
    if summary.get("airline_knowledge_publication_count", 0) < 1:
        raise AssertionError("Platform publication summary did not count records.")
    if summary.get("qa_review_count", 0) < 1 or summary.get("knowledge_version_count", 0) < 1:
        raise AssertionError("Platform publication summary did not count linked knowledge.")

    updated = put(
        f"/api/platform/airline-knowledge-publishing/{platform_publication['id']}",
        {"publication_status": "published", "release_channel": "production_reference", "consumer_readiness": {"agency_workspace": "ready", "offer_builder": "reviewed"}},
        OWNER_HEADERS,
    )["airline_knowledge_publication"]
    if updated.get("publication_status") != "published" or updated.get("release_channel") != "production_reference":
        raise AssertionError("Platform publication update did not persist status/channel metadata.")

    agency_reference = run_ref("AKP-SMOKE-AGENCY")
    agency_payload = publication_payload(agency_id, agency_reference, status="scheduled")
    agency_payload["publication_name"] = "Phase 52.7 WCHR agency preview"
    agency_payload["service_families"] = ["passenger_assistance"]
    agency_payload["release_channel"] = "agency_preview"
    agency_created = post(
        f"/api/agencies/{agency_id}/published-knowledge",
        agency_payload,
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(agency_created)
    agency_publication = agency_created["airline_knowledge_publication"]
    if agency_publication.get("agency_id") != agency_id:
        raise AssertionError("Agency publication did not preserve agency scope.")

    agency_filtered = get(
        f"/api/agencies/{agency_id}/published-knowledge?service_family=passenger_assistance&publication_status=scheduled&release_channel=agency_preview&AOIE_ready=true",
        OWNER_HEADERS,
    )
    if not any(item.get("publication_reference") == agency_reference for item in agency_filtered.get("items", [])):
        raise AssertionError("Agency publication filters did not return created metadata.")

    agency_updated = put(
        f"/api/agencies/{agency_id}/published-knowledge/{agency_publication['id']}",
        {"publication_status": "approved", "agency_visibility": {"visibility_status": "all_agencies"}},
        OWNER_HEADERS,
    )["airline_knowledge_publication"]
    if agency_updated.get("agency_visibility", {}).get("visibility_status") != "all_agencies":
        raise AssertionError("Agency publication update did not persist visibility metadata.")

    archived = request(
        "DELETE",
        f"/api/agencies/{agency_id}/published-knowledge/{agency_publication['id']}",
        None,
        OWNER_HEADERS,
        200,
    )[1]
    if archived.get("archived") is not True:
        raise AssertionError("Agency publication archive did not return archived metadata.")

    readiness = get("/api/readiness", OWNER_HEADERS)
    section = readiness.get("airline_knowledge_publishing_foundation") or {}
    for flag in [
        "airline_knowledge_publishing_enabled",
        "airline_knowledge_publications_collection_enabled",
        "platform_airline_knowledge_publishing_metadata_crud_enabled",
        "agency_published_knowledge_metadata_crud_enabled",
        "controlled_publication_workflow_metadata_enabled",
        "automatic_publication_disabled",
        "recommendation_execution_disabled",
        "human_authority_final",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing flag: {flag}")
    if section.get("airline_knowledge_publication_knowledge_version_count", 0) < 1:
        raise AssertionError("Readiness did not count included knowledge versions.")
    if section.get("airline_knowledge_publication_qa_review_count", 0) < 1:
        raise AssertionError("Readiness did not count QA review links.")
    if section.get("airline_knowledge_publication_supersession_count", 0) < 1:
        raise AssertionError("Readiness did not count supersession links.")


def verify_boundaries() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    for path in openapi.get("paths") or {}:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/admin"):
            raise AssertionError(f"Old admin route registered: {path}")
        if "airline-knowledge-publishing" in lowered or "published-knowledge" in lowered:
            for marker in ["/publish-now", "/auto-publish", "/execute-recommendation", "/run-recommendation"]:
                if marker in lowered:
                    raise AssertionError(f"Forbidden Airline Knowledge Publishing execution route registered: {path}")

    for path in [
        ROOT / "backend/services/airline_knowledge_publishing_service.py",
        ROOT / "backend/routers/platform_airline_knowledge_publishing.py",
        ROOT / "backend/routers/agency_airline_knowledge_publishing.py",
        ROOT / "frontend/src/pages/platform/AirlineKnowledgePublishingPage.jsx",
        ROOT / "frontend/src/pages/agency/PublishedKnowledgePage.jsx",
    ]:
        for marker in [
            "import requests",
            "import httpx",
            "from openai",
            "import openai",
            "BackgroundTasks",
            "asyncio.create_task(",
            "def publish_",
            "def auto_publish",
            "def execute_recommendation",
            "auto_publish",
            "automatic_publication_enabled",
            "recommendation_execution_enabled",
            "provider_client =",
            "@router.post(\"/api/platform/airline-knowledge-publishing/publish",
            "@router.post(\"/api/platform/airline-knowledge-publishing/execute",
            "@router.post(\"/api/agencies/{agency_id}/published-knowledge/publish",
            "@router.post(\"/api/agencies/{agency_id}/published-knowledge/execute",
            "@router.get(\"/admin",
            "@router.post(\"/admin",
            "\"/api/admin",
        ]:
            reject_text(path, marker)


def main() -> int:
    verify_model_and_collection_registration()
    verify_router_ui_docs_registration()
    verify_crud_and_readiness()
    verify_boundaries()
    print("Airline knowledge publishing foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Airline knowledge publishing foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
