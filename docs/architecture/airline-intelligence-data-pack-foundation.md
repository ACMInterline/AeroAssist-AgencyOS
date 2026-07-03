# Airline Intelligence Data Pack Foundation

Phase 39.0 adds a governed staging layer for airline intelligence metadata. Data packs let platform users collect, review, validate, and snapshot airline coverage before any future operational use.

## Purpose

Airline data is useful across many parts of AgencyOS, but it should not flow directly into operational rules or public surfaces without review. Data packs provide a safe holding area for airline profiles, contacts, fleet, routes, fare families, RBD matrices, fare rules, ancillaries, interline/distribution notes, PSS/GDS parameters, exception metadata, brand assets, special-services metadata, CMS display summaries, and future client portal display metadata.

This foundation supports future CRM context, offer-builder guidance, agency website/CMS content planning, client portal display readiness, fare/fleet/route workflows, and special-services review. It does not make any of those areas automatically consume the data yet.

## Core Records

- `AirlineIntelligenceDataPack` records package-level source, airline, verification, display, and safety metadata.
- `AirlineIntelligenceDataPackItem` records staged target-domain payloads and normalized metadata.
- `AirlineIntelligenceDataPackValidationIssue` records deterministic review warnings or errors.
- `AirlineIntelligenceDataPackImportRun` records inline JSON/CSV dry-run metadata.
- `AirlineIntelligenceDataPackReviewNote` records human source, review, agency-display, CMS, client-portal, offer-builder, and verification notes.
- `AirlineIntelligenceCoverageSnapshot` records immutable coverage counts and readiness summaries.

## Review Model

Platform users can create data packs, add staged items, run local dry-run imports, validate staged data, acknowledge validation issues, write review notes, and create coverage snapshots.

Agency users can only view coverage and approved/safe display summaries through `/agency/airline-intelligence-coverage`. They do not edit global packs, payloads, validation rules, or source data. Agency responses hide raw staged payloads so agents see readable coverage and readiness, not maintenance internals.

## Demo Vs Operationally Verified

Demo or sample packs are allowed for development, training, and UI review. They must remain clearly marked and should not be treated as operationally verified.

Operationally verified packs require explicit human review metadata, source references, confidence, and verification status. Phase 39.0 still keeps verified data in the staging layer; it does not promote anything into operational airline tables automatically.

## CRM, CMS, Client Portal, And Offer Builder Alignment

Data packs include explicit flags for:

- `safe_for_agency_internal_crm`
- `safe_for_agency_display`
- `safe_for_cms_display`
- `safe_for_client_portal_later`
- `safe_for_offer_builder`

These flags are planning metadata only. They help future phases decide what can be reviewed for CRM context, agency website/CMS content, client portal display, and offer-builder advisory context. They do not publish content, create public links, recommend airlines, or mutate offers.

## Safety Boundaries

Phase 39.0 is metadata-only. It does not:

- Scrape airline websites.
- Call external airline APIs.
- Call external AI.
- Automatically promote staged data into operational airline tables.
- Recommend airlines.
- Edit offers or prices.
- Publish CMS or client portal content.
- Create public portal links.
- Send email, SMS, notifications, or documents.
- Execute providers, GDS, NDC, booking, PNR mutation, ticketing, EMD issuance, payments, invoices, accounting, or settlement.

## Canonical Routes

Platform governance lives under:

- `/platform/airline-intelligence-data-packs`
- `/api/platform/airline-intelligence-data-packs/*`

Agency read-only coverage lives under:

- `/agency/airline-intelligence-coverage`
- `/api/agencies/{agency_id}/airline-intelligence-data-packs/*`

No `/agent`, `/admin`, `/api/agent`, or `/api/admin` routes are added.
