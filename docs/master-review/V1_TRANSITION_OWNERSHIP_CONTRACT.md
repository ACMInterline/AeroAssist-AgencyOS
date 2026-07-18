# AeroAssist V1 Transition Ownership Contract

## Contract Rules

The table below names existing record families. “Projection” means a mutable operational view or compatibility representation; it is not a competing source of truth. “Evidence” means immutable or append-only history that must not be rewritten to match a mutable workspace.

| Object | Canonical record family and source collection | Mutable projections/workspaces | Immutable snapshots/evidence | Create and mutation owner | Archive owner | Downstream direction and compatibility | Forbidden reverse transition |
|---|---|---|---|---|---|---|---|
| Client | `ClientMasterRecord` in `client_master_records` | `client_profiles`, CRM/client overview projections | `client_passenger_links`, audit events | Client/CRM master service; agency-authorized staff | Client master lifecycle owner | Client -> relationship, request, trip, offer, invoice; legacy profile IDs remain mapped | Passenger, request, invoice, or portal projection must not rewrite client identity |
| Passenger | `PassengerMasterRecord` in `passenger_master_records` | `passenger_profiles`, `passenger_workspaces`, request/trip passenger snapshots | known-document and service-history records; audit | Passenger master service; agency-authorized staff | Passenger master lifecycle owner | Passenger -> request/trip snapshots, services, booking, ticket, EMD | Journey snapshots and ticket data must not silently rewrite identity history |
| Request | `TravelRequest` in `travel_requests` with scoped records in `request_passengers`, `request_segments`, and requested-service collections | `travel_request_workspaces`, request builder/detail projections | request timeline, messages, conversion source snapshots | Request intake/builder service | Request owner under agency retention policy | Request -> conversion plan/mapping -> Trip | Trip state must not overwrite intake truth or reuse request ID as trip ID |
| Trip | `TripDossier` in `trip_dossiers` | `trip_workspaces`, journey/segment/service projections | conversion results/mappings, `trip_timeline_events` | Request-to-trip conversion then Trip owner | Trip owner after completion checks | Trip -> Offer, Booking, Service, Document, Finance, After Sales | Offer/booking/service projections must not rewrite conversion source evidence |
| Offer | `OfferWorkspace` in `offer_workspaces` and its option/segment/price child collections | Offer builder, comparison, delivery views | comparison/delivery snapshots and offer timeline | Offer Builder service | Offer owner after supersession/expiry | Trip -> mutable Offer -> explicit acceptance | Acceptance or booking must not mutate the historical request/trip facts |
| Accepted Offer | `OfferAcceptance` in `offer_acceptances` plus `trip_accepted_offer_snapshots` | Readiness summaries only | frozen accepted option, passenger, segment, service, and price snapshot | Offer Acceptance service; explicit authorized acceptance | Retained as immutable audit evidence | Accepted Offer -> BookingReadinessPackage -> Booking Handoff | Later Offer edits, Booking edits, or finance changes must not rewrite accepted evidence |
| Booking Handoff | `OfferBookingHandoff` in `offer_booking_handoffs` | checks, mappings, instructions in handoff child collections | assessment snapshots, workflow/audit/timeline events | Offer-to-booking handoff service | Handoff owner when cancelled/archived | Frozen Accepted Offer -> Handoff -> Booking workspace/record | Direct primary-UI readiness-to-booking bypass; Booking must not backfill a missing accepted snapshot |
| Booking | `BookingWorkspace`/`BookingRecord` in `booking_workspaces` and `booking_records` | booking detail, imported/manual result views | accepted snapshot reference, readiness/handoff instructions, booking timeline/import evidence | Booking service from canonical handoff; external result recorded by authorized agency staff | Booking owner | Booking -> Ticket, EMD, Service linkage, Document, Finance, After Sales | External booking result must not alter frozen accepted price or passenger identity |
| Ticket | `TicketRecord` and `TicketCoupon` in `ticket_records` and `ticket_coupons` | ticket workspace/read views and compatibility `ticket_workspaces` metadata | external evidence, fare/coupon snapshots, ticket/booking/trip timelines, audit | Ticket/EMD service; manual external-result recorder and reconciler | Ticket lifecycle owner via guarded servicing | Booking -> externally obtained Ticket -> reconciliation -> Finance/After Sales | Ticket must not originate Passenger Service need or imply provider issuance from a local record |
| EMD | `EMDRecord` and `EmdCoupon` in `emd_records` and `emd_coupons` | EMD workspace/read views and compatibility `emd_workspaces` metadata | external evidence, RFIC/RFISC/service association snapshots, timeline/audit | Ticket/EMD service; manual external-result recorder and reconciler | EMD lifecycle owner via guarded servicing | Booking/Passenger Service -> EMD -> fulfilment/Finance/After Sales | EMD must not create passenger need or imply external issuance/fulfilment without evidence |
| Passenger Service Case | `PassengerServiceRequest` in `passenger_service_requests` | `SsrOsiWorkspace`, `PassengerServiceWorkflow`, service panels | airline/airport evidence references, reconciliation snapshots, timeline/audit | Special Services service from Request/Trip need; fulfilment actions remain with that owner | Passenger-service owner after final outcome | Request/Trip -> Booking/confirmation/Documents/EMD -> fulfilment outcome | Ticket must not create the need; SSR text must not imply airline confirmation |
| Document Requirement | `DocumentWorkspace` in `document_workspaces` | Documents/Passenger Services operational views | render job/output links, explicit review actor/time, audit/timeline | Document Workspace service; explicit operator reconciliation | Document workspace lifecycle/retention owner | Service/Trip/Booking -> requirement -> received/generated/reviewed result | Render output must not automatically verify the requirement |
| Rendered Document | `DocumentRenderJob`/render output in `document_render_jobs` and existing rendered-document collections | preview/package/share views | frozen render input/output metadata and checksums where available | Document render service; operator explicitly attaches to requirement | Document/render retention owner | Source context -> rendered output -> optional DocumentWorkspace reconciliation | Rendering must not create financial truth, verify a requirement, send, publish, or sign |
| Invoice | `Invoice` in `invoices` with `invoice_line_items` | Finance and optional document presentation views | issued snapshots/timelines where available; after-sales before/proposed/final snapshots | Finance router/service and authorized agency finance role | Finance lifecycle owner | Accepted Offer/Booking -> Invoice -> Payment/reconciliation -> optional After Sales | Document rendering, Payment, or After Sales must not silently rewrite issued history |
| Payment | `PaymentRecord` in `payment_records` | Finance reconciliation views | external/manual payment reference and reconciliation audit | Finance owner; authorized agency role | Finance lifecycle owner | Invoice -> Payment evidence -> reconciliation -> optional After Sales | A manual estimate or rendered receipt must not claim payment or settlement |
| After Sales Case | `AfterSalesCase` in `after_sales_cases` with child case/decision/impact/resolution/communication collections | After Sales case workspace | coupon, financial, accepted-offer, decision, and resolution snapshots; timeline/audit/workflow | After Sales workflow service; authorized agency staff | After Sales owner | Trip/Booking/Ticket/EMD/Service/Finance/disruption/client request -> Case | Case estimates must not mutate Ticket, EMD, Invoice, Payment, or accepted snapshots |
| Operational Work Item | `OperationalWorkItem` in `operational_work_items` | queue definitions/views and source compatibility mappings | `operational_assignment_events` and work-item history | Agent Work Queue service; source owner synchronizes one item | Queue owner on completion/cancellation | Source obligation -> one deterministic work item -> assignment/closure | Queue status must not overwrite source-domain state or create duplicate task systems |
| Timeline / Audit Event | `OperationalTimeline` in `operational_timelines`, domain timelines, and `AuditEvent` in `audit_events` | chronological/operator and client-safe projections | append-only event payload and actor/time/source/target evidence | The service owning the state-changing action | Retention/governance owner; not normal business mutation | Source transition -> append evidence -> filtered projections | Timeline/audit history must not be edited to manufacture state or leak internal fields |

## Transition Evidence Envelope

Every state-changing action touched by V1 integration must carry this information in its existing audit, timeline, or workflow payload:

```text
agency_id
actor_user_id
source_entity_type + source_entity_id
target_entity_type + target_entity_id
correlation_id (deterministic for retried linkage)
occurred_at
result
warnings[]
visibility: internal and client-safe summaries kept separate
```

The envelope is reused inside existing event models. It is not a new global event subsystem.

## Compatibility Obligations

- Legacy profile/workspace records stay readable while their canonical master/source ID remains explicit.
- Existing route families stay available when removal would break known callers, but canonical UI navigation uses the contract above.
- Compatibility booking creation must require the same frozen accepted-offer snapshot and agency ownership as the Booking Handoff.
- Unknown or incomplete external state remains `unknown`, `manual_review`, or an explicit warning.
- Historical snapshots, imports, accepted offers, invoice evidence, and event history are not destructively normalized.

## Mutation Authority

An authorized actor may record a manual or external result only through the domain service that owns it. A linked downstream service may request a projection or write evidence, but it may not seize mutation ownership. Human authority remains final for acceptance, confirmation, verification, reconciliation, financial approval, and after-sales resolution.
