# Commercial Pilot Agency Onboarding Foundation

## Purpose

Phase 58.1 introduces the first-time commercial-pilot setup experience for newly created agencies. It is a resumable coordination workflow over canonical AgencyOS records, not a second agency profile or travel architecture.

The active marker is `phase_58_1_commercial_pilot_agency_onboarding_foundation`.

## Eligibility And Lifecycle

`AgencyOnboardingProfile` is created in the same authenticated create-agency request for every newly created agency. The shared Agency frontend loader redirects an incomplete profile to `/agency/onboarding`; a completed profile returns to the normal workspace. Legacy agencies without an onboarding profile are explicitly exempt and continue to operate unchanged.

Each successful step persists immediately. The profile stores the current step, completed steps, progress, seed manifests, save timestamps, and completion actor. Completing the wizard changes the existing Agency status from `onboarding` to `active`; it does not activate providers or commercial execution.

## Canonical Ownership

- Agency name, legal identity, contact details, address, country, time zone, currency, and working hours remain on `Agency`.
- Logo assets and theme defaults remain in existing agency branding collections.
- Email readiness remains in `agency_email_settings`. The status records configuration state only and sends no message.
- Document defaults remain in `document_templates`.
- Dashboard and notification defaults use `agency_dashboard_preferences` and `agency_notification_preferences`.
- Synthetic examples use existing Client, Passenger, Operational Travel Workspace, Travel Request Workspace, Passenger Workspace, Flight Workspace, Trip Workspace, Offer Workspace, and Booking Workspace collections.

The onboarding profile owns only progress and deterministic references to records it coordinated.

## Default Seed

An explicit, idempotent onboarding action creates:

- one canonical agency workspace;
- restrained AeroAssist branding defaults;
- itinerary, booking-confirmation, and invoice document templates;
- operational dashboard widgets and notification preferences;
- disabled email metadata when no email settings exist.

Every seed uses deterministic agency-scoped IDs or compound keys. Retrying updates the same records rather than creating duplicates.

## Synthetic Travel Workspace

The demo workspace is realistic synthetic data for a Sofia–Frankfurt–New York business journey. It includes a demo company client, passenger, WCHR review context, request, operational workspace, two flight segments, trip, illustrative offer, and draft manual booking workspace.

All synthetic operational records are marked with `demo_data`, `synthetic`, and the Phase 58.1 source marker where the canonical model supports metadata. Email addresses use IANA-reserved `example.com` recipients and no messaging operation is invoked; passport data is deliberately omitted. The offer price and schedules are explicitly illustrative.

No airline, supplier, GDS, NDC, payment, ticket, email, SMS, AI, or other external operation is performed. No PNR, ticket, EMD, or payment is generated.

## Security And Audit

Agency owner/admin and Platform owner/admin roles may update onboarding. Existing agency read roles and Platform support may inspect state. Every mutation uses existing authentication, tenant membership checks, `Database` abstractions, and `audit_events`.

The new collections are agency-owned and use additive indexes. Uniqueness is compound by agency and profile/preference key; no existing production index or record is changed destructively.

## Routes

- UI: `/agency/onboarding`
- State: `GET /api/agencies/{agency_id}/onboarding`
- Agency details: `PUT /api/agencies/{agency_id}/onboarding/profile`
- Email status: `PUT /api/agencies/{agency_id}/onboarding/email-status`
- Preferences: `PUT /api/agencies/{agency_id}/onboarding/preferences`
- Logo confirmation/skip: `POST /api/agencies/{agency_id}/onboarding/logo/confirm|skip`
- Defaults: `POST /api/agencies/{agency_id}/onboarding/seed-defaults`
- Demo: `POST /api/agencies/{agency_id}/onboarding/demo-workspace`
- Completion: `POST /api/agencies/{agency_id}/onboarding/complete`

## Readiness And Verification

Public and internal readiness expose static, non-sensitive capability metadata under `commercial_pilot_agency_onboarding_foundation`. The focused smoke verifies new-agency eligibility, legacy exemption, progress, validation, idempotent defaults and synthetic records, completion gating, tenant isolation, audit evidence, route/UI registration, readiness, and execution-disabled boundaries.
