import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, SelectField, formatType, optionPair, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaultFilters = {
  scenario_family: "",
  test_status: "",
  airline_code: "",
  service_code: "",
  expected_recommendation_level: "",
  search: "",
}

const scenarioFamilies = ["petc", "avih", "svan", "exst_passenger_of_size", "cbbg", "wchc", "medif", "poc", "umnr", "musical_instrument", "sports_equipment", "restricted_equipment"]
const testStatuses = ["draft", "ready_for_review", "reviewed", "approved", "needs_update", "archived"]
const recommendationLevels = ["highly_recommended", "recommended", "acceptable", "use_with_caution", "not_recommended", "not_applicable"]

export default function ScenarioTestingPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const response = await apiGet(`/api/agencies/${context.agency.id}/operational-scenario-testing${query}`)
    setState({ ...context, items: response.items || response.scenarios || [], summary: response.summary || {} })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.scenario_family, filters.test_status, filters.airline_code, filters.service_code, filters.expected_recommendation_level, filters.search])

  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Scenarios", summary.operational_scenario_test_count ?? items.length],
    ["Active", summary.active_scenario_test_count || 0],
    ["Evidence Links", summary.evidence_link_count || 0],
    ["Required Actions", summary.expected_required_action_count || 0],
    ["Documents", summary.document_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Scenario Testing</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only passenger service scenario metadata. These examples do not run providers, AI, parser execution, workers, or automated evaluation.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Scenario Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Family" value={filters.scenario_family} onChange={(value) => setFilters({ ...filters, scenario_family: value })} options={scenarioFamilies.map(optionPair)} placeholder="All families" />
              <SelectField label="Status" value={filters.test_status} onChange={(value) => setFilters({ ...filters, test_status: value })} options={testStatuses.map(optionPair)} placeholder="All statuses" />
              <Field label="Airline" value={filters.airline_code} onChange={(value) => setFilters({ ...filters, airline_code: value })} />
              <Field label="Service Code" value={filters.service_code} onChange={(value) => setFilters({ ...filters, service_code: value })} />
              <SelectField label="Expected Recommendation" value={filters.expected_recommendation_level} onChange={(value) => setFilters({ ...filters, expected_recommendation_level: value })} options={recommendationLevels.map(optionPair)} placeholder="Any level" />
              <Field label="Search" value={filters.search} onChange={(value) => setFilters({ ...filters, search: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Scenario Test Cases</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <ScenarioList items={items} /> : <EmptyState title="No scenario tests" body="Scenario test metadata for this agency will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function ScenarioList({ items }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_190px_190px]">
              <div>
                <p className="font-semibold text-slate-950">{item.scenario_name || item.scenario_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.scenario_reference || item.id}</p>
              </div>
              <p className="text-xs text-slate-600">Family: {formatType(item.scenario_family)}</p>
              <div className="text-xs text-slate-600">
                <p>Status: {formatType(item.test_status)}</p>
                <p className="mt-1">Expected: {formatType(item.expected_recommendation_level)}</p>
              </div>
            </div>
          </summary>
          <ScenarioSections item={item} />
        </details>
      ))}
    </div>
  )
}

function ScenarioSections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <RecordCard title="Scenario" value={item.scenario_section} />
      <RecordCard title="Passenger Context" value={item.passenger_context_section} />
      <RecordCard title="Operational Context" value={item.operational_context_section} />
      <RecordCard title="Expected Outcomes" value={item.expected_outcome_section} />
      <RecordCard title="Evidence" value={item.evidence_section} />
      <RecordCard title="Review" value={item.review_section} />
      <RecordCard title="Boundaries" value={item.boundary_section} />
    </div>
  )
}
