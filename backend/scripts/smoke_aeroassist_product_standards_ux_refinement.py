#!/usr/bin/env python3
from __future__ import annotations

import sys
import re
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
FRONTEND = ROOT / "frontend/src"
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE
from scripts.phase_assertions import application_phase_is_at_least
from services.aeroassist_product_standards_service import (
    PHASE_LABEL,
    aeroassist_product_standards_readiness_metadata,
)


COMPONENTS = {
    "PageHeader": "frontend/src/components/PageHeader.jsx",
    "SectionHeader": "frontend/src/components/SectionHeader.jsx",
    "PrimaryButton": "frontend/src/components/PrimaryButton.jsx",
    "SecondaryButton": "frontend/src/components/SecondaryButton.jsx",
    "DestructiveButton": "frontend/src/components/DestructiveButton.jsx",
    "EmptyState": "frontend/src/components/EmptyState.jsx",
    "LoadingState": "frontend/src/components/LoadingState.jsx",
    "ErrorState": "frontend/src/components/ErrorState.jsx",
    "StatusBadge": "frontend/src/components/StatusBadge.jsx",
    "PriorityBadge": "frontend/src/components/PriorityBadge.jsx",
    "FilterBar": "frontend/src/components/FilterBar.jsx",
    "ConfirmationDialog": "frontend/src/components/ConfirmationDialog.jsx",
    "DetailSummary": "frontend/src/components/DetailSummary.jsx",
    "Timeline": "frontend/src/components/Timeline.jsx",
    "OperationalAlert": "frontend/src/components/OperationalAlert.jsx",
    "FormSection": "frontend/src/components/FormSection.jsx",
}

MINIMUM_PHASE = PHASE_LABEL

SURFACES = {
    "onboarding": "frontend/src/pages/agency/AgencyOnboardingPage.jsx",
    "operations": "frontend/src/pages/agency/OperationsCommandCenterPage.jsx",
    "request_list": "frontend/src/pages/agency/RequestsPage.jsx",
    "request_create": "frontend/src/pages/agency/RequestCreatePage.jsx",
    "request_detail": "frontend/src/pages/agency/RequestDetailPage.jsx",
    "offer_list": "frontend/src/pages/agency/OffersPage.jsx",
    "offer_detail": "frontend/src/pages/agency/OfferDetailPage.jsx",
    "booking_list": "frontend/src/pages/agency/BookingWorkspacesPage.jsx",
    "booking_detail": "frontend/src/pages/agency/BookingWorkspaceDetailPage.jsx",
    "passenger_list": "frontend/src/pages/agency/PassengersPage.jsx",
    "passenger_detail": "frontend/src/pages/agency/PassengerDetailPage.jsx",
    "document_workspaces": "frontend/src/pages/agency/DocumentWorkspacesPage.jsx",
    "documents": "frontend/src/pages/agency/DocumentsPage.jsx",
    "tasks": "frontend/src/pages/agency/AgentWorkQueuePage.jsx",
}


def read(relative_path: str) -> str:
    path = ROOT / relative_path
    assert path.is_file(), f"Missing {relative_path}"
    return path.read_text(encoding="utf-8")


def require_markers(relative_path: str, markers: list[str]) -> None:
    content = read(relative_path)
    for marker in markers:
        assert marker in content, f"Missing {marker!r} in {relative_path}"


def verify_phase_and_readiness() -> None:
    assert application_phase_is_at_least(CURRENT_BUILD_PHASE, MINIMUM_PHASE)
    metadata = aeroassist_product_standards_readiness_metadata()
    for key in [
        "travel_first_terminology_enabled",
        "shared_product_components_enabled",
        "priority_workflow_refinement_enabled",
        "understandable_empty_loading_error_states_enabled",
        "permission_aware_actions_preserved",
        "accessible_control_labels_enabled",
        "confirmation_dialog_focus_management_enabled",
        "reduced_motion_support_enabled",
        "desktop_and_tablet_responsive_scope_enabled",
        "canonical_route_families_preserved",
    ]:
        assert metadata[key] is True, key
    assert metadata["backend_contract_changes_enabled"] is False
    assert metadata["new_persistence_enabled"] is False
    assert metadata["readiness_required"] is False

    require_markers(
        "backend/server.py",
        [
            '"aeroassist_product_standards_ux_refinement": True',
            '"aeroassist_product_standards_ux_refinement": aeroassist_product_standards_readiness_metadata()',
        ],
    )


def verify_shared_components() -> None:
    for component, relative_path in COMPONENTS.items():
        read(relative_path)

    representative_usage = {
        "PageHeader": SURFACES["operations"],
        "SectionHeader": SURFACES["tasks"],
        "PrimaryButton": SURFACES["request_list"],
        "SecondaryButton": SURFACES["offer_detail"],
        "DestructiveButton": SURFACES["booking_detail"],
        "EmptyState": SURFACES["request_list"],
        "LoadingState": SURFACES["booking_list"],
        "ErrorState": SURFACES["request_create"],
        "StatusBadge": SURFACES["document_workspaces"],
        "PriorityBadge": SURFACES["tasks"],
        "FilterBar": SURFACES["offer_list"],
        "ConfirmationDialog": SURFACES["operations"],
        "DetailSummary": SURFACES["request_detail"],
        "Timeline": SURFACES["offer_detail"],
        "OperationalAlert": SURFACES["documents"],
        "FormSection": SURFACES["booking_list"],
    }
    for component, relative_path in representative_usage.items():
        if component == "Timeline":
            require_markers(
                relative_path,
                [
                    'components/OperationalCollaborationPanel"',
                    "<OperationalCollaborationPanel",
                ],
            )
            continue
        require_markers(relative_path, [f'components/{component}"', f"<{component}"])


def verify_priority_workflows() -> None:
    expected = {
        SURFACES["onboarding"]: [
            "AeroAssist setup",
            "Progress is saved after each step",
            'aria-live="polite"',
            "Complete pilot workspace",
        ],
        SURFACES["operations"]: [
            "<PageHeader",
            "<ConfirmationDialog",
            "<OperationalAlert",
            "Here\u2019s what needs attention and the next action",
        ],
        SURFACES["request_list"]: [
            "<PageHeader",
            "<FilterBar",
            "<PriorityBadge",
            "No requests match these filters",
        ],
        SURFACES["request_create"]: [
            "<PageHeader",
            "<ErrorState",
            "New travel request",
        ],
        SURFACES["request_detail"]: [
            "<DetailSummary",
            "<OperationalCollaborationPanel",
            "Advanced source details",
            "Prepare trip",
        ],
        SURFACES["offer_list"]: [
            "<PageHeader",
            "<FilterBar",
            "No offers match these filters",
        ],
        SURFACES["offer_detail"]: [
            "<ConfirmationDialog",
            "<OperationalCollaborationPanel",
            "Prepare booking",
        ],
        SURFACES["booking_list"]: [
            "<PageHeader",
            "<FilterBar",
            "<FormSection",
            "<LoadingState",
        ],
        SURFACES["booking_detail"]: [
            "<DetailSummary",
            "<ConfirmationDialog",
            "Add ticket details",
        ],
        SURFACES["passenger_list"]: [
            "<PageHeader",
            "<FilterBar",
            "No passengers match these filters",
        ],
        SURFACES["passenger_detail"]: [
            "<PageHeader",
            "<ConfirmationDialog",
            "Resolve a duplicate passenger",
        ],
        SURFACES["document_workspaces"]: [
            "<PageHeader",
            "<FilterBar",
            "<OperationalAlert",
            "No documents match these filters",
        ],
        SURFACES["documents"]: [
            "<PageHeader",
            "<OperationalAlert",
            "No prepared documents",
        ],
        SURFACES["tasks"]: [
            "<PageHeader",
            "<FilterBar",
            "<PriorityBadge",
            "<StatusBadge",
            "Nothing needs attention here",
        ],
    }
    for relative_path, markers in expected.items():
        require_markers(relative_path, markers)


def verify_travel_first_terminology() -> None:
    prohibited_visible_phrases = {
        "crud",
        "entity",
        "execution mode",
        "identifier",
        "object",
        "payload",
        "record type",
        "schema",
        "state transition",
        "workflow engine",
    }
    retired_surface_phrases = [
        "operational request builder v1",
        "crm foundation",
        "manual offer builder",
        "document foundation",
        "agent work queue",
        "canonical agency queue",
        "source payload / snapshot",
        "provider execution is disabled",
        "source record id",
        "create inline",
    ]
    for relative_path in SURFACES.values():
        content = read(relative_path)
        lowered = content.lower()
        for phrase in retired_surface_phrases:
            assert phrase not in lowered, f"Retired visible phrase {phrase!r} remains in {relative_path}"
        visible_literals = [
            match.group(1)
            for match in re.finditer(r">([^<>{}\\n]+)<", content)
        ]
        visible_literals.extend(
            match.group(1)
            for match in re.finditer(
                r"(?:body|busyLabel|cancelLabel|confirmLabel|description|empty|emptyBody|emptyTitle|eyebrow|label|message|placeholder|title)=[\"']([^\"']+)[\"']",
                content,
            )
        )
        visible_text = " ".join(visible_literals).lower()
        for phrase in prohibited_visible_phrases:
            assert not re.search(rf"\b{re.escape(phrase)}\b", visible_text), (
                f"Prohibited visible terminology {phrase!r} remains in {relative_path}"
            )

    combined = "\n".join(read(relative_path) for relative_path in SURFACES.values())
    for preferred_term in [
        "Passenger",
        "Client",
        "Trip",
        "Request",
        "Offer",
        "Booking",
        "Ticket",
        "Special Service",
        "Task",
        "Follow-up",
        "Current status",
        "Assigned consultant",
        "Next action",
    ]:
        assert preferred_term.lower() in combined.lower(), f"Travel-first term {preferred_term!r} is not represented"


def verify_accessible_controls() -> None:
    require_markers(
        COMPONENTS["PageHeader"],
        ['aria-label="Breadcrumb"', "<h1"],
    )
    require_markers(
        COMPONENTS["LoadingState"],
        ['aria-live="polite"', 'role="status"'],
    )
    require_markers(COMPONENTS["ErrorState"], ['role="alert"'])
    require_markers(COMPONENTS["EmptyState"], ['role="status"'])
    require_markers(
        "frontend/src/components/ActionButton.jsx",
        ["disabled={disabled || busy}", "<span>{busy ? busyLabel : children}</span>"],
    )
    require_markers(
        COMPONENTS["FilterBar"],
        ["aria-label={title}", 'aria-live="polite"', "Clear filters"],
    )
    require_markers(COMPONENTS["StatusBadge"], ['aria-hidden="true"', "productLabel"])
    require_markers(COMPONENTS["PriorityBadge"], ['aria-hidden="true"', "priority</span>"])
    require_markers(
        COMPONENTS["ConfirmationDialog"],
        [
            'role="alertdialog"',
            'aria-modal="true"',
            'event.key === "Escape"',
            "previousFocus?.focus?.()",
            "confirmRef.current?.focus()",
        ],
    )
    require_markers(
        "frontend/src/styles.css",
        [":focus-visible", "@media (prefers-reduced-motion: reduce)"],
    )
    require_markers(
        SURFACES["onboarding"],
        ['aria-label={`${item.day} opening time`', 'aria-label={`${item.day} closing time`'],
    )
    require_markers(
        SURFACES["tasks"],
        ['aria-label={`Select ${item.title}`', 'disabled={!selectedIds.length}'],
    )
    require_markers(
        "frontend/src/components/WorkflowContinuityPanel.jsx",
        [
            "const enabled = action.enabled !== false",
            "disabled={!enabled}",
            "title={!enabled ? action.reason : undefined}",
        ],
    )
    for relative_path in [
        SURFACES["request_detail"],
        SURFACES["booking_detail"],
        SURFACES["passenger_detail"],
        SURFACES["document_workspaces"],
    ]:
        require_markers(relative_path, ["<WorkflowContinuityPanel", "reason:"])


def verify_routes_and_docs() -> None:
    for relative_path in [
        "frontend/src/App.jsx",
        "frontend/src/lib/moduleCatalog.js",
    ]:
        content = read(relative_path)
        assert '"/admin/' not in content and "'/admin/" not in content
        assert '"/agent/' not in content and "'/agent/" not in content

    app_routes = re.findall(
        r'^\s*"(/[^"]*)":\s*[A-Za-z]',
        read("frontend/src/App.jsx"),
        flags=re.MULTILINE,
    )
    duplicate_routes = sorted({route for route in app_routes if app_routes.count(route) > 1})
    assert not duplicate_routes, f"Duplicate frontend routes found: {duplicate_routes}"
    assert any(route == "/agency" for route in app_routes)
    assert any(route.startswith("/platform") for route in app_routes)

    standards = read("docs/product/aeroassist-product-standards.md")
    for section in [
        "## Product Language",
        "## Shared Component Inventory",
        "## 1. Page Structure",
        "## 2. Headers And Breadcrumbs",
        "## 3. Primary And Secondary Actions",
        "## 4. Buttons",
        "## 5. Forms",
        "## 6. Field Labels And Help Text",
        "## 7. Tables And Lists",
        "## 8. Status Indicators",
        "## 9. Empty States",
        "## 10. Loading States",
        "## 11. Error States",
        "## 12. Confirmation Dialogs",
        "## 13. Timelines",
        "## 14. Operational Alerts",
        "## 15. Filters",
        "## 16. Responsive Behaviour",
        "## 17. Accessibility",
        "## 18. Progressive Disclosure",
        "## 19. Destructive Actions",
        "## 20. Customization Principles",
        "## Priority Workflow Application",
        "## Review Checklist",
        "## Known Limitations And Deferred Work",
    ]:
        assert section in standards, f"Missing product standard section {section!r}"

    for relative_path in [
        "README.md",
        "BUILD_PHASES.md",
        "docs/architecture/canonical-route-policy.md",
        "docs/architecture/current-model-inventory.md",
    ]:
        require_markers(relative_path, [PHASE_LABEL])


def main() -> None:
    verify_phase_and_readiness()
    verify_shared_components()
    verify_priority_workflows()
    verify_travel_first_terminology()
    verify_accessible_controls()
    verify_routes_and_docs()
    print("AeroAssist product standards and UX refinement smoke passed.")


if __name__ == "__main__":
    main()
