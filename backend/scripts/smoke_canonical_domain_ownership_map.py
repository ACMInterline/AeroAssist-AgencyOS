#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE  # noqa: E402
from canonical_domain_ownership import (  # noqa: E402
    CANONICAL_DOMAIN_OWNERSHIP_REGISTRY,
    DOMAIN_OWNERSHIP_BY_KEY,
    PRODUCT_KERNEL_LIFECYCLE,
    REQUIRED_DOMAIN_KEYS,
    TENANT_BOUNDARY_DECISION,
)
from phase_assertions import assert_application_phase_at_least  # noqa: E402
from scripts.validate_canonical_domain_ownership import validate_registry  # noqa: E402


MINIMUM_PHASE = "phase_59_0_product_experience_recovery"
EXPECTED_DECISIONS = {
    "airline_knowledge",
    "policy",
    "pricing",
}
EXPECTED_TARGETS = {
    "authentication_identity": "AuthIdentity",
    "platform_user": "PlatformUser",
    "agency_membership": "AgencyStaffMembership",
    "client_portal_identity": "PortalAccessMapping",
    "passenger_portal_identity": "PortalAccessMapping",
    "agency_tenant_workspace": "Agency",
    "crm_client": "ClientProfile",
    "passenger": "PassengerProfile",
    "client_passenger_relationship": "ClientPassengerRelationship",
    "request": "TravelRequest",
    "request_passenger": "RequestPassenger (child of TravelRequest)",
    "request_segment": "RequestSegment (child of TravelRequest)",
    "passenger_service": "PassengerServiceRequest",
    "pet": "RequestPet (child of TravelRequest)",
    "special_item": "RequestSpecialItem (child of TravelRequest)",
    "offer": "OfferWorkspace",
    "offer_option": "OfferOption (child of OfferWorkspace)",
    "offer_acceptance": "OfferAcceptance",
    "accepted_offer_snapshot": "TripAcceptedOfferSnapshot (creation only)",
    "trip": "TripDossier",
    "booking_pnr": "BookingRecord",
    "booking_handoff": "OfferBookingHandoff",
    "ticket": "TicketRecord",
    "ticket_coupon": "TicketCoupon (child of TicketRecord)",
    "emd": "EMDRecord",
    "emd_coupon": "EmdCoupon (child of EMDRecord)",
    "ssr_osi": "SsrOsiWorkspace",
    "invoice": "Invoice",
    "invoice_line": "InvoiceLineItem (child of Invoice)",
    "payment": "PaymentRecord",
    "refund_exchange": "AfterSalesCase",
    "document": "DocumentWorkspace",
    "task_work_item": "OperationalWorkItem",
    "timeline": "OperationalTimeline",
    "audit_event": "AuditEvent",
    "reference_data": "GlobalReferenceRecord",
}


def require_text(path: str, values: tuple[str, ...]) -> None:
    absolute = ROOT / path
    if not absolute.is_file():
        raise AssertionError(f"Required ownership artifact is missing: {path}")
    text = absolute.read_text(encoding="utf-8")
    missing = [value for value in values if value not in text]
    if missing:
        raise AssertionError(f"{path} is missing ownership markers: {missing}")


def main() -> int:
    assert_application_phase_at_least(
        CURRENT_BUILD_PHASE,
        MINIMUM_PHASE,
        source="canonical build phase",
    )
    summary, errors = validate_registry()
    if errors:
        raise AssertionError("Canonical ownership validation failed: " + "; ".join(errors))
    if tuple(record["domain_key"] for record in CANONICAL_DOMAIN_OWNERSHIP_REGISTRY) != REQUIRED_DOMAIN_KEYS:
        raise AssertionError("Required domain order changed.")
    actual_decisions = {
        record["domain_key"]
        for record in CANONICAL_DOMAIN_OWNERSHIP_REGISTRY
        if record["decision_status"] == "decision_required"
    }
    if actual_decisions != EXPECTED_DECISIONS:
        raise AssertionError(f"Decision-required set changed: {sorted(actual_decisions)}")
    for key, target in EXPECTED_TARGETS.items():
        if DOMAIN_OWNERSHIP_BY_KEY[key]["target_write_owner"] != target:
            raise AssertionError(f"{key} target owner changed.")
    if TENANT_BOUNDARY_DECISION["decision"] != "agency_id_is_canonical_workspace_boundary":
        raise AssertionError("agency_id is no longer the explicit tenant boundary.")
    if TENANT_BOUNDARY_DECISION["migration_required"]:
        raise AssertionError("A workspace_id tenant migration was introduced.")

    snapshot = DOMAIN_OWNERSHIP_BY_KEY["accepted_offer_snapshot"]
    if snapshot["artifacts"][0]["classification"] != "immutable_snapshot":
        raise AssertionError("Accepted Offer Snapshot lost immutable classification.")
    if DOMAIN_OWNERSHIP_BY_KEY["passenger"]["canonical_model"] != "PassengerProfile":
        raise AssertionError("P0 passenger identity owner regressed.")
    if "ClientMasterRecord" not in DOMAIN_OWNERSHIP_BY_KEY["crm_client"]["compatibility_writers"]:
        raise AssertionError("Client Master compatibility writer is no longer visible.")
    if "OfferWorkspaceV2" not in DOMAIN_OWNERSHIP_BY_KEY["offer"]["compatibility_writers"]:
        raise AssertionError("Duplicate Offer workspace is no longer visible.")
    if (
        DOMAIN_OWNERSHIP_BY_KEY["communication"]["canonical_model"]
        != "CommunicationThread / CommunicationMessage"
    ):
        raise AssertionError("Canonical communication ownership regressed.")
    if (
        DOMAIN_OWNERSHIP_BY_KEY["timeline"]["canonical_model"]
        != "OperationalTimeline"
    ):
        raise AssertionError("Canonical operational timeline ownership regressed.")
    if not any(item["stage"] == "portal_visibility" for item in PRODUCT_KERNEL_LIFECYCLE):
        raise AssertionError("Lifecycle continuity does not reach the portal boundary.")
    if summary["kernel_status"] != "migration_required":
        raise AssertionError("Focused smoke must not falsify canonical migration readiness.")

    require_text(
        "docs/architecture/canonical-domain-ownership-map.md",
        (
            "# Canonical Domain Ownership Map",
            "agency_id is the canonical workspace boundary",
            "## 40. Pricing",
        ),
    )
    ownership_map = (
        ROOT / "docs/architecture/canonical-domain-ownership-map.md"
    ).read_text(encoding="utf-8")
    if sum(
        1
        for line in ownership_map.splitlines()
        if line.startswith("### ") and line[4:5].isdigit()
    ) != 40:
        raise AssertionError("Ownership documentation does not contain one table section per domain.")
    require_text(
        "docs/architecture/canonical-domain-migration-register.md",
        (
            "# Canonical Domain Migration Register",
            "## Recommended Repair Order",
            "## Exit Criteria",
        ),
    )
    require_text("README.md", ("Canonical Domain Ownership Map",))
    require_text("BUILD_PHASES.md", ("P1 Product Kernel Repair 2",))

    for runtime_file in ("backend/server.py", "backend/database.py", "backend/persistence_query.py"):
        if "canonical_domain_ownership" in (ROOT / runtime_file).read_text(encoding="utf-8"):
            raise AssertionError(f"Governance registry was introduced into runtime code: {runtime_file}")

    print(
        "Canonical domain ownership map smoke passed: "
        f"{summary['registered_domain_count']} domains, "
        f"{summary['decision_required_count']} decision-required, "
        f"{summary['migration_required_count']} migration-required."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
