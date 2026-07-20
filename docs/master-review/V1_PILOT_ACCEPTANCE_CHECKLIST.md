# AeroAssist V1 Pilot Acceptance Checklist

## Scope

- Branch: `v1-integration-program`
- Baseline commit: `46990a88`
- Audit date: 2026-07-20
- Path: Client -> Passenger -> Request -> Trip -> Offer -> Accepted Offer -> Booking Handoff -> Booking -> Ticket / EMD -> Passenger Services -> Documents -> Invoice / Payment -> After Sales
- Safety boundary: no provider execution, live booking, ticket or EMD issuance, payment capture, deployment, or production access.

The persisted acceptance smoke uses an isolated in-memory database and canonical services. It proves state transitions, persistence, validation recovery, reconciliation, idempotency, tenant isolation, and operational evidence. Static UI contracts prove the registered pages and continuity controls target those APIs. A human browser walkthrough remains required before pilot release because no interactive browser runtime was available during this audit.

## Status Legend

- **PASS**: executable evidence and UI contract are present.
- **PASS (read-only)**: opening and continuation are supported; editing is intentionally unavailable at this step.
- **MANUAL SIGN-OFF**: must be visually confirmed in a pilot browser session.

## Golden Path Acceptance

| Step | Create | Open | Edit where permitted | Continue workflow | Related records | Validation / recovery | Empty / loading / failure | Isolation | Audit / timeline evidence | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Client | Canonical CRM action | Detail route | Supported | Passenger | Passenger relationships | Relationship guard | Protected loading/error and empty relationship state | Agency-scoped API | Transition evidence downstream | PASS |
| Passenger | Canonical passenger action | Detail route | Supported | Request | Client relationships and travel records | Relationship guard | Protected loading/error and empty relationship state | Agency-scoped API | Transition evidence downstream | PASS |
| Request | Intake/create action | Detail route | Supported | Conversion preview | Client, passenger, segments, services | Critical structures block; warnings remain reviewable | Protected loading/error and source-snapshot empty state | Cross-agency conversion rejected | Conversion audit, timeline, queue, workflow | PASS |
| Trip | Request conversion | Detail route | Supported | Offer Builder | Request, passengers, segments, services, offers | Duplicate conversion reuses result | Protected loading/error and section empty states | Cross-agency conversion rejected | Correlated conversion evidence | PASS |
| Offer | Trip-scoped builder | Builder/detail routes | Supported | Acceptance | Trip, options, pricing and service feasibility | Invalid/missing option remains blocked | Protected loading/error and option empty states | Agency-scoped API | Offer transition evidence | PASS |
| Accepted Offer | Explicit acceptance | Offer history | Immutable snapshot | Booking Handoff | Frozen offer, trip and readiness package | Mutable offer cannot replace accepted snapshot | Protected loading/error and no-history state | Agency-scoped API | Acceptance audit and workflow evidence | PASS (read-only) |
| Booking Handoff | Accepted snapshot action | Handoff workspace | Metadata review | Booking | Snapshot, mappings, checks and readiness | Missing canonical source blocks; conditional handoff is explicit | Protected loading/error and no-handoff state | Cross-agency handoff rejected | Handoff audit, queue and workflow | PASS |
| Booking | Handoff action | Booking detail | Manual metadata updates | Ticket / EMD | Trip, offer, passengers and segments | Duplicate create reuses workspace | Protected loading/error and missing-record recovery | Agency-scoped API | Booking audit, timeline and work item | PASS |
| Ticket | Manual external-result record | Ticket detail | Reconciliation metadata | Passenger Services | Booking, coupons and EMDs | Mismatch is explicit and can reconcile to matched | Protected loading/error and linked-EMD empty state | Agency-scoped API | Ticket audit and timeline | PASS |
| EMD | Booking-service metadata action | EMD detail | Manual mirror metadata | Passenger Services | Booking, ticket, coupons and service | Missing service link shows review warning; linked service continues directly | Protected loading/error and record-list empty states | Agency-scoped API | EMD timeline and linked operational evidence | PASS |
| Passenger Services | Canonical service action | Service workspace | Fulfilment metadata | Documents | Booking, ticket, EMD, coupons and documents | Fulfilment without verified evidence fails; corrected evidence succeeds | Protected loading/error and service/workspace empty states | Cross-agency selector and link rejected | Service audit, timeline, queue and workflow | PASS |
| Documents | Service requirement action | Document workspace | Review/reconciliation metadata | Finance | Service, booking, ticket and EMD | Rendered output does not imply verification; verified evidence is explicit | Protected loading/error and document empty state | Cross-agency reconciliation rejected | Document transition audit and timeline | PASS |
| Invoice / Payment | Booking-to-invoice action | Invoice detail | Manual payment metadata | After Sales | Booking, invoice lines and payments | Canonical line ownership and payment context validated | Protected loading/error and payment empty state | Agency-scoped API | Finance transition evidence | PASS |
| After Sales | Contextual source actions | Case workspace | Case and financial metadata | Terminal servicing workspace | Booking, accepted snapshot, services, documents, invoice, lines, payment, ticket and EMD | Mismatch/manual review can reconcile; duplicate attempts are idempotent | Protected loading/error and case/metadata empty states | Cross-agency options and create rejected | Immutable references, audit, timeline, queue and workflow | PASS |

## Automated Acceptance Scenarios

`backend/scripts/smoke_v1_pilot_acceptance.py` proves:

1. One successful persisted workflow through After Sales, including Ticket and EMD.
2. One validation failure when fulfilment evidence is incomplete, followed by successful recovery.
3. Ticket and After Sales financial mismatch states followed by explicit reconciliation.
4. Duplicate conversion, handoff, booking, document, link, case, and financial-impact attempts do not duplicate canonical records.
5. Cross-agency conversion, handoff, service, document, and After Sales access is rejected.
6. After Sales retains immutable invoice, invoice-line, payment, accepted-offer, ticket, EMD, and passenger-service references.

## Manual Pilot Sign-Off

- [ ] Complete the path in a supported desktop browser using one synthetic pilot agency.
- [ ] Repeat responsive checks at a narrow/mobile viewport.
- [ ] Confirm every loading state remains stable under throttled network conditions.
- [ ] Confirm API failures remain recoverable without losing entered metadata.
- [ ] Confirm labels and previews are understandable without reading raw identifiers.
- [ ] Confirm keyboard focus, form labels, and disabled transition explanations.
- [ ] Confirm no internal note appears in client-facing projections.
- [ ] Remove the synthetic tenant records through the governed cleanup workflow.

Pilot release acceptance is incomplete until these manual checks and the release evidence gates in `V1_DEPLOYMENT_READINESS_REPORT.md` are signed off.
