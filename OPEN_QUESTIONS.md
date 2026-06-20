# Open Questions

## Resolved Decisions

- MVP uses one primary workspace per agency. `agency_id` is mandatory on every agency-owned table; `agency_workspace_id` may exist for future expansion.
- `client_profile` represents the agency's commercial/account relationship and may be an `individual`, `family_household`, or `organization`.
- Client does not equal traveler. Travelers are always represented by `passenger_profile`.
- Individual travelers have both a client profile and a passenger profile linked by `client_passenger_relationship` with relationship type `self`.
- Organization/company clients are supported in MVP through `client_profile.client_type = organization` and staff-managed `client_contact` records.
- Multiple portal logins for one organization client are not MVP.
- Client self-registration creates `client_account.portal_status = email_unverified` until email verification or invitation acceptance.
- Unverified clients cannot view existing records, accept offers, view bookings/documents, pay, or manage non-self passenger relationships.
- Passenger self-service is agency-configurable and creates proposed relationship records until approved by staff or policy.
- Passenger merge is allowed only within the same agency and only by `agency_owner` or `agency_admin`.
- Historical snapshots and generated documents retain original passenger data after a merge.
- Status enums for core operational records are defined in `CANONICAL_DATA_MODEL.md`.
- Snapshot payload rules for offer, booking, ticket, EMD, invoice, refund, and exchange milestones are defined in `CANONICAL_DATA_MODEL.md`.
- Invoices can exist without bookings in MVP for manual agency billing.
- Payments apply to one invoice in MVP; partial payments and multiple payments per invoice are allowed.
- Unapplied payments, split payments across invoices, and multi-currency invoices are not MVP.
- Refund and exchange use one combined `refund_exchange_case` model with explicit adjustment lines.
- Document retention classes and visibility rules are defined in `CANONICAL_DATA_MODEL.md`.
- Agency airline overrides use a generic typed `agency_airline_override` schema with `replace`, `augment`, and `annotate` modes.
- Platform support access is audited, reason-coded, read-only by default, and does not change tenant data ownership.
- MVP is tracking only for financials, not full accounting, payment processing, general ledger, or tax filing.

## Remaining Product Decisions

- How much public website publishing is required at launch: hosted subdomain only, custom domains, or both?
- Should document generation in the first release use fixed templates only, or allow limited agency-editable content blocks?
- Which exact airline knowledge domains and airlines are required for launch coverage?
- Which early agencies or pilot customers define the first vertical slice acceptance criteria?
- Which launch languages, currencies, and tax display formats are required?

## Remaining Legal And Policy Decisions

- Exact retention periods for identity, medical, consent/legal, financial, and operational documents by launch market.
- Whether hard deletion must be available for specific client/passenger documents under privacy law, and what audit metadata may remain.
- Required consent wording for guardians, assistants, company travel arrangers, and passenger document uploads.
- Whether platform support users may ever edit tenant operational records under emergency support, or only guide agency staff.
- Required data export format for agencies and clients/passengers.

## Remaining Implementation Design Questions

- Exact uniqueness rules for passenger documents, ticket numbers, EMD numbers, invoice numbers, and PNR references per agency.
- Whether invoice numbers are assigned on draft creation or only when issued.
- Whether portal legal identity edits attached to active travel records require mandatory approval or configurable agency approval.
- Exact schema validators for each `airline_knowledge_item.structured_data` domain/layer.
- Exact schema validators for each `agency_airline_override.override_type`.
- Exact tenant isolation test strategy and fixture matrix.

## Data Model Risks To Monitor

- Passenger duplication can still become operationally messy despite merge rules.
- Relationship permissions can become hard to reason about if authorized contacts expand beyond MVP.
- Snapshot payloads may grow large and should be version-linked where possible.
- Agency overrides may conflict with global updates and need clear review queues.
- Financial tracking may drift toward accounting unless payment provider and ledger features remain out of MVP.

## Validation Needed With Early Agencies

- Most common request types.
- Most common special services.
- Required launch document types.
- Typical invoice/payment practices.
- Preferred offer comparison format.
- Minimum acceptable airline intelligence coverage.
- Whether agency websites need custom domains for launch.
- Whether WhatsApp/email summaries should be first-class records in MVP.
