import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import PassengerForm from "../../components/PassengerForm"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function PassengersPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ search: "", passenger_type: "", status: "" })
  const [showCreate, setShowCreate] = useState(false)
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const passengers = context.agency ? await apiGet(`/api/agencies/${context.agency.id}/passengers`) : { items: [] }
    setState({ ...context, passengers: passengers.items })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const filteredPassengers = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.passengers || []).filter((passenger) => {
      const matchesSearch = !search || [passenger.display_name, passenger.first_name, passenger.last_name, passenger.nationality].some((value) => String(value || "").toLowerCase().includes(search))
      return matchesSearch
        && (!filters.passenger_type || passenger.passenger_type === filters.passenger_type)
        && (!filters.status || passenger.status === filters.status)
    })
  }, [filters, state])

  async function createPassenger(payload) {
    const cleanPayload = Object.fromEntries(Object.entries(payload).filter(([, value]) => value !== ""))
    await apiPost(`/api/agencies/${state.agency.id}/passengers`, cleanPayload)
    setShowCreate(false)
    await load()
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">CRM Foundation</p>
              <h2 className="text-2xl font-semibold text-slate-950">Passengers</h2>
              <p className="mt-1 text-sm text-slate-600">Traveler profiles with PTC, documents, assistance needs, and client relationships.</p>
            </div>
            <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" onClick={() => setShowCreate((value) => !value)}>
              {showCreate ? "Close form" : "Create passenger"}
            </button>
          </div>
          {showCreate ? <PassengerForm onSubmit={createPassenger} submitLabel="Create passenger" /> : null}
          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-3">
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search passengers" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.passenger_type} onChange={(event) => setFilters({ ...filters, passenger_type: event.target.value })}>
              <option value="">All PTCs</option>
              {["ADT", "CHD", "INF", "YTH", "SRC", "STU", "UMNR", "INS", "other"].map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="archived">Archived</option>
              <option value="duplicate_merged">Duplicate merged</option>
            </select>
          </section>
          {filteredPassengers.length ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {filteredPassengers.map((passenger) => (
                <a className="rounded-lg border border-slate-200 bg-white p-5 hover:border-blue-300" href={`/agency/passengers/${passenger.id}`} key={passenger.id}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-slate-950">{passenger.display_name}</h3>
                      <p className="mt-1 text-sm text-slate-600">{passenger.passenger_type} · born {passenger.date_of_birth}</p>
                    </div>
                    <StatusBadge status={passenger.status} />
                  </div>
                  <p className="mt-4 text-sm text-slate-600">{passenger.nationality || "Nationality not set"} / {passenger.residence_country || "Residence not set"}</p>
                </a>
              ))}
            </div>
          ) : (
            <EmptyState title="No passengers found" body="Create traveler profiles separately from client account records." />
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
