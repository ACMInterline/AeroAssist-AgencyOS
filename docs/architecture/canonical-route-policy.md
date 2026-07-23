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

## Audit Event Access

- Canonical Platform review: `GET /api/platform/audit-events`, limited to Platform Owner and Platform Admin.
- Canonical Agency review: `GET /api/agencies/{agency_id}/audit-events`, limited to Agency Owner and Agency Admin for their own agency.
- Legacy `GET /api/audit-events` remains only as a deprecated Platform Owner/Admin compatibility alias and identifies the canonical replacement in its response.
- All audit reads are bounded, ordered newest first, and return a recursively redacted projection. Portal identities, Platform Support, unauthorized agency roles, anonymous callers, and cross-agency reads are rejected.
- Audit writes and stored source records are unchanged; read-time redaction never mutates audit history.

## Request Passenger Identity

- Unconfirmed traveler information remains on the agency-scoped `RequestPassenger` record.
- Explicit confirmation uses `POST /api/agencies/{agency_id}/requests/{request_id}/passengers/{request_passenger_id}/confirm-identity`.
- The route is limited to existing Agency write roles and Platform Owner/Admin override, enforces agency ownership for request and existing passenger selections, and records audit plus request-timeline evidence.
- Intake conversion and request creation do not create a `PassengerProfile`; offer creation from a request rejects unresolved passenger identities.

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

Phase 52.5 adds operational rule composer APIs only under `/api/platform/operational-rule-composer/*` and `/api/agencies/{agency_id}/rule-composer/*`, plus frontend pages under `/platform/operational-rule-composer` and `/agency/rule-composer`. It records metadata-only compound rule metadata and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, rule execution, live rule evaluation, pricing calculation, provider integrations, AI/LLM generation, background workers, automatic decisions, or automation.

Phase 52.6 adds knowledge quality assurance APIs only under `/api/platform/knowledge-quality-assurance/*` and `/api/agencies/{agency_id}/knowledge-quality-assurance/*`, plus frontend pages under `/platform/knowledge-quality-assurance` and `/agency/knowledge-quality-assurance`. It records metadata-only QA review metadata and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, auto-approval, publishing, rule execution, AI/LLM generation, provider integrations, background workers, automatic decisions, or automation.

Phase 52.7 adds airline knowledge publishing APIs only under `/api/platform/airline-knowledge-publishing/*` and `/api/agencies/{agency_id}/published-knowledge/*`, plus frontend pages under `/platform/knowledge-publishing` and `/agency/published-knowledge`. It records metadata-only controlled publication workflow metadata and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, automatic publication, recommendation execution, AI/LLM generation, provider integrations, background workers, automatic decisions, or automation.

Phase 52.8 adds operational scenario testing APIs only under `/api/platform/operational-scenario-testing/*` and `/api/agencies/{agency_id}/operational-scenario-testing/*`, plus frontend pages under `/platform/operational-scenario-testing` and `/agency/scenario-testing`. It records metadata-only passenger service scenario examples and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, live provider tests, AI/LLM generation, parser execution, automated scenario execution, background workers, booking, ticketing, EMD issuance, or automation.

Phase 52.9 adds knowledge population toolkit APIs only under `/api/platform/knowledge-population-toolkit/*` and `/api/agencies/{agency_id}/knowledge-population-toolkit/*`, plus frontend pages under `/platform/knowledge-population-toolkit` and `/agency/knowledge-population-toolkit`. It records metadata-only airline knowledge population readiness and coverage metadata and does not add route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, scraping, automatic import, AI/LLM generation, parser execution, provider integrations, background workers, population jobs, or automation.

Phase 53.0 adds pilot readiness APIs only under `/api/platform/pilot-readiness/*` and `/api/agencies/{agency_id}/pilot-readiness/*`, plus frontend pages under `/platform/pilot-readiness` and `/agency/pilot-readiness`. It records metadata-only stabilization diagnostics, deterministic readiness scores, golden-path case/run metadata, and issue remediation links without route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, production auto-seeding, destructive resets, provider execution, AI/LLM generation, background workers, schedulers, sending, booking, ticketing, EMD issuance, or automation.

Phase 54.1 adds operational workflow APIs only under `/api/platform/operational-workflows/*` and `/api/agencies/{agency_id}/operational-workflows/*`, plus frontend pages under `/platform/operational-workflows` and `/agency/operational-workflows`. It records metadata-only workflow definitions, instances, guard results, transition history, warnings, blockers, and events without route blocking, redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, provider execution, AI/LLM generation, background workers, schedulers, sending, booking, ticketing, EMD issuance, automatic workflow execution, or existing entity status mutation without future explicit adapters.

Phase 54.2 adds agent work queue APIs only under `/api/platform/work-queues/*` and `/api/agencies/{agency_id}/work-queue/*`, plus frontend pages under `/platform/work-queues` and `/agency/work-queue`. It records metadata-only operational work items, queue definitions, assignment events, and queue views without adding redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, duplicate task systems, duplicate workflow architectures, provider execution, AI/LLM generation, background workers, schedulers, sending, booking, ticketing, EMD issuance, or automatic operational execution.

Phase 54.3 adds SLA and operational deadline APIs only under `/api/platform/sla-policies/*` and `/api/agencies/{agency_id}/deadlines/*`, plus frontend pages under `/platform/sla-policies` and `/agency/deadlines`. It records metadata-only SLA policies, business calendars, deadlines, and SLA events without adding redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, duplicate task systems, duplicate workflow architectures, provider execution, AI/LLM generation, background workers, schedulers, sending, booking, ticketing, EMD issuance, route blocking, access enforcement, or automatic operational execution.

Phase 54.4 adds task automation and dependency orchestration APIs only under `/api/platform/task-automation/*` and `/api/agencies/{agency_id}/task-automation/*`, plus frontend pages under `/platform/task-automation` and `/agency/task-automation`. It records metadata-only task templates, dependencies, automation rules, and automation runs while reusing existing request tasks and work queues without adding redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, duplicate task systems, arbitrary code execution, provider execution, AI/LLM generation, background workers, schedulers, sending, booking, ticketing, EMD issuance, route blocking, access enforcement, or automatic operational execution.

Phase 54.5 adds request-to-trip operational conversion APIs only under `/api/platform/request-trip-conversion/*` and `/api/agencies/{agency_id}/request-trip-conversion/*`, plus frontend pages under `/platform/request-trip-conversion` and `/agency/request-trip-conversion`. It records metadata-only preview, validation, conversion run, mapping, and issue records while preserving the request as intake origin and the trip as downstream shell without adding redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, automatic trip id reuse from request ids, booking, ticketing, provider execution, AI/LLM generation, background workers, schedulers, sending, route blocking, access enforcement, or automatic operational execution.

Phase 54.6 adds offer-to-booking handoff APIs only under `/api/platform/booking-handoffs/*` and `/api/agencies/{agency_id}/booking-handoffs/*`, plus frontend pages under `/platform/booking-handoffs` and `/agency/booking-handoffs`. It records metadata-only accepted-offer handoff, readiness-check, mapping, and booking-instruction records while reusing frozen accepted-offer snapshots and existing booking readiness packages without adding redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, mutable-offer commercial reconstruction, live booking, ticketing, EMD issuance, provider execution, AI/LLM generation, background workers, schedulers, sending, payment processing, route blocking, access enforcement, or automatic operational execution.

Phase 54.7 adds servicing and after-sales workflow APIs only under `/api/platform/after-sales/*` and `/api/agencies/{agency_id}/after-sales/*`, plus frontend pages under `/platform/after-sales` and `/agency/after-sales`. It records metadata-only after-sales cases, affected item links, decisions, financial placeholders, resolutions, and communication records without adding redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, ticket or EMD mutation, financial commitments, provider execution, AI/LLM generation, background workers, schedulers, sending, payment processing, route blocking, access enforcement, or automatic operational execution.

Phase 54.8 adds operations command center APIs only under `/api/platform/operations-governance/*` and `/api/agencies/{agency_id}/operations-command-center/*`, plus frontend pages under `/platform/operations-governance` and `/agency/operations-command-center`. It aggregates existing operational metadata into read-only dashboard, queue, kanban, calendar, timeline, exception, and workload views without adding redirects, aliases, `/admin`, `/agent`, `/api/admin`, `/api/agent`, duplicate operations collections, duplicate task systems, duplicate workflow architectures, uncontrolled drag-and-drop mutation, provider execution, AI/LLM generation, background workers, schedulers, sending, booking, ticketing, EMD issuance, payment processing, route blocking, access enforcement, or automatic operational execution.

Phase 54.9 adds workflow maturity APIs only under `/api/platform/workflow-maturity/*` and `/api/agencies/{agency_id}/workflow-maturity/*`, plus frontend pages under `/platform/workflow-maturity` and `/agency/workflow-maturity`. The diagnostic test-run POST returns an isolated non-persisted assessment and does not create production operational records. No `/admin`, `/agent`, `/api/admin`, `/api/agent`, redirect, alias, parallel workflow, or parallel maturity collection is introduced.

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
| `/admin/operational-workflows` | `/platform/operational-workflows` |
| `/agent/operational-workflows` | `/agency/operational-workflows` |
| `/admin/work-queues` | `/platform/work-queues` |
| `/admin/sla-policies` | `/platform/sla-policies` |
| `/agent/deadlines` | `/agency/deadlines` |
| `/agent/work-queue` | `/agency/work-queue` |
| `/admin/operations-command-center` | `/platform/operations-governance` |
| `/agent/operations-command-center` | `/agency/operations-command-center` |
| `/admin/workflow-maturity` | `/platform/workflow-maturity` |
| `/agent/workflow-maturity` | `/agency/workflow-maturity` |
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
| `/admin/pilot-readiness` | `/platform/pilot-readiness` |
| `/agent/pilot-readiness` | `/agency/pilot-readiness` |
| `/admin/client-master` | `/platform/client-master` |
| `/admin/passenger-master` | `/platform/passenger-master` |
| `/agent/passengers` | `/agency/passengers` |
| `/documents` | `/agency/documents` and `/platform/document-templates` |
| `/tickets` | `/agency/tickets-emds` |
| `/bookings` | `/agency/booking-workspaces` |
| `/changes` or `/exchanges` | `/agency/trips/{trip_id}` changes panel and `/agency/tickets-emds` exchange actions |

## Boundary

This policy does not redesign the app shell, introduce new route roots, or change existing tenant authorization. It records that `/platform` and `/agency` are the canonical user-facing roots for AeroAssist AgencyOS.
# Phase 55.1 Airline Master Profiles

Phase 55.1 uses `/api/platform/airline-master-profiles` for platform governance and `/api/agencies/{agency_id}/airline-master-profiles` for tenant-checked, approved/published read-only consumption. UI routes are `/platform/airline-master-profiles` and `/agency/airline-profiles`. No `/admin/*` or `/agent/*` route family is introduced.

## Phase 55.2 Airline Evidence

Phase 55.2 uses `/api/platform/airline-evidence` for evidence governance and `/api/agencies/{agency_id}/airline-evidence` for tenant-checked, approved read-only summaries. UI routes are `/platform/airline-evidence` and `/agency/airline-evidence`. No alternate `/admin/*` or `/agent/*` root is introduced.

## Phase 55.3 Airline Knowledge Versions

Phase 55.3 uses `/api/platform/knowledge-versions` for deterministic version, comparison, impact, review, and revalidation metadata. Agency published-update visibility is read-only at `/api/agencies/{agency_id}/knowledge-updates`. UI routes are `/platform/knowledge-versions` and `/agency/knowledge-updates`. Existing Phase 50.4 governance and Phase 39.2 data-pack version routes remain canonical for their separate lifecycle and staging responsibilities; no `/admin/*` or `/agent/*` root is introduced.

## Phase 55.4 Airline Service Coverage

Phase 55.4 uses `/api/platform/airline-service-coverage` for coverage targets, deterministic assessments, matrix views, gap review, and remediation-plan metadata. Agency published coverage is read-only at `/api/agencies/{agency_id}/airline-service-coverage`. UI routes are `/platform/airline-service-coverage` and `/agency/airline-service-coverage`. The older `/agency/airline-intelligence-coverage` route remains the Phase 39 data-pack coverage view; Phase 55.4 is the canonical operational knowledge usability matrix. No `/admin/*` or `/agent/*` route root is introduced.

## Phase 55.5 Airline Distribution Capabilities

Phase 55.5 uses `/api/platform/airline-distribution-capabilities` for governed channel, capability, PSS, GDS, NDC, fulfillment, servicing, restriction, and evidence metadata. Agency published planning visibility is read-only at `/api/agencies/{agency_id}/distribution-capabilities`. UI routes are `/platform/airline-distribution-capabilities` and `/agency/distribution-capabilities`. Existing broad distribution/PSS/GDS records remain canonical source context; no `/admin/*`, `/agent/*`, or provider-specific route root is introduced.

## Phase 55.6 Interline and Codeshare Intelligence

Phase 55.6 uses `/api/platform/interline-codeshare-intelligence` for governed carrier relationships and responsibility-rule metadata. Agency published intelligence and transient advisory evaluation use `/api/agencies/{agency_id}/interline-codeshare-advisor`. UI routes are `/platform/interline-codeshare-intelligence` and `/agency/interline-codeshare-advisor`. Existing canonical `/platform/*`, `/agency/*`, `/api/platform/*`, and `/api/agencies/{agency_id}/*` families remain unchanged; no carrier-, provider-, `/admin/*`, or `/agent/*` route root is introduced.

## Phase 55.7 Fare Brand Intelligence

Phase 55.7 uses `/api/platform/fare-brand-intelligence` for governed fare-family, RBD, baggage, commercial-attribute, evidence-link, and comparison-profile metadata. Agency published intelligence and transient read-only comparisons use `/api/agencies/{agency_id}/fare-brand-library`. UI routes are `/platform/fare-brand-intelligence` and `/agency/fare-brand-library`. No provider, pricing-engine, `/admin/*`, or `/agent/*` route root is introduced.

## Phase 55.8 Airline Contact Intelligence

Phase 55.8 uses `/api/platform/airline-contact-intelligence` for governed contact directory, channel, scope, hours, escalation, template, requirement, verification, and interaction metadata. Agency published directory access, transient desk/template advice, and agency-owned interaction history use `/api/agencies/{agency_id}/airline-contact-directory`. UI routes are `/platform/airline-contact-intelligence` and `/agency/airline-contact-directory`. No provider-messaging, `/admin/*`, or `/agent/*` route root is introduced.

## Phase 55.9 Airline Intelligence Readiness

Phase 55.9 uses `/api/platform/airline-intelligence-readiness` for readiness profiles, deterministic assessments, release candidates and gates, audited decisions, population waves, and issue metadata. Agency read-only released coverage uses `/api/agencies/{agency_id}/airline-intelligence-readiness`. UI routes are `/platform/airline-intelligence-readiness` and `/agency/airline-intelligence-readiness`. Draft governance and restricted source traces are excluded from agency responses, and no `/admin/*` or `/agent/*` route root is introduced.

## Phase 56.0 Journey Engine

Platform read-only governance and diagnostics use `/api/platform/journey-engine` and `/platform/journey-engine`. Agency representation reads and authorized metadata writes use `/api/agencies/{agency_id}/journeys` and `/agency/journeys`. Source projection actions remain under the same agency route family, including `from-trip`, `from-offer`, `from-booking`, `from-ticket`, and `from-emd`. Finalized snapshots have no destructive route. No `/admin/*`, `/agent/*`, parallel public journey API, or unauthenticated mutation route is introduced.

## Phase 56.1 Journey Authoring

- Agency workspace: `/agency/journey-authoring`
- Platform diagnostics: `/platform/journey-authoring`
- Agency API: `/api/agencies/{agency_id}/journey-authoring`
- Platform API: `/api/platform/journey-authoring`

Agency routes permit governed authoring metadata operations under existing agency-role checks. Platform routes are read-only diagnostics. Phase 56.1 introduces no `/admin/*`, `/agent/*`, parallel Journey route root, provider endpoint, or unauthenticated mutation.

## Phase 56.2 Journey Option Composition Routes

- Agency workspace: `/agency/journey-option-composition`
- Platform diagnostics: `/platform/journey-option-compositions`
- Agency API: `/api/agencies/{agency_id}/journey-option-compositions`
- Platform API: `/api/platform/journey-option-compositions`

Agency APIs expose agency-scoped composition metadata operations through existing authorization. Platform APIs expose read-only totals, validation metadata, and composition diagnostics. Phase 56.2 introduces no `/admin/*`, `/agent/*`, parallel Offer or Journey root, provider endpoint, public mutation, or direct database access from the frontend.

## Phase 56.3 Journey Comparison Presentation Routes

- Agency workspace: `/agency/journey-comparison-presentations`
- Platform diagnostics: `/platform/journey-comparison-presentations`
- Agency API: `/api/agencies/{agency_id}/journey-comparison-presentations`
- Platform API: `/api/platform/journey-comparison-presentations`

## Phase 56.4 Offer Delivery

- Primary Agency workspace: `/agency/offers/{offer_id}` with Delivery & Responses context
- Contextual compatibility route: `/agency/offer-deliveries?offer_id={offer_id}`
- Agency API: `/api/agencies/{agency_id}/offer-deliveries`
- Authenticated client workspace: `/portal/travel-options`
- Authenticated client API: `/api/portal/offer-deliveries`
- Platform diagnostics: `/platform/offer-delivery-diagnostics`
- Platform API: `/api/platform/offer-delivery-diagnostics`

Client routes extend the existing authenticated portal family and resolve authorization through canonical portal, client, passenger relationship, delivery-recipient, and agency records. IDs are never authorization credentials. No anonymous public link, `/admin/*`, `/agent/*`, duplicate offer/acceptance route family, or unrestricted Platform impersonation route is introduced.

The permanent [Product Surface Review Gate](product-surface-workspace-governance.md) requires engines and supporting tools to preserve the route context of their owning primary workspace. Phase 56 authoring, options, comparison, and delivery routes are contextual tools; only Offer Workspace owns the Agency commercial lifecycle.

Agency APIs expose tenant-checked presentation projection, wording, preview, explicit preference, snapshot, review, and metadata-only handoff operations. Platform APIs expose read-only counts, dimensions, validation metadata, and summarized diagnostics. Phase 56.3 introduces no `/admin/*`, `/agent/*`, public share route, unauthenticated mutation, parallel Offer/Document/Journey domain, provider endpoint, or direct frontend database access.
## Phase 57.0 Pilot Operations Routes

- Canonical Platform UI: `/platform/pilot-operations`.
- Canonical protected API root: `/api/platform/pilot-operations`.
- Evidence, assessments, sign-offs, pilot agencies, synthetic datasets, health timeline, and production diagnostics are subresources of that root.
- There is no `/admin/*`, Agency, portal, or public pilot-operations route. Public `/api/health` and `/api/readiness` expose only static, non-sensitive Phase 57.0 capability metadata.

## Phase 58.1 Commercial Pilot Agency Onboarding Routes

- Canonical Agency UI: `/agency/onboarding`.
- Canonical API root: `/api/agencies/{agency_id}/onboarding`.
- Newly created incomplete agencies are redirected through the shared Agency loader; completed and legacy-exempt agencies retain existing canonical routes.
- Platform agency detail links to the same Agency route and API under existing Platform authorization; no parallel Platform onboarding API is introduced.
- Phase 58.1 adds no `/admin/*`, `/agent/*`, public mutation, provider route, or duplicate agency/travel route family.

## Phase 58.2 Commercial Pilot Operations Command Centre Routes

- Canonical Agency home: `/agency`.
- Compatibility Agency route: `/agency/operations-command-center`.
- Canonical tenant-scoped read API: `GET /api/agencies/{agency_id}/operations-command-center`.
- Supported assignment and completion mutations remain under `/api/agencies/{agency_id}/work-queue/work-items/{work_item_id}/*` and are not duplicated by the command-centre router.
- Incomplete newly created agencies continue through the Phase 58.1 redirect before either Agency operations route is rendered.
- Phase 58.2 adds no `/admin/*`, `/agent/*`, public mutation, provider route, parallel queue API, or parallel workflow route.

## Phase 58.3 Complete Pilot Agency Experience Routes

- The canonical Agency UI remains `/agency/onboarding`.
- Profile preview uses `GET /api/agencies/{agency_id}/onboarding/demo-workspace/profiles`.
- Profile generation continues to use `POST /api/agencies/{agency_id}/onboarding/demo-workspace`, with an optional validated `demo_profile` body.
- Generation remains restricted by the existing onboarding Agency authorization and reuses all downstream canonical UI/API route families.
- Phase 58.3 adds no separate demo UI route, `/admin/*`, `/agent/*`, public mutation, fake operational API, provider route, or alternate workflow route.

## Phase 58.4 Product Standards and UX Refinement Routes

- Active marker: `phase_58_4_aeroassist_product_standards_ux_refinement`.
- Phase 58.4 adds no frontend or API route.
- Shared components refine existing `/agency/*` workspaces and continue to call their existing `/api/agencies/{agency_id}/*` contracts.
- Platform, Agency, Client Portal, and public route ownership remains unchanged.
- Travel-first labels do not rename internal route paths, model symbols, or compatibility identifiers.
- No `/admin/*`, `/agent/*`, parallel workflow root, public mutation, or direct frontend persistence access is introduced.

## Phase 58.5 Commercial Pilot Readiness Routes

- Agency help and feedback UI: `/agency/pilot-feedback`.
- Tenant-scoped Agency API: `GET|POST /api/agencies/{agency_id}/pilot-feedback` and `GET /api/agencies/{agency_id}/pilot-feedback/{feedback_id}`.
- Platform feedback review UI: `/platform/pilot-feedback`.
- Protected Platform feedback API: `GET /api/platform/pilot-feedback`, `GET /api/platform/pilot-feedback/{feedback_id}`, and `PATCH /api/platform/pilot-feedback/{feedback_id}`.
- Platform Commercial Pilot readiness UI: `/platform/commercial-pilot-readiness`.
- Protected computed assessment API: `GET /api/platform/commercial-pilot-readiness`, optionally scoped with `agency_id`.
- Phase 58.5 adds no public or anonymous feedback route, `/admin/*`, `/agent/*`, external support endpoint, parallel incident/ticketing system, or Phase 57 release mutation.

## Phase 59.0 Product Experience Recovery Routes

- Phase 59.0 adds no frontend route, API route, alias, router, or mutation.
- Task-based navigation projects existing module-catalogue entries into Platform and Agency product areas.
- Canonical `/platform/*`, `/agency/*`, `/api/platform/*`, and `/api/agencies/{agency_id}/*` ownership remains unchanged.
- `/platform` continues to resolve to the Platform Overview and `/agency` continues to resolve to the Phase 58.2 Operations Command Centre after the existing onboarding check.
- Specialist deep links remain valid in collapsed Advanced navigation; contextual tools remain owned by their existing primary workspaces.
- No `/admin/*`, `/agent/*`, parallel workflow root, or direct frontend persistence path is introduced.
