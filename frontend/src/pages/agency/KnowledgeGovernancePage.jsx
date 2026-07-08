import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const lifecycleStatuses = ["draft", "under_review", "approved", "published", "effective", "superseded", "archived", "historical_audit"]
const releaseStatuses = ["draft", "under_review", "approved", "published", "effective", "superseded", "archived"]
const scopes = ["evidence", "policy", "pricing", "capability", "operational_constraints", "operational_procedures"]

const defaultFilters = {
  lifecycle_status: "",
  release_status: "",
  knowledge_scope: "",
  airline_code: "",
  country: "",
  service_domain: "",
}

export default function KnowledgeGovernancePage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const response = await apiGet(`/api/agencies/${context.agency.id}/airline-knowledge-governance${query}`)
    setState({ ...context, versions: response.versions || [], releases: response.releases || [], summary: response.summary || {} })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.lifecycle_status, filters.release_status, filters.knowledge_scope, filters.airline_code, filters.country, filters.service_domain])

  const versions = state?.versions || []
  const releases = state?.releases || []
  const summary = state?.summary || {}
  const metrics = [
    ["Versions", versions.length],
    ["Releases", releases.length],
    ["Review queue", summary.review_queue_count || 0],
    ["Approval queue", summary.approval_queue_count || 0],
    ["Historical", summary.historical_version_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Knowledge Governance</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only lifecycle, release, comparison, rollback, superseded, archived, and historical metadata for airline operational knowledge. It does not evaluate rules, reason with AI, execute parsers, recommend, calculate pricing, call providers, run workers, or automatically publish.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Governance filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-3">
              <SelectField label="Version lifecycle" value={filters.lifecycle_status} onChange={(value) => setFilters({ ...filters, lifecycle_status: value })} options={lifecycleStatuses.map(optionPair)} placeholder="All lifecycle" />
              <SelectField label="Release status" value={filters.release_status} onChange={(value) => setFilters({ ...filters, release_status: value })} options={releaseStatuses.map(optionPair)} placeholder="All releases" />
              <SelectField label="Knowledge scope" value={filters.knowledge_scope} onChange={(value) => setFilters({ ...filters, knowledge_scope: value })} options={scopes.map(optionPair)} placeholder="All scopes" />
              <Field label="Airline" value={filters.airline_code} onChange={(value) => setFilters({ ...filters, airline_code: value })} />
              <Field label="Country" value={filters.country} onChange={(value) => setFilters({ ...filters, country: value })} />
              <Field label="Service domain" value={filters.service_domain} onChange={(value) => setFilters({ ...filters, service_domain: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <h3 className="text-lg font-semibold text-slate-950">Knowledge Versions</h3>
            {versions.length ? <VersionList versions={versions} /> : <EmptyState title="No knowledge versions" body="Governed airline operational knowledge versions visible to this agency will appear here." />}
          </section>

          <section className="space-y-3">
            <h3 className="text-lg font-semibold text-slate-950">Knowledge Releases</h3>
            {releases.length ? <ReleaseList releases={releases} /> : <EmptyState title="No knowledge releases" body="Read-only release metadata visible to this agency will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function VersionList({ versions }) {
  return (
    <div className="space-y-3">
      {versions.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_180px_180px]">
              <div>
                <p className="font-semibold text-slate-950">{item.version_display_name || item.knowledge_version_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.semantic_version || "Version unset"} - {formatList(item.knowledge_scope)}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Lifecycle: {formatType(item.lifecycle_status)}</p>
                <p className="mt-1">Review: {formatType(item.review_status)}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Approval: {formatType(item.approval_status)}</p>
                <p className="mt-1">Read-only metadata</p>
              </div>
            </div>
          </summary>
          <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
            <RecordCard title="Reference IDs" value={{ evidence_ids: item.evidence_ids, policy_ids: item.policy_ids, pricing_ids: item.pricing_ids, capability_ids: item.capability_ids, constraint_ids: item.constraint_ids, procedure_ids: item.procedure_ids }} />
            <RecordCard title="Version Comparison" value={item.version_comparison || {}} />
            <RecordCard title="Rollback / History" value={{ previous_version_id: item.previous_version_id, supersedes_version_ids: item.supersedes_version_ids, replaced_by_version_id: item.replaced_by_version_id, rollback_to_version_id: item.rollback_to_version_id, historical_lookup_tags: item.historical_lookup_tags }} />
            <RecordCard title="Governance" value={{ author: item.author, reviewer: item.reviewer, approver: item.approver, publisher: item.publisher, publication_channel: item.publication_channel, publication_scope: item.publication_scope }} />
          </div>
        </details>
      ))}
    </div>
  )
}

function ReleaseList({ releases }) {
  return (
    <div className="space-y-3">
      {releases.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4">
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_180px_180px]">
              <div>
                <p className="font-semibold text-slate-950">{item.release_display_name || item.release_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.release_version || "Release version unset"} - {item.included_version_count || 0} versions</p>
              </div>
              <p className="text-xs text-slate-600">Status: {formatType(item.release_status)}</p>
              <p className="text-xs text-slate-600">Read-only metadata</p>
            </div>
          </summary>
          <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
            <RecordCard title="Applicability" value={{ airline_codes: item.airline_codes, countries: item.countries, service_domains: item.service_domains }} />
            <RecordCard title="Included Versions" value={item.included_version_ids || []} />
            <RecordCard title="Audit" value={{ author: item.release_author, reviewer: item.release_reviewer, approver: item.release_approver }} />
            <RecordCard title="Future AOIE" value={{ evaluation_ready: item.evaluation_ready, recommendation_ready: item.recommendation_ready }} />
          </div>
        </details>
      ))}
    </div>
  )
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function RecordCard({ title, value }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <p className="font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <pre className="mt-2 max-h-56 overflow-auto whitespace-pre-wrap rounded-md bg-white p-3 text-xs leading-5 text-slate-600">{hasContent(value) ? JSON.stringify(value, null, 2) : "No metadata recorded."}</pre>
    </div>
  )
}

function Field({ label, value, onChange }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input type="text" className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function SelectField({ label, value, onChange, options, placeholder }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <select className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">{placeholder}</option>
        {options.map(([optionValue, labelText]) => <option value={optionValue} key={optionValue}>{labelText}</option>)}
      </select>
    </label>
  )
}

function queryString(filters) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const query = params.toString()
  return query ? `?${query}` : ""
}

function optionPair(value) {
  return [value, formatType(value)]
}

function hasContent(value) {
  if (!value) return false
  if (Array.isArray(value)) return value.length > 0
  if (typeof value === "object") return Object.values(value).some((item) => hasContent(item) || (item !== null && item !== undefined && item !== ""))
  return true
}

function formatList(values) {
  return Array.isArray(values) && values.length ? values.join(", ") : "None"
}

function formatType(value) {
  return value ? String(value).replaceAll("_", " ") : "Unset"
}
