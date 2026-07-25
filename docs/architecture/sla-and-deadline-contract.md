# SLA and Deadline Contract

## Ownership

`OperationalDeadline` stores one calculated operational deadline. It links to
its source entity, workflow, work item, and timeline evidence. The record keeps
the matched `OperationalSlaPolicy` ID and version, original due date,
calculated due date, current due date, explanation, calculation snapshot,
pause duration, override history, breach state, and optimistic version.

## Calculation

The service supports fixed minutes, hours, and days; calendar hours; Agency
business hours and business days; Agency timezone; weekends; configured
holidays and exceptions; priority and task context; and evidenced external
dates. Server timestamps are UTC. UI display uses the browser or Agency
timezone.

Policy changes do not rewrite historical deadlines. Airline and supplier dates
are recorded evidence, not inferred universal truth.

## Actions and Evidence

Pause, resume, extend, complete, waive, and recalculate require active Agency
membership and `edit_tasks`. Pause, resume, extension, and override operations
require a reason. Manual extensions preserve the original date and append
actor, reason, timestamp, and before/after values to override history.

Due-soon and breach monitoring is deterministic, bounded, optimistic-versioned,
and idempotently reflected in work-item, workflow, and timeline evidence.
External reminders and enforcement remain disabled.
