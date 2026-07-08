import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaultFilters = {
  evaluation_status: "",
  evaluation_type: "",
  airline: "",
  passenger: "",
  service_domain: "",
  service_family: "",
  ssr_code: "",
  capability_result: "",
  policy_result: "",
  pricing_result: "",
  constraint_result: "",
  operational_result: "",
  operational_risk: "",
  confidence: "",
  evaluation_completed: "",
}

const statuses = ["draft", "in_review", "completed", "blocked", "archived"]
const resultValues = ["pass", "fail", "warning", "manual_review", "not_applicable", "unknown"]
const operationalResults = ["applies", "does_not_apply", "conditional", "blocked", "manual_review", "unknown"]
const risks = ["low", "medium", "high", "critical", "unknown"]
const confidences = ["official", "high", "medium", "low", "unknown"]

export default function OperationalEvaluationsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const response = await apiGet(`/api/agencies/${context.agency.id}/operational-evaluations${query}`)
    setState({ ...context, items: response.items || response.evaluations || [], summary: response.summary || {} })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.evaluation_status, filters.evaluation_type, filters.airline, filters.passenger, filters.service_domain, filters.service_family, filters.ssr_code, filters.capability_result, filters.policy_result, filters.pricing_result, filters.constraint_result, filters.operational_result, filters.operational_risk, filters.confidence, filters.evaluation_completed])

  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Evaluations", items.length],
    ["Completed", summary.completed_count || 0],
    ["Evidence traces", summary.evidence_trace_count || 0],
    ["Source refs", summary.source_reference_count || 0],
    ["Required actions", summary.required_action_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Operational Evaluations</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only operational knowledge evaluation metadata. Evaluation is not recommendation and does not determine passenger feasibility, use AI or LLM prompts, search flights, book, ticket, call providers, execute parsers, optimise pricing, or run workers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Evidence trace</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Evaluation filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Status" value={filters.evaluation_status} onChange={(value) => setFilters({ ...filters, evaluation_status: value })} options={statuses.map(optionPair)} placeholder="All statuses" />
              <Field label="Evaluation type" value={filters.evaluation_type} onChange={(value) => setFilters({ ...filters, evaluation_type: value })} />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <Field label="Passenger" value={filters.passenger} onChange={(value) => setFilters({ ...filters, passenger: value })} />
              <Field label="Service domain" value={filters.service_domain} onChange={(value) => setFilters({ ...filters, service_domain: value })} />
              <Field label="Service family" value={filters.service_family} onChange={(value) => setFilters({ ...filters, service_family: value })} />
              <Field label="SSR code" value={filters.ssr_code} onChange={(value) => setFilters({ ...filters, ssr_code: value })} />
              <SelectField label="Capability result" value={filters.capability_result} onChange={(value) => setFilters({ ...filters, capability_result: value })} options={resultValues.map(optionPair)} placeholder="All capability" />
              <SelectField label="Policy result" value={filters.policy_result} onChange={(value) => setFilters({ ...filters, policy_result: value })} options={resultValues.map(optionPair)} placeholder="All policy" />
              <SelectField label="Pricing result" value={filters.pricing_result} onChange={(value) => setFilters({ ...filters, pricing_result: value })} options={resultValues.map(optionPair)} placeholder="All pricing" />
              <SelectField label="Constraint result" value={filters.constraint_result} onChange={(value) => setFilters({ ...filters, constraint_result: value })} options={resultValues.map(optionPair)} placeholder="All constraint" />
              <SelectField label="Operational result" value={filters.operational_result} onChange={(value) => setFilters({ ...filters, operational_result: value })} options={operationalResults.map(optionPair)} placeholder="All outcomes" />
              <SelectField label="Operational risk" value={filters.operational_risk} onChange={(value) => setFilters({ ...filters, operational_risk: value })} options={risks.map(optionPair)} placeholder="All risk" />
              <SelectField label="Confidence" value={filters.confidence} onChange={(value) => setFilters({ ...filters, confidence: value })} options={confidences.map(optionPair)} placeholder="All confidence" />
              <SelectField label="Completed" value={filters.evaluation_completed} onChange={(value) => setFilters({ ...filters, evaluation_completed: value })} options={[["true", "Completed"], ["false", "Not completed"]]} placeholder="All completion" />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Evaluation Records</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <EvaluationList items={items} /> : <EmptyState title="No operational evaluations" body="Operational knowledge evaluation metadata visible to this agency will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function EvaluationList({ items }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_180px_180px]">
              <div>
                <p className="font-semibold text-slate-950">{item.evaluation_display_name || item.evaluation_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.airline_code || "Airline unset"} - {formatType(item.operational_result)} - {formatType(item.evaluation_confidence)}</p>
              </div>
              <p className="text-xs text-slate-600">Status: {formatType(item.evaluation_status)}</p>
              <p className="text-xs text-slate-600">Read-only metadata</p>
            </div>
          </summary>
          <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
            <RecordCard title="Evaluation Overview" value={{ evaluation_reference: item.evaluation_reference, evaluation_status: item.evaluation_status, evaluation_type: item.evaluation_type, evaluation_version: item.evaluation_version, evaluation_completed: item.evaluation_completed, evaluation_confidence: item.evaluation_confidence, evaluation_reasoning_available: item.evaluation_reasoning_available }} />
            <RecordCard title="Passenger Context" value={{ passenger_workspace_id: item.passenger_workspace_id, passenger_profile_reference: item.passenger_profile_reference, passenger_need_summary: item.passenger_need_summary }} />
            <RecordCard title="Trip Context" value={{ travel_request_id: item.travel_request_id, trip_workspace_id: item.trip_workspace_id, booking_workspace_id: item.booking_workspace_id }} />
            <RecordCard title="Airline Context" value={{ airline_code: item.airline_code, validating_carrier: item.validating_carrier, operating_carrier: item.operating_carrier, marketing_carrier: item.marketing_carrier }} />
            <RecordCard title="Knowledge Sources" value={{ knowledge_version_ids: item.knowledge_version_ids, capability_matrix_ids: item.capability_matrix_ids, operational_constraint_ids: item.operational_constraint_ids, acquisition_ids: item.acquisition_ids, evidence_reference_ids: item.evidence_reference_ids, source_summary: item.source_summary }} />
            <RecordCard title="Evaluation Scope" value={{ evaluated_service_domains: item.evaluated_service_domains, evaluated_service_families: item.evaluated_service_families, evaluated_ssrs: item.evaluated_ssrs, evaluated_osis: item.evaluated_osis, evaluated_emd_requirements: item.evaluated_emd_requirements, scope_summary: item.scope_summary }} />
            <RecordCard title="Capability Evaluation" value={{ capability_result: item.capability_result, capability_reason: item.capability_reason, capability_evidence: item.capability_evidence }} />
            <RecordCard title="Policy Evaluation" value={{ policy_result: item.policy_result, policy_reason: item.policy_reason, policy_evidence: item.policy_evidence }} />
            <RecordCard title="Pricing Evaluation" value={{ pricing_result: item.pricing_result, pricing_reason: item.pricing_reason, pricing_reference: item.pricing_reference }} />
            <RecordCard title="Constraint Evaluation" value={{ constraint_result: item.constraint_result, constraint_reason: item.constraint_reason, triggered_constraints: item.triggered_constraints, blocking_constraints: item.blocking_constraints, warning_constraints: item.warning_constraints }} />
            <RecordCard title="Procedure Evaluation" value={{ operational_procedure_result: item.operational_procedure_result, operational_procedure_reason: item.operational_procedure_reason }} />
            <RecordCard title="Required Operational Actions" value={{ required_ssrs: item.required_ssrs, required_osis: item.required_osis, required_emds: item.required_emds, required_documents: item.required_documents, required_medif: item.required_medif, required_manual_review: item.required_manual_review, required_airline_approval: item.required_airline_approval, required_station_notification: item.required_station_notification, required_crew_notification: item.required_crew_notification, action_summary: item.action_summary }} />
            <RecordCard title="Evidence Trace" value={{ evaluation_steps: item.evaluation_steps, evaluated_objects: item.evaluated_objects, evidence_trace: item.evidence_trace, structured_explanation: item.structured_explanation, explanation_sections: item.explanation_sections }} />
            <RecordCard title="Operational Risk" value={{ operational_risk: item.operational_risk, operational_risk_reason: item.operational_risk_reason }} />
            <RecordCard title="Lifecycle" value={{ feasibility_ready: item.feasibility_ready, recommendation_ready: item.recommendation_ready, archived: item.archived, archived_at: item.archived_at, created_at: item.created_at, updated_at: item.updated_at }} />
            <RecordCard title="Notes" value={{ operational_result: item.operational_result, operational_summary: item.operational_summary, operational_notes: item.operational_notes, internal_notes: item.internal_notes }} />
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
