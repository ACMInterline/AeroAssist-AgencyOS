# Knowledge Import Templates Foundation

Phase 52.2 adds the metadata-only Knowledge Import Templates Foundation.

It creates `knowledge_import_templates` as reusable schemas for future airline knowledge population. Templates define which columns, mappings, validations, sample rows, file types, review requirements, target domains, target collections, and governance links should be used when humans prepare airline knowledge data.

## Scope

- Platform API: `/api/platform/knowledge-import-templates`
- Agency API: `/api/agencies/{agency_id}/knowledge-import-templates`
- Platform UI: `/platform/knowledge-import-templates`
- Agency UI: `/agency/import-templates`
- Collection: `knowledge_import_templates`
- Models: `KnowledgeImportTemplate`, `KnowledgeImportTemplateCreate`, `KnowledgeImportTemplateUpdate`

## Template Types

Supported template types are:

- `airline_manual`
- `operational_bulletin`
- `policy_update`
- `capability_table`
- `pricing_table`
- `service_parameter_table`
- `reference_data_table`
- `evidence_pack`
- `exception_rule_pack`

## Stored Metadata

Each template stores a reference, name, type, version, target knowledge domain, target collections, required columns, optional columns, validation rules, mapping rules, sample rows, accepted file types, import scope, review requirement, governance links, timestamps, and agency scope when applicable.

## Boundaries

Phase 52.2 does not parse files, execute imports, scrape websites, use AI/LLM generation, call provider systems, run background workers, automatically populate airline knowledge, or replace human review.

Templates are preparation metadata only. They make future airline knowledge population more consistent, but final import, review, promotion, and operational authority remain explicitly human-governed.

## Relationships

Knowledge Import Templates support:

- Reference Data Engine domain population
- Service Parameter Taxonomy population
- Visual Policy Editor card preparation
- Pricing Formula Builder preparation
- Operational Rule Composer preparation
- Airline knowledge acquisition and governance review
- Scenario testing and future real airline data population

These relationships are links and schemas only. They do not execute parsing, transformation, validation, promotion, or provider integrations.

Phase 52.4 adds `pricing_formula_builders` for no-code pricing formula metadata. Knowledge Import Templates can describe future pricing-table population schemas that target pricing formula records, but they do not parse files, execute imports, calculate prices, call providers, integrate payments, use AI, run workers, or send automatically to clients.

Phase 52.5 adds `operational_rule_composer_rules` for no-code compound rule metadata. Knowledge Import Templates can describe future exception-rule-pack population schemas that target rule-composer records, but they do not parse files, execute imports, evaluate rules, calculate prices, call providers, use AI, run workers, make automatic decisions, or replace human review.

Phase 52.6 adds `knowledge_quality_assurance_reviews` for metadata-only QA reviews. Knowledge Import Templates can describe future QA population columns, but they do not perform QA execution, auto-approve, publish, call providers, use AI, run workers, or replace human review.
