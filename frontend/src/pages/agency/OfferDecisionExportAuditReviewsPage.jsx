import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaults = {
  outcome_id: "",
  title: "Offer decision export audit review",
  finding_title: "Audit review finding metadata",
  finding_description: "Human-recorded audit finding.",
  checklist_key: "manual_audit_note",
  checklist_label: "Manual audit checklist metadata",
}

export default function OfferDecisionExportAuditReviewsPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaults)
  const [selectedReviewId, setSelectedReviewId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [working, setWorking] = useState("")

  async function load(nextReviewId = selectedReviewId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/offer-decision-export-audit-reviews`
    const outcomeBase = `/api/agencies/${context.agency.id}/offer-decision-export-delivery-outcomes`
    const [summary, reviewsResult, outcomesResult] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/reviews`),
      apiGet(`${outcomeBase}/outcomes`),
    ])
    const reviews = reviewsResult.items || []
    const chosenReviewId = nextReviewId || reviews[0]?.id || ""
    const detail = chosenReviewId ? await apiGet(`${base}/reviews/${chosenReviewId}`) : null
    setSelectedReviewId(chosenReviewId)
    setState({
      ...context,
      base,
      summary,
      reviews,
      outcomes: outcomesResult.items || [],
      detail,
    })
    const firstOutcome = outcomesResult.items?.[0]
    setForm((current) => ({ ...current, outcome_id: current.outcome_id || firstOutcome?.id || "" }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedReview = state?.detail?.review || state?.reviews?.find((item) => item.id === selectedReviewId)
  const firstFinding = state?.detail?.findings?.find((item) => item.finding_status === "open")
  const firstChecklist = state?.detail?.checklist_items?.find((item) => item.item_status !== "passed")
  const metrics = useMemo(() => [
    ["Reviews", state?.summary?.review_count],
    ["Findings", state?.summary?.finding_count],
    ["Checklist", state?.summary?.checklist_item_count],
    ["Snapshots", state?.summary?.snapshot_count],
    ["Score", selectedReview?.completion_score],
  ], [state, selectedReview])

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

  function createReview(event) {
    event.preventDefault()
    runAction("review", async () => {
      const result = await apiPost(`${state.base}/reviews`, {
        outcome_id: form.outcome_id,
        title: form.title || null,
        review_scope: "full_lifecycle",
      })
      setMessage("Audit review metadata created.")
      await load(result.review.id)
    })
  }

  function updateStatus() {
    if (!selectedReviewId) return
    runAction("status", async () => {
      await apiPatch(`${state.base}/reviews/${selectedReviewId}/status`, {
        review_status: "in_review",
        status_reason: "Human audit review metadata recorded.",
      })
      setMessage("Audit review status metadata recorded.")
      await load(selectedReviewId)
    })
  }

  function addFinding(event) {
    event.preventDefault()
    if (!selectedReviewId) return
    runAction("finding", async () => {
      await apiPost(`${state.base}/reviews/${selectedReviewId}/findings`, {
        finding_type: "metadata_gap",
        severity: "medium",
        title: form.finding_title,
        description: form.finding_description,
      })
      setMessage("Audit finding metadata added.")
      await load(selectedReviewId)
    })
  }

  function resolveFinding() {
    if (!firstFinding) return
    runAction("resolve", async () => {
      await apiPatch(`${state.base}/findings/${firstFinding.id}`, {
        finding_status: "resolved",
        resolution_notes: "Human-recorded finding resolution metadata.",
      })
      setMessage("Finding resolution metadata recorded.")
      await load(selectedReviewId)
    })
  }

  function addChecklist(event) {
    event.preventDefault()
    if (!selectedReviewId) return
    runAction("checklist", async () => {
      await apiPost(`${state.base}/reviews/${selectedReviewId}/checklist-items`, {
        item_key: form.checklist_key,
        label: form.checklist_label,
        item_status: "pending",
      })
      setMessage("Checklist metadata added.")
      await load(selectedReviewId)
    })
  }

  function passChecklist() {
    if (!firstChecklist) return
    runAction("pass-checklist", async () => {
      await apiPatch(`${state.base}/checklist-items/${firstChecklist.id}`, {
        item_status: "passed",
        notes: "Human audit checklist pass recorded.",
      })
      setMessage("Checklist pass metadata recorded.")
      await load(selectedReviewId)
    })
  }

  function createSnapshot() {
    if (!selectedReviewId) return
    runAction("snapshot", async () => {
      await apiPost(`${state.base}/reviews/${selectedReviewId}/snapshots`, {
        snapshot_type: "checklist_review",
      })
      setMessage("Immutable audit review snapshot created.")
      await load(selectedReviewId)
    })
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Decision Export Audit</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Audit Review Foundation</h2>
              <p className="mt-1 text-sm text-slate-600">Review lifecycle completeness, trails, issues, and immutable snapshot coverage as metadata only.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Review only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">No execution</span>
            </div>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[410px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createReview}>
                <h3 className="font-semibold text-slate-950">Create audit review</h3>
                <Select label="Manual outcome" value={form.outcome_id} onChange={(value) => setForm({ ...form, outcome_id: value })} options={(state?.outcomes || []).map((item) => [item.id, `${item.title || item.id} / ${item.outcome_status}`])} />
                <Field label="Title" value={form.title} onChange={(value) => setForm({ ...form, title: value })} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "review" || !form.outcome_id}>{working === "review" ? "Creating..." : "Create audit review metadata"}</button>
              </form>

              <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Review records</h3>
                <Select label="Audit review" value={selectedReviewId} onChange={(value) => load(value).catch((err) => setError(err.message))} options={(state?.reviews || []).map((item) => [item.id, `${item.title || item.id} / ${item.review_status}`])} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={updateStatus} disabled={!selectedReviewId || working === "status"}>Record review status</button>
              </div>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addFinding}>
                <h3 className="font-semibold text-slate-950">Findings</h3>
                <Field label="Finding title" value={form.finding_title} onChange={(value) => setForm({ ...form, finding_title: value })} />
                <TextArea label="Description" value={form.finding_description} onChange={(value) => setForm({ ...form, finding_description: value })} />
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="submit" disabled={!selectedReviewId || working === "finding"}>Add finding metadata</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={resolveFinding} disabled={!firstFinding || working === "resolve"}>Resolve finding metadata</button>
                </div>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addChecklist}>
                <h3 className="font-semibold text-slate-950">Checklist</h3>
                <Field label="Item key" value={form.checklist_key} onChange={(value) => setForm({ ...form, checklist_key: value })} />
                <Field label="Label" value={form.checklist_label} onChange={(value) => setForm({ ...form, checklist_label: value })} />
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="submit" disabled={!selectedReviewId || working === "checklist"}>Add checklist metadata</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={passChecklist} disabled={!firstChecklist || working === "pass-checklist"}>Record checklist pass</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={createSnapshot} disabled={!selectedReviewId || working === "snapshot"}>Create immutable review snapshot</button>
                </div>
              </form>
            </div>

            <div className="space-y-4">
              <ReviewSummary review={selectedReview} />
              <SimpleList title="Findings" items={state?.detail?.findings || []} fields={["finding_type", "severity", "finding_status", "title"]} />
              <SimpleList title="Checklist" items={state?.detail?.checklist_items || []} fields={["item_key", "item_status", "required", "label"]} />
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

function ReviewSummary({ review }) {
  if (!review) return <EmptyState title="No audit review selected" body="Create audit review metadata from a completed manual outcome trail." />
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{review.title || review.id}</h3>
      <div className="mt-3 grid gap-2 text-sm md:grid-cols-5">
        <Summary label="Status" value={review.review_status} />
        <Summary label="Score" value={review.completion_score} />
        <Summary label="Findings" value={review.finding_count ?? 0} />
        <Summary label="Checklist" value={review.checklist_count ?? 0} />
        <Summary label="Snapshots" value={review.snapshot_count ?? 0} />
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
