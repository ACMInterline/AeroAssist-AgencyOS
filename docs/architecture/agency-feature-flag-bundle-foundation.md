# Agency Feature Flag Bundle Foundation

Phase 39.9 adds reusable Feature Flag Bundle metadata for Platform Console review and Agency Workspace read-only visibility.

## Scope

The foundation records and displays bundle definitions such as:

- Core Agency
- CRM
- Ticketing
- Booking
- Airline Intelligence
- GDS
- Finance
- Premium Operations
- Beta Features
- Internal Testing

Bundles are grouping metadata only. They do not enable features, enforce access, hide modules, make permission decisions, change subscriptions, bill, publish, roll out changes, execute providers, call external APIs, scrape, call external AI, start background workers, send notifications, or send email.

## Models

Phase 39.9 introduces:

- `FeatureFlagBundle`
- `FeatureFlagBundleSummary`
- `FeatureFlagBundleReview`
- `FeatureFlagBundleMember`
- `BundleReadiness`

Persistent collections are:

- `agency_feature_flag_bundles`
- `agency_feature_flag_bundle_reviews`

The service also exposes default bundle definitions without writing them during read-only requests.

## Review Workflow

Platform Console owners can review reusable bundle metadata under `/platform/feature-flag-bundles`.

Agency Workspace users can view available feature bundle metadata under `/agency/feature-bundles`.

Both views are read-only. There are no toggles, publish actions, rollout controls, background workers, notifications, or operational execution paths.

## Relationship To Feature Flags

Feature flag bundles reference member `module_key` and `feature_key` values. They are not agency-specific feature state records and do not update `AgencyFeatureFlag` records.

Phase 39.7 remains the metadata-only source for agency-specific feature availability states. Phase 39.8 remains the metadata-only source for feature readiness and audit history. Phase 39.9 only groups feature keys into reusable bundle definitions for review and visibility.

## Relationship To Subscription Entitlements

Bundles are independent of subscription plans and entitlement metadata. They do not perform entitlement checks, subscription charging, plan assignment, access enforcement, or route blocking.

Subscription entitlement visibility remains informational under the Phase 39.5 and Phase 39.6 foundations.

## Future Enforcement Phases

Any future enforcement, rollout, percentage deployment, permission decision, subscription coupling, module hiding, or publishing behavior requires a separate explicit phase with its own authorization model, migration plan, route behavior, audit design, and tests.

## Route Boundary

Phase 39.9 preserves canonical `/platform/*`, `/agency/*`, `/api/platform/*`, and `/api/agencies/{agency_id}/*` routes.

It adds read-only APIs:

- `GET /api/platform/feature-flag-bundles`
- `GET /api/platform/feature-flag-bundles/{bundle_id}`
- `GET /api/platform/feature-flag-bundles/{bundle_id}/members`
- `GET /api/platform/feature-flag-bundles/reviews`
- `GET /api/agencies/{agency_id}/feature-flag-bundles`
- `GET /api/agencies/{agency_id}/feature-flag-bundles/{bundle_id}`

It does not add `/admin`, `/agent`, `/api/admin`, or `/api/agent` routes.
