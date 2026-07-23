#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from fastapi import HTTPException


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE, phase_is_exact
from database import Database
from models import (
    Agency,
    CommercialPilotFeedbackCreate,
    CommercialPilotFeedbackReviewUpdate,
)
from routers.agency_pilot_feedback import authorize as authorize_agency_feedback
from services.commercial_pilot_readiness_service import (
    PHASE_LABEL,
    PILOT_DOCUMENTS,
    CommercialPilotReadinessError,
    CommercialPilotReadinessService,
    commercial_pilot_readiness_metadata,
)
from services.agency_onboarding_service import AgencyOnboardingService


async def verify_feedback_and_readiness() -> None:
    database = Database()
    service = CommercialPilotReadinessService(database)
    for agency in (
        Agency(id="pilot-agency-a", name="Pilot Agency A", legal_name="Pilot Agency A Ltd", slug="pilot-agency-a"),
        Agency(id="pilot-agency-b", name="Pilot Agency B", legal_name="Pilot Agency B Ltd", slug="pilot-agency-b"),
        Agency(id="legacy-agency", name="Legacy Agency", legal_name="Legacy Agency Ltd", slug="legacy-agency"),
    ):
        await database.collection("agencies").insert_one(agency.model_dump(mode="json"))
    for membership in (
        {"id": "membership-owner", "agency_id": "pilot-agency-a", "user_id": "agency-owner", "agency_role": "agency_owner", "status": "active"},
        {"id": "membership-readonly", "agency_id": "pilot-agency-a", "user_id": "agency-reader", "agency_role": "agency_readonly", "status": "active"},
    ):
        await database.collection("agency_staff_memberships").insert_one(membership)
    onboarding_service = AgencyOnboardingService(database)
    await onboarding_service.initialize_for_new_agency("pilot-agency-a", "platform-reviewer")

    await authorize_agency_feedback(
        database,
        "pilot-agency-a",
        {"id": "agency-owner", "global_role": "agency_user"},
        write=True,
    )
    await authorize_agency_feedback(
        database,
        "pilot-agency-a",
        {"id": "agency-reader", "global_role": "agency_user"},
        write=False,
    )
    try:
        await authorize_agency_feedback(
            database,
            "pilot-agency-a",
            {"id": "agency-reader", "global_role": "agency_user"},
            write=True,
        )
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("Agency read-only role was allowed to submit pilot feedback.")

    await database.collection("travel_requests").insert_one(
        {
            "id": "request-a",
            "agency_id": "pilot-agency-a",
            "request_reference": "REQ-PILOT-A",
            "title": "Sofia to London",
        }
    )
    await database.collection("travel_requests").insert_one(
        {
            "id": "request-b",
            "agency_id": "pilot-agency-b",
            "request_reference": "REQ-PILOT-B",
            "title": "Other agency request",
        }
    )
    agency_user = {
        "id": "agency-owner",
        "full_name": "Agency Owner",
        "email": "owner@example.test",
        "global_role": "agency_user",
    }
    platform_user = {
        "id": "platform-reviewer",
        "full_name": "Platform Reviewer",
        "email": "reviewer@example.test",
        "global_role": "platform_admin",
    }
    created = await service.submit_feedback(
        "pilot-agency-a",
        CommercialPilotFeedbackCreate(
            category="workflow",
            title="Request handoff needs context",
            description="The next action was clear, but the route summary needed more context.",
            affected_area="requests",
            urgency="high",
            related_record_type="request",
            related_record_id="request-a",
        ),
        agency_user,
    )
    assert created["status"] == "submitted"
    assert created["related_record_label"] == "REQ-PILOT-A · Sofia to London"
    assert created["submitted_by"] == "agency-owner"

    try:
        await service.submit_feedback(
            "pilot-agency-a",
            CommercialPilotFeedbackCreate(
                category="defect",
                title="Cross-agency record",
                description="This reference belongs to a different tenant and must be rejected.",
                affected_area="requests",
                related_record_type="request",
                related_record_id="request-b",
            ),
            agency_user,
        )
    except CommercialPilotReadinessError as exc:
        assert "Cross-agency records cannot be linked" in str(exc)
    else:
        raise AssertionError("Cross-agency feedback reference was accepted.")

    try:
        await service.submit_feedback(
            "pilot-agency-a",
            CommercialPilotFeedbackCreate(
                category="data",
                title="Incomplete reference",
                description="A related record type without an identifier must be rejected.",
                affected_area="requests",
                related_record_type="request",
            ),
            agency_user,
        )
    except CommercialPilotReadinessError as exc:
        assert "supplied together" in str(exc)
    else:
        raise AssertionError("Incomplete related-record reference was accepted.")

    await service.submit_feedback(
        "pilot-agency-b",
        CommercialPilotFeedbackCreate(
            category="documentation",
            title="Daily guide wording",
            description="The daily operations checklist needs one additional example.",
            affected_area="operations",
        ),
        platform_user,
    )
    agency_a = await service.list_agency_feedback("pilot-agency-a")
    agency_b = await service.list_agency_feedback("pilot-agency-b")
    assert [item["id"] for item in agency_a["items"]] == [created["id"]]
    assert len(agency_b["items"]) == 1
    try:
        await service.get_agency_feedback("pilot-agency-a", agency_b["items"][0]["id"])
    except CommercialPilotReadinessError as exc:
        assert str(exc) == "Pilot feedback not found."
    else:
        raise AssertionError("Agency feedback detail leaked a different tenant.")

    try:
        await service.review_feedback(
            created["id"],
            CommercialPilotFeedbackReviewUpdate(status="resolved", review_notes="Skipped review."),
            platform_user,
        )
    except CommercialPilotReadinessError as exc:
        assert "cannot move" in str(exc)
    else:
        raise AssertionError("Invalid pilot-feedback lifecycle jump was accepted.")

    for next_status in ("reviewing", "planned", "resolved", "closed"):
        reviewed = await service.review_feedback(
            created["id"],
            CommercialPilotFeedbackReviewUpdate(
                status=next_status,
                review_notes=f"Moved to {next_status} during governed review.",
            ),
            platform_user,
        )
        assert reviewed["status"] == next_status
        if next_status == "reviewing":
            reviewed = await service.review_feedback(
                created["id"],
                CommercialPilotFeedbackReviewUpdate(
                    status="reviewing",
                    review_notes="Additional review context without a lifecycle jump.",
                ),
                platform_user,
            )
            assert reviewed["review_notes"].startswith("Additional review context")
    persisted = await database.collection("commercial_pilot_feedback").find_one({"id": created["id"]})
    assert persisted["agency_id"] == "pilot-agency-a"
    assert persisted["title"] == created["title"]
    assert persisted["related_record_id"] == "request-a"
    assert await database.collection("audit_events").count(
        {"agency_id": "pilot-agency-a", "entity_type": "commercial_pilot_feedback"}
    ) == 6

    platform = await service.list_platform_feedback(status="closed")
    assert len(platform["items"]) == 1 and platform["items"][0]["agency_name"] == "Pilot Agency A"

    base_signals = {
        "configuration_ready": True,
        "configuration_warnings": 0,
        "database_ready": True,
        "smoke_inventory_ready": True,
        "onboarding_ready": True,
        "demo_profiles_ready": True,
        "operations_ready": True,
        "product_standards_ready": True,
        "documentation_ready": True,
        "feedback_ready": True,
        "execution_boundaries_disabled": True,
        "agency_onboarding_state": None,
        "agency_demo_ready": None,
    }
    ready = service.classify_checks(service.build_checks(base_signals))
    conditional = service.classify_checks(
        service.build_checks({**base_signals, "configuration_warnings": 1})
    )
    blocked = service.classify_checks(
        service.build_checks({**base_signals, "database_ready": False})
    )
    assert ready.status == "ready"
    assert conditional.status == "conditionally_ready" and conditional.warning_count == 1
    assert blocked.status == "blocked" and blocked.blocker_count == 1

    legacy = await service.assess("legacy-agency")
    legacy_check = next(item for item in legacy["checks"] if item["key"] == "selected_agency_onboarding")
    assert legacy_check["status"] == "pass"
    assert legacy["phase_57_release_gate"]["preserved"] is True
    assert legacy["phase_57_release_gate"]["replaced_by_commercial_assessment"] is False

    incomplete = await service.assess("pilot-agency-a")
    incomplete_check = next(
        item for item in incomplete["checks"] if item["key"] == "selected_agency_onboarding"
    )
    demo_check = next(
        item for item in incomplete["checks"] if item["key"] == "selected_agency_demo"
    )
    assert incomplete_check["status"] == "warning"
    assert demo_check["status"] == "warning"
    assert incomplete["status"] == "conditionally_ready"

    await database.collection("agency_onboarding_profiles").update_one(
        {"agency_id": "pilot-agency-a", "profile_key": "commercial_pilot"},
        {"onboarding_status": "completed", "demo_workspace_seeded": True},
    )
    completed = await service.assess("pilot-agency-a")
    completed_check = next(
        item for item in completed["checks"] if item["key"] == "selected_agency_onboarding"
    )
    completed_demo_check = next(
        item for item in completed["checks"] if item["key"] == "selected_agency_demo"
    )
    assert completed_check["status"] == "pass"
    assert completed_demo_check["status"] == "pass"
    assert completed["status"] in {"ready", "conditionally_ready"}
    assert not any(
        item["key"] in {"selected_agency_onboarding", "selected_agency_demo"}
        and item["status"] != "pass"
        for item in completed["checks"]
    )


def verify_registration_and_safety() -> None:
    assert phase_is_exact(CURRENT_BUILD_PHASE, CURRENT_BUILD_PHASE)
    assert CURRENT_BUILD_PHASE == PHASE_LABEL
    metadata = commercial_pilot_readiness_metadata()
    assert metadata["pilot_document_count"] == 13
    assert metadata["tenant_scoped_feedback_enabled"] is True
    assert metadata["phase_57_release_gate_preserved"] is True
    for key in (
        "anonymous_feedback_enabled",
        "public_feedback_endpoint_enabled",
        "external_support_integration_enabled",
        "automatic_release_approval_enabled",
        "automatic_production_seeding_enabled",
        "provider_execution_enabled",
        "payment_execution_enabled",
        "ticketing_execution_enabled",
    ):
        assert metadata[key] is False, key

    assert len(PILOT_DOCUMENTS) == 13
    for item in PILOT_DOCUMENTS:
        path = ROOT / item["path"]
        assert path.is_file(), f"Missing pilot document: {item['path']}"

    expected = {
        "backend/server.py": [
            '"commercial_pilot_readiness": True',
            '"commercial_pilot_readiness": commercial_pilot_readiness_metadata()',
            "agency_pilot_feedback.router",
            "platform_pilot_feedback.router",
            "platform_commercial_pilot_readiness.router",
        ],
        "backend/database.py": [
            '"commercial_pilot_feedback"',
            "commercial_pilot_feedback_agency_status_submitted_lookup",
            "commercial_pilot_feedback_platform_review_lookup",
        ],
        "backend/persistence_query.py": [
            '"commercial_pilot_feedback"',
            "commercial_pilot_feedback_agency_status_submitted_lookup",
        ],
        "backend/routers/agency_pilot_feedback.py": [
            'prefix="/api/agencies/{agency_id}/pilot-feedback"',
            "Depends(get_current_user)",
            "require_any_agency_role",
        ],
        "backend/routers/platform_pilot_feedback.py": [
            'prefix="/api/platform/pilot-feedback"',
            "require_any_platform_role",
            '@router.patch("/{feedback_id}")',
        ],
        "backend/routers/platform_commercial_pilot_readiness.py": [
            'prefix="/api/platform/commercial-pilot-readiness"',
            "require_any_platform_role",
        ],
        "frontend/src/App.jsx": [
            '"/agency/pilot-feedback"',
            '"/platform/pilot-feedback"',
            '"/platform/commercial-pilot-readiness"',
        ],
        "frontend/src/lib/moduleCatalog.js": [
            "Pilot Help & Feedback",
            "Pilot Feedback Review",
            "Commercial Pilot Readiness",
        ],
        "frontend/src/pages/agency/PilotFeedbackPage.jsx": [
            "No pilot feedback yet",
            "Submitting...",
            "Feedback could not be saved",
            "belongs to another agency",
        ],
        "frontend/src/pages/platform/PilotFeedbackReviewPage.jsx": [
            "No feedback matches these filters",
            "Lifecycle transitions are validated",
        ],
        "frontend/src/pages/platform/CommercialPilotReadinessPage.jsx": [
            "Phase 57 governance remains authoritative",
            "Blocking checks",
            "Controlled pilot package",
        ],
        "docs/architecture/canonical-route-policy.md": [
            "Phase 58.5 Commercial Pilot Readiness Routes",
            "no public or anonymous feedback route",
        ],
        "docs/architecture/current-model-inventory.md": [
            "Phase 58.5 Commercial Pilot Readiness",
            "`commercial_pilot_feedback`",
        ],
    }
    for relative, markers in expected.items():
        content = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in content, f"Missing {marker!r} in {relative}"

    for relative, area in (
        ("frontend/src/pages/agency/AgencyOnboardingPage.jsx", "onboarding"),
        ("frontend/src/pages/agency/OperationsCommandCenterPage.jsx", "operations"),
        ("frontend/src/pages/agency/RequestsPage.jsx", "requests"),
        ("frontend/src/pages/agency/OffersPage.jsx", "offers"),
        ("frontend/src/pages/agency/BookingWorkspacesPage.jsx", "booking"),
        ("frontend/src/pages/agency/PassengersPage.jsx", "passengers"),
        ("frontend/src/pages/agency/DocumentWorkspacesPage.jsx", "documents"),
        ("frontend/src/pages/agency/AgentWorkQueuePage.jsx", "tasks"),
    ):
        content = (ROOT / relative).read_text(encoding="utf-8")
        assert "pilot-feedback" in content or f'<PilotGuidance area="{area}"' in content

    service_source = (ROOT / "backend/services/commercial_pilot_readiness_service.py").read_text(
        encoding="utf-8"
    )
    for forbidden in ("import requests", "import httpx", "import openai", "BackgroundTasks", "send_email", "send_sms"):
        assert forbidden not in service_source, forbidden


async def main() -> None:
    verify_registration_and_safety()
    await verify_feedback_and_readiness()
    print("Commercial Pilot readiness smoke passed.")


if __name__ == "__main__":
    asyncio.run(main())
