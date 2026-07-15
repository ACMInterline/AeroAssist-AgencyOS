import { useEffect, useMemo, useState } from "react"
import GitBranch from "lucide-react/dist/esm/icons/git-branch.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import ShieldCheck from "lucide-react/dist/esm/icons/shield-check.js"
import TriangleAlert from "lucide-react/dist/esm/icons/triangle-alert.js"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const initialFilters = { agency_id: "", status: "", source_entity_type: "" }

export default function JourneyEnginePage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(initialFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, dashboard] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/journey-engine${query}`),
    ])
    setState({ me, agencies: agencies.items || [], ...dashboard })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id])

  const visible = useMemo(() => (state?.items || []).filter((item) => {
    if (filters.status && item.status !== filters.status) return false
    if (filters.source_entity_type && item.source_entity_type !== filters.source_entity_type) return false
    return true
  }), [state?.items, filters.status, filters.source_entity_type])

  const summary = state?.summary || {}
  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase text-blue-700">Journey Governance</p>
              <h1 className="mt-2 text-2xl font-semibold text-slate-950">Journey Engine</h1>
              <p className="mt-1 max-w-4xl text-sm text-slate-600">Diagnostic visibility over canonical journey projections. Trip, Offer, Booking, Ticket, EMD, Passenger, and segment records remain source truth; this view performs no shopping, pricing, provider execution, or publication.</p>
            </div>
            <button type="button" title="Refresh journeys" onClick={() => load().catch((err) => setError(err.message))} className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-300 bg-white text-slate-700"><RefreshCw className="h-4 w-4" /></button>
          </header>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
            <Metric label="Journeys" value={summary.journey_count} />
            <Metric label="Options" value={summary.itinerary_option_count} />
            <Metric label="Segments" value={summary.journey_segment_count} />
            <Metric label="Connections" value={summary.connection_count} />
            <Metric label="Snapshots" value={summary.snapshot_count} />
            <Metric label="Manual review" value={summary.manual_review_journey_count} tone="warning" />
          </section>

          <section className="grid gap-3 border-y border-slate-200 py-4 md:grid-cols-3">
            <Select label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={(state?.agencies || []).map((item) => [item.id, item.name || item.slug || item.id])} placeholder="All agencies" />
            <Select label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={(state?.filters?.statuses || []).map((item) => [item, title(item)])} placeholder="All statuses" />
            <Select label="Source" value={filters.source_entity_type} onChange={(value) => setFilters({ ...filters, source_entity_type: value })} options={Object.keys(summary.source_type_counts || {}).map((item) => [item, title(item)])} placeholder="All source types" />
          </section>

          {visible.length ? (
            <section className="overflow-x-auto border-y border-slate-200">
              <table className="w-full min-w-[900px] text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-3">Journey</th><th className="px-3 py-3">Agency</th><th className="px-3 py-3">Source</th><th className="px-3 py-3">Route</th><th className="px-3 py-3">Status</th><th className="px-3 py-3">Completeness</th><th className="px-3 py-3">Version</th></tr></thead>
                <tbody>{visible.map((item) => <tr className="border-t border-slate-200" key={item.id}>
                  <td className="px-3 py-4"><div className="flex items-start gap-2"><GitBranch className="mt-0.5 h-4 w-4 text-blue-700" /><div><p className="font-semibold text-slate-950">{item.title}</p><p className="mt-1 text-xs text-slate-500">{item.journey_reference}</p></div></div></td>
                  <td className="px-3 py-4 text-slate-600">{agencyName(state?.agencies, item.agency_id)}</td>
                  <td className="px-3 py-4"><p>{title(item.source_entity_type)}</p><p className="mt-1 text-xs text-slate-500">Referenced, not copied as source truth</p></td>
                  <td className="px-3 py-4 font-semibold">{item.origin_airport_code || "Unknown"} → {item.destination_airport_code || "Unknown"}</td>
                  <td className="px-3 py-4"><Badge value={item.presentation_status || item.status} /></td>
                  <td className="px-3 py-4"><div className="flex items-center gap-2">{item.manual_review_required ? <TriangleAlert className="h-4 w-4 text-amber-700" /> : <ShieldCheck className="h-4 w-4 text-emerald-700" />}<span>{item.completeness_score || 0}%</span></div></td>
                  <td className="px-3 py-4">v{item.current_version_number || 0}</td>
                </tr>)}</tbody>
              </table>
            </section>
          ) : <EmptyState title="No journey representations" body="Journey projections will appear here after an agency creates them from canonical operational records." />}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Metric({ label, value = 0, tone }) {
  return <div className={`rounded-md border p-4 ${tone === "warning" ? "border-amber-200 bg-amber-50" : "border-slate-200 bg-white"}`}><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value || 0}</p></div>
}

function Select({ label, value, onChange, options, placeholder }) {
  return <label className="grid gap-1 text-sm"><span className="font-medium text-slate-700">{label}</span><select className="rounded-md border border-slate-300 bg-white px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}><option value="">{placeholder}</option>{options.map(([key, text]) => <option value={key} key={key}>{text}</option>)}</select></label>
}

function Badge({ value }) {
  return <span className="inline-flex rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700 ring-1 ring-blue-200">{title(value)}</span>
}

function queryString(filters) {
  const params = new URLSearchParams()
  if (filters.agency_id) params.set("agency_id", filters.agency_id)
  return params.toString() ? `?${params}` : ""
}

function title(value) {
  return String(value || "Unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function agencyName(agencies, agencyId) {
  const agency = (agencies || []).find((item) => item.id === agencyId)
  return agency?.name || agency?.slug || "Agency unavailable"
}
