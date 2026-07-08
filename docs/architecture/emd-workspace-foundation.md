# EMD Workspace Foundation

Phase 41.8 adds the metadata-only EMD workspace layer for AeroAssist operations.

This foundation is intentionally separate from execution. It links an agency EMD workspace to operational workspaces, trips, offers, bookings, ticket workspaces, ticket/EMD mirrors, SSR/OSI references, RFIC/RFISC service mechanics, ancillary service metadata, and pricing/payment notes without creating a second EMD issuance architecture.

## Data Model

The `emd_workspaces` collection stores operational EMD metadata:

- `agency_id`, `operational_workspace_id`, `trip_workspace_id`, `offer_workspace_id`, `booking_workspace_id`, `ticket_workspace_id`
- `emd_reference`, `emd_status`, `emd_document_status`, `emd_type`, `emd_number`, `emd_form_type`, `emd_a_or_s`
- `validating_carrier`, `issuing_agent`, `issuing_office`, `issue_date`
- `passenger_id`, `passenger_name`
- `booking_reference`, `airline_pnr`, `gds_record_locator`
- `associated_ticket_number`, `associated_ticket_coupon_numbers`, `associated_flight_workspace_ids`
- `ssr_ids`, `osi_ids`, `ancillary_service_ids`
- `rfic`, `rfisc`, `service_reason`, `service_description`, `service_category`, `service_status`, `service_quantity`, `service_route_scope`, `service_segment_scope`
- `emd_coupon_status_summary`, `emd_coupon_details`
- `fare_amount`, `taxes_amount`, `total_amount`, `currency`, `tax_breakdown`
- `form_of_payment`, `payment_reference`, `payment_restrictions`
- `exchange_reference_ids`, `refund_reference_ids`, `void_reference_ids`, `linked_document_ids`
- `lifecycle_notes`, `operational_notes`

`emd_coupon_details` is metadata only and may include coupon number, coupon status, associated ticket/coupon references, flight workspace reference, segment, origin, destination, RFIC/RFISC, service description/date, validity dates, amount, currency, and remarks.

## APIs And UI

Platform metadata APIs live under `/api/platform/emd-workspaces`. Platform users may list, read, create, update, and metadata-archive records.

Agency read-only APIs live under `/api/agencies/{agency_id}/emd-workspaces`. Agency users can list, summarize, and read only records scoped to their agency.

Frontend pages:

- `/platform/emd-workspaces`
- `/agency/emd-workspaces`

Both pages show EMD document status, EMD-A/EMD-S type, RFIC/RFISC, associated ticket/coupon and flight references, service metadata, coupon details, fare/tax/payment metadata, exchange/refund/void references, linked documents, lifecycle notes, and operational notes.

## Safety Boundary

Phase 41.8 does not issue EMDs, exchange EMDs, refund EMDs, void EMDs, validate RFIC/RFISC, transmit SSR/OSI, process payments, connect to GDS or NDC, call airline APIs, run background workers, call external integrations, or automate EMD operations.

It reuses and links to the earlier ticket/EMD mirror, service mechanics, and ancillary pricing foundations. It does not create parallel duplicate EMD execution architecture.

The `/api/readiness` payload exposes `emd_workspace_foundation` and the active phase marker is `phase_41_8_emd_workspace_foundation`.
