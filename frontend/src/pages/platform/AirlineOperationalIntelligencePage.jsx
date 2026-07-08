import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const base = "/api/platform/airline-operational-intelligence"

export default function AirlineOperationalIntelligencePage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const [me, response] = await Promise.all([
        apiGet("/api/auth/me"),
        apiGet(base),
      ])
      setState({ me, ...response })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const architecture = state?.architecture || {}
  const sections = state?.sections || []
  const metrics = [
    ["Architecture records", state?.summary?.architecture_record_count || 0],
    ["Linked foundations", state?.summary?.linked_existing_foundation_count || 0],
    ["Future AOIE phases", state?.summary?.future_aoie_phase_count || 0],
    ["Excluded scopes", state?.summary?.excluded_scope_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Airline Operational Intelligence</h2>
              <p className="mt-1 text-sm text-slate-600">AOIE is an architecture-only governance layer for future passenger service decision support. It does not run AI, scrape, call airline APIs, execute providers, search itineraries, recommend automatically, book, ticket, issue EMDs, or start workers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Architecture only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No execution</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{architecture.architecture_reference}</p>
            <h3 className="mt-2 text-lg font-semibold text-slate-950">Passenger Service Operations System</h3>
            <p className="mt-2 text-sm text-slate-700">{architecture.principle || state?.summary?.passenger_service_operations_principle}</p>
            <p className="mt-3 text-sm text-slate-600">{architecture.purpose}</p>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            {sections.length ? sections.map((section) => <SectionCard section={section} key={section.key} />) : <EmptyState title="No AOIE sections" body="Architecture metadata will appear here after the seed record is available." />}
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <ListPanel title="Linked existing foundations" items={architecture.linked_existing_foundations} />
            <ListPanel title="Future AOIE phase map" items={architecture.linked_future_phases} />
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
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

function SectionCard({ section }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{section.label}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-600">{section.body || "Metadata will be added in a future AOIE phase."}</p>
    </article>
  )
}

function ListPanel({ title, items }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{title}</h3>
      <div className="mt-4 grid gap-2">
        {(items || []).map((item) => <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700" key={item}>{item}</p>)}
      </div>
    </section>
  )
}
