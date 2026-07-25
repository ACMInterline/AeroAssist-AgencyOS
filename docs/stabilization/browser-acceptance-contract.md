# Browser Acceptance Contract

**Status:** 51/51 checks pass in disposable Chromium.

## Environment

- Playwright is a development-only dependency.
- Backend uses the in-memory adapter and deterministic demo fixtures.
- Frontend and backend bind to loopback ports only.
- Document bytes use a disposable repository-local directory that is removed
  after validation.
- Production is never contacted.
- Screenshots and traces are retained only on failure.

## Contract

The browser test covers:

1. Platform Owner login and overview.
2. Platform Agency list.
3. Agency Owner login and Operations Command Centre.
4. Request V4 creation with an existing Client and Passenger.
5. Reference-driven ADT PTC.
6. Two canonical itinerary segments.
7. Segment-scoped mobility assistance.
8. PETC details and a special item.
9. Request submission and detail projection.
10. Offer Workspace with multiple options, segments, fare bundles, and prices.
11. Explicit release of exact Offer presentation version 1.
12. Client Portal Offer display without internal notes.
13. Safe Portal question with no external delivery.
14. Exact option and fare-brand selection.
15. Exact-version Offer acceptance.
16. Immutable acceptance snapshot and confirmed Trip.
17. Booking readiness handoff.
18. Booking workspace creation without provider execution.
19. Explicit booking-preparation transition.
20. Manual Booking result with source evidence.
21. Ticket and EMD mirrors with issuance controls disabled.
22. Booking linkage to Ticket and EMD.
23. Governed Invoice creation, line calculation, and issue transition.
24. Received Payment and immutable allocation.
25. Client-safe Invoice and Payment projection.
26. Requested Document upload with immutable version.
27. Work Queue and governed automation visibility.
28. Approval-required actions remain non-executory.
29. Shared search keyboard focus and restoration.
30. Read-only Agency mutation rejection.
31. Cross-Agency record rejection.
32. Passenger Portal exact-subject projection.
33. Real Not Found rendering.
34. Revoked Portal mapping rejection.
35. Zero uncaught browser page errors.

The named Playwright test contains 51 granular `test.step` checks across these
contract areas.

## Acceptance Command

```bash
npm run test:e2e --prefix frontend
```

## Evidence

- `frontend/tests/e2e/full-system-acceptance.spec.js`
- `backend/scripts/run_browser_acceptance_server.py`
- `frontend/playwright.config.js`

## Limits

This is browser acceptance, not production acceptance. It does not prove
provider behavior, real email/SMS, payments, issuance, production migration,
production load, Firefox/Safari behavior, or formal accessibility conformance.
