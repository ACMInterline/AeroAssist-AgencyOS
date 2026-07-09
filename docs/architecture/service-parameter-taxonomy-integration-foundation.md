# Phase 51.1 - Service Parameter Taxonomy Integration Foundation

Phase 51.1 adds the metadata-only `service_parameter_taxonomies` collection and the `ServiceParameterTaxonomy` model family.

The purpose is to define measurable service-policy parameters that can be reused across the current Chapter 50/51 architecture:

- knowledge acquisition
- operational constraints
- knowledge normalisation and governance
- capability matrix records
- operational evaluations
- passenger service feasibility records
- airline recommendations
- intelligent offer packages
- operational intelligence cases

## Core Boundary

Service Parameter Taxonomies define fields that other operational objects may use. They do not merge Policy, Pricing, Capability, Constraints, or Procedures.

Policy remains separate from Capability. Pricing remains separate from Capability and Policy. Constraints remain the metadata language for future applicability, and Procedures remain operational handling guidance.

Phase 51.1 does not copy a legacy standalone policy engine. It does not introduce an old standalone `airline_policies` collection, an old `policy_evaluations` collection, PocketBase logic, `airlinePolicyEngine.js`, or `pricingEngine.js`. It does not evaluate rules, calculate prices, run recommendations, call providers, use AI/LLM logic, run background workers, book, ticket, issue EMDs, or automatically send anything.

## Canonical Objects

- `ServiceParameterTaxonomy`
- `ServiceParameterTaxonomyCreate`
- `ServiceParameterTaxonomyUpdate`
- `ServiceParameterTaxonomyService`
- `service_parameter_taxonomies`
- `/api/platform/service-parameter-taxonomies`
- `/api/agencies/{agency_id}/service-parameter-taxonomies`
- `/platform/service-parameter-taxonomies`
- `/agency/service-parameter-taxonomies`

## Parameter Domains

The taxonomy records organize measurable metadata for:

- passenger assistance, including WCHR, WCHS, WCHC, WCOB, MAAS, MEDA, MEDIF, STCR, OXYG, POC, UMNR, YP, EXST, and CBBG
- pets and animals, including PETC, AVIH, SVAN, and ESAN
- special items and baggage, including SPEQ, BIKE, SKI, GOLF, SURF, DIVE, MUSI, FRAGILE, VALUABLE, CBBG, EXST, WEAP, and special baggage
- route, aircraft, airport, country, cabin, seat, and aircraft-family metadata
- pricing parameter metadata such as unit, way, route type, flight type, fare bundle, amount type, basis, formula components, applicability, refund conditions, and exchange conditions

## Operational Use

Taxonomies prepare the system for structured knowledge entry, future scenario testing, and real airline data population. They provide consistent measurable fields for human-reviewed records without making operational decisions.

Human authority remains final.

## Phase 51.2 Relationship

Phase 51.2 adds `request_segment_service_scopes` as segment-first intake metadata that may reference Service Parameter Taxonomies through `service_parameter_taxonomy_ids`. The scope records passenger + segment + service context, including pet and special item metadata, but it does not evaluate the taxonomy, calculate pricing, book, ticket, issue EMDs, call providers, generate AI/LLM output, run workers, send automatically, or convert trips automatically.

## Reference Data Engine Alignment

Phase 52.1 adds `reference_data_domains` as governed domain metadata that Service Parameter Taxonomies may reference for allowed values, aliases, normalization rules, validation rules, and import-template references.

## Visual Policy Editor Alignment

Phase 52.3 adds `visual_policy_editor_cards` as no-code airline service policy-card metadata. Cards may reference Service Parameter Taxonomies through `service_parameter_taxonomy_links`, but they do not execute policy logic, evaluate rules, calculate pricing, call providers, generate AI/LLM output, run workers, or replace human review.

Reference Data Domains are not parameter taxonomies and do not evaluate rules, calculate prices, call providers, generate AI/LLM output, run workers, or automate operational decisions. Human authority remains final for both taxonomy governance and reference-domain governance.
