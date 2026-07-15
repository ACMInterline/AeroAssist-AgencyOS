from __future__ import annotations

from typing import Any

from database import Database
from models import CapabilityCatalogEntry
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService


PHASE_LABEL = "phase_56_1_journey_segment_authoring_intelligent_import_workspace_foundation"

CAPABILITY_COLLECTION = "capability_catalog"

DEFAULT_CAPABILITY_CATALOG: list[dict[str, Any]] = [
    {
        "code": "dashboard",
        "name": "Dashboard",
        "description": "Agency workspace home, status cards, and operational entry points.",
        "category": "core",
        "module": "daily_work",
        "required_feature_flags": ["dashboard"],
        "required_bundles": ["core_agency"],
        "ui_routes": ["/agency"],
        "documentation_links": ["docs/architecture/platform-agency-ux-consolidation.md"],
        "introduced_phase": "phase_39_4_platform_agency_ux_consolidation",
    },
    {
        "code": "requests",
        "name": "Requests",
        "description": "Agency travel request intake and request workspace metadata.",
        "category": "operations",
        "module": "requests_trips",
        "required_feature_flags": ["requests"],
        "required_bundles": ["core_agency"],
        "dependencies": ["clients", "passengers"],
        "ui_routes": ["/agency/requests", "/agency/requests/new"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_1_core_requests",
    },
    {
        "code": "request_intakes",
        "name": "Intakes",
        "description": "Public and portal request intake review metadata.",
        "category": "operations",
        "module": "daily_work",
        "required_feature_flags": ["request_intakes"],
        "recommended_bundles": ["core_agency"],
        "ui_routes": ["/agency/request-intakes"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_8_request_intake_foundation",
    },
    {
        "code": "clients",
        "name": "Clients",
        "description": "Agency-owned client account and contact metadata.",
        "category": "crm",
        "module": "crm",
        "required_feature_flags": ["clients"],
        "required_bundles": ["crm"],
        "ui_routes": ["/agency/clients"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_2_crm_foundation",
    },
    {
        "code": "passengers",
        "name": "Passengers",
        "description": "Traveler profile metadata linked to requests and trips.",
        "category": "crm",
        "module": "crm",
        "required_feature_flags": ["passengers"],
        "required_bundles": ["crm"],
        "ui_routes": ["/agency/passengers"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_2_crm_foundation",
    },
    {
        "code": "client_portal",
        "name": "Client Portal Actions",
        "description": "Controlled portal action metadata for client-facing workflows.",
        "category": "crm",
        "module": "client_portal",
        "required_feature_flags": ["client_portal"],
        "required_bundles": ["crm"],
        "ui_routes": ["/agency/portal-actions"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_24_client_portal_foundation",
    },
    {
        "code": "trips",
        "name": "Trips",
        "description": "Trip dossiers and itinerary mirror metadata.",
        "category": "operations",
        "module": "requests_trips",
        "required_feature_flags": ["trips"],
        "required_bundles": ["core_agency"],
        "dependencies": ["requests", "passengers"],
        "ui_routes": ["/agency/trips"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_6_trip_dossier_foundation",
    },
    {
        "code": "offers",
        "name": "Offers",
        "description": "Offer workspace, comparison, and review metadata.",
        "category": "operations",
        "module": "offers",
        "required_feature_flags": ["offers"],
        "recommended_bundles": ["premium_operations"],
        "dependencies": ["requests", "trips"],
        "ui_routes": ["/agency/offers"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_34_offer_builder_foundation",
    },
    {
        "code": "booking_workspaces",
        "name": "Booking Workspaces",
        "description": "Internal booking workspace and PNR mirror metadata without provider execution.",
        "category": "operations",
        "module": "booking",
        "required_feature_flags": ["booking_workspaces"],
        "required_bundles": ["booking"],
        "dependencies": ["offers"],
        "ui_routes": ["/agency/booking-workspaces"],
        "documentation_links": ["docs/architecture/booking-pnr-foundation.md"],
        "introduced_phase": "phase_36_3_booking_pnr_foundation",
        "notes": "No booking execution or PNR mutation is performed.",
    },
    {
        "code": "booking_imports",
        "name": "Booking Imports",
        "description": "Imported confirmation and GDS text draft metadata.",
        "category": "operations",
        "module": "booking",
        "required_feature_flags": ["booking_imports"],
        "required_bundles": ["booking"],
        "ui_routes": ["/agency/booking-imports"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_36_4_6_standalone_import_change_foundation",
    },
    {
        "code": "tickets_emds",
        "name": "Tickets & EMDs",
        "description": "Ticket and EMD mirror records without issuance.",
        "category": "ticketing",
        "module": "tickets_emds",
        "required_feature_flags": ["ticket_records", "emd_records"],
        "required_bundles": ["ticketing"],
        "dependencies": ["booking_workspaces"],
        "ui_routes": ["/agency/tickets-emds"],
        "documentation_links": ["docs/architecture/ticket-emd-foundation.md"],
        "introduced_phase": "phase_36_4_ticket_emd_foundation",
        "notes": "Ticketing and EMD issuance remain disabled.",
    },
    {
        "code": "refunds_exchanges",
        "name": "Refunds & Exchanges",
        "description": "Manual service case metadata for refunds, exchanges, and related workflows.",
        "category": "finance",
        "module": "service_cases",
        "required_feature_flags": ["refunds_exchanges"],
        "recommended_bundles": ["finance"],
        "dependencies": ["tickets_emds"],
        "ui_routes": ["/agency/refunds-exchanges"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_36_4_6_standalone_import_change_foundation",
    },
    {
        "code": "website_cms",
        "name": "Website / CMS",
        "description": "Agency website content and CMS draft metadata.",
        "category": "cms",
        "module": "website_cms",
        "required_feature_flags": ["cms"],
        "recommended_bundles": ["core_agency"],
        "ui_routes": ["/agency/website"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_12_agency_website_foundation",
        "notes": "Publishing remains disabled unless a future phase explicitly authorizes it.",
    },
    {
        "code": "gds_parser",
        "name": "GDS Parser",
        "description": "Governed parser profile, sample, correction, and evaluation metadata.",
        "category": "supplier",
        "module": "gds",
        "required_feature_flags": ["gds_parser"],
        "required_bundles": ["gds"],
        "ui_routes": ["/agency/gds-parser", "/platform/gds-parser"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_36_6_gds_parser_foundation",
        "notes": "No provider or GDS execution is performed.",
    },
    {
        "code": "airline_intelligence",
        "name": "Airline Intelligence",
        "description": "Platform-reviewed airline policy and knowledge visibility metadata.",
        "category": "intelligence",
        "module": "airline_intelligence",
        "required_feature_flags": ["policy_library", "airline_coverage", "knowledge_versions"],
        "required_bundles": ["airline_intelligence"],
        "ui_routes": ["/agency/airline-policy-library", "/agency/airline-intelligence-coverage"],
        "documentation_links": ["docs/architecture/airline-intelligence-agency-consumption.md"],
        "introduced_phase": "phase_39_3_airline_intelligence_agency_consumption",
    },
    {
        "code": "service_taxonomy",
        "name": "Service Taxonomy",
        "description": "Canonical service domain, family, variant, alias, and applicability metadata.",
        "category": "intelligence",
        "module": "service_taxonomy",
        "required_feature_flags": ["service_taxonomy"],
        "recommended_bundles": ["airline_intelligence"],
        "ui_routes": ["/agency/service-taxonomy", "/platform/service-taxonomy"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_36_8_service_taxonomy_foundation",
    },
    {
        "code": "service_mechanics",
        "name": "Service Mechanics",
        "description": "SSR/OSI and EMD/RFIC/RFISC mechanics metadata.",
        "category": "intelligence",
        "module": "service_mechanics",
        "required_feature_flags": ["service_mechanics"],
        "recommended_bundles": ["airline_intelligence"],
        "dependencies": ["service_taxonomy"],
        "ui_routes": ["/agency/service-mechanics", "/platform/service-mechanics"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_36_9_service_mechanics_foundation",
    },
    {
        "code": "ancillary_pricing",
        "name": "Ancillary Pricing",
        "description": "Non-binding ancillary pricing and service exception metadata.",
        "category": "intelligence",
        "module": "ancillary_pricing",
        "required_feature_flags": ["ancillary_pricing"],
        "recommended_bundles": ["airline_intelligence"],
        "dependencies": ["service_taxonomy", "service_mechanics"],
        "ui_routes": ["/agency/ancillary-pricing", "/platform/ancillary-pricing"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_37_0_ancillary_pricing_foundation",
        "notes": "No payments, invoices, settlement, or EMD issuance are performed.",
    },
    {
        "code": "policy_comparison",
        "name": "Policy Comparison",
        "description": "Airline policy comparison and saved view metadata.",
        "category": "intelligence",
        "module": "policy_comparison",
        "required_feature_flags": ["policy_comparison"],
        "recommended_bundles": ["airline_intelligence"],
        "dependencies": ["airline_intelligence"],
        "ui_routes": ["/agency/policy-comparison", "/platform/policy-comparison"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_37_1_policy_comparison_foundation",
        "notes": "Automatic airline recommendation is not performed.",
    },
    {
        "code": "offer_policy_advisor",
        "name": "Offer Advisor",
        "description": "Offer-linked policy advisor context metadata.",
        "category": "offers",
        "module": "offer_policy_advisor",
        "required_feature_flags": ["offer_policy_advisor"],
        "required_bundles": ["premium_operations"],
        "dependencies": ["offers", "policy_comparison"],
        "ui_routes": ["/agency/offer-policy-advisor", "/platform/offer-policy-advisor"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_37_2_offer_policy_advisor_foundation",
    },
    {
        "code": "offer_decision_evidence",
        "name": "Offer Decision Evidence",
        "description": "Decision packs, explanations, and review evidence metadata.",
        "category": "offers",
        "module": "offer_decision",
        "required_feature_flags": ["offer_decision_evidence"],
        "required_bundles": ["premium_operations"],
        "dependencies": ["offer_policy_advisor"],
        "ui_routes": ["/agency/offer-decision-packs", "/agency/offer-decision-explanations"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_37_3_offer_decision_pack_foundation",
    },
    {
        "code": "offer_exports",
        "name": "Decision Exports",
        "description": "Review exports, render previews, release readiness, handoffs, outcomes, audit, governance, and compliance metadata.",
        "category": "documents",
        "module": "offer_exports",
        "required_feature_flags": ["offer_exports"],
        "recommended_bundles": ["premium_operations"],
        "dependencies": ["offer_decision_evidence"],
        "ui_routes": ["/agency/offer-decision-exports", "/agency/offer-decision-export-previews"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_37_5_offer_decision_export_foundation",
        "notes": "No automatic sending, public links, or real PDF delivery are performed.",
    },
    {
        "code": "manual_delivery",
        "name": "Manual Delivery",
        "description": "Manual delivery handoff and outcome metadata after human action outside AgencyOS.",
        "category": "documents",
        "module": "manual_delivery",
        "required_feature_flags": ["manual_delivery"],
        "required_bundles": ["premium_operations"],
        "dependencies": ["offer_exports"],
        "ui_routes": ["/agency/offer-decision-export-deliveries", "/agency/offer-decision-export-delivery-outcomes"],
        "documentation_links": ["README.md"],
        "introduced_phase": "phase_37_8_manual_delivery_handoff_foundation",
    },
    {
        "code": "documents",
        "name": "Documents",
        "description": "Document template, render, storage, package, and manual delivery metadata.",
        "category": "documents",
        "module": "documents",
        "required_feature_flags": ["documents"],
        "recommended_bundles": ["premium_operations"],
        "ui_routes": ["/agency/documents", "/platform/document-templates"],
        "documentation_links": ["docs/architecture/document-foundation.md"],
        "introduced_phase": "phase_36_5_document_foundation",
    },
    {
        "code": "feature_availability",
        "name": "Feature Availability",
        "description": "Agency-specific feature flag visibility metadata.",
        "category": "feature_governance",
        "module": "settings",
        "required_feature_flags": ["feature_availability"],
        "required_bundles": ["beta_features"],
        "ui_routes": ["/agency/feature-availability", "/platform/feature-flags"],
        "documentation_links": ["docs/architecture/agency-feature-flags-foundation.md"],
        "introduced_phase": "phase_39_7_agency_feature_flags_foundation",
    },
    {
        "code": "feature_readiness",
        "name": "Feature Readiness",
        "description": "Feature flag readiness checklist and audit metadata.",
        "category": "feature_governance",
        "module": "settings",
        "required_feature_flags": ["feature_readiness"],
        "required_bundles": ["beta_features"],
        "dependencies": ["feature_availability"],
        "ui_routes": ["/agency/feature-readiness", "/platform/feature-flag-audit"],
        "documentation_links": ["docs/architecture/agency-feature-flag-audit-foundation.md"],
        "introduced_phase": "phase_39_8_feature_flag_audit_foundation",
    },
    {
        "code": "feature_bundles",
        "name": "Feature Bundles",
        "description": "Reusable feature flag bundle metadata.",
        "category": "feature_governance",
        "module": "settings",
        "required_feature_flags": ["feature_bundles"],
        "required_bundles": ["beta_features"],
        "dependencies": ["feature_availability"],
        "ui_routes": ["/agency/feature-bundles", "/platform/feature-flag-bundles"],
        "documentation_links": ["docs/architecture/agency-feature-flag-bundle-foundation.md"],
        "introduced_phase": "phase_39_9_feature_flag_bundle_foundation",
    },
    {
        "code": "assigned_bundles",
        "name": "Assigned Bundles",
        "description": "Agency feature bundle assignment metadata and preserved history.",
        "category": "feature_governance",
        "module": "settings",
        "required_feature_flags": ["assigned_bundles"],
        "recommended_bundles": ["beta_features"],
        "dependencies": ["feature_bundles"],
        "ui_routes": ["/agency/assigned-bundles", "/platform/feature-bundle-assignments"],
        "documentation_links": ["docs/architecture/feature-bundle-assignment-foundation.md"],
        "introduced_phase": "phase_40_0_feature_bundle_assignment_foundation",
    },
    {
        "code": "capability_catalog",
        "name": "Capability Catalog",
        "description": "Canonical metadata inventory of AgencyOS functional capabilities.",
        "category": "feature_governance",
        "module": "platform",
        "status": "active",
        "visibility": "platform_and_agency",
        "required_feature_flags": ["capability_catalog"],
        "recommended_bundles": ["beta_features"],
        "dependencies": ["feature_bundles", "assigned_bundles"],
        "ui_routes": ["/platform/capabilities", "/agency/capabilities"],
        "documentation_links": ["docs/architecture/capability-catalog-foundation.md"],
        "introduced_phase": PHASE_LABEL,
    },
]


class CapabilityCatalogService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_capabilities(
        self,
        *,
        category: str | None = None,
        module: str | None = None,
        status: str | None = None,
        agency_view: bool = False,
    ) -> list[dict[str, Any]]:
        stored = await self.db.collection(CAPABILITY_COLLECTION).find_many()
        entries_by_code = {item.get("code"): self._normalize_entry(item, default_entry=False) for item in stored if item.get("code")}
        for default_entry in DEFAULT_CAPABILITY_CATALOG:
            entries_by_code.setdefault(default_entry["code"], self._normalize_entry(default_entry, default_entry=True))
        entries = list(entries_by_code.values())
        if agency_view:
            entries = [item for item in entries if item.get("visibility") in {"agency", "platform_and_agency", "public"}]
        if category:
            entries = [item for item in entries if item.get("category") == category]
        if module:
            entries = [item for item in entries if item.get("module") == module]
        if status:
            entries = [item for item in entries if item.get("status") == status]
        entries.sort(key=lambda item: (item.get("category") or "", item.get("module") or "", item.get("name") or ""))
        return [self._entry_projection(item, agency_view=agency_view) for item in entries]

    async def get_capability(self, code: str, *, agency_view: bool = False) -> dict[str, Any] | None:
        entries = await self.list_capabilities(agency_view=agency_view)
        return next((item for item in entries if code in {item.get("code"), item.get("id")}), None)

    async def list_categories(self) -> list[dict[str, Any]]:
        entries = await self.list_capabilities()
        categories = sorted({item.get("category") for item in entries if item.get("category")})
        return [{"category": category, "count": len([item for item in entries if item.get("category") == category])} for category in categories]

    async def list_modules(self) -> list[dict[str, Any]]:
        entries = await self.list_capabilities()
        modules = sorted({item.get("module") for item in entries if item.get("module")})
        return [{"module": module, "count": len([item for item in entries if item.get("module") == module])} for module in modules]

    async def platform_capabilities_response(
        self,
        *,
        category: str | None = None,
        module: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_capabilities(category=category, module=module, status=status)
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "capability_count": len(items),
            "default_capability_count": len(DEFAULT_CAPABILITY_CATALOG),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def platform_capability_detail_response(self, code: str) -> dict[str, Any]:
        capability = await self.get_capability(code)
        return {
            "phase": PHASE_LABEL,
            "capability": capability,
            "found": capability is not None,
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def platform_categories_response(self) -> dict[str, Any]:
        items = await self.list_categories()
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "category_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def platform_modules_response(self) -> dict[str, Any]:
        items = await self.list_modules()
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "module_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_capabilities_response(self, agency_id: str, *, availability: str | None = None) -> dict[str, Any]:
        entries = await self.list_capabilities(agency_view=True)
        assignment_context = await self._agency_assignment_context(agency_id)
        flag_states = await self._agency_flag_states(agency_id)
        items = [
            self._agency_capability_projection(entry, agency_id, assignment_context, flag_states)
            for entry in entries
        ]
        if availability:
            items = [item for item in items if item.get("informational_availability") == availability]
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "capability_count": len(items),
            "availability_counts": self._availability_counts(items),
            "notice": "Capability availability is informational only. No feature enforcement, entitlement checks, route blocking, permission changes, or execution are performed.",
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def _normalize_entry(self, entry: dict[str, Any], *, default_entry: bool) -> dict[str, Any]:
        normalized = CapabilityCatalogEntry(
            id=entry.get("id") or f"capability_{entry.get('code') or 'catalog'}",
            code=entry.get("code") or "capability",
            name=entry.get("name") or entry.get("code", "Capability").replace("_", " ").title(),
            description=entry.get("description"),
            category=entry.get("category") or "general",
            module=entry.get("module") or "general",
            status=entry.get("status") or "active",
            visibility=entry.get("visibility") or "platform_and_agency",
            tags=list(entry.get("tags") or []),
            required_feature_flags=list(entry.get("required_feature_flags") or []),
            required_bundles=list(entry.get("required_bundles") or []),
            recommended_bundles=list(entry.get("recommended_bundles") or []),
            dependencies=list(entry.get("dependencies") or []),
            ui_routes=list(entry.get("ui_routes") or []),
            documentation_links=list(entry.get("documentation_links") or []),
            introduced_phase=entry.get("introduced_phase") or PHASE_LABEL,
            deprecated=bool(entry.get("deprecated", False)),
            notes=entry.get("notes"),
            metadata_only=True,
            execution_logic_disabled=True,
            entitlement_enforcement_disabled=True,
        ).model_dump(mode="json")
        normalized["default_entry"] = default_entry
        return normalized

    def _entry_projection(self, entry: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        projected = dict(entry)
        projected["documentation_count"] = len(projected.get("documentation_links") or [])
        projected["dependency_count"] = len(projected.get("dependencies") or [])
        projected["required_bundle_count"] = len(projected.get("required_bundles") or [])
        projected["required_feature_flag_count"] = len(projected.get("required_feature_flags") or [])
        projected["read_only"] = True
        projected.update(self.safety_flags())
        if agency_view:
            projected["payloads_hidden"] = True
        return projected

    async def _agency_assignment_context(self, agency_id: str) -> dict[str, Any]:
        assignments = await self.db.collection("agency_feature_bundle_assignments").find_many({"agency_id": agency_id})
        active_assignments = [item for item in assignments if item.get("status") != "inactive"]
        bundle_keys: set[str] = set()
        bundle_ids: set[str] = set()
        bundle_service = AgencyFeatureFlagBundleService(self.db)
        for assignment in active_assignments:
            bundle_id = assignment.get("bundle_id")
            if not bundle_id:
                continue
            bundle_ids.add(bundle_id)
            bundle = await bundle_service.get_bundle(bundle_id)
            if bundle:
                bundle_keys.add(bundle.get("bundle_key") or bundle_id)
                bundle_ids.add(bundle.get("bundle_id") or bundle_id)
            else:
                bundle_keys.add(bundle_id)
        return {
            "assignment_count": len(active_assignments),
            "bundle_keys": bundle_keys,
            "bundle_ids": bundle_ids,
        }

    async def _agency_flag_states(self, agency_id: str) -> dict[str, str]:
        flags = await self.db.collection("agency_feature_flags").find_many({"agency_id": agency_id})
        return {item.get("feature_key"): item.get("state") or "unknown" for item in flags if item.get("feature_key")}

    def _agency_capability_projection(
        self,
        entry: dict[str, Any],
        agency_id: str,
        assignment_context: dict[str, Any],
        flag_states: dict[str, str],
    ) -> dict[str, Any]:
        projected = self._entry_projection(entry, agency_view=True)
        required_bundles = set(projected.get("required_bundles") or [])
        assigned_bundles = set(assignment_context.get("bundle_keys") or set()) | set(assignment_context.get("bundle_ids") or set())
        missing_bundles = sorted(required_bundles - assigned_bundles)
        required_flags = list(projected.get("required_feature_flags") or [])
        reviewed_flags = {"enabled", "beta", "pilot"}
        missing_flags = sorted([flag for flag in required_flags if flag_states.get(flag) not in reviewed_flags])
        if projected.get("deprecated"):
            availability = "unavailable"
            reason = "Capability is deprecated metadata."
        elif not missing_bundles and not missing_flags:
            availability = "available"
            reason = "Required metadata is present for informational visibility."
        else:
            availability = "unavailable"
            reason = "Required bundle or feature flag metadata is not present."
        projected.update(
            {
                "agency_id": agency_id,
                "informational_availability": availability,
                "availability_reason": reason,
                "missing_bundles": missing_bundles,
                "missing_feature_flags": missing_flags,
                "assigned_bundle_count": assignment_context.get("assignment_count") or 0,
                "feature_flag_states": {flag: flag_states.get(flag, "unknown") for flag in required_flags},
            }
        )
        return projected

    def _availability_counts(self, items: list[dict[str, Any]]) -> dict[str, int]:
        return {
            "available": len([item for item in items if item.get("informational_availability") == "available"]),
            "unavailable": len([item for item in items if item.get("informational_availability") == "unavailable"]),
        }

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "read_only": True,
            "no_execution_logic": True,
            "execution_logic_disabled": True,
            "runtime_feature_enforcement_disabled": True,
            "entitlement_checks_disabled": True,
            "entitlement_enforcement_disabled": True,
            "route_blocking_disabled": True,
            "permission_changes_disabled": True,
            "billing_disabled": True,
            "payments_disabled": True,
            "subscription_charging_disabled": True,
            "provider_execution_disabled": True,
            "publishing_disabled": True,
            "external_services_disabled": True,
            "external_api_calls_disabled": True,
            "external_ai_disabled": True,
            "background_workers_disabled": True,
            "cron_disabled": True,
        }
