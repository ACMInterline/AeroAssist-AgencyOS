import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaults = {
  handoff_id: "",
  title: "Manual delivery outcome metadata",
  outcome_status: "pending",
  event_title: "Manual outcome event",
  event_note: "Human-recorded outcome metadata. AgencyOS did not send or deliver anything.",
  receipt_label: "Manual confirmation reference",
  receipt_notes: "Receipt metadata only.",
  issue_title: "Manual delivery issue metadata",
  issue_description: "Human-recorded issue metadata.",
}

export default function OfferDecisionExportDeliveryOutcomesPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaults)
  const [selectedOutcomeId, setSelectedOutcomeId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [working, setWorking] = useState("")

  async function load(nextOutcomeId = selectedOutcomeId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/offer-decision-export-delivery-outcomes`
    const handoffBase = `/api/agencies/${context.agency.id}/offer-decision-export-deliveries`
    const [summary, outcomesResult, handoffsResult] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/outcomes`),
      apiGet(`${handoffBase}/handoffs`),
    ])
    const outcomes = outcomesResult.items || []
    const chosenOutcomeId = nextOutcomeId || outcomes[0]?.id || ""
    const detail = chosenOutcomeId ? await apiGet(`${base}/outcomes/${chosenOutcomeId}`) : null
    setSelectedOutcomeId(chosenOutcomeId)
    setState({
      ...context,
      base,
      summary,
      outcomes,
      handoffs: handoffsResult.items || [],
      detail,
    })
    const firstHandoff = handoffsResult.items?.[0]
    setForm((current) => ({
      ...current,
      handoff_id: current.handoff_id || firstHandoff?.id || "",
    }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedOutcome = state?.detail?.outcome || state?.outcomes?.find((item) => item.id === selectedOutcomeId)
  const firstIssue = state?.detail?.issues?.find((item) => item.issue_status !== "resolved")
  const metrics = useMemo(() => [
    ["Outcomes", state?.summary?.outcome_count],
    ["Events", state?.summary?.event_count],
    ["Receipts", state?.summary?.receipt_count],
    ["Issues", state?.summary?.issue_count],
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

  function createOutcome(event) {
    event.preventDefault()
    runAction("outcome", async () => {
      const result = await apiPost(`${state.base}/outcomes`, {
        handoff_id: form.handoff_id,
        title: form.title || null,
        outcome_status: form.outcome_status,
        actor_type: "agency_user",
      })
      setMessage("Manual outcome metadata created.")
      await load(result.outcome.id)
    })
  }

  function recordOutcomeStatus() {
    if (!selectedOutcomeId) return
    runAction("status", async () => {
      await apiPatch(`${state.base}/outcomes/${selectedOutcomeId}`, {
        outcome_status: "manually_sent",
        status_reason: "Human-recorded manual outcome. No system delivery occurred.",
        actor_type: "agency_user",
      })
      setMessage("Outcome status metadata recorded.")
      await load(selectedOutcomeId)
    })
  }

  function addEvent(event) {
    event.preventDefault()
    if (!selectedOutcomeId) return
    runAction("event", async () => {
      await apiPost(`${state.base}/outcomes/${selectedOutcomeId}/events`, {
        event_type: "sent_recorded",
        actor_type: "agency_user",
        event_title: form.event_title,
        event_note: form.event_note,
      })
      setMessage("Manual event metadata recorded.")
      await load(selectedOutcomeId)
    })
  }

  function addReceipt(event) {
    event.preventDefault()
    if (!selectedOutcomeId) return
    runAction("receipt", async () => {
      await apiPost(`${state.base}/outcomes/${selectedOutcomeId}/receipts`, {
        receipt_type: "manual_note",
        reference_label: form.receipt_label,
        notes: form.receipt_notes,
      })
      setMessage("Receipt metadata added.")
      await load(selectedOutcomeId)
    })
  }

  function addIssue(event) {
    event.preventDefault()
    if (!selectedOutcomeId) return
    runAction("issue", async () => {
      await apiPost(`${state.base}/outcomes/${selectedOutcomeId}/issues`, {
        issue_type: "delivery_failed",
        severity: "medium",
        title: form.issue_title,
        description: form.issue_description,
      })
      setMessage("Issue metadata added.")
      await load(selectedOutcomeId)
    })
  }

  function resolveIssue() {
    if (!firstIssue) return
    runAction("resolve", async () => {
      await apiPatch(`${state.base}/issues/${firstIssue.id}`, {
        issue_status: "resolved",
        resolution_notes: "Human-recorded issue resolution metadata.",
      })
      setMessage("Issue resolution metadata recorded.")
      await load(selectedOutcomeId)
    })
  }

  function createSnapshot() {
    if (!selectedOutcomeId) return
    runAction("snapshot", async () => {
      await apiPost(`${state.base}/outcomes/${selectedOutcomeId}/snapshots`, {
        snapshot_type: selectedOutcome?.outcome_status === "closed" ? "closed" : "outcome_recorded",
      })
      setMessage("Immutable outcome snapshot created.")
      await load(selectedOutcomeId)
    })
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Decision Export Outcomes</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Manual Delivery Outcome Tracking</h2>
              <p className="mt-1 text-sm text-slate-600">Record human-entered outcome metadata after delivery occurs outside AgencyOS.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Manual tracking</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">No provider execution</span>
            </div>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[410px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createOutcome}>
                <h3 className="font-semibold text-slate-950">Create outcome</h3>
                <Select label="Manual handoff" value={form.handoff_id} onChange={(value) => setForm({ ...form, handoff_id: value })} options={(state?.handoffs || []).map((item) => [item.id, `${item.title || item.id} / ${item.status}`])} />
                <Field label="Title" value={form.title} onChange={(value) => setForm({ ...form, title: value })} />
                <Select label="Initial status" value={form.outcome_status} onChange={(value) => setForm({ ...form, outcome_status: value })} options={[
                  ["pending", "Pending"],
                  ["manually_sent", "Manually sent"],
                  ["failed", "Failed"],
                  ["acknowledged", "Acknowledged"],
                ]} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "outcome" || !form.handoff_id}>{working === "outcome" ? "Creating..." : "Create outcome metadata"}</button>
              </form>

              <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Outcome records</h3>
                <Select label="Outcome" value={selectedOutcomeId} onChange={(value) => load(value).catch((err) => setError(err.message))} options={(state?.outcomes || []).map((item) => [item.id, `${item.title || item.id} / ${item.outcome_status}`])} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={recordOutcomeStatus} disabled={!selectedOutcomeId || working === "status"}>{working === "status" ? "Recording..." : "Record outcome status"}</button>
              </div>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addEvent}>
                <h3 className="font-semibold text-slate-950">Manual event</h3>
                <Field label="Event title" value={form.event_title} onChange={(value) => setForm({ ...form, event_title: value })} />
                <TextArea label="Event note" value={form.event_note} onChange={(value) => setForm({ ...form, event_note: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="submit" disabled={!selectedOutcomeId || working === "event"}>{working === "event" ? "Recording..." : "Record manual outcome event"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addReceipt}>
                <h3 className="font-semibold text-slate-950">Receipt metadata</h3>
                <Field label="Reference label" value={form.receipt_label} onChange={(value) => setForm({ ...form, receipt_label: value })} />
                <TextArea label="Notes" value={form.receipt_notes} onChange={(value) => setForm({ ...form, receipt_notes: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="submit" disabled={!selectedOutcomeId || working === "receipt"}>{working === "receipt" ? "Adding..." : "Add receipt metadata"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addIssue}>
                <h3 className="font-semibold text-slate-950">Issue metadata</h3>
                <Field label="Issue title" value={form.issue_title} onChange={(value) => setForm({ ...form, issue_title: value })} />
                <TextArea label="Description" value={form.issue_description} onChange={(value) => setForm({ ...form, issue_description: value })} />
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="submit" disabled={!selectedOutcomeId || working === "issue"}>{working === "issue" ? "Adding..." : "Add issue metadata"}</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={resolveIssue} disabled={!firstIssue || working === "resolve"}>Resolve issue metadata</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={createSnapshot} disabled={!selectedOutcomeId || working === "snapshot"}>{working === "snapshot" ? "Creating..." : "Create immutable outcome snapshot"}</button>
                </div>
              </form>
            </div>

            <div className="space-y-4">
              <OutcomeSummary outcome={selectedOutcome} />
              <SimpleList title="Events" items={state?.detail?.events || []} fields={["event_type", "actor_type", "event_title", "occurred_at"]} />
              <SimpleList title="Receipts" items={state?.detail?.receipts || []} fields={["receipt_type", "reference_label", "received_from", "created_at"]} />
              <SimpleList title="Issues" items={state?.detail?.issues || []} fields={["issue_type", "issue_status", "severity", "title"]} />
              <SimpleList title="Snapshots" items={state?.detail?.snapshots || []} fields={["snapshot_type", "immutable", "created_by", "created_at"]} />
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

function OutcomeSummary({ outcome }) {
  if (!outcome) return <EmptyState title="No outcome selected" body="Create outcome metadata from a manual delivery handoff." />
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{outcome.title || outcome.id}</h3>
      <div className="mt-3 grid gap-2 text-sm md:grid-cols-5">
        <Summary label="Status" value={outcome.outcome_status} />
        <Summary label="Events" value={outcome.event_count ?? 0} />
        <Summary label="Receipts" value={outcome.receipt_count ?? 0} />
        <Summary label="Issues" value={outcome.issue_count ?? 0} />
        <Summary label="Snapshots" value={outcome.snapshot_count ?? 0} />
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
