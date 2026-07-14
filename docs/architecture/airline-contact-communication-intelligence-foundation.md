# Airline Contact and Communication Intelligence Foundation

## Purpose

Phase 55.8 creates a governed operational intelligence layer for finding the correct airline or supplier desk, choosing a documented channel, understanding operating hours and required information, preparing separated communication text, following a manual escalation path, and recording evidence of an interaction.

This phase is metadata and advisory infrastructure. AeroAssist does not send the supplier-facing or client-facing text, call a provider, store provider credentials, or perform an automatic escalation.

## Canonical Contact Model

The existing `airline_contacts` collection remains the canonical airline contact registry. `AirlineContactDirectoryEntry` aligns richer desk, scope, verification, evidence, publication, and agency-visibility metadata with that registry; it does not create a second airline-contact master.

Supporting collections add focused governance records:

- `airline_contact_channels`
- `airline_contact_scopes`
- `airline_contact_availabilities`
- `airline_contact_escalation_paths`
- `airline_communication_templates`
- `airline_communication_requirements`
- `airline_contact_verifications`
- `airline_supplier_interactions`

Directory entries and their supporting records can be global platform knowledge or agency-specific metadata. Agency projections include only published records for all agencies or the selected agency. Restricted internal and platform-only channels are excluded.

## Desk and Scope Intelligence

The directory supports general agency, trade, ticketing, refunds, schedule change, medical, special assistance, UMNR, pet, group, baggage, airport station, disruption, NDC, GDS, EMD/ancillary, accounting/ADM, and complaints/claims desks.

Desk matching is deterministic. It considers airline, desk type, market, country, airport, route, service code, distribution channel, effective dates, contact state, publication, and agency visibility. Specific matching scope outranks generic scope. Missing, stale, closed, or unverified knowledge produces a warning and manual-review state rather than unsupported certainty.

## Availability and Escalation

Availability records hold an IANA timezone, working periods, holidays, exceptions, after-hours instructions, and expected response metadata. Evaluation converts the supplied timestamp into the governed local timezone before deciding whether a desk is currently open. Invalid or incomplete time data remains unknown.

Escalation paths contain ordered metadata and a suggested trigger interval. They never run automatically. An agent decides whether and how to use the suggested path.

## Communication Separation

Every governed template preserves three distinct fields:

- internal operational instructions
- supplier-facing message text
- client-facing status text

Communication requirements add identifiers, information, document, attachment, authentication-summary, and format checklists. Template composition is a transient formatting operation. It reports missing checklist values and never sends a message.

## Verification, Evidence, and Versions

Contact, channel, scope, availability, escalation, template, and requirement records can reference governed evidence. Manual verification records preserve method, reviewer, source, decision, verified time, and next-review time. A verified record becomes current; review-due and stale states remain explicit.

The supporting knowledge types are registered with the existing evidence-governance and structured knowledge-version services. Superseded or conflicting source truth is preserved by those foundations rather than overwritten or deleted.

## Operational Integration

`AirlineSupplierInteractionRecord` stores metadata about an interaction completed outside AeroAssist. It can link to passenger-service and operational workflows, after-sales cases, tasks, work items, SLA deadlines, passengers, requests, trips, bookings, tickets, EMDs, SSR/OSI workspaces, and documents. Missing optional links create review warnings rather than crashes.

Logging an interaction creates an internal operational timeline entry through the existing timeline service. It does not mutate the linked workflow, case, task, queue item, deadline, ticket, or EMD. The record always states that external sending and provider messaging are disabled.

## Routes and UI

- Platform API: `/api/platform/airline-contact-intelligence`
- Agency API: `/api/agencies/{agency_id}/airline-contact-directory`
- Platform UI: `/platform/airline-contact-intelligence`
- Agency UI: `/agency/airline-contact-directory`

Platform owners, administrators, and knowledge editors govern directory metadata. Agency staff consume published intelligence, perform transient desk and template lookups, and may record agency-owned interaction history. No `/admin/*` or `/agent/*` route root is introduced.

## Security Boundary

Payloads containing password, secret, token, API-key, private-key, or authorization-header fields are rejected. Contact channels can record a public or agency-operational address, phone, URL, queue, or reference and a plain-language authentication requirement, but never a private credential value.

Phase 55.8 adds no email, SMS, chat, GDS, NDC, supplier, airline, or external API connectivity; no background worker; no AI; no automatic escalation; no booking, ticketing, EMD, refund, exchange, payment, or operational execution.
