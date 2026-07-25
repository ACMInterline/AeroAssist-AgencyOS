# Accessibility Findings

**Status:** fundamental source and Chromium keyboard checks pass; no formal
WCAG conformance claim is made.

| Severity | Finding | Remediation status | Evidence |
|---|---|---|---|
| High | Critical dialogs did not share focus containment/restoration. | Resolved | `useDialogFocus.js`; browser check 44 |
| High | Unknown paths lacked a literal page-level error heading. | Resolved | `NotFoundPage.jsx` |
| Medium | Portal Invoice detail could crash before loading completed. | Resolved | guarded detail body and application error boundary |
| Medium | Login controls lacked complete browser identity/autocomplete state. | Resolved | named, typed, required controls and live status/error |
| Medium | Some modal surfaces lacked consistent semantic dialog metadata. | Resolved for the five current dialog sources | source validator |
| Low | Financial values were inconsistent between Portal and Agency. | Resolved | fixed two-decimal Portal presentation |
| Review | Formal contrast measurement across all themes. | Open, not a release blocker for source review | independent audit required |
| Review | Screen-reader matrix, 200% zoom, mobile, Safari, and Firefox. | Open | independent/manual audit required |
| Review | Older specialist pages may use page-local field patterns. | Open compatibility debt | Product Page Inventory |

## Accepted Fundamentals

- semantic `main`, banner, navigation, complementary, and heading landmarks;
- skip links and focusable `main-content` targets;
- global visible `:focus-visible` treatment;
- reduced-motion CSS;
- text-bearing status and priority badges;
- loading `role=status` with polite announcement;
- error `role=alert`;
- table captions, scoped headers, and sort state;
- labelled login and critical workflow controls;
- dialog naming, modal semantics, Tab containment, Escape, and restoration;
- responsive disclosure and navigation controls remain keyboard-operable.

## Validation

**Evidence:** `validate_stabilization_accessibility.py` checks all current
dialog sources and critical shared components. Playwright validates initial
focus, Escape dismissal, restoration, and the absence of uncaught page errors.
