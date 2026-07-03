import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaults = {
  preview_id: "",
  approval_name: "Manual release approval",
  assigned_reviewer: "",
  checkpoint_title: "Preview reviewed for manual release readiness",
  checkpoint_type: "preview_review",
  status_reason: "Human reviewer approved metadata-only release readiness.",
  readiness_name: "Manual release readiness",
  hold_title: "Manual review hold",
  hold_reason: "Review hold captured before manual release.",
  snapshot_name: "Release readiness snapshot",
}

export default function OfferDecisionExportReleasesPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaults)
  const [selectedApprovalId, setSelectedApprovalId] = useState("")
  const [selectedReadinessId, setSelectedReadinessId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [working, setWorking] = useState("")

  async function load(nextApprovalId = selectedApprovalId, nextReadinessId = selectedReadinessId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/offer-decision-export-releases`
    const previewBase = `/api/agencies/${context.agency.id}/offer-decision-export-previews`
    const [summary, previewsResult, approvalsResult, readinessResult] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${previewBase}/previews`),
      apiGet(`${base}/approvals`),
      apiGet(`${base}/readiness`),
    ])
    const approvals = approvalsResult.items || []
    const readiness = readinessResult.items || []
    const chosenApprovalId = nextApprovalId || approvals[0]?.id || ""
    const chosenReadinessId = nextReadinessId || readiness[0]?.id || ""
    const [approvalDetail, readinessDetail] = await Promise.all([
      chosenApprovalId ? apiGet(`${base}/approvals/${chosenApprovalId}`) : Promise.resolve(null),
      chosenReadinessId ? apiGet(`${base}/readiness/${chosenReadinessId}`) : Promise.resolve(null),
    ])
    setSelectedApprovalId(chosenApprovalId)
    setSelectedReadinessId(chosenReadinessId)
    setState({
      ...context,
      base,
      summary,
      previews: previewsResult.items || [],
      approvals,
      readiness,
      approvalDetail,
      readinessDetail,
    })
    if (!form.preview_id && previewsResult.items?.[0]?.id) {
      setForm((current) => ({ ...current, preview_id: previewsResult.items[0].id }))
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedApproval = state?.approvalDetail?.approval || state?.approvals?.find((item) => item.id === selectedApprovalId)
  const selectedReadiness = state?.readinessDetail?.readiness || state?.readiness?.find((item) => item.id === selectedReadinessId)
  const holds = state?.readinessDetail?.holds || []
  const activeHold = holds.find((item) => item.hold_status === "active")
  const metrics = useMemo(() => [
    ["Approvals", state?.summary?.approval_count],
    ["Checkpoints", state?.summary?.checkpoint_count],
    ["Readiness", state?.summary?.readiness_count],
    ["Holds", state?.summary?.hold_count],
    ["Snapshots", state?.summary?.snapshot_count],
  ], [state])

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
    runAction("approval", async () => {
      const result = await apiPost(`${state.base}/approvals`, {
        preview_id: form.preview_id,
        approval_name: form.approval_name || null,
        assigned_reviewer: form.assigned_reviewer || null,
      })
      setMessage("Manual release approval metadata created.")
      await load(result.approval.id, selectedReadinessId)
    })
  }

  function addCheckpoint(event) {
    event.preventDefault()
    if (!selectedApprovalId) return
    runAction("checkpoint", async () => {
      await apiPost(`${state.base}/approvals/${selectedApprovalId}/checkpoints`, {
        checkpoint_type: form.checkpoint_type,
        checkpoint_status: "passed",
        checkpoint_title: form.checkpoint_title,
        notes: "Metadata-only checkpoint. No sending, public link, PDF delivery, booking, ticketing, payment, or provider execution occurred.",
      })
      setMessage("Approval checkpoint recorded.")
      await load(selectedApprovalId, selectedReadinessId)
    })
  }

  function approveSelected() {
    if (!selectedApprovalId) return
    runAction("approve", async () => {
      await apiPost(`${state.base}/approvals/${selectedApprovalId}/status`, {
        approval_status: "approved",
        status_reason: form.status_reason || null,
      })
      setMessage("Approval status set to approved for manual readiness review.")
      await load(selectedApprovalId, selectedReadinessId)
    })
  }

  function createReadiness(event) {
    event.preventDefault()
    runAction("readiness", async () => {
      const result = await apiPost(`${state.base}/readiness`, {
        approval_id: selectedApprovalId || null,
        preview_id: selectedApprovalId ? null : form.preview_id,
        readiness_name: form.readiness_name || null,
      })
      setMessage("Manual release readiness metadata created.")
      await load(selectedApprovalId, result.readiness.id)
    })
  }

  function addHold(event) {
    event.preventDefault()
    if (!selectedReadinessId) return
    runAction("hold", async () => {
      await apiPost(`${state.base}/readiness/${selectedReadinessId}/holds`, {
        hold_type: "manual_review",
        severity: "medium",
        title: form.hold_title,
        reason: form.hold_reason,
      })
      setMessage("Manual release hold recorded.")
      await load(selectedApprovalId, selectedReadinessId)
    })
  }

  function releaseHold() {
    if (!selectedReadinessId || !activeHold) return
    runAction("release", async () => {
      await apiPost(`${state.base}/readiness/${selectedReadinessId}/holds/${activeHold.id}/release`, {
        release_notes: "Hold released after human metadata review.",
      })
      setMessage("Manual release hold released.")
      await load(selectedApprovalId, selectedReadinessId)
    })
  }

  function saveSnapshot() {
    if (!selectedReadinessId) return
    runAction("snapshot", async () => {
      await apiPost(`${state.base}/readiness/${selectedReadinessId}/snapshots`, {
        snapshot_name: form.snapshot_name || null,
      })
      setMessage("Immutable release readiness snapshot saved.")
      await load(selectedApprovalId, selectedReadinessId)
    })
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Decision Export Releases</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Manual Release Readiness</h2>
              <p className="mt-1 text-sm text-slate-600">Prepare human approval, release holds, and immutable readiness snapshots for export previews.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Manual approval</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">No delivery</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Metadata only</span>
            </div>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[410px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createApproval}>
                <h3 className="font-semibold text-slate-950">Create approval</h3>
                <Select label="Export preview" value={form.preview_id} onChange={(value) => setForm({ ...form, preview_id: value })} options={(state?.previews || []).map((item) => [item.id, `${item.render_profile || "preview"} / ${item.preview_status}`])} />
                <Field label="Approval name" value={form.approval_name} onChange={(value) => setForm({ ...form, approval_name: value })} />
                <Field label="Assigned reviewer" value={form.assigned_reviewer} onChange={(value) => setForm({ ...form, assigned_reviewer: value })} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "approval" || !form.preview_id}>{working === "approval" ? "Creating..." : "Create approval metadata"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addCheckpoint}>
                <h3 className="font-semibold text-slate-950">Approval review</h3>
                <Select label="Approval" value={selectedApprovalId} onChange={(value) => load(value, selectedReadinessId).catch((err) => setError(err.message))} options={(state?.approvals || []).map((item) => [item.id, `${item.approval_name || item.id} / ${item.approval_status}`])} />
                <Select label="Checkpoint type" value={form.checkpoint_type} onChange={(value) => setForm({ ...form, checkpoint_type: value })} options={[
                  ["preview_review", "Preview review"],
                  ["artifact_metadata_review", "Artifact metadata review"],
                  ["recipient_draft_review", "Recipient draft review"],
                  ["safety_boundary_review", "Safety boundary review"],
                  ["internal_approval", "Internal approval"],
                  ["manual_release_readiness", "Manual release readiness"],
                ]} />
                <Field label="Checkpoint title" value={form.checkpoint_title} onChange={(value) => setForm({ ...form, checkpoint_title: value })} />
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="submit" disabled={!selectedApprovalId || working === "checkpoint"}>{working === "checkpoint" ? "Recording..." : "Record checkpoint"}</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={approveSelected} disabled={!selectedApprovalId || working === "approve"}>{working === "approve" ? "Approving..." : "Approve manually"}</button>
                </div>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createReadiness}>
                <h3 className="font-semibold text-slate-950">Release readiness</h3>
                <Field label="Readiness name" value={form.readiness_name} onChange={(value) => setForm({ ...form, readiness_name: value })} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "readiness" || (!selectedApprovalId && !form.preview_id)}>{working === "readiness" ? "Creating..." : "Create readiness metadata"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addHold}>
                <h3 className="font-semibold text-slate-950">Release holds</h3>
                <Select label="Readiness" value={selectedReadinessId} onChange={(value) => load(selectedApprovalId, value).catch((err) => setError(err.message))} options={(state?.readiness || []).map((item) => [item.id, `${item.readiness_name || item.id} / ${item.readiness_status}`])} />
                <Field label="Hold title" value={form.hold_title} onChange={(value) => setForm({ ...form, hold_title: value })} />
                <TextArea label="Hold reason" value={form.hold_reason} onChange={(value) => setForm({ ...form, hold_reason: value })} />
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="submit" disabled={!selectedReadinessId || working === "hold"}>{working === "hold" ? "Recording..." : "Add hold"}</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={releaseHold} disabled={!activeHold || working === "release"}>{working === "release" ? "Releasing..." : "Release active hold"}</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={saveSnapshot} disabled={!selectedReadinessId || working === "snapshot"}>{working === "snapshot" ? "Saving..." : "Save snapshot"}</button>
                </div>
              </form>
            </div>

            <div className="space-y-4">
              <ApprovalSummary approval={selectedApproval} readiness={selectedReadiness} />
              <SimpleList title="Approval checkpoints" items={state?.approvalDetail?.checkpoints || []} fields={["sequence_order", "checkpoint_type", "checkpoint_status", "checkpoint_title"]} />
              <SimpleList title="Readiness records" items={state?.readiness || []} fields={["readiness_name", "readiness_status", "active_hold_count", "ready_for_manual_release"]} />
              <SimpleList title="Release holds" items={holds} fields={["hold_type", "hold_status", "severity", "title"]} />
              <SimpleList title="Release snapshots" items={state?.readinessDetail?.snapshots || []} fields={["snapshot_name", "immutable", "saved_by", "saved_at"]} />
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

function Field({ label, value, onChange }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function TextArea({ label, value, onChange }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <textarea className="mt-1 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function Select({ label, value, onChange, options }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Select</option>
        {options.map(([id, labelText]) => <option value={id} key={id}>{labelText}</option>)}
      </select>
    </label>
  )
}

function ApprovalSummary({ approval, readiness }) {
  if (!approval && !readiness) return <EmptyState title="No release readiness selected" body="Create approval metadata from an export preview to prepare manual release readiness." />
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{approval?.approval_name || readiness?.readiness_name || "Release readiness"}</h3>
      <div className="mt-3 grid gap-2 text-sm md:grid-cols-4">
        <Summary label="Approval" value={approval?.approval_status || "-"} />
        <Summary label="Checkpoints" value={approval?.checkpoint_count ?? 0} />
        <Summary label="Readiness" value={readiness?.readiness_status || "-"} />
        <Summary label="Manual ready" value={readiness?.ready_for_manual_release ? "yes" : "no"} />
      </div>
    </div>
  )
}

function Summary({ label, value }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 truncate text-slate-800">{formatValue(value)}</p>
    </div>
  )
}

function SimpleList({ title, items, fields }) {
  if (!items.length) return <EmptyState title={`No ${title.toLowerCase()}`} body="No records found." />
  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="flex items-center justify-between border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">{title}</h3>
        <span className="text-sm text-slate-500">{items.length}</span>
      </div>
      <div className="divide-y divide-slate-100">
        {items.slice(0, 10).map((item) => (
          <div className="grid gap-2 p-4 text-sm md:grid-cols-4" key={item.id}>
            {fields.map((field) => <span className="truncate text-slate-700" key={field}>{formatValue(item[field])}</span>)}
          </div>
        ))}
      </div>
    </div>
  )
}

function formatValue(value) {
  if (Array.isArray(value)) return value.join(", ")
  if (typeof value === "string" && value.includes("T")) return new Date(value).toLocaleString()
  if (typeof value === "boolean") return value ? "Yes" : "No"
  return value || "-"
}
