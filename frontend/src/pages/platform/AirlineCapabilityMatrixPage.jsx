import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
  airline: "",
  service_domain: "",
  service_family: "",
  ssr_code: "",
  rfic: "",
  rfisc: "",
  aircraft_family: "",
  cabin: "",
  airport: "",
  route: "",
  country: "",
  season: "",
  capability_status: "",
  operational_risk: "",
  confidence_level: "",
  effective_date: "",
}

const capabilityStatuses = ["draft", "under_review", "approved", "active", "superseded", "archived", "available", "unavailable", "conditional", "restricted", "manual_review", "unknown"]
const riskLevels = ["low", "medium", "high", "critical", "unknown"]
const confidenceLevels = ["official", "high", "medium", "low", "unknown"]

export default function AirlineCapabilityMatrixPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/airline-capability-matrix${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      items: response.items || response.capabilities || [],
      summary: response.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.airline, filters.service_domain, filters.service_family, filters.ssr_code, filters.rfic, filters.rfisc, filters.aircraft_family, filters.cabin, filters.airport, filters.route, filters.country, filters.season, filters.capability_status, filters.operational_risk, filters.confidence_level, filters.effective_date])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Capabilities", items.length],
    ["Airlines", summary.airline_count || 0],
    ["Services", summary.service_domain_count || 0],
    ["Governance links", summary.knowledge_governance_link_count || 0],
    ["Manual review", summary.manual_review_required_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Airline Capability Matrix</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only inventory of what airlines can operationally deliver. Capability is different from policy; this page does not evaluate passenger cases, score feasibility, rank airlines, reason with AI, execute parsers, calculate pricing, call providers, run workers, or automatically publish.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Capability inventory</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Capability filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <Field label="Service domain" value={filters.service_domain} onChange={(value) => setFilters({ ...filters, service_domain: value })} />
              <Field label="Service family" value={filters.service_family} onChange={(value) => setFilters({ ...filters, service_family: value })} />
              <Field label="SSR code" value={filters.ssr_code} onChange={(value) => setFilters({ ...filters, ssr_code: value })} />
              <Field label="RFIC" value={filters.rfic} onChange={(value) => setFilters({ ...filters, rfic: value })} />
              <Field label="RFISC" value={filters.rfisc} onChange={(value) => setFilters({ ...filters, rfisc: value })} />
              <Field label="Aircraft family" value={filters.aircraft_family} onChange={(value) => setFilters({ ...filters, aircraft_family: value })} />
              <Field label="Cabin" value={filters.cabin} onChange={(value) => setFilters({ ...filters, cabin: value })} />
              <Field label="Airport" value={filters.airport} onChange={(value) => setFilters({ ...filters, airport: value })} />
              <Field label="Route" value={filters.route} onChange={(value) => setFilters({ ...filters, route: value })} />
              <Field label="Country" value={filters.country} onChange={(value) => setFilters({ ...filters, country: value })} />
              <Field label="Season" value={filters.season} onChange={(value) => setFilters({ ...filters, season: value })} />
              <SelectField label="Capability status" value={filters.capability_status} onChange={(value) => setFilters({ ...filters, capability_status: value })} options={capabilityStatuses.map(optionPair)} placeholder="All status" />
              <SelectField label="Operational risk" value={filters.operational_risk} onChange={(value) => setFilters({ ...filters, operational_risk: value })} options={riskLevels.map(optionPair)} placeholder="All risk" />
              <SelectField label="Confidence" value={filters.confidence_level} onChange={(value) => setFilters({ ...filters, confidence_level: value })} options={confidenceLevels.map(optionPair)} placeholder="All confidence" />
              <Field label="Effective date" type="date" value={filters.effective_date} onChange={(value) => setFilters({ ...filters, effective_date: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Capability Records</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <CapabilityList items={items} showAgency /> : <EmptyState title="No capability matrix records" body="Airline operational capability metadata will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function CapabilityList({ items, showAgency = false }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_190px_190px]">
              <div>
                <p className="font-semibold text-slate-950">{item.capability_display_name || item.capability_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.airline_code || "Airline unset"} - {item.service_domain || "Service unset"} - {formatType(item.capability_outcome)}</p>
              </div>
              <div className="text-xs text-slate-600">
                {showAgency ? <p>{item.agency_name || item.agency_id || "Platform governed"}</p> : null}
                <p className="mt-1">Status: {formatType(item.capability_status)}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Risk: {formatType(item.operational_risk_level)}</p>
                <p className="mt-1">Confidence: {formatType(item.capability_confidence)}</p>
              </div>
            </div>
          </summary>
          <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
            <DetailCard title="Capability Overview" lines={[
              `Reference: ${item.capability_reference || "Unset"}`,
              `Version: ${item.capability_version || "Unset"}`,
              `Name: ${item.capability_name || "Unset"}`,
              `Description: ${item.capability_description || "Unset"}`,
              `Outcome: ${formatType(item.capability_outcome)}`,
            ]} />
            <DetailCard title="Airline" lines={[
              `Airline: ${item.airline_code || "Unset"} ${item.airline_name || ""}`,
              `Validating carrier: ${item.validating_carrier || "Unset"}`,
              `Operating carrier: ${item.operating_carrier || "Unset"}`,
              `Marketing carrier: ${item.marketing_carrier || "Unset"}`,
            ]} />
            <RecordCard title="Service" value={{ service_domain: item.service_domain, service_family: item.service_family, service_variant: item.service_variant, passenger_need_category: item.passenger_need_category, ssr_code: item.ssr_code, osi_relevance: item.osi_relevance, rfic: item.rfic, rfisc: item.rfisc, emd_relevance: item.emd_relevance, document_relevance: item.document_relevance }} />
            <RecordCard title="Knowledge Governance Links" value={{ knowledge_version_ids: item.knowledge_version_ids, knowledge_release_ids: item.knowledge_release_ids, acquisition_ids: item.acquisition_ids, normalisation_ids: item.normalisation_ids, constraint_ids: item.constraint_ids, evidence_reference_ids: item.evidence_reference_ids, summary: item.knowledge_governance_summary }} />
            <RecordCard title="Aircraft / Cabin Capability" value={{ aircraft_applicability: item.aircraft_applicability, aircraft_family: item.aircraft_family, aircraft_subtype: item.aircraft_subtype, aircraft_configuration: item.aircraft_configuration, cabin_applicability: item.cabin_applicability, cabin_family: item.cabin_family, cabin_name: item.cabin_name, seat_type: item.seat_type, seat_map_relevance: item.seat_map_relevance, adjacent_seat_available: item.adjacent_seat_available, adjacent_seat_required: item.adjacent_seat_required, fixed_armrests: item.fixed_armrests, movable_armrests: item.movable_armrests, bulkhead_restriction: item.bulkhead_restriction, exit_row_restriction: item.exit_row_restriction, under_seat_space_available: item.under_seat_space_available, under_seat_space_notes: item.under_seat_space_notes, accessible_lavatory_available: item.accessible_lavatory_available, onboard_wheelchair_capability: item.onboard_wheelchair_capability, cabin_notes: item.cabin_notes }} />
            <RecordCard title="Airport / Station Capability" value={{ airport_applicability: item.airport_applicability, station_applicability: item.station_applicability, origin_airport_applicability: item.origin_airport_applicability, destination_airport_applicability: item.destination_airport_applicability, transit_airport_applicability: item.transit_airport_applicability, ground_handling_capability: item.ground_handling_capability, airport_handling_required: item.airport_handling_required, station_notification_required: item.station_notification_required, airport_restriction_notes: item.airport_restriction_notes }} />
            <RecordCard title="Route / Country / Season Capability" value={{ route_applicability: item.route_applicability, origin_country_applicability: item.origin_country_applicability, destination_country_applicability: item.destination_country_applicability, transit_country_applicability: item.transit_country_applicability, seasonal_applicability: item.seasonal_applicability, date_range_applicability: item.date_range_applicability, event_based_applicability: item.event_based_applicability, embargo_applicability: item.embargo_applicability, weather_temperature_relevance: item.weather_temperature_relevance }} />
            <RecordCard title="Interline / Codeshare Capability" value={{ interline_allowed: item.interline_allowed, codeshare_allowed: item.codeshare_allowed, operating_carrier_control_required: item.operating_carrier_control_required, validating_carrier_control_required: item.validating_carrier_control_required, marketing_carrier_restriction_notes: item.marketing_carrier_restriction_notes }} />
            <RecordCard title="Animal Transport Capability" value={{ animal_transport_applicable: item.animal_transport_applicable, petc_capability: item.petc_capability, avih_capability: item.avih_capability, species_applicability: item.species_applicability, breed_applicability: item.breed_applicability, brachycephalic_capability: item.brachycephalic_capability, carrier_dimension_capability: item.carrier_dimension_capability, carrier_weight_capability: item.carrier_weight_capability, pet_under_seat_capability: item.pet_under_seat_capability, pet_on_adjacent_extra_seat_capability: item.pet_on_adjacent_extra_seat_capability, animal_transport_notes: item.animal_transport_notes }} />
            <RecordCard title="Extra Seat / EXST Capability" value={{ extra_seat_applicable: item.extra_seat_applicable, extra_seat_available: item.extra_seat_available, extra_seat_reason: item.extra_seat_reason, passenger_of_size_capability: item.passenger_of_size_capability, comfort_extra_seat_capability: item.comfort_extra_seat_capability, cbbg_capability: item.cbbg_capability, musical_instrument_extra_seat_capability: item.musical_instrument_extra_seat_capability, medical_extra_seat_capability: item.medical_extra_seat_capability, adjacent_extra_seat_capability: item.adjacent_extra_seat_capability, extra_seat_cabin_restriction_notes: item.extra_seat_cabin_restriction_notes, extra_seat_refund_capability_notes: item.extra_seat_refund_capability_notes }} />
            <RecordCard title="Medical / Accessibility Capability" value={{ wheelchair_capability: item.wheelchair_capability, wchr_capability: item.wchr_capability, wchs_capability: item.wchs_capability, wchc_capability: item.wchc_capability, medif_capability: item.medif_capability, oxygen_capability: item.oxygen_capability, stretcher_capability: item.stretcher_capability, medical_equipment_capability: item.medical_equipment_capability, reduced_mobility_notes: item.reduced_mobility_notes }} />
            <RecordCard title="Operational Requirements" value={{ approval_required: item.approval_required, document_required: item.document_required, emd_required: item.emd_required, ssr_required: item.ssr_required, osi_required: item.osi_required, medif_required: item.medif_required, advance_notice_required: item.advance_notice_required, advance_notice_hours: item.advance_notice_hours, crew_notification_required: item.crew_notification_required, operational_procedure_required: item.operational_procedure_required, manual_review_required: item.manual_review_required }} />
            <RecordCard title="Risk / Confidence" value={{ operational_risk_level: item.operational_risk_level, operational_risk_reason: item.operational_risk_reason, data_confidence_level: item.data_confidence_level, evidence_confidence_level: item.evidence_confidence_level, capability_confidence: item.capability_confidence, operational_validity_status: item.operational_validity_status, operational_validity_confidence: item.operational_validity_confidence, last_operational_confirmation_date: item.last_operational_confirmation_date, operational_confirmation_source: item.operational_confirmation_source }} />
            <RecordCard title="Lifecycle" value={{ effective_from: item.effective_from, effective_until: item.effective_until, superseded_by_capability_id: item.superseded_by_capability_id, supersedes_capability_ids: item.supersedes_capability_ids, archived_at: item.archived_at }} />
            <RecordCard title="Notes" value={{ capability_reason: item.capability_reason, operational_notes: item.operational_notes, internal_notes: item.internal_notes }} />
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

function Field({ label, type = "text", value, onChange }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input type={type} className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
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
