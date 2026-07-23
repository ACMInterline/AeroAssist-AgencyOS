#!/usr/bin/env python3
from __future__ import annotations

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
    "Agencies",
    "Airline Knowledge",
    "Services & Pricing",
    "Product Configuration",
    "Pilot & Support",
    "System Health",
    "Advanced",
]
AGENCY_AREAS = [
    "Operations",
    "Requests",
    "Clients & Passengers",
    "Trips",
    "Offers",
    "Bookings",
    "Tickets & EMDs",
    "Special Services",
    "Documents",
    "Tasks & Follow-ups",
    "Reports",
    "Settings",
    "Advanced",
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


def verify_navigation() -> None:
    snapshot = catalogue_snapshot()
    platform = snapshot["platform"]
    agency = snapshot["agency"]
    assert [area["title"] for area in platform] == PLATFORM_AREAS
    assert len(platform) <= 8
    assert [area["title"] for area in agency] == AGENCY_AREAS

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
        "entity",
        "entity id",
        "state map",
        "foundation",
        "execution disabled",
        "read-only diagnostics",
        "architecture only",
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

    platform_primary = {item["href"] for area in platform[:-1] for item in area["items"]}
    agency_primary = {item["href"] for area in agency[:-1] for item in area["items"]}
    for technical_route in [
        "/platform/operational-workflows",
        "/platform/workflow-maturity",
        "/platform/feature-bundle-rollout-plans",
        "/platform/blueprint",
    ]:
        assert technical_route not in platform_primary
    for technical_route in [
        "/agency/operational-workflows",
        "/agency/workflow-maturity",
        "/agency/rollout-plans",
        "/agency/task-automation",
    ]:
        assert technical_route not in agency_primary

    assert [area["title"] for area in snapshot["platform_support"]] == [
        "Overview",
        "Agencies",
        "Airline Knowledge",
        "Pilot & Support",
        "System Health",
    ]
    assert "Settings" not in [area["title"] for area in snapshot["agency_agent"]]
    assert "Advanced" not in [area["title"] for area in snapshot["agency_agent"]]
    assert "Settings" not in [area["title"] for area in snapshot["agency_readonly"]]
    assert "Reports" in [area["title"] for area in snapshot["agency_accountant"]]


def verify_shells_and_routes() -> None:
    require(
        "frontend/src/layouts/PlatformLayout.jsx",
        [
            "platformProductNavigation",
            "productNavigationForRole",
            "aa-advanced-navigation",
            "<details",
            "Collapse navigation",
        ],
    )
    require(
        "frontend/src/layouts/AgencyLayout.jsx",
        [
            "agencyProductNavigation",
            "productNavigationForRole",
            "agencyNavigationRole",
            "aa-advanced-navigation",
            "<details",
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

    require(
        "frontend/src/layouts/PlatformLayout.jsx",
        [
            'aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}',
            'aria-current={active ? "page" : undefined}',
        ],
    )
    require(
        "frontend/src/layouts/AgencyLayout.jsx",
        ['aria-current={active ? "page" : undefined}'],
    )

    app = read("frontend/src/App.jsx")
    assert '"/platform": PlatformDashboardPage' in app
    assert '"/agency": OperationsCommandCenterPage' in app
    for route in [
        "/platform/operational-workflows",
        "/platform/feature-bundle-rollout-plans",
        "/agency/operational-workflows",
        "/agency/workflow-maturity",
        "/agency/rollout-plans",
    ]:
        assert f'"{route}"' in app
    for rejected_root in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
        assert rejected_root not in app

    require(
        "frontend/src/lib/agency.js",
        [
            'window.location.pathname !== "/agency/onboarding"',
            "onboarding.required",
            "current_membership",
        ],
    )


def verify_overview_and_recovery() -> None:
    dashboard = read("frontend/src/pages/platform/PlatformDashboardPage.jsx")
    for marker in [
        "Attention required",
        "Agencies",
        "Knowledge readiness",
        "Pilot status",
        "System health",
        "Recent activity",
        "Quick actions",
        'variant="wide"',
    ]:
        assert marker in dashboard
    assert "platformModuleGroups" not in dashboard
    assert "Object.entries(summary?.counts" not in dashboard

    workflow = read("frontend/src/pages/agency/OperationalWorkflowsPage.jsx")
    for marker in [
        "Operational workflow instance metadata not found.",
        "No workflow diagnostics are available for this agency yet.",
        "These system details appear after operational workflows have been recorded.",
        "Advanced system details",
        "Related item type",
        "Related item reference",
    ]:
        assert marker in workflow
    assert '<details className="rounded-md border border-slate-200 bg-white p-4">' in workflow
    assert '<details className="rounded-md border border-slate-200 bg-white p-4" open>' not in workflow


def verify_layout_primitives() -> None:
    component = read("frontend/src/components/WorkspacePage.jsx")
    styles = read("frontend/src/styles.css")
    for variant in ["standard", "wide", "focused", "reading"]:
        assert f"{variant}:" in component
        assert f".aa-workspace-{variant}" in styles
    require(
        "frontend/src/pages/agency/OperationsCommandCenterPage.jsx",
        ['components/WorkspacePage"', 'variant="wide"'],
    )
    for layout in ["frontend/src/layouts/PlatformLayout.jsx", "frontend/src/layouts/AgencyLayout.jsx"]:
        assert "max-w-[1440px]" not in read(layout)
        assert "max-w-7xl" not in read(layout)


def verify_phase_and_safety() -> None:
    assert CURRENT_BUILD_PHASE == PHASE_LABEL
    metadata = product_experience_recovery_readiness_metadata()
    assert metadata["platform_primary_area_count"] == 8
    assert metadata["agency_primary_area_count"] == 13
    for key in [
        "task_based_platform_navigation_enabled",
        "workflow_ordered_agency_navigation_enabled",
        "advanced_navigation_collapsed_by_default",
        "module_catalogue_remains_source_of_truth",
        "permission_aware_navigation_enabled",
        "practical_platform_overview_enabled",
        "agency_operations_home_preserved",
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
    require("README.md", ["Phase 59.0", "product experience recovery"])
    require("BUILD_PHASES.md", ["Phase 59.0", "phase_59_0_product_experience_recovery"])
    require("docs/architecture/canonical-route-policy.md", ["Phase 59.0", "Task-based navigation"])
    require("docs/architecture/current-model-inventory.md", ["Phase 59.0", "no new persistence"])


def main() -> int:
    verify_navigation()
    verify_shells_and_routes()
    verify_overview_and_recovery()
    verify_layout_primitives()
    verify_phase_and_safety()
    verify_documentation()
    print("Phase 59.0 product experience UX governance validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
