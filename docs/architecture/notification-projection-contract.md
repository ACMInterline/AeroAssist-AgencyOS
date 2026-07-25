# Notification Projection Contract

## Principle

An operational notification is a disposable projection. It is not business
truth. `OperationalTimeline` is the source of truth.

`operational_notification_projections` may contain:

- `info`
- `warning`
- `action_required`
- `approval_required`
- `deadline`
- `failed`

Each projection links one timeline entry, carries the same Agency and
visibility boundary, and uses a deterministic projection key.

## Regeneration

Projection rebuild:

1. reads bounded canonical timeline entries;
2. applies deterministic event/status/priority rules;
3. inserts only missing deterministic projections;
4. leaves timeline, communication, audit, task, and workflow records
   untouched.

Projection deletion or re-creation can never delete operational evidence.
Unread/read state is presentation state and cannot replace workflow, queue, or
approval state.

## Safety

No projection sends email, SMS, chat, Portal, supplier, or airline messages.
No background worker or provider integration is enabled. A projected
notification indicates attention only; it never approves, executes, books,
tickets, charges, refunds, or changes a business record.
