# Operational Constraint Engine Foundation

Phase 50.2 creates the Operational Constraint Engine foundation.

This phase is metadata only. It defines the formal constraint language that future AOIE phases will use to reason over Airline Operational Knowledge. It does not execute constraints.

## Purpose

Airline operations are conditional operational constraints, not simple flat rules. Policy, pricing, capability, and operational procedures can all create constraints.

Examples:

- IF species equals Bird and destination country equals Qatar and season equals Bird Exhibition, THEN service allowed.
- IF cabin equals Business and aircraft equals A321, THEN extra seat possible is false.
- IF breed equals French Bulldog and temperature is greater than 29C, THEN transport embargo applies.

## Data

Collection: `operational_constraints`

Models:

- `OperationalConstraint`
- `OperationalConstraintCreate`
- `OperationalConstraintUpdate`
- `OperationalConstraintCondition`
- `OperationalConstraintConditionGroup`

Each record stores constraint reference/status/version/name/description, knowledge links to Phase 50.1 acquisition metadata, condition logic, condition groups, direct conditions, outcome metadata, applicability metadata, priority and precedence metadata, governance metadata, future evaluation metadata, operational workspace links, and internal notes.

Supported condition operators are metadata values only:

- `equals`
- `not_equals`
- `contains`
- `not_contains`
- `greater_than`
- `less_than`
- `greater_than_or_equal`
- `less_than_or_equal`
- `in`
- `not_in`
- `between`
- `exists`
- `not_exists`

Outcome metadata can describe allowed, not allowed, approval required, document required, EMD required, manual review required, embargo, restriction applies, pricing rule applies, refund condition applies, capability available, and capability unavailable.

## Routes

Platform metadata views and create/update/archive:

- `GET /api/platform/operational-constraints`
- `GET /api/platform/operational-constraints/summary`
- `POST /api/platform/operational-constraints`
- `GET /api/platform/operational-constraints/{constraint_id}`
- `PUT /api/platform/operational-constraints/{constraint_id}`
- `DELETE /api/platform/operational-constraints/{constraint_id}`

Agency read-only visibility:

- `GET /api/agencies/{agency_id}/operational-constraints`
- `GET /api/agencies/{agency_id}/operational-constraints/summary`
- `GET /api/agencies/{agency_id}/operational-constraints/{constraint_id}`

There is no evaluation route.

## UI

- Platform Console: `/platform/operational-constraints`
- Agency Workspace: `/agency/operational-constraints`

The UI displays Constraint Overview, Knowledge Link, Conditions, Outcomes, Applicability, Priority / Precedence, Governance, Future Evaluation, and Operational Links.

## AOIE Linkage

Operational Constraints are the future reasoning language of AOIE. Future feasibility and recommendation phases may evaluate constraints only in explicitly authorized later phases.

Phase 50.3 Airline Operational Knowledge Normalisation creates canonical vocabulary and taxonomy metadata for the terms used by constraints. Normalisation does not evaluate rules; it helps future AOIE compare airlines consistently.

Phase 50.4 Airline Operational Knowledge Governance & Version Control versions operational constraints as governed knowledge assets and links them to releases, comparison metadata, rollback metadata, superseded metadata, and historical audit metadata. Governance does not execute constraints.

Phase 50.5 Airline Operational Capability Matrix links governed operational constraints to capability inventory records. It records whether a capability is available, unavailable, conditional, restricted, or manually reviewed under stated operational conditions, but it does not execute constraints or evaluate passenger cases.

Phase 50.2 does not implement live rule execution, AI reasoning, recommendation engines, feasibility scoring, pricing calculation, parser execution, scraping, background workers, provider integrations, or external API calls.
