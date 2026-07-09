import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaultFilters = {
  recommendation_status: "",
  airline: "",
  recommendation_level: "",
  operational_score: "",
  risk: "",
  passenger_need_category: "",
  cabin: "",
  destination: "",
  travel_date: "",
}

const statuses = ["draft", "in_review", "ready", "archived"]
const levels = ["highly_recommended", "recommended", "acceptable", "use_with_caution", "not_recommended"]

export default function RecommendationsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const response = await apiGet(`/api/agencies/${context.agency.id}/airline-recommendations${query}`)
    setState({ ...context, items: response.items || response.recommendations || [], summary: response.summary || {} })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.recommendation_status, filters.airline, filters.recommendation_level, filters.operational_score, filters.risk, filters.passenger_need_category, filters.cabin, filters.destination, filters.travel_date])

  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Recommendations", items.length],
    ["Ready", summary.recommendation_ready_count || 0],
    ["Comparisons", summary.comparison_matrix_count || 0],
    ["Evidence", summary.recommendation_evidence_count || 0],
    ["Required actions", summary.required_action_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Recommendations</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only advisory recommendation metadata. Recommendation is not feasibility, booking, provider search, live pricing, ticketing, EMD issuance, parser execution, AI generation, or final authority.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Advisory</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Recommendation Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Status" value={filters.recommendation_status} onChange={(value) => setFilters({ ...filters, recommendation_status: value })} options={statuses.map(optionPair)} placeholder="All statuses" />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <SelectField label="Recommendation Level" value={filters.recommendation_level} onChange={(value) => setFilters({ ...filters, recommendation_level: value })} options={levels.map(optionPair)} placeholder="All levels" />
              <Field label="Operational Score" value={filters.operational_score} onChange={(value) => setFilters({ ...filters, operational_score: value })} />
              <Field label="Risk" value={filters.risk} onChange={(value) => setFilters({ ...filters, risk: value })} />
              <Field label="Passenger Need" value={filters.passenger_need_category} onChange={(value) => setFilters({ ...filters, passenger_need_category: value })} />
              <Field label="Cabin" value={filters.cabin} onChange={(value) => setFilters({ ...filters, cabin: value })} />
              <Field label="Destination" value={filters.destination} onChange={(value) => setFilters({ ...filters, destination: value })} />
              <Field label="Travel Date" value={filters.travel_date} onChange={(value) => setFilters({ ...filters, travel_date: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Recommendation Dashboard</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <RecommendationList items={items} /> : <EmptyState title="No recommendations" body="Airline recommendation metadata visible to this agency will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function RecommendationList({ items }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_180px_180px]">
              <div>
                <p className="font-semibold text-slate-950">{item.recommendation_display_name || item.recommendation_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.airline_code || "Airline unset"} - {formatType(item.recommendation_level)} - score {item.recommendation_score ?? "unset"}</p>
              </div>
              <p className="text-xs text-slate-600">Rank: {item.recommendation_rank ?? "Unset"}</p>
              <p className="text-xs text-slate-600">Read-only metadata</p>
            </div>
          </summary>
          <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
            <RecordCard title="Recommendation Cards" value={{ recommendation_reference: item.recommendation_reference, recommendation_status: item.recommendation_status, recommendation_rank: item.recommendation_rank, recommendation_status_value: item.recommendation_status_value, recommendation_level: item.recommendation_level, recommendation_summary: item.recommendation_summary }} />
            <RecordCard title="Passenger Context" value={{ passenger_workspace_id: item.passenger_workspace_id, passenger_profile_reference: item.passenger_profile_reference, passenger_need_summary: item.passenger_need_summary, passenger_need_category: item.passenger_need_category }} />
            <RecordCard title="Trip Context" value={{ travel_request_id: item.travel_request_id, trip_workspace_id: item.trip_workspace_id, itinerary_reference: item.itinerary_reference, itinerary_summary: item.itinerary_summary, origin: item.origin, destination: item.destination, travel_date: item.travel_date, cabin_requested: item.cabin_requested }} />
            <RecordCard title="Airline Context" value={{ airline_code: item.airline_code, airline_name: item.airline_name, validating_carrier: item.validating_carrier, operating_carrier: item.operating_carrier, marketing_carrier: item.marketing_carrier }} />
            <RecordCard title="Input References" value={{ feasibility_ids: item.feasibility_ids, operational_evaluation_ids: item.operational_evaluation_ids, capability_matrix_ids: item.capability_matrix_ids, knowledge_version_ids: item.knowledge_version_ids, evidence_reference_ids: item.evidence_reference_ids, input_reference_summary: item.input_reference_summary }} />
            <RecordCard title="Operational Scores" value={{ operational_feasibility_score: item.operational_feasibility_score, operational_confidence_score: item.operational_confidence_score, operational_risk_score: item.operational_risk_score, passenger_comfort_score: item.passenger_comfort_score, operational_complexity_score: item.operational_complexity_score }} />
            <RecordCard title="Commercial Scores" value={{ ancillary_cost_score: item.ancillary_cost_score, ticket_cost_reference: item.ticket_cost_reference, ancillary_cost_reference: item.ancillary_cost_reference, total_cost_reference: item.total_cost_reference }} />
            <RecordCard title="Recommendation Explanation" value={{ recommendation_reason: item.recommendation_reason, recommendation_strengths: item.recommendation_strengths, recommendation_limitations: item.recommendation_limitations, recommendation_conditions: item.recommendation_conditions }} />
            <RecordCard title="Required Actions" value={{ required_ssrs: item.required_ssrs, required_osis: item.required_osis, required_emds: item.required_emds, required_documents: item.required_documents, required_medif: item.required_medif, required_manual_review: item.required_manual_review, required_station_notification: item.required_station_notification, required_crew_notification: item.required_crew_notification, action_summary: item.action_summary }} />
            <RecordCard title="Comparison Matrix" value={{ compared_airlines: item.compared_airlines, compared_itineraries: item.compared_itineraries, comparison_summary: item.comparison_summary, comparison_notes: item.comparison_notes, comparison_matrix: item.comparison_matrix, comparison_metadata_summary: item.comparison_metadata_summary }} />
            <RecordCard title="Evidence" value={{ recommendation_evidence: item.recommendation_evidence, recommendation_trace: item.recommendation_trace, evidence_summary: item.evidence_summary }} />
            <RecordCard title="Lifecycle" value={{ recommendation_ready: item.recommendation_ready, archived: item.archived, archived_at: item.archived_at, created_at: item.created_at, updated_at: item.updated_at }} />
            <RecordCard title="Notes" value={{ internal_notes: item.internal_notes }} />
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
