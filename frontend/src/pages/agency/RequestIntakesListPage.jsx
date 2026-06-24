import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statuses = ["new", "triaged", "converted", "rejected", "duplicate", "archived"]

export default function RequestIntakesListPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ search: "", status: "" })
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const intakes = await apiGet(`/api/request-intakes${context.agency ? `?agency_id=${context.agency.id}` : ""}`)
      setState({ ...context, intakes: intakes.items })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const filtered = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.intakes || []).filter((intake) => {
      const contact = intake.contact_snapshot || {}
      const travel = intake.travel_summary || {}
      const matchesSearch = !search || [intake.reference_code, contact.name, contact.email, travel.origin, travel.destination].some((value) => String(value || "").toLowerCase().includes(search))
      return matchesSearch && (!filters.status || intake.status === filters.status)
    })
  }, [filters, state])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Request Intake</p>
              <h2 className="text-2xl font-semibold text-slate-950">Intake queue</h2>
              <p className="mt-1 text-sm text-slate-600">Public and portal submissions wait here until staff explicitly convert them.</p>
            </div>
            <a className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold" href="/agency/requests">Operational requests</a>
          </div>
          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-2">
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search intakes" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">All statuses</option>
              {statuses.map((status) => <option key={status} value={status}>{status.replaceAll("_", " ")}</option>)}
            </select>
          </section>
          {filtered.length ? (
            <div className="grid gap-4">
              {filtered.map((intake) => <IntakeCard intake={intake} key={intake.id} />)}
            </div>
          ) : (
            <EmptyState title="No intakes found" body="Public and portal submissions will appear here before operational conversion." />
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function IntakeCard({ intake }) {
  const contact = intake.contact_snapshot || {}
  const travel = intake.travel_summary || {}
  const services = intake.service_summary || {}
  const route = travel.origin && travel.destination ? `${travel.origin} → ${travel.destination}` : travel.itinerary_notes || "Route not set"
  return (
    <a className="rounded-lg border border-slate-200 bg-white p-5 hover:border-blue-300" href={`/agency/request-intakes/${intake.id}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{intake.reference_code}</p>
          <h3 className="mt-1 font-semibold text-slate-950">{contact.name || "Unnamed contact"}</h3>
          <p className="mt-1 text-sm text-slate-600">{route}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{intake.status}</span>
      </div>
      <div className="mt-4 grid gap-2 text-sm text-slate-600 md:grid-cols-4">
        <span>Priority: {intake.priority}</span>
        <span>Source: {intake.source?.replaceAll("_", " ")}</span>
        <span>Passengers: {travel.passenger_count || 1}</span>
        <span>Services: {(services.selected_service_categories || []).join(", ") || "review needed"}</span>
      </div>
    </a>
  )
}
