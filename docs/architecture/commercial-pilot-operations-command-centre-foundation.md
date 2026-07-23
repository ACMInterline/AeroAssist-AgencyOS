# Commercial Pilot Operations Command Centre Foundation

Phase 58.2 makes the canonical Agency home route a calm operational workspace for travel consultants. A consultant should be able to identify the next work, its urgency, its deadline, and the relevant client or passenger within seconds.

## Canonical Surface

- Agency home: `/agency`
- Compatibility UI route: `/agency/operations-command-center`
- Agency API: `GET /api/agencies/{agency_id}/operations-command-center`
- Existing work-item actions: `/api/agencies/{agency_id}/work-queue/work-items/{work_item_id}/*`

Completed and legacy-exempt agencies open the command centre through the shared Agency loader. Newly created agencies that have not completed Phase 58.1 continue to be redirected to `/agency/onboarding`; Phase 58.2 does not add another onboarding gate.

## Aggregation Contract

The Agency API returns a stable operational summary containing:

- `generated_at`, `agency_id`, and the current user and role context;
- `priorities` for My Work Today;
- named `queues` with counts and bounded previews;
- a timezone-aware selected-day `timeline` with previous, today, and next navigation;
- actionable `alerts` containing what happened, why it matters, the next action, any deadline, and a canonical link;
- permission-aware `quick_actions`;
- user-facing `recent_activity` from canonical timeline and audit records;
- selected filters, filter options, assignees, and explicit result limits;
- Phase 54.8 compatibility fields for existing consumers.

All source reads are agency-scoped and bounded to 250 records per collection. My Work results are capped at 50, queue previews at 10, alerts at 30, and recent activity at 20. Ordering is deterministic by urgency, deadline, creation time, and stable identifier. Empty agencies return complete empty structures rather than errors.

## Urgency Rules

Urgency is a deterministic presentation score derived from the canonical work item's priority, severity, SLA/status, and due time. Overdue work and critical severity display as critical; high combined scores display as urgent or high; lower active work displays as normal or low. Due work gains weight at 72 and 24 hours, and passed deadlines gain the strongest due-time weight. The command centre never writes this derived label back to the source record. Ties resolve by earliest deadline, earliest creation time, then stable identifier.

## Canonical Sources

The service extends the Phase 54.8 `OperationsCommandCenterService` presentation layer. It reads existing work items, SLA deadlines, workflow state, requests, offers, booking handoffs, booking readiness, booking/ticket/EMD workspaces, passenger services, document workspaces and deliveries, trips, flights, finance records, request tasks, operational timelines, audit events, agency staff, and Phase 58.1 preferences.

No command-centre collection, task model, workflow model, timeline, alert record, or queue record is created. Alerts and queue groupings are derived views over canonical records.

## Supported Actions

The command centre itself remains a read aggregation endpoint. Work rows can expose only operations already governed by the canonical work queue:

- open the canonical linked record;
- assign to self;
- reassign to an active agency staff member;
- complete the work item with confirmation.

The work-queue API continues to enforce agency access, agency role, valid action semantics, persistence, and assignment history. Platform users viewing an agency receive a read-only context and Agency Readonly users receive only safe navigation actions.

## Preferences and Compatibility

`AgencyDashboardPreferences` adds optional fields for the preferred starting section, visible operations sections, default assignment filter, and default urgency filter. Phase 58.1 seeds these values for new agencies. Records created before Phase 58.2 receive conservative in-service defaults and require no migration.

The previous `/agency/operations-command-center` route remains registered, but primary navigation points to `/agency`. Phase 54.8 Platform operations governance is unchanged.

## Safety Boundaries

Phase 58.2 does not call airlines, GDS, NDC, payment, messaging, AI, or other providers. It does not add a background worker, automatic transition, uncontrolled drag-and-drop, cross-tenant query, second task system, second workflow system, or duplicate operational store. Unknown links become plain missing-context labels and manual review remains visible.

## Verification

`backend/scripts/smoke_commercial_pilot_operations_command_centre_foundation.py` verifies populated and empty summaries, deterministic ordering, tenant isolation, user and team assignment visibility, role-aware actions, queue grouping, overdue detection, timeline navigation, canonical links, Phase 58.1 preference and legacy behavior, frontend registration, readiness, and no-execution boundaries.
