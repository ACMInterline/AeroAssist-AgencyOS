import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function AirlineIntelligenceConsumptionPage() {
  const [state, setState] = useState(null)
  const [selectedAssignmentId, setSelectedAssignmentId] = useState("")
  const [error, setError] = useState("")

  async function load(openAssignmentId = selectedAssignmentId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/airline-intelligence-consumption`
    const [summary, assigned, readiness, notes, snapshots] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/assigned-knowledge`),
      apiGet(`${base}/usage-readiness`),
      apiGet(`${base}/notes`),
      apiGet(`${base}/snapshots`),
    ])
    const assignments = assigned.items || []
    const nextAssignmentId = openAssignmentId || assignments[0]?.id || ""
    setSelectedAssignmentId(nextAssignmentId)
    setState({
      ...context,
      summary,
      assignments,
      readiness: readiness.items || [],
      notes: notes.items || [],
      snapshots: snapshots.items || [],
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedAssignment = useMemo(() => state?.assignments?.find((item) => item.id === selectedAssignmentId), [state, selectedAssignmentId])
  const readinessForAssignment = (state?.readiness || []).filter((item) => !selectedAssignment?.profile_id || item.profile_id === selectedAssignment.profile_id)
  const metrics = [
    ["Assigned knowledge", state?.summary?.assigned_knowledge_count || 0],
    ["Visible profiles", state?.summary?.profile_count || 0],
    ["Readiness checks", state?.summary?.usage_readiness_count || 0],
    ["Guidance notes", state?.summary?.note_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Airline Intelligence Usage</h2>
            <p className="mt-1 text-sm text-slate-600">Read-only safe-use visibility for platform-reviewed airline intelligence.</p>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">What is available</h3>
            <p className="mt-2 text-sm text-slate-600">{state?.summary?.plain_language_overview || "Airline intelligence usage is read-only and metadata-only."}</p>
          </section>

          <section className="grid gap-3 md:grid-cols-4">
            {(state?.summary?.usage_cards || []).map((card) => (
              <div className="rounded-lg border border-slate-200 bg-white p-4" key={card.usage_area}>
                <p className="text-sm font-semibold text-slate-950">{card.label}</p>
                <p className="mt-3 text-2xl font-semibold text-slate-950">{card.available ? "Yes" : "No"}</p>
                <p className="mt-2 text-sm text-slate-600">{card.plain_language_summary}</p>
                <Status text={label(card.status)} ready={card.available} />
              </div>
            ))}
          </section>

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([text, value]) => <Metric label={text} value={value} key={text} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
            <div className="rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-200 p-4">
                <h3 className="font-semibold text-slate-950">Assigned knowledge</h3>
              </div>
              {!state?.assignments?.length ? <EmptyState title="No agency-visible airline intelligence" body="Platform review has not marked any knowledge version safe for this agency yet." /> : (
                <div className="divide-y divide-slate-100">
                  {state.assignments.map((assignment) => (
                    <button className={`block w-full p-4 text-left hover:bg-slate-50 ${selectedAssignmentId === assignment.id ? "bg-blue-50" : ""}`} type="button" onClick={() => load(assignment.id)} key={assignment.id}>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold text-slate-950">{assignment.plain_language_summary || "Airline intelligence assignment"}</p>
                          <p className="mt-1 text-sm text-slate-600">{assignment.allowed_usage_notes || "Usage is controlled by platform safe-use flags."}</p>
                        </div>
                        <Status text={label(assignment.status)} ready={assignment.status === "visible"} />
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-4">
              {!selectedAssignment ? <EmptyState title="Select assigned knowledge" body="Safe-use guidance will appear here." /> : (
                <>
                  <section className="rounded-lg border border-slate-200 bg-white p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-slate-950">Safe-use summary</h3>
                        <p className="mt-1 text-sm text-slate-600">{selectedAssignment.plain_language_summary || "Agency-visible airline intelligence metadata."}</p>
                      </div>
                      <Status text={label(selectedAssignment.status)} ready={selectedAssignment.status === "visible"} />
                    </div>
                    <div className="mt-4 grid gap-2 text-sm md:grid-cols-2">
                      <Flag label="Available for CRM" enabled={selectedAssignment.crm_safe} />
                      <Flag label="Available for agency website" enabled={selectedAssignment.cms_safe} />
                      <Flag label="Available for client portal" enabled={selectedAssignment.client_portal_safe} />
                      <Flag label="Available for offer builder" enabled={selectedAssignment.offer_builder_safe} />
                    </div>
                    {selectedAssignment.blocked_usage_notes ? <p className="mt-4 rounded-md bg-amber-50 p-3 text-sm text-amber-800">{selectedAssignment.blocked_usage_notes}</p> : null}
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white">
                    <div className="border-b border-slate-200 p-4">
                      <h3 className="font-semibold text-slate-950">Readiness by usage area</h3>
                    </div>
                    {readinessForAssignment.length ? (
                      <div className="divide-y divide-slate-100">
                        {readinessForAssignment.map((item) => (
                          <div className="p-4" key={item.id}>
                            <div className="flex items-center justify-between gap-3">
                              <p className="font-semibold text-slate-950">{usageLabel(item.usage_area)}</p>
                              <Status text={label(item.status)} ready={item.status === "ready"} />
                            </div>
                            <p className="mt-1 text-sm text-slate-600">{item.plain_language_summary}</p>
                          </div>
                        ))}
                      </div>
                    ) : <EmptyState title="No readiness checks yet" body="Platform review has not calculated usage readiness for this assignment." />}
                  </section>

                  <section className="grid gap-4 lg:grid-cols-2">
                    <ListPanel title="Guidance notes" items={state.notes} emptyTitle="No guidance notes" textKey="note" />
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
      ) : <EmptyState title={emptyTitle} body="Platform guidance will appear here when available." />}
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

function Flag({ label: text, enabled }) {
  return <span className={`rounded-md px-3 py-2 ${enabled ? "bg-emerald-50 text-emerald-800" : "bg-slate-50 text-slate-500"}`}>{text}: {enabled ? "Ready" : "Not active"}</span>
}

function Status({ text, ready }) {
  const tone = ready ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-amber-50 text-amber-700 ring-amber-200"
  return <span className={`mt-3 inline-flex w-fit rounded-full px-2 py-1 text-xs font-semibold ring-1 ${tone}`}>{text}</span>
}

function usageLabel(value) {
  return {
    crm: "Available for CRM",
    cms: "Available for agency website",
    client_portal: "Available for client portal",
    offer_builder: "Available for offer builder",
  }[value] || label(value)
}

function label(value) {
  return String(value || "").replaceAll("_", " ")
}
