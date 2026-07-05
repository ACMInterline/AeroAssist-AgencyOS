export const platformModuleGroups = [
  {
    title: "SaaS & Agencies",
    description: "Platform owners manage subscribed agencies, account setup, and the overall SaaS operating layer.",
    audience: "Platform only",
    safety: "Metadata only",
    items: [
      { label: "Platform Console", description: "Owner overview and system counts", href: "/platform", icon: "shield", badge: "Platform only" },
      { label: "Subscriptions & Entitlements", description: "Plan and agency entitlement metadata", href: "/platform/saas-subscriptions", icon: "layers", badge: "No billing" },
      { label: "Feature Flags", description: "Agency feature visibility metadata", href: "/platform/feature-flags", icon: "layers", badge: "Metadata only" },
      { label: "Feature Flag Audit", description: "Read-only feature audit history", href: "/platform/feature-flag-audit", icon: "clipboard", badge: "Metadata only", metadata_only: true },
      { label: "Feature Flag Bundles", description: "Reusable feature grouping metadata", href: "/platform/feature-flag-bundles", icon: "layers", badge: "Metadata only", metadata_only: true },
      { label: "Feature Bundle Assignments", description: "Agency bundle assignment metadata", href: "/platform/feature-bundle-assignments", icon: "clipboard", badge: "Metadata only", metadata_only: true },
      { label: "Feature Bundle Rollout Readiness", description: "Assignment readiness checklists", href: "/platform/feature-bundle-rollout-readiness", icon: "clipboard", badge: "Metadata only", metadata_only: true },
      { label: "Feature Bundle Rollout Plans", description: "Planned rollout metadata", href: "/platform/feature-bundle-rollout-plans", icon: "clipboard", badge: "Metadata only", metadata_only: true },
      { label: "Capability Catalog", description: "Canonical capability inventory", href: "/platform/capabilities", icon: "database", badge: "Metadata only", metadata_only: true },
      { label: "Agencies", description: "Subscribed travel agency workspaces", href: "/platform/agencies", icon: "building", badge: "Platform only" },
      { label: "Reference Data", description: "Shared platform lookup data", href: "/platform/reference", icon: "database", badge: "Platform only" },
      { label: "Blueprint", description: "Route and model alignment", href: "/platform/blueprint", icon: "git", badge: "Read-only" },
    ],
  },
  {
    title: "Airline Intelligence Governance",
    description: "Platform owners curate airline data packs, policies, service taxonomy, mechanics, pricing, and safe agency visibility.",
    audience: "Platform only",
    safety: "No provider execution",
    items: [
      { label: "Airlines / Knowledge", description: "Global airline records", href: "/platform/airlines", icon: "plane", badge: "Platform only" },
      { label: "Airline Data Packs", description: "Staged airline intelligence", href: "/platform/airline-intelligence-data-packs", icon: "file", badge: "Metadata only" },
      { label: "Data Pack Reviews", description: "Checklist and conflict review", href: "/platform/airline-intelligence-data-pack-reviews", icon: "git", badge: "Metadata only" },
      { label: "Knowledge Versions", description: "Release-channel metadata", href: "/platform/airline-intelligence-knowledge-versions", icon: "layers", badge: "Metadata only" },
      { label: "Agency Consumption", description: "Safe-use visibility bridge", href: "/platform/airline-intelligence-agency-consumption", icon: "layers", badge: "Metadata only" },
      { label: "Policy Ingestion", description: "Source and extraction review", href: "/platform/airline-policy-ingestion", icon: "file", badge: "Metadata only" },
      { label: "Service Taxonomy", description: "Canonical service meaning", href: "/platform/service-taxonomy", icon: "tags", badge: "Metadata only" },
      { label: "Service Mechanics", description: "SSR/EMD handling metadata", href: "/platform/service-mechanics", icon: "check", badge: "No execution" },
      { label: "Ancillary Pricing", description: "Non-binding price metadata", href: "/platform/ancillary-pricing", icon: "check", badge: "No payments" },
      { label: "Policy Comparison", description: "Comparison profile metadata", href: "/platform/policy-comparison", icon: "rows", badge: "No recommendations" },
    ],
  },
  {
    title: "Agency Website/CMS Governance",
    description: "Platform owners inspect shared website/CMS foundations while agencies maintain their own public site content.",
    audience: "Platform only",
    safety: "No publishing yet",
    items: [
      { label: "Documents", description: "Platform document templates", href: "/platform/document-templates", icon: "file", badge: "Metadata only" },
      { label: "GDS Parser", description: "Parser profiles and samples", href: "/platform/gds-parser", icon: "database", badge: "No provider calls" },
    ],
  },
  {
    title: "CRM / Client Portal Governance",
    description: "Platform owners can see the foundations agencies use for clients, passengers, portal visibility, and controlled actions.",
    audience: "Platform only",
    safety: "No automatic sending",
    items: [
      { label: "Rules & Services", description: "Shared request service rules", href: "/platform/rules-services", icon: "check", badge: "Platform only" },
    ],
  },
  {
    title: "Offer & Document Governance",
    description: "Platform owners review offer advisor, decision evidence, export, release, delivery, audit, compliance, and document metadata.",
    audience: "Platform only",
    safety: "No booking or payment",
    items: [
      { label: "Offer Advisor", description: "Offer policy diagnostics", href: "/platform/offer-policy-advisor", icon: "rows", badge: "Read-only" },
      { label: "Decision Packs", description: "Offer evidence bundles", href: "/platform/offer-decision-packs", icon: "rows", badge: "Read-only" },
      { label: "Decision Explanations", description: "Human explanation timelines", href: "/platform/offer-decision-explanations", icon: "rows", badge: "Read-only" },
      { label: "Decision Exports", description: "Review export metadata", href: "/platform/offer-decision-exports", icon: "file", badge: "No sending" },
      { label: "Export Previews", description: "Render preview metadata", href: "/platform/offer-decision-export-previews", icon: "file", badge: "No PDF delivery" },
      { label: "Export Releases", description: "Manual readiness metadata", href: "/platform/offer-decision-export-releases", icon: "file", badge: "Manual only" },
      { label: "Export Handoffs", description: "Manual handoff metadata", href: "/platform/offer-decision-export-deliveries", icon: "file", badge: "No sending" },
      { label: "Export Outcomes", description: "Human-recorded outcomes", href: "/platform/offer-decision-export-delivery-outcomes", icon: "file", badge: "Metadata only" },
      { label: "Export Audits", description: "Lifecycle review records", href: "/platform/offer-decision-export-audit-reviews", icon: "file", badge: "Read-only" },
      { label: "Export Governance", description: "Retention and legal metadata", href: "/platform/offer-decision-export-governance", icon: "file", badge: "Metadata only" },
      { label: "Export Compliance", description: "Evidence metadata", href: "/platform/offer-decision-export-compliance", icon: "file", badge: "Metadata only" },
    ],
  },
  {
    title: "System Readiness",
    description: "Platform owners verify health, phase readiness, safe boundaries, and canonical route policy before release.",
    audience: "Platform only",
    safety: "Read-only",
    items: [
      { label: "Readiness", description: "Health and phase state", href: "/platform", icon: "shield", badge: "Read-only" },
    ],
  },
]

export const agencyModuleGroups = [
  {
    title: "Daily Work",
    description: "Agency staff start here for new requests, intake review, and active work queues.",
    audience: "Agency workspace",
    safety: "Manual operations",
    items: [
      { label: "Dashboard", description: "Workspace home", href: "/agency", icon: "building", entitlementKey: "dashboard" },
      { label: "Create request", description: "Start a staff request", href: "/agency/requests/new", icon: "plus", entitlementKey: "requests" },
      { label: "Intakes", description: "Public and portal queue", href: "/agency/request-intakes", icon: "inbox", entitlementKey: "request_intakes" },
      { label: "GDS Parser", description: "Parse review only", href: "/agency/gds-parser", icon: "database", badge: "No provider calls", entitlementKey: "gds_parser" },
    ],
  },
  {
    title: "Clients & Passengers",
    description: "Agency-owned CRM records for requesters, travelers, relationships, and portal-facing profiles.",
    audience: "Agency workspace",
    safety: "Agency owned",
    items: [
      { label: "Clients", description: "Accounts and contacts", href: "/agency/clients", icon: "users", entitlementKey: "crm" },
      { label: "Passengers", description: "Traveler profiles", href: "/agency/passengers", icon: "user", entitlementKey: "crm" },
      { label: "Portal Actions", description: "Controlled client actions", href: "/agency/portal-actions", icon: "globe", badge: "Manual only", entitlementKey: "client_portal" },
    ],
  },
  {
    title: "Requests, Offers & Trips",
    description: "Agency staff manage requests, trip dossiers, offer options, internal booking mirrors, tickets, EMDs, and service cases.",
    audience: "Agency workspace",
    safety: "No live provider execution",
    items: [
      { label: "Requests", description: "Operational work", href: "/agency/requests", icon: "clipboard", entitlementKey: "requests" },
      { label: "Trips", description: "Travel dossiers", href: "/agency/trips", icon: "plane", entitlementKey: "trips" },
      { label: "Offers", description: "Compare options", href: "/agency/offers", icon: "sparkles", entitlementKey: "offers" },
      { label: "Booking Workspaces", description: "PNR mirrors", href: "/agency/booking-workspaces", icon: "clipboard", badge: "Mirror only", entitlementKey: "booking_workspaces" },
      { label: "Booking Imports", description: "GDS drafts", href: "/agency/booking-imports", icon: "files", badge: "Review only", entitlementKey: "booking_imports" },
      { label: "Tickets & EMDs", description: "Mirror records", href: "/agency/tickets-emds", icon: "files", badge: "No issuance", entitlementKey: "tickets_emds" },
      { label: "Refunds & Exchanges", description: "Service cases", href: "/agency/refunds-exchanges", icon: "clipboard", badge: "Manual only", entitlementKey: "refunds_exchanges" },
    ],
  },
  {
    title: "Website/CMS",
    description: "Agency staff maintain their own website content and media. Public publishing stays controlled by CMS safety settings.",
    audience: "Agency workspace",
    safety: "No publishing yet",
    items: [
      { label: "Website / CMS", description: "Public content drafts", href: "/agency/website", icon: "globe", badge: "No publishing yet", entitlementKey: "cms" },
      { label: "CMS Media", description: "Website assets", href: "/agency/website/media", icon: "files", badge: "Public-safe media", entitlementKey: "cms_media" },
    ],
  },
  {
    title: "Airline Intelligence Visibility",
    description: "Agency staff consume platform-reviewed airline intelligence as read-only guidance for daily work.",
    audience: "Agency read-only",
    safety: "Metadata only",
    items: [
      { label: "Policy Library", description: "Airline rules", href: "/agency/airline-policy-library", icon: "database", badge: "Agency read-only", entitlementKey: "airline_intelligence" },
      { label: "Airline Coverage", description: "Data readiness", href: "/agency/airline-intelligence-coverage", icon: "plane", badge: "Agency read-only", entitlementKey: "airline_coverage" },
      { label: "Review Coverage", description: "Safe-use status", href: "/agency/airline-intelligence-review-coverage", icon: "clipboard", badge: "Agency read-only", entitlementKey: "airline_coverage" },
      { label: "Knowledge Versions", description: "Visible airline data", href: "/agency/airline-intelligence-knowledge-versions", icon: "files", badge: "Agency read-only", entitlementKey: "knowledge_versions" },
      { label: "Airline Intelligence Usage", description: "Safe-use bridge", href: "/agency/airline-intelligence-consumption", icon: "files", badge: "Agency read-only", entitlementKey: "airline_intelligence_consumption" },
      { label: "Service Taxonomy", description: "Canonical services", href: "/agency/service-taxonomy", icon: "tags", badge: "Agency read-only", entitlementKey: "service_taxonomy" },
      { label: "Service Mechanics", description: "SSR/EMD lookup", href: "/agency/service-mechanics", icon: "clipboard", badge: "Metadata only", entitlementKey: "service_mechanics" },
      { label: "Ancillary Pricing", description: "Price estimates", href: "/agency/ancillary-pricing", icon: "clipboard", badge: "No payments", entitlementKey: "ancillary_pricing" },
      { label: "Policy Comparison", description: "Airline operations", href: "/agency/policy-comparison", icon: "rows", badge: "No recommendations", entitlementKey: "policy_comparison" },
      { label: "Service Advisor", description: "Operational guidance", href: "/agency/airline-service-advisor", icon: "clipboard", badge: "Human review", entitlementKey: "airline_service_advisor" },
      { label: "Offer Advisor", description: "Offer policy context", href: "/agency/offer-policy-advisor", icon: "rows", badge: "Metadata only", entitlementKey: "offer_policy_advisor" },
    ],
  },
  {
    title: "Documents & Delivery",
    description: "Agency staff review document packages, offer decision evidence, manual release readiness, handoffs, and outcomes.",
    audience: "Agency workspace",
    safety: "No automatic sending",
    items: [
      { label: "Documents", description: "Rendered files", href: "/agency/documents", icon: "files", badge: "Manual only", entitlementKey: "documents" },
      { label: "Decision Packs", description: "Offer evidence", href: "/agency/offer-decision-packs", icon: "rows", badge: "Human review", entitlementKey: "offer_decision_evidence" },
      { label: "Decision Explanations", description: "Timeline audit", href: "/agency/offer-decision-explanations", icon: "rows", badge: "Metadata only", entitlementKey: "offer_decision_evidence" },
      { label: "Decision Exports", description: "Review snapshots", href: "/agency/offer-decision-exports", icon: "files", badge: "No sending", entitlementKey: "offer_exports" },
      { label: "Export Previews", description: "Render review", href: "/agency/offer-decision-export-previews", icon: "files", badge: "No PDF delivery", entitlementKey: "offer_exports" },
      { label: "Export Releases", description: "Manual readiness", href: "/agency/offer-decision-export-releases", icon: "files", badge: "Manual only", entitlementKey: "offer_exports" },
      { label: "Export Handoffs", description: "Manual metadata", href: "/agency/offer-decision-export-deliveries", icon: "files", badge: "No sending", entitlementKey: "manual_delivery" },
      { label: "Export Outcomes", description: "Manual tracking", href: "/agency/offer-decision-export-delivery-outcomes", icon: "files", badge: "Metadata only", entitlementKey: "manual_delivery" },
      { label: "Export Audits", description: "Read-only review trail", href: "/agency/offer-decision-export-audit-reviews", icon: "files", badge: "Agency read-only", entitlementKey: "offer_decision_evidence" },
      { label: "Export Policy", description: "Retention metadata", href: "/agency/offer-decision-export-governance", icon: "files", badge: "Metadata only", entitlementKey: "offer_decision_evidence" },
      { label: "Export Compliance Evidence", description: "Proof metadata", href: "/agency/offer-decision-export-compliance", icon: "files", badge: "Metadata only", entitlementKey: "offer_decision_evidence" },
    ],
  },
  {
    title: "Settings",
    description: "Agency staff configure team access, brand settings, forms, reference data suggestions, and workspace preferences.",
    audience: "Agency workspace",
    safety: "Agency owned",
    items: [
      { label: "Team", description: "Staff access", href: "/agency", icon: "users", badge: "Dashboard", entitlementKey: "dashboard" },
      { label: "My Subscription", description: "Assigned plan and entitlements", href: "/agency/saas-subscription", icon: "layers", badge: "Agency read-only", entitlementKey: "subscription" },
      { label: "Feature Availability", description: "Feature visibility metadata", href: "/agency/feature-availability", icon: "layers", badge: "Agency read-only", entitlementKey: "settings" },
      { label: "Feature Readiness", description: "Feature checklist metadata", href: "/agency/feature-readiness", icon: "clipboard", badge: "Metadata only", entitlementKey: "settings", metadata_only: true },
      { label: "Feature Bundles", description: "Available feature bundle metadata", href: "/agency/feature-bundles", icon: "layers", badge: "Metadata only", entitlementKey: "settings", metadata_only: true },
      { label: "Assigned Bundles", description: "Feature bundle assignment metadata", href: "/agency/assigned-bundles", icon: "clipboard", badge: "Metadata only", entitlementKey: "settings", metadata_only: true },
      { label: "Bundle Rollout Readiness", description: "Read-only bundle readiness summaries", href: "/agency/bundle-rollout-readiness", icon: "clipboard", badge: "Metadata only", entitlementKey: "settings", metadata_only: true },
      { label: "Rollout Plans", description: "Read-only bundle rollout plan metadata", href: "/agency/rollout-plans", icon: "clipboard", badge: "Metadata only", entitlementKey: "settings", metadata_only: true },
      { label: "Available Capabilities", description: "Capability catalog visibility metadata", href: "/agency/capabilities", icon: "database", badge: "Metadata only", entitlementKey: "settings", metadata_only: true },
      { label: "Reference Data", description: "Lookups and suggestions", href: "/agency/reference", icon: "database", badge: "Suggest only", entitlementKey: "reference_data" },
      { label: "Form Profiles", description: "Field menus", href: "/agency/settings/forms", icon: "clipboard", entitlementKey: "form_profiles" },
      { label: "Settings", description: "Brand and theme", href: "/agency/settings", icon: "settings", entitlementKey: "settings" },
    ],
  },
]

export function flattenModuleGroups(groups) {
  return groups.flatMap((group) => group.items.map((item) => ({ ...item, group: group.title })))
}

export const entitlementVisibilityLabels = {
  included: "Included",
  limited: "Limited",
  review_required: "Review required",
  not_included: "Not included",
  unknown: "Unknown",
}

export const entitlementVisibilityTone = {
  included: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  limited: "bg-amber-50 text-amber-700 ring-amber-200",
  review_required: "bg-sky-50 text-sky-700 ring-sky-200",
  not_included: "bg-slate-100 text-slate-600 ring-slate-200",
  unknown: "bg-zinc-50 text-zinc-600 ring-zinc-200",
}

export function entitlementVisibilityForItem(item, visibilityByKey = {}) {
  return visibilityByKey[item.entitlementKey] || visibilityByKey[item.href] || null
}

export function entitlementLabel(status) {
  return entitlementVisibilityLabels[status] || entitlementVisibilityLabels.unknown
}

export function entitlementTone(status) {
  return entitlementVisibilityTone[status] || entitlementVisibilityTone.unknown
}

export function summarizeEntitlementVisibility(items, visibilityByKey = {}) {
  return items.reduce((counts, item) => {
    const visibility = entitlementVisibilityForItem(item, visibilityByKey)
    const status = visibility?.status || "unknown"
    counts[status] = (counts[status] || 0) + 1
    return counts
  }, {})
}

export const featureFlagLabels = {
  enabled: "Enabled",
  disabled: "Disabled",
  hidden: "Hidden",
  beta: "Beta",
  pilot: "Pilot",
}

export const featureFlagTone = {
  enabled: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  disabled: "bg-slate-100 text-slate-600 ring-slate-200",
  hidden: "bg-zinc-50 text-zinc-600 ring-zinc-200",
  beta: "bg-sky-50 text-sky-700 ring-sky-200",
  pilot: "bg-violet-50 text-violet-700 ring-violet-200",
}

export function featureFlagLabel(state) {
  return featureFlagLabels[state] || featureFlagLabels.disabled
}

export function featureFlagClass(state) {
  return featureFlagTone[state] || featureFlagTone.disabled
}
