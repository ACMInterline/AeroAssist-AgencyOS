# Phase 26 — Request Intake Operational Request Stabilization

Phase 26 makes public and portal request submission production-safe by storing submissions as request intakes first. Staff must explicitly triage and convert an intake before it becomes a canonical operational request.

## Implemented

- Public unauthenticated intake endpoint: `POST /api/public/request-intakes`.
- Staff intake queue endpoints: `GET /api/request-intakes`, `GET /api/request-intakes/{id}`.
- Staff triage/action endpoints:
  - `PATCH /api/request-intakes/{id}/triage`
  - `POST /api/request-intakes/{id}/convert`
  - `POST /api/request-intakes/{id}/reject`
  - `POST /api/request-intakes/{id}/archive`
  - `POST /api/request-intakes/{id}/mark-duplicate`
- Additive `request_intakes` model with contact, travel, services, raw/canonical payload, triage fields, conversion metadata, and timestamps.
- Conversion service that creates or reuses a client, creates a canonical `travel_requests` record, adds route/service snapshots, links `source_intake_id`, and preserves intake payload snapshots.
- Duplicate conversion guard: repeated conversion returns the existing converted request instead of creating another request.
- Portal request submission now creates a request intake and portal action instead of directly creating an operational request.
- Public homepage form submits to the public intake endpoint and returns only a safe reference code.
- Staff UI pages for intake queue and intake detail/triage/conversion.
- Operational request detail links back to the source intake when converted.
- Platform/readiness summaries include intake and open operational request counts without making readiness depend on any intake existing.
- Smoke script: `backend/scripts/smoke_request_intake_conversion.py`.

## Public Intake Behavior

- No authentication is required for `POST /api/public/request-intakes`.
- Public payloads are schema-forbid by default and cannot set status, assignment, agency role, internal notes, conversion fields, or privileged workflow state.
- Public responses include only `id`, `reference_code`, and safe status `received`.
- Submissions default to `status=new` and `source=public_website`.
- If exactly one active agency/workspace is configured, the intake is routed there; otherwise staff/platform triage can assign routing later.

## Staff Triage Behavior

- Staff endpoints require authenticated platform/staff users.
- Platform owner/admin/support can view all intakes.
- Agency users see only intakes scoped to their active agency memberships.
- Read-only/accounting roles can view; owner/admin/agent can triage and act.
- Triage can update priority, assignment, notes, and routing where permitted.
- Reject, archive, duplicate, triage, and conversion actions write audit events.

## Conversion Behavior

- Conversion validates:
  - assigned agency exists,
  - client name exists,
  - route summary or travel notes exist,
  - service category or request details exist.
- Conversion preserves:
  - contact snapshot,
  - travel/route summary,
  - passenger count,
  - selected services,
  - canonical/raw intake payload snapshot,
  - internal notes,
  - source intake id.
- Conversion does not create bookings, offers, airline tasks, payments, document deliveries, or automatic email.

## Not Included

- No GDS/NDC/airline integrations.
- No automatic pricing.
- No payment gateway integration.
- No automatic email sending.
- No public document links.
- No customer portal account creation.
- No external SaaS dependency.
- No demo auth or seed endpoint re-enablement.

## Known Limits

- Public submissions are lightweight and intentionally do not create full passenger profiles.
- Phone-only public contacts convert with an internal placeholder email because existing client profiles require `primary_email`.
- Duplicate detection is staff-marked; no fuzzy matching automation is included.
- Portal request history still shows operational requests, while newly submitted portal requests remain intake records until staff conversion.

## Next Recommended Phase

Phase 27 should harden post-conversion operational workspace depth: passenger/profile enrichment from intake, duplicate detection assistance, and clearer staff work queues before adding external delivery, airline, payment, or pricing automation.
