import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
  feasibility_status: "",
  feasibility_type: "",
  airline: "",
  feasibility_outcome: "",
  confidence_level: "",
  operational_risk: "",
  passenger_need_category: "",
  ssr_code: "",
  travel_date: "",
  cabin: "",
  destination: "",
  recommendation_ready: "",
}

const statuses = ["draft", "in_review", "completed", "blocked", "archived"]
const outcomes = ["fully_feasible", "conditionally_feasible", "operational_review_required", "operationally_blocked", "unknown"]
const confidences = ["official", "high", "medium", "low", "unknown"]
const risks = ["low", "medium", "high", "critical", "unknown"]

export default function PassengerServiceFeasibilityPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/passenger-service-feasibility${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      items: response.items || response.feasibilities || [],
      summary: response.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.feasibility_status, filters.feasibility_type, filters.airline, filters.feasibility_outcome, filters.confidence_level, filters.operational_risk, filters.passenger_need_category, filters.ssr_code, filters.travel_date, filters.cabin, filters.destination, filters.recommendation_ready])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Feasibilities", items.length],
    ["Evidence traces", summary.evidence_trace_count || 0],
    ["Evaluation traces", summary.evaluation_trace_count || 0],
    ["Required actions", summary.required_action_count || 0],
    ["Recommendation ready", summary.recommendation_ready_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Passenger Service Feasibility</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only advisory feasibility records. Feasibility is not Boolean, not recommendation, and human authority remains final. This page does not rank airlines, search flights, book, ticket, use AI or LLM prompts, call providers, execute parsers, optimise pricing, or run workers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Advisory</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata CRUD API</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Feasibility filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <SelectField label="Status" value={filters.feasibility_status} onChange={(value) => setFilters({ ...filters, feasibility_status: value })} options={statuses.map(optionPair)} placeholder="All statuses" />
              <Field label="Feasibility type" value={filters.feasibility_type} onChange={(value) => setFilters({ ...filters, feasibility_type: value })} />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <SelectField label="Outcome" value={filters.feasibility_outcome} onChange={(value) => setFilters({ ...filters, feasibility_outcome: value })} options={outcomes.map(optionPair)} placeholder="All outcomes" />
              <SelectField label="Confidence" value={filters.confidence_level} onChange={(value) => setFilters({ ...filters, confidence_level: value })} options={confidences.map(optionPair)} placeholder="All confidence" />
              <SelectField label="Risk" value={filters.operational_risk} onChange={(value) => setFilters({ ...filters, operational_risk: value })} options={risks.map(optionPair)} placeholder="All risk" />
              <Field label="Passenger need category" value={filters.passenger_need_category} onChange={(value) => setFilters({ ...filters, passenger_need_category: value })} />
              <Field label="SSR code" value={filters.ssr_code} onChange={(value) => setFilters({ ...filters, ssr_code: value })} />
              <Field label="Travel date" value={filters.travel_date} onChange={(value) => setFilters({ ...filters, travel_date: value })} />
              <Field label="Cabin" value={filters.cabin} onChange={(value) => setFilters({ ...filters, cabin: value })} />
              <Field label="Destination" value={filters.destination} onChange={(value) => setFilters({ ...filters, destination: value })} />
              <SelectField label="Recommendation ready" value={filters.recommendation_ready} onChange={(value) => setFilters({ ...filters, recommendation_ready: value })} options={[["true", "Ready"], ["false", "Not ready"]]} placeholder="All readiness" />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Feasibility Records</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <FeasibilityList items={items} showAgency /> : <EmptyState title="No passenger service feasibilities" body="Passenger service feasibility metadata will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function FeasibilityList({ items, showAgency = false }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_190px_190px]">
              <div>
                <p className="font-semibold text-slate-950">{item.feasibility_display_name || item.feasibility_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.airline_code || "Airline unset"} - {formatType(item.feasibility_outcome)} - {formatType(item.feasibility_confidence)}</p>
              </div>
              <div className="text-xs text-slate-600">
                {showAgency ? <p>{item.agency_name || item.agency_id || "Platform governed"}</p> : null}
                <p className="mt-1">Status: {formatType(item.feasibility_status)}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Risk: {formatType(item.operational_risk_level)}</p>
                <p className="mt-1">Recommendation ready: {item.recommendation_ready ? "Yes" : "No"}</p>
              </div>
            </div>
          </summary>
          <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
            <RecordCard title="Feasibility Overview" value={{ feasibility_reference: item.feasibility_reference, feasibility_status: item.feasibility_status, feasibility_type: item.feasibility_type, feasibility_version: item.feasibility_version }} />
            <RecordCard title="Passenger Context" value={{ passenger_workspace_id: item.passenger_workspace_id, passenger_profile_reference: item.passenger_profile_reference, passenger_need_summary: item.passenger_need_summary, passenger_need_category: item.passenger_need_category, passenger_type: item.passenger_type, passenger_age: item.passenger_age, passenger_requirements: item.passenger_requirements }} />
            <RecordCard title="Trip / Itinerary Context" value={{ travel_request_id: item.travel_request_id, trip_workspace_id: item.trip_workspace_id, flight_workspace_ids: item.flight_workspace_ids, booking_workspace_id: item.booking_workspace_id, itinerary_summary: item.itinerary_summary, origin: item.origin, destination: item.destination, transit_points: item.transit_points, travel_date: item.travel_date, cabin_requested: item.cabin_requested }} />
            <RecordCard title="Airline Context" value={{ airline_code: item.airline_code, airline_name: item.airline_name, validating_carrier: item.validating_carrier, operating_carrier: item.operating_carrier, marketing_carrier: item.marketing_carrier }} />
            <RecordCard title="Evaluation Links" value={{ operational_evaluation_ids: item.operational_evaluation_ids, capability_matrix_ids: item.capability_matrix_ids, knowledge_version_ids: item.knowledge_version_ids, constraint_ids: item.constraint_ids, evidence_reference_ids: item.evidence_reference_ids, evaluation_link_summary: item.evaluation_link_summary }} />
            <RecordCard title="Feasibility Result" value={{ feasibility_outcome: item.feasibility_outcome, feasibility_confidence: item.feasibility_confidence, feasibility_summary: item.feasibility_summary, feasibility_reason: item.feasibility_reason, feasibility_blocking_reasons: item.feasibility_blocking_reasons, feasibility_warning_reasons: item.feasibility_warning_reasons, feasibility_conditions: item.feasibility_conditions }} />
            <RecordCard title="Satisfied / Conditional / Unsatisfied / Unknown Requirements" value={{ satisfied_requirements: item.satisfied_requirements, conditionally_satisfied_requirements: item.conditionally_satisfied_requirements, unsatisfied_requirements: item.unsatisfied_requirements, unknown_requirements: item.unknown_requirements, requirement_summary: item.requirement_summary }} />
            <RecordCard title="Required Actions" value={{ required_ssrs: item.required_ssrs, required_osis: item.required_osis, required_emds: item.required_emds, required_documents: item.required_documents, required_medif: item.required_medif, required_airline_approval: item.required_airline_approval, required_station_notification: item.required_station_notification, required_crew_notification: item.required_crew_notification, required_manual_review: item.required_manual_review, required_follow_up_tasks: item.required_follow_up_tasks, action_summary: item.action_summary }} />
            <RecordCard title="Operational Risk" value={{ operational_risk_level: item.operational_risk_level, operational_risk_summary: item.operational_risk_summary, operational_risk_reasons: item.operational_risk_reasons, adm_risk_relevance: item.adm_risk_relevance, disruption_risk_relevance: item.disruption_risk_relevance, service_failure_risk_relevance: item.service_failure_risk_relevance, risk_summary: item.risk_summary }} />
            <RecordCard title="Evidence Trace" value={{ evidence_trace: item.evidence_trace, evaluation_trace: item.evaluation_trace, decision_trace: item.decision_trace }} />
            <RecordCard title="Confidence" value={{ data_confidence_level: item.data_confidence_level, evidence_confidence_level: item.evidence_confidence_level, operational_validation_confidence: item.operational_validation_confidence, confidence_reason: item.confidence_reason, confidence_summary: item.confidence_summary }} />
            <RecordCard title="Lifecycle" value={{ feasibility_ready: item.feasibility_ready, recommendation_ready: item.recommendation_ready, archived: item.archived, archived_at: item.archived_at, created_at: item.created_at, updated_at: item.updated_at }} />
            <RecordCard title="Notes" value={{ internal_notes: item.internal_notes, agent_notes: item.agent_notes }} />
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
