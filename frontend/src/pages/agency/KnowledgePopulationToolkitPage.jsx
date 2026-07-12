import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, SelectField, formatType, optionPair, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaultFilters = {
  airline_code: "",
  population_status: "",
  QA_status: "",
  publishing_status: "",
  scenario_test_status: "",
  owner: "",
  search: "",
}

const populationStatuses = ["draft", "onboarding", "reference_readiness", "template_readiness", "content_population", "qa_review", "publishing_readiness", "scenario_review", "ready", "blocked", "archived"]
const readinessStatuses = ["not_started", "in_progress", "ready", "needs_review", "blocked", "not_applicable"]

export default function KnowledgePopulationToolkitPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const response = await apiGet(`/api/agencies/${context.agency.id}/knowledge-population-toolkit${query}`)
    setState({ ...context, items: response.items || response.toolkits || [], summary: response.summary || {} })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.airline_code, filters.population_status, filters.QA_status, filters.publishing_status, filters.scenario_test_status, filters.owner, filters.search])

  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Toolkits", summary.knowledge_population_toolkit_count ?? items.length],
    ["Active", summary.active_toolkit_count || 0],
    ["Service Families", summary.service_family_coverage_count || 0],
    ["Blockers", summary.blocker_count || 0],
    ["Next Actions", summary.next_action_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Knowledge Population Toolkit</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only airline knowledge population readiness and coverage metadata. No scraping, auto-import, AI, provider calls, workers, or population jobs.</p>
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
            <h3 className="font-semibold text-slate-950">Toolkit Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <Field label="Airline" value={filters.airline_code} onChange={(value) => setFilters({ ...filters, airline_code: value })} />
              <SelectField label="Population Status" value={filters.population_status} onChange={(value) => setFilters({ ...filters, population_status: value })} options={populationStatuses.map(optionPair)} placeholder="All statuses" />
              <SelectField label="QA Status" value={filters.QA_status} onChange={(value) => setFilters({ ...filters, QA_status: value })} options={readinessStatuses.map(optionPair)} placeholder="Any QA status" />
              <SelectField label="Publishing Status" value={filters.publishing_status} onChange={(value) => setFilters({ ...filters, publishing_status: value })} options={readinessStatuses.map(optionPair)} placeholder="Any publishing status" />
              <SelectField label="Scenario Status" value={filters.scenario_test_status} onChange={(value) => setFilters({ ...filters, scenario_test_status: value })} options={readinessStatuses.map(optionPair)} placeholder="Any scenario status" />
              <Field label="Owner" value={filters.owner} onChange={(value) => setFilters({ ...filters, owner: value })} />
              <Field label="Search" value={filters.search} onChange={(value) => setFilters({ ...filters, search: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Population Toolkit Records</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <ToolkitList items={items} /> : <EmptyState title="No population toolkits" body="Knowledge population toolkit metadata for this agency will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function ToolkitList({ items }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[1fr_180px_190px]">
              <div>
                <p className="font-semibold text-slate-950">{item.airline_code || item.toolkit_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{item.toolkit_reference || item.id}</p>
              </div>
              <p className="text-xs text-slate-600">Owner: {item.owner || "Unassigned"}</p>
              <div className="text-xs text-slate-600">
                <p>Status: {formatType(item.population_status)}</p>
                <p className="mt-1">Scenario: {formatType(item.scenario_test_status)}</p>
              </div>
            </div>
          </summary>
          <ToolkitSections item={item} />
        </details>
      ))}
    </div>
  )
}

function ToolkitSections({ item }) {
  return (
    <div className="mt-4 grid gap-3 text-xs text-slate-600 lg:grid-cols-2">
      <RecordCard title="Toolkit" value={item.toolkit_section} />
      <RecordCard title="Readiness" value={item.readiness_section} />
      <RecordCard title="Coverage" value={item.coverage_section} />
      <RecordCard title="QA / Publishing / Scenarios" value={item.quality_release_section} />
      <RecordCard title="Actions" value={item.actions_section} />
      <RecordCard title="Review" value={item.review_section} />
      <RecordCard title="Boundaries" value={item.boundary_section} />
    </div>
  )
}
