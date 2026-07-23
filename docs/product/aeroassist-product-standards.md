# AeroAssist Product Standards

## Purpose

These standards define how AeroAssist should feel and behave for travel professionals. They apply first to the Agency workspace and should guide future Platform and Client Portal work where the audience and permissions are comparable.

The product should be understandable without software training. A consultant should be able to answer three questions on every operational page:

1. What am I looking at?
2. What needs attention?
3. What should I do next?

These standards refine presentation and interaction. They do not change canonical models, authorization, workflow guards, or operational ownership.

## Product Language

Use travel and service language in ordinary Agency UI.

| Prefer | Avoid in ordinary UI |
| --- | --- |
| Passenger | entity, object |
| Client | account object |
| Request | intake entity |
| Trip | journey record type |
| Offer | commercial payload |
| Booking | booking object |
| Ticket | ticket record |
| Special Service | service schema |
| Task | work item entity |
| Follow-up | automation event |
| Current Status | state transition |
| Assigned Consultant | assigned user identifier |
| Next Action | execution mode |

Technical names may remain in source code, APIs, architecture documents, Platform diagnostics, and an explicitly labelled **Advanced** disclosure. They should not be the first explanation an Agency user sees.

Status labels should be sentence-like and meaningful:

- `waiting_for_client` becomes **Waiting for client**.
- `ready_to_book` becomes **Ready to book**.
- `draft_metadata` becomes **Draft**.
- `duplicate_merged` becomes **Merged duplicate**.

## Shared Component Inventory

Phase 58.4 uses the existing React and Tailwind foundations. Shared components remain small and domain-neutral:

| Component | Standard use |
| --- | --- |
| `PageHeader` | Breadcrumbs, page purpose, current status, and primary actions. |
| `SectionHeader` | A section title, short purpose, and at most one section action. |
| `PrimaryButton` | The clearest next action on the current surface. |
| `SecondaryButton` | Safe supporting actions. |
| `DestructiveButton` | Reversible or destructive actions that require clear intent. |
| `EmptyState` | Explains why a list is empty and provides a useful next action where permitted. |
| `LoadingState` | Announces that a workspace is opening without shifting the layout. |
| `ErrorState` | Explains failure in plain language and supports safe retry where available. |
| `StatusBadge` | Text plus colour treatment for current status. |
| `PriorityBadge` | Text plus colour treatment for operational priority. |
| `FilterBar` | Labelled search and filters, result count, and clear action. |
| `ConfirmationDialog` | Focused confirmation for consequential actions. |
| `DetailSummary` | Compact labelled facts for the current operational object. |
| `Timeline` | Chronological activity with event, summary, and time. |
| `OperationalAlert` | Actionable information, success, warning, or error. |
| `FormSection` | Related form fields with a meaningful heading and optional help. |

Do not create a page-local equivalent when one of these components fits. A domain-specific badge may wrap `StatusBadge` when it needs a constrained status vocabulary.

## 1. Page Structure

Use this order where the information exists:

1. Breadcrumbs and page header.
2. Current status and primary next action.
3. Blocking warning or important operational alert.
4. Summary facts.
5. Main work area.
6. Related records and activity history.
7. Advanced or rarely used details.

The primary experience should not sit inside a decorative hero or marketing card. Operational pages should be quiet, scan-friendly, and constrained by the shared Agency layout.

## 2. Headers And Breadcrumbs

Use one `h1` for the page title. Headings should describe the travel object or task:

- **Requests**
- **New travel request**
- **Booking workspace**
- **Maria Petrova**

Use breadcrumbs for location, not as a substitute for a browser back button. Example:

`Requests / REQ-1042`

The description should explain purpose in one or two sentences. Do not describe implementation architecture.

## 3. Primary And Secondary Actions

Every page should have zero or one visually dominant action. A second action may be primary only when the user must choose between two equivalent starts.

Examples:

- Requests: **Create request**
- Accepted offer: **Prepare booking**
- Booking: **Add ticket details**
- Document requirement: **Record document review**

Put supporting actions beside the primary action or in their owning section. Put rarely used actions in an **Advanced** disclosure or menu.

## 4. Buttons

Use an icon when a familiar Lucide icon improves recognition. Keep the text as a verb phrase:

- **Create request**
- **Refresh tasks**
- **Save booking details**
- **Archive passenger**

Buttons should have a stable height, visible focus, disabled styling, and a busy label that describes the work. Avoid vague labels such as **Submit**, **Execute**, **Run**, or **OK** when a specific action is known.

## 5. Forms

Group related fields with `FormSection`. Keep the default form width readable and use responsive columns only when fields have a clear relationship.

Required information should be apparent before submission. Preserve entered values after a recoverable error. Validation should explain how to fix the issue:

- Good: **Add at least one passenger and one flight segment before preparing the trip.**
- Avoid: **Validation failed for payload.**

Use a selector for an existing Client, Passenger, Request, Trip, Offer, Booking, Ticket, EMD, Special Service, or Document. Manual reference entry belongs only in an advanced or import context when no selector contract exists.

## 6. Field Labels And Help Text

Every control needs a visible label or an accessible name. Placeholder text is an example, not a label.

Use business labels:

- **Passenger type**, not **PTC** as the only label.
- **Received through**, not **Source enum**.
- **Booking source**, not **Provider target**.
- **Related reference**, not **Object ID**.

Help text should explain why information matters or what happens next. Keep it brief and place it next to the control.

## 7. Tables And Lists

Use tables for comparison and lists or rows for operational scanning. The first column should identify the travel object in human-readable language. Raw references are secondary.

Tables must:

- keep column headings visible and unambiguous;
- provide a useful empty state;
- retain a stable layout while status or action content changes;
- scroll horizontally on narrow tablet layouts rather than compressing text into unreadable columns;
- avoid relying on hover to expose essential actions.

## 8. Status Indicators

Show status as text with colour, never colour alone. Use one shared label for the same status across pages.

Place the current status near the title or relevant row. When status does not explain readiness, add a short reason:

**More trip details needed**

Add at least one passenger and one flight segment.

Do not imply that a feature, ticket, payment, provider action, or approval occurred when AeroAssist only stores the result entered by an operator.

## 9. Empty States

An empty state should say:

1. what is absent;
2. whether filters may be hiding results;
3. what the authorized user can do next.

Example:

**No requests match these filters**

Clear the filters or create a request when a client needs travel support.

Do not use empty states to explain internal architecture.

## 10. Loading States

Use `LoadingState` with `role="status"` and `aria-live="polite"`. Prefer a specific label such as **Opening accepted offers** when the context is useful.

Loading content should not alter the width of a fixed-format table, toolbar, dialog, or board. Disable the initiating action and use a meaningful busy label.

## 11. Error States

Errors should preserve the user's context whenever existing data has already loaded. Use an in-page `OperationalAlert` for action failures and `ErrorState` when the page cannot open.

Messages should:

- describe what could not be completed;
- avoid stack traces and internal field names;
- say whether existing work was changed;
- provide retry or correction guidance where safe.

## 12. Confirmation Dialogs

Require confirmation before cancellation, archive, merge, release, or another consequential action. The dialog must:

- name the action and affected travel object;
- explain what remains preserved;
- focus a dialog action when opened;
- close with Escape;
- restore prior focus when closed;
- use explicit confirm and cancel labels.

Never use a destructive colour for a safe navigation action.

## 13. Timelines

Display newest or oldest first according to the operational context and say which ordering is used when it is not obvious. Each item should include:

- event or action;
- actor label when safe and available;
- timestamp;
- short description;
- link to related work when useful.

Do not expose internal correlation values in the main timeline. Those can remain in Advanced diagnostics.

## 14. Operational Alerts

Alerts must be actionable. Use:

- **Info** for context or a safe boundary.
- **Success** for a completed save or review.
- **Warning** for work that can continue with attention.
- **Error** for a failed action or blocked step.

Do not use an alert solely as decoration. Do not dismiss a critical blocker automatically.

## 15. Filters

Use `FilterBar` with visible labels, a result count, and **Clear filters**. Filters should reflect travel work:

- Current status
- Priority
- Assigned consultant
- Travel date
- Client
- Airline

Keep filters when refreshing the same list. Avoid exposing database field names.

## 16. Responsive Behaviour

Phase 58.4 targets:

- standard desktop;
- smaller laptop;
- tablet landscape;
- tablet portrait where practical.

Use wrapping action groups, bounded form columns, stable controls, and horizontal table scrolling. Do not scale font size with viewport width. Mobile-phone optimization remains a later, separate validation scope.

## 17. Accessibility

The baseline includes:

- semantic headings and landmarks;
- visible labels or accessible names for controls;
- keyboard-accessible buttons, links, disclosures, and dialogs;
- visible focus indicators;
- text labels in status and priority badges;
- polite loading and progress announcements;
- error alerts announced by assistive technology;
- reduced-motion support.

This phase does not claim WCAG conformance. Formal screen-reader, keyboard-only, zoom, contrast, and browser testing remains required before such a claim.

## 18. Progressive Disclosure

Show the information needed for today's decision first. Place raw source details, import overrides, internal references, and rarely used recovery controls inside an **Advanced** disclosure.

Progressive disclosure must not hide:

- blockers;
- required client or passenger information;
- the primary next action;
- consequential warnings;
- current status.

## 19. Destructive Actions

Destructive actions must be visually distinct, permission-checked by the existing backend, and confirmed with a reason when the domain requires one.

Prefer archive or status change over deletion. Explain the preserved history. Never expose a destructive action merely because a button can be rendered; existing authorization remains authoritative.

## 20. Customization Principles

Describe preferences as business choices:

- **Show ticketing work first.**
- **Start on today's operations.**
- **Notify me when a document deadline changes.**
- **Use a compact list.**

Avoid exposing rules as implementation controls:

- **Default queue type**
- **Trigger transition**
- **Automation payload**

Customization may adjust order, density, defaults, and visibility. It must not create a second workflow engine, bypass guards, or change tenant boundaries.

## Priority Workflow Application

Phase 58.4 applies these standards first to:

1. Agency onboarding.
2. Operations.
3. Requests.
4. Offers.
5. Booking workspace.
6. Passenger profiles.
7. Documents.
8. Tasks and follow-ups.

These workflows keep their existing APIs and domain ownership. The refinement standardizes page headers, actions, filters, states, badges, confirmations, summaries, timelines, terminology, and advanced disclosures.

## Review Checklist

Before approving a new or changed product surface, verify:

- The title and description use travel language.
- The primary next action is clear.
- Every control has an accessible name.
- Empty, loading, error, disabled, and success states exist where relevant.
- Status is not conveyed by colour alone.
- Consequential actions require confirmation.
- Raw references and implementation details are not primary content.
- Agency permissions and tenant isolation are preserved.
- Desktop and tablet layouts remain readable.
- The capability belongs to an existing primary workspace or has a documented ownership exception.

## Known Limitations And Deferred Work

- No formal WCAG audit has been completed.
- Mobile-phone optimization is not part of Phase 58.4.
- Browser and assistive-technology matrices require separate executed testing.
- Older non-priority Agency pages may still contain foundation-era terminology or page-local component patterns.
- A full workflow editor is intentionally deferred.
- Phase 58.4 introduces no backend label directory, design-token migration, new route, model, collection, or operational capability.
