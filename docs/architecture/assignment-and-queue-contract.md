# Assignment and Queue Contract

## Eligibility

Assignments require an active `AgencyStaffMembership` in the work item's
Agency. The assignee must hold the task type's required permission. Platform
role alone never grants Agency assignment eligibility. Revoked or disabled
members are excluded and historical assignments remain visible for
reassignment.

## Strategies

The governed router supports:

- fixed user
- fixed team
- least open eligible work
- deterministic round robin
- retain current owner
- parent entity owner
- manual assignment required

Least-workload ties resolve by stable user ID. Round robin uses a stable hash
of Agency, work item, and eligible user set. If no candidate is eligible, the
work remains unassigned in its canonical queue with an explanation.

## Queues and Ordering

Canonical views include My Work, Team Work, Unassigned, Urgent/Critical,
Due Soon, Overdue, Waiting, Blocked, Approval Required, documents, payment,
disruption, service case, knowledge gap, and workflow blocker queues.

Results are bounded and ordered by priority, SLA state, due date, severity,
creation time, and ID. Assignment events retain actor, reason, previous and
next owner/team, and canonical timeline evidence. Bulk assignment is limited
to safe eligible records.
