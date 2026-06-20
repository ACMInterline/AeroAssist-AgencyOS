# Review Notes

## Files Inspected

- `PRODUCT_SPEC.md`
- `CANONICAL_DATA_MODEL.md`
- `WORKFLOWS.md`
- `AIRLINE_INTELLIGENCE_MODEL.md`
- `PERMISSIONS_AND_TENANCY.md`
- `BUILD_PHASES.md`
- `NAVIGATION_MODEL.md`
- `OPEN_QUESTIONS.md`

## Contradictions Found

- `WORKFLOWS.md` allowed client self-registration to create an `active` or verification-pending account, but the canonical account status list did not include verification-pending. This has been resolved with `client_account.portal_status = email_unverified`.
- The specs correctly state that requests and offers are optionally linked, but the relationship cardinality and lifecycle rules were not explicit enough for implementation.
- Snapshot rules existed in multiple docs, but workflow-specific timing for booking, ticket, EMD, invoice, refund/exchange, payment, and document events was not precise enough.
- Agency airline overrides were defined as private and layered over global knowledge, but override precedence and conflict behavior were underspecified.
- Platform support access was mentioned, but edit boundaries and audit expectations were too broad for safe tenant isolation.

## Fixes Made

- Added required relationship and foreign-key contract to `CANONICAL_DATA_MODEL.md`.
- Added source-of-truth boundaries for global, agency, and portal-entered data to `CANONICAL_DATA_MODEL.md`.
- Added immutable snapshot payload rules to `CANONICAL_DATA_MODEL.md`.
- Added cross-record lifecycle rules and workflow snapshot timing to `WORKFLOWS.md`.
- Added known workflow gaps that must be resolved before build to `WORKFLOWS.md`.
- Added missing permission decisions, platform support access limits, and portal visibility rules to `PERMISSIONS_AND_TENANCY.md`.
- Added override precedence, conflict handling, ownership guardrails, and flexible-layer governance to `AIRLINE_INTELLIGENCE_MODEL.md`.
- Added MVP scope risks, recommended first vertical slice, premature modules to defer, and phase dependencies to `BUILD_PHASES.md`.
- Added must-resolve pre-database questions to `OPEN_QUESTIONS.md`.

## Remaining Open Questions

- Exact status enums across all operational records.
- Exact legal and policy behavior after verification may vary by agency, but the account status itself is resolved as `email_unverified` before activation.
- Whether client profiles combine people and organizations or use separate models.
- Whether multiple portal users can belong to one organization client in MVP.
- Passenger merge, duplicate handling, and legal identity approval rules.
- Invoice and payment capabilities: manual invoices, unapplied payments, partial payments, split payments, and multi-currency.
- Whether refund and exchange remain one combined model or split into specialized models.
- Sensitive document retention, archive, deletion, and portal visibility rules.
- Launch schemas and vocabularies for flexible airline knowledge layers.
- Final committed MVP slice versus full MVP list.

## Database Implementation Readiness

- Status enums, tenant isolation strategy, relationship constraints, snapshot payload requirements, client/person/organization modeling, verification-pending behavior, passenger merge rules, MVP financial allocation rules, document visibility/retention classes, and airline override schema are now resolved at architecture level.
- Database implementation may begin for the first vertical slice if the team accepts the remaining product/legal questions as configurable or non-blocking.
- Do not implement market-specific retention/deletion automation until legal retention periods are finalized.
- Do not implement payment provider automation, accounting exports, or multi-currency invoice behavior in MVP.
- Do not implement broad airline flexible-layer publishing until schema validators are defined for the first launch domains.

## Blockers Resolved In Architecture Decision Pass

- Status enums: resolved in `CANONICAL_DATA_MODEL.md`.
- Tenant isolation strategy: resolved with mandatory `agency_id` on agency-owned tables and controlled access to platform-owned global records.
- Snapshot payloads: resolved by milestone in `CANONICAL_DATA_MODEL.md`.
- Verification-pending account behavior: resolved as `client_account.portal_status = email_unverified`.
- Client/person vs organization modeling: resolved with `client_profile.client_type` and separate passenger profiles.
- Passenger merge rules: resolved as same-agency, admin/owner-only, audited, non-destructive merge.
- Financial allocation rules: resolved as invoice/payment/refund tracking only, not full accounting.
- Document retention and visibility rules: resolved with owner, linked entity, visibility flags, retention classes, archive/delete rules, and sensitive document handling.
- Airline override schemas: resolved with typed `agency_airline_override` envelope and replace/augment/annotate modes.

## Remaining Non-Blocking Questions

- Launch website publishing model: hosted subdomain, custom domains, or both.
- Exact launch airline/domain coverage.
- Exact legal retention periods by market.
- Exact uniqueness rules for PNR, invoice number, ticket number, EMD number, and passenger document records.
- Schema validators for the first airline knowledge and agency override structured payloads.
- Tenant isolation test matrix.

## Recommended First Build Phase

Build the first usable vertical slice after Phase 0 in this order:

1. Multi-tenant identity and agency workspace foundation.
2. Client/passenger CRM with many-to-many relationship permissions.
3. Basic request capture, messages, tasks, and timeline.
4. Manual offer builder with up to three route alternatives and three fare bundles per route.
5. Fixed-template branded document output and offer snapshots.

This validates the core AgencyOS workflow before expanding into full website/CMS publishing, deep airline intelligence editing, refund/exchange servicing, payment automation, or advanced document-template tooling.
