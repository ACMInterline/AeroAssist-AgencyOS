# AeroAssist Golden Path Integration Audit

## Audit question

Can an agency operator move a real case through the following chain using the implemented product, with each handoff owning state, persisting a result, and leaving enough operational evidence for the next team member?

`Client -> Passenger -> Request -> Trip -> Offer -> Booking -> Ticket -> Passenger Services -> Documents -> Financial Tracking -> After Sales`

This review evaluates transitions only. A destination module being present is not evidence that the preceding module can hand work to it. A foreign key is not a transition unless an operator can invoke a governed action, the system validates it, and the result is persisted and traceable.

## Overall verdict

**BROKEN**

| Verdict | Transitions |
| --- | ---: |
| PASS | 1 |
| PASS WITH WARNINGS | 6 |
| BROKEN | 3 |
| UNKNOWN | 0 |

The path reaches Ticket through usable, though fragmented, handoffs. It then breaks because no Ticket-to-Passenger-Services transition exists. The proposed Documents-to-Financial-Tracking direction also does not exist; the implemented product creates finance records first and may render an invoice document afterward. Finally, Financial Tracking cannot hand an invoice or payment into an After Sales case.

```mermaid
flowchart LR
    C["Client"] -->|"PASS WITH WARNINGS"| P["Passenger"]
    P -->|"PASS WITH WARNINGS"| R["Request"]
    R -->|"PASS"| T["Trip"]
    T -->|"PASS WITH WARNINGS"| O["Offer"]
    O -->|"PASS WITH WARNINGS"| B["Booking"]
    B -->|"PASS WITH WARNINGS"| K["Ticket"]
    K -->|"BROKEN"| S["Passenger Services"]
    S -->|"PASS WITH WARNINGS"| D["Documents"]
    D -->|"BROKEN"| F["Financial Tracking"]
    F -->|"BROKEN"| A["After Sales"]
```

## Verdict rules

- **PASS:** a dedicated operator action validates the handoff, persists authoritative state and mappings, is idempotent where duplication is dangerous, and records adequate audit/timeline/workflow evidence.
- **PASS WITH WARNINGS:** the handoff is usable, but important traceability, consistency, navigation, or downstream synchronization is missing.
- **BROKEN:** no implemented transition exists, the stated direction is invalid, or an operator cannot carry the required state into the destination.
- **UNKNOWN:** implementation evidence is insufficient to determine behavior.

## Transition summary

| # | Transition | Verdict | Operational finding |
| ---: | --- | --- | --- |
| 1 | Client -> Passenger | PASS WITH WARNINGS | A governed relationship can be created, but it is an association rather than a lifecycle handoff and has no timeline, queue, or workflow record. |
| 2 | Passenger -> Request | PASS WITH WARNINGS | Request Builder snapshots passengers and validates service scope, but workflow and triage queue creation are not part of the same transaction. |
| 3 | Request -> Trip | PASS | Dedicated preview, validation, execution, mapping, idempotency, timeline, workflow, task, and deadline behavior form a complete handoff. |
| 4 | Trip -> Offer | PASS WITH WARNINGS | An operator can create or reopen an offer workspace from a trip, but there is no transition timeline/workflow and overlapping offer-workspace implementations remain. |
| 5 | Offer -> Booking | PASS WITH WARNINGS | Frozen acceptance, readiness, and booking handoff are strong, but the UI retains a direct readiness-to-booking path that can bypass the canonical handoff. |
| 6 | Booking -> Ticket | PASS WITH WARNINGS | An agent can record an externally issued ticket, but state is split across legacy and newer record families and the action does not close queue/workflow work atomically. |
| 7 | Ticket -> Passenger Services | BROKEN | No ticket-driven service transition exists; services are normally requested before ticketing from request, trip, or booking context. |
| 8 | Passenger Services -> Documents | PASS WITH WARNINGS | A document can be rendered from a service-request context, but the agent must initiate it manually and rendering does not close the operational document requirement. |
| 9 | Documents -> Financial Tracking | BROKEN | No document-to-finance API or UI exists. The implemented direction is finance-to-rendered-invoice-document. |
| 10 | Financial Tracking -> After Sales | BROKEN | After Sales stores manual financial estimates but cannot link or reconcile source invoices and payments. |

## 1. Client -> Passenger

**Verdict: PASS WITH WARNINGS**

| Audit question | Finding |
| --- | --- |
| 1. Which model owns the state? | `ClientPassengerRelationship` owns the operational relationship between `ClientProfile` and `PassengerProfile`. A separate `ClientPassengerMasterLink` also represents this concept in the master-record layer. |
| 2. Which API performs the transition? | `POST /api/agencies/{agency_id}/client-passenger-relationships` validates both records and rejects duplicate active relationships. |
| 3. Which UI performs the transition? | `ClientDetailPage.jsx` uses `RelationshipEditor.jsx`; passenger detail also displays relationship context. |
| 4. Which collection stores the transition? | `client_passenger_relationships`. The overlapping master relationship uses `client_passenger_links`. |
| 5. Which audit trail records it? | `audit_events`, event `relationship.created`; update and archive actions also write relationship events. |
| 6. Which timeline records it? | None. |
| 7. Which queue records it? | None. |
| 8. Which workflow records it? | None. |
| 9. Which document records it? | None, and none is required for the relationship itself. |
| 10. Which downstream objects depend on it? | Request passenger selection, guardian/payer/contact semantics, client portal passenger access, and relationship-aware request validation. |

The operator can perform and audit the association. The warning is that two relationship representations coexist and no unified operational history records when the passenger became connected to the client.

**Evidence:** `backend/models.py` (`ClientPassengerRelationship`), `backend/routers/clients.py`, `frontend/src/pages/agency/ClientDetailPage.jsx`, `frontend/src/components/RelationshipEditor.jsx`.

## 2. Passenger -> Request

**Verdict: PASS WITH WARNINGS**

| Audit question | Finding |
| --- | --- |
| 1. Which model owns the state? | `TravelRequest` owns the request; `RequestPassenger` owns the passenger snapshot and role within that request. Segment-scoped service applicability is normalized in `RequestPassengerSegmentService`. |
| 2. Which API performs the transition? | `POST /api/agencies/{agency_id}/requests/builder` creates the request graph. `POST /api/agencies/{agency_id}/requests/{request_id}/passengers` adds a passenger later. |
| 3. Which UI performs the transition? | `RequestCreatePage.jsx` performs the builder submission; `RequestDetailPage.jsx` supports later passenger additions. |
| 4. Which collection stores the transition? | `travel_requests`, `request_passengers`, `request_segments`, `requested_services`, and `request_passenger_segment_services`. |
| 5. Which audit trail records it? | `audit_events`, including `request.builder_created` and `request.passenger_added`. |
| 6. Which timeline records it? | `request_timeline_events` records builder creation and passenger additions. |
| 7. Which queue records it? | No queue item is created atomically by Request Builder. `AgentWorkQueueService` can later synchronize an idempotent `new_request_triage` item into `operational_work_items`. |
| 8. Which workflow records it? | No workflow instance is created as part of Request Builder. Workflow initialization is a later operation. |
| 9. Which document records it? | No document is generated; the request and passenger snapshots are the persisted intake record. |
| 10. Which downstream objects depend on it? | Request-to-trip conversion, trip passengers, service requirements, offer preparation, SLA/triage, portal views, and operational readiness. |

The request can carry a passenger and preserve intake truth. The handoff is not fully operationally atomic because triage queue and workflow state can lag behind the request transaction.

**Evidence:** `backend/models.py` (`RequestPassenger`), `backend/routers/requests.py`, `frontend/src/pages/agency/RequestCreatePage.jsx`, `frontend/src/pages/agency/RequestDetailPage.jsx`, `backend/services/agent_work_queue_service.py`.

## 3. Request -> Trip

**Verdict: PASS**

| Audit question | Finding |
| --- | --- |
| 1. Which model owns the state? | `RequestTripConversionRun` owns the handoff result; `RequestTripEntityMapping` owns source-to-target mappings; `TripDossier` becomes the downstream operational owner. |
| 2. Which API performs the transition? | `POST /api/agencies/{agency_id}/request-trip-conversion/preview`, `/validate`, and `/execute`. Execution can create a new trip or attach to an explicitly selected existing trip. |
| 3. Which UI performs the transition? | `RequestTripConversionPage.jsx`, entered from `RequestDetailPage.jsx`. |
| 4. Which collection stores the transition? | `request_trip_conversion_plans`, `request_trip_conversion_runs`, `request_trip_entity_mappings`, `request_trip_conversion_issues`; target records are stored in `trip_dossiers`, `trip_passengers`, `trip_segments`, and `trip_service_items`. |
| 5. Which audit trail records it? | `audit_events` records `trip_created_from_request`; conversion run records preserve actor, source snapshot, result snapshot, warnings, and issues. |
| 6. Which timeline records it? | `request_timeline_events` and `trip_timeline_events` record `request_trip_conversion_executed`. |
| 7. Which queue records it? | Generated safe tasks can synchronize into `operational_work_items`; final document checking is seeded as downstream work. |
| 8. Which workflow records it? | `operational_workflow_instances` and `operational_workflow_events` start the trip lifecycle and record the conversion event. |
| 9. Which document records it? | No document artifact is created; document readiness is represented by generated downstream work, which is appropriate at this handoff. |
| 10. Which downstream objects depend on it? | Trip passengers and segments, service cases, offer workspaces, booking handoff, tasks, deadlines, timeline, and later document readiness. |

This is the reference-quality transition in the audited path: preview, critical validation, warning-tolerant conversion, mapping, immutable source evidence, idempotency, and operational integrations are all present.

**Evidence:** `backend/models.py` (`RequestTripConversionRun`, `RequestTripEntityMapping`), `backend/routers/agency_request_trip_conversion.py`, `backend/services/request_to_trip_conversion_service.py`, `frontend/src/pages/agency/RequestTripConversionPage.jsx`.

## 4. Trip -> Offer

**Verdict: PASS WITH WARNINGS**

| Audit question | Finding |
| --- | --- |
| 1. Which model owns the state? | The active builder uses `OfferWorkspace` and its option, routing, segment, fare-bundle, and pricing-line children. `OfferWorkspaceV2` is a separate overlapping record family. |
| 2. Which API performs the transition? | `POST /api/agencies/{agency_id}/trips/{trip_id}/offer-workspace`; the service reuses an existing workspace for the trip when appropriate. |
| 3. Which UI performs the transition? | `TripDetailPage.jsx` provides “Create / open offer workspace” and navigates to the offer workspace. |
| 4. Which collection stores the transition? | `offer_workspaces`, followed by `offer_options`, `offer_routing_options`, `offer_segments`, `offer_fare_bundles`, and `offer_pricing_lines`. |
| 5. Which audit trail records it? | `audit_events`, event `offer_workspace.created`. |
| 6. Which timeline records it? | No trip or offer timeline entry is written by workspace creation. |
| 7. Which queue records it? | None at workspace creation. |
| 8. Which workflow records it? | None at workspace creation. |
| 9. Which document records it? | None; offer rendering is a later action. |
| 10. Which downstream objects depend on it? | Offer options, comparison snapshots, recommendation trace, pricing, acceptance, booking readiness, and booking handoff. |

The operator has a clear action and reaches the correct builder. The warning is not cosmetic: overlapping workspace models and the absence of timeline/workflow progression make it harder to establish one authoritative offer lifecycle.

**Evidence:** `backend/models.py` (`OfferWorkspace`), `backend/routers/agency_offer_builder.py`, `backend/services/offer_builder_service.py`, `frontend/src/pages/agency/TripDetailPage.jsx`.

## 5. Offer -> Booking

**Verdict: PASS WITH WARNINGS**

| Audit question | Finding |
| --- | --- |
| 1. Which model owns the state? | `OfferAcceptance` and the immutable accepted-offer snapshot own the commercial decision. `BookingReadinessPackage` and `OfferBookingHandoff` own readiness and handoff; `BookingWorkspace`/`BookingRecord` own the destination. |
| 2. Which API performs the transition? | Accept with `POST /api/agencies/{agency_id}/offer-workspaces/{workspace_id}/options/{option_id}/accept`; create, assess, and execute handoff through `/api/agencies/{agency_id}/booking-handoffs`; create the booking workspace through `/{handoff_id}/create-booking-workspace`. |
| 3. Which UI performs the transition? | `OfferWorkspaceDetailPage.jsx` accepts the offer and opens handoff/readiness. `BookingHandoffsPage.jsx` performs assessment and booking creation. The offer page also exposes a direct readiness-to-booking action. |
| 4. Which collection stores the transition? | `offer_acceptances`, `trip_accepted_offer_snapshots`, `booking_readiness_packages`, `offer_booking_handoffs`, `offer_booking_handoff_checks`, `offer_booking_handoff_mappings`, `booking_execution_instructions`, `booking_workspaces`, and `booking_records`. |
| 5. Which audit trail records it? | `audit_events` records `offer_acceptance.accepted`. Handoff records preserve snapshots and actor fields, but conventional audit-event coverage is incomplete across all handoff mutations. |
| 6. Which timeline records it? | `operational_timelines` records handoff and booking creation; booking-specific timeline records are also created. |
| 7. Which queue records it? | `operational_work_items` receives booking-readiness and booking-created work through `AgentWorkQueueService`. |
| 8. Which workflow records it? | `operational_workflow_instances` and `operational_workflow_events` record readiness/handoff progression. |
| 9. Which document records it? | No document artifact is produced by the handoff. Required-document references are readiness inputs. |
| 10. Which downstream objects depend on it? | Booking/import instructions, booking passengers and segments, tickets, EMDs, payments, passenger services, and documents. |

The canonical handoff correctly uses the frozen accepted snapshot and guards readiness. However, `OfferWorkspaceDetailPage.jsx` can call the direct `booking-workspaces/from-readiness` path, allowing operators to bypass the richer handoff record and mappings.

**Evidence:** `backend/routers/agency_offer_acceptance.py`, `backend/routers/agency_offer_booking_handoffs.py`, `backend/services/offer_to_booking_handoff_service.py`, `frontend/src/pages/agency/OfferWorkspaceDetailPage.jsx`, `frontend/src/pages/agency/BookingHandoffsPage.jsx`.

## 6. Booking -> Ticket

**Verdict: PASS WITH WARNINGS**

| Audit question | Finding |
| --- | --- |
| 1. Which model owns the state? | `TicketRecord` and `TicketCoupon` own current operational ticket records. A separate read-oriented `TicketWorkspace` exists, while booking state is divided among `Booking`, `BookingWorkspace`, and `BookingRecord`. |
| 2. Which API performs the transition? | Legacy booking UI uses `POST /api/agencies/{agency_id}/bookings/{booking_id}/tickets`. Newer paths use `POST /api/agencies/{agency_id}/tickets/from-booking-record` or `/tickets/manual`. |
| 3. Which UI performs the transition? | `BookingDetailPage.jsx` provides “Record ticket” for a ticket issued outside AeroAssist. Booking workspace/import pages lead to manual or imported ticket recording. |
| 4. Which collection stores the transition? | `ticket_records` and `ticket_coupons`, linked to `bookings` or `booking_records`; `ticket_workspaces` is a separate representation. |
| 5. Which audit trail records it? | The legacy record-ticket action does not write the shared `audit_events` ledger. Actor fields and timeline entries provide partial provenance. |
| 6. Which timeline records it? | `booking_timeline_events` records `booking.ticket_recorded`; newer ticket/EMD operations use `ticket_emd_timeline_events` and may add trip context. |
| 7. Which queue records it? | No work-item completion or creation is atomic with recording the ticket. |
| 8. Which workflow records it? | No workflow stage transition is atomic with recording the ticket. |
| 9. Which document records it? | A ticket receipt can be rendered afterward; no receipt or source evidence is required or created by the transition itself. |
| 10. Which downstream objects depend on it? | Coupons, EMDs, document rendering, passenger/travel readiness, financial tracking, exchange/refund servicing, and after-sales impact analysis. |

An agent can accurately record a real externally issued ticket, which is enough for a usable handoff. It is not closed-loop: the product does not reconcile provider truth, require source evidence, or atomically advance workflow and queue state.

**Evidence:** `backend/models.py` (`TicketRecord`, `TicketWorkspace`), `backend/routers/bookings.py`, `backend/routers/agency_ticket_emd.py`, `backend/services/ticket_emd_service.py`, `frontend/src/pages/agency/BookingDetailPage.jsx`.

## 7. Ticket -> Passenger Services

**Verdict: BROKEN**

| Audit question | Finding |
| --- | --- |
| 1. Which model owns the state? | No model owns a ticket-to-service handoff. `PassengerServiceRequest` owns service requirements; `SsrOsiWorkspace` owns SSR/OSI operational records. |
| 2. Which API performs the transition? | None. Service creation APIs operate from request or trip, and parsed-PNR import can attach services to a booking. No API creates or advances a passenger service from a ticket. |
| 3. Which UI performs the transition? | None. `PassengerServicesPage.jsx` is read-only, and ticket pages expose no service-handoff action. |
| 4. Which collection stores the transition? | None. Ticket and service collections may share trip/booking context, but no transition record or mapping is persisted. |
| 5. Which audit trail records it? | None. Service creation has its own `passenger_service_request.created` audit event, not a ticket-service transition. |
| 6. Which timeline records it? | None. |
| 7. Which queue records it? | None. |
| 8. Which workflow records it? | `PassengerServiceWorkflow` may independently reference ticket and SSR/OSI workspaces, but it does not record this transition. |
| 9. Which document records it? | None. |
| 10. Which downstream objects depend on it? | Airline approvals, SSR/OSI confirmation, EMD requirements, service documents, airport handling, and travel readiness would need a reliable service state, but ticketing does not supply it. |

The stated sequence is operationally incorrect. Passenger services are requirements that should be established from passenger/request/trip context before ticketing, then tracked through booking, airline approval, EMD, document, and fulfillment state. Ticketing can become evidence or a dependency of service fulfillment; it is not the implemented source of service requirements.

**Evidence:** `backend/routers/agency_special_services.py`, `backend/models.py` (`PassengerServiceRequest`, `SsrOsiWorkspace`), `frontend/src/pages/agency/PassengerServicesPage.jsx`, `backend/services/passenger_service_workflow_service.py`.

## 8. Passenger Services -> Documents

**Verdict: PASS WITH WARNINGS**

| Audit question | Finding |
| --- | --- |
| 1. Which model owns the state? | `DocumentRenderJob` owns this render path and stores its HTML/text output. The separate `DocumentWorkspace` owns operational document requirements and verification state; `RenderedDocument` exists in another document path but is not created here. |
| 2. Which API performs the transition? | `POST /api/agencies/{agency_id}/documents/context-preview` and `POST /api/agencies/{agency_id}/documents/render-jobs` with `source_context_type=service_request`. |
| 3. Which UI performs the transition? | `DocumentsPage.jsx` can select a service-request source and render. `PassengerServicesPage.jsx` has no direct action, so the operator must navigate and provide the source reference manually. |
| 4. Which collection stores the transition? | `document_render_jobs`; optional packaging uses `document_packages`. The action creates neither a `rendered_documents` record nor an update to `document_workspaces`. |
| 5. Which audit trail records it? | The render job stores actor and source context, but the service does not write the shared `audit_events` ledger. |
| 6. Which timeline records it? | The render-job path does not add an operational timeline entry or service timeline entry. |
| 7. Which queue records it? | None; missing-document work is not closed by rendering. |
| 8. Which workflow records it? | None; passenger-service readiness is not advanced by rendering. |
| 9. Which document records it? | `DocumentRenderJob` persists the source context and rendered HTML/text. It does not promote that output into the separate `rendered_documents` collection. |
| 10. Which downstream objects depend on it? | Document packages, controlled sharing/delivery records, booking/trip document sets, client visibility, and service readiness. |

The product can produce a document from service context, so the handoff is usable. It remains open-loop because generated output is not reconciled to the operational document requirement, verification status, service case, queue item, or workflow stage.

**Evidence:** `backend/models.py` (`DocumentRenderJob`, `DocumentWorkspace`), `backend/routers/agency_documents.py`, `backend/services/document_context_service.py`, `backend/services/document_render_service.py`, `frontend/src/pages/agency/DocumentsPage.jsx`.

## 9. Documents -> Financial Tracking

**Verdict: BROKEN**

| Audit question | Finding |
| --- | --- |
| 1. Which model owns the state? | No model owns a document-to-finance transition. `Invoice`, `InvoiceLineItem`, and `PaymentRecord` own finance state. |
| 2. Which API performs the transition? | None. Finance APIs create invoices, line items, and payments from booking/agency context. Invoice rendering occurs after the invoice exists. |
| 3. Which UI performs the transition? | None. Document pages do not create or reconcile finance records. Finance and booking pages create financial records, and invoice detail may render the invoice document afterward. |
| 4. Which collection stores the transition? | None. Source finance data is stored in `invoices`, `invoice_line_items`, and `payment_records`. |
| 5. Which audit trail records it? | None for this transition. Finance creation and status actions have their own `audit_events`. |
| 6. Which timeline records it? | None for this transition. Finance actions may add `booking_timeline_events`. |
| 7. Which queue records it? | None. |
| 8. Which workflow records it? | None. |
| 9. Which document records it? | An invoice document can be rendered downstream of an existing invoice; it does not create the financial obligation. |
| 10. Which downstream objects depend on it? | Booking balances, payment reconciliation, client reporting, release blockers, and after-sales financial assessment depend on finance records, but not on a document handoff. |

The proposed direction is reversed. A rendered invoice is evidence or presentation of financial state; it is not the authoritative source of that state. No implemented action derives an invoice or payment from a document.

**Evidence:** `backend/models.py` (`Invoice`, `PaymentRecord`), `backend/routers/finance.py`, `frontend/src/pages/agency/InvoiceDetailPage.jsx`, `frontend/src/pages/agency/DocumentsPage.jsx`.

## 10. Financial Tracking -> After Sales

**Verdict: BROKEN**

| Audit question | Finding |
| --- | --- |
| 1. Which model owns the state? | `AfterSalesCase` owns the case and `AfterSalesFinancialImpact` owns estimates. Neither owns a source invoice/payment mapping. |
| 2. Which API performs the transition? | None. `POST /api/agencies/{agency_id}/after-sales` creates a case manually; `POST /api/agencies/{agency_id}/after-sales/{case_id}/financial-impacts` records estimates without invoice/payment linkage. |
| 3. Which UI performs the transition? | `AfterSalesPage.jsx` creates a case and financial-impact entries manually. It does not select or carry an invoice or payment from finance. |
| 4. Which collection stores the transition? | None. After-sales data is stored in `after_sales_cases`, `after_sales_case_items`, `after_sales_financial_impacts`, `after_sales_decisions`, `after_sales_resolutions`, and `after_sales_communication_records`. |
| 5. Which audit trail records it? | No shared `audit_events` entry records a finance-to-case handoff. Case records retain actor fields. |
| 6. Which timeline records it? | `operational_timelines` records after-sales case and child-record activity, but not a financial-source transition. |
| 7. Which queue records it? | `operational_work_items` receives after-sales work through `AgentWorkQueueService`. |
| 8. Which workflow records it? | `operational_workflow_instances` and `operational_workflow_events` are created for the case. |
| 9. Which document records it? | The case can reference document workspaces, but no financial advice, refund statement, or settlement document is created by the handoff. |
| 10. Which downstream objects depend on it? | Change/refund/claim decisions, residual-value estimates, penalties, client approval, settlement, communications, and case resolution. |

After Sales has useful case orchestration, but the audited transition does not exist. Financial impact values are free-standing case data rather than reconciled references to invoice lines, payments, refunds, or credits. An agent cannot prove what financial record a case is changing.

**Evidence:** `backend/models.py` (`AfterSalesCase`, `AfterSalesFinancialImpact`), `backend/routers/agency_after_sales_workflows.py`, `backend/services/after_sales_workflow_service.py`, `frontend/src/pages/agency/AfterSalesPage.jsx`, `backend/routers/finance.py`.

## End-to-end proof limitation

`backend/scripts/smoke_end_to_end_operational_workflow_maturity_foundation.py` does not establish that this production workflow works. Its golden-path runs are isolated assessment templates. The associated maturity service explicitly reports that production records were not created. That is useful for deterministic assessment safety, but it cannot substitute for an integration test that invokes the actual request, conversion, offer, acceptance, handoff, booking, ticket, service, document, finance, and after-sales APIs against one correlated case.

## Conclusion

A real agency can progress from client intake to a recorded ticket, but the path is not one coherent operating workflow. Request-to-trip conversion demonstrates the standard the rest of the chain needs: explicit ownership, guarded execution, mappings, idempotency, and correlated evidence. Beyond ticketing, the current chain either changes direction, requires manual re-entry, or has no transition. AeroAssist should therefore not claim a complete Golden Path on the evidence inspected in this audit.
