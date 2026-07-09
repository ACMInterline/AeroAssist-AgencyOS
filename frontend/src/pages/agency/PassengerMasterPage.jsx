import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, MasterRecordList, Metric, SelectField, optionPair, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaultFilters = {
  search: "",
  status: "",
  service: "",
}

const statuses = ["active", "in_review", "needs_review", "merged", "archived"]

export default function PassengerMasterPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const response = await apiGet(`/api/agencies/${context.agency.id}/passenger-master${query}`)
    setState({ ...context, items: response.items || response.passengers || [], summary: response.summary || {} })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.search, filters.status, filters.service])

  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Passengers", summary.passenger_master_record_count ?? items.length],
    ["Reusable history", summary.passenger_master_reusable_history_count || 0],
    ["Known documents", summary.passenger_master_known_document_count || 0],
    ["Relationships", summary.client_passenger_link_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Passenger Master</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Passengers</h2>
              <p className="mt-1 text-sm text-slate-600">Reusable operational identity metadata for service history, preferences, documents, requests, trips, booking mirrors, tickets, EMDs, feasibility, and recommendations.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Operational identity</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Passenger Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-3">
              <Field label="Search" value={filters.search} onChange={(value) => setFilters({ ...filters, search: value })} />
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={statuses.map(optionPair)} placeholder="All statuses" />
              <Field label="Service" value={filters.service} onChange={(value) => setFilters({ ...filters, service: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Passenger Master Records</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <MasterRecordList items={items} type="passenger" /> : <EmptyState title="No passenger master records" body="Passenger operational identity metadata will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
