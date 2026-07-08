import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const lifecycleStatuses = ["draft", "under_review", "approved", "published", "effective", "superseded", "archived", "historical_audit"]
const releaseStatuses = ["draft", "under_review", "approved", "published", "effective", "superseded", "archived"]
const reviewStatuses = ["not_started", "under_review", "changes_requested", "reviewed", "rejected"]
const approvalStatuses = ["not_requested", "pending", "approved", "rejected"]
const scopes = ["evidence", "policy", "pricing", "capability", "operational_constraints", "operational_procedures"]

const defaultFilters = {
  agency_id: "",
  lifecycle_status: "",
  release_status: "",
  review_status: "",
  approval_status: "",
  publication_channel: "",
  publication_scope: "",
  knowledge_scope: "",
  airline_code: "",
  country: "",
  service_domain: "",
}

export default function AirlineKnowledgeGovernancePage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/airline-knowledge-governance${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      versions: response.versions || [],
      releases: response.releases || [],
      summary: response.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.lifecycle_status, filters.release_status, filters.review_status, filters.approval_status, filters.publication_channel, filters.publication_scope, filters.knowledge_scope, filters.airline_code, filters.country, filters.service_domain])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const versions = state?.versions || []
  const releases = state?.releases || []
  const summary = state?.summary || {}
  const reviewQueue = versions.filter((item) => item.lifecycle_status === "under_review" || item.review_status === "under_review")
  const approvalQueue = versions.filter((item) => item.approval_status === "pending")
  const publicationQueue = versions.filter((item) => item.lifecycle_status === "approved")
  const historicalVersions = versions.filter((item) => item.lifecycle_status === "historical_audit" || hasItems(item.historical_lookup_tags))
  const comparisonVersions = versions.filter((item) => item.version_comparison && comparisonHasContent(item.version_comparison))
  const supersededVersions = versions.filter((item) => item.lifecycle_status === "superseded" || hasItems(item.supersedes_version_ids))
  const archivedVersions = versions.filter((item) => item.lifecycle_status === "archived")

  const metrics = [
    ["Versions", versions.length],
    ["Releases", releases.length],
    ["Review queue", summary.review_queue_count || reviewQueue.length],
    ["Approval queue", summary.approval_queue_count || approvalQueue.length],
    ["Historical", summary.historical_version_count || historicalVersions.length],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Airline Knowledge Governance</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only lifecycle and version-control visibility for Evidence, Policy, Pricing, Capability, Operational Constraints, Operational Procedures, Knowledge Releases, and historical versions. No live rule evaluation, AI reasoning, parser execution, recommendations, pricing calculation, provider calls, workers, or automatic publication.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Version control</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Governance filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <SelectField label="Version lifecycle" value={filters.lifecycle_status} onChange={(value) => setFilters({ ...filters, lifecycle_status: value })} options={lifecycleStatuses.map(optionPair)} placeholder="All lifecycle" />
              <SelectField label="Release status" value={filters.release_status} onChange={(value) => setFilters({ ...filters, release_status: value })} options={releaseStatuses.map(optionPair)} placeholder="All releases" />
              <SelectField label="Review" value={filters.review_status} onChange={(value) => setFilters({ ...filters, review_status: value })} options={reviewStatuses.map(optionPair)} placeholder="All review" />
              <SelectField label="Approval" value={filters.approval_status} onChange={(value) => setFilters({ ...filters, approval_status: value })} options={approvalStatuses.map(optionPair)} placeholder="All approval" />
              <SelectField label="Knowledge scope" value={filters.knowledge_scope} onChange={(value) => setFilters({ ...filters, knowledge_scope: value })} options={scopes.map(optionPair)} placeholder="All scopes" />
              <Field label="Publication channel" value={filters.publication_channel} onChange={(value) => setFilters({ ...filters, publication_channel: value })} />
              <Field label="Publication scope" value={filters.publication_scope} onChange={(value) => setFilters({ ...filters, publication_scope: value })} />
              <Field label="Airline" value={filters.airline_code} onChange={(value) => setFilters({ ...filters, airline_code: value })} />
              <Field label="Country" value={filters.country} onChange={(value) => setFilters({ ...filters, country: value })} />
              <Field label="Service domain" value={filters.service_domain} onChange={(value) => setFilters({ ...filters, service_domain: value })} />
            </div>
          </section>

          <DashboardSection title="Knowledge Versions" count={versions.length}>
            {versions.length ? <VersionList versions={versions} showAgency /> : <EmptyState title="No knowledge versions" body="Governed airline operational knowledge versions will appear here." />}
          </DashboardSection>
          <DashboardSection title="Knowledge Releases" count={releases.length}>
            {releases.length ? <ReleaseList releases={releases} showAgency /> : <EmptyState title="No knowledge releases" body="Grouped release metadata will appear here." />}
          </DashboardSection>
          <QueueGrid sections={[
            ["Review Queue", reviewQueue],
            ["Approval Queue", approvalQueue],
            ["Publication Queue", publicationQueue],
            ["Historical Versions", historicalVersions],
            ["Version Comparison", comparisonVersions],
            ["Superseded Knowledge", supersededVersions],
            ["Archived Knowledge", archivedVersions],
          ]} />
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function VersionList({ versions, showAgency = false }) {
  return (
    <div className="space-y-3">
      {versions.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_190px_190px]">
              <div>
                <p className="font-semibold text-slate-950">{item.version_display_name || item.knowledge_version_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.semantic_version || "Version unset"} - {formatType(item.change_type)} - {formatList(item.knowledge_scope)}</p>
              </div>
              <div className="text-xs text-slate-600">
                {showAgency ? <p>{item.agency_name || item.agency_id || "Platform governed"}</p> : null}
                <p className="mt-1">Lifecycle: {formatType(item.lifecycle_status)}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Review: {formatType(item.review_status)}</p>
                <p className="mt-1">Approval: {formatType(item.approval_status)}</p>
              </div>
            </div>
          </summary>
          <VersionSections item={item} />
        </details>
      ))}
    </div>
  )
}

function VersionSections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <DetailCard title="Lifecycle" lines={[
        `Reference: ${item.knowledge_version_reference || "Unset"}`,
        `Version number: ${item.version_number ?? "Unset"}`,
        `Semantic version: ${item.semantic_version || "Unset"}`,
        `Status: ${formatType(item.lifecycle_status)}`,
        `Effective: ${formatDateTime(item.effective_from)} -> ${formatDateTime(item.effective_until)}`,
      ]} />
      <DetailCard title="Governance" lines={[
        `Author: ${item.author || "Unset"}`,
        `Reviewer: ${item.reviewer || "Unset"}`,
        `Approver: ${item.approver || "Unset"}`,
        `Publisher: ${item.publisher || "Unset"}`,
        `Publication: ${item.publication_channel || "Unset"} / ${item.publication_scope || "Unset"}`,
      ]} />
      <RecordCard title="Knowledge Scope" value={item.governed_knowledge_summary || {}} />
      <RecordCard title="Reference IDs" value={{
        evidence_ids: item.evidence_ids,
        policy_ids: item.policy_ids,
        pricing_ids: item.pricing_ids,
        capability_ids: item.capability_ids,
        constraint_ids: item.constraint_ids,
        procedure_ids: item.procedure_ids,
      }} />
      <RecordCard title="Version Comparison" value={item.version_comparison || {}} />
      <RecordCard title="Rollback / History" value={{
        previous_version_id: item.previous_version_id,
        supersedes_version_ids: item.supersedes_version_ids,
        replaced_by_version_id: item.replaced_by_version_id,
        rollback_from_version_id: item.rollback_from_version_id,
        rollback_to_version_id: item.rollback_to_version_id,
        rollback_reason: item.rollback_reason,
        historical_lookup_tags: item.historical_lookup_tags,
      }} />
    </div>
  )
}

function ReleaseList({ releases, showAgency = false }) {
  return (
    <div className="space-y-3">
      {releases.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4">
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_190px_190px]">
              <div>
                <p className="font-semibold text-slate-950">{item.release_display_name || item.release_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.release_version || "Release version unset"} - {item.included_version_count || 0} versions</p>
              </div>
              <div className="text-xs text-slate-600">
                {showAgency ? <p>{item.agency_name || item.agency_id || "Platform governed"}</p> : null}
                <p className="mt-1">Status: {formatType(item.release_status)}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Evaluation ready: {item.evaluation_ready ? "Yes" : "No"}</p>
                <p className="mt-1">Recommendation ready: {item.recommendation_ready ? "Yes" : "No"}</p>
              </div>
            </div>
          </summary>
          <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
            <DetailCard title="Release Metadata" lines={[
              `Reference: ${item.release_reference || "Unset"}`,
              `Description: ${item.release_description || "Unset"}`,
              `Approved: ${formatDateTime(item.approved_at)}`,
              `Published: ${formatDateTime(item.published_at)}`,
              `Notes: ${item.release_notes || "Unset"}`,
            ]} />
            <RecordCard title="Applicability" value={{ airline_codes: item.airline_codes, countries: item.countries, service_domains: item.service_domains }} />
            <RecordCard title="Included Versions" value={item.included_version_ids || []} />
            <RecordCard title="Audit" value={{ author: item.release_author, reviewer: item.release_reviewer, approver: item.release_approver, rollback_release_id: item.rollback_release_id, superseded_release_ids: item.superseded_release_ids }} />
          </div>
        </details>
      ))}
    </div>
  )
}

function QueueGrid({ sections }) {
  return (
    <section className="grid gap-3 lg:grid-cols-2">
      {sections.map(([title, items]) => (
        <div key={title} className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between gap-3">
            <h3 className="font-semibold text-slate-950">{title}</h3>
            <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
          </div>
          <div className="mt-3 space-y-2">
            {items.slice(0, 5).map((item) => (
              <div key={`${title}-${item.id}`} className="rounded-md border border-slate-100 bg-slate-50 p-3 text-xs text-slate-600">
                <p className="font-semibold text-slate-800">{item.version_display_name || item.knowledge_version_reference}</p>
                <p className="mt-1">{formatType(item.lifecycle_status)} - {formatType(item.change_type)}</p>
              </div>
            ))}
            {!items.length ? <p className="text-sm text-slate-500">No metadata in this queue.</p> : null}
          </div>
        </div>
      ))}
    </section>
  )
}

function DashboardSection({ title, count, children }) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-slate-950">{title}</h3>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{count}</span>
      </div>
      {children}
    </section>
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

function DetailCard({ title, lines }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <p className="font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <div className="mt-2 space-y-1">
        {lines.map((line) => <p key={line}>{line}</p>)}
      </div>
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

function optionPair(value) {
  return [value, formatType(value)]
}

function queryString(filters) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const query = params.toString()
  return query ? `?${query}` : ""
}

function hasItems(value) {
  return Array.isArray(value) && value.length > 0
}

function comparisonHasContent(value) {
  return Boolean(value?.version_a || value?.version_b || hasItems(value?.added) || hasItems(value?.modified) || hasItems(value?.removed) || hasItems(value?.changed_effective_dates) || hasItems(value?.changed_pricing) || hasItems(value?.changed_capability) || hasItems(value?.changed_operational_constraints) || hasItems(value?.changed_procedures))
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

function formatDateTime(value) {
  if (!value) return "Unset"
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString()
}
