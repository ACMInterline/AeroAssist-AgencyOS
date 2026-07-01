# Supplementary Blueprint Adoption Map

Phase 36.4.5 adopts useful structures from the supplementary blueprint without replacing AgencyOS architecture. Phase 36.4.6 extends that alignment to standalone manual, imported confirmation/GDS, and existing-trip change/exchange workflows. Phase 36.5 adds the safe document foundation layer. Phase 36.6 adds governed GDS parser profiles, versions, runs, entities, corrections, samples, and evaluations. Phase 36.7 adds governed airline policy source ingestion, deterministic candidate extraction, human review, and approved knowledge records. `/platform/*` and `/agency/*` remain canonical, provider execution stays disabled, and existing request/trip/offer/booking/ticket/EMD models remain the source of truth.

| Supplementary concept | Current AgencyOS equivalent | Status | Action |
|---|---|---|---|
| `users`, `roles`, `user_roles`, `permissions`, `role_permissions` | `platform_users`, `auth_identities`, `auth_sessions`, `agency_staff_memberships`, invitations, platform/agency role helpers | built differently | Do not duplicate RBAC; current platform and agency role model remains canonical. |
| Airline intelligence tables | `airline_profiles`, `airline_intelligence_profiles`, contacts, fleet, aircraft, routes, fare families, RBD rows, fare rules, ancillaries, interline, distribution, PSS/GDS parameters, `unified_exception_rules` | partially built | Use existing Phase 36 airline structures; add only `AirlineBrandAsset` as safe foundation. |
| Airline policy ingestion and reviewed knowledge | `AirlinePolicySource`, `AirlinePolicySection`, `AirlinePolicyExtractionRun`, policy candidate records, review corrections, and approved knowledge records | foundation adopted | Preserve source provenance and human review; do not auto-promote into canonical rules/services or call external AI/provider systems. |
| Supplier endpoints, credentials, health, failover | Provider targets and provider payload/response placeholders on booking records/workspaces | planned later | No live supplier execution, credentials, failover, or health checks yet. |
| GDS parser samples and normalizer traces | Parser profiles, versions, runs, parsed entities, corrections, `GdsParseSample`, evaluations, and `AiTraceEvent` | built | Preserve parser runs, samples, corrections, and evaluations without provider calls or external AI parser automation. |
| Trip requests and trip segments | `request_intakes`, `travel_requests`, `request_segments`, `trip_dossiers`, `trip_segments` | built | Map to existing request-to-trip lifecycle. |
| Offers and offer items | `offer_workspaces`, `offer_options`, `offer_builder_segments`, `offer_fare_bundles`, `offer_pricing_lines` | built | Continue using rule-aware offer builder foundations. |
| Bookings and PNR snapshots | `booking_workspaces`, `booking_records`, `BookingImportDraft`, `TripChangeOperation`, `internal_pnr_mirror_json` | built | Support readiness-driven, standalone manual, imported, and existing-trip change booking mirrors; no provider execution. |
| Tickets and EMDs | `ticket_records`, `ticket_coupons`, `emd_records`, `emd_coupons`, `TicketExchangeOperation`, `EmdExchangeOperation` | built | Recognize Phase 36.4 Tickets + EMD Foundation and Phase 36.4.6 exchange mirror foundation; do not add duplicate models. |
| Documents, versions, shares, templates, designer | `document_templates`, `document_render_jobs`, `document_packages`, `document_share_records`, legacy rendered/export/storage records | foundation adopted | Adopt default templates, internal render jobs, normalized context, packages, and manual/internal share records; defer visual designer, public links, automatic delivery, and version governance. |
| Fragmented AI logs | `AiTraceEvent` | add foundation now | Use one unified trace collection instead of many `ai_*_logs` tables. |
| ADM risk events | `AdmRiskEvent` | add foundation now | Provide reviewable risk-event records without an ADM AI engine. |
| Audit logs and system events | `audit_events` plus workflow timeline events | built differently | Do not duplicate audit logs; defer formal error/API usage telemetry. |
| Passenger, medical, cargo, VIP special service modules | `PassengerServiceRequest`, request pets/items, trip service items, service catalogue, rules/services registry, exception engine, SSR/OSI generator | built differently | Add `SpecialServicesUnifiedFacade`; do not rebuild parallel special-service modules. |
| `/agent/*` and `/admin/*` route shells | `/agency/*` and `/platform/*` | intentionally rejected | Keep canonical route roots and document mappings instead of aliases. |

## Adopted Now

- `AiTraceEvent`
- `AdmRiskEvent`
- `GdsParseSample`
- `AirlineBrandAsset`
- Static blueprint adoption API and `/platform/blueprint` UI
- `SpecialServicesUnifiedFacade`
- `BookingImportDraft`, `TripChangeOperation`, `TicketExchangeOperation`, and `EmdExchangeOperation`
- Source-context fields for booking, ticket, and EMD mirror records
- `DocumentRenderJob`, `DocumentPackage`, and `DocumentShareRecord`
- Unified document context/render services and platform default document templates
- `GdsParserProfile`, `GdsParserVersion`, `GdsParserRun`, `GdsParsedEntity`, `GdsParseCorrection`, extended `GdsParseSample`, and `GdsParserEvaluationRun`
- `/agency/gds-parser` and `/platform/gds-parser`
- `AirlinePolicySource`, `AirlinePolicySection`, `AirlinePolicyExtractionRun`, extracted rule/price/communication/EMD/exception candidates, review corrections, and approved knowledge records
- `/agency/airline-policy-library` and `/platform/airline-policy-ingestion`

## Deferred

- Full visual document designer, document version governance, public sharing links, automatic delivery, e-signature, and document-payment/invoice/accounting coupling
- Full host grammar coverage, provider imports/reconciliation, and request/offer quote UX for trip changes
- Visual airline dashboards
- Live AI engines, AI model configuration, and ADM automation
- Supplier credentials, health, failover, and execution
- Payments, invoices/accounting expansion, settlement, and live ticket/EMD issuance

## Recognized Existing Work

Phase 36.4 Tickets + EMD Foundation is already built. The booking workspace creation entry point fix is recognized as the canonical readiness-package entry point, Phase 36.4.6 recognizes standalone manual, imported confirmation/GDS, and existing-trip change/exchange workflows as valid internal mirror paths, Phase 36.5 recognizes internal document rendering/packages as the canonical document foundation, Phase 36.6 recognizes governed parser runs/training/evaluation as the parser foundation, and Phase 36.7 recognizes governed airline policy ingestion/review as the source-backed policy knowledge foundation.
