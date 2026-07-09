import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
  package_status: "",
  airline: "",
  recommendation_level: "",
  readiness_status: "",
  operational_risk: "",
  passenger_need: "",
  destination: "",
  travel_date: "",
  offer_workspace: "",
  client_visibility_status: "",
}

const packageStatuses = ["draft", "in_review", "ready", "approved", "archived"]
const recommendationLevels = ["highly_recommended", "recommended", "acceptable", "use_with_caution", "not_recommended"]
const readinessStatuses = ["ready", "conditional", "blocked", "needs_review", "unknown"]
const riskLevels = ["low", "medium", "high", "critical", "unknown"]
const visibilityStatuses = ["internal", "agent_review", "client_ready", "client_visible", "hidden"]

export default function IntelligentOfferBuilderPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/intelligent-offer-builder${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      items: response.items || response.packages || [],
      summary: response.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.package_status, filters.airline, filters.recommendation_level, filters.readiness_status, filters.operational_risk, filters.passenger_need, filters.destination, filters.travel_date, filters.offer_workspace, filters.client_visibility_status])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Packages", items.length],
    ["Decision ready", summary.decision_pack_ready_count || 0],
    ["Approved", summary.approved_for_client_presentation_count || 0],
    ["Inputs", (summary.recommendation_reference_count || 0) + (summary.feasibility_reference_count || 0) + (summary.operational_evaluation_reference_count || 0)],
    ["Required actions", summary.required_action_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Intelligent Offer Builder</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only offer-intelligence packages that consume approved recommendations, feasibility, operational evaluations, capability matrix records, and evidence. No search, booking, ticketing, EMD issuance, provider calls, AI generation, or automatic sending.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Decision support</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata CRUD API</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Package Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <SelectField label="Package Status" value={filters.package_status} onChange={(value) => setFilters({ ...filters, package_status: value })} options={packageStatuses.map(optionPair)} placeholder="All statuses" />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <SelectField label="Recommendation Level" value={filters.recommendation_level} onChange={(value) => setFilters({ ...filters, recommendation_level: value })} options={recommendationLevels.map(optionPair)} placeholder="All levels" />
              <SelectField label="Readiness Status" value={filters.readiness_status} onChange={(value) => setFilters({ ...filters, readiness_status: value })} options={readinessStatuses.map(optionPair)} placeholder="All readiness" />
              <SelectField label="Operational Risk" value={filters.operational_risk} onChange={(value) => setFilters({ ...filters, operational_risk: value })} options={riskLevels.map(optionPair)} placeholder="All risk" />
              <Field label="Passenger Need" value={filters.passenger_need} onChange={(value) => setFilters({ ...filters, passenger_need: value })} />
              <Field label="Destination" value={filters.destination} onChange={(value) => setFilters({ ...filters, destination: value })} />
              <Field label="Travel Date" value={filters.travel_date} onChange={(value) => setFilters({ ...filters, travel_date: value })} />
              <Field label="Offer Workspace" value={filters.offer_workspace} onChange={(value) => setFilters({ ...filters, offer_workspace: value })} />
              <SelectField label="Client Visibility" value={filters.client_visibility_status} onChange={(value) => setFilters({ ...filters, client_visibility_status: value })} options={visibilityStatuses.map(optionPair)} placeholder="All visibility" />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Offer Intelligence Packages</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <PackageList items={items} showAgency /> : <EmptyState title="No offer intelligence packages" body="Metadata packages prepared for offer builder decision support will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function PackageList({ items, showAgency = false }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_190px_190px]">
              <div>
                <p className="font-semibold text-slate-950">{item.package_display_name || item.offer_intelligence_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{(item.recommended_airlines || []).join(", ") || "Airline unset"} - {formatType(item.readiness_status)} - {formatType(item.client_visibility_status)}</p>
              </div>
              <div className="text-xs text-slate-600">
                {showAgency ? <p>{item.agency_name || item.agency_id || "Platform governed"}</p> : null}
                <p className="mt-1">Offer: {item.offer_reference || item.offer_workspace_id || "Unset"}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Status: {formatType(item.package_status)}</p>
                <p className="mt-1">Decision pack: {item.decision_pack_ready ? "Ready" : "Not ready"}</p>
              </div>
            </div>
          </summary>
          <PackageSections item={item} />
        </details>
      ))}
    </div>
  )
}

function PackageSections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <RecordCard title="Package Overview" value={{ offer_intelligence_reference: item.offer_intelligence_reference, package_status: item.package_status, package_version: item.package_version, created_by: item.created_by }} />
      <RecordCard title="Passenger Context" value={{ passenger_workspace_id: item.passenger_workspace_id, passenger_profile_reference: item.passenger_profile_reference, passenger_need_summary: item.passenger_need_summary, passenger_requirements: item.passenger_requirements }} />
      <RecordCard title="Trip / Request Context" value={{ travel_request_id: item.travel_request_id, trip_workspace_id: item.trip_workspace_id, flight_workspace_ids: item.flight_workspace_ids, itinerary_summary: item.itinerary_summary, origin: item.origin, destination: item.destination, transit_points: item.transit_points, travel_date: item.travel_date, cabin_requested: item.cabin_requested }} />
      <RecordCard title="Offer Context" value={{ offer_workspace_id: item.offer_workspace_id, offer_reference: item.offer_reference, offer_option_ids: item.offer_option_ids, offer_status: item.offer_status, client_visibility_status: item.client_visibility_status }} />
      <RecordCard title="Intelligence Inputs" value={{ recommendation_ids: item.recommendation_ids, feasibility_ids: item.feasibility_ids, operational_evaluation_ids: item.operational_evaluation_ids, capability_matrix_ids: item.capability_matrix_ids, knowledge_version_ids: item.knowledge_version_ids, evidence_reference_ids: item.evidence_reference_ids, input_reference_summary: item.input_reference_summary }} />
      <RecordCard title="Recommended Options" value={{ recommended_airlines: item.recommended_airlines, recommended_itineraries: item.recommended_itineraries, recommendation_rankings: item.recommendation_rankings, recommendation_scores: item.recommendation_scores, recommendation_levels: item.recommendation_levels, recommendation_reasons: item.recommendation_reasons, recommended_option_summary: item.recommended_option_summary }} />
      <RecordCard title="Operational Readiness" value={{ readiness_status: item.readiness_status, readiness_summary: item.readiness_summary, readiness_blockers: item.readiness_blockers, readiness_warnings: item.readiness_warnings, readiness_conditions: item.readiness_conditions, operational_risk_level: item.operational_risk_level, readiness_metadata_summary: item.readiness_metadata_summary }} />
      <RecordCard title="Required Actions" value={{ required_ssrs: item.required_ssrs, required_osis: item.required_osis, required_emds: item.required_emds, required_documents: item.required_documents, required_medif: item.required_medif, required_airline_approval: item.required_airline_approval, required_station_notification: item.required_station_notification, required_crew_notification: item.required_crew_notification, required_manual_review: item.required_manual_review, required_follow_up_tasks: item.required_follow_up_tasks, required_action_summary: item.required_action_summary }} />
      <RecordCard title="Pricing / Cost References" value={{ ticket_cost_reference: item.ticket_cost_reference, ancillary_cost_reference: item.ancillary_cost_reference, total_cost_reference: item.total_cost_reference, pricing_notes: item.pricing_notes, refund_condition_references: item.refund_condition_references, exchange_condition_references: item.exchange_condition_references }} />
      <RecordCard title="Client Explanation" value={{ client_explanation_summary: item.client_explanation_summary, client_visible_reasons: item.client_visible_reasons, client_visible_limitations: item.client_visible_limitations, client_visible_conditions: item.client_visible_conditions, client_visible_documents: item.client_visible_documents, client_visible_price_notes: item.client_visible_price_notes }} />
      <RecordCard title="Internal Explanation" value={{ internal_operational_reasoning: item.internal_operational_reasoning, internal_risk_notes: item.internal_risk_notes, internal_evidence_trace: item.internal_evidence_trace, internal_decision_trace: item.internal_decision_trace, explanation_summary: item.explanation_summary }} />
      <RecordCard title="Decision Pack" value={{ decision_pack_ready: item.decision_pack_ready, decision_pack_reference: item.decision_pack_reference, decision_pack_summary: item.decision_pack_summary, decision_pack_sections: item.decision_pack_sections, decision_pack_evidence: item.decision_pack_evidence, decision_pack_metadata_summary: item.decision_pack_metadata_summary }} />
      <RecordCard title="Lifecycle" value={{ prepared_for_offer_builder: item.prepared_for_offer_builder, reviewed_by_agent: item.reviewed_by_agent, approved_for_client_presentation: item.approved_for_client_presentation, archived: item.archived, archived_at: item.archived_at, created_at: item.created_at, updated_at: item.updated_at }} />
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
