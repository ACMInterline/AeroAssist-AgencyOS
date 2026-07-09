import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
  taxonomy_status: "",
  policy_family: "",
  service_family: "",
  service_code: "",
  parameter_domain: "",
  parameter_group: "",
  parameter_scope: "",
  review_status: "",
  approval_status: "",
}

const taxonomyStatuses = ["draft", "active", "in_review", "approved", "deprecated", "archived"]
const reviewStatuses = ["not_reviewed", "in_review", "changes_requested", "reviewed", "approved", "rejected"]
const approvalStatuses = ["not_submitted", "pending", "approved", "rejected", "expired"]

export default function ServiceParameterTaxonomiesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/service-parameter-taxonomies${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      items: response.items || response.taxonomies || [],
      summary: response.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.taxonomy_status, filters.policy_family, filters.service_family, filters.service_code, filters.parameter_domain, filters.parameter_group, filters.parameter_scope, filters.review_status, filters.approval_status])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Taxonomies", items.length],
    ["Service codes", summary.service_code_count || 0],
    ["Parameters", totalParameterCount(summary)],
    ["References", summary.reference_requirement_count || 0],
    ["Graph links", summary.knowledge_graph_link_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operational Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Service Parameter Taxonomies</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only measurable service parameters reused by knowledge, constraints, capability, evaluation, feasibility, recommendation, offer intelligence, and case records. No rule evaluation, price calculation, provider calls, AI generation, or workers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Reusable parameters</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Human authority</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Taxonomy Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <SelectField label="Taxonomy Status" value={filters.taxonomy_status} onChange={(value) => setFilters({ ...filters, taxonomy_status: value })} options={taxonomyStatuses.map(optionPair)} placeholder="All statuses" />
              <SelectField label="Review Status" value={filters.review_status} onChange={(value) => setFilters({ ...filters, review_status: value })} options={reviewStatuses.map(optionPair)} placeholder="Any review" />
              <SelectField label="Approval Status" value={filters.approval_status} onChange={(value) => setFilters({ ...filters, approval_status: value })} options={approvalStatuses.map(optionPair)} placeholder="Any approval" />
              <Field label="Policy Family" value={filters.policy_family} onChange={(value) => setFilters({ ...filters, policy_family: value })} />
              <Field label="Service Family" value={filters.service_family} onChange={(value) => setFilters({ ...filters, service_family: value })} />
              <Field label="Service Code" value={filters.service_code} onChange={(value) => setFilters({ ...filters, service_code: value })} />
              <Field label="Parameter Domain" value={filters.parameter_domain} onChange={(value) => setFilters({ ...filters, parameter_domain: value })} />
              <Field label="Parameter Group" value={filters.parameter_group} onChange={(value) => setFilters({ ...filters, parameter_group: value })} />
              <Field label="Parameter Scope" value={filters.parameter_scope} onChange={(value) => setFilters({ ...filters, parameter_scope: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Taxonomies</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <TaxonomyList items={items} showAgency /> : <EmptyState title="No service parameter taxonomies" body="Reusable parameter taxonomy metadata will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function TaxonomyList({ items, showAgency = false }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_190px_190px]">
              <div>
                <p className="font-semibold text-slate-950">{item.taxonomy_display_name || item.taxonomy_name || item.taxonomy_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{formatType(item.service_family)} - {formatType(item.parameter_group)} - {(item.service_codes || []).join(", ") || "Codes unset"}</p>
              </div>
              <div className="text-xs text-slate-600">
                {showAgency ? <p>{item.agency_name || item.agency_id || "Platform governed"}</p> : null}
                <p className="mt-1">Status: {formatType(item.taxonomy_status)}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Review: {formatType(item.review_status)}</p>
                <p className="mt-1">Approval: {formatType(item.approval_status)}</p>
              </div>
            </div>
          </summary>
          <TaxonomySections item={item} />
        </details>
      ))}
    </div>
  )
}

function TaxonomySections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <RecordCard title="Taxonomy Overview" value={{ taxonomy_reference: item.taxonomy_reference, taxonomy_status: item.taxonomy_status, taxonomy_version: item.taxonomy_version, taxonomy_name: item.taxonomy_name, taxonomy_description: item.taxonomy_description, created_by: item.created_by, created_at: item.created_at, updated_at: item.updated_at }} />
      <RecordCard title="Classification" value={{ policy_family: item.policy_family, service_family: item.service_family, service_codes: item.service_codes, beneficiary_type: item.beneficiary_type, parameter_domain: item.parameter_domain, parameter_group: item.parameter_group, parameter_scope: item.parameter_scope }} />
      <RecordCard title="Support / Evaluation Vocabulary" value={{ support_status_options: item.support_status_options, evaluation_status_options: item.evaluation_status_options, restriction_status_options: item.restriction_status_options, approval_status_options: item.approval_status_options, vocabulary_summary: item.vocabulary_summary }} />
      <RecordCard title="Passenger Assistance Parameters" value={{ wheelchair_mobility_parameters: item.wheelchair_mobility_parameters, mobility_level_parameters: item.mobility_level_parameters, wheelchair_device_parameters: item.wheelchair_device_parameters, battery_type_parameters: item.battery_type_parameters, device_weight_dimension_parameters: item.device_weight_dimension_parameters, airport_assistance_parameters: item.airport_assistance_parameters, onboard_assistance_parameters: item.onboard_assistance_parameters, medical_support_parameters: item.medical_support_parameters, medif_parameters: item.medif_parameters, fit_to_fly_parameters: item.fit_to_fly_parameters, stretcher_parameters: item.stretcher_parameters, oxygen_poc_parameters: item.oxygen_poc_parameters, battery_duration_parameters: item.battery_duration_parameters, umnr_age_parameters: item.umnr_age_parameters, umnr_route_parameters: item.umnr_route_parameters, guardian_parameters: item.guardian_parameters, extra_seat_parameters: item.extra_seat_parameters, passenger_of_size_parameters: item.passenger_of_size_parameters, cbbg_parameters: item.cbbg_parameters, adjacent_seat_parameters: item.adjacent_seat_parameters, cabin_restriction_parameters: item.cabin_restriction_parameters, extra_seat_refund_parameters: item.extra_seat_refund_parameters }} />
      <RecordCard title="Pets / Animals Parameters" value={{ petc_parameters: item.petc_parameters, avih_parameters: item.avih_parameters, svan_parameters: item.svan_parameters, esan_parameters: item.esan_parameters, species_parameters: item.species_parameters, breed_parameters: item.breed_parameters, breed_risk_flag_parameters: item.breed_risk_flag_parameters, animal_age_parameters: item.animal_age_parameters, animal_weight_parameters: item.animal_weight_parameters, container_dimension_parameters: item.container_dimension_parameters, container_type_parameters: item.container_type_parameters, pet_under_seat_parameters: item.pet_under_seat_parameters, pet_on_adjacent_extra_seat_parameters: item.pet_on_adjacent_extra_seat_parameters, animal_purpose_parameters: item.animal_purpose_parameters, temperature_parameters: item.temperature_parameters, seasonal_restriction_parameters: item.seasonal_restriction_parameters, animal_document_parameters: item.animal_document_parameters }} />
      <RecordCard title="Special Items / Baggage Parameters" value={{ sports_equipment_parameters: item.sports_equipment_parameters, musical_instrument_parameters: item.musical_instrument_parameters, fragile_valuable_parameters: item.fragile_valuable_parameters, restricted_equipment_parameters: item.restricted_equipment_parameters, special_baggage_parameters: item.special_baggage_parameters, item_type_parameters: item.item_type_parameters, item_weight_dimension_parameters: item.item_weight_dimension_parameters, packaging_parameters: item.packaging_parameters, declared_value_parameters: item.declared_value_parameters, permit_document_parameters: item.permit_document_parameters }} />
      <RecordCard title="Route / Aircraft / Cabin Parameters" value={{ route_type_parameters: item.route_type_parameters, flight_type_parameters: item.flight_type_parameters, airport_parameters: item.airport_parameters, country_parameters: item.country_parameters, aircraft_type_parameters: item.aircraft_type_parameters, aircraft_family_parameters: item.aircraft_family_parameters, cabin_parameters: item.cabin_parameters, seat_type_parameters: item.seat_type_parameters, fixed_armrest_parameters: item.fixed_armrest_parameters, under_seat_space_parameters: item.under_seat_space_parameters, accessible_lavatory_parameters: item.accessible_lavatory_parameters }} />
      <RecordCard title="Pricing Parameters" value={{ pricing_units: item.pricing_units, pricing_way_values: item.pricing_way_values, pricing_route_types: item.pricing_route_types, pricing_flight_types: item.pricing_flight_types, pricing_fare_bundles: item.pricing_fare_bundles, pricing_categories: item.pricing_categories, amount_types: item.amount_types, pricing_basis_parameters: item.pricing_basis_parameters, pricing_formula_components: item.pricing_formula_components, pricing_applicability_parameters: item.pricing_applicability_parameters, refund_condition_parameters: item.refund_condition_parameters, exchange_condition_parameters: item.exchange_condition_parameters }} />
      <RecordCard title="Reference Requirements" value={{ required_reference_collections: item.required_reference_collections, required_reference_values: item.required_reference_values, missing_reference_notes: item.missing_reference_notes }} />
      <RecordCard title="Knowledge Graph Links" value={{ acquisition_ids: item.acquisition_ids, normalisation_ids: item.normalisation_ids, constraint_ids: item.constraint_ids, knowledge_version_ids: item.knowledge_version_ids, capability_matrix_ids: item.capability_matrix_ids, operational_evaluation_ids: item.operational_evaluation_ids, feasibility_ids: item.feasibility_ids, recommendation_ids: item.recommendation_ids, intelligent_offer_package_ids: item.intelligent_offer_package_ids, operational_intelligence_case_ids: item.operational_intelligence_case_ids, knowledge_graph_link_summary: item.knowledge_graph_link_summary }} />
      <RecordCard title="Governance" value={{ review_status: item.review_status, approval_status: item.approval_status, reviewer: item.reviewer, review_notes: item.review_notes, approved_by: item.approved_by, approved_at: item.approved_at, governance_summary: item.governance_summary }} />
      <RecordCard title="Notes" value={{ internal_notes: item.internal_notes, metadata: item.metadata, parameter_summary: item.parameter_summary, template_matches: item.template_matches }} />
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

function totalParameterCount(summary) {
  return [
    summary.passenger_assistance_parameter_count,
    summary.pets_animals_parameter_count,
    summary.special_item_parameter_count,
    summary.route_aircraft_cabin_parameter_count,
    summary.pricing_parameter_count,
  ].reduce((total, value) => total + Number(value || 0), 0)
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
