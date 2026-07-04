# Canonical Route Policy

AgencyOS keeps the current route model. The supplementary `/agent/*` and `/admin/*` route roots are intentionally not adopted.

## Canonical Routes

| Route root | Purpose |
|---|---|
| `/platform/*` | Platform owner and global governance/configuration UI |
| `/agency/*` | Agency operational workspace UI |
| `/api/platform/*` | Platform owner governance APIs |
| `/api/agencies/{agency_id}/*` | Agency operational APIs |
| `/api/reference/*` | Shared consume APIs |

## Rejected Roots

| Supplementary root | Decision | Reason |
|---|---|---|
| `/agent/*` | intentionally rejected | Duplicates `/agency/*` and would split agency workflow navigation. |
| `/admin/*` | intentionally rejected | Duplicates `/platform/*` and would blur platform governance boundaries. |

No redirects or aliases are added in Phase 36.4.5, Phase 36.4.6, Phase 36.5, Phase 36.6, Phase 36.7, Phase 36.8, Phase 36.9, Phase 37.0, Phase 37.1, Phase 37.2, Phase 37.3, Phase 37.4, Phase 37.5, Phase 37.6, Phase 37.7, Phase 37.8, Phase 37.9, Phase 38.0, Phase 38.1, Phase 38.2, Phase 39.0, Phase 39.1, Phase 39.2, Phase 39.3, Phase 39.4, Phase 39.5, Phase 39.6, Phase 39.7, Phase 39.8, or Phase 39.9. Documentation and API/UI mapping are preferred so future work remains explicit.

Phase 39.4 changes visible navigation wording and helper descriptions only. It keeps all route paths under the existing `/platform/*` and `/agency/*` roots.
Phase 39.5 adds subscription APIs only under `/api/platform/saas-subscriptions/*` and `/api/agencies/{agency_id}/saas-subscriptions/*`, plus frontend pages under `/platform/saas-subscriptions` and `/agency/saas-subscription`.
Phase 39.6 adds read-only entitlement visibility APIs under the same subscription route families: `/api/platform/saas-subscriptions/entitlement-visibility` and `/api/agencies/{agency_id}/saas-subscriptions/module-visibility`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent`.
Phase 39.7 adds feature flag APIs only under `/api/platform/feature-flags/*` and `/api/agencies/{agency_id}/feature-flags/*`, plus frontend pages under `/platform/feature-flags` and `/agency/feature-availability`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent`.
Phase 39.8 adds read-only feature flag audit and readiness APIs only under `/api/platform/feature-flags/audits`, `/api/platform/feature-flags/readiness`, and `/api/agencies/{agency_id}/feature-readiness/*`, plus frontend pages under `/platform/feature-flag-audit` and `/agency/feature-readiness`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent`.
Phase 39.9 adds read-only feature flag bundle APIs only under `/api/platform/feature-flag-bundles/*` and `/api/agencies/{agency_id}/feature-flag-bundles/*`, plus frontend pages under `/platform/feature-flag-bundles` and `/agency/feature-bundles`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent`.

## Route Mapping

| Supplementary route | AgencyOS route |
|---|---|
| `/agent/clients` | `/agency/clients` |
| `/agent/trip-requests` | `/agency/requests` and `/agency/trips` |
| `/agent/parser` | `/agency/gds-parser` |
| `/agent/parser/imports` | `/agency/booking-imports` and `/agency/gds-parser` |
| `/admin/parser` | `/platform/gds-parser` |
| `/admin/exception-rules` | `/platform/rules-services` |
| `/admin/special-services` | `/platform/rules-services` |
| `/admin/service-taxonomy` | `/platform/service-taxonomy` |
| `/agent/service-taxonomy` | `/agency/service-taxonomy` |
| `/admin/service-mechanics` | `/platform/service-mechanics` |
| `/agent/service-mechanics` | `/agency/service-mechanics` |
| `/admin/ancillary-pricing` | `/platform/ancillary-pricing` |
| `/agent/ancillary-pricing` | `/agency/ancillary-pricing` |
| `/admin/policy-comparison` | `/platform/policy-comparison` |
| `/agent/policy-comparison` | `/agency/policy-comparison` |
| `/agent/service-advisor` | `/agency/airline-service-advisor` |
| `/admin/offer-advisor` | `/platform/offer-policy-advisor` |
| `/agent/offer-advisor` | `/agency/offer-policy-advisor` |
| `/admin/offer-decision-packs` | `/platform/offer-decision-packs` |
| `/agent/offer-decision-packs` | `/agency/offer-decision-packs` |
| `/admin/offer-decision-explanations` | `/platform/offer-decision-explanations` |
| `/agent/offer-decision-explanations` | `/agency/offer-decision-explanations` |
| `/admin/offer-decision-exports` | `/platform/offer-decision-exports` |
| `/agent/offer-decision-exports` | `/agency/offer-decision-exports` |
| `/admin/offer-decision-export-previews` | `/platform/offer-decision-export-previews` |
| `/agent/offer-decision-export-previews` | `/agency/offer-decision-export-previews` |
| `/admin/offer-decision-export-releases` | `/platform/offer-decision-export-releases` |
| `/agent/offer-decision-export-releases` | `/agency/offer-decision-export-releases` |
| `/admin/offer-decision-export-deliveries` | `/platform/offer-decision-export-deliveries` |
| `/agent/offer-decision-export-deliveries` | `/agency/offer-decision-export-deliveries` |
| `/admin/offer-decision-export-delivery-outcomes` | `/platform/offer-decision-export-delivery-outcomes` |
| `/agent/offer-decision-export-delivery-outcomes` | `/agency/offer-decision-export-delivery-outcomes` |
| `/admin/offer-decision-export-audit-reviews` | `/platform/offer-decision-export-audit-reviews` |
| `/agent/offer-decision-export-audit-reviews` | `/agency/offer-decision-export-audit-reviews` |
| `/admin/offer-decision-export-governance` | `/platform/offer-decision-export-governance` |
| `/agent/offer-decision-export-governance` | `/agency/offer-decision-export-governance` |
| `/admin/offer-decision-export-compliance` | `/platform/offer-decision-export-compliance` |
| `/agent/offer-decision-export-compliance` | `/agency/offer-decision-export-compliance` |
| `/admin/feature-flag-bundles` | `/platform/feature-flag-bundles` |
| `/agent/feature-bundles` | `/agency/feature-bundles` |
| `/admin/airline-data-packs` | `/platform/airline-intelligence-data-packs` |
| `/agent/airline-coverage` | `/agency/airline-intelligence-coverage` |
| `/admin/airline-data-pack-reviews` | `/platform/airline-intelligence-data-pack-reviews` |
| `/agent/airline-review-coverage` | `/agency/airline-intelligence-review-coverage` |
| `/admin/airline-knowledge-versions` | `/platform/airline-intelligence-knowledge-versions` |
| `/agent/airline-knowledge-versions` | `/agency/airline-intelligence-knowledge-versions` |
| `/admin/airline-agency-consumption` | `/platform/airline-intelligence-agency-consumption` |
| `/agent/airline-intelligence-usage` | `/agency/airline-intelligence-consumption` |
| `/documents` | `/agency/documents` and `/platform/document-templates` |
| `/tickets` | `/agency/tickets-emds` |
| `/bookings` | `/agency/booking-workspaces` |
| `/changes` or `/exchanges` | `/agency/trips/{trip_id}` changes panel and `/agency/tickets-emds` exchange actions |

## Boundary

This policy does not redesign the app shell, introduce new route roots, or change existing tenant authorization. It records that `/platform` and `/agency` are the canonical user-facing roots for AeroAssist AgencyOS.
