import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiDelete, apiGet, apiPost, apiPut } from "../../lib/api"

const defaultForm = {
  agency_id: "",
  bundle_id: "",
  status: "assigned",
  effective_date: "",
  expiration_date: "",
  notes: "",
  review_status: "pending_review",
}

export default function PlatformFeatureBundleAssignmentsPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaultForm)
  const [selectedAssignmentId, setSelectedAssignmentId] = useState("")
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load(nextSelectedId = selectedAssignmentId) {
    const [me, agencies, bundles, assignments] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet("/api/platform/feature-flag-bundles"),
      apiGet("/api/platform/feature-bundle-assignments"),
    ])
    const agencyItems = agencies.items || []
    const bundleItems = bundles.items || []
    const assignmentItems = assignments.items || []
    setState({
      me,
      agencies: agencyItems,
      bundles: bundleItems,
      assignments: assignmentItems,
      history: assignments.history || [],
    })
    setForm((current) => ({
      ...current,
      agency_id: current.agency_id || agencyItems[0]?.id || "",
      bundle_id: current.bundle_id || bundleItems[0]?.bundle_id || "",
    }))
    setSelectedAssignmentId(nextSelectedId || assignmentItems[0]?.assignment_id || "")
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

  function createAssignment(event) {
    event.preventDefault()
    runAction("create", async () => {
      const payload = cleanPayload(form)
      const result = await apiPost(`/api/platform/agencies/${form.agency_id}/bundle-assignments`, payload)
      setMessage("Feature bundle assignment metadata saved.")
      setForm({ ...defaultForm, agency_id: form.agency_id, bundle_id: form.bundle_id })
      await load(result.assignment.assignment_id)
    })
  }

  function markReviewed(item) {
    runAction(`review-${item.assignment_id}`, async () => {
      await apiPut(`/api/platform/bundle-assignments/${item.assignment_id}`, {
        review_status: "reviewed",
        notes: item.notes || "Platform reviewed feature bundle assignment metadata. No activation is performed.",
      })
      setMessage("Assignment review metadata updated.")
      await load(item.assignment_id)
    })
  }

  function markInactive(item) {
    runAction(`inactive-${item.assignment_id}`, async () => {
      await apiDelete(`/api/platform/bundle-assignments/${item.assignment_id}`)
      setMessage("Assignment marked inactive. History was preserved.")
      await load(item.assignment_id)
    })
  }

  const selectedAssignment = state?.assignments?.find((item) => item.assignment_id === selectedAssignmentId)
  const selectedHistory = (state?.history || []).filter((item) => item.assignment_id === selectedAssignmentId)
  const metrics = [
    ["Assignments", state?.assignments?.length || 0],
    ["History", state?.history?.length || 0],
    ["Inactive", state?.assignments?.filter((item) => item.status === "inactive").length || 0],
    ["Review", state?.assignments?.filter((item) => item.review_status !== "reviewed").length || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Feature Flags</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Feature Bundle Assignments</h2>
              <p className="mt-1 text-sm text-slate-600">Assignments are metadata only. They do not activate features, enforce entitlements, or change permissions.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Platform metadata</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No activation</span>
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
              <h3 className="font-semibold text-slate-950">Assign bundle metadata</h3>
              <form className="mt-4 grid gap-3" onSubmit={createAssignment}>
                <SelectField label="Agency" value={form.agency_id} onChange={(value) => setForm({ ...form, agency_id: value })} options={(state?.agencies || []).map((agency) => [agency.id, agency.name])} />
                <SelectField label="Bundle" value={form.bundle_id} onChange={(value) => setForm({ ...form, bundle_id: value })} options={(state?.bundles || []).map((bundle) => [bundle.bundle_id, bundle.bundle_name])} />
                <SelectField label="Status" value={form.status} onChange={(value) => setForm({ ...form, status: value })} options={["assigned", "review", "paused", "inactive"].map((item) => [item, titleize(item)])} />
                <DateField label="Effective date" value={form.effective_date} onChange={(value) => setForm({ ...form, effective_date: value })} />
                <DateField label="Expiration date" value={form.expiration_date} onChange={(value) => setForm({ ...form, expiration_date: value })} />
                <SelectField label="Review status" value={form.review_status} onChange={(value) => setForm({ ...form, review_status: value })} options={["pending_review", "reviewed", "needs_review"].map((item) => [item, titleize(item)])} />
                <label className="grid gap-1 text-sm">
                  <span className="font-medium text-slate-700">Notes</span>
                  <textarea className="min-h-20 rounded-md border border-slate-300 px-3 py-2" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} />
                </label>
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={!form.agency_id || !form.bundle_id || working === "create"}>Save assignment metadata</button>
              </form>
            </section>

            <div className="space-y-4">
              <section className="rounded-lg border border-slate-200 bg-white">
                <div className="border-b border-slate-200 p-4">
                  <h3 className="font-semibold text-slate-950">Assignment table</h3>
                </div>
                {state?.assignments?.length ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-100 text-left text-sm">
                      <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                        <tr>
                          <th className="px-4 py-3">Agency</th>
                          <th className="px-4 py-3">Bundle</th>
                          <th className="px-4 py-3">Status</th>
                          <th className="px-4 py-3">Effective</th>
                          <th className="px-4 py-3">Expiration</th>
                          <th className="px-4 py-3">Review status</th>
                          <th className="px-4 py-3">Notes</th>
                          <th className="px-4 py-3">History</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {state.assignments.map((item) => (
                          <tr key={item.assignment_id}>
                            <td className="px-4 py-3 text-slate-600">{agencyName(state.agencies, item.agency_id)}</td>
                            <td className="px-4 py-3 font-semibold text-slate-950">{item.bundle_name}</td>
                            <td className="px-4 py-3"><StatusBadge label={titleize(item.status)} /></td>
                            <td className="px-4 py-3 text-slate-600">{formatDate(item.effective_date)}</td>
                            <td className="px-4 py-3 text-slate-600">{formatDate(item.expiration_date)}</td>
                            <td className="px-4 py-3"><StatusBadge label={titleize(item.review_status)} tone="blue" /></td>
                            <td className="max-w-xs px-4 py-3 text-slate-600">{item.notes || "Metadata assignment"}</td>
                            <td className="px-4 py-3">
                              <div className="flex flex-wrap gap-2">
                                <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => setSelectedAssignmentId(item.assignment_id)}>History</button>
                                <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => markReviewed(item)} disabled={working === `review-${item.assignment_id}`}>Review</button>
                                <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => markInactive(item)} disabled={item.status === "inactive" || working === `inactive-${item.assignment_id}`}>Inactive</button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : <EmptyState title="No bundle assignments" body="Feature bundle assignment metadata will appear here." />}
              </section>

              <section className="rounded-lg border border-slate-200 bg-white">
                <div className="border-b border-slate-200 p-4">
                  <h3 className="font-semibold text-slate-950">History drawer</h3>
                </div>
                {selectedAssignment ? (
                  <div className="divide-y divide-slate-100">
                    {selectedHistory.length ? selectedHistory.map((item) => <HistoryRow item={item} key={item.id} />) : <EmptyState title="No history" body="History is created when assignment metadata changes." />}
                  </div>
                ) : <EmptyState title="Select an assignment" body="Choose an assignment row to inspect history metadata." />}
              </section>
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function cleanPayload(form) {
  return Object.fromEntries(Object.entries(form).filter(([, value]) => value !== ""))
}

function HistoryRow({ item }) {
  return (
    <div className="p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-slate-950">{titleize(item.history_event)}</p>
          <p className="mt-1 text-sm text-slate-600">{item.bundle_name} · {titleize(item.status)} · {titleize(item.review_status)}</p>
          {item.notes ? <p className="mt-1 text-sm text-slate-500">{item.notes}</p> : null}
        </div>
        <span className="text-xs font-semibold text-slate-500">{formatDateTime(item.changed_at)}</span>
      </div>
    </div>
  )
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

function StatusBadge({ label, tone = "slate" }) {
  const toneClass = tone === "blue" ? "bg-blue-50 text-blue-700 ring-blue-200" : "bg-slate-100 text-slate-700 ring-slate-200"
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ring-1 ${toneClass}`}>{label}</span>
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

function formatDateTime(value) {
  if (!value) return "Not recorded"
  return new Date(value).toLocaleString()
}
