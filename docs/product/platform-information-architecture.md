# Platform Information Architecture

Phase 59.0 replaces the Platform Console's implementation-history navigation with a task-based product hierarchy. It changes presentation only: canonical routes, APIs, authorization, and domain ownership remain unchanged.

## Product Goal

A Platform Owner should understand current agency, knowledge, pilot, and system priorities within 30 seconds. The default `/platform` page therefore shows decisions and exceptions rather than every registered module.

## Before

The Platform shell rendered the complete internal module catalogue as a multi-column header. Around one hundred operational workspaces, rollout registers, governance tools, and diagnostics had similar visual weight. The home page repeated those groups and exposed raw collection counts regardless of operational value.

## After

The primary navigation has exactly eight areas:

1. Overview
2. Agencies
3. Airline Knowledge
4. Services & Pricing
5. Product Configuration
6. Pilot & Support
7. System Health
8. Advanced

`Advanced` is collapsed by default and visually separated. Platform Owner and Platform Admin receive the complete permitted product hierarchy. Platform Support receives Overview, Agencies, Airline Knowledge, Pilot & Support, and System Health. The existing knowledge-editor role receives its permitted knowledge and service areas. API authorization remains authoritative.

## Before And After Mapping

| Before: catalogue group or item | After: primary area | Notes |
|---|---|---|
| Platform Console and full count grid | Overview | Replaced by attention, agency, knowledge, pilot, health, activity, and quick-action sections. |
| Agencies, subscriptions, feature flags | Agencies | Feature rollout registers move to Advanced. |
| Airlines, profiles, policies, evidence, coverage, distribution, interline, brands, contacts, releases | Airline Knowledge | Operational evaluation internals and population tooling move to Advanced. |
| Rules & Services, taxonomy, mechanics, ancillary pricing, policy comparison, rule composition, scenarios | Services & Pricing | Labels describe user outcomes rather than implementation layers. |
| Reference data, document templates, feature bundles, offer settings | Product Configuration | Detailed import and export registers remain available in Advanced. |
| Commercial Pilot readiness, feedback, pilot guidance | Pilot & Support | Phase 57 release authority remains separate and unchanged. |
| Pilot Operations and Operations Governance | System Health | Surfaces existing health, readiness, backup, smoke, release, and alert information. |
| Operational workspace mirrors, raw registers, rollout internals, workflow diagnostics, maturity, blueprints | Advanced | Existing routes remain available as collapsed specialist links. |
| CMS, offer-export, document-delivery, and implementation-specific governance pages | Advanced | Nothing is deleted; deep links remain valid. |

## Platform Overview

The Overview answers:

- Which agencies need onboarding attention?
- Are airline knowledge release gates blocked?
- Is the Commercial Pilot blocked?
- Is new pilot feedback waiting?
- Is public system readiness healthy?
- What recent governed activity occurred?

Optional summary APIs degrade independently so one unavailable specialist assessment does not hide the rest of the overview. Recent activity is bounded and contains only its event label, summary, and timestamp.

## Catalogue Ownership

`frontend/src/lib/moduleCatalog.js` remains the internal module and route source. Phase 59.0 adds a validated product-navigation projection over those entries. Every projected item resolves an existing catalogue route and carries:

- `primary_area`
- `user_purpose`
- `audience`
- `navigation_priority`
- `advanced_only`
- `hidden_from_primary_navigation`
- `preferred_label`
- `preferred_description`

Unselected non-contextual catalogue entries are projected into Advanced. This avoids a parallel route registry while preserving specialist access.

## Safety

Phase 59.0 adds no router, mutation, model, collection, index, provider connection, payment, ticket issuance, messaging, or release action. Navigation visibility improves product comprehension but never replaces backend authorization.

