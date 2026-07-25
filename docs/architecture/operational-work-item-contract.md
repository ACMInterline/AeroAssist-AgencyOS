# Operational Work Item Contract

## Canonical Owner

`OperationalWorkItem` in `operational_work_items` is the sole task truth.
Assignment events, dependencies, deadlines, approvals, automation runs, and
timeline entries are governed child evidence, not competing task records.

## Lifecycle

Canonical statuses are:

- `open`
- `assigned`
- `in_progress`
- `waiting`
- `blocked`
- `approval_required`
- `completed`
- `cancelled`
- `overdue`

Legacy `accept` and `reopen` actions remain valid deep-link adapters. They
normalize to `assigned` and `open`. Every transition is centralized in
`AgentWorkQueueService`, agency-scoped, optimistic-versioned, and evidenced by
an assignment event plus canonical timeline entry.

## Lineage and Completion

Generated work records the source entity, exact source timeline entry, rule
version, execution ID, and stable source fingerprint. Duplicate source/rule
actions reuse the existing canonical record.

Completion requires an actor and bounded completion evidence. Active mandatory
dependencies and unresolved blockers prevent completion. Class C work also
requires approved internal approval evidence; approval never performs the
underlying business action.

## Compatibility

Historical `RequestTask` records in `request_tasks` remain readable. Request
task create/update/complete routes adapt to canonical work-item operations and
do not create parallel task truth. Unsupported legacy mutations return `409`.

## Visibility

Agency membership and centralized task permissions are required. Internal
context, supplier cost, margin, secrets, and automation traces are not exposed
to Portal users. Entity pages consume the same reusable canonical work panel.
