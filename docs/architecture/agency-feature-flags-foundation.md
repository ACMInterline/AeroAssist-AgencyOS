# Agency Feature Flags Foundation

Phase 39.7 adds metadata-only agency feature flag records so Platform Console owners can describe feature visibility independently of subscription plans.

Phase 39.8 builds on these records with read-only audit history and readiness checklist metadata documented in `docs/architecture/agency-feature-flag-audit-foundation.md`.

## Scope

The foundation records:

- `AgencyFeatureFlag` for agency/module/feature visibility states.
- `AgencyFeatureFlagReview` for platform review notes.
- `AgencyFeatureFlagSnapshot` for immutable visibility snapshots.

Feature flags are informational metadata. They do not enforce permissions, block routes, bill, charge, publish, execute providers, book, mutate PNRs, ticket, issue EMDs, scrape, call external APIs, call external AI, or send automatically.

## States

Feature visibility can be one of:

- `enabled`
- `disabled`
- `hidden`
- `beta`
- `pilot`

These states are badges and review hints only. Operational enforcement is not performed.

## APIs

Platform Console APIs:

- `GET /api/platform/feature-flags/summary`
- `GET /api/platform/feature-flags/flags`
- `POST /api/platform/feature-flags/flags`
- `PATCH /api/platform/feature-flags/flags/{flag_id}`
- `GET /api/platform/feature-flags/reviews`
- `POST /api/platform/feature-flags/reviews`
- `GET /api/platform/feature-flags/snapshots`
- `POST /api/platform/feature-flags/snapshots`

Agency Workspace read-only APIs:

- `GET /api/agencies/{agency_id}/feature-flags/summary`
- `GET /api/agencies/{agency_id}/feature-flags/flags`
- `GET /api/agencies/{agency_id}/feature-flags/reviews`

Agency APIs are read-only and return visibility metadata plus disabled safety flags.

## UI

Platform Console adds `Platform -> Feature Flags` at `/platform/feature-flags` for owner review metadata.

Agency Workspace adds `Agency -> Feature Availability` at `/agency/feature-availability` with badges for Enabled, Disabled, Hidden, Beta, and Pilot.

Both surfaces show:

`Feature visibility is informational only. Operational enforcement is not performed.`

## Readiness

`/api/readiness` exposes `agency_feature_flags_foundation` with enabled metadata flags for feature flags, review notes, snapshots, platform review, and agency read-only visibility. It also exposes disabled flags for automatic enforcement, billing, payments, provider execution, booking, PNR mutation, ticketing, EMD issuance, CMS publishing, client portal publishing, external API calls, external AI, scraping, automatic sending, and feature blocking. `readiness_required` remains `false`.

## Route Boundary

Phase 39.7 preserves canonical `/platform/*`, `/agency/*`, `/api/platform/*`, and `/api/agencies/{agency_id}/*` routes. It does not add `/admin`, `/agent`, `/api/admin`, or `/api/agent` routes.
