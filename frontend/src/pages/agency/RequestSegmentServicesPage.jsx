import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaultFilters = {
  request: "",
  passenger: "",
  segment: "",
  service_family: "",
  ssr_code: "",
  pet_transport_mode: "",
  item_category: "",
  readiness_status: "",
  requires_policy_review: "",
  requires_document_followup: "",
}

const readinessStatuses = ["missing_information", "needs_review", "blocked", "ready_for_agent_review", "ready_for_trip_conversion", "converted", "unknown"]
const booleanOptions = [["true", "Yes"], ["false", "No"]]

export default function RequestSegmentServicesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const response = await apiGet(`/api/agencies/${context.agency.id}/request-segment-services${query}`)
    setState({ ...context, items: response.items || response.scopes || [], summary: response.summary || {} })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.request, filters.passenger, filters.segment, filters.service_family, filters.ssr_code, filters.pet_transport_mode, filters.item_category, filters.readiness_status, filters.requires_policy_review, filters.requires_document_followup])

  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Scopes", items.length],
    ["Policy review", summary.policy_review_count || 0],
    ["Documents", summary.document_followup_count || 0],
    ["Pet scopes", summary.pet_transport_scope_count || 0],
    ["Item scopes", summary.special_item_scope_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Request Intake</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Request Segment Services</h2>
              <p className="mt-1 text-sm text-slate-600">Segment-scoped passenger service metadata for intake precision. Pets and special items stay attached to the relevant request segment.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Human review</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Scope Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <Field label="Request" value={filters.request} onChange={(value) => setFilters({ ...filters, request: value })} />
              <Field label="Passenger" value={filters.passenger} onChange={(value) => setFilters({ ...filters, passenger: value })} />
              <Field label="Segment" value={filters.segment} onChange={(value) => setFilters({ ...filters, segment: value })} />
              <Field label="Service Family" value={filters.service_family} onChange={(value) => setFilters({ ...filters, service_family: value })} />
              <Field label="SSR Code" value={filters.ssr_code} onChange={(value) => setFilters({ ...filters, ssr_code: value })} />
              <Field label="Pet Transport Mode" value={filters.pet_transport_mode} onChange={(value) => setFilters({ ...filters, pet_transport_mode: value })} />
              <Field label="Item Category" value={filters.item_category} onChange={(value) => setFilters({ ...filters, item_category: value })} />
              <SelectField label="Readiness Status" value={filters.readiness_status} onChange={(value) => setFilters({ ...filters, readiness_status: value })} options={readinessStatuses.map(optionPair)} placeholder="All statuses" />
              <SelectField label="Policy Review" value={filters.requires_policy_review} onChange={(value) => setFilters({ ...filters, requires_policy_review: value })} options={booleanOptions} placeholder="Any" />
              <SelectField label="Document Follow-up" value={filters.requires_document_followup} onChange={(value) => setFilters({ ...filters, requires_document_followup: value })} options={booleanOptions} placeholder="Any" />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Scopes</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <ScopeList items={items} /> : <EmptyState title="No request segment services" body="Passenger, segment, and service scope metadata will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function ScopeList({ items }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_190px_190px]">
              <div>
                <p className="font-semibold text-slate-950">{item.scope_display_name || item.scope_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{formatType(item.service_family)} - {item.ssr_code || item.service_code || "Service unset"} - {item.origin || "?"} to {item.destination || "?"}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Request: {item.travel_request_id || item.request_reference || "Unset"}</p>
                <p className="mt-1">Passenger: {item.passenger_id || item.request_passenger_reference || "Unset"}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Readiness: {formatType(item.readiness_status)}</p>
                <p className="mt-1">Status: {formatType(item.scope_status)}</p>
              </div>
            </div>
          </summary>
          <ScopeSections item={item} />
        </details>
      ))}
    </div>
  )
}

function ScopeSections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <RecordCard title="Scope Overview" value={{ scope_reference: item.scope_reference, scope_status: item.scope_status, scope_version: item.scope_version, created_by: item.created_by, created_at: item.created_at, updated_at: item.updated_at }} />
      <RecordCard title="Request Context" value={{ travel_request_id: item.travel_request_id, request_reference: item.request_reference, source_entry_path: item.source_entry_path, submission_channel: item.submission_channel, client_id: item.client_id, contact_summary: item.contact_summary }} />
      <RecordCard title="Passenger Context" value={{ request_passenger_reference: item.request_passenger_reference, passenger_workspace_id: item.passenger_workspace_id, passenger_id: item.passenger_id, passenger_link_mode: item.passenger_link_mode, passenger_snapshot: item.passenger_snapshot, beneficiary_type: item.beneficiary_type }} />
      <RecordCard title="Segment Context" value={{ request_segment_reference: item.request_segment_reference, segment_order: item.segment_order, origin: item.origin, destination: item.destination, departure_date: item.departure_date, arrival_date: item.arrival_date, preferred_airline: item.preferred_airline, cabin_requested: item.cabin_requested, segment_scope_type: item.segment_scope_type }} />
      <RecordCard title="Service Context" value={{ service_family: item.service_family, service_code: item.service_code, ssr_code: item.ssr_code, service_catalogue_reference: item.service_catalogue_reference, selected_service_key: item.selected_service_key, service_details: item.service_details, requested_status: item.requested_status, passenger_segment_service_summary: item.passenger_segment_service_summary }} />
      <RecordCard title="Pet Context" value={{ pet_reference: item.pet_reference, pet_id: item.pet_id, pet_transport_mode: item.pet_transport_mode, species: item.species, breed: item.breed, snub_nosed_flag: item.snub_nosed_flag, pet_weight_kg: item.pet_weight_kg, container_dimensions: item.container_dimensions, pet_document_status: item.pet_document_status }} />
      <RecordCard title="Special Item Context" value={{ special_item_reference: item.special_item_reference, special_item_id: item.special_item_id, item_category: item.item_category, transport_location: item.transport_location, item_weight_kg: item.item_weight_kg, item_dimensions: item.item_dimensions, battery_type: item.battery_type, documentation_status: item.documentation_status }} />
      <RecordCard title="Operational Flags" value={{ requires_airline_policy_review: item.requires_airline_policy_review, requires_medical_review: item.requires_medical_review, requires_document_followup: item.requires_document_followup, requires_airline_approval: item.requires_airline_approval, requires_manual_review: item.requires_manual_review, requires_pricing_review: item.requires_pricing_review, operational_flag_summary: item.operational_flag_summary }} />
      <RecordCard title="Knowledge Links" value={{ service_parameter_taxonomy_ids: item.service_parameter_taxonomy_ids, operational_constraint_ids: item.operational_constraint_ids, capability_matrix_ids: item.capability_matrix_ids, operational_evaluation_ids: item.operational_evaluation_ids, feasibility_ids: item.feasibility_ids, recommendation_ids: item.recommendation_ids, knowledge_link_summary: item.knowledge_link_summary }} />
      <RecordCard title="Readiness" value={{ readiness_status: item.readiness_status, missing_fields: item.missing_fields, missing_documents: item.missing_documents, readiness_warnings: item.readiness_warnings, readiness_blockers: item.readiness_blockers, readiness_summary: item.readiness_summary }} />
      <RecordCard title="Conversion Metadata" value={{ linked_trip_id: item.linked_trip_id, converted_to_trip: item.converted_to_trip, converted_at: item.converted_at, trip_segment_ids: item.trip_segment_ids, carried_forward_to_trip: item.carried_forward_to_trip, conversion_summary: item.conversion_summary }} />
      <RecordCard title="Trace / Notes" value={{ request_snapshot: item.request_snapshot, decision_trace: item.decision_trace, operational_notes: item.operational_notes, internal_notes: item.internal_notes, metadata: item.metadata }} />
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
