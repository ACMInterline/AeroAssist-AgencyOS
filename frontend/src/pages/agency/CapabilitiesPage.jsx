import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function CapabilitiesPage() {
  const [state, setState] = useState(null)
  const [status, setStatus] = useState("")
  const [search, setSearch] = useState("")
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const capabilities = await apiGet(`/api/agencies/${context.agency.id}/capabilities`)
      setState({
        ...context,
        capabilities: capabilities.items || [],
        summary: capabilities,
      })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    return (state?.capabilities || []).filter((item) => {
      const text = [item.name, item.code, item.category, item.module, ...(item.required_bundles || []), ...(item.required_feature_flags || [])].join(" ").toLowerCase()
      return (!status || item.informational_availability === status) && (!term || text.includes(term))
    })
  }, [state, status, search])

  const metrics = [
    ["Capabilities", state?.capabilities?.length || 0],
    ["Available", state?.summary?.availability_counts?.available || 0],
    ["Unavailable", state?.summary?.availability_counts?.unavailable || 0],
    ["Read-only", state?.summary?.read_only ? "Yes" : "No"],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Agency</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Available Capabilities</h2>
              <p className="mt-1 text-sm text-slate-600">Capability availability is informational only. No feature enforcement, route blocking, permission changes, or execution are performed.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No enable buttons</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-[1fr_220px]">
            <label className="grid gap-1 text-sm">
              <span className="font-medium text-slate-700">Search</span>
              <input className="rounded-md border border-slate-300 px-3 py-2" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search capabilities" />
            </label>
            <label className="grid gap-1 text-sm">
              <span className="font-medium text-slate-700">Status</span>
              <select className="rounded-md border border-slate-300 px-3 py-2" value={status} onChange={(event) => setStatus(event.target.value)}>
                <option value="">All</option>
                <option value="available">Available</option>
                <option value="unavailable">Unavailable</option>
              </select>
            </label>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-200 p-4">
              <h3 className="font-semibold text-slate-950">Capability metadata</h3>
            </div>
            {filtered.length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-100 text-left text-sm">
                  <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Capability</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Required Bundle</th>
                      <th className="px-4 py-3">Required Feature Flags</th>
                      <th className="px-4 py-3">Dependency Count</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filtered.map((item) => (
                      <tr key={item.code}>
                        <td className="px-4 py-3">
                          <p className="font-semibold text-slate-950">{item.name}</p>
                          <p className="mt-1 text-xs text-slate-500">{item.description || item.code}</p>
                        </td>
                        <td className="px-4 py-3"><AvailabilityBadge status={item.informational_availability} /></td>
                        <td className="px-4 py-3"><ChipList items={item.required_bundles} empty="None required" /></td>
                        <td className="px-4 py-3"><ChipList items={item.required_feature_flags} empty="None required" /></td>
                        <td className="px-4 py-3 text-slate-600">{item.dependency_count || 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <EmptyState title="No capabilities" body="Capability metadata matching the filters will appear here." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function AvailabilityBadge({ status }) {
  const available = status === "available"
  const classes = available ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-slate-100 text-slate-700 ring-slate-200"
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ring-1 ${classes}`}>{available ? "Available" : "Unavailable"}</span>
}

function ChipList({ items = [], empty }) {
  return (
    <div className="flex max-w-xs flex-wrap gap-1">
      {items.length ? items.slice(0, 3).map((item) => <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200" key={item}>{item}</span>) : <span className="text-slate-500">{empty}</span>}
      {items.length > 3 ? <span className="rounded-full bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700 ring-1 ring-blue-200">+{items.length - 3}</span> : null}
    </div>
  )
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}
