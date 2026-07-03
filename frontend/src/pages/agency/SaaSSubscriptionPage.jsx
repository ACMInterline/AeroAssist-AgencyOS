import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function SaaSSubscriptionPage() {
  const [state, setState] = useState(null)
  const [selectedAssignmentId, setSelectedAssignmentId] = useState("")
  const [error, setError] = useState("")

  async function load(openAssignmentId = selectedAssignmentId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/saas-subscriptions`
    const [summary, assignments, readiness, notes, snapshots] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/assignments`),
      apiGet(`${base}/readiness`),
      apiGet(`${base}/notes`),
      apiGet(`${base}/snapshots`),
    ])
    const assignmentItems = assignments.items || []
    setSelectedAssignmentId(openAssignmentId || assignmentItems[0]?.id || "")
    setState({
      ...context,
      summary,
      assignments: assignmentItems,
      readiness: readiness.items || [],
      notes: notes.items || [],
      snapshots: snapshots.items || [],
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedAssignment = useMemo(() => state?.assignments?.find((assignment) => assignment.id === selectedAssignmentId), [state, selectedAssignmentId])
  const readinessForAssignment = (state?.readiness || []).filter((item) => !selectedAssignment?.id || item.assignment_id === selectedAssignment.id)
  const metrics = [
    ["Assignments", state?.summary?.assignment_count || 0],
    ["Readiness", state?.summary?.readiness_count || 0],
    ["Notes", state?.summary?.note_count || 0],
    ["Snapshots", state?.summary?.snapshot_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Settings</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">My Subscription</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only subscription and entitlement visibility for your agency workspace.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No billing</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Subscription overview</h3>
            <p className="mt-2 text-sm text-slate-600">{state?.summary?.plain_language_overview || "Subscription visibility is read-only and metadata-only."}</p>
          </section>

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <div className="rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-200 p-4">
                <h3 className="font-semibold text-slate-950">Assigned plans</h3>
              </div>
              {!state?.assignments?.length ? <EmptyState title="No subscription assignment" body="The Platform Console has not assigned subscription metadata to this agency yet." /> : (
                <div className="divide-y divide-slate-100">
                  {state.assignments.map((assignment) => (
                    <button className={`block w-full p-4 text-left hover:bg-slate-50 ${selectedAssignmentId === assignment.id ? "bg-blue-50" : ""}`} type="button" onClick={() => load(assignment.id)} key={assignment.id}>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold text-slate-950">Subscription assignment</p>
                          <p className="mt-1 text-sm text-slate-600">{label(assignment.assignment_status)} · access enforcement disabled</p>
                        </div>
                        <Status text={label(assignment.assignment_status)} ready={assignment.assignment_status === "active"} />
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-4">
              {!selectedAssignment ? <EmptyState title="Select subscription metadata" body="Entitlement details will appear here." /> : (
                <>
                  <section className="rounded-lg border border-slate-200 bg-white p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-slate-950">Assigned entitlement scope</h3>
                        <p className="mt-1 text-sm text-slate-600">This view does not bill, charge, invoice, settle, or automatically disable access.</p>
                      </div>
                      <Status text={label(selectedAssignment.assignment_status)} ready={selectedAssignment.assignment_status === "active"} />
                    </div>
                    <div className="mt-4 grid gap-3 text-sm md:grid-cols-3">
                      <Info label="Modules" values={selectedAssignment.included_modules} />
                      <Info label="Airline intelligence" values={selectedAssignment.included_airline_intelligence_domains} />
                      <Info label="Data-pack channels" values={selectedAssignment.included_data_pack_channels} />
                    </div>
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white">
                    <div className="border-b border-slate-200 p-4">
                      <h3 className="font-semibold text-slate-950">Entitlement readiness</h3>
                    </div>
                    {readinessForAssignment.length ? (
                      <div className="divide-y divide-slate-100">
                        {readinessForAssignment.map((item) => (
                          <div className="p-4" key={item.id}>
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <p className="font-semibold text-slate-950">{item.entitlement_key}</p>
                                <p className="mt-1 text-sm text-slate-600">{item.plain_language_summary || "Readiness metadata."}</p>
                              </div>
                              <Status text={label(item.status)} ready={item.status === "ready"} />
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : <EmptyState title="No entitlement readiness yet" body="Platform review has not added readiness metadata for this subscription." />}
                  </section>

                  <section className="grid gap-4 lg:grid-cols-2">
                    <ListPanel title="Review notes" items={state.notes} emptyTitle="No review notes" textKey="note" />
                    <ListPanel title="Snapshot history" items={state.snapshots} emptyTitle="No snapshots" textKey="plain_language_summary" />
                  </section>
                </>
              )}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Info({ label: text, values }) {
  return (
    <div className="rounded-md bg-slate-50 p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{text}</p>
      <p className="mt-2 text-slate-700">{values?.length ? values.join(", ") : "Not assigned"}</p>
    </div>
  )
}

function ListPanel({ title, items, emptyTitle, textKey }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">{title}</h3>
      </div>
      {items?.length ? (
        <div className="divide-y divide-slate-100">
          {items.slice(0, 6).map((item) => (
            <div className="p-4 text-sm" key={item.id}>
              <p className="text-slate-700">{item[textKey] || "Metadata record"}</p>
              <p className="mt-1 text-xs text-slate-500">{label(item.note_type || item.snapshot_type)}</p>
            </div>
          ))}
        </div>
      ) : <EmptyState title={emptyTitle} body="Platform-visible metadata will appear here when available." />}
    </section>
  )
}

function Metric({ label: text, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{text}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function Status({ text, ready }) {
  const tone = ready ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-amber-50 text-amber-700 ring-amber-200"
  return <span className={`inline-flex w-fit rounded-full px-2 py-1 text-xs font-semibold ring-1 ${tone}`}>{text}</span>
}

function label(value) {
  return String(value || "").replaceAll("_", " ")
}
