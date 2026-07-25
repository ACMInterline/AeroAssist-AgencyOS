# Security Stabilization Review

**Status:** focused source and disposable runtime controls pass; this is not a
destructive penetration test.

## Findings

| Boundary | Result | Evidence |
|---|---|---|
| Authentication | Server-issued opaque sessions; active state is rechecked. | auth/security regressions |
| Agency access | Path Agency requires active membership; body/query IDs cannot widen scope. | identity/tenancy and browser cross-tenant tests |
| Portal access | Exact active `PortalAccessMapping`; Client and Passenger projections remain separate. | Portal regression and browser checks 22, 25, 32, 34 |
| Audit access | Global audit route requires approved Platform audit role; Agency audit remains scoped. | P0 audit regression |
| Finance privacy | Supplier cost, margin, and internal notes are absent from Portal projection. | ledger/Portal regressions and browser check 25 |
| Internal collaboration | Internal messages and timeline entries remain excluded from Portal. | collaboration and browser Offer-note checks |
| Document upload | Ownership, requested state, MIME allowlist, extension, size, basename, and byte signature are verified. | Portal projection service and regression |
| Error output | Status-safe messages redact stack, Mongo, collection, and filesystem detail while retaining correlation IDs. | `frontend/src/lib/api.js` |
| Unsafe rendering | No application `dangerouslySetInnerHTML`, `eval`, or `new Function` use was found. | source scan |
| Automation | Allowlisted deterministic actions only; Class D rejected and Class C creates approval work only. | automation contract/regression |
| HTTP | Existing production CORS, headers, throttling, and security configuration remain unchanged. | security smoke/config validation |
| Seeds/migrations | Demo paths stay production-disabled; analyzers remain zero-write. | production config and migration validators |
| Dependencies | Production and full npm audits report zero known vulnerabilities after tooling updates. | `npm audit` |

## Protected Diagnostics

Bounded operational counters and timings remain available through the
Platform-authorized observability endpoint. Public summary readiness contains
capability metadata, not raw logs or telemetry snapshots. Process-local
limitations remain explicit.

## Non-Claims

**Evidence:** no production data or infrastructure was accessed. No active
penetration testing, credential testing, dependency exploit, or external
provider testing was performed.
