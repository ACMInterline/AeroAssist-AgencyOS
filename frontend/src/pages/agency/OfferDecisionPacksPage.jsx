import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaults = {
  offer_workspace_id: "",
  pack_name: "Offer decision pack",
}

const attachDefaults = {
  advisor_context_id: "",
  advisor_saved_snapshot_id: "",
  offer_option_id: "",
  airline_code: "",
}

const noteDefaults = {
  offer_option_id: "",
  airline_code: "",
  note_title: "Human review note",
  note_body: "Reviewed advisor evidence for this offer decision pack.",
}

export default function OfferDecisionPacksPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaults)
  const [attachForm, setAttachForm] = useState(attachDefaults)
  const [noteForm, setNoteForm] = useState(noteDefaults)
  const [selectedPackId, setSelectedPackId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [working, setWorking] = useState("")

  async function load(nextPackId = selectedPackId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/offer-decision-packs`
    const advisorBase = `/api/agencies/${context.agency.id}/offer-policy-advisor`
    const [summary, packs, options, evidence, warnings, notes, snapshots, workspaces, advisorContexts, advisorSnapshots] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/packs`),
      apiGet(`${base}/options`),
      apiGet(`${base}/evidence`),
      apiGet(`${base}/warnings`),
      apiGet(`${base}/review-notes`),
      apiGet(`${base}/snapshots`),
      apiGet(`/api/agencies/${context.agency.id}/offer-workspaces`),
      apiGet(`${advisorBase}/contexts`),
      apiGet(`${advisorBase}/saved-snapshots`),
    ])
    const items = packs.items || []
    const chosenPackId = nextPackId || items[0]?.id || ""
    setSelectedPackId(chosenPackId)
    setState({
      ...context,
      base,
      summary,
      packs: items,
      options: options.items || [],
      evidence: evidence.items || [],
      warnings: warnings.items || [],
      notes: notes.items || [],
      snapshots: snapshots.items || [],
      workspaces: workspaces.items || [],
      advisorContexts: advisorContexts.items || [],
      advisorSnapshots: advisorSnapshots.items || [],
    })
    if (!form.offer_workspace_id && workspaces.items?.[0]?.id) {
      setForm((current) => ({ ...current, offer_workspace_id: workspaces.items[0].id }))
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedPack = useMemo(
    () => state?.packs?.find((item) => item.id === selectedPackId) || state?.packs?.[0],
    [state, selectedPackId],
  )
  const packOptions = useMemo(() => state?.options?.filter((item) => item.decision_pack_id === selectedPack?.id) || [], [state, selectedPack])
  const packEvidence = useMemo(() => state?.evidence?.filter((item) => item.decision_pack_id === selectedPack?.id) || [], [state, selectedPack])
  const packWarnings = useMemo(() => state?.warnings?.filter((item) => item.decision_pack_id === selectedPack?.id) || [], [state, selectedPack])
  const packNotes = useMemo(() => state?.notes?.filter((item) => item.decision_pack_id === selectedPack?.id) || [], [state, selectedPack])
  const packSnapshots = useMemo(() => state?.snapshots?.filter((item) => item.decision_pack_id === selectedPack?.id) || [], [state, selectedPack])
  const metrics = useMemo(() => [
    ["Decision packs", state?.summary?.decision_pack_count],
    ["Evidence", state?.summary?.option_evidence_count],
    ["Warnings", state?.summary?.warning_count],
    ["Review notes", state?.summary?.review_note_count],
    ["Snapshots", state?.summary?.saved_snapshot_count],
  ], [state])

  async function buildPack(event) {
    event.preventDefault()
    setWorking("build")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`${state.base}/packs/build`, {
        offer_workspace_id: form.offer_workspace_id,
        pack_name: form.pack_name || null,
      })
      setMessage("Decision pack built for human review.")
      await load(result.pack.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function attachEvidence(event) {
    event.preventDefault()
    if (!selectedPack) return
    setWorking("attach")
    setError("")
    setMessage("")
    try {
      await apiPost(`${state.base}/packs/${selectedPack.id}/attach-advisor-evidence`, {
        advisor_context_id: attachForm.advisor_context_id || null,
        advisor_saved_snapshot_id: attachForm.advisor_saved_snapshot_id || null,
        offer_option_id: attachForm.offer_option_id || null,
        airline_code: attachForm.airline_code || null,
      })
      setMessage("Advisor evidence attached.")
      await load(selectedPack.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function saveReviewNote(event) {
    event.preventDefault()
    if (!selectedPack) return
    setWorking("note")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`${state.base}/packs/${selectedPack.id}/review-notes`, {
        ...noteForm,
        offer_option_id: noteForm.offer_option_id || null,
        airline_code: noteForm.airline_code || null,
      })
      await apiPatch(`${state.base}/packs/${selectedPack.id}/review-notes/${result.review_note.id}`, {
        note_status: "reviewed",
      })
      setMessage("Review note saved and marked reviewed.")
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
      await apiPost(`${state.base}/packs/${selectedPack.id}/snapshots`, {
        snapshot_name: `${selectedPack.pack_name} snapshot`,
      })
      setMessage("Decision pack snapshot saved.")
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
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Decision Packs</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Advisor Evidence Review</h2>
              <p className="mt-1 text-sm text-slate-600">Human-reviewed decision packs for offer options and saved advisor evidence.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Human review required</span>
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
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={buildPack}>
                <h3 className="font-semibold text-slate-950">Build decision pack</h3>
                <Select label="Offer workspace" value={form.offer_workspace_id} onChange={(value) => setForm({ ...form, offer_workspace_id: value })} options={(state?.workspaces || []).map((item) => [item.id, item.title || item.id])} />
                <Field label="Pack name" value={form.pack_name} onChange={(value) => setForm({ ...form, pack_name: value })} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "build" || !form.offer_workspace_id}>{working === "build" ? "Building..." : "Build decision pack"}</button>
              </form>

              <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Selected pack</h3>
                <Select label="Decision pack" value={selectedPack?.id || ""} onChange={setSelectedPackId} options={(state?.packs || []).map((item) => [item.id, item.pack_name || item.id])} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={saveSnapshot} disabled={working === "snapshot" || !selectedPack}>{working === "snapshot" ? "Saving..." : "Save immutable snapshot"}</button>
              </div>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={attachEvidence}>
                <h3 className="font-semibold text-slate-950">Attach advisor evidence</h3>
                <Select label="Advisor context" value={attachForm.advisor_context_id} onChange={(value) => setAttachForm({ ...attachForm, advisor_context_id: value })} options={(state?.advisorContexts || []).map((item) => [item.id, item.context_name || item.id])} />
                <Select label="Saved advisor snapshot" value={attachForm.advisor_saved_snapshot_id} onChange={(value) => setAttachForm({ ...attachForm, advisor_saved_snapshot_id: value })} options={(state?.advisorSnapshots || []).map((item) => [item.id, item.snapshot_name || item.id])} />
                <Field label="Offer option ID" value={attachForm.offer_option_id} onChange={(value) => setAttachForm({ ...attachForm, offer_option_id: value })} />
                <Field label="Airline code" value={attachForm.airline_code} onChange={(value) => setAttachForm({ ...attachForm, airline_code: value.toUpperCase() })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "attach" || !selectedPack || (!attachForm.advisor_context_id && !attachForm.advisor_saved_snapshot_id)}>{working === "attach" ? "Attaching..." : "Attach evidence"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={saveReviewNote}>
                <h3 className="font-semibold text-slate-950">Review note</h3>
                <Field label="Offer option ID" value={noteForm.offer_option_id} onChange={(value) => setNoteForm({ ...noteForm, offer_option_id: value })} />
                <Field label="Airline code" value={noteForm.airline_code} onChange={(value) => setNoteForm({ ...noteForm, airline_code: value.toUpperCase() })} />
                <Field label="Title" value={noteForm.note_title} onChange={(value) => setNoteForm({ ...noteForm, note_title: value })} />
                <TextArea label="Note" value={noteForm.note_body} onChange={(value) => setNoteForm({ ...noteForm, note_body: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "note" || !selectedPack}>{working === "note" ? "Saving..." : "Save review note"}</button>
              </form>
            </div>

            <div className="space-y-4">
              <PackSummary pack={selectedPack} />
              <OptionTable options={packOptions} />
              <EvidenceTable evidence={packEvidence} />
              <SimpleList title="Warnings" items={packWarnings} fields={["warning_level", "airline_code", "warning_type", "message"]} />
              <SimpleList title="Review notes" items={packNotes} fields={["airline_code", "note_title", "note_status", "created_at"]} />
              <SimpleList title="Snapshots" items={packSnapshots} fields={["snapshot_name", "immutable", "created_at"]} />
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
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value || ""} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function TextArea({ label, value, onChange }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <textarea className="mt-1 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value || ""} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function Select({ label, value, onChange, options }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value || ""} onChange={(event) => onChange(event.target.value)}>
        <option value="">Select</option>
        {options.map(([optionValue, labelText]) => <option value={optionValue} key={optionValue}>{labelText}</option>)}
      </select>
    </label>
  )
}

function PackSummary({ pack }) {
  if (!pack) return <EmptyState title="No decision pack" body="No offer decision pack is selected." />
  const fields = [
    ["Workspace", pack.offer_workspace_summary_json?.title || pack.offer_workspace_id],
    ["Status", pack.pack_status],
    ["Airlines", (pack.airline_codes || []).join(", ")],
    ["Warning", pack.warning_level],
    ["Complexity", pack.operational_complexity_score ?? 0],
    ["Manual review", pack.manual_review_required ? "Required" : "Not flagged"],
  ]
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="font-semibold text-slate-950">{pack.pack_name}</h3>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{pack.metadata_only ? "Metadata only" : "Review"}</span>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {fields.map(([label, value]) => (
          <div key={label}>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
            <p className="mt-1 break-words text-sm text-slate-800">{value || "-"}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function OptionTable({ options }) {
  if (!options.length) return <EmptyState title="No option evidence" body="Build a decision pack to create option-level evidence." />
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">Option review rows</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-[860px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              {["Option", "Airline", "Warning", "Complexity", "Evidence", "Unresolved", "Advisor snapshot"].map((header) => <th className="px-3 py-2" key={header}>{header}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {options.map((option) => (
              <tr key={option.id}>
                <td className="px-3 py-3 font-semibold text-slate-950">{option.option_label || option.offer_option_id}</td>
                <td className="px-3 py-3">{option.airline_code || "-"}</td>
                <td className="px-3 py-3">{option.warning_level}</td>
                <td className="px-3 py-3">{option.operational_complexity_score ?? 0}</td>
                <td className="px-3 py-3">{option.evidence_count ?? 0}</td>
                <td className="px-3 py-3">{option.unresolved_warning_count ?? 0}</td>
                <td className="px-3 py-3">{option.advisor_saved_snapshot_id || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function EvidenceTable({ evidence }) {
  if (!evidence.length) return <EmptyState title="No evidence" body="No decision pack evidence found." />
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">Advisor evidence</h3>
      </div>
      <div className="divide-y divide-slate-100">
        {evidence.slice(0, 10).map((item) => (
          <div className="grid gap-2 p-4 text-sm md:grid-cols-4" key={item.id}>
            <span className="font-semibold text-slate-950">{item.evidence_type}</span>
            <span className="text-slate-700">{item.airline_code || "-"}</span>
            <span className="truncate text-slate-700">{item.evidence_title}</span>
            <span className="truncate text-slate-500">{item.source_record_id || "-"}</span>
          </div>
        ))}
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
