# Phase 33.1 — Global Reference Data Governance, Bulk Import, and Agency Suggestion Queue

Phase 33.1 hardens Reference Data as a globally governed AeroAssist/platform-owned subsystem.

## Implemented

- Global approved records remain in `global_reference_records` and are the canonical lookup source for agencies, builders, forms, documents, and future operational modules.
- Agency suggestions are stored in `reference_data_suggestions` with submitting agency/workspace, submitted-by user, domain, suggested values, source context, evidence note, review status, reviewer metadata, and approved record linkage.
- Manual import batches are stored in `reference_import_batches` with file hash, validation counts, insert/update/skip counts, status, and error reports.
- Platform owners/admins can create, update, activate, deactivate, import, and review global reference data.
- Agency users can read active global records and submit suggestions, but cannot create active global records or approve suggestions directly.
- Approval of `new_record` and `missing_domain_value` suggestions promotes or updates a global record.
- Approval of `correction` updates the target global record.
- Approval of `deactivation_request` deactivates the target global record.
- Rejected, archived, or needs-more-information suggestions remain non-global.

## Bulk Import

- Import is manual only through `POST /api/reference/import-batches` or `backend/scripts/import_reference_data_csv.py`.
- CSV columns: `domain`, `code`, `label`, `description`, `aliases`, `sort_order`, `is_active`, `metadata_json`.
- Validation checks supported domain, required columns, row domain, required code/label, duplicate codes within the file, integer sort order, and object-shaped `metadata_json`.
- Import is additive/idempotent: matching `domain + code` rows update existing records; new codes insert records; no destructive deletes run.
- Import batches write audit events for upload, validation, import, or failure.

## Future Policy Governance Preparation

The same governance pattern is reserved for future airline policy learning:

- `agency_policy_overrides` remain agency-local and usable only by that agency.
- `policy_rule_suggestions` will allow agencies to submit local overrides and evidence for platform review.
- `policy_evidence` will preserve source notes/files for reviewer decisions.
- Approved rules can become global policy rules available to all agencies.
- Rejected rules remain local, rejected, or archived and do not affect global behavior.

## Phase 34.1 Relationship

Phase 34.1 applies the same platform-owned governance principle to form fields: AeroAssist owns canonical field definitions and agencies configure only presentation/profile settings. Reference Data remains the source for controlled select lists, while form profiles decide where approved fields appear.

## Phase 34.2 Relationship

Phase 34.2 moves global Reference Data management into the platform owner layer at `/platform/reference`, adds domain metadata and enriched country fields, and preserves `/agency/reference` as a consume-and-suggest surface only. The legacy `POST /api/reference/import-batches` path remains compatible, while the platform console adds enriched country CSV columns and export tooling.

## Known Limits

- No full airline policy engine is implemented.
- No policy suggestion approval workflow is implemented yet.
- No external data provider, automatic web scraping, pricing, offer, GDS/NDC, invoice, or payment module is added.
- No destructive seed/reset or automatic startup import is introduced.
- Public/anonymous routes do not expose internal suggestion queues.

## Validation

- `backend/scripts/smoke_reference_data_governance.py` verifies owner global creation, agency direct-create denial, suggestion submission, owner approval/promotion, rejection non-promotion, safe duplicate import reporting, idempotent import updates, inactive filtering, service catalogue accessibility, and readiness flags.
