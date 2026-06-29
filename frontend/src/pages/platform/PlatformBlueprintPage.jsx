import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

export default function PlatformBlueprintPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const [summary, adoption, routePolicy, gaps, nextPhases] = await Promise.all([
        apiGet("/api/platform/summary"),
        apiGet("/api/platform/blueprint/adoption-map"),
        apiGet("/api/platform/blueprint/route-policy"),
        apiGet("/api/platform/blueprint/gaps"),
        apiGet("/api/platform/blueprint/next-phases"),
      ])
      setState({ summary, adoption, routePolicy, gaps, nextPhases })
    }
    load().catch((err) => setError(err.message))
  }, [])

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header className="rounded-lg border border-slate-200 bg-white p-6">
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Blueprint Sync</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Supplementary Blueprint Adoption</h2>
            <p className="mt-1 text-sm text-slate-600">Governance map for adopted, deferred, and rejected structures. AgencyOS keeps /platform and /agency as canonical route roots.</p>
          </header>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Supplementary Blueprint Adoption Map</h3>
            <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
              <div className="grid grid-cols-[0.8fr_1fr_1.5fr_0.8fr_1.4fr] gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <span>Category</span><span>Concept</span><span>Current AgencyOS equivalent</span><span>Status</span><span>Action</span>
              </div>
              <div className="divide-y divide-slate-100">
                {(state?.adoption?.items || []).map((item) => (
                  <div className="grid grid-cols-[0.8fr_1fr_1.5fr_0.8fr_1.4fr] gap-3 px-4 py-4 text-sm text-slate-700" key={`${item.category}-${item.concept}`}>
                    <span className="font-medium text-slate-950">{item.category}</span>
                    <span>{item.concept}</span>
                    <span>{item.current_equivalent}</span>
                    <StatusPill value={item.status} />
                    <span>{item.action}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Canonical Route Policy">
              <Rows items={state?.routePolicy?.canonical_routes || []} render={(item) => `${item.root} - ${item.purpose}`} />
              <div className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-800">
                {(state?.routePolicy?.rejected_routes || []).map((item) => <p key={item.root}>{item.root} rejected: {item.reason}</p>)}
              </div>
            </Panel>
            <Panel title="Route Mapping Examples">
              <Rows items={state?.routePolicy?.route_mappings || []} render={(item) => `${item.supplementary} -> ${item.agencyos}`} />
            </Panel>
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            <Panel title="Foundations Added Now"><Rows items={state?.gaps?.foundations_added_now || []} /></Panel>
            <Panel title="Deferred"><Rows items={state?.gaps?.deferred || []} /></Panel>
            <Panel title="Rejected"><Rows items={state?.gaps?.intentionally_rejected || []} /></Panel>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Next Phase Recommendations</h3>
            <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {(state?.nextPhases?.items || []).map((item) => (
                <article className="rounded-lg border border-slate-200 p-4" key={item.phase}>
                  <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">{item.phase}</p>
                  <h4 className="mt-1 font-semibold text-slate-950">{item.title}</h4>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{item.reason}</p>
                </article>
              ))}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Panel({ title, children }) {
  return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><div className="mt-4">{children}</div></section>
}

function Rows({ items, render }) {
  if (!items.length) return <EmptyState title="No items" body="No blueprint sync items were returned." />
  return (
    <div className="divide-y divide-slate-100 rounded-lg border border-slate-200">
      {items.map((item, index) => <p className="px-3 py-2 text-sm text-slate-700" key={typeof item === "string" ? item : index}>{render ? render(item) : item}</p>)}
    </div>
  )
}

function StatusPill({ value }) {
  return <span className="inline-flex w-fit rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{value}</span>
}
