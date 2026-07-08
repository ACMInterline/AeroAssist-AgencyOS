# Ticket Workspace Foundation

Phase 41.7 introduces metadata-only ticket workspaces for viewing ticket records inside AeroAssist. A ticket workspace is an agency-scoped record that captures ticket reference, workspace status, whole-ticket document status, ticket number, validating carrier, issuing metadata, passenger, booking links, flight links, fare summaries, fare construction metadata, pricing units, fare components, coupon status summaries, per-coupon detail metadata, lifecycle references, linked EMDs, linked documents, and operational notes.

This phase is intentionally safe and foundational. It does not issue tickets, reissue tickets, void tickets, process refunds, process exchanges, process payments, connect to GDS or NDC, call airline APIs, calculate or recalculate fares, validate tickets or coupons automatically, run background workers, call external integrations, or automate ticket operations.

## Data Model

`TicketWorkspace` records live in the additive `ticket_workspaces` collection and store:

- agency and operational workspace links
- trip, offer, and booking workspace links
- ticket reference, workspace status, type, and ticket number
- `ticket_document_status` for the whole ticket document, such as `draft_metadata`, `issued`, `voided`, `exchanged`, `refunded`, `partially_refunded`, `cancelled`, or `unknown`
- validating carrier, issuing agent, issuing office, and issue date metadata
- passenger identifier and passenger display name
- flight workspace references
- booking reference, airline PNR, and GDS locator metadata
- fare basis summary, fare amount, taxes amount, total amount, and currency metadata
- `fare_calculation_line`, `fare_calculation_currency`, `fare_calculation_nuc_total`, and `fare_calculation_roe` for inert fare construction review metadata
- `equivalent_fare_paid`, `equivalent_fare_currency`, form of payment, payment reference, payment restrictions, commission summary, tax breakdown, and fare construction notes
- `pricing_units` with pricing unit reference, type, origin, destination, fare component references, NUC amount, currency, and notes
- `fare_components` with fare component reference, origin, destination, carrier, fare basis, booking class, NUC amount, mileage/routing note, rule reference, and notes
- `coupon_status_summary` and `coupon_details` for coupon-level travel or usage metadata only
- coupon detail fields such as coupon number, flight workspace, segment reference, origin, destination, marketing carrier, operating carrier, coupon-level fare basis, fare component reference, pricing unit reference, coupon status, validity window, baggage summary, and remarks
- baggage, endorsement, and restriction summaries
- exchange, refund, and void reference id lists for future metadata linking only
- linked EMD and document references
- lifecycle notes, operational notes, and metadata-only safety flags

All records carry disabled flags for ticket issuance, ticket reissue, voiding, refunds, exchanges, payment processing, GDS/NDC connectivity, airline API calls, fare calculation, fare recalculation, automated ticket validation, coupon validation, background workers, external integrations, and automation.

The whole-ticket document status and per-coupon status are intentionally separate. `ticket_document_status` describes the document as a whole. `coupon_details[].coupon_status` describes individual coupon travel/usage metadata such as `open_for_use`, `airport_control`, `checked_in`, `flown`, `closed`, `suspended`, `void`, `exchanged`, `refunded`, or `unknown`. Neither field triggers workflow, validation, exchange, refund, void, provider, or airline behavior.

Fare basis handling is coupon and fare-component related. `fare_basis_summary` is only a readable summary. The source metadata should live on `coupon_details[].fare_basis` and/or `fare_components[].fare_basis` so later exchange foundations can inspect fare construction without calculating, validating, reissuing, or exchanging anything.

## APIs

Platform routes under `/api/platform/ticket-workspaces` provide metadata create, update, archive, list, detail, and summary views.

Agency routes under `/api/agencies/{agency_id}/ticket-workspaces` are read-only and scoped to the agency. They provide list, detail, and summary views only.

Supported metadata filters:

- ticket status
- ticket document status
- validating carrier
- issue date
- passenger
- booking reference
- currency

## UI

Platform Console adds `/platform/ticket-workspaces` as **Ticket Workspaces**.

Agency Workspace adds `/agency/ticket-workspaces` as **Tickets**.

Both pages render read-only tables with ticket reference, ticket number, workspace status, ticket document status, passenger, validating carrier, issue date, booking reference, airline PNR, GDS locator, flights, fare basis summary, fare/tax/total amounts, fare calculation line, NUC total, ROE, equivalent fare paid, form of payment, tax breakdown, pricing units, fare components, coupon status summary, coupon details with coupon-level fare basis, baggage, endorsements, restrictions, exchange/refund/void references, linked EMDs, linked documents, lifecycle notes, and operational notes.

## Database

MongoDB collection registration is additive only. Phase 41.7 registers `ticket_workspaces` with indexes for:

- `id`
- `ticket_reference`
- `agency_id + ticket_status`
- `ticket_document_status`
- `coupon_details.coupon_status`
- `coupon_details.fare_basis`
- fare calculation currency, equivalent fare currency, form of payment, pricing unit references, and fare component references
- `agency_id + validating_carrier`
- `agency_id + issue_date`
- `agency_id + passenger_id`
- `agency_id + booking_reference`
- `agency_id + currency`
- operational workspace, trip workspace, offer workspace, and booking workspace links
- ticket number, airline PNR, GDS locator, flight links, EMD links, document links, exchange references, refund references, void references, and creation time

No destructive migration is introduced.

## Readiness

The `/api/health/ready` payload exposes `ticket_workspace_foundation` with counters and safety flags. The active phase marker is `phase_41_7_ticket_workspace_foundation`.

## Explicit Non-Goals

Phase 41.7 does not implement:

- ticket issuance
- ticket reissue
- voiding
- refunds
- exchanges
- payment processing
- GDS connectivity
- NDC connectivity
- airline APIs
- fare calculation
- fare recalculation
- automated ticket validation
- coupon validation
- background workers
- external integrations
- automation
