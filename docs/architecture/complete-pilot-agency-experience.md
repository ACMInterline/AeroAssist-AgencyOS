# Complete Pilot Agency Experience

Phase 58.3 extends the Phase 58.1 onboarding demo action into a complete, synthetic pilot environment. It does not add a demo domain, route family, collection, or alternative workflow. The generator writes linked records through existing canonical AgencyOS models and collections so a newly onboarded agency can inspect the main operating journey without first entering data manually.

## Generation Strategy

`AgencyDemoWorkspaceGenerator` is called by the existing `AgencyOnboardingService.seed_demo_workspace` method. The existing `POST /api/agencies/{agency_id}/onboarding/demo-workspace` action accepts one of four profiles:

- Small Agency: eight compact active and historical cases.
- Medium Agency: ten cases with additional workload and follow-up depth.
- Corporate Agency: ten managed-travel cases with corporate ownership, approval, and pricing context.
- Luxury Leisure Agency: ten high-touch cases with premium illustrative pricing and concierge ownership.

The profile catalogue is available from `GET /api/agencies/{agency_id}/onboarding/demo-workspace/profiles`. Generation remains an explicit Agency Owner or Agency Admin onboarding action. It never runs at application startup or for historical agencies.

## Supported Scenarios

The bounded dataset includes family travel ready for ticketing, a corporate medical case waiting for an airline, an offer expiring today, an unaccompanied minor with a missing document, multi-city PETC/AVIH travel, a completed adaptive-sports journey, a cancelled flight with refund and voucher placeholders, a schedule change with partial ticketing, an archived journey, and an outstanding supplier follow-up.

Across those cases the generator provides canonical clients, associated passengers, requests, trips, flight segments, offer comparisons, accepted/declined/pending offers, frozen acceptance snapshots, booking readiness, handoffs, booking workspaces and timelines, Ticket and EMD mirrors, SSR/OSI and passenger-service records, document workspaces and packages, invoice/payment states, tasks, deadlines, workflow records, timeline events, internal/client/supplier communication placeholders, and after-sales financial placeholders. Airline policy, reference-service, and pricing examples are preserved as linked snapshots on canonical offer, booking-readiness, and passenger-service records; onboarding does not create tenant-specific copies in shared airline knowledge collections.

## Referential Integrity

Every scenario starts from a canonical Client and one or more Passenger profiles. The same stable identifiers are carried through Request, operational workspace, Trip, Flight, Offer, acceptance, readiness, Booking, Ticket/EMD, passenger service, Document, Finance, Workflow, Timeline, and After Sales records. Frozen accepted-offer and pricing snapshots remain immutable inputs to booking examples. Document packages point back to their canonical Trip or Booking context, and financial placeholders point to canonical invoices, payments, accepted snapshots, bookings, and issued-record mirrors.

The generator validates every record with its existing Pydantic model before persistence. No generated operational record is intentionally isolated.

## Determinism And Idempotency

Record IDs use UUID5 over the agency ID and a stable scenario/entity key. The first generation stores a `demo_anchor_date` on `AgencyOnboardingProfile`; dates and timestamps are derived from that anchor on every rerun. Rerunning the same profile updates the same records and does not create duplicate operational data. Audit history may append a user-action record for each explicit generation request, while the scenario audit records themselves use stable IDs.

Once generated, an onboarding profile cannot be changed to another demo profile. This avoids mixing differently scaled datasets. The selected profile can be rerun safely. Generation is capped at 400 records and each canonical collection remains below the Operations Command Centre bounded source limit.

## Tenant Isolation

All generated operational records include the onboarding agency ID and are upserted with an agency-and-ID filter. The manifest is stored only on that agency's `AgencyOnboardingProfile`. No generated record is shared with another agency, and no global airline knowledge record is written. The existing onboarding router continues to enforce canonical agency roles.

## Seeding Lifecycle

1. The user previews and selects a profile in the existing onboarding wizard.
2. Phase 58.1 canonical defaults are safely upserted.
3. The profile records `generating` and fixes its anchor date.
4. The generator builds and validates all linked records in memory before persistence.
5. Canonical records are inserted or updated using stable IDs.
6. The profile records the selected profile, counts, scenarios, safety flags, manifest, and `completed` generation status.
7. The onboarding review step shows the persisted completion summary.

A validation failure records a failed generation state and returns a controlled onboarding error. The action can be retried; successful records already written use stable IDs.

## Operations Command Centre

Generated data naturally populates My Work Today, operational queues, today's timeline, alerts, recent activity, and existing permission-aware quick actions. It includes new-request triage, offers awaiting action, client/airline/supplier waits, approval review, booking and ticketing readiness, passenger services, documents, follow-ups, overdue deadlines, disruption work, after-sales cases, and payment blockers.

## Safety Boundaries

The dataset is synthetic and uses `example.com` addresses, synthetic names, illustrative references, and explicit metadata flags. Ticket and EMD records are operational mirrors only. The generator performs no provider call, live search, booking, PNR creation, ticket/EMD issuance, fare calculation, payment, airline/customer communication, document rendering/delivery, background work, AI operation, or deployment.

## Limitations

- Dates remain anchored to the initial generation date; an old pilot workspace may no longer represent today's workload after prolonged use.
- PNRs, ticket numbers, EMD numbers, fares, taxes, policies, service references, and schedules are realistic illustrations, not supplier-confirmed truth.
- Shared airline policy and service knowledge is not seeded because it is not agency-owned; cases contain linked advisory snapshots instead.
- The generation request is synchronous. The frontend progress display describes bounded request progress but does not stream per-record backend events.
- Switching profile after generation is intentionally unsupported; a separate newly created pilot agency should be used to evaluate another profile.
