# Client Passenger Master Workspace Foundation

Phase 51.3 adds metadata-only master workspace consolidation for Client and Passenger entities.

Client represents the commercial relationship and commercial owner. Passenger represents the operational beneficiary and reusable operational identity. The foundation supports many-to-many client-passenger relationships without replacing the existing client and passenger profile records.

## Scope

- `client_master_records` stores commercial-owner metadata: profile, contacts, portal status, permissions, linked passengers, requests, trips, offers, invoices, communications, and documents.
- `passenger_master_records` stores operational identity metadata: operational profile, service history, mobility and medical profile, pets, special items, documents, trips, booking mirrors, ticket mirrors, EMD mirrors, operational evaluations, feasibility history, recommendation history, preferred airlines, preferred cabins, and preferred seats.
- `client_passenger_links` records many-to-many relationship metadata between client masters and passenger masters.
- `passenger_service_history` stores reusable service-history references across requests, trips, booking mirrors, ticket mirrors, EMD mirrors, documents, operational evaluations, feasibility, and recommendations.
- `passenger_operational_preferences`, `passenger_known_documents`, and `client_portal_access_profiles` store preference, document, and portal-access metadata for review.

## Boundaries

Phase 51.3 is metadata-only. It does not add CRM sales pipeline behavior, marketing automation, provider integrations, AI/LLM generation, booking, ticketing, payment gateway processing, background workers, or automatic client sending.

The foundation does not add new airline intelligence. It prepares the system to reuse passenger operational history across the Chapter 50 and Chapter 51 intelligence pipeline, especially scenario testing and real airline data population.

Human authority remains final for relationship interpretation, passenger operational suitability, portal visibility, offer readiness, and client-facing presentation.

## Routes And UI

- Platform API: `/api/platform/client-master`, `/api/platform/passenger-master`, plus child metadata routes for client-passenger links, passenger service history, passenger operational preferences, passenger known documents, and client portal access profiles.
- Agency API: `/api/agencies/{agency_id}/client-master`, `/api/agencies/{agency_id}/passenger-master`, plus the same agency-scoped child metadata routes.
- Platform UI: `/platform/client-master` and `/platform/passenger-master`.
- Agency UI: `/agency/clients` and `/agency/passengers`.

The UI shows Case-style operational sections for Client Overview, Passenger Overview, Service History, Known Operational Profile, Known Preferences, Portal Access, Relationship Graph, and Notes.
