# Commercial Pilot Overview

## Purpose

The Commercial Pilot lets a real micro or small travel agency evaluate AeroAssist in controlled daily work. The pilot should prove that staff can understand the product, complete setup, use linked synthetic examples, follow the main operational path, recover from understandable errors, and submit governed feedback.

## Supported Scope

The supported pilot path covers:

- Agency onboarding, branding defaults, working hours, currency, dashboard preferences, and notification preferences.
- Synthetic demo profiles and linked Client, Passenger, Request, Trip, Offer, accepted-offer, Booking, Ticket/EMD, passenger-service, Document, Finance, task, deadline, timeline, disruption, and after-sales metadata.
- Agency Operations as the primary daily home.
- Canonical work queues, deadlines, status visibility, validation states, related records, and guarded operator actions.
- Platform visibility for Commercial Pilot readiness and tenant-scoped feedback review.
- Human-reviewed release, evidence, backup, rollback, and sign-off governance from Phase 57.

## Known Limitations

The pilot does not provide live provider connectivity, GDS/NDC execution, airline API calls, automatic booking, ticket or EMD issuance, payment execution, automatic messaging, background automation, production seeding, automatic deployment, automatic backup/restore, or automatic release approval.

Some workspaces intentionally hold operational metadata rather than authoritative supplier state. Staff must verify airline, supplier, financial, ticket, document, and passenger-service facts using the agency’s approved external procedures. Unknown or incomplete data should remain visible as a warning or manual-review condition.

Repository document paths shown in the UI are controlled references. Access to the actual files follows the deployment owner’s approved documentation procedure.

## Roles

- **Agency Owner / Administrator:** completes setup, manages staff and agency configuration, reviews operational workload, and owns pilot acceptance.
- **Travel Consultant:** manages day-to-day requests, passengers, offers, readiness, bookings, documents, tasks, and follow-up metadata.
- **Agency Read-only user:** may inspect permitted feedback and operational records but cannot submit or review governed feedback.
- **Platform Owner / Administrator / Support:** reviews pilot feedback and Commercial Pilot readiness within existing role boundaries.

## Success

A pilot is successful when the agency can complete the acceptance checklist without bypassing permissions or execution boundaries, all material defects and workflow gaps are recorded, recovery responsibilities are understood, and the authorized humans decide whether and how to continue.
