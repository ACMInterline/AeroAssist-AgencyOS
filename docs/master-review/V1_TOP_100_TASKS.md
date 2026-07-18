# AeroAssist V1 Top 100 Completion Tasks

## Purpose

This is the ordered closure list for Version 1.0. It is not a phase plan. Tasks are ranked by operational risk to a real agency, not by implementation convenience or module breadth.

Priority meanings:

- **P0:** required before any external pilot handles real customer work;
- **P1:** required before general V1 availability or before the affected workflow is offered;
- **P2:** important hardening, consolidation, or usability work that may follow a tightly bounded pilot if there is an explicit workaround and owner.

## Ordered Tasks

| # | Priority | Domain | Task | Acceptance evidence |
|---:|---|---|---|---|
| 1 | P0 | Pilot readiness | Complete the persisted production deployment evidence record for the exact running commit and phase. | Reviewed record matches `/api/health`, contains sanitized references, and cannot be edited after approval. |
| 2 | P0 | Production | Perform an authenticated production backup and verify its checksum and manifest. | Timestamped operator evidence records success, checksum, manifest, retention location, and no secrets. |
| 3 | P0 | Production | Complete a restore rehearsal into an isolated non-production environment. | Restore time, integrity checks, failure notes, and operator approval are recorded. |
| 4 | P0 | Production | Prove the documented rollback procedure against a known release reference. | Rehearsal identifies rollback commit, data compatibility, commands, owner, and result. |
| 5 | P0 | Security | Execute a cross-tenant isolation test suite across agency APIs, platform APIs, portal views, exports, and diagnostics. | All positive and negative cases pass with reviewed evidence and no cross-agency object disclosure. |
| 6 | P0 | Production | Establish production monitoring and an on-call response procedure for health, readiness, errors, latency, storage, and database availability. | Named owner receives and acknowledges a synthetic incident; escalation and recovery are timed. |
| 7 | P0 | Production | Run an incident-response tabletop covering outage, data corruption, credential leak, and tenant leak. | Decisions, contacts, containment, communication, recovery, and lessons are recorded. |
| 8 | P0 | Security | Apply the evidence sanitization rules to every release, backup, smoke, and diagnostic evidence mutation. | Automated and manual tests reject secrets, passenger data, raw logs, and local filesystem paths. |
| 9 | P0 | Authentication | Require strong second-factor authentication for platform owners/admins and agency owners. | Enrollment, challenge, recovery, reset, and audit cases pass for every privileged role. |
| 10 | P0 | Authentication | Add operator-visible session administration and revocation. | A user can view active sessions; an authorized actor can revoke one; revoked tokens fail immediately. |
| 11 | P0 | Agency management | Define and test agency owner transfer, staff offboarding, emergency lockout, and tenant closure procedures. | Each lifecycle scenario preserves audit history and removes access without orphaning records. |
| 12 | P0 | Client Portal | Complete object-level authorization tests for every portal read and mutation. | Tests cover wrong client, wrong agency, guessed ID, stale invitation, revoked access, and internal-only fields. |
| 13 | P0 | Security | Audit all ID-based service lookups for tenant-scoped resolution, including exports and linked-object expansion. | Static inventory and runtime tests show no unscoped agency-owned lookup on protected paths. |
| 14 | P0 | Passengers | Define field-level protection and access policy for passport, medical, assistance, contact, and identity data. | API projections, logs, exports, diagnostics, and portal responses expose only authorized fields. |
| 15 | P0 | Architecture | Publish canonical ID and ownership rules for client, passenger, trip, offer, booking, ticket, EMD, document, work item, and timeline records. | Every compatibility model names its canonical owner and permitted projection direction. |
| 16 | P0 | Passenger Services | Correct and test the stale SSR/OSI integration collection mapping. | Cross-module lookup uses the implemented `ssr_osi_workspaces` collection and regression coverage passes. |
| 17 | P0 | Trips | Make the Trip Dossier the unambiguous aggregate for passenger, segment, service, offer, booking, and completion linkage. | A single API view resolves the dossier without divergent trip/workspace/journey state. |
| 18 | P0 | Offer Builder | Declare one authoritative Offer Workspace and preserve accepted offer snapshots as immutable audit anchors. | Editing an offer cannot change the accepted snapshot used by booking handoff. |
| 19 | P0 | Booking | Separate booking instruction, external supplier result, and reconciled canonical booking state. | A manual/imported booking records all three, with actor, timestamps, source evidence, and mismatch status. |
| 20 | P0 | Ticketing | Define ticket-document and coupon status authority, including unknown and externally pending states. | Imported ticket evidence reconciles document and coupon state without inferring issuance or flown status. |
| 21 | P0 | EMD | Define EMD document, coupon/service association, fulfillment, and financial status authority. | One record traces EMD evidence to passenger, segment/service, amount, status, and unresolved mismatches. |
| 22 | P0 | Documents | Define one document lifecycle across workspace, storage, verification, package, share, delivery, expiry, and archival capabilities. | A document has one status authority and an auditable chain from receipt to disposition. |
| 23 | P0 | Operations | Define one canonical daily work item and compatibility mapping from tasks, workflow actions, issues, and domain reminders. | Every actionable blocker appears once in the agency queue and links back to its source. |
| 24 | P0 | Airline Intelligence | Populate approved, evidenced, effective-dated knowledge for the exact pilot airlines and service families. | Coverage matrix shows no critical gaps for the bounded pilot scope. |
| 25 | P0 | Airline Intelligence | Enforce freshness and conflict review before knowledge is presented as operationally usable. | Stale, conflicting, unsupported, or unpublished assertions show manual-review state, never confirmed status. |
| 26 | P0 | Airline Intelligence | Run representative scenario tests for every pilot service/airline combination. | Expected policy, pricing, feasibility, required actions, and recommendation outcomes are reviewed and pass. |
| 27 | P0 | Flights | Establish an operator-owned schedule and carrier reconciliation procedure for every active trip. | Source, checked-at time, differences, owner, and next review are visible on each segment. |
| 28 | P0 | Offer Builder | Require source, captured-at time, validity, currency, inclusions, exclusions, and caveats for every offered price and flight. | Offer cannot be marked ready with an untraceable or expired commercial fact. |
| 29 | P0 | Booking | Complete the accepted-offer-to-booking manual/import path with idempotency and mismatch handling. | Repeating the handoff does not duplicate bookings; changed external data creates a review issue. |
| 30 | P0 | Ticketing | Add a controlled external ticket-result import and reconciliation procedure. | Ticket number, fare/tax totals, coupons, passenger, flights, evidence, and discrepancies are reviewed. |
| 31 | P0 | EMD | Add a controlled external EMD-result import and reconciliation procedure. | EMD number, value, RFIC/RFISC, passenger, service/segment association, evidence, and discrepancies are reviewed. |
| 32 | P0 | Passenger Services | Consolidate requirement, SSR/OSI, approval, document, contact, EMD, and airport fulfillment into one service-case ledger. | Each passenger/segment requirement has an owner, external state, deadline, evidence, and final outcome. |
| 33 | P0 | Trips | Implement a single travel-readiness completion gate. | Trip cannot be marked travel-ready while critical booking, ticket, service, document, payment, or schedule checks are unresolved. |
| 34 | P0 | Financial tracking | Define the canonical operational ledger for customer charges, receipts, supplier costs, tickets, EMDs, fees, commissions, refunds, and credits. | Every amount has currency, source, owner, status, linkage, and reconciliation state. |
| 35 | P0 | Financial tracking | Reconcile one end-to-end booking financially, including a changed or refunded item. | Customer balance, supplier liability, fees, taxes, refund, and audit trail agree with source evidence. |
| 36 | P0 | Operations | Guarantee durable detection of overdue SLA, document, service, payment, ticketing, and departure-proximity events. | Events become visible without relying on a user opening the record; restart does not lose evaluation state. |
| 37 | P0 | End-to-end | Execute the standard request-to-completed-trip golden path using isolated synthetic records. | Reviewed run proves queue, SLA, conversion, offer snapshot, booking, ticket/EMD, service, finance, and archive linkage. |
| 38 | P0 | End-to-end | Execute a complex assistance golden path for a WCHC, PETC, MEDIF/POC, or UMNR case. | Segment-scoped requirements, evidence, approval, documents, deadlines, EMD where applicable, and fulfillment all close. |
| 39 | P0 | Pilot readiness | Resolve every blocked required assessment dimension or explicitly narrow the pilot scope so the dimension is not claimed. | Reviewed assessment has no BLOCKED/NOT_VERIFIED required dimension and retains its hash. |
| 40 | P0 | Pilot readiness | Record authorized human sign-off with conditions, rollback reference, staffing, and stop criteria. | Immutable approval history identifies operator, assessment snapshot/hash, decision time, and conditions. |
| 41 | P1 | Authentication | Add tested account recovery that does not depend on an administrator changing credentials informally. | Expiring recovery flow resists enumeration/replay and records security events. |
| 42 | P1 | Authentication | Add privileged access review and dormant-account reporting. | Owners can certify or revoke access; stale privileged accounts are flagged on a defined cadence. |
| 43 | P1 | Authentication | Remove avoidable permissive browser security policy exceptions. | Production CSP and cookie policy pass UI tests without broad `unsafe-inline` reliance. |
| 44 | P1 | Platform | Consolidate release, evidence, security, database, smoke, backup, and incident exceptions into one governance inbox. | A platform owner can identify all unresolved production actions without traversing diagnostic pages. |
| 45 | P1 | Platform | Rationalize platform navigation and module catalog around owner workflows. | User testing shows core governance tasks are findable without route knowledge. |
| 46 | P1 | Agency management | Add agency data-retention, export, suspension, reactivation, and closure controls. | Lifecycle actions are authorized, reversible where intended, audited, and tenant-scoped. |
| 47 | P1 | CRM | Consolidate client profile and master-record authority. | Duplicate candidates can be reviewed/merged while source references and audit history remain intact. |
| 48 | P1 | CRM | Add consent, preferred-channel, do-not-contact, and communication-purpose controls. | Outbound/manual communication views honor consent and retain decision evidence. |
| 49 | P1 | CRM | Provide a complete client chronology across requests, trips, offers, bookings, payments, services, documents, and portal actions. | Timeline is tenant-safe, ordered, and links to canonical records. |
| 50 | P1 | Passengers | Consolidate passenger identity master versus request/trip snapshots. | Journey-specific changes do not silently rewrite historical identity snapshots. |
| 51 | P1 | Passengers | Add duplicate-passenger review and explicit identity resolution. | Potential matches create warnings and an authorized merge/link decision, never automatic matching. |
| 52 | P1 | Passengers | Add passport/document expiry, name-match, and assistance-data review workflows. | Unknown or mismatched data creates owned work before offer/booking/travel-readiness gates. |
| 53 | P1 | Requests | Consolidate request list/detail/workspace navigation and remove duplicate entry surfaces. | Staff use one primary request workspace with consistent actions and state. |
| 54 | P1 | Requests | Support inbound attachments and communication evidence without leaking internal notes. | Files/messages are classified, scanned or safely handled, linked, and projected appropriately. |
| 55 | P1 | Trips | Add an explicit trip close/archive checklist and reopen policy. | Closure proves completion, outstanding servicing, finance, documents, and retention disposition. |
| 56 | P1 | Flights | Define canonical segment identity and update semantics for marketing/operating carrier, airports, times, status, and source. | Imports and manual corrections reconcile to one segment without destructive history loss. |
| 57 | P1 | Flights | Add schedule-change comparison and affected-work detection. | A changed segment creates visible trip, service, ticket, client, and deadline review work. |
| 58 | P1 | Airline Intelligence | Fix unsupported certainty across recommendation, comparison, and client-safe messages. | Unknown or conditional knowledge always carries evidence confidence and required manual action. |
| 59 | P1 | Airline Intelligence | Define minimum publication criteria by service family. | Policy, pricing, capability, constraint, evidence, QA, scenario, effective date, and client message requirements are explicit. |
| 60 | P1 | Airline Intelligence | Add operator verification for airline contacts and distribution capabilities used by the pilot. | Desk/channel availability, last verified date, fallback, and evidence are current. |
| 61 | P1 | Offer Builder | Consolidate offer list, detail, workspace, policy advisor, and journey composition into one operator flow. | Staff can prepare, review, deliver, revise, and accept without switching between overlapping owners. |
| 62 | P1 | Offer Builder | Add multi-currency rounding, tax/fee classification, commission, and manual-price review controls. | Totals reconcile and every manual override has reason, actor, and source. |
| 63 | P1 | Offer Builder | Show internal policy evidence separately from client-safe explanation. | Portal/customer exports cannot expose restricted evidence or internal confidence notes. |
| 64 | P1 | Offer Builder | Add offer expiry and changed-source revalidation before acceptance or booking handoff. | Expired availability/price creates a block or explicit authorized conditional decision. |
| 65 | P1 | Booking | Consolidate booking workspace, record, readiness package, and handoff views. | One booking screen identifies instruction, supplier result, readiness, tickets, EMDs, services, documents, and finance. |
| 66 | P1 | Booking | Add PNR/import conflict handling and source-preserving amendments. | Conflicting imports are retained, compared, reviewed, and never silently overwrite accepted snapshots. |
| 67 | P1 | Booking | Add explicit booking cancellation and failure states with downstream cleanup work. | Failed/cancelled booking updates queue, client status, finance, offer validity, and audit history safely. |
| 68 | P1 | Ticketing | Add guarded void, exchange, refund, and reissue case linkage without implying provider execution. | Authorized case records preserve before/after ticket and coupon evidence plus financial effects. |
| 69 | P1 | Ticketing | Validate fare construction, taxes, forms of payment, and ticket totals against source evidence. | Mismatch rules create manual review and prevent a reconciled state. |
| 70 | P1 | Ticketing | Add document/coupon lifecycle consistency checks. | Invalid combinations such as voided document with open coupons are flagged, not normalized silently. |
| 71 | P1 | EMD | Add EMD-A/EMD-S and associated/standalone handling rules. | Service association and fulfillment state remain explicit across change/refund cases. |
| 72 | P1 | EMD | Validate RFIC/RFISC, coupon, value, currency, and service linkage against evidence. | Unknown or unsupported codes create review work and cannot be presented as fulfilled. |
| 73 | P1 | Passenger Services | Add segment-level responsibility for marketing, operating, handling, and validating carriers. | Multi-carrier cases identify confirmation, pricing, EMD, airport, and escalation owner or require review. |
| 74 | P1 | Passenger Services | Add departure-day fulfillment confirmation and failure capture. | Service case records delivered/not-delivered/unknown outcome with actor, time, evidence, and follow-up. |
| 75 | P1 | Passenger Services | Make supplier-facing, internal, and client-facing messages separate governed artifacts. | Tests prove updates cannot cross visibility boundaries and templates preserve required facts. |
| 76 | P1 | Documents | Add malware-safe upload handling, type/size controls, and storage integrity checks. | Rejected files are quarantined; accepted files have checksum, metadata, access scope, and audit event. |
| 77 | P1 | Documents | Implement retention, expiry, supersession, and deletion/hold policy. | Each sensitive document has disposition state and deletion cannot erase required audit evidence. |
| 78 | P1 | Documents | Add verification responsibility and four-eyes review for critical travel documents. | Verified status identifies reviewer, source, time, scope, and expiry. |
| 79 | P1 | Client Portal | Complete usability and accessibility testing on mobile and desktop. | Pilot users can submit, review, accept, upload, and understand status at WCAG-aligned quality. |
| 80 | P1 | Client Portal | Add safe notification preference and manual communication status handling. | Portal distinguishes message prepared, sent externally, delivered, failed, and not sent. |
| 81 | P1 | Financial tracking | Implement invoice versioning and immutable issued-document snapshots. | Corrections create credit/replacement history rather than mutating issued financial evidence. |
| 82 | P1 | Financial tracking | Add payment allocation and unapplied-payment handling. | Partial, over-, under-, reversed, and multi-item payments reconcile deterministically. |
| 83 | P1 | Financial tracking | Add refund, credit, chargeback, and supplier-recovery tracking. | Each case traces expected, requested, received/paid, outstanding, currency, owner, and evidence. |
| 84 | P1 | Financial tracking | Define margin and commission calculations with source and currency policy. | Reports reconcile to transaction-level evidence and state assumptions. |
| 85 | P1 | Operations | Reduce queue duplication and guarantee one source-linked actionable item per unresolved obligation. | Deduplication and reopen behavior pass across requests, workflows, tasks, SLA, documents, and disruptions. |
| 86 | P1 | Operations | Add shift handover and ownership coverage controls. | Unassigned, absent-owner, overdue, departure-critical, and unresolved external-wait items are visible at handover. |
| 87 | P1 | Operations | Add operator-safe retry/recovery for failed idempotent automations. | Retry shows original event, deduplication key, effects, warnings, and audit result. |
| 88 | P1 | Operations | Validate allowed Kanban/workflow transitions and prevent display-only state drift. | Every move invokes a guarded transition and updates queue, task, SLA, and timeline consistently. |
| 89 | P1 | Reporting | Publish a V1 KPI dictionary with canonical source, filter, timezone, currency, and owner. | Request, conversion, offer, booking, service, SLA, revenue, and margin metrics reproduce from source records. |
| 90 | P1 | Reporting | Build owner and operations reports that reconcile to queue and trip records. | Sampled totals and drill-down records agree; unknown data is reported explicitly. |
| 91 | P1 | Reporting | Build finance reconciliation and outstanding-liability reports. | Customer receivables, supplier liabilities, refunds, credits, fees, and commissions tie to ledger records. |
| 92 | P1 | SaaS | Decide and document the V1 commercial entitlement model. | The product clearly states whether plans are enforced, manually governed, or out of scope; UI/API behavior agrees. |
| 93 | P1 | SaaS | Consolidate feature flags, bundles, assignments, rollout plans, and approvals into one supportable governance flow. | Platform staff can explain an agency's effective configuration without interpreting multiple metadata registers. |
| 94 | P2 | Frontend | Remove duplicate route registrations and orphan page modules after confirming compatibility behavior. | Route inventory has one primary component per canonical path and no unreachable production page. |
| 95 | P2 | Backend | Classify every collection owner and convert remaining critical indexes to governed query-index registration. | Startup inventory names ownership, tenant field, lifecycle owner, and compatible index purpose. |
| 96 | P2 | Backend | Review the 29 heuristically unused model/schema classes and repeated public helper names. | Each is removed, documented as compatibility/public API, or linked to a concrete caller. |
| 97 | P2 | Documentation | Reconcile implemented capabilities, route inventory, model ownership, and operational runbooks. | Documentation links to canonical code owners and no capability is described as executable when metadata-only. |
| 98 | P2 | Training | Create role-based operator playbooks for request, offer, booking, ticket/EMD, service, finance, disruption, and incident handling. | A new agent completes observed scenarios without developer intervention. |
| 99 | P2 | Pilot | Run supervised pilot UAT with agency owner, agent, and client roles using bounded service/airline scope. | Findings have severity, owner, workaround, resolution evidence, and explicit go/no-go decision. |
| 100 | P2 | Version 1 | Freeze the V1 claim set and operating boundaries. | Release notes state supported workflows, manual/external steps, exclusions, known limitations, support hours, and stop criteria. |

## Completion Rule

P0 tasks are conjunctive: one unresolved P0 keeps external-pilot readiness blocked. P1 tasks may be scoped out only by removing the affected capability from the V1 claim set and documenting the operator workaround and customer impact. P2 tasks can remain open only when they do not weaken security, tenant isolation, data integrity, financial accuracy, or the bounded pilot's daily workflow.
