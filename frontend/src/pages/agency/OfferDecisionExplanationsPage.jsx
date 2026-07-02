import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const explanationDefaults = {
  decision_pack_id: "",
  offer_option_id: "",
  title: "Offer decision explanation",
  explanation_type: "summary",
  explanation_text: "Human-reviewed explanation for this offer decision.",
  finalized: false,
}

const reasonDefaults = {
  reason_category: "manual",
  importance: "medium",
  text: "Manual decision reason recorded by agency staff.",
}

const acknowledgementDefaults = {
  acknowledged_by: "",
  acknowledgement_type: "reviewed",
  notes: "Decision explanation reviewed.",
}

export default function OfferDecisionExplanationsPage() {
  const [state, setState] = useState(null)
  const [selectedPackId, setSelectedPackId] = useState("")
  const [explanationForm, setExplanationForm] = useState(explanationDefaults)
  const [reasonForm, setReasonForm] = useState(reasonDefaults)
  const [ackForm, setAckForm] = useState(acknowledgementDefaults)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [working, setWorking] = useState("")

  async function load(nextPackId = selectedPackId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/offer-decision-explanations`
    const packsBase = `/api/agencies/${context.agency.id}/offer-decision-packs`
    const [summary, packs, explanations, timeline, evidence, reasons, acknowledgements, snapshots] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${packsBase}/packs`),
      apiGet(`${base}/explanations`),
      apiGet(`${base}/timeline`),
      apiGet(`${base}/evidence`),
      apiGet(`${base}/reasons`),
      apiGet(`${base}/acknowledgements`),
      apiGet(`${base}/snapshots`),
    ])
    const packItems = packs.items || []
    const chosenPackId = nextPackId || packItems[0]?.id || ""
    setSelectedPackId(chosenPackId)
    setState({
      ...context,
      base,
      packsBase,
      summary,
      packs: packItems,
      explanations: explanations.items || [],
      timeline: timeline.items || [],
      evidence: evidence.items || [],
      reasons: reasons.items || [],
      acknowledgements: acknowledgements.items || [],
      snapshots: snapshots.items || [],
    })
    if (!explanationForm.decision_pack_id && chosenPackId) {
      setExplanationForm((current) => ({ ...current, decision_pack_id: chosenPackId }))
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedPack = useMemo(
    () => state?.packs?.find((item) => item.id === selectedPackId) || state?.packs?.[0],
    [state, selectedPackId],
  )
  const selectedPackRecords = useMemo(() => {
    const packId = selectedPack?.id
    return {
      explanations: state?.explanations?.filter((item) => item.decision_pack_id === packId) || [],
      timeline: state?.timeline?.filter((item) => item.decision_pack_id === packId) || [],
      evidence: state?.evidence?.filter((item) => item.decision_pack_id === packId) || [],
      reasons: state?.reasons?.filter((item) => item.decision_pack_id === packId) || [],
      acknowledgements: state?.acknowledgements?.filter((item) => item.decision_pack_id === packId) || [],
      snapshots: state?.snapshots?.filter((item) => item.decision_pack_id === packId) || [],
    }
  }, [state, selectedPack])

  const metrics = useMemo(() => [
    ["Explanations", state?.summary?.explanations],
    ["Timeline events", state?.summary?.timeline_events],
    ["Evidence refs", state?.summary?.evidence_references],
    ["Reasons", state?.summary?.reasons],
    ["Snapshots", state?.summary?.snapshots],
  ], [state])

  function selectPack(packId) {
    setSelectedPackId(packId)
    setExplanationForm((current) => ({ ...current, decision_pack_id: packId }))
  }

  async function createExplanation(event) {
    event.preventDefault()
    setWorking("explanation")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`${state.base}/explanations`, {
        ...explanationForm,
        decision_pack_id: explanationForm.decision_pack_id || selectedPack?.id,
        offer_option_id: explanationForm.offer_option_id || null,
      })
      setMessage("Decision explanation recorded for human review.")
      await load(result.explanation.decision_pack_id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function finalizeExplanation(explanation) {
    setWorking(`finalize-${explanation.id}`)
    setError("")
    setMessage("")
    try {
      await apiPatch(`${state.base}/explanations/${explanation.id}`, { finalized: true })
      setMessage("Explanation finalized.")
      await load(explanation.decision_pack_id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function createReason(event) {
    event.preventDefault()
    if (!selectedPack) return
    setWorking("reason")
    setError("")
    setMessage("")
    try {
      await apiPost(`${state.base}/reasons`, { ...reasonForm, decision_pack_id: selectedPack.id })
      setMessage("Decision reason recorded.")
      await load(selectedPack.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function createAcknowledgement(event) {
    event.preventDefault()
    if (!selectedPack) return
    setWorking("acknowledgement")
    setError("")
    setMessage("")
    try {
      await apiPost(`${state.base}/acknowledgements`, {
        ...ackForm,
        decision_pack_id: selectedPack.id,
        acknowledged_by: ackForm.acknowledged_by || state?.me?.user?.email || "agency-user",
      })
      setMessage("Decision acknowledgement recorded.")
      await load(selectedPack.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function appendTimelineEvent() {
    if (!selectedPack) return
    setWorking("timeline")
    setError("")
    setMessage("")
    try {
      await apiPost(`${state.base}/timeline-events`, {
        decision_pack_id: selectedPack.id,
        event_type: "review_started",
        actor_type: "agency",
        description: "Human review timeline event recorded.",
      })
      setMessage("Timeline event appended.")
      await load(selectedPack.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function saveSnapshot() {
    if (!selectedPack) return
    setWorking("snapshot")
    setError("")
    setMessage("")
    try {
      await apiPost(`${state.base}/snapshots`, {
        decision_pack_id: selectedPack.id,
        snapshot_name: `${selectedPack.pack_name || "Offer decision"} explanation audit snapshot`,
      })
      setMessage("Decision explanation audit snapshot saved.")
      await load(selectedPack.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Decision Explanations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Explanation and Decision Timeline</h2>
              <p className="mt-1 text-sm text-slate-600">Human-reviewed explanation, reasons, evidence references, acknowledgements, and immutable audit snapshots.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Human review only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">No automatic recommendation</span>
            </div>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[390px_minmax(0,1fr)]">
            <div className="space-y-4">
              <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Decision pack</h3>
                <Select label="Pack" value={selectedPack?.id || ""} onChange={selectPack} options={(state?.packs || []).map((item) => [item.id, item.pack_name || item.id])} />
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={appendTimelineEvent} disabled={working === "timeline" || !selectedPack}>{working === "timeline" ? "Appending..." : "Append review event"}</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={saveSnapshot} disabled={working === "snapshot" || !selectedPack}>{working === "snapshot" ? "Saving..." : "Save audit snapshot"}</button>
                </div>
              </div>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createExplanation}>
                <h3 className="font-semibold text-slate-950">Create explanation</h3>
                <Field label="Title" value={explanationForm.title} onChange={(value) => setExplanationForm({ ...explanationForm, title: value })} />
                <Select label="Type" value={explanationForm.explanation_type} onChange={(value) => setExplanationForm({ ...explanationForm, explanation_type: value })} options={["summary", "operational", "policy", "pricing", "mechanics", "warning", "evidence", "review", "comparison", "detailed_explanation"].map((item) => [item, item])} />
                <Field label="Offer option ID" value={explanationForm.offer_option_id} onChange={(value) => setExplanationForm({ ...explanationForm, offer_option_id: value })} />
                <TextArea label="Explanation" value={explanationForm.explanation_text} onChange={(value) => setExplanationForm({ ...explanationForm, explanation_text: value })} />
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input type="checkbox" checked={explanationForm.finalized} onChange={(event) => setExplanationForm({ ...explanationForm, finalized: event.target.checked })} />
                  Finalize after creation
                </label>
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "explanation" || !selectedPack}>{working === "explanation" ? "Saving..." : "Record explanation"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createReason}>
                <h3 className="font-semibold text-slate-950">Decision reason</h3>
                <Select label="Category" value={reasonForm.reason_category} onChange={(value) => setReasonForm({ ...reasonForm, reason_category: value })} options={["policy", "commercial", "operational", "customer", "airline", "manual", "pricing", "mechanics", "risk"].map((item) => [item, item])} />
                <Select label="Importance" value={reasonForm.importance} onChange={(value) => setReasonForm({ ...reasonForm, importance: value })} options={["low", "medium", "high", "critical"].map((item) => [item, item])} />
                <TextArea label="Reason" value={reasonForm.text} onChange={(value) => setReasonForm({ ...reasonForm, text: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "reason" || !selectedPack}>{working === "reason" ? "Saving..." : "Record reason"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createAcknowledgement}>
                <h3 className="font-semibold text-slate-950">Acknowledgement</h3>
                <Field label="Acknowledged by" value={ackForm.acknowledged_by} onChange={(value) => setAckForm({ ...ackForm, acknowledged_by: value })} />
                <Select label="Type" value={ackForm.acknowledgement_type} onChange={(value) => setAckForm({ ...ackForm, acknowledgement_type: value })} options={["read", "reviewed", "accepted", "rejected", "requires_followup"].map((item) => [item, item])} />
                <TextArea label="Notes" value={ackForm.notes} onChange={(value) => setAckForm({ ...ackForm, notes: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "acknowledgement" || !selectedPack}>{working === "acknowledgement" ? "Saving..." : "Record acknowledgement"}</button>
              </form>
            </div>

            <div className="space-y-4">
              <PackSummary pack={selectedPack} />
              <ExplanationsTable explanations={selectedPackRecords.explanations} onFinalize={finalizeExplanation} working={working} />
              <SimpleList title="Timeline" items={selectedPackRecords.timeline} fields={["event_type", "actor_type", "description", "timestamp"]} />
              <SimpleList title="Evidence references" items={selectedPackRecords.evidence} fields={["reference_type", "display_name", "reference_id", "summary"]} />
              <SimpleList title="Reasons" items={selectedPackRecords.reasons} fields={["reason_category", "importance", "text", "created_at"]} />
              <SimpleList title="Acknowledgements" items={selectedPackRecords.acknowledgements} fields={["acknowledgement_type", "acknowledged_by", "notes", "acknowledged_at"]} />
              <SimpleList title="Audit snapshots" items={selectedPackRecords.snapshots} fields={["snapshot_name", "immutable", "created_at"]} />
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

function TextArea({ label, value, onChange }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <textarea className="mt-1 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function PackSummary({ pack }) {
  if (!pack) return <EmptyState title="No decision pack selected" body="Build a decision pack before recording explanations." />
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{pack.pack_name || pack.id}</h3>
      <div className="mt-3 grid gap-2 text-sm md:grid-cols-3">
        <Summary label="Workspace" value={pack.offer_workspace_id} />
        <Summary label="Warning" value={pack.warning_level} />
        <Summary label="Evidence" value={pack.evidence_count ?? 0} />
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

function ExplanationsTable({ explanations, onFinalize, working }) {
  if (!explanations.length) return <EmptyState title="No explanations" body="No explanation records found for this decision pack." />
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">Explanations</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-[820px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              {["Title", "Type", "Finalized", "Archived", "Created", "Action"].map((header) => <th className="px-3 py-2" key={header}>{header}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {explanations.map((item) => (
              <tr key={item.id}>
                <td className="px-3 py-3 font-semibold text-slate-950">{item.title}</td>
                <td className="px-3 py-3">{item.explanation_type}</td>
                <td className="px-3 py-3">{formatValue(item.finalized)}</td>
                <td className="px-3 py-3">{formatValue(item.archived)}</td>
                <td className="px-3 py-3">{formatValue(item.created_at)}</td>
                <td className="px-3 py-3">
                  <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold disabled:opacity-60" type="button" onClick={() => onFinalize(item)} disabled={item.finalized || working === `finalize-${item.id}`}>
                    {working === `finalize-${item.id}` ? "Finalizing..." : "Finalize"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
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
        {items.slice(0, 8).map((item) => (
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
