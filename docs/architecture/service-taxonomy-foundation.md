# Service Taxonomy Foundation

Phase 36.8 adds the canonical special/ancillary service taxonomy foundation for AeroAssist AgencyOS.

## Purpose

The taxonomy maps airline-specific service names, commercial labels, SSR/GDS codes, NDC/internal labels, and reviewed policy wording into normalized service domains, families, and variants.

It prepares future use in request guidance, offer builder checks, booking readiness, booking/PNR mirrors, ticket/EMD mirrors, documents, GDS/parser workflows, policy comparison, and future SSR/OSI/EMD/RFIC/RFISC mapping.

## Data Model

Core global taxonomy records:

- `CanonicalServiceDomain`
- `CanonicalServiceFamily`
- `CanonicalServiceVariant`
- `ServiceApplicabilityDimension`
- `ServicePolicyOutcomeType`

Mapping and review records:

- `AirlineServiceAlias`
- `ServiceTaxonomyMappingRule`
- `PolicyCandidateTaxonomyLink`
- `ServiceTaxonomyReviewCorrection`

The taxonomy is explicitly separate from `ServiceCatalogueRecord`. The service catalogue remains the operational service catalogue used by request, offer, booking readiness, documents, and EMD mirror workflows. The taxonomy normalizes service meaning across airlines and policy sources.

## Deterministic Mapping

`ServiceTaxonomyService` performs conservative deterministic mapping only:

- lowercase, strip punctuation, and collapse whitespace
- exact alias match
- exact SSR/GDS code match
- exact mapping rule match
- contains mapping rule match
- token mapping rule match
- guarded simple regex matching
- fallback to `needs_review` / `unknown_review_required`

There are no external AI calls, no airline website scraping, and no live provider calls.

## Governance

Platform owns global taxonomy records and baseline seed data through `/api/platform/service-taxonomy/*` and `/platform/service-taxonomy`.

Agencies can browse global taxonomy through `/api/agencies/{agency_id}/service-taxonomy/*` and `/agency/service-taxonomy`. Agencies can map candidate text, create agency-local candidate taxonomy links, and record agency-local corrections.

Agencies cannot create, update, archive, or auto-promote global domains, families, variants, aliases, dimensions, outcome types, or mapping rules. Agency corrections may request promotion, but promotion remains pending until platform review.

## Phase 36.7 Integration

`PolicyCandidateTaxonomyLink` can reference Phase 36.7 records from:

- `airline_policy_extracted_rules`
- `airline_policy_extracted_prices`
- `airline_policy_extracted_communication_rules`
- `airline_policy_extracted_emd_rules`
- `airline_policy_extracted_exceptions`
- `airline_policy_approved_knowledge_records`

Phase 36.8 does not destructively alter Phase 36.7 collections.

## Boundaries

Phase 36.8 does not implement:

- full SSR/OSI instruction mapping
- EMD/RFIC/RFISC payment mechanics
- normalized ancillary pricing matrices
- policy comparison matrix
- live GDS/NDC/provider connectivity
- live booking, ticketing, EMD issuance, exchange, refund, void, payment, invoice, accounting, BSP/ARC, or settlement
- external AI taxonomy mapping
- airline scraping
- agency auto-promotion into global taxonomy
- `/agent/*` or `/admin/*` routes

Phase 36.9 is expected to handle SSR/OSI and EMD/RFIC/RFISC mapping foundations. Phase 37.0 is expected to handle pricing schema and exception matrix foundations.
