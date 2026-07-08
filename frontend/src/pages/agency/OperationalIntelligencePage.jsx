import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function OperationalIntelligencePage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const response = await apiGet(`/api/agencies/${context.agency.id}/airline-operational-intelligence`)
      setState({ ...context, ...response })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const architecture = state?.architecture || {}
  const sections = state?.sections || []
  const metrics = [
    ["Linked foundations", state?.summary?.linked_existing_foundation_count || 0],
    ["Future phases", state?.summary?.future_aoie_phase_count || 0],
    ["Excluded scopes", state?.summary?.excluded_scope_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Operational Intelligence</h2>
            <p className="mt-1 text-sm text-slate-600">Read-only AOIE architecture metadata for future passenger service decision support. This page does not run AI, scrape, call providers, search itineraries, book, ticket, issue EMDs, or automate recommendations.</p>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Passenger Service Operations Principle</p>
            <p className="mt-2 text-sm font-semibold text-slate-950">{architecture.principle || state?.summary?.passenger_service_operations_principle}</p>
            <p className="mt-3 text-sm text-slate-600">AOIE coordinates existing metadata foundations into future human-reviewed feasibility, risk, cost, and recommendation evidence. It does not replace agency workflows or operational workspaces.</p>
          </section>

          <section className="grid gap-3 md:grid-cols-3">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            {sections.length ? sections.map((section) => <SectionCard section={section} key={section.key} />) : <EmptyState title="No operational intelligence sections" body="AOIE architecture metadata will appear here when platform governance is available." />}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Excluded scope</h3>
            <div className="mt-4 flex flex-wrap gap-2">
              {(architecture.excluded_scope || []).map((item) => <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700" key={item}>{item}</span>)}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
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
