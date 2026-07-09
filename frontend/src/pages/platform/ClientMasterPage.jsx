import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, MasterRecordList, Metric, SelectField, optionPair, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
  search: "",
  status: "",
  portal_status: "",
  passenger: "",
}

const statuses = ["active", "in_review", "needs_review", "merged", "archived"]
const portalStatuses = ["no_portal_access", "invited", "active", "suspended", "archived"]

export default function ClientMasterPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/client-master${query}`),
    ])
    setState({ me, agencies: agencies.items || [], items: response.items || response.clients || [], summary: response.summary || {} })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.search, filters.status, filters.portal_status, filters.passenger])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const items = state?.items || []
  const summary = state?.summary || {}
  const metrics = [
    ["Clients", summary.client_master_record_count ?? items.length],
    ["Linked passengers", summary.client_master_linked_passenger_count || 0],
    ["Relationships", summary.client_passenger_link_count || 0],
    ["Portal profiles", summary.client_portal_access_profile_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Client Passenger Master</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Client Master</h2>
              <p className="mt-1 text-sm text-slate-600">Commercial owner metadata for client relationships, linked passengers, portal access, and operational references.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Commercial owner</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Client Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-5">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <Field label="Search" value={filters.search} onChange={(value) => setFilters({ ...filters, search: value })} />
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={statuses.map(optionPair)} placeholder="All statuses" />
              <SelectField label="Portal" value={filters.portal_status} onChange={(value) => setFilters({ ...filters, portal_status: value })} options={portalStatuses.map(optionPair)} placeholder="Any portal status" />
              <Field label="Passenger" value={filters.passenger} onChange={(value) => setFilters({ ...filters, passenger: value })} />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Clients</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
            </div>
            {items.length ? <MasterRecordList items={items} type="client" showAgency /> : <EmptyState title="No client master records" body="Client master metadata will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
