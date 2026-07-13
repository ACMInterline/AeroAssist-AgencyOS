# SLA and Operational Deadline Engine Foundation

Phase 54.3 adds a metadata-only SLA and operational deadline engine.

The foundation registers:

- `OperationalSlaPolicy`
- `OperationalDeadline`
- `OperationalSlaEvent`
- `OperationalBusinessCalendar`
- `operational_sla_policies`
- `operational_deadlines`
- `operational_sla_events`
- `operational_business_calendars`
- `/api/platform/sla-policies`
- `/api/agencies/{agency_id}/deadlines`
- `/platform/sla-policies`
- `/agency/deadlines`

The engine supports request response, offer preparation, offer expiry, ticketing, airline approval, MEDIF/document, PETC/AVIH notice, UMNR notice, mobility/POC notice, payment, booking/ticketing, task, disruption response, and claim/refund/change deadline metadata.

## Calculation Metadata

`OperationalSlaDeadlineService` matches policy metadata by agency, deadline type, entity type, work item type, priority, service family, and effective dates. It calculates advisory `due_at` values from calendar time or business calendars, stores `original_due_at`, `calculated_due_at`, `due_at`, explanation text, calculation snapshots, and escalation suggestions.

Manual extensions are preserved. Recalculation does not silently overwrite a manually approved extension unless a caller explicitly asks for forced recalculation.

## Audit And Visibility

Every pause, resume, warning, breach, extension, completion, waiver, and recalculation records `OperationalSlaEvent` metadata. Deadline records can synchronize advisory `due_at` and `sla_status` metadata onto existing `OperationalWorkItem` records, and can emit operational workflow/timeline metadata references.

These emissions are records only. They are not workers, schedulers, provider calls, route blocking, messaging, or operational execution.

## Boundaries

Phase 54.3 does not enforce access, block routes, execute workflows, call providers, send email/SMS/WhatsApp/Slack/Teams, schedule jobs, calculate live fares, book, ticket, issue EMDs, process payments, use AI, scrape, publish, or automate operational action.

Human authority remains final.
