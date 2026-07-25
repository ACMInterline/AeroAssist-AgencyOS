# Task Automation And Dependency Orchestration Foundation

Phase 54.4 adds a metadata-only task automation and dependency orchestration foundation.

The foundation registers:

- `OperationalTaskTemplate`
- `OperationalTaskDependency`
- `OperationalTaskAutomationRule`
- `OperationalTaskAutomationRun`
- `operational_task_templates`
- `operational_task_dependencies`
- `operational_task_automation_rules`
- `operational_task_automation_runs`
- `/api/platform/task-automation`
- `/api/agencies/{agency_id}/task-automation`
- `/platform/task-automation`
- `/agency/task-automation`

This historical Phase 54 layer is reconciled by Product Recovery 11A.
`OperationalWorkItem` is now the sole actionable-work owner. Existing
`request_tasks` records remain readable compatibility history and projection
input; no new governed automation action writes parallel task truth.

## Safe Task Creation

`TaskAutomationDependencyService` stores reusable task templates and versioned
automation rules. Published active rules may create canonical
`OperationalWorkItem` records for known operational events such as request
triage, missing passenger data, documents, MEDIF, POC/battery checks,
PETC/AVIH documents, airline approval, offer preparation, manual quote review,
client acceptance follow-up, booking readiness, ticket/EMD verification,
payment follow-up, disruption handling, refund/change/claim follow-up, and
final trip document checks.

Creation is idempotent through automation run records and deduplication keys. Re-running the same safe metadata event records skipped tasks rather than creating duplicates.

## Dependencies

`OperationalTaskDependency` records predecessor and successor task relationships. Successor tasks with unsatisfied dependencies are marked as waiting and are synchronized into the canonical work queue as blocked/manual-review work. When predecessor task metadata is completed, dependencies can be satisfied and successor tasks return to ready visibility.

Dependency orchestration is advisory metadata. It does not execute tasks, enforce rollouts, block routes, or call providers.

## Queue, Workflow, And SLA Links

Generated work is created through the existing agent work queue service. Due
offsets and SLA policies create canonical deadline metadata for queue
visibility. Runs record exact source timeline lineage and may retain workflow
instance linkage where present.

These integrations are records only. They do not schedule workers, send communications, invoke provider systems, mutate booking/ticket/EMD state, or perform operational execution.

## Boundaries

Phase 54.4 does not run arbitrary code, execute providers, call external APIs, use AI, scrape, send email/SMS/WhatsApp/Slack/Teams, schedule background jobs, issue tickets, issue EMDs, process payments, enforce route access, or create a second task system.

Human authority remains final.
