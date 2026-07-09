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
Phase 41.6 adds booking workspace APIs only under `/api/platform/booking-workspaces/*` and `/api/agencies/{agency_id}/booking-workspaces/*`, plus frontend pages under `/platform/booking-workspaces` and `/agency/booking-workspaces`. It uses the existing agency booking-workspace root for read-only metadata views while leaving prior explicit booking mirror action subroutes in place. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, live booking creation, ticket issuance, GDS connectivity, NDC connectivity, airline APIs, payment processing, fare calculation, AI, background workers, automatic booking confirmation, automatic ticket generation, external integrations, external APIs, or automation.
Phase 41.7 adds ticket workspace APIs only under `/api/platform/ticket-workspaces/*` and `/api/agencies/{agency_id}/ticket-workspaces/*`, plus frontend pages under `/platform/ticket-workspaces` and `/agency/ticket-workspaces`. It stores separate whole-ticket document status, per-coupon travel/usage status, fare construction, pricing unit, fare component, tax, and payment reference metadata only. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, ticket issuance, ticket reissue, voiding, refunds, exchanges, payment processing, GDS connectivity, NDC connectivity, airline APIs, fare calculation, fare recalculation, automated ticket validation, coupon validation, background workers, external integrations, external APIs, or automation.
Phase 41.8 adds EMD workspace APIs only under `/api/platform/emd-workspaces/*` and `/api/agencies/{agency_id}/emd-workspaces/*`, plus frontend pages under `/platform/emd-workspaces` and `/agency/emd-workspaces`. It stores EMD document status, EMD-A/EMD-S metadata, associated ticket/coupon/flight links, SSR/OSI links, RFIC/RFISC service metadata, coupon details, amounts, tax/payment metadata, exchange/refund/void references, lifecycle notes, and operational notes only. It does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, EMD issuance, EMD exchange, EMD refund, EMD voiding, RFIC/RFISC validation engines, SSR/OSI transmission, payment processing, GDS connectivity, NDC connectivity, airline APIs, background workers, external integrations, external APIs, duplicate EMD architecture, or automation.
Phase 50.0 adds AOIE architecture APIs only under `/api/platform/airline-operational-intelligence/*` and `/api/agencies/{agency_id}/airline-operational-intelligence/*`, plus frontend pages under `/platform/airline-operational-intelligence` and `/agency/operational-intelligence`. It is read-only architecture metadata and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, AI generation, airline scraping, automatic web crawling, live airline APIs, provider integrations, pricing engine execution, itinerary search, booking execution, ticket issuance, EMD issuance, recommendation automation, background workers, external API calls, or automation.
Phase 41.9 adds SSR / OSI operational workspace APIs only under `/api/platform/ssr-osi-workspaces/*` and `/api/agencies/{agency_id}/ssr-osi-workspaces/*`, plus frontend pages under `/platform/ssr-osi-workspaces` and `/agency/passenger-services`. It records passenger service operation metadata only and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, live SSR transmission, live OSI transmission, GDS connectivity, NDC connectivity, airline APIs, AI recommendation, automatic airline approval, automatic EMD issuance, background workers, provider integrations, external API calls, or automation.
Phase 42.0 adds document workspace APIs only under `/api/platform/document-workspaces/*` and `/api/agencies/{agency_id}/document-workspaces/*`, plus frontend pages under `/platform/document-workspaces` and `/agency/document-workspaces`. It records operational document workspace metadata only, does not duplicate the Phase 36.5 render/package/share foundation, and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, live document delivery, e-signature, public share links, automatic PDF generation, payment or invoice generation, external storage integrations, background workers, AI document generation, external API calls, or automation.
Phase 42.1 adds operational timeline APIs only under `/api/platform/operational-timelines/*` and `/api/agencies/{agency_id}/operational-timelines/*`, plus frontend pages under `/platform/operational-timelines` and `/agency/timeline`. It records operational history and communication-summary metadata only and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, email sending, SMS sending, WhatsApp, Teams, Slack, live airline messaging, live customer messaging, AI summarization, background workers, provider integrations, external API calls, or automation.
Phase 42.2 adds passenger service workflow APIs only under `/api/platform/passenger-service-workflows/*` and `/api/agencies/{agency_id}/passenger-service-workflows/*`, plus frontend pages under `/platform/passenger-service-workflows` and `/agency/workflow-engine`. It records workflow coordination metadata only and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, automatic workflow execution, AI decision making, background workers, airline APIs, GDS/NDC connectivity, automatic approvals, ticketing, EMD issuance, messaging, provider integrations, external API calls, or automation.
Phase 50.1 adds airline knowledge acquisition APIs only under `/api/platform/airline-knowledge-acquisition/*` and `/api/agencies/{agency_id}/airline-knowledge-acquisition/*`, plus frontend pages under `/platform/airline-knowledge-acquisition` and `/agency/knowledge-acquisition`. It records manually entered Airline Operational Knowledge Graph metadata only, including evidence, policy, pricing, capability, and operational constraint pillars, and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, AI parsing, automatic extraction, scraping, crawling, airline website automation, provider integrations, live airline APIs, recommendation engines, feasibility engines, pricing calculation engines, background workers, parser execution, external API calls, or automation.
Phase 50.2 adds operational constraint APIs only under `/api/platform/operational-constraints/*` and `/api/agencies/{agency_id}/operational-constraints/*`, plus frontend pages under `/platform/operational-constraints` and `/agency/operational-constraints`. It records metadata-only AOIE condition groups, supported operators, outcomes, applicability, priority, governance, future evaluation notes, and operational links, and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, live rule execution, AI reasoning, recommendation engines, feasibility scoring, pricing calculation, parser execution, scraping, background workers, provider integrations, external API calls, evaluation endpoints, or automation.
Phase 50.3 adds airline knowledge normalisation APIs only under `/api/platform/airline-knowledge-normalisation/*` and `/api/agencies/{agency_id}/airline-knowledge-normalisation/*`, plus frontend pages under `/platform/airline-knowledge-normalisation` and `/agency/knowledge-normalisation`. It records canonical operational vocabulary and taxonomy metadata only, and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, live evaluation, AI parsing, recommendation engines, feasibility scoring, pricing calculation, scraping, background workers, provider integrations, external API calls, or automation.
Phase 50.4 adds airline operational knowledge governance APIs only under `/api/platform/airline-knowledge-governance/*` and `/api/agencies/{agency_id}/airline-knowledge-governance/*`, plus frontend pages under `/platform/airline-knowledge-governance`, `/platform/airline-knowledge-releases`, and `/agency/knowledge-governance`. It records lifecycle, version, release, comparison, rollback, superseded, archived, and historical metadata only, and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, live rule evaluation, AI reasoning, parser execution, recommendation engines, pricing calculation, provider integrations, background workers, automatic publication, external API calls, or automation.
Phase 50.5 adds airline operational capability matrix APIs only under `/api/platform/airline-capability-matrix/*` and `/api/agencies/{agency_id}/airline-capability-matrix/*`, plus frontend pages under `/platform/airline-capability-matrix` and `/agency/capability-matrix`. It records operational capability inventory metadata only, and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, live rule evaluation, passenger feasibility scoring, airline recommendation ranking, AI reasoning, parser execution, pricing calculation, provider integrations, background workers, scraping, automatic publication, external API calls, or automation.
Phase 50.6 adds operational knowledge evaluation APIs only under `/api/platform/operational-evaluations/*` and `/api/agencies/{agency_id}/operational-evaluations/*`, plus frontend pages under `/platform/operational-evaluations` and `/agency/operational-evaluations`. It records deterministic, explainable, evidence-backed evaluation metadata only, and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, AI reasoning, LLM prompts, flight search, itinerary recommendation, passenger feasibility scoring, booking, ticketing, provider integrations, parser execution, pricing optimisation, background workers, external API calls, or automation.
Phase 50.7 adds passenger service feasibility APIs only under `/api/platform/passenger-service-feasibility/*` and `/api/agencies/{agency_id}/passenger-service-feasibility/*`, plus frontend pages under `/platform/passenger-service-feasibility` and `/agency/service-feasibility`. It records advisory, explainable, evidence-linked, non-Boolean feasibility metadata only, and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, airline recommendation ranking, flight search, booking, ticketing, live provider integrations, AI or LLM reasoning, parser execution, pricing optimisation, background workers, external API calls, or automatic operational decisions.
Phase 50.8 adds airline recommendation APIs only under `/api/platform/airline-recommendations/*` and `/api/agencies/{agency_id}/airline-recommendations/*`, plus frontend pages under `/platform/airline-recommendations` and `/agency/recommendations`. It records advisory airline and itinerary recommendation metadata only, and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, live GDS search, NDC search, flight booking, ticket issuance, EMD issuance, provider APIs, parser execution, AI or LLM generation, price generation, background workers, external API calls, or automation.
Phase 50.9 adds intelligent offer builder integration APIs only under `/api/platform/intelligent-offer-builder/*` and `/api/agencies/{agency_id}/offer-intelligence/*`, plus frontend pages under `/platform/intelligent-offer-builder` and `/agency/offer-intelligence`. It records offer-intelligence package metadata only, and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, live GDS search, NDC search, booking, ticketing, EMD issuance, provider APIs, parser execution, AI or LLM generation, price generation, background workers, automatic client sending, external API calls, or automation.
Phase 51.0 adds operational intelligence case APIs only under `/api/platform/operational-intelligence-cases/*` and `/api/agencies/{agency_id}/intelligence-cases/*`, plus frontend pages under `/platform/operational-intelligence-cases` and `/agency/intelligence-cases`. It records Chapter 50 pipeline consolidation metadata only, adds no new intelligence, and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, live flight search, booking, ticketing, EMD issuance, provider integrations, parser execution, AI or LLM generation, background workers, automatic client sending, external API calls, or automation.
Phase 51.1 adds service parameter taxonomy APIs only under `/api/platform/service-parameter-taxonomies/*` and `/api/agencies/{agency_id}/service-parameter-taxonomies/*`, plus frontend pages under `/platform/service-parameter-taxonomies` and `/agency/service-parameter-taxonomies`. It records reusable measurable service parameter metadata only, and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, live rule evaluation, live pricing calculation, recommendation execution, provider integrations, AI or LLM generation, background workers, duplicate operational models, or automation.
Phase 51.2 adds request segment service APIs only under `/api/platform/request-segment-services/*` and `/api/agencies/{agency_id}/request-segment-services/*`, plus frontend pages under `/platform/request-segment-services` and `/agency/request-segment-services`. It records segment-first passenger + segment + service metadata only, keeps requests as intake and trips as operational dossiers, and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, policy evaluation, pricing calculation, live flight search, booking, ticketing, EMD issuance, provider integrations, AI or LLM generation, background workers, automatic client sending, automatic trip conversion, or automation.
Phase 51.3 adds client/passenger master APIs only under `/api/platform/client-master`, `/api/platform/passenger-master`, `/api/agencies/{agency_id}/client-master`, and `/api/agencies/{agency_id}/passenger-master`, plus child metadata routes for links, service history, preferences, known documents, and portal access profiles. Frontend pages live under `/platform/client-master`, `/platform/passenger-master`, `/agency/clients`, and `/agency/passengers`. It records Client as commercial owner and Passenger as reusable operational identity, supports many-to-many metadata, and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, CRM sales pipeline behavior, marketing automation, provider integrations, AI/LLM generation, booking, ticketing, payment gateway processing, background workers, automatic client sending, or automation.
Phase 52.1 adds reference data engine APIs only under `/api/platform/reference-data-engine/*` and `/api/agencies/{agency_id}/reference-data-engine/*`, plus frontend pages under `/platform/reference-data-engine` and `/agency/reference-data-engine`. It records metadata-only reference domains for airline operational knowledge production and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, provider integrations, AI/LLM generation, live evaluation, pricing calculation, booking, ticketing, background workers, old admin routes, or automation.

Phase 52.2 adds knowledge import template APIs only under `/api/platform/knowledge-import-templates/*` and `/api/agencies/{agency_id}/knowledge-import-templates/*`, plus frontend pages under `/platform/knowledge-import-templates` and `/agency/import-templates`. It records reusable import-template metadata and does not add parsing execution, scraping, AI/LLM generation, background workers, provider integrations, automatic imports, redirects, aliases, `/admin`, `/agent`, `/api/admin`, or `/api/agent` routes.

Phase 52.3 adds visual policy editor APIs only under `/api/platform/visual-policy-editor/*` and `/api/agencies/{agency_id}/policy-editor/*`, plus frontend pages under `/platform/visual-policy-editor` and `/agency/policy-editor`. It records metadata-only airline service policy cards and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, policy execution, rule evaluation, pricing calculation, provider integrations, AI/LLM generation, background workers, or automation.

Phase 52.4 adds pricing formula builder APIs only under `/api/platform/pricing-formula-builder/*` and `/api/agencies/{agency_id}/pricing-formula-builder/*`, plus frontend pages under `/platform/pricing-formula-builder` and `/agency/pricing-formula-builder`. It records metadata-only pricing formula metadata and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, live price calculation, payment integrations, provider integrations, AI/LLM generation, background workers, automatic client sending, or automation.

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
| `/admin/booking-workspaces` | `/platform/booking-workspaces` |
| `/agent/booking-workspaces` | `/agency/booking-workspaces` |
| `/admin/ticket-workspaces` | `/platform/ticket-workspaces` |
| `/agent/ticket-workspaces` | `/agency/ticket-workspaces` |
| `/admin/emd-workspaces` | `/platform/emd-workspaces` |
| `/agent/emd-workspaces` | `/agency/emd-workspaces` |
| `/admin/ssr-osi-operations` | `/platform/ssr-osi-workspaces` |
| `/agent/passenger-services` | `/agency/passenger-services` |
| `/admin/document-workspaces` | `/platform/document-workspaces` |
| `/agent/document-workspaces` | `/agency/document-workspaces` |
| `/admin/operational-timelines` | `/platform/operational-timelines` |
| `/agent/timeline` | `/agency/timeline` |
| `/admin/passenger-service-workflows` | `/platform/passenger-service-workflows` |
| `/agent/workflow-engine` | `/agency/workflow-engine` |
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
| `/admin/airline-operational-intelligence` | `/platform/airline-operational-intelligence` |
| `/agent/operational-intelligence` | `/agency/operational-intelligence` |
| `/admin/airline-knowledge-acquisition` | `/platform/airline-knowledge-acquisition` |
| `/agent/knowledge-acquisition` | `/agency/knowledge-acquisition` |
| `/admin/airline-knowledge-normalisation` | `/platform/airline-knowledge-normalisation` |
| `/agent/knowledge-normalisation` | `/agency/knowledge-normalisation` |
| `/admin/airline-knowledge-governance` | `/platform/airline-knowledge-governance` |
| `/admin/airline-knowledge-releases` | `/platform/airline-knowledge-releases` |
| `/agent/knowledge-governance` | `/agency/knowledge-governance` |
| `/admin/airline-capability-matrix` | `/platform/airline-capability-matrix` |
| `/agent/capability-matrix` | `/agency/capability-matrix` |
| `/admin/operational-evaluations` | `/platform/operational-evaluations` |
| `/agent/operational-evaluations` | `/agency/operational-evaluations` |
| `/admin/passenger-service-feasibility` | `/platform/passenger-service-feasibility` |
| `/agent/service-feasibility` | `/agency/service-feasibility` |
| `/admin/airline-recommendations` | `/platform/airline-recommendations` |
| `/agent/recommendations` | `/agency/recommendations` |
| `/admin/intelligent-offer-builder` | `/platform/intelligent-offer-builder` |
| `/agent/offer-intelligence` | `/agency/offer-intelligence` |
| `/admin/operational-intelligence-cases` | `/platform/operational-intelligence-cases` |
| `/agent/intelligence-cases` | `/agency/intelligence-cases` |
| `/admin/reference-data-engine` | `/platform/reference-data-engine` |
| `/agent/reference-data-engine` | `/agency/reference-data-engine` |
| `/agent/reference-data` | `/agency/reference-data-engine` |
| `/admin/service-parameter-taxonomies` | `/platform/service-parameter-taxonomies` |
| `/agent/service-parameter-taxonomies` | `/agency/service-parameter-taxonomies` |
| `/admin/request-segment-services` | `/platform/request-segment-services` |
| `/agent/request-segment-services` | `/agency/request-segment-services` |
| `/admin/client-master` | `/platform/client-master` |
| `/admin/passenger-master` | `/platform/passenger-master` |
| `/agent/passengers` | `/agency/passengers` |
| `/documents` | `/agency/documents` and `/platform/document-templates` |
| `/tickets` | `/agency/tickets-emds` |
| `/bookings` | `/agency/booking-workspaces` |
| `/changes` or `/exchanges` | `/agency/trips/{trip_id}` changes panel and `/agency/tickets-emds` exchange actions |

## Boundary

This policy does not redesign the app shell, introduce new route roots, or change existing tenant authorization. It records that `/platform` and `/agency` are the canonical user-facing roots for AeroAssist AgencyOS.
