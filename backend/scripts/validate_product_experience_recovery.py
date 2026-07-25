#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE
from services.product_experience_recovery_service import (
    PHASE_LABEL,
    product_experience_recovery_readiness_metadata,
)


PLATFORM_AREAS = [
    "Overview",
    "Reference Data",
    "Airline Knowledge",
    "Policies",
    "Agencies",
    "Users",
    "Monitoring",
    "Audit",
    "Settings",
    "Advanced",
]
PLATFORM_PRIMARY_ROUTES = [
    "/platform",
    "/platform/reference",
    "/platform/airlines",
    "/platform/visual-policy-editor",
    "/platform/agencies",
    "/platform/users",
    "/platform/monitoring",
    "/platform/audit",
    "/platform/settings",
]
AGENCY_AREAS = [
    "Dashboard",
    "Requests",
    "Offers",
    "Trips",
    "Bookings",
    "Tickets & EMDs",
    "Finance",
    "Clients",
    "Passengers",
    "Communications",
    "Documents",
    "Operations",
    "Reports",
    "Settings",
    "Advanced",
]
AGENCY_PRIMARY_ROUTES = [
    "/agency",
    "/agency/requests",
    "/agency/offers",
    "/agency/trips",
    "/agency/bookings",
    "/agency/tickets-emds",
    "/agency/finance",
    "/agency/clients",
    "/agency/passengers",
    "/agency/communications",
    "/agency/document-workspaces",
    "/agency/work-queue",
    "/agency/reports",
    "/agency/settings",
]
PRODUCT_METADATA_FIELDS = {
    "primary_area",
    "user_purpose",
    "audience",
    "navigation_priority",
    "advanced_only",
    "hidden_from_primary_navigation",
    "preferred_label",
    "preferred_description",
}


def read(relative_path: str) -> str:
    path = ROOT / relative_path
    assert path.is_file(), f"Missing {relative_path}"
    return path.read_text(encoding="utf-8")


def require(relative_path: str, markers: list[str]) -> None:
    source = read(relative_path)
    for marker in markers:
        assert marker in source, f"{relative_path} missing {marker!r}"


def catalogue_snapshot() -> dict:
    script = """
import {
  agencyProductNavigation,
  platformProductNavigation,
  productNavigationForRole,
} from "./frontend/src/lib/moduleCatalog.js";
const compact = (areas) => areas.map((area) => ({
  title: area.title,
  advanced_only: area.advanced_only,
  items: area.items.map((item) => ({
    href: item.href,
    label: item.preferred_label,
    description: item.preferred_description,
    metadata_fields: Object.keys(item),
    advanced_only: item.advanced_only,
    hidden_from_primary_navigation: item.hidden_from_primary_navigation,
  })),
}));
console.log(JSON.stringify({
  platform: compact(platformProductNavigation),
  agency: compact(agencyProductNavigation),
  platform_support: compact(productNavigationForRole(platformProductNavigation, "platform_support")),
  platform_knowledge_editor: compact(productNavigationForRole(platformProductNavigation, "platform_knowledge_editor")),
  agency_agent: compact(productNavigationForRole(agencyProductNavigation, "agency_agent")),
  agency_readonly: compact(productNavigationForRole(agencyProductNavigation, "agency_readonly")),
  agency_accountant: compact(productNavigationForRole(agencyProductNavigation, "agency_accountant")),
}));
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def primary_routes(areas: list[dict]) -> list[str]:
    return [item["href"] for area in areas[:-1] for item in area["items"]]


def verify_navigation() -> None:
    snapshot = catalogue_snapshot()
    platform = snapshot["platform"]
    agency = snapshot["agency"]
    assert [area["title"] for area in platform] == PLATFORM_AREAS
    assert [area["title"] for area in agency] == AGENCY_AREAS
    assert primary_routes(platform) == PLATFORM_PRIMARY_ROUTES
    assert primary_routes(agency) == AGENCY_PRIMARY_ROUTES
    assert all(len(area["items"]) == 1 for area in [*platform[:-1], *agency[:-1]])

    for area in [*platform, *agency]:
        for item in area["items"]:
            assert PRODUCT_METADATA_FIELDS.issubset(item["metadata_fields"]), (
                f"Product metadata incomplete for {item['href']}"
            )

    for navigation in [platform, agency]:
        advanced = navigation[-1]
        assert advanced["title"] == "Advanced"
        assert advanced["advanced_only"] is True
        assert advanced["items"], "Advanced navigation must retain specialist routes"
        assert all(item["advanced_only"] and item["hidden_from_primary_navigation"] for item in advanced["items"])

    prohibited_primary_terms = {
        "metadata only",
        "canonical",
        "entity id",
        "state map",
        "foundation",
        "execution disabled",
        "architecture only",
        "workspace v2",
        "lifecycle engine",
    }
    for navigation in [platform, agency]:
        primary_items = [item for area in navigation[:-1] for item in area["items"]]
        primary_hrefs = [item["href"] for item in primary_items]
        assert len(primary_hrefs) == len(set(primary_hrefs)), "Primary navigation contains a duplicate route"
        for item in primary_items:
            product_text = f"{item['label']} {item['description']}".lower()
            for term in prohibited_primary_terms:
                assert not re.search(rf"\b{re.escape(term)}\b", product_text), (
                    f"Primary navigation exposes technical term {term!r}: {item['href']}"
                )

    assert [area["title"] for area in snapshot["platform_support"]] == [
        "Overview",
        "Reference Data",
        "Airline Knowledge",
        "Agencies",
        "Monitoring",
    ]
    assert [area["title"] for area in snapshot["platform_knowledge_editor"]] == [
        "Reference Data",
        "Airline Knowledge",
        "Policies",
    ]
    for role_view in ["agency_agent", "agency_readonly"]:
        titles = [area["title"] for area in snapshot[role_view]]
        assert "Settings" not in titles
        assert "Advanced" not in titles
    assert "Reports" in [area["title"] for area in snapshot["agency_accountant"]]


def verify_shells_routes_and_performance() -> None:
    require(
        "frontend/src/layouts/PlatformLayout.jsx",
        [
            "platformProductNavigation",
            "productNavigationForRole",
            "ProductQuickSearch",
            "aa-advanced-navigation",
            "aa-skip-link",
            'id="main-content"',
            'aria-current={active ? "page" : undefined}',
        ],
    )
    require(
        "frontend/src/layouts/AgencyLayout.jsx",
        [
            "agencyProductNavigation",
            "productNavigationForRole",
            "agencyNavigationRole",
            "ProductQuickSearch",
            "WorkflowQuickActions",
            "aa-advanced-navigation",
            "aa-skip-link",
            'id="main-content"',
            'aria-current={active ? "page" : undefined}',
        ],
    )
    for relative_path in [
        "frontend/src/layouts/PlatformLayout.jsx",
        "frontend/src/layouts/AgencyLayout.jsx",
    ]:
        source = read(relative_path)
        advanced_details = source[source.index("aa-advanced-navigation") - 80 :]
        assert "<details" in advanced_details
        assert "<details open" not in advanced_details
        assert 'aria-label="Open navigation"' in source
        assert "max-w-[1440px]" not in source
        assert "max-w-7xl" not in source

    app = read("frontend/src/App.jsx")
    assert '"/platform": PlatformDashboardPage' in app
    assert '"/agency": OperationsCommandCenterPage' in app
    for route in [
        *PLATFORM_PRIMARY_ROUTES,
        *AGENCY_PRIMARY_ROUTES,
        "/platform/pilot-operations",
        "/agency/operations-command-center",
        "/agency/operational-workflows",
        "/agency/workflow-maturity",
    ]:
        assert f'"{route}"' in app
    for rejected_root in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
        assert rejected_root not in app

    lazy_imports = re.findall(r'^const \w+ = lazy\(\(\) => import\("\./pages/', app, flags=re.MULTILINE)
    assert len(lazy_imports) >= 300, f"Expected route-level lazy loading, found {len(lazy_imports)} page imports"
    assert not re.search(r'^import .+ from "\./pages/', app, flags=re.MULTILINE)
    assert "<Suspense" in app
    assert 'LoadingState label="Opening page"' in app

    require(
        "frontend/src/lib/agency.js",
        [
            'window.location.pathname !== "/agency/onboarding"',
            "onboarding.required",
            "current_membership",
        ],
    )
    require(
        "frontend/src/components/ProductQuickSearch.jsx",
        ['aria-haspopup="dialog"', 'event.key === "Escape"', "No permitted page matches"],
    )
    require(
        "frontend/src/components/WorkflowQuickActions.jsx",
        [
            "hasPermission(action.permission)",
            'permission: "edit_requests"',
            'permission: "edit_offers"',
            'permission: "edit_documents"',
        ],
    )


def verify_dashboards_and_portals() -> None:
    platform = read("frontend/src/pages/platform/PlatformDashboardPage.jsx")
    for marker in [
        "Attention required",
        "Agency health",
        "Reference updates",
        "Knowledge updates",
        "Operational alerts",
        "Commercial Pilot",
        "System health",
        "Recent activity",
        "Quick actions",
        'variant="wide"',
    ]:
        assert marker in platform
    assert "platformModuleGroups" not in platform
    assert "Object.entries(summary?.counts" not in platform

    agency = read("frontend/src/pages/agency/OperationsCommandCenterPage.jsx")
    for marker in [
        "Today’s work",
        "Action required",
        "Deadlines",
        "Bookings needing action",
        "Pending offers",
        "Pending approvals",
        "Recent communications",
        "Financial summary",
        "Notifications",
        'variant="wide"',
    ]:
        assert marker in agency

    portal_layout = read("frontend/src/layouts/ClientPortalLayout.jsx")
    client_navigation = portal_layout.split("const clientLinks = [", 1)[1].split("const passengerLinks = [", 1)[0]
    ordered_client_labels = [
        "Dashboard",
        "Trips",
        "Offers",
        "Requests",
        "Documents",
        "Messages",
        "Payments",
        "Profile",
    ]
    positions = [client_navigation.index(f'"{label}"') for label in ordered_client_labels]
    assert positions == sorted(positions)
    assert "subjectType === \"passenger\" ? passengerLinks : clientLinks" in portal_layout
    for marker in ["Upcoming trips", "Pending offers", "Action required", "Documents", "Messages", "Outstanding payments"]:
        assert marker in read("frontend/src/pages/portal/PortalDashboardPage.jsx")


def verify_workflow_and_product_language() -> None:
    workflow = read("frontend/src/components/WorkflowContinuityPanel.jsx")
    for marker in [
        "Current stage",
        "Completed",
        "Next action",
        "Deadline",
        "Warning",
        "Blocked",
        "Timeline",
        "relatedRecords",
        "previous",
        "next",
    ]:
        assert marker in workflow

    covered_pages = [
        "AfterSalesPage.jsx",
        "BookingHandoffsPage.jsx",
        "BookingWorkspaceDetailPage.jsx",
        "ClientDetailPage.jsx",
        "DocumentWorkspacesPage.jsx",
        "EmdDetailPage.jsx",
        "InvoiceDetailPage.jsx",
        "OfferBuilderPage.jsx",
        "OfferWorkspaceDetailPage.jsx",
        "PassengerDetailPage.jsx",
        "PassengerServicesPage.jsx",
        "RequestDetailPage.jsx",
        "RequestTripConversionPage.jsx",
        "TicketDetailPage.jsx",
        "TripDetailPage.jsx",
    ]
    for filename in covered_pages:
        assert "WorkflowContinuityPanel" in read(f"frontend/src/pages/agency/{filename}")

    operational_workflows = read("frontend/src/pages/agency/OperationalWorkflowsPage.jsx")
    for marker in [
        "No workflow diagnostics are available for this agency yet.",
        "Advanced system details",
        "Related item type",
        "Related item reference",
    ]:
        assert marker in operational_workflows
    assert '<details className="rounded-md border border-slate-200 bg-white p-4" open>' not in operational_workflows

    for relative_path in [
        "frontend/src/pages/agency/ClientMasterPage.jsx",
        "frontend/src/pages/agency/PassengerMasterPage.jsx",
        "frontend/src/pages/agency/OfferWorkspacesPage.jsx",
        "frontend/src/pages/agency/TicketsEmdsPage.jsx",
        "frontend/src/pages/portal/PortalDashboardPage.jsx",
    ]:
        source = read(relative_path)
        for phrase in [
            "Metadata only",
            "Client Master Records",
            "Passenger Master Records",
            "Offer Workspaces",
            "Internal mirrors only",
            "workspace v2",
        ]:
            assert phrase not in source, f"{relative_path} exposes {phrase!r}"

    master_list = read("frontend/src/components/ClientPassengerMasterRecordList.jsx")
    assert "JSON.stringify(value" not in master_list
    assert "No details recorded." in master_list


def verify_design_system_and_accessibility() -> None:
    component = read("frontend/src/components/WorkspacePage.jsx")
    styles = read("frontend/src/styles.css")
    for variant in ["standard", "wide", "focused", "reading"]:
        assert f"{variant}:" in component
        assert f".aa-workspace-{variant}" in styles
    for marker in [".aa-skip-link", ":focus-visible", "prefers-reduced-motion", ".aa-sticky-actions"]:
        assert marker in styles

    require(
        "frontend/src/components/ProductTable.jsx",
        [
            "<caption",
            'scope="col"',
            "overflow-x-auto",
            "EmptyState",
            "aria-sort",
            "Select visible rows",
            "bulkActions",
            "Previous page",
            "Next page",
        ],
    )
    require(
        "frontend/src/components/EmptyState.jsx",
        ["title", "body"],
    )
    require(
        "frontend/src/components/LoadingState.jsx",
        ["label"],
    )


def verify_page_inventory() -> None:
    result = subprocess.run(
        ["node", "frontend/scripts/audit-product-pages.mjs", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    inventory_path = ROOT / "docs/architecture/product-page-inventory.csv"
    with inventory_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 311
    assert all((ROOT / row["source_file"]).is_file() for row in rows)
    assert {row["audience"] for row in rows} == {
        "agency",
        "authentication",
        "platform",
        "client_or_passenger_portal",
        "public",
    }
    assert {row["navigation_placement"] for row in rows} == {
        "primary",
        "contextual",
        "advanced",
        "orphan",
    }
    orphans = {
        Path(row["source_file"]).name
        for row in rows
        if row["route_status"] == "orphan"
    }
    assert orphans == {
        "AgencyDashboardPage.jsx",
        "BookingCreatePage.jsx",
        "ClientsPage.jsx",
        "OfferDetailPage.jsx",
        "OffersPage.jsx",
        "PassengersPage.jsx",
        "PortalOffersPage.jsx",
    }
    for row in rows:
        if row["navigation_placement"] == "primary" and row["audience"] in {
            "agency",
            "client_or_passenger_portal",
        }:
            assert row["visible_technical_indicators"] == "none", (
                f"Primary product page exposes technical language: {row['source_file']}"
            )


def verify_phase_and_safety() -> None:
    assert CURRENT_BUILD_PHASE == PHASE_LABEL
    metadata = product_experience_recovery_readiness_metadata()
    assert metadata["platform_primary_area_count"] == 9
    assert metadata["agency_primary_area_count"] == 14
    for key in [
        "task_based_platform_navigation_enabled",
        "workflow_ordered_agency_navigation_enabled",
        "advanced_navigation_collapsed_by_default",
        "module_catalogue_remains_source_of_truth",
        "permission_aware_navigation_enabled",
        "practical_platform_overview_enabled",
        "agency_operations_home_preserved",
        "task_dashboard_summaries_enabled",
        "workflow_guidance_banner_enabled",
        "quick_page_search_enabled",
        "permission_aware_quick_actions_enabled",
        "route_level_lazy_loading_enabled",
        "portal_task_navigation_enabled",
        "onboarding_redirect_preserved",
        "full_width_workspace_shell_enabled",
        "workspace_layout_primitives_enabled",
        "optional_diagnostics_empty_state_enabled",
        "raw_state_details_collapsed_by_default",
        "canonical_routes_preserved",
        "execution_boundaries_unchanged",
    ]:
        assert metadata[key] is True, key
    assert metadata["new_persistence_enabled"] is False
    assert metadata["readiness_required"] is False
    require(
        "backend/server.py",
        [
            '"product_experience_recovery": True',
            '"product_experience_recovery": product_experience_recovery_readiness_metadata()',
        ],
    )
    assert not (BACKEND / "routers/platform_product_experience_recovery.py").exists()
    assert not (BACKEND / "routers/agency_product_experience_recovery.py").exists()


def verify_documentation() -> None:
    for relative_path in [
        "docs/product/platform-information-architecture.md",
        "docs/product/agency-information-architecture.md",
        "docs/product/navigation-and-layout-standards.md",
    ]:
        require(relative_path, ["Phase 59.0", "Before", "After", "Advanced"])
    require(
        "docs/architecture/product-navigation-contract.md",
        ["Platform Navigation", "Agency Navigation", "Portal Navigation", "311 page files"],
    )
    require(
        "docs/architecture/dashboard-contract.md",
        ["Agency Dashboard", "Platform Dashboard", "Portal Dashboards"],
    )
    require(
        "docs/architecture/design-system-contract.md",
        ["Product Primitives", "Responsive Rules", "Accessibility Rules", "route-level lazy loaded"],
    )
    require(
        "docs/architecture/workflow-banner-contract.md",
        ["Required Content", "Detail Page Order", "Safety Rules"],
    )
    require("README.md", ["P1 Product Recovery 10", "Product Navigation Contract"])
    require("BUILD_PHASES.md", ["P1 Product Recovery 10", "phase_59_0_product_experience_recovery"])
    require(
        "docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md",
        ["Product Experience Contract", "Product Navigation Contract"],
    )
    require("docs/architecture/canonical-route-policy.md", ["P1 Product Recovery 10", "/platform/monitoring"])
    require("docs/architecture/current-model-inventory.md", ["P1 Product Recovery 10", "Product Page Inventory"])


def main() -> int:
    verify_navigation()
    verify_shells_routes_and_performance()
    verify_dashboards_and_portals()
    verify_workflow_and_product_language()
    verify_design_system_and_accessibility()
    verify_page_inventory()
    verify_phase_and_safety()
    verify_documentation()
    print("Phase 59.0 product experience UX governance validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
