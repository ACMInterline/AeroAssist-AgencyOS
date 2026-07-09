import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
  case_status: "",
  overall_case_status: "",
  airline: "",
  passenger_need: "",
  travel_request: "",
  trip_workspace: "",
  ready_for_agent_review: "",
  ready_for_offer_builder: "",
  ready_for_client_presentation: "",
}

const caseStatuses = ["draft", "assembling", "in_review", "ready", "blocked", "archived"]
const overallStatuses = ["ready", "conditional", "blocked", "needs_review", "unknown"]
const booleanOptions = [["true", "Yes"], ["false", "No"]]

export default function OperationalIntelligenceCasesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/operational-intelligence-cases${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      items: response.items || response.cases || [],
      summary: response.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.case_status, filters.overall_case_status, filters.airline, filters.passenger_need, filters.travel_request, filters.trip_workspace, filters.ready_for_agent_review, filters.ready_for_offer_builder, filters.ready_for_client_presentation])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const items = state?.items || []
  const summary = state?.summary || {}
  const linkCounts = summary.pipeline_link_counts || {}
  const metrics = [
    ["Cases", items.length],
    ["Agent review", summary.ready_for_agent_review_count || 0],
    ["Offer builder", summary.ready_for_offer_builder_count || 0],
    ["Client ready", summary.ready_for_client_presentation_count || 0],
    ["Pipeline links", Object.values(linkCounts).reduce((total, value) => total + Number(value || 0), 0)],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operational Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Operational Intelligence Cases</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only case views that consolidate the Chapter 50 chain from passenger requirement through offer-intelligence package. No new intelligence, live search, booking, ticketing, EMD issuance, provider calls, AI generation, workers, or automatic sending.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Pipeline consolidation</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Human authority</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Case Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <SelectField label="Case Status" value={filters.case_status} onChange={(value) => setFilters({ ...filters, case_status: value })} options={caseStatuses.map(optionPair)} placeholder="All statuses" />
              <SelectField label="Overall Status" value={filters.overall_case_status} onChange={(value) => setFilters({ ...filters, overall_case_status: value })} options={overallStatuses.map(optionPair)} placeholder="All outcomes" />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <Field label="Passenger Need" value={filters.passenger_need} onChange={(value) => setFilters({ ...filters, passenger_need: value })} />
              <Field label="Travel Request" value={filters.travel_request} onChange={(value) => setFilters({ ...filters, travel_request: value })} />
              <Field label="Trip Workspace" value={filters.trip_workspace} onChange={(value) => setFilters({ ...filters, trip_workspace: value })} />
              <SelectField label="Agent Review Ready" value={filters.ready_for_agent_review} onChange={(value) => setFilters({ ...filters, ready_for_agent_review: value })} options={booleanOptions} placeholder="Any" />
              <SelectField label="Offer Builder Ready" value={filters.ready_for_offer_builder} onChange={(value) => setFilters({ ...filters, ready_for_offer_builder: value })} options={booleanOptions} placeholder="Any" />
              <SelectField label="Client Presentation Ready" value={filters.ready_for_client_presentation} onChange={(value) => setFilters({ ...filters, ready_for_client_presentation: value })} options={booleanOptions} placeholder="Any" />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Cases</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <CaseList items={items} showAgency /> : <EmptyState title="No operational intelligence cases" body="Consolidated Chapter 50 intelligence case metadata will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function CaseList({ items, showAgency = false }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_190px_190px]">
              <div>
                <p className="font-semibold text-slate-950">{item.case_display_name || item.case_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{(item.recommended_airlines || []).join(", ") || "Airline unset"} - {formatType(item.overall_case_status)} - {formatType(item.case_status)}</p>
              </div>
              <div className="text-xs text-slate-600">
                {showAgency ? <p>{item.agency_name || item.agency_id || "Platform governed"}</p> : null}
                <p className="mt-1">Request: {item.travel_request_id || "Unset"}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Offer builder: {item.ready_for_offer_builder ? "Ready" : "Not ready"}</p>
                <p className="mt-1">Client: {item.ready_for_client_presentation ? "Ready" : "Not ready"}</p>
              </div>
            </div>
          </summary>
          <CaseSections item={item} />
        </details>
      ))}
    </div>
  )
}

function CaseSections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <RecordCard title="Case Overview" value={{ case_reference: item.case_reference, case_status: item.case_status, case_version: item.case_version, created_by: item.created_by, created_at: item.created_at, updated_at: item.updated_at }} />
      <RecordCard title="Passenger / Request" value={{ passenger_workspace_id: item.passenger_workspace_id, travel_request_id: item.travel_request_id, trip_workspace_id: item.trip_workspace_id, passenger_need_summary: item.passenger_need_summary, passenger_requirements: item.passenger_requirements, itinerary_summary: item.itinerary_summary }} />
      <RecordCard title="Pipeline Status" value={{ acquisition_ready: item.acquisition_ready, normalisation_ready: item.normalisation_ready, constraints_ready: item.constraints_ready, governance_ready: item.governance_ready, capability_matrix_ready: item.capability_matrix_ready, evaluation_ready: item.evaluation_ready, feasibility_ready: item.feasibility_ready, recommendation_ready: item.recommendation_ready, offer_intelligence_ready: item.offer_intelligence_ready, pipeline_status_summary: item.pipeline_status_summary }} />
      <RecordCard title="Pipeline Links" value={{ knowledge_acquisition_ids: item.knowledge_acquisition_ids, normalisation_ids: item.normalisation_ids, operational_constraint_ids: item.operational_constraint_ids, knowledge_version_ids: item.knowledge_version_ids, knowledge_release_ids: item.knowledge_release_ids, capability_matrix_ids: item.capability_matrix_ids, operational_evaluation_ids: item.operational_evaluation_ids, feasibility_ids: item.feasibility_ids, recommendation_ids: item.recommendation_ids, intelligent_offer_package_ids: item.intelligent_offer_package_ids, pipeline_link_summary: item.pipeline_link_summary }} />
      <RecordCard title="Decision Summary" value={{ overall_case_status: item.overall_case_status, overall_case_summary: item.overall_case_summary, recommended_airlines: item.recommended_airlines, blocked_airlines: item.blocked_airlines, conditional_airlines: item.conditional_airlines, decision_summary_metadata: item.decision_summary_metadata }} />
      <RecordCard title="Required Actions" value={{ required_actions_summary: item.required_actions_summary }} />
      <RecordCard title="Evidence Trace" value={{ evidence_summary: item.evidence_summary, evidence_trace: item.evidence_trace, decision_trace: item.decision_trace, knowledge_trace: item.knowledge_trace, operational_trace: item.operational_trace, trace_summary: item.trace_summary }} />
      <RecordCard title="Risk / Confidence" value={{ operational_risk_summary: item.operational_risk_summary, confidence_summary: item.confidence_summary }} />
      <RecordCard title="Readiness" value={{ ready_for_agent_review: item.ready_for_agent_review, ready_for_offer_builder: item.ready_for_offer_builder, ready_for_client_presentation: item.ready_for_client_presentation, missing_pipeline_items: item.missing_pipeline_items, blocking_pipeline_items: item.blocking_pipeline_items, readiness_metadata_summary: item.readiness_metadata_summary }} />
      <RecordCard title="Notes" value={{ internal_notes: item.internal_notes, agent_notes: item.agent_notes, metadata: item.metadata }} />
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
      <input className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
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

function formatType(value) {
  return value ? String(value).replaceAll("_", " ") : "Unset"
}
