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
