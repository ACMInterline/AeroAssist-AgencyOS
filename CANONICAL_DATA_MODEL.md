# Canonical Data Model

## Modeling Rules

Every model must declare:

- Ownership: global, agency-owned, portal-owned, or mixed.
- Tenant boundary: isolated by `agency_id`, globally shared, or join-controlled.
- View permission.
- Edit permission.
- Snapshot behavior.
- Agency override allowance.
- Source of truth.

Operational records must never silently change because global knowledge changes. Offers, bookings, tickets, EMDs, invoices, refunds, exchanges, and issued documents must preserve snapshots.

## Core Identity And Tenancy Entities

| Entity | Ownership | Source Of Truth | Notes |
| --- | --- | --- | --- |
| `platform_owner` | Global | AeroAssist | SaaS owner concept, not an agency tenant. |
| `platform_user` | Global | AeroAssist | Platform admins, support, knowledge editors. |
| `agency` | Global registry, agency-operated | AeroAssist for subscription; agency for profile | Legal/commercial agency record. |
| `agency_workspace` | Agency-owned | Agency | Operational tenant container. Usually one active workspace per agency in MVP. |
| `agency_staff_user` | Agency-owned | Agency | Staff identity, role, status, and workspace access. |
| `client_user` | Agency-owned identity with portal access | Agency/client | Person or organization contact that requests, decides, pays, or communicates. |
| `passenger_profile` | Agency-owned, relationship-controlled | Agency/passenger/client with permissions | Traveler record that may relate to multiple clients. |
| `client_passenger_relationship` | Agency-owned | Agency | Mandatory many-to-many permission and consent model. |

## Client vs Passenger

Client means the party that requests, decides, pays, communicates, or manages travel. A client may be a person or organization and may not travel.

Passenger means the traveler. A passenger has travel-specific data such as date of birth, PTC, nationality, passport/travel documents, assistance needs, service requirements, and travel history.

Passengers are not owned by a single client. Access is controlled by `client_passenger_relationship`.

### `client_passenger_relationship`

Required fields:

- `agency_id`
- `client_id`
- `passenger_id`
- `relationship_type`: `self`, `spouse`, `child`, `parent`, `guardian`, `employee`, `assistant`, `company_traveler`, `other`
- `can_view`
- `can_edit`
- `can_upload_documents`
- `can_request_travel`
- `can_pay`
- `can_receive_notifications`
- `consent_status`
- `valid_from`
- `valid_to`
- `notes`

This model supports company-paid travel, family travel, assistants managing VIPs, children managed by parents, and later passenger portal access.

## Global Reference Entities

| Entity | Ownership | Tenant Isolation | Agency Override | Snapshot |
| --- | --- | --- | --- | --- |
| `airline` | Global | Shared read | Limited fields only | Referenced and snapshotted in operations |
| `airport` | Global | Shared read | No | Referenced |
| `city` | Global | Shared read | No | Referenced |
| `country` | Global | Shared read | No | Referenced |
| `aircraft_type` | Global | Shared read | No | Referenced |
| `service_taxonomy_item` | Global | Shared read | Agency labels optional later | Snapshotted when used |
| `rfic_rfisc_code` | Global | Shared read | Airline/agency mapping override allowed | Snapshotted when used |
| `global_document_template` | Global | Shared read | Agency copy/customization | Copied or version-referenced |
| `global_website_template` | Global | Shared read | Agency configuration | Version-referenced |

## Airline Intelligence Entities

| Entity | Ownership | Notes |
| --- | --- | --- |
| `airline_profile` | Global | Identity, channels, operational notes. |
| `airline_contact` | Global or agency override | Desk, support, sales, escalation, hours, URLs. |
| `airline_ssr_osi_format` | Global with agency notes | SSR/OSI format by airline, service, GDS, scope. |
| `airline_service_policy` | Global with override | Special service policy details. |
| `airline_product` | Global | Cabin products, fare families, branded fares. |
| `airline_ancillary_rule` | Global with override | Service fees, pricing basis, route applicability. |
| `airline_emd_mapping` | Global with override | Service code, RFIC, RFISC, issuance type, review flags. |
| `airline_procedure` | Global with override | Manual/GDS/portal/phone/email process. |
| `airline_agreement` | Agency-owned or global confidential | PCC/OID/account, commission, waiver, private fare notes. |
| `airline_knowledge_item` | Global or agency-owned override | Flexible extensible policy/product/operation layer. |
| `knowledge_source` | Global or agency-owned | Evidence, URL, document, captured/reviewed metadata. |
| `knowledge_version` | Global or agency-owned | Version history and publishing status. |

## Agency Workspace Entities

| Entity | Ownership | Notes |
| --- | --- | --- |
| `agency_branding` | Agency | Logo, colors, fonts, contact details. |
| `agency_website_config` | Agency | Template selection, public page settings, request form settings. |
| `agency_website_page` | Agency | Home, services, about, FAQ, legal, optional guides/blog. |
| `agency_setting` | Agency | Operational defaults. |
| `agency_markup_rule` | Agency | Service fee and markup configuration. |
| `agency_document_template` | Agency | Customized from global or created by agency. |
| `agency_airline_override` | Agency | Private contacts, agreements, notes, pricing rules, procedures. |
| `staff_role_assignment` | Agency | Staff permissions. |

## CRM And Portal Entities

| Entity | Ownership | Notes |
| --- | --- | --- |
| `client_profile` | Agency | Person/company profile, communication details, preferences. |
| `client_account` | Agency | Portal status: `no_portal_access`, `invited`, `active`, `suspended`, `archived`. |
| `client_invitation` | Agency | Invite token metadata, expiry, resend history. |
| `passenger_profile` | Agency | Traveler core profile. |
| `passenger_document` | Agency | Passport, visa, ID, medical, consent, uploaded files. |
| `portal_session` | Agency | Authentication/session audit. |
| `authorized_contact` | Agency | Optional contact authorized to act for client/passenger. |

## Request Entities

| Entity | Ownership | Notes |
| --- | --- | --- |
| `travel_request` | Agency | May originate from website, portal, staff, phone, email, WhatsApp. |
| `request_passenger` | Agency | Links passengers to request. |
| `request_segment_intent` | Agency | Intended route, dates, flexibility. |
| `request_service_need` | Agency | Requested services, pets, assistance, documents. |
| `request_document` | Agency | Files linked to request. |
| `request_timeline_event` | Agency | Communication and status history. |
| `request_internal_note` | Agency | Staff-only notes. |

Requests may consume airline intelligence but must remain valid without evaluation.

## Offer Entities

| Entity | Ownership | Notes |
| --- | --- | --- |
| `offer` | Agency | May be request-linked or manual. |
| `offer_passenger` | Agency | Passenger links. |
| `offer_route_alternative` | Agency | Up to 3 alternatives per offer. |
| `offer_segment` | Agency | Itinerary segments for each alternative. |
| `offer_fare_bundle` | Agency | Up to 3 bundle/pricing options per route alternative. |
| `offer_price_line` | Agency | Fare, tax, ancillary, service fee, UMNR/PETC/WCHR, etc. |
| `offer_recommendation` | Agency | Agent label and reasoning. |
| `offer_snapshot` | Agency | Knowledge/pricing/document snapshot at send/acceptance. |
| `offer_client_action` | Agency/client | Accept, reject, comment, request changes. |

## Booking, Ticket, EMD, Invoice, Payment Entities

| Entity | Ownership | Notes |
| --- | --- | --- |
| `booking` | Agency | From accepted offer or manual. |
| `booking_segment` | Agency | PNR segment, route, status. |
| `booking_service_confirmation` | Agency | SSR/service confirmation tracking. |
| `ticket` | Agency | Passenger ticket number, validating airline, fare/tax, status. |
| `emd` | Agency | Passenger EMD number, service code, RFIC/RFISC, amount, status. |
| `invoice` | Agency | Client billing record. |
| `invoice_line_item` | Agency | Fees, taxes, pass-through charges, service lines. |
| `payment` | Agency | Method, amount, status, reconciliation. |
| `refund_exchange_case` | Agency | Original/new docs, penalties, differences, notes. |
| `refund_exchange_line` | Agency | Fare difference, tax difference, penalty, refund, agency fee. |

## Document, Message, Task, Timeline Entities

| Entity | Ownership | Notes |
| --- | --- | --- |
| `document_template` | Global or agency | Template source and version. |
| `generated_document` | Agency | PDF/HTML output, archive, visibility. |
| `document_file` | Agency | Stored file metadata. |
| `message_thread` | Agency | Client/staff communication grouping. |
| `message` | Agency/client | Portal, email, phone summary, WhatsApp summary. |
| `task` | Agency | Staff or client task. |
| `timeline_event` | Agency | Cross-entity audit/event model. |
| `internal_note` | Agency | Staff-only note attached to operational records. |

## Snapshot Rules

Snapshot when:

- Offer is sent.
- Offer is accepted.
- Booking is created.
- Ticket is issued.
- EMD is issued.
- Invoice is issued.
- Refund/exchange is processed.
- Client-facing document is generated.

Snapshots should include:

- Airline policy summary used.
- Pricing/EMD mapping used.
- Fare bundle details used.
- Document requirements used.
- Client-visible wording.
- Staff/internal warnings where relevant.
- Source/version identifiers for global knowledge.

## Agency Override Rules

Overrides are allowed for:

- Agency-private airline contacts.
- Agency-specific commercial agreements.
- Agency-specific document templates.
- Agency-specific pricing/markup rules.
- Agency-specific website content.
- Agency-specific internal notes and operating procedures.

Overrides must not mutate global records. They should layer over global data through explicit override entities and be visible only to the owning agency unless promoted by platform review.

## Review Hardening: Required Relationship Contract

The database implementation must make these relationships explicit before migrations are written:

- `agency_workspace.agency_id` references `agency.id`.
- Every agency-owned operational record carries `agency_id` and, where workspace support exists, `agency_workspace_id`.
- `agency_staff_user.agency_id` references `agency.id`; role assignments reference staff user, agency, and role.
- `client_profile.agency_id`, `client_account.agency_id`, `passenger_profile.agency_id`, and `client_passenger_relationship.agency_id` must match.
- `client_account.client_profile_id` references `client_profile.id`; a client profile may exist without a portal account.
- `client_passenger_relationship.client_id` references `client_profile.id` and `passenger_id` references `passenger_profile.id`; both records must belong to the same agency.
- `authorized_contact` must reference either a client, passenger, or relationship and must declare the permission basis.
- `travel_request.client_id` references `client_profile.id`; `request_passenger.request_id` references `travel_request.id`; `request_passenger.passenger_id` references `passenger_profile.id`.
- `offer.client_id` references `client_profile.id`; `offer.request_id` is nullable; `offer_passenger`, `offer_route_alternative`, `offer_segment`, `offer_fare_bundle`, `offer_price_line`, and `offer_client_action` all reference the owning offer chain.
- `offer_route_alternative` must be limited to three rows per offer.
- `offer_fare_bundle` must be limited to three rows per route alternative.
- `booking.client_id` references `client_profile.id`; `booking.offer_id` is nullable; `booking.accepted_offer_action_id` is nullable but required when created from an accepted offer.
- Tickets, EMDs, invoices, payments, refunds, exchanges, generated documents, messages, tasks, notes, and timeline events must reference their parent operational record and `agency_id`.
- `ticket.passenger_id` and `emd.passenger_id` reference `passenger_profile.id`; both should also reference `booking_id` when created from a booking.
- `emd.ticket_id` is nullable because some EMDs may be standalone, but `emd.booking_id` or another service context must be present.
- `invoice.client_id` references `client_profile.id`; `invoice.booking_id` and `invoice.offer_id` are nullable to allow manual invoices, but invoice line items must preserve their source record when derived.
- `payment.invoice_id` references `invoice.id` unless the system later supports unapplied payments, which must be modeled explicitly.
- `refund_exchange_case` references at least one original ticket, EMD, booking, invoice, or client request; new ticket/EMD references are nullable.
- `generated_document` references a source template version and the operational record that produced it.
- `message_thread` may reference client, request, offer, booking, invoice, refund/exchange, or a general client conversation, but it must always carry `agency_id`.
- `timeline_event` must carry `agency_id`, actor, record type, and record ID; cross-record events should use an explicit link table or structured related-record fields.

## Review Hardening: Source Of Truth Boundaries

- Global airline, airport, country, aircraft, service taxonomy, RFIC/RFISC, website template, and base document template records are owned by AeroAssist.
- Agency website content, branding, staff, clients, passengers, relationships, requests, offers, bookings, tickets, EMDs, invoices, payments, documents, messages, tasks, notes, and timelines are agency-owned.
- Client-entered portal data is proposed or edited within the agency-owned record; the agency remains the operational data owner.
- Agency overrides are agency-owned records that reference global records. They never become the global source of truth unless copied into a platform review workflow and published as a new global version.
- Agency commercial data such as PCC/OID/account references, private fares, commission, waiver notes, markups, and internal procedures must never be stored in global knowledge records.

## Review Hardening: Snapshot Payload Rules

Each snapshot should record both a compact human-readable summary and machine-resolvable provenance:

- `snapshot_reason`: sent, accepted, booking_created, ticket_issued, emd_issued, invoice_issued, refund_exchange_processed, document_generated.
- `source_record_type` and `source_record_id`.
- Global knowledge version IDs used.
- Agency override version IDs used.
- Airline, service, route, fare bundle, EMD mapping, document requirement, and pricing context used.
- Client-visible wording at the time of output.
- Internal warnings shown to staff at the time of decision.
- Actor and timestamp.

Snapshots are immutable. Corrections create a new snapshot linked to the same operational record with a new reason or revision marker.

## Architecture Decisions: Client, Person, Organization, And Passenger

Decision: `client_profile` is the agency's commercial/account relationship record. It may represent an individual person, a family/household, or an organization/company. A client is not assumed to be a traveler.

Initial client model:

- `client_profile.client_type`: `individual`, `family_household`, `organization`
- Individual client fields: legal/preferred name, contact details, billing details, communication preferences.
- Family/household client fields: household display name, primary contact, billing details, communication preferences.
- Organization client fields: legal name, trade name, registration/tax fields where needed, billing details, primary contact, communication preferences.
- `client_contact`: agency-owned contact person linked to a client profile. In MVP this supports multiple contacts for organization/family clients without creating multiple client profiles.
- `client_account`: portal login tied to one `client_profile` and one primary contact identity. Multiple portal users per organization are not MVP; additional organization contacts are staff-managed contacts until later expansion.

Passenger model:

- `passenger_profile` is always the traveler record and is separate from `client_profile`.
- An individual client who travels must have both a `client_profile` and a linked `passenger_profile`.
- The self-travel case uses `client_passenger_relationship.relationship_type = self`.
- Family, guardian, assistant, company, and VIP cases use relationship rows rather than ownership.
- Passengers remain agency-scoped in MVP and are not shared globally across agencies.

Relationship examples:

- Individual traveler: one individual `client_profile`, one `passenger_profile`, one `self` relationship.
- Parent and child: parent `client_profile`, child `passenger_profile`, `parent` or `guardian` relationship with edit/upload/request permissions.
- Family: family/household `client_profile`, multiple passenger profiles, relationship rows for each passenger.
- Company: organization `client_profile`, employee passenger profiles, `company_traveler` or `employee` relationships.
- Assistant: assistant may be an individual client/contact or authorized contact linked to a VIP passenger with delegated permissions.

## Architecture Decisions: Tenant Isolation Strategy

Decision: every agency-owned table must include `agency_id`. `agency_workspace_id` may also be present for future multi-workspace support, but `agency_id` is the required isolation key for MVP.

Rules:

- Agency-owned operational records must never be queried without an agency scope.
- Child records inherit tenant scope from their parent and also store `agency_id` for enforcement, indexing, and audit.
- Cross-agency links are not allowed for operational records in MVP.
- Passenger profiles are unique only within an agency, not across the platform.
- Platform-owned global records do not carry `agency_id`; access is controlled by published status, subscription/feature flags, and platform role.
- Agency overrides carry `agency_id` and reference a global record or global knowledge item by ID and version.
- Agency overrides must not copy sensitive agency commercial data into platform-owned global records.
- Platform support access to agency data requires audited, reason-coded access and does not change ownership.

Implementation expectation:

- Use database constraints where possible to ensure child rows match the parent `agency_id`.
- Use application authorization and tests to enforce tenant-scoped reads and writes.
- Use immutable audit events for cross-tenant support access.

## Architecture Decisions: Initial Status Enums

These enums are the initial database contract. They may be expanded through migrations later, but application code should not invent additional statuses without updating this spec.

| Domain | Initial Values |
| --- | --- |
| `agency.status` | `prospect`, `onboarding`, `active`, `suspended`, `cancelled`, `archived` |
| `agency_workspace.status` | `setup`, `active`, `suspended`, `archived` |
| `platform_user.status` | `invited`, `active`, `suspended`, `archived` |
| `agency_staff_user.status` | `invited`, `active`, `suspended`, `archived` |
| `client_account.portal_status` | `no_portal_access`, `invited`, `email_unverified`, `active`, `suspended`, `archived` |
| `client_profile.status` | `lead`, `active`, `inactive`, `blocked`, `archived` |
| `passenger_profile.status` | `active`, `inactive`, `deceased`, `merged`, `archived` |
| `client_passenger_relationship.status` | `proposed`, `active`, `restricted`, `expired`, `revoked`, `archived` |
| `client_passenger_relationship.consent_status` | `not_required`, `pending`, `granted`, `declined`, `withdrawn`, `expired` |
| `travel_request.status` | `draft`, `new`, `triage`, `awaiting_client`, `researching`, `offered`, `accepted`, `closed_no_offer`, `cancelled`, `archived` |
| `offer.status` | `draft`, `ready_to_send`, `sent`, `viewed`, `accepted`, `rejected`, `changes_requested`, `expired`, `superseded`, `withdrawn`, `archived` |
| `offer_route_alternative.status` | `draft`, `available`, `recommended`, `unavailable`, `withdrawn`, `selected`, `not_selected` |
| `offer_fare_bundle.status` | `draft`, `available`, `recommended`, `unavailable`, `price_changed`, `selected`, `not_selected`, `withdrawn` |
| `booking.status` | `draft`, `on_hold`, `confirmed`, `ticketing_pending`, `ticketed`, `partially_ticketed`, `cancelled`, `completed`, `archived` |
| `booking_segment.status` | `planned`, `held`, `confirmed`, `waitlisted`, `cancelled`, `flown`, `changed` |
| `booking_service_confirmation.status` | `not_requested`, `requested`, `pending`, `confirmed`, `rejected`, `cancelled`, `not_required` |
| `ticket.status` | `draft`, `issued`, `voided`, `exchanged`, `refunded`, `partially_refunded`, `cancelled`, `archived` |
| `emd.status` | `draft`, `issued`, `voided`, `exchanged`, `refunded`, `partially_refunded`, `cancelled`, `archived` |
| `invoice.status` | `draft`, `issued`, `sent`, `partially_paid`, `paid`, `overdue`, `voided`, `refunded`, `partially_refunded`, `archived` |
| `payment.status` | `scheduled`, `pending`, `received`, `failed`, `cancelled`, `refunded`, `partially_refunded`, `reconciled` |
| `refund_exchange_case.status` | `draft`, `reviewing`, `awaiting_airline`, `awaiting_client`, `quoted`, `approved`, `processed`, `rejected`, `cancelled`, `closed`, `archived` |
| `generated_document.status` | `draft`, `generated`, `sent`, `viewed`, `downloaded`, `archived`, `voided` |
| `document_file.status` | `uploaded`, `pending_review`, `accepted`, `rejected`, `expired`, `archived`, `deleted` |
| `message_thread.status` | `open`, `waiting_on_client`, `waiting_on_agency`, `closed`, `archived` |
| `message.status` | `draft`, `sent`, `delivered`, `read`, `failed`, `archived` |
| `task.status` | `open`, `in_progress`, `waiting`, `completed`, `cancelled`, `archived` |
| `airline_knowledge.review_status` | `draft`, `needs_review`, `approved`, `published`, `deprecated`, `superseded`, `rejected` |
| `knowledge_source.confidence` | `low`, `medium`, `high`, `official` |
| `knowledge_source.review_status` | `unreviewed`, `reviewing`, `accepted`, `rejected`, `stale` |

## Architecture Decisions: Snapshot Payloads By Milestone

All operational snapshots include: `agency_id`, source record type/ID, snapshot reason, actor, timestamp, client-visible wording, internal warnings, global knowledge version IDs, agency override version IDs, and generated document/template version IDs where applicable.

Offer sent snapshot must include:

- Client, passenger, and relationship IDs used for the offer.
- Route alternatives and fare bundles as sent.
- Segment details, carrier combinations, schedule, baggage/flexibility notes, and recommendation labels.
- Fare, tax, airline/supplier pass-through, agency service fee, ancillary/service fee, currency, and total price lines.
- Airline policy hints, EMD readiness, document requirements, warnings, and source versions used.
- Quote expiry, manual-review flags, and client-visible terms.

Offer accepted snapshot must include:

- Accepted route alternative and fare bundle IDs.
- Accepted total and price-line breakdown.
- Client action metadata: actor, timestamp, channel, acceptance text/version, comments.
- Any changed availability, price, or document warnings shown at acceptance.

Booking created snapshot must include:

- Booking source: accepted offer, manual booking, existing PNR, or other.
- Client, passengers, segments, PNR, booking channel, supplier/airline references, and service confirmations known at creation.
- Selected offer snapshot reference if applicable.
- Policy/procedure/contact knowledge used for booking actions.

Ticket issued snapshot must include:

- Passenger, ticket number, validating airline, issue date, status, fare/tax breakdown, currency, linked booking/segment references, and receipt document.
- Fare basis or booking-class notes if captured.
- Exchange or original-ticket reference if applicable.

EMD issued snapshot must include:

- Passenger, EMD number, service code, RFIC, RFISC, reason for issuance, amount, currency, issuance type, linked ticket/booking/service, and receipt document.
- EMD mapping source versions and manual-review flags.

Invoice issued snapshot must include:

- Client, billing details, invoice number, issue/due dates, currency, line items, tax treatment, totals, linked offer/booking/ticket/EMD/refund records, and branded invoice document version.
- Internal reconciliation notes are excluded from client-visible invoice output but retained in audit.

Refund/exchange processed snapshot must include:

- Original ticket/EMD references, new ticket/EMD references if any, fare difference, tax difference, airline penalty, agency fee, refund amount, currency, approval channel, client-visible confirmation wording, and policy/source versions used.
- Payment/invoice adjustment references and final case outcome.

## Architecture Decisions: Passenger Merge Rules

Decision: passenger merge is agency-scoped and available only to `agency_owner` and `agency_admin` in MVP.

Merge is allowed when:

- Both passenger records belong to the same `agency_id`.
- Staff confirms they refer to the same real traveler.
- No active booking, ticket, EMD, invoice, refund/exchange, or generated document would lose historical meaning.
- Conflicting legal identity or date-of-birth fields are resolved explicitly.

Merge behavior:

- One passenger becomes the surviving record.
- The duplicate passenger status changes to `merged`.
- The duplicate stores `merged_into_passenger_id`.
- Relationships, documents, requests, offers, bookings, tickets, EMDs, messages, tasks, and timeline links are re-pointed to the surviving passenger where safe.
- Historical snapshots and generated documents keep the passenger data that existed at the time they were created.
- If a record cannot be safely re-pointed, it retains the original reference and displays the merge relationship for staff context.

Audit requirements:

- Record actor, timestamp, agency ID, source passenger ID, surviving passenger ID, before/after key identity fields, reason, and conflict resolution notes.
- Merge cannot be hard-deleted.
- Unmerge is not MVP; correction requires support/admin review and a new audit event.

## Architecture Decisions: Financial Allocation Rules

Decision: MVP tracks travel operations money and payment status; it is not a full accounting ledger.

Money is modeled through invoice line items, payments, refund/exchange lines, and reconciliation notes:

- Airline/supplier pass-through amounts are invoice line items with category `supplier_pass_through`.
- Ticket fares are invoice line items with category `ticket_fare`.
- Ticket taxes are invoice line items with category `ticket_tax`.
- EMD amounts are invoice line items with category `emd`.
- Agency service fees are invoice line items with category `agency_service_fee`.
- Ancillary/service fees may be `supplier_pass_through`, `emd`, or `agency_service_fee` depending on who collects and issues them.
- Adjustments use category `adjustment`.
- Refunds use category `refund`.
- Exchange fare/tax differences and penalties use explicit refund/exchange lines and may create invoice adjustment lines.

MVP payment rules:

- Payments apply to one invoice.
- Partial payments are allowed.
- Multiple payments may apply to one invoice.
- A payment cannot be split across multiple invoices in MVP.
- Unapplied payments are not MVP.
- Multi-currency invoices are not MVP; each invoice has one currency. Source amounts in other currencies may be stored as notes or later structured fields.
- Payment records track method, amount, currency, status, due date, received date, external reference optional, and reconciliation notes.
- Reconciliation notes are internal-only.
- Invoice balance is derived from issued invoice total minus received/reconciled payments plus/minus refund or adjustment lines.

Refund/exchange financial rules:

- Refund/exchange cases record operational facts first, then create invoice/payment adjustments when the agency needs client-facing financial output.
- Airline penalties, agency fees, fare differences, tax differences, refund amounts, and new ticket/EMD amounts must be separate lines for audit.
- Payment provider automation, general ledger postings, chart of accounts, tax filing, and accounting exports are outside MVP.

## Architecture Decisions: Document Retention And Visibility

Every document record must include:

- `agency_id`
- `owner_type`: `platform_template`, `agency_template`, `agency_generated`, `client_upload`, `passenger_upload`, `staff_upload`
- `linked_entity_type` and `linked_entity_id`
- `passenger_id` optional for passenger-specific documents
- `client_id` optional for client-specific documents
- `client_visible`
- `passenger_visible`
- `internal_only`
- `retention_class`
- `status`
- created/uploaded actor and timestamp

Retention classes:

- `operational`: offers, itineraries, confirmations, handling notes.
- `financial`: invoices, receipts, refund/exchange confirmations.
- `identity_document`: passports, IDs, visas.
- `medical_sensitive`: MEDIF, oxygen/POC, disability assistance, medical approvals.
- `consent_legal`: consents, powers of attorney, guardian permissions.
- `template`: global or agency template assets.
- `communication_attachment`: files attached to messages.

Visibility rules:

- `internal_only = true` always overrides client/passenger visibility.
- Client-visible documents require `client_visible = true`, active portal access, tenant match, and relevant relationship permissions.
- Passenger-specific documents require a relationship with `can_view` for viewing and `can_upload_documents` for upload/update.
- Sensitive documents default to internal-only or staff-review-required until explicitly accepted and published to portal.
- Generated client-facing documents preserve the template version and data snapshot used.

Deletion/archive rules:

- Operational, financial, ticket, EMD, invoice, refund/exchange, and generated offer documents are archived, not hard-deleted, during normal use.
- Uploaded documents may be marked deleted when legally/operationally allowed, but metadata and audit events remain.
- Expired identity/medical documents should be retained or archived according to agency policy and applicable law; the app should support status `expired` without deleting the file.
- Hard deletion is restricted to platform/agency owner policy workflows and must not break historical snapshots.
