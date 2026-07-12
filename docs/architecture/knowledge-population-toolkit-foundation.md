# Knowledge Population Toolkit Foundation

Phase 52.9 adds metadata-only Knowledge Population Toolkit records.

This foundation creates an operational toolkit for planning and tracking airline knowledge population at scale. It stores readiness, coverage, progress, gaps, blockers, warnings, and next-action metadata only. It does not scrape airline sources, auto-import files, call providers, use AI, run background workers, or execute population jobs.

## Purpose

Knowledge Population Toolkit records help Platform/Admin users see whether the surrounding Epic 52 knowledge-production surfaces are ready for an airline:

- airline onboarding checklist
- reference readiness
- import template readiness
- policy editor readiness
- pricing builder readiness
- rule composer readiness
- QA readiness
- publishing readiness
- scenario test readiness
- evidence coverage
- population progress
- missing domains
- next actions

Agency users can view read-only toolkit metadata for their agency scope.

## Collection

`knowledge_population_toolkits`

## Models

- `KnowledgePopulationToolkit`
- `KnowledgePopulationToolkitCreate`
- `KnowledgePopulationToolkitUpdate`

## Toolkit Fields

Each toolkit stores:

- `toolkit_reference`
- `airline_code`
- `population_status`
- `airline_onboarding_checklist`
- `reference_readiness`
- `import_template_readiness`
- `policy_editor_readiness`
- `pricing_builder_readiness`
- `rule_composer_readiness`
- `qa_readiness`
- `publishing_readiness`
- `scenario_test_readiness`
- `coverage_summary`
- `service_family_coverage`
- `evidence_coverage`
- `pricing_coverage`
- `capability_coverage`
- `QA_status`
- `publishing_status`
- `scenario_test_status`
- `population_progress`
- `missing_domains`
- `blockers`
- `warnings`
- `next_actions`
- `owner`
- `due_dates`
- `notes`

## Routes

Platform routes:

- `/api/platform/knowledge-population-toolkit`
- `/api/platform/knowledge-population-toolkit/summary`
- `/api/platform/knowledge-population-toolkit/{toolkit_id}`

Agency read-only routes:

- `/api/agencies/{agency_id}/knowledge-population-toolkit`
- `/api/agencies/{agency_id}/knowledge-population-toolkit/summary`
- `/api/agencies/{agency_id}/knowledge-population-toolkit/{toolkit_id}`

Frontend routes:

- `/platform/knowledge-population-toolkit`
- `/agency/knowledge-population-toolkit`

## Explicit Exclusions

Phase 52.9 does not implement scraping, automatic import, parsing execution, provider calls, AI/LLM generation, live evaluation, live pricing calculation, publishing, background workers, schedulers, booking, ticketing, EMD issuance, or automated operational authority.

Human authority remains final.
