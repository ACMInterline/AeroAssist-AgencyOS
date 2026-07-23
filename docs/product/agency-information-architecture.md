# Agency Information Architecture

Phase 59.0 orders the Agency Workspace around the work a travel consultant performs. It retains the Phase 58.2 Operations Command Centre as the default home and preserves Phase 58.1 onboarding behavior.

## Product Goal

An Agency user should understand the next action within 10 seconds. Daily operational work is primary; system diagnostics and planning registers are secondary.

## Before

The sidebar mixed daily work, metadata workspaces, airline intelligence foundations, rollout registers, state diagnostics, website tools, and settings. Several routes represented the same user objective, and implementation labels obscured the normal order of travel work.

## After

The Agency navigation follows this workflow:

1. Operations
2. Requests
3. Clients & Passengers
4. Trips
5. Offers
6. Bookings
7. Tickets & EMDs
8. Special Services
9. Documents
10. Tasks & Follow-ups
11. Reports
12. Settings
13. Advanced

`/agency` and the visible Operations link both open the Phase 58.2 Operations Command Centre. Newly created incomplete agencies still redirect to `/agency/onboarding`. Legacy agencies without onboarding profiles remain compatible through the existing legacy exemption.

## Before And After Mapping

| Before: navigation item or group | After: primary area | Notes |
|---|---|---|
| Daily Work, Operations Command Centre compatibility route | Operations | One visible home route: `/agency`. |
| Requests, Create request, Intakes, Travel Request Workspaces | Requests | Creation stays a prominent action; specialist request mirrors move to Advanced. |
| Clients & Passengers, Passenger Workspaces | Clients & Passengers | Canonical client and passenger workspaces are primary. |
| Trips, Trip Workspaces, Journey views | Trips | Trip dossiers are primary; journey engines and diagnostics are contextual or Advanced. |
| Offers, offer intelligence, comparison, delivery, export registers | Offers | Offer Workspace is primary; supporting engines remain contextual or Advanced. |
| Booking Mirrors, Booking Handoffs, imports | Bookings | Booking records and readiness are primary; import diagnostics move to Advanced. |
| Tickets & EMDs, Ticket Workspaces, EMD Workspaces | Tickets & EMDs | One daily objective; detailed mirrors remain available in Advanced. |
| Passenger Services, service feasibility, policy advisors | Special Services | Passenger assistance is primary; specialist intelligence stays Advanced. |
| Document Workspaces, Documents, export governance | Documents | Required documents and prepared files are primary. |
| Agent Work Queue, Deadlines, Task Automation | Tasks & Follow-ups | Work and deadlines are primary; automation diagnostics move to Advanced. |
| Invoices and payment status | Reports | Existing finance route is reused; no reporting subsystem is introduced. |
| Branding, forms, subscription, feature and rollout settings | Settings | Owner/Admin see everyday settings; rollout internals move to Advanced. |
| Workflow maturity, operational workflows, state details, rollout registers, knowledge tooling | Advanced | Collapsed by default and limited to Agency Owner/Admin. |

## Permission Behavior

- Agency Owner and Agency Admin see operational areas, Settings, and Advanced.
- Agency Agent sees daily operational areas without Settings or Advanced.
- Agency Read-only sees permitted read views without Settings or Advanced.
- Agency Accountant sees finance-relevant Operations, clients, bookings, tickets, documents, tasks, and Reports.
- Platform Owner/Admin entering an Agency context receive the existing platform override behavior.

These rules only prevent misleading navigation exposure. Tenant and role checks on the canonical API remain authoritative.

## Workflow Diagnostics Recovery

`/agency/operational-workflows` is now an Advanced view. A stale or absent optional workflow-diagnostics record no longer turns the entire page into a red failure. The page displays:

> No workflow diagnostics are available for this agency yet.

Genuine authorization, tenancy, and unrelated API errors still fail normally. Technical workflow-state JSON is inside a closed Advanced system details disclosure and is not visible by default.

## Safety

No fake workflow records are created. No workflow, provider, payment, ticketing, messaging, or automation behavior is enabled. All existing deep links remain valid.

