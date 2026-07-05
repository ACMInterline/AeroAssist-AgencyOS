import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function RolloutApprovalPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const [approvals, summary] = await Promise.all([
        apiGet(`/api/agencies/${context.agency.id}/feature-bundle-rollout-approvals`),
        apiGet(`/api/agencies/${context.agency.id}/feature-bundle-rollout-approvals/summary`),
      ])
      setState({
        ...context,
        approvals: approvals.items || [],
        summary: summary.summary || approvals.summary || {},
      })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const statusCounts = state?.summary?.by_status || {}
  const metrics = [
    ["Approvals", state?.approvals?.length || 0],
    ["Under review", statusCounts.under_review || 0],
    ["Approved", statusCounts.approved || 0],
    ["Rejected", statusCounts.rejected || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Settings</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Rollout Approval</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only approval metadata for rollout plans. It does not activate features, enforce permissions, gate access, bill, deploy, notify, publish, or execute rollouts.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No execution</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          {state?.approvals?.length ? (
            <section className="grid gap-4 xl:grid-cols-2">
              {state.approvals.map((approval) => (
                <article className="rounded-lg border border-slate-200 bg-white p-5" key={approval.approval_id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{approval.bundle_name || approval.bundle_id}</p>
                      <h3 className="mt-1 font-semibold text-slate-950">{approval.plan_name || approval.rollout_plan_id}</h3>
                      <p className="text-sm text-slate-600">{approval.approval_id}</p>
                    </div>
                    <StatusBadge status={approval.status} />
                  </div>

                  <dl className="mt-4 grid gap-3 text-sm md:grid-cols-3">
                    <Info label="Reviewer" value={approval.reviewer || approval.reviewed_by || "Not assigned"} />
                    <Info label="Approved by" value={approval.approved_by || "Not approved"} />
                    <Info label="Approved at" value={formatDateTime(approval.approved_at)} />
                    <Info label="Rollout stage" value={titleize(approval.rollout_stage)} />
                    <Info label="Target start" value={formatDate(approval.target_start_date)} />
                    <Info label="Target end" value={formatDate(approval.target_end_date)} />
                  </dl>

                  <section className="mt-4">
                    <h4 className="text-sm font-semibold text-slate-950">Review history</h4>
                    <div className="mt-2 space-y-2">
                      {(approval.timeline || []).slice(-5).map((entry) => (
                        <div className="rounded-md border border-slate-100 bg-slate-50 p-3 text-xs text-slate-600" key={entry.timeline_entry_id || `${entry.event_type}-${entry.occurred_at}`}>
                          <p className="font-semibold text-slate-800">{titleize(entry.event_type)}</p>
                          <p>{formatDateTime(entry.occurred_at)} · {entry.actor || "Platform metadata"}</p>
                          {entry.notes ? <p className="mt-1">{entry.notes}</p> : null}
                        </div>
                      ))}
                    </div>
                  </section>

                  <section className="mt-4">
                    <h4 className="text-sm font-semibold text-slate-950">Notes</h4>
                    <div className="mt-2 space-y-2">
                      {(approval.notes_list || []).length ? approval.notes_list.map((note) => (
                        <div className="rounded-md border border-slate-100 bg-slate-50 p-3 text-xs text-slate-600" key={note.note_id || note.id}>
                          <p className="font-semibold text-slate-800">{note.author || "Platform metadata"}</p>
                          <p>{note.note_text}</p>
                        </div>
                      )) : <p className="text-sm text-slate-500">No approval notes yet.</p>}
                    </div>
                  </section>
                </article>
              ))}
            </section>
          ) : <EmptyState title="No rollout approvals" body="Platform approval metadata will appear here after rollout plans are reviewed." />}
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

function Info({ label, value }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 text-slate-700">{value || "Not set"}</dd>
    </div>
  )
}

function StatusBadge({ status }) {
  const tones = {
    approved: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    under_review: "bg-blue-50 text-blue-700 ring-blue-200",
    submitted: "bg-sky-50 text-sky-700 ring-sky-200",
    rejected: "bg-red-50 text-red-700 ring-red-200",
    archived: "bg-slate-100 text-slate-600 ring-slate-200",
  }
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${tones[status] || "bg-amber-50 text-amber-700 ring-amber-200"}`}>{titleize(status)}</span>
}

function titleize(value) {
  return String(value || "unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function formatDate(value) {
  if (!value) return "Not set"
  return new Date(value).toLocaleDateString()
}

function formatDateTime(value) {
  if (!value) return "Not set"
  return new Date(value).toLocaleString()
}
