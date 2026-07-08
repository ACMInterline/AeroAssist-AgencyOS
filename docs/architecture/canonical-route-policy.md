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

No redirects or aliases are added in Phase 36.4.5, Phase 36.4.6, Phase 36.5, Phase 36.6, Phase 36.7, Phase 36.8, Phase 36.9, Phase 37.0, Phase 37.1, Phase 37.2, Phase 37.3, Phase 37.4, Phase 37.5, Phase 37.6, Phase 37.7, Phase 37.8, Phase 37.9, Phase 38.0, Phase 38.1, Phase 38.2, Phase 39.0, Phase 39.1, Phase 39.2, Phase 39.3, Phase 39.4, Phase 39.5, Phase 39.6, Phase 39.7, Phase 39.8, Phase 39.9, Phase 40.0, Phase 40.1, Phase 40.2, Phase 40.3, or Phase 40.4. Documentation and API/UI mapping are preferred so future work remains explicit.

Phase 39.4 changes visible navigation wording and helper descriptions only. It keeps all route paths under the existing `/platform/*` and `/agency/*` roots.
Phase 39.5 adds subscription APIs only under `/api/platform/saas-subscriptions/*` and `/api/agencies/{agency_id}/saas-subscriptions/*`, plus frontend pages under `/platform/saas-subscriptions` and `/agency/saas-subscription`.
Phase 39.6 adds read-only entitlement visibility APIs under the same subscription route families: `/api/platform/saas-subscriptions/entitlement-visibility` and `/api/agencies/{agency_id}/saas-subscriptions/module-visibility`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent`.
Phase 39.7 adds feature flag APIs only under `/api/platform/feature-flags/*` and `/api/agencies/{agency_id}/feature-flags/*`, plus frontend pages under `/platform/feature-flags` and `/agency/feature-availability`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent`.
Phase 39.8 adds read-only feature flag audit and readiness APIs only under `/api/platform/feature-flags/audits`, `/api/platform/feature-flags/readiness`, and `/api/agencies/{agency_id}/feature-readiness/*`, plus frontend pages under `/platform/feature-flag-audit` and `/agency/feature-readiness`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent`.
Phase 39.9 adds read-only feature flag bundle APIs only under `/api/platform/feature-flag-bundles/*` and `/api/agencies/{agency_id}/feature-flag-bundles/*`, plus frontend pages under `/platform/feature-flag-bundles` and `/agency/feature-bundles`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent`.
Phase 40.0 adds feature bundle assignment APIs only under `/api/platform/feature-bundle-assignments`, `/api/platform/agencies/{agency_id}/bundle-assignments`, `/api/platform/bundle-assignments/{assignment_id}`, `/api/agencies/{agency_id}/feature-bundle-assignments`, and `/api/agencies/{agency_id}/feature-bundle-assignment-history`, plus frontend pages under `/platform/feature-bundle-assignments` and `/agency/assigned-bundles`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent`.
Phase 40.1 adds feature bundle rollout readiness APIs only under `/api/platform/feature-bundle-rollout-readiness/*` and `/api/agencies/{agency_id}/feature-bundle-rollout-readiness/*`, plus frontend pages under `/platform/feature-bundle-rollout-readiness` and `/agency/bundle-rollout-readiness`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent`.
Phase 40.1 adds read-only capability catalog APIs only under `/api/platform/capabilities/*` and `/api/agencies/{agency_id}/capabilities/*`, plus frontend pages under `/platform/capabilities` and `/agency/capabilities`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent`.
Phase 40.2 adds feature bundle rollout plan APIs only under `/api/platform/feature-bundle-rollout-plans/*` and `/api/agencies/{agency_id}/feature-bundle-rollout-plans/*`, plus frontend pages under `/platform/feature-bundle-rollout-plans` and `/agency/rollout-plans`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent`.
Phase 40.3 adds read-only rollout dashboard APIs only under `/api/platform/rollout-dashboard/*` and `/api/agencies/{agency_id}/rollout-dashboard/*`, plus frontend pages under `/platform/rollout-dashboard` and `/agency/rollout-dashboard`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent`.
Phase 40.4 adds feature bundle rollout approval APIs only under `/api/platform/feature-bundle-rollout-approvals/*` and `/api/agencies/{agency_id}/feature-bundle-rollout-approvals/*`, plus frontend pages under `/platform/feature-bundle-rollout-approvals` and `/agency/rollout-approval`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent`.
Phase 40.5 adds feature bundle rollout schedule APIs only under `/api/platform/feature-bundle-rollout-schedule/*` and `/api/agencies/{agency_id}/feature-bundle-rollout-schedule/*`, plus frontend pages under `/platform/feature-bundle-rollout-schedule` and `/agency/rollout-schedule`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, cron jobs, schedulers, workers, queues, timers, or rollout execution.
Phase 40.6 adds feature bundle rollout timeline APIs only under `/api/platform/feature-bundle-rollout-timeline/*` and `/api/agencies/{agency_id}/feature-bundle-rollout-timeline/*`, plus frontend pages under `/platform/feature-bundle-rollout-timeline` and `/agency/rollout-timeline`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, background jobs, provider calls, publishing, notifications, subscription changes, automation, or rollout execution.
Phase 40.7 adds feature bundle dependency APIs only under `/api/platform/feature-bundle-dependencies/*` and `/api/agencies/{agency_id}/feature-bundle-dependencies/*`, plus frontend pages under `/platform/feature-bundle-dependencies` and `/agency/bundle-dependencies`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, dependency enforcement, rollout blocking, background jobs, notifications, provider calls, publishing, automation, or rollout execution.
Phase 40.8 adds feature bundle rollout risk APIs only under `/api/platform/feature-bundle-rollout-risks/*` and `/api/agencies/{agency_id}/feature-bundle-rollout-risks/*`, plus frontend pages under `/platform/feature-bundle-rollout-risks` and `/agency/rollout-risks`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, rollout execution, risk decision enforcement, blocking, notifications, bundle activation, automation, or provider calls.
Phase 40.9 adds feature bundle rollout issue APIs only under `/api/platform/feature-bundle-rollout-issues/*` and `/api/agencies/{agency_id}/feature-bundle-rollout-issues/*`, plus frontend pages under `/platform/feature-bundle-rollout-issues` and `/agency/rollout-issues`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, rollout execution, bundle activation, blocking enforcement, notifications, provider calls, AI/provider execution, or automation.
Phase 40.10 adds feature bundle rollout decision APIs only under `/api/platform/feature-bundle-rollout-decisions/*` and `/api/agencies/{agency_id}/feature-bundle-rollout-decisions/*`, plus frontend pages under `/platform/feature-bundle-rollout-decisions` and `/agency/rollout-decisions`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, rollout execution, deployment automation, feature activation, entitlement enforcement, billing, provider integrations, AI, external APIs, background workers, schedulers, notifications, email, webhooks, publishing, runtime switching, or automation.
Phase 40.11 adds feature bundle rollout change request APIs only under `/api/platform/feature-bundle-rollout-change-requests/*` and `/api/agencies/{agency_id}/feature-bundle-rollout-change-requests/*`, plus frontend pages under `/platform/feature-bundle-rollout-change-requests` and `/agency/rollout-change-requests`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, rollout execution, deployment automation, feature activation, entitlement enforcement, billing, provider integrations, AI, external APIs, background workers, schedulers, notifications, email, webhooks, publishing, runtime switching, or automation.
Phase 40.12 adds feature bundle rollout rollback plan APIs only under `/api/platform/feature-bundle-rollout-rollback-plans/*` and `/api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans/*`, plus frontend pages under `/platform/feature-bundle-rollout-rollback-plans` and `/agency/rollout-rollback-plans`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, actual rollback execution, deployment automation, feature activation/deactivation, entitlement enforcement, billing, provider integrations, AI, external APIs, background workers, schedulers, notifications, email, webhooks, publishing, runtime switching, or automation.
Phase 40.13 adds feature bundle rollout summary pack APIs only under `/api/platform/feature-bundle-rollout-summary-packs/*` and `/api/agencies/{agency_id}/feature-bundle-rollout-summary-packs/*`, plus frontend pages under `/platform/feature-bundle-rollout-summary-packs` and `/agency/rollout-summary-packs`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, rollout execution, deployment automation, feature activation/deactivation, entitlement enforcement, billing, provider integrations, AI, external APIs, background workers, schedulers, notifications, email, webhooks, publishing, runtime switching, PDF generation, file export, or automation.
Phase 41.0 adds operational travel workspace APIs only under `/api/platform/operational-travel-workspaces/*` and `/api/agencies/{agency_id}/operational-travel-workspaces/*`, plus frontend pages under `/platform/operational-travel-workspaces` and `/agency/travel-workspaces`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, booking execution, ticket issuance, live GDS or NDC connectivity, payment processing, email or SMS sending, AI automation, external APIs, supplier integrations, live airline calls, background workers, or automation.
Phase 41.1 adds travel request workspace APIs only under `/api/platform/travel-request-workspaces/*` and `/api/agencies/{agency_id}/travel-request-workspaces/*`, plus frontend pages under `/platform/travel-request-workspaces` and `/agency/travel-requests`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, booking execution, ticket issuance, live GDS or NDC connectivity, payment processing, email or SMS sending, AI automation, external APIs, supplier integrations, live airline calls, background workers, automatic conversion to trips, automatic offer creation, or automation.
Phase 41.2 adds passenger workspace APIs only under `/api/platform/passenger-workspaces/*` and `/api/agencies/{agency_id}/passenger-workspaces/*`, plus frontend pages under `/platform/passenger-workspaces` and `/agency/passenger-workspaces`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, booking execution, ticket issuance, GDS connectivity, NDC connectivity, payment processing, supplier integrations, AI, email, SMS, background workers, external APIs, automatic profile matching, automatic document validation, airline communication, or automation.
Phase 41.3 adds flight workspace APIs only under `/api/platform/flight-workspaces/*` and `/api/agencies/{agency_id}/flight-workspaces/*`, plus frontend pages under `/platform/flight-workspaces` and `/agency/flight-workspaces`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, booking execution, live flight search, GDS connectivity, NDC connectivity, airline APIs, payment, ticket issuance, schedule synchronization, external APIs, AI, background workers, automatic route generation, flight validation, airline lookups, live schedule updates, or automation.
Phase 41.4 adds trip workspace APIs only under `/api/platform/trip-workspaces/*` and `/api/agencies/{agency_id}/trip-workspaces/*`, plus frontend pages under `/platform/trip-workspaces` and `/agency/trip-workspaces`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, booking execution, ticket issuance, GDS connectivity, NDC connectivity, airline APIs, payment processing, invoicing, AI, background workers, automatic trip generation, automatic itinerary generation, external integrations, external APIs, or automation.
Phase 41.5 adds offer workspace APIs only under `/api/platform/offer-workspaces/*` and `/api/agencies/{agency_id}/offer-workspaces-v2/*`, plus frontend pages under `/platform/offer-workspaces` and `/agency/offer-workspaces`. The v2 agency API path avoids colliding with the existing offer-builder workspace APIs under `/api/agencies/{agency_id}/offer-workspaces/*`. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, booking execution, ticket issuance, payment processing, GDS connectivity, NDC connectivity, airline APIs, fare calculation engines, live pricing, AI itinerary generation, supplier integrations, external APIs, automatic booking conversion, background workers, or automation.

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
| `/admin/feature-bundle-assignments` | `/platform/feature-bundle-assignments` |
| `/agent/assigned-bundles` | `/agency/assigned-bundles` |
| `/admin/feature-bundle-dependencies` | `/platform/feature-bundle-dependencies` |
| `/agent/bundle-dependencies` | `/agency/bundle-dependencies` |
| `/admin/feature-bundle-rollout-risks` | `/platform/feature-bundle-rollout-risks` |
| `/agent/rollout-risks` | `/agency/rollout-risks` |
| `/admin/feature-bundle-rollout-issues` | `/platform/feature-bundle-rollout-issues` |
| `/agent/rollout-issues` | `/agency/rollout-issues` |
| `/admin/feature-bundle-rollout-decisions` | `/platform/feature-bundle-rollout-decisions` |
| `/agent/rollout-decisions` | `/agency/rollout-decisions` |
| `/admin/feature-bundle-rollout-change-requests` | `/platform/feature-bundle-rollout-change-requests` |
| `/agent/rollout-change-requests` | `/agency/rollout-change-requests` |
| `/admin/feature-bundle-rollout-rollback-plans` | `/platform/feature-bundle-rollout-rollback-plans` |
| `/agent/rollout-rollback-plans` | `/agency/rollout-rollback-plans` |
| `/admin/feature-bundle-rollout-summary-packs` | `/platform/feature-bundle-rollout-summary-packs` |
| `/agent/rollout-summary-packs` | `/agency/rollout-summary-packs` |
| `/admin/operational-travel-workspaces` | `/platform/operational-travel-workspaces` |
| `/agent/travel-workspaces` | `/agency/travel-workspaces` |
| `/admin/travel-request-workspaces` | `/platform/travel-request-workspaces` |
| `/agent/travel-requests` | `/agency/travel-requests` |
| `/admin/passenger-workspaces` | `/platform/passenger-workspaces` |
| `/agent/passenger-workspaces` | `/agency/passenger-workspaces` |
| `/admin/flight-workspaces` | `/platform/flight-workspaces` |
| `/agent/flight-workspaces` | `/agency/flight-workspaces` |
| `/admin/trip-workspaces` | `/platform/trip-workspaces` |
| `/agent/trip-workspaces` | `/agency/trip-workspaces` |
| `/admin/offer-workspaces` | `/platform/offer-workspaces` |
| `/agent/offer-workspaces` | `/agency/offer-workspaces` |
| `/admin/feature-bundle-rollout-readiness` | `/platform/feature-bundle-rollout-readiness` |
| `/agent/bundle-rollout-readiness` | `/agency/bundle-rollout-readiness` |
| `/admin/feature-bundle-rollout-plans` | `/platform/feature-bundle-rollout-plans` |
| `/agent/rollout-plans` | `/agency/rollout-plans` |
| `/admin/feature-bundle-rollout-approvals` | `/platform/feature-bundle-rollout-approvals` |
| `/agent/rollout-approval` | `/agency/rollout-approval` |
| `/admin/feature-bundle-rollout-schedule` | `/platform/feature-bundle-rollout-schedule` |
| `/agent/rollout-schedule` | `/agency/rollout-schedule` |
| `/admin/feature-bundle-rollout-timeline` | `/platform/feature-bundle-rollout-timeline` |
| `/agent/rollout-timeline` | `/agency/rollout-timeline` |
| `/admin/rollout-dashboard` | `/platform/rollout-dashboard` |
| `/agent/rollout-dashboard` | `/agency/rollout-dashboard` |
| `/admin/capabilities` | `/platform/capabilities` |
| `/agent/capabilities` | `/agency/capabilities` |
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
