# Visual Policy Editor Foundation

Phase 52.3 adds the metadata-only Visual Policy Editor Foundation.

It creates `visual_policy_editor_cards` as structured airline service policy-card metadata for human-reviewed operational knowledge production. The foundation provides no-code sections for overview, support status, limits, route/aircraft/cabin/date/weather restrictions, documents, approvals, warnings, evidence, governance links, and service parameter taxonomy links.

## Scope

- Platform API: `/api/platform/visual-policy-editor`
- Agency API: `/api/agencies/{agency_id}/policy-editor`
- Platform UI: `/platform/visual-policy-editor`
- Agency UI: `/agency/policy-editor`
- Collection: `visual_policy_editor_cards`
- Models: `VisualPolicyEditorCard`, `VisualPolicyEditorCardCreate`, `VisualPolicyEditorCardUpdate`

## Policy Families

The foundation supports PETC, AVIH, SVAN, ESAN, WCHR, WCHS, WCHC, WCOB, MAAS, MEDIF, MEDA, STCR, OXYG, POC, UMNR, YP, EXST, CBBG, sports equipment, musical instruments, fragile/valuable items, restricted equipment, and documents compliance.

## Boundaries

Phase 52.3 does not execute policies, evaluate rules, calculate pricing, call provider systems, use AI/LLM generation, run background workers, send messages automatically, create old `/admin` routes, or replace human authority.

The policy card is an operational metadata surface. Final interpretation, client communication, airline contact, booking, ticketing, EMD issuance, and exception handling remain human-authorized workflows.

## Relationships

Visual Policy Editor cards can reference:

- evidence links from knowledge acquisition and reviewed airline sources
- knowledge governance/version/release metadata
- service parameter taxonomy records
- reference data domains for future controlled values
- knowledge import template records for future structured data population
- pricing formula builder records for separate no-code ancillary and service pricing metadata

These links are stored as metadata only. The editor prepares the system for scenario testing, real airline data population, and future governed production workflows without introducing executable policy logic.

Phase 52.4 adds `pricing_formula_builders` as a separate metadata layer for pricing formula records. Visual Policy Editor remains policy-card metadata and does not calculate pricing. Pricing Formula Builder references may use policy-card evidence, but live price calculation, payment integrations, provider integrations, AI, workers, and automatic client sending remain disabled.
