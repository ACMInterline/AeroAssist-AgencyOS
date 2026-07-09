import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, SelectField, formatType, optionPair, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaultFilters = {
  target_type: "",
  airline_code: "",
  service_family: "",
  service_code: "",
  qa_status: "",
  severity: "",
  issue_check: "",
  approval_recommendation: "",
  search: "",
}

const targetTypes = ["knowledge_acquisition", "reference_data_domain", "knowledge_import_template", "visual_policy_card", "pricing_formula", "operational_rule", "service_parameter_taxonomy", "capability_matrix", "operational_evaluation", "passenger_service_feasibility", "airline_recommendation", "offer_intelligence_package", "operational_intelligence_case"]
const qaStatuses = ["open", "in_review", "changes_requested", "recommended_for_approval", "blocked", "resolved", "archived"]
const severities = ["info", "low", "medium", "high", "critical", "blocking"]
const checks = ["missing_evidence", "missing_effective_dates", "missing_pricing_applicability", "conflicting_support_status", "incomplete_service_parameters", "missing_documents", "unsupported_reference_values", "stale_review", "low_confidence", "operational_validation_pending", "duplicate_policy_card", "conflicting_rule", "incomplete_pricing_formula"]
const recommendations = ["no_recommendation", "ready_for_human_approval", "approve_after_changes", "hold", "reject"]

export default function KnowledgeQualityAssurancePage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const response = await apiGet(`/api/agencies/${context.agency.id}/knowledge-quality-assurance${query}`)
    setState({ ...context, items: response.items || response.reviews || [], summary: response.summary || {} })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.target_type, filters.airline_code, filters.service_family, filters.service_code, filters.qa_status, filters.severity, filters.issue_check, filters.approval_recommendation, filters.search])

  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Reviews", summary.knowledge_quality_assurance_review_count ?? items.length],
    ["Issues", summary.issue_count || 0],
    ["Changes", summary.requested_change_count || 0],
    ["Governance", summary.governance_link_count || 0],
    ["Checks", summary.supported_check_count || checks.length],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Knowledge QA</h2>
              <p className="mt-1 text-sm text-slate-600">Agency QA review metadata for airline knowledge production.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Human authority</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">QA Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Target Type" value={filters.target_type} onChange={(value) => setFilters({ ...filters, target_type: value })} options={targetTypes.map(optionPair)} placeholder="All targets" />
              <Field label="Airline" value={filters.airline_code} onChange={(value) => setFilters({ ...filters, airline_code: value })} />
              <Field label="Service Family" value={filters.service_family} onChange={(value) => setFilters({ ...filters, service_family: value })} />
              <Field label="Service Code" value={filters.service_code} onChange={(value) => setFilters({ ...filters, service_code: value })} />
              <SelectField label="QA Status" value={filters.qa_status} onChange={(value) => setFilters({ ...filters, qa_status: value })} options={qaStatuses.map(optionPair)} placeholder="All statuses" />
              <SelectField label="Severity" value={filters.severity} onChange={(value) => setFilters({ ...filters, severity: value })} options={severities.map(optionPair)} placeholder="All severities" />
              <SelectField label="Check" value={filters.issue_check} onChange={(value) => setFilters({ ...filters, issue_check: value })} options={checks.map(optionPair)} placeholder="All checks" />
              <SelectField label="Recommendation" value={filters.approval_recommendation} onChange={(value) => setFilters({ ...filters, approval_recommendation: value })} options={recommendations.map(optionPair)} placeholder="Any recommendation" />
              <Field label="Search" value={filters.search} onChange={(value) => setFilters({ ...filters, search: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">QA Reviews</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <ReviewList items={items} /> : <EmptyState title="No QA reviews" body="Knowledge QA metadata for this agency will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function ReviewList({ items }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_190px_190px]">
              <div>
                <p className="font-semibold text-slate-950">{item.review_display_name || item.review_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.review_reference || item.id}</p>
              </div>
              <p className="text-xs text-slate-600">Target: {formatType(item.target_type)}</p>
              <div className="text-xs text-slate-600">
                <p>Status: {formatType(item.qa_status)}</p>
                <p className="mt-1">Severity: {formatType(item.severity)}</p>
              </div>
            </div>
          </summary>
          <ReviewSections item={item} />
        </details>
      ))}
    </div>
  )
}

function ReviewSections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <RecordCard title="Overview" value={item.overview_section} />
      <RecordCard title="Issues" value={item.issues_section} />
      <RecordCard title="Requested Changes" value={item.requested_changes_section} />
      <RecordCard title="Reviewer / Recommendation" value={item.reviewer_section} />
      <RecordCard title="Governance" value={item.governance_section} />
      <RecordCard title="Lifecycle" value={item.lifecycle_section} />
      <RecordCard title="Boundaries" value={item.boundary_section} />
    </div>
  )
}
