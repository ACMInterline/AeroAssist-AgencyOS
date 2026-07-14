import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
  status: "",
  booking_mode: "",
  trip_id: "",
  offer_workspace_id: "",
}

export default function BookingHandoffDiagnosticsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/booking-handoffs${query}`),
    ])
    setState({ me, agencies: agencies.items || [], ...response })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.status, filters.booking_mode, filters.trip_id, filters.offer_workspace_id])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const summary = state?.summary || {}

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations Governance</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Booking Handoff Diagnostics</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only platform visibility into accepted-offer to booking handoff metadata. This does not create bookings, call providers, issue tickets, process payments, or act as agency staff.</p>
            </div>
            <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Read-only diagnostics</span>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            <Metric label="Handoffs" value={summary.handoff_count || 0} />
            <Metric label="Blocked" value={summary.blocked_count || 0} />
            <Metric label="Conditional" value={summary.conditional_count || 0} />
            <Metric label="Ready" value={summary.ready_count || 0} />
            <Metric label="Instructions" value={summary.instruction_count || 0} />
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Filters</h3>
            <div className="mt-4 grid gap-3 md:grid-cols-5">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={[["", "All agencies"], ...agencyOptions]} />
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={["", "blocked", "conditional", "ready", "booking_created"].map((value) => [value, value ? formatType(value) : "All statuses"])} />
              <SelectField label="Mode" value={filters.booking_mode} onChange={(value) => setFilters({ ...filters, booking_mode: value })} options={["", "manual", "pnr_import", "imported_gds", "imported_confirmation", "supplier_reference"].map((value) => [value, value ? formatType(value) : "All modes"])} />
              <TextField label="Trip id" value={filters.trip_id} onChange={(value) => setFilters({ ...filters, trip_id: value })} />
              <TextField label="Offer workspace id" value={filters.offer_workspace_id} onChange={(value) => setFilters({ ...filters, offer_workspace_id: value })} />
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Recent handoffs</h3>
            {!state?.items?.length ? <EmptyState title="No handoffs" body="Agency booking handoff metadata will appear here." /> : (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
                      {["Reference", "Agency", "Status", "Mode", "Warnings", "Blockers", "Booking"].map((label) => <th className="px-3 py-2" key={label}>{label}</th>)}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {state.items.map((item) => (
                      <tr key={item.id}>
                        <td className="px-3 py-2 font-semibold text-slate-950">{item.handoff_reference}</td>
                        <td className="px-3 py-2 text-slate-700">{item.agency_id}</td>
                        <td className="px-3 py-2 text-slate-700">{formatType(item.handoff_status)}</td>
                        <td className="px-3 py-2 text-slate-700">{formatType(item.booking_mode)}</td>
                        <td className="px-3 py-2 text-slate-700">{item.warning_count || 0}</td>
                        <td className="px-3 py-2 text-slate-700">{item.blocker_count || 0}</td>
                        <td className="px-3 py-2 text-slate-700">{item.booking_workspace_id || "not created"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div>
}

function TextField({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<input className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function SelectField({ label, value, onChange, options }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<select className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)}>{options.map(([option, text]) => <option value={option} key={option}>{text}</option>)}</select></label>
}

function queryString(values) {
  const params = new URLSearchParams()
  Object.entries(values || {}).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const text = params.toString()
  return text ? `?${text}` : ""
}

function formatType(value) {
  if (value === null || value === undefined || value === "") return "Not set"
  return String(value).replaceAll("_", " ")
}
