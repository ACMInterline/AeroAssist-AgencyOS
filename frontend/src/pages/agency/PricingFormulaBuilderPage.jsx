import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, SelectField, formatType, optionPair, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaultFilters = {
  airline: "",
  service_family: "",
  service_code: "",
  pricing_unit: "",
  way: "",
  route_type: "",
  flight_type: "",
  fare_bundle: "",
  pricing_category: "",
  amount_type: "",
  currency: "",
  formula_status: "",
  manual_confirmation_required: "",
  client_visibility: "",
  search: "",
}

const pricingUnits = ["passenger", "passenger_per_segment", "pet", "pet_per_segment", "item", "item_per_segment", "booking", "trip", "request", "document", "hour", "case"]
const wayValues = ["one_way", "round_trip", "per_direction", "open_jaw", "multi_city"]
const routeTypes = ["domestic", "international", "regional_cross_border", "schengen", "non_schengen"]
const flightTypes = ["short", "regional", "mediumhaul", "longhaul", "ultra_longhaul", "interline", "connecting"]
const fareBundles = ["basic", "standard", "flex", "premium", "business", "custom", "unknown"]
const amountTypes = ["fixed", "range", "percentage", "manual_quote", "formula", "included", "not_applicable"]
const pricingCategories = ["transport_core", "ancillary_airline", "ancillary_non_airline", "documentation", "service_coordination", "compliance_review", "manual_handling", "premium_support", "after_sales_change", "refund_processing", "claim_processing"]
const statuses = ["draft", "in_review", "approved", "retired", "archived"]
const visibilityOptions = ["internal_only", "agent_visible", "client_visible", "client_hidden", "manual_review"]
const boolOptions = [["true", "Required"], ["false", "Optional"]]

export default function PricingFormulaBuilderPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const response = await apiGet(`/api/agencies/${context.agency.id}/pricing-formula-builder${query}`)
    setState({ ...context, items: response.items || response.pricing_formulas || [], summary: response.summary || {} })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.airline, filters.service_family, filters.service_code, filters.pricing_unit, filters.way, filters.route_type, filters.flight_type, filters.fare_bundle, filters.pricing_category, filters.amount_type, filters.currency, filters.formula_status, filters.manual_confirmation_required, filters.client_visibility, filters.search])

  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Formulas", summary.pricing_formula_builder_count ?? items.length],
    ["Categories", `${summary.covered_pricing_category_count || 0}/${summary.supported_pricing_category_count || pricingCategories.length}`],
    ["Components", summary.formula_component_count || 0],
    ["Multipliers", summary.multiplier_count || 0],
    ["Refund/Exchange", summary.refund_exchange_reference_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Pricing Formula Builder</h2>
              <p className="mt-1 text-sm text-slate-600">Agency pricing formula metadata for airline ancillary and service pricing review.</p>
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
            <h3 className="font-semibold text-slate-950">Formula Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <Field label="Service Family" value={filters.service_family} onChange={(value) => setFilters({ ...filters, service_family: value })} />
              <Field label="Service Code" value={filters.service_code} onChange={(value) => setFilters({ ...filters, service_code: value })} />
              <SelectField label="Pricing Unit" value={filters.pricing_unit} onChange={(value) => setFilters({ ...filters, pricing_unit: value })} options={pricingUnits.map(optionPair)} placeholder="All units" />
              <SelectField label="Way" value={filters.way} onChange={(value) => setFilters({ ...filters, way: value })} options={wayValues.map(optionPair)} placeholder="All ways" />
              <SelectField label="Route Type" value={filters.route_type} onChange={(value) => setFilters({ ...filters, route_type: value })} options={routeTypes.map(optionPair)} placeholder="All routes" />
              <SelectField label="Flight Type" value={filters.flight_type} onChange={(value) => setFilters({ ...filters, flight_type: value })} options={flightTypes.map(optionPair)} placeholder="All flights" />
              <SelectField label="Fare Bundle" value={filters.fare_bundle} onChange={(value) => setFilters({ ...filters, fare_bundle: value })} options={fareBundles.map(optionPair)} placeholder="All bundles" />
              <SelectField label="Category" value={filters.pricing_category} onChange={(value) => setFilters({ ...filters, pricing_category: value })} options={pricingCategories.map(optionPair)} placeholder="All categories" />
              <SelectField label="Amount Type" value={filters.amount_type} onChange={(value) => setFilters({ ...filters, amount_type: value })} options={amountTypes.map(optionPair)} placeholder="All amount types" />
              <Field label="Currency" value={filters.currency} onChange={(value) => setFilters({ ...filters, currency: value })} />
              <SelectField label="Status" value={filters.formula_status} onChange={(value) => setFilters({ ...filters, formula_status: value })} options={statuses.map(optionPair)} placeholder="All statuses" />
              <SelectField label="Manual Confirmation" value={filters.manual_confirmation_required} onChange={(value) => setFilters({ ...filters, manual_confirmation_required: value })} options={boolOptions} placeholder="Any confirmation" />
              <SelectField label="Client Visibility" value={filters.client_visibility} onChange={(value) => setFilters({ ...filters, client_visibility: value })} options={visibilityOptions.map(optionPair)} placeholder="Any visibility" />
              <Field label="Search" value={filters.search} onChange={(value) => setFilters({ ...filters, search: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Pricing Formulas</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <FormulaList items={items} /> : <EmptyState title="No pricing formulas" body="Pricing Formula Builder metadata for this agency will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function FormulaList({ items }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_180px_180px]">
              <div>
                <p className="font-semibold text-slate-950">{item.formula_display_name || item.formula_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.formula_reference || item.id}</p>
              </div>
              <p className="text-xs text-slate-600">Category: {formatType(item.pricing_category)}</p>
              <p className="text-xs text-slate-600">Visibility: {formatType(item.client_visibility)}</p>
            </div>
          </summary>
          <FormulaSections item={item} />
        </details>
      ))}
    </div>
  )
}

function FormulaSections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <RecordCard title="Overview" value={item.overview_section} />
      <RecordCard title="Pricing Context" value={item.pricing_context_section} />
      <RecordCard title="Amount" value={item.amount_section} />
      <RecordCard title="Formula Components" value={item.formula_components_section} />
      <RecordCard title="Multipliers" value={item.multipliers_section} />
      <RecordCard title="Applicability" value={item.applicability_section} />
      <RecordCard title="Manual Confirmation / Client Visibility" value={item.review_visibility_section} />
      <RecordCard title="Refund / Exchange Conditions" value={item.refund_exchange_section} />
      <RecordCard title="Evidence / Governance" value={item.evidence_governance_section} />
      <RecordCard title="Boundaries" value={item.boundary_section} />
    </div>
  )
}
