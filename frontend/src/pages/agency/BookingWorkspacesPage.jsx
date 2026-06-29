import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statuses = ["draft", "ready_to_book", "booking_in_progress", "booked", "blocked", "cancelled"]
const providers = ["manual", "travelport", "amadeus", "ndc", "supplier", "other"]

export default function BookingWorkspacesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ status: "", provider_target: "", search: "" })
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [selectedPackageId, setSelectedPackageId] = useState("")
  const [readinessLoading, setReadinessLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState("")
  const [createError, setCreateError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const query = new URLSearchParams()
    if (filters.status) query.set("status", filters.status)
    if (filters.provider_target) query.set("provider_target", filters.provider_target)
    const suffix = query.toString() ? `?${query.toString()}` : ""
    const [workspaces, readinessPackages] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/booking-workspaces${suffix}`),
      apiGet(`/api/agencies/${context.agency.id}/booking-readiness-packages`),
    ])
    const packages = readinessPackages.items || []
    setState({ ...context, workspaces: workspaces.items || [], readinessPackages: packages })
    setSelectedPackageId((current) => current && packages.some((item) => item.id === current) ? current : packages[0]?.id || "")
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [filters.status, filters.provider_target])

  const filtered = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.workspaces || []).filter((workspace) => {
      const record = workspace.booking_record || {}
      const trip = workspace.trip_summary || {}
      return !search || [
        workspace.workspace_number,
        workspace.title,
        trip.trip_reference,
        trip.trip_title,
        record.pnr_locator,
        workspace.request_id,
      ].some((value) => String(value || "").toLowerCase().includes(search))
    })
  }, [filters.search, state])

  const selectedPackage = useMemo(
    () => (state?.readinessPackages || []).find((item) => item.id === selectedPackageId),
    [selectedPackageId, state],
  )

  async function refreshReadinessPackages() {
    const agencyId = state?.agency?.id
    if (!agencyId) return
    setReadinessLoading(true)
    setCreateError("")
    try {
      const readinessPackages = await apiGet(`/api/agencies/${agencyId}/booking-readiness-packages`)
      const packages = readinessPackages.items || []
      setState((current) => current ? { ...current, readinessPackages: packages } : current)
      setSelectedPackageId((current) => current && packages.some((item) => item.id === current) ? current : packages[0]?.id || "")
    } catch (err) {
      setCreateError(err.message)
    } finally {
      setReadinessLoading(false)
    }
  }

  function openCreateModal() {
    setCreateModalOpen(true)
    setCreateError("")
    refreshReadinessPackages()
  }

  async function createOrOpenBookingWorkspace() {
    if (!selectedPackage) {
      setCreateError("Select a booking readiness package first.")
      return
    }
    if (selectedPackage.booking_workspace_already_exists && selectedPackage.booking_workspace_id) {
      window.location.href = `/agency/booking-workspaces/${selectedPackage.booking_workspace_id}`
      return
    }
    setCreating(true)
    setCreateError("")
    try {
      const payload = {
        booking_readiness_package_id: selectedPackage.id,
        create_draft_record: true,
        ...(selectedPackage.provider_target ? { provider_target: selectedPackage.provider_target } : {}),
      }
      const created = await apiPost(`/api/agencies/${state.agency.id}/booking-workspaces/from-readiness`, payload)
      window.location.href = `/agency/booking-workspaces/${created.booking_workspace.id}`
    } catch (err) {
      setCreateError(err.message)
      setCreating(false)
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="text-2xl font-semibold text-slate-950">Booking Workspaces</h2>
              <p className="mt-1 text-sm text-slate-600">Manual booking workspace and PNR mirror records created from booking readiness packages.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={openCreateModal}>Create booking workspace</button>
              <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/bookings">Legacy bookings</a>
            </div>
          </div>

          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-3">
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search workspace, trip, PNR" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">All statuses</option>
              {statuses.map((value) => <option value={value} key={value}>{label(value)}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.provider_target} onChange={(event) => setFilters({ ...filters, provider_target: event.target.value })}>
              <option value="">All providers</option>
              {providers.map((value) => <option value={value} key={value}>{label(value)}</option>)}
            </select>
          </section>

          {filtered.length ? (
            <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
              <div className="grid grid-cols-[1.2fr_1.3fr_0.9fr_0.9fr_0.8fr_0.8fr_0.8fr] gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <span>Workspace</span>
                <span>Trip / request</span>
                <span>Provider</span>
                <span>Status</span>
                <span>Booking</span>
                <span>Warnings</span>
                <span>Created</span>
              </div>
              <div className="divide-y divide-slate-100">
                {filtered.map((workspace) => (
                  <a className="grid grid-cols-[1.2fr_1.3fr_0.9fr_0.9fr_0.8fr_0.8fr_0.8fr] gap-3 px-4 py-4 text-sm text-slate-700 hover:bg-blue-50/60" href={`/agency/booking-workspaces/${workspace.id}`} key={workspace.id}>
                    <span>
                      <span className="block font-semibold text-slate-950">{workspace.workspace_number}</span>
                      <span className="block truncate text-xs text-slate-500">{workspace.title}</span>
                    </span>
                    <span>
                      <span className="block font-medium text-slate-900">{workspace.trip_summary?.trip_reference || workspace.trip_id}</span>
                      <span className="block truncate text-xs text-slate-500">{workspace.request_id || "No request link"}</span>
                    </span>
                    <span>{label(workspace.provider_target)}</span>
                    <span>{label(workspace.status)}</span>
                    <span>
                      <span className="block">{label(workspace.booking_record?.booking_status || "draft")}</span>
                      <span className="block text-xs text-slate-500">{workspace.booking_record?.pnr_locator || "PNR pending"}</span>
                    </span>
                    <span>{workspace.warning_count || 0}</span>
                    <span>{dateLabel(workspace.created_at)}</span>
                  </a>
                ))}
              </div>
            </div>
          ) : (
            <EmptyState title="No booking workspaces found" body="Create a booking workspace from an accepted offer booking readiness package.">
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={openCreateModal}>Create booking workspace</button>
            </EmptyState>
          )}

          {createModalOpen ? (
            <CreateBookingWorkspaceModal
              creating={creating}
              error={createError}
              loading={readinessLoading}
              onClose={() => setCreateModalOpen(false)}
              onSelect={setSelectedPackageId}
              onSubmit={createOrOpenBookingWorkspace}
              packages={state?.readinessPackages || []}
              selectedPackage={selectedPackage}
              selectedPackageId={selectedPackageId}
            />
          ) : null}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function CreateBookingWorkspaceModal({ creating, error, loading, onClose, onSelect, onSubmit, packages, selectedPackage, selectedPackageId }) {
  const actionLabel = selectedPackage?.booking_workspace_already_exists ? "Open booking workspace" : "Create booking workspace"
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">
      <section className="flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-lg bg-white shadow-xl">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 p-5">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Booking readiness</p>
            <h3 className="text-xl font-semibold text-slate-950">Create booking workspace</h3>
            <p className="mt-1 text-sm text-slate-600">Select an accepted offer booking readiness package. No live booking or provider action will run.</p>
          </div>
          <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={onClose}>Close</button>
        </div>
        <div className="overflow-y-auto p-5">
          {error ? <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {loading ? <p className="text-sm text-slate-600">Loading booking readiness packages...</p> : null}
          {!loading && packages.length ? (
            <div className="space-y-3">
              {packages.map((item) => (
                <button
                  className={`w-full rounded-lg border p-4 text-left transition ${selectedPackageId === item.id ? "border-blue-500 bg-blue-50" : "border-slate-200 bg-white hover:border-blue-300"}`}
                  key={item.id}
                  onClick={() => onSelect(item.id)}
                  type="button"
                >
                  <div className="grid gap-3 lg:grid-cols-[1.2fr_1.2fr_0.8fr_0.8fr_0.7fr_0.8fr]">
                    <SummaryBlock label="Trip" value={tripLabel(item)} subvalue={item.trip_summary?.trip_title || item.trip_id || "No trip summary"} />
                    <SummaryBlock label="Accepted offer / workspace" value={offerLabel(item)} subvalue={item.accepted_offer_summary?.id || item.acceptance_id || "No acceptance summary"} />
                    <SummaryBlock label="Provider" value={label(item.provider_target || "manual")} />
                    <SummaryBlock label="Status" value={label(item.status)} />
                    <SummaryBlock label="Warnings" value={String(item.warning_count || 0)} subvalue={`${item.policy_violation_count || 0} policy`} />
                    <SummaryBlock label="Created" value={dateLabel(item.created_at)} />
                  </div>
                  {item.booking_workspace_already_exists ? (
                    <div className="mt-3 rounded-md bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800">
                      Booking workspace already exists: {item.booking_workspace_summary?.workspace_number || item.booking_workspace_id}
                    </div>
                  ) : null}
                </button>
              ))}
            </div>
          ) : null}
          {!loading && !packages.length ? (
            <EmptyState title="No booking readiness packages found" body="Accept an offer option first so AgencyOS can create a booking readiness package." />
          ) : null}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 p-5">
          <p className="text-sm text-slate-600">{selectedPackage ? selectedPackage.id : "No package selected"}</p>
          <button className="aa-primary-action rounded-md px-4 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={onSubmit} disabled={!selectedPackage || creating}>
            {creating ? "Working..." : actionLabel}
          </button>
        </div>
      </section>
    </div>
  )
}

function SummaryBlock({ label: blockLabel, value, subvalue }) {
  return (
    <span className="min-w-0">
      <span className="block text-xs font-semibold uppercase tracking-wide text-slate-500">{blockLabel}</span>
      <span className="mt-1 block truncate text-sm font-semibold text-slate-950">{value || "Not set"}</span>
      {subvalue ? <span className="mt-1 block truncate text-xs text-slate-500">{subvalue}</span> : null}
    </span>
  )
}

function tripLabel(item) {
  const trip = item.trip_summary || {}
  return trip.trip_reference || trip.route_summary || item.trip_id || "Trip pending"
}

function offerLabel(item) {
  const workspace = item.offer_workspace_summary || item.workspace_summary || {}
  return workspace.title || workspace.id || item.workspace_id || "Offer workspace"
}

function label(value) {
  return String(value || "none").replaceAll("_", " ")
}

function dateLabel(value) {
  return value ? new Date(value).toLocaleDateString() : "Not set"
}
