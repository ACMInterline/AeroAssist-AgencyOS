import { useEffect, useMemo, useState } from "react"
import ClientForm from "../../components/ClientForm"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function ClientsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ search: "", client_type: "", status: "", portal_status: "" })
  const [showCreate, setShowCreate] = useState(false)
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const clients = context.agency ? await apiGet(`/api/agencies/${context.agency.id}/clients`) : { items: [] }
    setState({ ...context, clients: clients.items })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const filteredClients = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.clients || []).filter((client) => {
      const matchesSearch = !search || [client.display_name, client.legal_name, client.primary_email, client.city].some((value) => String(value || "").toLowerCase().includes(search))
      return matchesSearch
        && (!filters.client_type || client.client_type === filters.client_type)
        && (!filters.status || client.status === filters.status)
        && (!filters.portal_status || client.portal_status === filters.portal_status)
    })
  }, [filters, state])

  async function createClient(payload) {
    await apiPost(`/api/agencies/${state.agency.id}/clients`, payload)
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
              <h2 className="text-2xl font-semibold text-slate-950">Clients</h2>
              <p className="mt-1 text-sm text-slate-600">Commercial/account records for people, families, and organizations.</p>
            </div>
            <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" onClick={() => setShowCreate((value) => !value)}>
              {showCreate ? "Close form" : "Create client"}
            </button>
          </div>
          {showCreate ? <ClientForm onSubmit={createClient} submitLabel="Create client" /> : null}
          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-4">
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search clients" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.client_type} onChange={(event) => setFilters({ ...filters, client_type: event.target.value })}>
              <option value="">All client types</option>
              <option value="individual">Individual</option>
              <option value="family_household">Family / household</option>
              <option value="organization">Organization</option>
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="archived">Archived</option>
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.portal_status} onChange={(event) => setFilters({ ...filters, portal_status: event.target.value })}>
              <option value="">All portal states</option>
              <option value="no_portal_access">No portal access</option>
              <option value="invited">Invited</option>
              <option value="email_unverified">Email unverified</option>
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
              <option value="archived">Archived</option>
            </select>
          </section>
          {filteredClients.length ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {filteredClients.map((client) => (
                <a className="rounded-lg border border-slate-200 bg-white p-5 hover:border-blue-300" href={`/agency/clients/${client.id}`} key={client.id}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-slate-950">{client.display_name}</h3>
                      <p className="mt-1 text-sm text-slate-600">{client.primary_email}</p>
                    </div>
                    <StatusBadge status={client.status} />
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-600">
                    <span className="rounded-full bg-slate-100 px-2 py-1">{client.client_type.replaceAll("_", " ")}</span>
                    <span className="rounded-full bg-slate-100 px-2 py-1">{client.portal_status.replaceAll("_", " ")}</span>
                  </div>
                </a>
              ))}
            </div>
          ) : (
            <EmptyState title="No clients found" body="Create the first client account record before linking traveler profiles." />
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
