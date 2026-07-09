import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, SelectField, formatType, optionPair, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
  template_type: "",
  target_knowledge_domain: "",
  target_collection: "",
  import_scope: "",
  review_required: "",
  accepted_file_type: "",
  search: "",
}

const templateTypes = [
  "airline_manual",
  "operational_bulletin",
  "policy_update",
  "capability_table",
  "pricing_table",
  "service_parameter_table",
  "reference_data_table",
  "evidence_pack",
  "exception_rule_pack",
]

const importScopes = ["platform_governed", "agency_scoped", "airline_specific", "scenario_testing", "reference_population"]
const fileTypes = ["csv", "xlsx", "json", "pdf", "txt", "md"]
const reviewOptions = [["true", "Review required"], ["false", "Review optional"]]

export default function KnowledgeImportTemplatesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/knowledge-import-templates${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      items: response.items || response.templates || [],
      summary: response.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.template_type, filters.target_knowledge_domain, filters.target_collection, filters.import_scope, filters.review_required, filters.accepted_file_type, filters.search])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Templates", summary.knowledge_import_template_count ?? items.length],
    ["Types", `${summary.covered_template_type_count || 0}/${summary.supported_template_type_count || templateTypes.length}`],
    ["Required Columns", summary.required_column_count || 0],
    ["Mapping Rules", summary.mapping_rule_count || 0],
    ["Governance Links", summary.governance_link_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence Governance</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Knowledge Import Templates</h2>
              <p className="mt-1 text-sm text-slate-600">Reusable metadata schemas for future airline knowledge population, review, and governance.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No parsing</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Template Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <SelectField label="Type" value={filters.template_type} onChange={(value) => setFilters({ ...filters, template_type: value })} options={templateTypes.map(optionPair)} placeholder="All types" />
              <Field label="Knowledge Domain" value={filters.target_knowledge_domain} onChange={(value) => setFilters({ ...filters, target_knowledge_domain: value })} />
              <Field label="Target Collection" value={filters.target_collection} onChange={(value) => setFilters({ ...filters, target_collection: value })} />
              <SelectField label="Scope" value={filters.import_scope} onChange={(value) => setFilters({ ...filters, import_scope: value })} options={importScopes.map(optionPair)} placeholder="All scopes" />
              <SelectField label="Review" value={filters.review_required} onChange={(value) => setFilters({ ...filters, review_required: value })} options={reviewOptions} placeholder="Any review" />
              <SelectField label="File Type" value={filters.accepted_file_type} onChange={(value) => setFilters({ ...filters, accepted_file_type: value })} options={fileTypes.map(optionPair)} placeholder="Any file" />
              <Field label="Search" value={filters.search} onChange={(value) => setFilters({ ...filters, search: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Templates</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <TemplateList items={items} showAgency /> : <EmptyState title="No knowledge import templates" body="Knowledge Import Template metadata will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function TemplateList({ items, showAgency = false }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_190px_190px]">
              <div>
                <p className="font-semibold text-slate-950">{item.template_display_name || item.template_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.template_reference || item.id}</p>
              </div>
              <div className="text-xs text-slate-600">
                {showAgency ? <p>{item.agency_name || item.agency_id || "Platform governed"}</p> : null}
                <p className="mt-1">Type: {formatType(item.template_type)}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Domain: {formatType(item.target_knowledge_domain)}</p>
                <p className="mt-1">Scope: {formatType(item.import_scope)}</p>
              </div>
            </div>
          </summary>
          <TemplateSections item={item} />
        </details>
      ))}
    </div>
  )
}

function TemplateSections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <RecordCard title="Template Overview" value={item.template_overview_section} />
      <RecordCard title="Columns" value={item.columns_section} />
      <RecordCard title="Validation Rules" value={item.validation_section} />
      <RecordCard title="Mapping Rules" value={item.mapping_section} />
      <RecordCard title="Sample Rows" value={item.sample_rows_section} />
      <RecordCard title="Governance" value={item.governance_section} />
      <RecordCard title="Readiness" value={item.readiness_section} />
      <RecordCard title="Boundaries" value={item.boundary_section} />
    </div>
  )
}
