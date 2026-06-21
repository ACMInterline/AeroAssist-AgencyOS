import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import OfferStatusBadge from "../../components/OfferStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function OffersPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ search: "", status: "", source: "", client_id: "" })
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const offers = await apiGet(`/api/agencies/${context.agency.id}/offers`)
      const clients = await apiGet(`/api/agencies/${context.agency.id}/clients`)
      setState({ ...context, offers: offers.items, clients: clients.items })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const filtered = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.offers || []).filter((offer) => {
      const matchesSearch = !search || [offer.offer_reference, offer.title, offer.client?.display_name].some((value) => String(value || "").toLowerCase().includes(search))
      return matchesSearch
        && (!filters.status || offer.status === filters.status)
        && (!filters.source || offer.source === filters.source)
        && (!filters.client_id || offer.client_id === filters.client_id)
    })
  }, [filters, state])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Manual Offer Builder</p>
              <h2 className="text-2xl font-semibold text-slate-950">Offers</h2>
              <p className="mt-1 text-sm text-slate-600">Manually researched options. No live fare search or booking automation.</p>
            </div>
            <a className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" href="/agency/offers/new">Create offer</a>
          </div>
          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-4">
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search offers" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">All statuses</option>
              {["draft", "ready_to_send", "sent", "viewed", "accepted", "rejected", "expired", "withdrawn", "archived"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.source} onChange={(event) => setFilters({ ...filters, source: event.target.value })}>
              <option value="">All sources</option>
              {["request", "client_profile", "passenger_profile", "airline_research", "manual", "imported_gds_text", "other"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.client_id} onChange={(event) => setFilters({ ...filters, client_id: event.target.value })}>
              <option value="">All clients</option>
              {state?.clients?.map((client) => <option key={client.id} value={client.id}>{client.display_name}</option>)}
            </select>
          </section>
          {filtered.length ? (
            <div className="grid gap-4">
              {filtered.map((offer) => (
                <a className="rounded-lg border border-slate-200 bg-white p-5 hover:border-blue-300" href={`/agency/offers/${offer.id}`} key={offer.id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{offer.offer_reference}</p>
                      <h3 className="mt-1 font-semibold text-slate-950">{offer.title}</h3>
                      <p className="mt-1 text-sm text-slate-600">{offer.client?.display_name || "Client"} · {offer.source.replaceAll("_", " ")}</p>
                    </div>
                    <OfferStatusBadge status={offer.status} />
                  </div>
                  <div className="mt-4 grid gap-2 text-sm text-slate-600 md:grid-cols-4">
                    <span>Routes: {offer.route_alternative_count}</span>
                    <span>Fare options: {offer.fare_option_count}</span>
                    <span>Min: {offer.total_min_amount ?? "n/a"} {offer.currency}</span>
                    <span>Max: {offer.total_max_amount ?? "n/a"} {offer.currency}</span>
                  </div>
                </a>
              ))}
            </div>
          ) : (
            <EmptyState title="No offers found" body="Create a manual offer from a request, client profile, passenger profile, or staff research." />
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
