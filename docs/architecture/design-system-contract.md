# Design System Contract

## Product Primitives

Normal AeroAssist surfaces reuse:

- `WorkspacePage` for standard, wide, focused, and reading layouts
- `PageHeader` for breadcrumbs, title, description, status, and actions
- `WorkflowContinuityPanel` for workflow position and guarded next actions
- `ProductTable` for accessible responsive lists with optional sorting,
  pagination, selection, and guarded bulk actions
- `EmptyState`, `LoadingState`, and `OperationalAlert` for system states
- `StatusBadge` and domain badges for concise status
- `FilterBar` for list filtering
- `ProductQuickSearch` for permitted-page discovery
- `WorkflowQuickActions` for permission-aware task shortcuts
- `ConfirmationDialog` for consequential guarded actions

## Visual Rules

- Use restrained white and neutral work surfaces with semantic blue, green,
  amber, and red accents.
- Keep cards at an 8px radius or less.
- Avoid cards nested inside decorative cards.
- Keep headings proportional to their operational context.
- Use Lucide icons for familiar actions and icon-only buttons.
- Give icon-only buttons an accessible name and tooltip.
- Keep tables scan-friendly with stable columns and horizontal overflow on
  narrow screens.

## Responsive Rules

- Agency navigation uses a mobile drawer and a desktop rail.
- Platform navigation supports a compact desktop state and mobile drawer.
- Portal navigation remains horizontally scrollable on small screens.
- Dashboard grids collapse progressively without changing reading order.
- Fixed controls have stable dimensions and text must not overlap.
- Detail actions wrap rather than overflow.

## Accessibility Rules

- Each shell provides a skip link and a focusable `main` target.
- Active navigation uses `aria-current="page"`.
- Dialog-like search controls expose their expanded state and close on Escape.
- Tables include captions and column scopes.
- Controls use visible focus styles.
- Reduced-motion preferences disable nonessential transitions.
- Hidden navigation never substitutes for backend authorization.

## Loading And Performance

Every page import in `frontend/src/App.jsx` is route-level lazy loaded and
rendered under one `Suspense` loading boundary. Shared components remain in
common chunks. Valid deep links and route aliases must continue to resolve.

## Language

Primary surfaces use travel-agent terms such as Requests, Offers, Trips,
Bookings, Passengers, Documents, and Payments. Words such as metadata,
foundation, diagnostics, canonical entity, migration, and state map belong in
Advanced specialist tools or engineering documentation, not normal task
navigation.
