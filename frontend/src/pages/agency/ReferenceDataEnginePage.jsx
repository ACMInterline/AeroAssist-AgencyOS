import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, SelectField, formatType, optionPair, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaultFilters = {
  domain_code: "",
  governance_status: "",
  review_status: "",
  active: "",
  search: "",
}

const domainCodes = [
  "airlines",
  "airports",
  "countries",
  "cities",
  "currencies",
  "aircraft_types",
  "aircraft_families",
  "cabin_classes",
  "seat_types",
  "passenger_types",
  "service_codes",
  "service_families",
  "ssr_codes",
  "osi_templates",
  "rfic_rfisc",
  "pet_species",
  "pet_breeds",
  "breed_risk_flags",
  "container_types",
  "document_types",
  "vaccination_types",
  "mobility_levels",
  "wheelchair_device_types",
  "battery_types",
  "medical_equipment_types",
  "route_types",
  "flight_types",
  "fare_bundles",
  "pricing_units",
  "pricing_categories",
  "formula_components",
  "temperature_zones",
  "seasonal_restriction_types",
  "travel_purposes",
]

const governanceStatuses = ["draft", "in_review", "approved", "retired", "archived"]
const reviewStatuses = ["needs_review", "approved", "rejected", "changes_requested", "not_required"]
const activeOptions = [["true", "Active"], ["false", "Inactive"]]

export default function ReferenceDataEnginePage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const response = await apiGet(`/api/agencies/${context.agency.id}/reference-data-engine${query}`)
    setState({ ...context, items: response.items || response.domains || [], summary: response.summary || {} })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.domain_code, filters.governance_status, filters.review_status, filters.active, filters.search])

  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Domains", summary.reference_data_domain_count ?? items.length],
    ["Records", summary.record_count || 0],
    ["Aliases", summary.alias_count || 0],
    ["Rules", Number(summary.normalization_rule_count || 0) + Number(summary.validation_rule_count || 0)],
    ["Coverage", `${summary.supported_domain_coverage_count || 0}/${summary.supported_domain_count || domainCodes.length}`],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Reference Data</h2>
              <p className="mt-1 text-sm text-slate-600">Agency-scoped reference domains for operational knowledge records, aliases, normalization rules, validation rules, and review metadata.</p>
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
            <h3 className="font-semibold text-slate-950">Domain Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-5">
              <SelectField label="Domain" value={filters.domain_code} onChange={(value) => setFilters({ ...filters, domain_code: value })} options={domainCodes.map(optionPair)} placeholder="All domains" />
              <SelectField label="Governance" value={filters.governance_status} onChange={(value) => setFilters({ ...filters, governance_status: value })} options={governanceStatuses.map(optionPair)} placeholder="All statuses" />
              <SelectField label="Review" value={filters.review_status} onChange={(value) => setFilters({ ...filters, review_status: value })} options={reviewStatuses.map(optionPair)} placeholder="Any review" />
              <SelectField label="Active" value={filters.active} onChange={(value) => setFilters({ ...filters, active: value })} options={activeOptions} placeholder="Any state" />
              <Field label="Search" value={filters.search} onChange={(value) => setFilters({ ...filters, search: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Reference Domains</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <DomainList items={items} /> : <EmptyState title="No reference data domains" body="Reference Data Engine metadata for this agency will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function DomainList({ items }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_180px_180px]">
              <div>
                <p className="font-semibold text-slate-950">{item.domain_display_name || item.domain_label || item.domain_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.domain_reference || item.id}</p>
              </div>
              <p className="text-xs text-slate-600">Domain: {formatType(item.domain_code)}</p>
              <p className="text-xs text-slate-600">Review: {formatType(item.review_status)}</p>
            </div>
          </summary>
          <DomainSections item={item} />
        </details>
      ))}
    </div>
  )
}

function DomainSections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <RecordCard title="Domain Overview" value={item.domain_summary} />
      <RecordCard title="Records" value={item.records_section} />
      <RecordCard title="Aliases" value={{ aliases: item.aliases }} />
      <RecordCard title="Normalization Rules" value={item.normalization_section} />
      <RecordCard title="Validation Rules" value={item.validation_section} />
      <RecordCard title="Governance" value={item.governance_section} />
      <RecordCard title="Production Readiness" value={item.production_readiness_section} />
      <RecordCard title="Boundaries" value={item.boundary_section} />
    </div>
  )
}
