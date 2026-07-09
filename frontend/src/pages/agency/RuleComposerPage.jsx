import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, SelectField, formatType, optionPair, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaultFilters = {
  rule_family: "",
  service_family: "",
  service_code: "",
  lifecycle_status: "",
  severity: "",
  operator: "",
  search: "",
}

const ruleFamilies = ["passenger_assistance", "pets_animals", "medical", "documents", "seating_baggage", "special_items", "route_aircraft_cabin", "pricing", "refund_exchange", "after_sales"]
const lifecycleStatuses = ["draft", "in_review", "approved", "retired", "archived"]
const severities = ["info", "advisory", "warning", "conditional", "blocking", "manual_review"]
const operators = ["=", "!=", ">", ">=", "<", "<=", "in", "not_in", "contains", "exists", "not_exists", "between", "between_month_day", "date_before", "date_after", "route_includes_country", "route_crosses_border", "outside_range"]

export default function RuleComposerPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const response = await apiGet(`/api/agencies/${context.agency.id}/rule-composer${query}`)
    setState({ ...context, items: response.items || response.rules || [], summary: response.summary || {} })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.rule_family, filters.service_family, filters.service_code, filters.lifecycle_status, filters.severity, filters.operator, filters.search])

  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Rules", summary.operational_rule_composer_rule_count ?? items.length],
    ["Families", `${summary.covered_rule_family_count || 0}/${summary.supported_rule_family_count || ruleFamilies.length}`],
    ["Conditions", summary.total_condition_count || 0],
    ["Evidence", summary.evidence_link_count || 0],
    ["Messages", (summary.client_message_count || 0) + (summary.internal_message_count || 0)],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Rule Composer</h2>
              <p className="mt-1 text-sm text-slate-600">Agency operational compound rule metadata for airline passenger service restrictions and outcomes.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No execution</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Rule Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Rule Family" value={filters.rule_family} onChange={(value) => setFilters({ ...filters, rule_family: value })} options={ruleFamilies.map(optionPair)} placeholder="All families" />
              <Field label="Service Family" value={filters.service_family} onChange={(value) => setFilters({ ...filters, service_family: value })} />
              <Field label="Service Code" value={filters.service_code} onChange={(value) => setFilters({ ...filters, service_code: value })} />
              <SelectField label="Lifecycle" value={filters.lifecycle_status} onChange={(value) => setFilters({ ...filters, lifecycle_status: value })} options={lifecycleStatuses.map(optionPair)} placeholder="All statuses" />
              <SelectField label="Severity" value={filters.severity} onChange={(value) => setFilters({ ...filters, severity: value })} options={severities.map(optionPair)} placeholder="All severities" />
              <SelectField label="Operator" value={filters.operator} onChange={(value) => setFilters({ ...filters, operator: value })} options={operators.map(optionPair)} placeholder="Any operator" />
              <Field label="Search" value={filters.search} onChange={(value) => setFilters({ ...filters, search: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Rules</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <RuleList items={items} /> : <EmptyState title="No operational rules" body="Rule Composer metadata for this agency will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function RuleList({ items }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_190px_190px]">
              <div>
                <p className="font-semibold text-slate-950">{item.rule_display_name || item.rule_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.rule_reference || item.id}</p>
              </div>
              <p className="text-xs text-slate-600">Family: {formatType(item.rule_family)}</p>
              <div className="text-xs text-slate-600">
                <p>Severity: {formatType(item.severity)}</p>
                <p className="mt-1">Lifecycle: {formatType(item.lifecycle_status)}</p>
              </div>
            </div>
          </summary>
          <RuleSections item={item} />
        </details>
      ))}
    </div>
  )
}

function RuleSections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <RecordCard title="Overview" value={item.overview_section} />
      <RecordCard title="Applies To" value={item.applicability_section} />
      <RecordCard title="All Conditions" value={item.conditions_section} />
      <RecordCard title="Any Conditions" value={item.any_conditions_section} />
      <RecordCard title="Result" value={item.result_section} />
      <RecordCard title="Messages" value={item.messaging_section} />
      <RecordCard title="Evidence / Governance" value={item.evidence_governance_section} />
      <RecordCard title="Lifecycle" value={item.lifecycle_section} />
      <RecordCard title="Boundaries" value={item.boundary_section} />
    </div>
  )
}
