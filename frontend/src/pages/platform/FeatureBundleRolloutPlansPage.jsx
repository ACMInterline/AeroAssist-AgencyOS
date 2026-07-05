import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"

const defaultForm = {
  agency_id: "",
  bundle_id: "",
  plan_name: "",
  rollout_stage: "draft",
  target_start_date: "",
  target_end_date: "",
  rollout_owner: "",
  readiness_snapshot_id: "",
  assigned_bundle_id: "",
  notes: "",
}

const planStages = ["draft", "readiness_review", "scheduled", "paused", "archived"]

export default function PlatformFeatureBundleRolloutPlansPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaultForm)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load(nextForm = form) {
    const [me, agencies, bundles, assignments, readiness, plans] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet("/api/platform/feature-flag-bundles"),
      apiGet("/api/platform/feature-bundle-assignments"),
      apiGet("/api/platform/feature-bundle-rollout-readiness"),
      apiGet("/api/platform/feature-bundle-rollout-plans"),
    ])
    const agencyItems = agencies.items || []
    const bundleItems = bundles.items || []
    const assignmentItems = assignments.items || []
    const readinessItems = readiness.items || []
    setState({
      me,
      agencies: agencyItems,
      bundles: bundleItems,
      assignments: assignmentItems,
      readiness: readinessItems,
      plans: plans.items || [],
      summary: plans.summary || {},
    })
    setForm((current) => {
      const agencyId = nextForm.agency_id || current.agency_id || agencyItems[0]?.id || ""
      const bundleId = nextForm.bundle_id || current.bundle_id || bundleItems[0]?.bundle_id || ""
      const matchingAssignment = assignmentItems.find((item) => item.agency_id === agencyId && item.bundle_id === bundleId)
      const matchingReadiness = readinessItems.find((item) => item.agency_id === agencyId && item.bundle_id === bundleId)
      return {
        ...current,
        ...nextForm,
        agency_id: agencyId,
        bundle_id: bundleId,
        assigned_bundle_id: nextForm.assigned_bundle_id || current.assigned_bundle_id || matchingAssignment?.assignment_id || "",
        readiness_snapshot_id: nextForm.readiness_snapshot_id || current.readiness_snapshot_id || matchingReadiness?.id || "",
      }
    })
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

  function createPlan(event) {
    event.preventDefault()
    runAction("create", async () => {
      const readinessItem = (state?.readiness || []).find((item) => item.id === form.readiness_snapshot_id)
      const payload = cleanPayload({
        ...form,
        checklist_summary: summaryFromReadiness(readinessItem),
      })
      const result = await apiPost("/api/platform/feature-bundle-rollout-plans", payload)
      setMessage("Rollout plan metadata saved. No activation, sending, billing, or execution was performed.")
      const nextForm = {
        ...defaultForm,
        agency_id: form.agency_id,
        bundle_id: form.bundle_id,
        assigned_bundle_id: form.assigned_bundle_id,
        readiness_snapshot_id: form.readiness_snapshot_id,
      }
      await load(nextForm)
      return result
    })
  }

  function updateStage(plan, rolloutStage) {
    runAction(`${rolloutStage}-${plan.rollout_plan_id}`, async () => {
      await apiPut(`/api/platform/feature-bundle-rollout-plans/${plan.rollout_plan_id}`, {
        rollout_stage: rolloutStage,
        notes: plan.notes || `Rollout plan stage updated to ${titleize(rolloutStage)} as metadata only.`,
      })
      setMessage(`Plan stage updated to ${titleize(rolloutStage)} as metadata only.`)
      await load()
    })
  }

  const stageCounts = state?.summary?.by_rollout_stage || {}
  const metrics = [
    ["Plans", state?.plans?.length || 0],
    ["Readiness review", stageCounts.readiness_review || 0],
    ["Scheduled", stageCounts.scheduled || 0],
    ["Paused", stageCounts.paused || 0],
  ]
  const assignmentOptions = (state?.assignments || [])
    .filter((item) => !form.agency_id || item.agency_id === form.agency_id)
    .filter((item) => !form.bundle_id || item.bundle_id === form.bundle_id)
    .map((item) => [item.assignment_id, `${agencyName(state?.agencies, item.agency_id)} · ${item.bundle_name || item.bundle_id}`])
  const readinessOptions = (state?.readiness || [])
    .filter((item) => !form.agency_id || item.agency_id === form.agency_id)
    .filter((item) => !form.bundle_id || item.bundle_id === form.bundle_id)
    .map((item) => [item.id, `${titleize(item.readiness_status)} · ${item.assignment_id}`])

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Feature Flags</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Feature Bundle Rollout Plans</h2>
              <p className="mt-1 text-sm text-slate-600">Plans are metadata only. They do not activate, publish, send, bill, enforce access, block routes, or execute rollout actions.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Platform metadata</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No execution</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No billing</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Plan metadata</h3>
              <form className="mt-4 grid gap-3" onSubmit={createPlan}>
                <SelectField label="Agency" value={form.agency_id} onChange={(value) => setForm({ ...form, agency_id: value, assigned_bundle_id: "", readiness_snapshot_id: "" })} options={(state?.agencies || []).map((agency) => [agency.id, agency.name])} />
                <SelectField label="Bundle" value={form.bundle_id} onChange={(value) => setForm({ ...form, bundle_id: value, assigned_bundle_id: "", readiness_snapshot_id: "" })} options={(state?.bundles || []).map((bundle) => [bundle.bundle_id, bundle.bundle_name])} />
                <label className="grid gap-1 text-sm">
                  <span className="font-medium text-slate-700">Plan name</span>
                  <input className="rounded-md border border-slate-300 px-3 py-2" value={form.plan_name} onChange={(event) => setForm({ ...form, plan_name: event.target.value })} />
                </label>
                <SelectField label="Stage" value={form.rollout_stage} onChange={(value) => setForm({ ...form, rollout_stage: value })} options={planStages.map((item) => [item, titleize(item)])} />
                <DateField label="Target start" value={form.target_start_date} onChange={(value) => setForm({ ...form, target_start_date: value })} />
                <DateField label="Target end" value={form.target_end_date} onChange={(value) => setForm({ ...form, target_end_date: value })} />
                <label className="grid gap-1 text-sm">
                  <span className="font-medium text-slate-700">Owner</span>
                  <input className="rounded-md border border-slate-300 px-3 py-2" value={form.rollout_owner} onChange={(event) => setForm({ ...form, rollout_owner: event.target.value })} />
                </label>
                <SelectField label="Assignment" value={form.assigned_bundle_id} onChange={(value) => setForm({ ...form, assigned_bundle_id: value })} options={[["", "No assignment link"], ...assignmentOptions]} />
                <SelectField label="Readiness snapshot" value={form.readiness_snapshot_id} onChange={(value) => setForm({ ...form, readiness_snapshot_id: value })} options={[["", "No readiness snapshot"], ...readinessOptions]} />
                <label className="grid gap-1 text-sm">
                  <span className="font-medium text-slate-700">Notes</span>
                  <textarea className="min-h-20 rounded-md border border-slate-300 px-3 py-2" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} />
                </label>
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={!form.agency_id || !form.bundle_id || !form.plan_name || working === "create"}>Save plan metadata</button>
              </form>
            </section>

            <section className="rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-200 p-4">
                <h3 className="font-semibold text-slate-950">Rollout plan table</h3>
              </div>
              {state?.plans?.length ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-100 text-left text-sm">
                    <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      <tr>
                        <th className="px-4 py-3">Plan</th>
                        <th className="px-4 py-3">Agency</th>
                        <th className="px-4 py-3">Bundle</th>
                        <th className="px-4 py-3">Stage</th>
                        <th className="px-4 py-3">Target</th>
                        <th className="px-4 py-3">Checklist</th>
                        <th className="px-4 py-3">Warnings</th>
                        <th className="px-4 py-3">Blockers</th>
                        <th className="px-4 py-3">Metadata updates</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {state.plans.map((plan) => (
                        <tr key={plan.rollout_plan_id}>
                          <td className="px-4 py-3">
                            <p className="font-semibold text-slate-950">{plan.plan_name}</p>
                            <p className="text-xs text-slate-500">{plan.rollout_plan_id}</p>
                          </td>
                          <td className="px-4 py-3 text-slate-600">{plan.agency_name || plan.agency_id}</td>
                          <td className="px-4 py-3">
                            <p className="font-semibold text-slate-950">{plan.bundle_name || plan.bundle_id}</p>
                            <p className="text-xs text-slate-500">{plan.bundle_key || plan.bundle_id}</p>
                          </td>
                          <td className="px-4 py-3"><StatusBadge status={plan.rollout_stage} /></td>
                          <td className="px-4 py-3 text-slate-600">{formatDate(plan.target_start_date)} - {formatDate(plan.target_end_date)}</td>
                          <td className="px-4 py-3 text-slate-600">{formatCounts(plan.checklist_summary?.counts)}</td>
                          <td className="px-4 py-3 text-slate-600">{plan.warnings || 0}</td>
                          <td className="px-4 py-3 text-slate-600">{plan.blockers || 0}</td>
                          <td className="px-4 py-3">
                            <div className="flex flex-wrap gap-2">
                              {["readiness_review", "scheduled", "paused", "archived"].map((stage) => (
                                <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => updateStage(plan, stage)} disabled={working === `${stage}-${plan.rollout_plan_id}` || plan.rollout_stage === stage} key={stage}>{titleize(stage)}</button>
                              ))}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : <EmptyState title="No rollout plans" body="Create metadata-only rollout plans after readiness has been reviewed." />}
            </section>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function cleanPayload(form) {
  return Object.fromEntries(Object.entries(form).filter(([, value]) => value !== ""))
}

function summaryFromReadiness(item) {
  if (!item) return { counts: {}, metadata_only: true }
  const counts = item.checklist_counts || {}
  return {
    counts,
    warning_count: counts.warning || 0,
    blocker_count: counts.blocked || 0,
    readiness_status: item.readiness_status,
    readiness_snapshot_id: item.id,
    metadata_only: true,
  }
}

function SelectField({ label, value, onChange, options }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <select className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([optionValue, optionLabel]) => <option value={optionValue} key={optionValue}>{optionLabel}</option>)}
      </select>
    </label>
  )
}

function DateField({ label, value, onChange }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input className="rounded-md border border-slate-300 px-3 py-2" type="date" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
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

function StatusBadge({ status }) {
  const tones = {
    scheduled: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    readiness_review: "bg-blue-50 text-blue-700 ring-blue-200",
    paused: "bg-amber-50 text-amber-700 ring-amber-200",
    archived: "bg-slate-100 text-slate-600 ring-slate-200",
    draft: "bg-slate-100 text-slate-700 ring-slate-200",
  }
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ring-1 ${tones[status] || tones.draft}`}>{titleize(status)}</span>
}

function formatCounts(counts = {}) {
  return `Passed ${counts.passed || 0} / Warn ${counts.warning || 0} / Block ${counts.blocked || 0}`
}

function agencyName(agencies, agencyId) {
  return agencies?.find((agency) => agency.id === agencyId)?.name || agencyId || "Agency"
}

function titleize(value) {
  if (!value) return "Metadata"
  return String(value).replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatDate(value) {
  if (!value) return "Not set"
  return new Date(value).toLocaleDateString()
}
