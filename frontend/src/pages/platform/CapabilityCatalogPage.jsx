import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const base = "/api/platform/capabilities"

export default function PlatformCapabilityCatalogPage() {
  const [state, setState] = useState(null)
  const [search, setSearch] = useState("")
  const [category, setCategory] = useState("")
  const [module, setModule] = useState("")
  const [selectedCode, setSelectedCode] = useState("")
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const [me, capabilities, categories, modules] = await Promise.all([
        apiGet("/api/auth/me"),
        apiGet(base),
        apiGet(`${base}/categories`),
        apiGet(`${base}/modules`),
      ])
      const items = capabilities.items || []
      setState({
        me,
        capabilities: items,
        categories: categories.items || [],
        modules: modules.items || [],
      })
      setSelectedCode(items[0]?.code || "")
    }
    load().catch((err) => setError(err.message))
  }, [])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    return (state?.capabilities || []).filter((item) => {
      const text = [item.code, item.name, item.description, item.category, item.module, ...(item.tags || [])].join(" ").toLowerCase()
      return (!term || text.includes(term)) && (!category || item.category === category) && (!module || item.module === module)
    })
  }, [state, search, category, module])

  const selected = filtered.find((item) => item.code === selectedCode) || filtered[0]
  const metrics = [
    ["Capabilities", state?.capabilities?.length || 0],
    ["Categories", state?.categories?.length || 0],
    ["Modules", state?.modules?.length || 0],
    ["Deprecated", state?.capabilities?.filter((item) => item.deprecated).length || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Platform</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Platform Capability Catalog</h2>
              <p className="mt-1 text-sm text-slate-600">Capabilities are metadata only. They reference feature flags, bundles, routes, dependencies, and documentation without enforcement.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No enforcement</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 lg:grid-cols-[1fr_220px_220px]">
            <label className="grid gap-1 text-sm">
              <span className="font-medium text-slate-700">Search</span>
              <input className="rounded-md border border-slate-300 px-3 py-2" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search capabilities" />
            </label>
            <SelectFilter label="Category" value={category} onChange={setCategory} options={(state?.categories || []).map((item) => item.category)} />
            <SelectFilter label="Module" value={module} onChange={setModule} options={(state?.modules || []).map((item) => item.module)} />
          </section>

          <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
            <section className="rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-200 p-4">
                <h3 className="font-semibold text-slate-950">Capability inventory</h3>
              </div>
              {filtered.length ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-100 text-left text-sm">
                    <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      <tr>
                        <th className="px-4 py-3">Capability</th>
                        <th className="px-4 py-3">Category</th>
                        <th className="px-4 py-3">Module</th>
                        <th className="px-4 py-3">Feature Flags</th>
                        <th className="px-4 py-3">Bundles</th>
                        <th className="px-4 py-3">Dependencies</th>
                        <th className="px-4 py-3">Docs</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {filtered.map((item) => (
                        <tr className={selected?.code === item.code ? "bg-blue-50/50" : ""} key={item.code}>
                          <td className="px-4 py-3">
                            <button className="text-left font-semibold text-slate-950" type="button" onClick={() => setSelectedCode(item.code)}>{item.name}</button>
                            <p className="mt-1 text-xs text-slate-500">{item.code}</p>
                          </td>
                          <td className="px-4 py-3 text-slate-600">{titleize(item.category)}</td>
                          <td className="px-4 py-3 text-slate-600">{titleize(item.module)}</td>
                          <td className="px-4 py-3"><ChipList items={item.required_feature_flags} empty="None" /></td>
                          <td className="px-4 py-3"><ChipList items={[...(item.required_bundles || []), ...(item.recommended_bundles || [])]} empty="None" /></td>
                          <td className="px-4 py-3 text-slate-600">{item.dependency_count || 0}</td>
                          <td className="px-4 py-3 text-slate-600">{item.documentation_count || 0}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : <EmptyState title="No capabilities" body="Capability metadata matching the filters will appear here." />}
            </section>

            <section className="rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-200 p-4">
                <h3 className="font-semibold text-slate-950">Dependency view</h3>
              </div>
              {selected ? <CapabilityDetail item={selected} /> : <EmptyState title="Select a capability" body="Choose a row to inspect metadata references." />}
            </section>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function CapabilityDetail({ item }) {
  return (
    <div className="space-y-4 p-4 text-sm">
      <div>
        <p className="font-semibold text-slate-950">{item.name}</p>
        <p className="mt-1 text-slate-600">{item.description || "Capability metadata."}</p>
      </div>
      <DetailBlock label="Required Feature Flags" items={item.required_feature_flags} />
      <DetailBlock label="Required Bundles" items={item.required_bundles} />
      <DetailBlock label="Recommended Bundles" items={item.recommended_bundles} />
      <DetailBlock label="Dependencies" items={item.dependencies} />
      <DetailBlock label="UI Routes" items={item.ui_routes} mono />
      <DetailBlock label="Documentation Links" items={item.documentation_links} mono />
      {item.notes ? <p className="rounded-lg bg-slate-50 p-3 text-slate-600">{item.notes}</p> : null}
    </div>
  )
}

function DetailBlock({ label, items = [], mono = false }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {items.length ? items.map((item) => <span className={`rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200 ${mono ? "font-mono" : ""}`} key={`${label}-${item}`}>{item}</span>) : <span className="text-sm text-slate-500">None</span>}
      </div>
    </div>
  )
}

function SelectFilter({ label, value, onChange, options }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <select className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">All</option>
        {options.map((option) => <option value={option} key={option}>{titleize(option)}</option>)}
      </select>
    </label>
  )
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

function titleize(value) {
  if (!value) return "Metadata"
  return String(value).replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase())
}
