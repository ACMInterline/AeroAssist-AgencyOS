# Timeline Event Catalog

## Canonical Events

| Event | Meaning |
|---|---|
| `request_created` | Canonical Request was created |
| `offer_created` | Offer preparation record was created |
| `offer_revised` | A new governed Offer version was recorded |
| `offer_delivered` | Immutable Offer delivery evidence was recorded |
| `offer_accepted` | Exact Offer version was accepted |
| `offer_declined` | Offer decision was declined |
| `trip_confirmed` | Trip reached governed confirmed state |
| `booking_prepared` | Booking preparation/handoff evidence was recorded |
| `booking_confirmed` | BookingRecord confirmation evidence was recorded |
| `ticket_imported` | Ticket mirror was imported; no issuance implied |
| `emd_imported` | EMD mirror was imported; no issuance implied |
| `invoice_issued` | Canonical Invoice entered issued state |
| `payment_received` | Received payment evidence was recorded |
| `refund_recorded` | Canonical Refund ledger evidence was recorded |
| `exchange_recorded` | Canonical Exchange ledger evidence was recorded |
| `supplier_cost_confirmed` | Agency-private Supplier Cost was confirmed |
| `portal_login` | Linked Portal identity authenticated |
| `portal_approval` | Governed Portal approval/decision was recorded |
| `document_uploaded` | Document reference was uploaded/registered |
| `document_delivered` | Document delivery evidence was recorded |
| `communication_sent` | Human outbound communication was recorded; provider send is not implied |
| `communication_received` | Human inbound or Portal communication was recorded |
| `manual_note` | Internal operational note was appended |
| `assignment` | Work assignment evidence was recorded |
| `status_transition` | A governed business status transition was recorded |
| `timeline_correction` | Append-only correction supersedes part of prior evidence |
| `timeline_superseded` | Prior entry was superseded without deletion |

## Source-Specific Events

Adapters place historical or module-specific labels in `event_subtype` and
structured `details`. They must select the closest canonical event type rather
than expand an ungoverned top-level vocabulary.

The catalog describes evidence, not execution. `ticket_imported`,
`emd_imported`, `payment_received`, and document or communication events do not
perform the underlying external action.
