# Release-Candidate Gap Register

**Status:** no known Product Kernel blocker after local browser and complete
smoke-inventory validation; human review remains the approval gate.

| Priority | Gap | Release effect | Required evidence or remediation |
|---|---|---|---|
| Warning | Formal accessibility conformance not audited | Do not claim WCAG conformance | independent keyboard, screen-reader, contrast, zoom, and browser matrix |
| Warning | Browser automation currently Chromium desktop | Cross-browser behavior not proven | add reviewed Firefox/WebKit matrix when CI/runtime support is approved |
| Warning | No production-like load profile | Capacity and tail latency are not proven | disposable load test with production-scale synthetic volumes |
| Warning | Large retained product surface | Maintenance and total-download complexity remain | governed route/catalogue decomposition without changing ownership |
| Warning | Ownership registry retains 21 migration-required and 3 decision-required domains | Do not claim complete Product Kernel migration | domain-by-domain reviewed reconciliation and ownership decisions |
| Warning | Compatibility writers and seven orphan pages remain | Migration/maintenance debt; not active primary truth | meet retirement-register evidence |
| Warning | No live provider paths are tested | Intentional safety boundary | separate authorized provider integration program |
| Warning | Persistent scheduler remains disabled | Automation is manual/bounded | deployment-safe single-processor design before enabling |

## Resolved During Stabilization

- initial eager JavaScript target;
- unknown route behavior;
- render error containment;
- critical dialog focus behavior;
- Request mobility serialization;
- Work Queue source filtering;
- Portal upload byte-signature validation;
- Portal Invoice loading and financial formatting;
- development dependency advisories.
- complete registered smoke inventory: 171/171;
- generated Python, Playwright, and frontend build artifacts removed.

## Evidence

This register is paired with the full-system report, browser contract,
accessibility findings, security review, performance report, compatibility
register, focused regressions, and complete smoke inventory.
