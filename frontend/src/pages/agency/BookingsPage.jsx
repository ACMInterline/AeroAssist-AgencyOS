import { useEffect, useMemo, useState } from "react"
import BookingStatusBadge from "../../components/BookingStatusBadge"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function BookingsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ search: "", status: "", channel: "", client_id: "" })
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const bookings = await apiGet(`/api/agencies/${context.agency.id}/bookings`)
      const clients = await apiGet(`/api/agencies/${context.agency.id}/clients`)
      setState({ ...context, bookings: bookings.items, clients: clients.items })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const filtered = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.bookings || []).filter((booking) => {
      const matchesSearch = !search || [booking.booking_reference, booking.pnr, booking.client?.display_name].some((value) => String(value || "").toLowerCase().includes(search))
      return matchesSearch
        && (!filters.status || booking.status === filters.status)
        && (!filters.channel || booking.booking_channel === filters.channel)
        && (!filters.client_id || booking.client_id === filters.client_id)
    })
  }, [filters, state])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="text-2xl font-semibold text-slate-950">Bookings</h2>
              <p className="mt-1 text-sm text-slate-600">Manual tracking only. Reservations and ticketing are issued externally.</p>
            </div>
            <a className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" href="/agency/bookings/new">Create booking</a>
          </div>
          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-4">
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search bookings" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">All statuses</option>
              {["draft", "pending_reservation", "reserved", "pending_payment", "paid", "ticketing_pending", "ticketed", "partially_ticketed", "completed", "cancelled", "archived"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.channel} onChange={(event) => setFilters({ ...filters, channel: event.target.value })}>
              <option value="">All channels</option>
              {["gds", "airline_portal", "ota_affiliate", "direct_airline_website", "supplier_email", "phone", "manual", "mixed"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.client_id} onChange={(event) => setFilters({ ...filters, client_id: event.target.value })}>
              <option value="">All clients</option>
              {state?.clients?.map((client) => <option key={client.id} value={client.id}>{client.display_name}</option>)}
            </select>
          </section>
          {filtered.length ? (
            <div className="grid gap-4">
              {filtered.map((booking) => (
                <a className="rounded-lg border border-slate-200 bg-white p-5 hover:border-blue-300" href={`/agency/bookings/${booking.id}`} key={booking.id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{booking.booking_reference}</p>
                      <h3 className="mt-1 font-semibold text-slate-950">{booking.client?.display_name || "Client"}</h3>
                      <p className="mt-1 text-sm text-slate-600">PNR {booking.pnr || "not set"} · {booking.booking_channel.replaceAll("_", " ")}</p>
                    </div>
                    <BookingStatusBadge status={booking.status} />
                  </div>
                  <div className="mt-4 grid gap-2 text-sm text-slate-600 md:grid-cols-4">
                    <span>Total: {booking.total_amount} {booking.currency}</span>
                    <span>Paid: {booking.amount_paid} {booking.currency}</span>
                    <span>Due: {booking.amount_due} {booking.currency}</span>
                    <span>Updated: {new Date(booking.updated_at).toLocaleDateString()}</span>
                  </div>
                </a>
              ))}
            </div>
          ) : (
            <EmptyState title="No bookings found" body="Create tracking records manually or from an accepted offer." />
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
