import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"

const approvalStatuses = ["draft", "submitted", "under_review", "approved", "rejected", "archived"]

const defaultForm = {
  rollout_plan_id: "",
  status: "draft",
  reviewer: "",
  notes: "",
}

export default function PlatformFeatureBundleRolloutApprovalsPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaultForm)
  const [noteText, setNoteText] = useState({})
  const [working, setWorking] = useState("")
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function load(nextForm = form) {
    const [me, plans, approvals] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/platform/feature-bundle-rollout-plans"),
      apiGet("/api/platform/feature-bundle-rollout-approvals"),
    ])
    const planItems = plans.items || []
    setState({
      me,
      plans: planItems,
      approvals: approvals.items || [],
      summary: approvals.summary || {},
    })
    setForm((current) => ({
      ...current,
      ...nextForm,
      rollout_plan_id: nextForm.rollout_plan_id || current.rollout_plan_id || planItems[0]?.rollout_plan_id || "",
    }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function runAction(name, action) {
    setWorking(name)
    setError("")
    setMessage("")
    try {
      await action()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  function createApproval(event) {
    event.preventDefault()
    runAction("create", async () => {
      await apiPost("/api/platform/feature-bundle-rollout-approvals", cleanPayload(form))
      setMessage("Approval metadata saved. No feature enablement, access gating, billing, deployment, notification, or rollout execution occurred.")
      await load({ ...defaultForm, rollout_plan_id: form.rollout_plan_id })
    })
  }

  function updateStatus(approval, status) {
    runAction(`${approval.approval_id}-${status}`, async () => {
      await apiPut(`/api/platform/feature-bundle-rollout-approvals/${approval.approval_id}`, {
        status,
        notes: approval.notes || `Approval status recorded as ${titleize(status)} as metadata only.`,
      })
      setMessage(`Approval status recorded as ${titleize(status)} metadata.`)
      await load()
    })
  }

  function addNote(approval) {
    const text = noteText[approval.approval_id] || ""
    if (!text.trim()) return
    runAction(`note-${approval.approval_id}`, async () => {
      await apiPost(`/api/platform/feature-bundle-rollout-approvals/${approval.approval_id}/notes`, {
        note_text: text,
        note_type: "review_note",
        agency_visible: true,
      })
      setNoteText((current) => ({ ...current, [approval.approval_id]: "" }))
      setMessage("Approval note metadata saved. No notification or rollout execution occurred.")
      await load()
    })
  }

  const statusCounts = state?.summary?.by_status || {}
  const metrics = [
    ["Approvals", state?.approvals?.length || 0],
    ["Under review", statusCounts.under_review || 0],
    ["Approved", statusCounts.approved || 0],
    ["Rejected", statusCounts.rejected || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Feature Flags</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Feature Bundle Rollout Approvals</h2>
              <p className="mt-1 text-sm text-slate-600">Approval records are metadata only. They do not enable features, enforce permissions, gate runtime access, bill, deploy, notify, publish, or execute rollouts.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Platform metadata</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No gating</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No notifications</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Approval metadata</h3>
            <form className="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_180px_minmax(0,220px)_minmax(0,1fr)_auto]" onSubmit={createApproval}>
              <SelectField label="Rollout plan" value={form.rollout_plan_id} onChange={(value) => setForm({ ...form, rollout_plan_id: value })} options={(state?.plans || []).map((plan) => [plan.rollout_plan_id, `${plan.plan_name} · ${plan.agency_name || plan.agency_id}`])} />
              <SelectField label="Status" value={form.status} onChange={(value) => setForm({ ...form, status: value })} options={approvalStatuses.map((status) => [status, titleize(status)])} />
              <label className="grid gap-1 text-sm">
                <span className="font-medium text-slate-700">Reviewer</span>
                <input className="rounded-md border border-slate-300 px-3 py-2" value={form.reviewer} onChange={(event) => setForm({ ...form, reviewer: event.target.value })} />
              </label>
              <label className="grid gap-1 text-sm">
                <span className="font-medium text-slate-700">Notes</span>
                <input className="rounded-md border border-slate-300 px-3 py-2" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} />
              </label>
              <div className="flex items-end">
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={!form.rollout_plan_id || working === "create"}>Save approval</button>
              </div>
            </form>
          </section>

          {state?.approvals?.length ? (
            <section className="grid gap-4 xl:grid-cols-2">
              {state.approvals.map((approval) => (
                <article className="rounded-lg border border-slate-200 bg-white p-5" key={approval.approval_id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{approval.agency_name || approval.agency_id}</p>
                      <h3 className="mt-1 font-semibold text-slate-950">{approval.plan_name || approval.rollout_plan_id}</h3>
                      <p className="text-sm text-slate-600">{approval.bundle_name || approval.bundle_id}</p>
                    </div>
                    <StatusBadge status={approval.status} />
                  </div>

                  <dl className="mt-4 grid gap-3 text-sm md:grid-cols-3">
                    <Info label="Reviewer" value={approval.reviewer || approval.reviewed_by || "Not assigned"} />
                    <Info label="Approved by" value={approval.approved_by || "Not approved"} />
                    <Info label="Approved at" value={formatDateTime(approval.approved_at)} />
                    <Info label="Rollout stage" value={titleize(approval.rollout_stage)} />
                    <Info label="Target start" value={formatDate(approval.target_start_date)} />
                    <Info label="Notes" value={approval.notes || "No approval notes"} />
                  </dl>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {["submitted", "under_review", "approved", "rejected", "archived"].map((status) => (
                      <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => updateStatus(approval, status)} disabled={working === `${approval.approval_id}-${status}` || approval.status === status} key={status}>{titleize(status)}</button>
                    ))}
                  </div>

                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <section>
                      <h4 className="text-sm font-semibold text-slate-950">Timeline</h4>
                      <div className="mt-2 space-y-2">
                        {(approval.timeline || []).slice(-4).map((entry) => (
                          <div className="rounded-md border border-slate-100 bg-slate-50 p-3 text-xs text-slate-600" key={entry.timeline_entry_id || `${entry.event_type}-${entry.occurred_at}`}>
                            <p className="font-semibold text-slate-800">{titleize(entry.event_type)}</p>
                            <p>{formatDateTime(entry.occurred_at)} · {entry.actor || "System metadata"}</p>
                            {entry.notes ? <p className="mt-1">{entry.notes}</p> : null}
                          </div>
                        ))}
                      </div>
                    </section>
                    <section>
                      <h4 className="text-sm font-semibold text-slate-950">Notes</h4>
                      <div className="mt-2 space-y-2">
                        {(approval.notes_list || []).slice(-3).map((note) => (
                          <div className="rounded-md border border-slate-100 bg-slate-50 p-3 text-xs text-slate-600" key={note.note_id || note.id}>
                            <p className="font-semibold text-slate-800">{note.author || "Platform metadata"}</p>
                            <p>{note.note_text}</p>
                          </div>
                        ))}
                      </div>
                      <div className="mt-3 flex gap-2">
                        <input className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" value={noteText[approval.approval_id] || ""} onChange={(event) => setNoteText({ ...noteText, [approval.approval_id]: event.target.value })} placeholder="Add metadata note" />
                        <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => addNote(approval)} disabled={working === `note-${approval.approval_id}`}>Add</button>
                      </div>
                    </section>
                  </div>
                </article>
              ))}
            </section>
          ) : <EmptyState title="No rollout approvals" body="Create approval metadata after rollout plans are ready for review." />}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function cleanPayload(form) {
  return Object.fromEntries(Object.entries(form).filter(([, value]) => value !== ""))
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function SelectField({ label, value, onChange, options }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <select className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([optionValue, labelText]) => <option value={optionValue} key={optionValue}>{labelText}</option>)}
      </select>
    </label>
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
