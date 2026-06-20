# AeroAssist AgencyOS Product Specification

## Product Definition

AeroAssist AgencyOS is a multi-tenant SaaS operating platform for micro and small travel agencies with 1-10 employees. It combines agency website/CMS, travel-specific CRM, client/passenger relationship management, requests, airline intelligence, branded offer creation, bookings, tickets, EMDs, invoices, payments, documents, timelines, and agency-branded client portal access.

The product helps small agencies work faster and look more professional without depending on expensive NDC aggregators, GDS APIs, content mixing engines, or OTA-style automation.

## Target Customer

- Independent travel agencies and boutique travel advisors.
- Small agencies with limited staff and high operational complexity.
- Agencies working through GDS, airline portals, supplier portals, OTA affiliate sources, email, phone, WhatsApp, and manual fare construction.
- Agencies serving business travel, family travel, VIP travel, special assistance cases, pets, groups, refunds, exchanges, and other high-touch workflows.

## Core Promise

AeroAssist does not replace the travel agent. It gives the travel agent a structured operating system for faster, cleaner, better-informed work.

The platform should help agencies:

- Keep a clean client and passenger CRM.
- Separate clients from passengers while supporting many-to-many relationships.
- Use reusable passenger, route, service, airline, and document data.
- Build professional branded offers from manually researched options.
- Track bookings, tickets, EMDs, invoices, payments, refunds, and exchanges.
- Generate branded documents.
- Give clients and passengers a useful portal.
- Consume AeroAssist-maintained airline knowledge without losing historical context.

## What The Product Is

- A multi-tenant SaaS workspace for travel agency operations.
- A controlled website/CMS and client portal platform for each agency.
- A travel-specific CRM with client/passenger relationship modeling.
- A manual-offer builder for expert agents.
- A booking, ticket, EMD, invoice, payment, document, and timeline tracker.
- A global airline intelligence system with review, source, version, publishing, and agency override support.
- A workflow assistant for human agents.

## What The Product Is Not

- Not a full OTA.
- Not a fare search engine.
- Not a GDS or NDC replacement.
- Not automatic ticketing.
- Not automatic airline scraping without human review.
- Not a complex drag/drop website builder in MVP.
- Not a full accounting system.
- Not centered only on itinerary automation.
- Not a set of isolated admin modules.

## Architectural Layers

### 1. AeroAssist Global / Platform Owner Layer

Owned by AeroAssist as SaaS provider.

Includes:

- Global airline intelligence.
- Global airline policy updates.
- Global reference data.
- Global service taxonomy.
- Global RFIC/RFISC/EMD knowledge.
- Global document template base library.
- Global website template library.
- Global feature configuration.
- Agency subscription and workspace management.

### 2. Agency Workspace Layer

Owned operationally by each subscribed travel agency.

Includes:

- Agency branding and website content.
- Agency staff users.
- Clients and passengers.
- Client/passenger relationships.
- Requests, offers, bookings, tickets, EMDs, invoices, payments.
- Documents, messages, tasks, timelines, internal notes.
- Agency-specific agreements, settings, commercial rules, and overrides.

### 3. Airline Intelligence Layer

Global by default, with agency-specific overrides where allowed.

Includes:

- Airline profiles and contacts.
- GDS, SSR, and OSI formats.
- Special service policies.
- Products, fare families, ancillary pricing rules.
- EMD/RFIC/RFISC mappings.
- Distribution and manual procedures.
- Agency agreements.
- Source evidence, review status, versions, warnings, and flexible knowledge layers.

### 4. Client / Passenger Portal Layer

Agency-branded access for clients and optionally passengers.

Includes:

- Client login, registration, invitations, and account status.
- Associated passenger profiles.
- Requests, offers, bookings, itineraries, tickets, EMDs, invoices, payments.
- Refund/exchange status.
- Documents and communication timelines.
- Permitted client/passenger data editing.

## MVP Scope

MVP includes:

1. Multi-tenant agency workspace.
2. Agency branding and basic website settings.
3. Staff login and agency roles.
4. Client and passenger CRM with many-to-many relationships.
5. Client portal access and invitation flow.
6. Requests.
7. Documents and messages.
8. Basic Airline Intelligence Knowledge Base.
9. Offer Builder with up to 3 route alternatives and up to 3 fare bundles per route.
10. Service and ancillary price lines.
11. Branded client offer view.
12. Booking tracker.
13. Ticket, EMD, invoice, and payment tracker.
14. Basic branded document output.

## Explicitly Not MVP

- Full NDC integration.
- GDS API integration.
- Full fare search automation.
- Full OTA content mixing.
- Full accounting.
- Complex drag/drop website builder.
- Native mobile app.
- Automatic airline scraping without review.
- Automatic ticketing.

## Later Scope

- Deeper document template editor.
- Advanced airline knowledge coverage and policy comparison.
- Optional supplier/GDS/NDC/portal integrations.
- Native mobile app.
- More advanced workflow automation.
- Advanced analytics and agency performance reporting.
- Payment provider integrations.
- Accounting export integrations.
- AI-assisted policy summarization with mandatory source review.
- Structured import from pasted GDS or booking data.
