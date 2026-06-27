import { useEffect, useMemo, useState } from "react"
import Columns3 from "lucide-react/dist/esm/icons/columns-3.js"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import Search from "lucide-react/dist/esm/icons/search.js"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statuses = ["draft", "in_review", "shared", "accepted", "rejected", "expired", "archived"]

export default function OfferWorkspacesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ search: "", status: "" })
  const [form, setForm] = useState({ title: "", currency: "EUR", request_id: "", trip_id: "" })
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const [workspaces, requests, trips] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/offer-workspaces`),
      apiGet(`/api/agencies/${context.agency.id}/requests`),
      apiGet(`/api/agencies/${context.agency.id}/trips`),
    ])
    setState({ ...context, workspaces: workspaces.items || [], requests: requests.items || [], trips: trips.items || [] })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const filtered = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.workspaces || []).filter((workspace) => {
      const haystack = [
        workspace.title,
        workspace.status,
        workspace.currency,
        workspace.request?.request_reference,
        workspace.request?.title,
        workspace.trip?.trip_reference,
        workspace.trip?.trip_title,
      ]
      return (!search || haystack.some((value) => String(value || "").toLowerCase().includes(search))) && (!filters.status || workspace.status === filters.status)
    })
  }, [filters, state])

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function createWorkspace(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      const payload = {
        title: form.title || "New offer workspace",
        currency: form.currency || "EUR",
        request_id: form.request_id || null,
        trip_id: form.trip_id || null,
      }
      const result = await apiPost(`/api/agencies/${state.agency.id}/offer-workspaces`, payload)
      window.location.href = `/agency/offers/${result.workspace.id}/builder`
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offers</p>
                <h2 className="text-3xl font-semibold tracking-tight text-slate-950">Offer Workspaces</h2>
                <p className="mt-1 text-sm text-slate-600">Internal option building, rule checks, and comparison matrices.</p>
              </div>
              <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                <Columns3 className="h-3.5 w-3.5" />
                {filtered.length} shown
              </span>
            </div>
          </div>

          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createWorkspace}>
              <h3 className="font-semibold text-slate-950">Create Workspace</h3>
              <Field label="Title">
                <input value={form.title} onChange={(event) => setField("title", event.target.value)} placeholder="Offer workspace title" />
              </Field>
              <Field label="Currency">
                <input value={form.currency} onChange={(event) => setField("currency", event.target.value.toUpperCase())} maxLength={3} />
              </Field>
              <Field label="Request">
                <select value={form.request_id} onChange={(event) => setField("request_id", event.target.value)}>
                  <option value="">No request link</option>
                  {(state?.requests || []).map((request) => <option value={request.id} key={request.id}>{request.request_reference} - {request.title}</option>)}
                </select>
              </Field>
              <Field label="Trip">
                <select value={form.trip_id} onChange={(event) => setField("trip_id", event.target.value)}>
                  <option value="">No trip link</option>
                  {(state?.trips || []).map((trip) => <option value={trip.id} key={trip.id}>{trip.trip_reference} - {trip.trip_title}</option>)}
                </select>
              </Field>
              <button className="aa-primary-action inline-flex w-full items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-semibold" type="submit">
                <Plus className="h-4 w-4" />
                Create
              </button>
            </form>

            <div className="space-y-4">
              <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-[minmax(0,1fr)_220px]">
                <label className="relative">
                  <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input className="w-full rounded-md border border-slate-300 py-2 pl-9 pr-3 text-sm" placeholder="Search workspaces" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
                </label>
                <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
                  <option value="">All statuses</option>
                  {statuses.map((status) => <option value={status} key={status}>{status.replaceAll("_", " ")}</option>)}
                </select>
              </section>

              {filtered.length ? (
                <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
                  <div className="grid grid-cols-[1.2fr_1fr_1fr_120px_120px] gap-3 border-b border-slate-100 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 max-lg:hidden">
                    <span>Workspace</span><span>Request</span><span>Trip</span><span>Options</span><span>Updated</span>
                  </div>
                  <div className="divide-y divide-slate-100">
                    {filtered.map((workspace) => <WorkspaceRow workspace={workspace} key={workspace.id} />)}
                  </div>
                </div>
              ) : (
                <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8">
                  <EmptyState title="No offer workspaces found" body="Create a workspace from a request, a trip, or manual research." />
                </div>
              )}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function WorkspaceRow({ workspace }) {
  return (
    <a className="grid gap-3 px-4 py-4 hover:bg-slate-50 lg:grid-cols-[1.2fr_1fr_1fr_120px_120px]" href={`/agency/offers/${workspace.id}`}>
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{workspace.status?.replaceAll("_", " ")} · {workspace.currency}</p>
        <h3 className="font-semibold text-slate-950">{workspace.title}</h3>
      </div>
      <p className="text-sm text-slate-600">{workspace.request ? `${workspace.request.request_reference} - ${workspace.request.title}` : "No request"}</p>
      <p className="text-sm text-slate-600">{workspace.trip ? `${workspace.trip.trip_reference} - ${workspace.trip.trip_title}` : "No trip"}</p>
      <p className="text-sm text-slate-600">{workspace.option_count || 0}</p>
      <p className="text-xs text-slate-500">{String(workspace.updated_at || workspace.created_at || "").slice(0, 10)}</p>
    </a>
  )
}

function Field({ label, children }) {
  return (
    <label className="grid gap-1 text-sm font-medium text-slate-700">
      {label}
      {children.type === "select"
        ? <select {...children.props} className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" />
        : <input {...children.props} className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" />}
    </label>
  )
}
