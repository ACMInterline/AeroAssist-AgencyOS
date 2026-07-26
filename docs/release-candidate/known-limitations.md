# Product Recovery Known Limitations

These warnings do not change canonical ownership or weaken a release gate.
Human reviewers decide whether each is acceptable for the intended pilot.

| Area | Current limitation | Control |
|---|---|---|
| Cross-browser | Deterministic browser acceptance is configured for Chromium only; Firefox and WebKit are not installed/configured | do not claim those browsers passed; add a reviewed matrix before broad browser support claims |
| Accessibility | Source checks and one critical keyboard-dialog path pass, but no formal WCAG conformance audit exists | retain independent keyboard, screen-reader, contrast, zoom, and browser review |
| Capacity | No production-scale load, mobile throttling, production RUM, or long-session memory test was run | use disposable synthetic load and production telemetry after separate approval |
| Compatibility | Ownership registry retains 21 migration-required and 3 decision-required domains | preserve compatibility data and complete domain-by-domain reviewed reconciliation |
| Persistence | 254 zero-argument governed `find_many` calls remain | adapter keeps them bounded and deterministically controlled; reduce the legacy ceiling incrementally |
| Product surface | 311 governed pages and seven orphan compatibility pages remain | use the page inventory and retirement register; do not delete without evidence |
| Automation | Persistent scheduler and external execution remain disabled | continue explicit bounded processing; Class C approval only and Class D prohibited |
| Providers | Airline, GDS/NDC, ticket/EMD issuance, payment/refund, and external communications are not enabled | treat records as operational evidence/planning until separately authorized |
| Hosted evidence | The first exact-commit tooling revision used the runner context in job-level environment mappings, causing planning failures with no jobs or logs | require a repaired tooling revision, zero-error `actionlint`, step-initialized runner paths, the approved application SHA, and a verified two-commit lineage artifact |
| Release identity | The application merge is `de22b70c1ccdabf7bd6d28765addf63f79dd189d`; the later workflow and deployment-tooling commits are intentionally distinct | never substitute a tooling SHA or branch tip for application evidence |
| Deployment | Current script intentionally remains pinned to the last approved Phase 58 application release | update only after the validated Product Recovery merge SHA exists |
| Production gate | Backup, off-host copy, restore rehearsal, production validation, and human sign-off are not completed by this review | Phase 57 must remain blocked until real reviewed evidence is persisted |

No warning authorizes a migration, provider call, payment, issuance, message,
deployment, restore, or production-data change.
