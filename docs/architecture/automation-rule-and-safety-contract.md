# Automation Rule and Safety Contract

## Rule Lifecycle

An automation rule has immutable Agency or Platform scope, stable `rule_key`,
version, trigger event and entity types, bounded conditions, allowlisted
actions, priority, effective dates, safety class, audit metadata, and
publication evidence.

Statuses are `draft`, `active`, `inactive`, `superseded`, and `archived`.
Draft, inactive, superseded, and unpublished versions never execute. Material
edits create a new draft version. Publishing rejects a duplicate active key in
the same scope; superseding preserves the predecessor.

## Safe Conditions

Conditions support bounded `all`, `any`, and `not` groups and these operators:
`equals`, `not_equals`, `in`, `not_in`, `exists`, `not_exists`,
`greater_than`, `greater_than_or_equal`, `less_than`,
`less_than_or_equal`, `before`, `after`, `within_minutes`, `within_hours`,
`within_days`, `contains`, `starts_with`, and `ends_with`.

Field roots and leaves are allowlisted. Values are scalar or bounded lists.
There is no stored database query, regular-expression engine, expression
parser, `eval`, dynamic import, Python, or JavaScript. Unknown fields,
operators, action keys, and executable payloads are rejected.

## Safety Classes

- Class A: internal work, queue, assignment, priority, deadline, dependency,
  timeline, notification projection, and readiness evidence.
- Class B: governed escalation, reassignment, reopen, evidenced completion,
  document or information request projection, and approval creation.
- Class C: explicit human approval and a separate canonical business service.
  Automation creates approval-required work only.
- Class D: always prohibited, including provider execution, issuance,
  payments, refunds, deletion, tenant reassignment, permission mutation,
  autonomous regulated decisions, and fabricated evidence.

A rule cannot lower an action's safety class. Dry runs perform no writes.
Evaluation traces are deterministic, bounded, redacted, and internal-only.
