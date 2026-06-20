# Build Phases

## Phase 0: Architecture Contract And Foundations

Goal: Establish canonical specifications before code.

Models needed: none implemented yet.

Pages needed: none implemented yet.

Workflows enabled: planning only.

Out of scope: application code, migrations, UI pages, integrations.

## Phase 1: Multi-Tenant Workspace Foundation

Goal: Create secure agency workspace and identity foundation.

Tables/models needed:

- `platform_user`
- `agency`
- `agency_workspace`
- `agency_staff_user`
- `staff_role_assignment`
- `agency_setting`
- audit events

Pages needed:

- Platform agency registry.
- Agency workspace setup.
- Staff management.
- Role assignment.

Workflows enabled:

- Agency setup.
- Staff invitation.
- Basic tenant isolation.

Out of scope:

- Airline intelligence depth.
- Offers/bookings.
- Public website publishing.

## Phase 2: Agency Branding, Website Settings, And Templates

Goal: Let each agency configure brand, public website basics, and template choices.

Tables/models needed:

- `agency_branding`
- `agency_website_config`
- `agency_website_page`
- `global_website_template`
- `global_document_template`
- `agency_document_template`

Pages needed:

- Branding settings.
- Website settings.
- Public website preview/publish controls.
- Template library.

Workflows enabled:

- Controlled website/CMS setup.
- Portal entry links.
- Basic branded document settings.

Out of scope:

- Complex drag/drop website builder.
- Blog automation.
- Custom web design tooling.

## Phase 3: CRM, Passenger Profiles, And Portal Accounts

Goal: Implement central client/passenger model.

Tables/models needed:

- `client_profile`
- `client_account`
- `client_invitation`
- `passenger_profile`
- `passenger_document`
- `client_passenger_relationship`
- `authorized_contact`

Pages needed:

- Client list/detail.
- Passenger list/detail.
- Relationship editor.
- Client portal account status/invite controls.
- Portal profile pages.

Workflows enabled:

- Staff-created clients.
- Client self-registration.
- Portal invitations.
- Client/passenger relationship permissions.
- Document upload basics.

Out of scope:

- Native mobile app.
- Advanced consent automation.

## Phase 4: Requests, Messages, Tasks, And Timelines

Goal: Capture agency work from website, portal, phone, email, or WhatsApp.

Tables/models needed:

- `travel_request`
- `request_passenger`
- `request_segment_intent`
- `request_service_need`
- `request_document`
- `message_thread`
- `message`
- `task`
- `timeline_event`
- `internal_note`

Pages needed:

- Request intake form.
- Agency request queue.
- Request detail.
- Portal requests.
- Messages.
- Tasks.

Workflows enabled:

- Website/portal/manual request creation.
- Request timeline.
- Client/staff communication.
- Task assignment.

Out of scope:

- Automated fare search.
- Mandatory airline evaluation.

## Phase 5: Airline Intelligence Basic Version

Goal: Deliver searchable reviewed airline knowledge for staff use.

Tables/models needed:

- `airline`
- `airport`
- `country`
- `aircraft_type`
- `service_taxonomy_item`
- `rfic_rfisc_code`
- `airline_profile`
- `airline_contact`
- `airline_ssr_osi_format`
- `airline_service_policy`
- `airline_product`
- `airline_ancillary_rule`
- `airline_emd_mapping`
- `airline_procedure`
- `airline_knowledge_item`
- `knowledge_source`
- `knowledge_version`
- `agency_airline_override`

Pages needed:

- Platform knowledge editor.
- Airline profile view.
- Knowledge search.
- Source/review workflow.
- Agency override editor.

Workflows enabled:

- Global knowledge creation and publishing.
- Agency read access.
- Agency-specific overrides.
- Policy hints for requests and offers.

Out of scope:

- Automatic scraping without review.
- Complete global airline coverage on day one.

## Phase 6: Offer Builder

Goal: Let agents create branded professional offers from manually researched options.

Tables/models needed:

- `offer`
- `offer_passenger`
- `offer_route_alternative`
- `offer_segment`
- `offer_fare_bundle`
- `offer_price_line`
- `offer_recommendation`
- `offer_snapshot`
- `offer_client_action`

Pages needed:

- Offer list/detail.
- Offer builder.
- Route alternative comparison.
- Fare bundle editor.
- Branded client offer view.
- Portal offer response.

Workflows enabled:

- Manual offers.
- Request-linked offers.
- Up to 3 route alternatives.
- Up to 3 fare bundles per route.
- Offer send, acceptance, rejection, and snapshot.

Out of scope:

- GDS/NDC fare search.
- Automatic ticketing.

## Phase 7: Bookings, Tickets, EMDs, Invoices, And Payments

Goal: Track the operational and financial lifecycle after offer acceptance or manual booking.

Tables/models needed:

- `booking`
- `booking_segment`
- `booking_service_confirmation`
- `ticket`
- `emd`
- `invoice`
- `invoice_line_item`
- `payment`
- `generated_document`
- `document_file`

Pages needed:

- Booking tracker.
- Ticket detail.
- EMD detail.
- Invoice builder.
- Payment tracker.
- Portal booking/invoice/document views.

Workflows enabled:

- Booking from offer or manual.
- Ticket and EMD tracking.
- Invoice generation.
- Payment status tracking.
- Branded document output.

Out of scope:

- Full accounting.
- Payment provider automation unless separately prioritized.

## Phase 8: Refunds, Exchanges, And Advanced Documents

Goal: Support post-issuance servicing and richer branded document workflows.

Tables/models needed:

- `refund_exchange_case`
- `refund_exchange_line`
- additional document template block/version fields if needed

Pages needed:

- Refund/exchange case detail.
- Document generation center.
- Template customization.

Workflows enabled:

- Refund case tracking.
- Exchange/reissue tracking.
- Branded refund/exchange confirmations.
- Document checklist and consent form generation.

Out of scope:

- Fully automated airline refund/exchange execution.

## Review Hardening: MVP Scope Risks

The MVP is coherent, but it is broad for a first release. Highest-risk scope areas:

- Public website/CMS, client portal, CRM, requests, airline intelligence, offers, bookings, financial tracking, and documents are all meaningful products on their own.
- Airline intelligence requires operational content ownership in addition to software features.
- Offer builder can expand into fare search if boundaries are not enforced.
- Document generation can expand into a full template-builder product.
- Payments can expand into accounting or payment processing if MVP does more than tracking.
- Refunds and exchanges are operationally complex and should not block first usable agency workflow unless early agencies require them.

Recommended first build phase after Phase 0:

1. Phase 1 tenant and identity foundation.
2. Phase 3 CRM, passenger profiles, and relationship permissions.
3. A thin slice of Phase 4 request capture and timeline.
4. A thin slice of Phase 6 manual offer builder with snapshots.
5. Basic document output from fixed templates.

This vertical slice validates the central product promise before building the full website/CMS, deep airline intelligence editor, refund/exchange casework, or advanced financial workflows.

## Review Hardening: Premature Or Overbuilt Items To Defer Unless Validated

- Native passenger portal accounts beyond client-managed passengers.
- Advanced blog/guides CMS.
- Complex document template block editing.
- Full agency override editor for every airline knowledge domain.
- Broad airline knowledge coverage before a small reviewed launch set.
- Analytics and performance reporting.
- Payment provider automation.
- Accounting exports.
- Automatic task generation from messages.
- Multi-workspace support under one agency account.

## Review Hardening: Phase Dependencies

- Phase 6 Offer Builder depends on Phase 3 client/passenger relationships and the snapshot contract.
- Phase 7 Booking/Ticket/EMD/Invoice/Payment depends on Phase 6 only when bookings are created from accepted offers; manual booking creation must remain possible.
- Phase 5 Airline Intelligence can start with read-only curated content. Agency override editing can be limited to contacts/notes in the first implementation.
- Phase 2 Website Settings can be delayed or reduced to branding and portal links if the first release focuses on agency operations.
- Phase 8 Refunds/Exchanges depends on ticket, EMD, invoice, payment, document, and message records being stable.

## Recommended MVP Cut

MVP should include Phases 1-7 with a deliberately narrow Phase 5 airline knowledge set and basic Phase 7 document generation. Phase 8 can follow quickly if servicing workflows are a key sales promise for launch agencies.
