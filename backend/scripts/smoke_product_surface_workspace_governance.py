#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, value: str) -> None:
    if value not in read(path):
        raise AssertionError(f"{path} missing product-surface contract: {value}")


def main() -> None:
    catalog = read("frontend/src/lib/moduleCatalog.js")
    layout = read("frontend/src/layouts/AgencyLayout.jsx")
    offer_workspace = read("frontend/src/pages/agency/OfferWorkspaceDetailPage.jsx")
    app = read("frontend/src/App.jsx")
    service = read("backend/services/offer_delivery_client_interaction_service.py")

    expected_tools = [
        "Itinerary Builder",
        "Itinerary Options & Fare Brands",
        "Offer Comparison",
        "Offer Delivery",
    ]
    for label in expected_tools:
        matching_lines = [line for line in catalog.splitlines() if f'label: "{label}"' in line]
        if len(matching_lines) != 1:
            raise AssertionError(f"Expected one Agency module record for {label}, found {len(matching_lines)}")
        if 'surface_type: "contextual_tool"' not in matching_lines[0] or 'navigation_visibility: "contextual"' not in matching_lines[0]:
            raise AssertionError(f"{label} is not classified as a hidden contextual tool.")
    for forbidden_label in [
        'label: "Journey Authoring"',
        'label: "Journey Option Composition"',
        'label: "Journey Comparison Presentation"',
        'label: "Journey Offer Delivery"',
    ]:
        agency_catalog = catalog.split("export const agencyModuleGroups", 1)[-1]
        if forbidden_label in agency_catalog:
            raise AssertionError(f"Forbidden technical Agency label remains: {forbidden_label}")

    if 'item.navigation_visibility !== "contextual"' not in layout:
        raise AssertionError("Agency navigation does not hide contextual tools.")
    for value in ["OfferDeliveryPanel", "Delivery & Responses", "Client & Passengers", "Airline Suitability", "Client Preview"]:
        if value not in offer_workspace:
            raise AssertionError(f"Canonical Offer Workspace lifecycle is missing: {value}")
    if 'href: "/agency/offers"' not in catalog or 'surface_type: "primary_workspace"' not in catalog:
        raise AssertionError("Canonical Offer Workspace is not classified as a primary workspace.")
    if '"/portal/travel-options"' not in app or '"/platform/offer-delivery-diagnostics"' not in app:
        raise AssertionError("Client Portal or Platform diagnostics surface was removed.")
    if '"/agency/offer-deliveries"' not in app or "Offer context required" not in read("frontend/src/components/offers/OfferDeliveryPanel.jsx"):
        raise AssertionError("Guarded Offer Delivery compatibility route is unavailable.")
    if 'collection("offer_workspaces")' not in service or 'collection("journey_presentation_snapshots")' not in service:
        raise AssertionError("Offer Delivery is disconnected from canonical Offer or Phase 56.3 snapshot ownership.")

    ordinary_surfaces = [
        "frontend/src/components/offers/OfferDeliveryPanel.jsx",
        "frontend/src/pages/agency/OfferDeliveryContextPage.jsx",
        "frontend/src/pages/portal/PortalOfferDeliveriesPage.jsx",
        "frontend/src/pages/portal/PortalOfferDeliveryDetailPage.jsx",
    ]
    for path in ordinary_surfaces:
        content = read(path)
        if "Journey Offer Delivery" in content:
            raise AssertionError(f"Forbidden user-facing term remains in {path}")

    router_sources = "\n".join(read(path) for path in [
        "backend/routers/agency_offer_deliveries.py",
        "backend/routers/portal_offer_deliveries.py",
        "backend/routers/platform_offer_delivery_diagnostics.py",
    ])
    if "/api/public" in router_sources:
        raise AssertionError("Offer Delivery introduced an anonymous public API route.")

    require("docs/architecture/product-surface-workspace-governance.md", "Product Surface Review Gate")
    require("docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md", "Product Surface Review Gate")
    require("docs/architecture/canonical-route-policy.md", "Product Surface Review Gate")
    print("Product surface and workspace governance smoke passed.")


if __name__ == "__main__":
    main()
