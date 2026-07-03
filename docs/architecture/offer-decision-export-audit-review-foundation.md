# Offer Decision Export Audit Review Foundation

Phase 38.0 adds a metadata-only audit review layer over the completed offer decision export lifecycle:

decision pack -> explanation -> export -> preview -> release readiness -> manual delivery handoff -> manual delivery outcome.

The layer lets agency users and platform users review completeness, approval trail, handoff trail, outcome trail, unresolved issues, and immutable snapshot coverage. It is not a delivery, booking, pricing, payment, settlement, provider, ticketing, or EMD execution layer.

## Records

| Record | Collection | Purpose |
|---|---|---|
| `OfferDecisionExportAuditReview` | `offer_decision_export_audit_reviews` | Review header, lifecycle source ids, coverage summary, checklist/finding/snapshot counts, and status. |
| `OfferDecisionExportAuditReviewFinding` | `offer_decision_export_audit_review_findings` | Missing metadata, unresolved issue, and snapshot-coverage finding records. |
| `OfferDecisionExportAuditReviewChecklistItem` | `offer_decision_export_audit_review_checklist_items` | Human-review checklist items for lifecycle stages and immutable snapshot coverage. |
| `OfferDecisionExportAuditReviewSnapshot` | `offer_decision_export_audit_review_snapshots` | Immutable metadata snapshot of the review, findings, checklist, source summary, and safety flags. |

Audit review creation reads prior lifecycle metadata and writes only audit review records. It does not mutate decision packs, explanations, exports, previews, approvals, readiness records, handoffs, outcomes, offer options, pricing, bookings, tickets, EMDs, payments, invoices, or provider data.

## Agency Operations

Agency routes live under:

- `/api/agencies/{agency_id}/offer-decision-export-audit-reviews/summary`
- `/api/agencies/{agency_id}/offer-decision-export-audit-reviews/reviews`
- `/api/agencies/{agency_id}/offer-decision-export-audit-reviews/reviews/{review_id}`
- `/api/agencies/{agency_id}/offer-decision-export-audit-reviews/reviews/{review_id}/status`
- `/api/agencies/{agency_id}/offer-decision-export-audit-reviews/reviews/{review_id}/findings`
- `/api/agencies/{agency_id}/offer-decision-export-audit-reviews/findings`
- `/api/agencies/{agency_id}/offer-decision-export-audit-reviews/checklist-items`
- `/api/agencies/{agency_id}/offer-decision-export-audit-reviews/reviews/{review_id}/checklist-items`
- `/api/agencies/{agency_id}/offer-decision-export-audit-reviews/snapshots`
- `/api/agencies/{agency_id}/offer-decision-export-audit-reviews/reviews/{review_id}/snapshots`

The agency UI is `/agency/offer-decision-export-audit-reviews`.

## Platform Diagnostics

Platform routes are read-only and live under:

- `/api/platform/offer-decision-export-audit-reviews/summary`
- `/api/platform/offer-decision-export-audit-reviews/diagnostics`
- `/api/platform/offer-decision-export-audit-reviews/reviews`
- `/api/platform/offer-decision-export-audit-reviews/reviews/{review_id}`
- `/api/platform/offer-decision-export-audit-reviews/findings`
- `/api/platform/offer-decision-export-audit-reviews/checklist-items`
- `/api/platform/offer-decision-export-audit-reviews/snapshots`

The platform UI is `/platform/offer-decision-export-audit-reviews`.

## Safety Boundaries

Phase 38.0 explicitly keeps these capabilities disabled:

- Email or SMS sending.
- Public links or real PDF delivery.
- Offer or price mutation.
- Automatic airline recommendation.
- Provider execution.
- Booking execution or PNR creation/mutation.
- Ticketing or EMD issuance.
- Payment, invoice, accounting, or settlement execution.
- Scraping or external AI calls.
- `/agent`, `/admin`, `/api/agent`, or `/api/admin` route roots.

Readiness exposes `offer_decision_export_audit_review_foundation` with audit review counts, UI flags, metadata-only flags, and execution-disabled flags.
