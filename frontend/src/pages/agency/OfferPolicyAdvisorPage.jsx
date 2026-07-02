import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaults = {
  offer_workspace_id: "",
  offer_option_id: "",
  context_name: "Offer policy advisor context",
  airline_codes: "LH, AF",
  domain_code: "mobility",
  family_code: "wheelchair",
  variant_code: "wchr",
}

const noteDefaults = {
  airline_code: "",
  note_title: "Manual advisor decision note",
  note_body: "Reviewed policy advisor metadata with the agent.",
}

export default function OfferPolicyAdvisorPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaults)
  const [noteForm, setNoteForm] = useState(noteDefaults)
  const [selectedContextId, setSelectedContextId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [working, setWorking] = useState("")

  async function load(nextContextId = selectedContextId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/offer-policy-advisor`
    const [summary, contexts, rows, warnings, notes, snapshots, workspaces] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/contexts`),
      apiGet(`${base}/airline-rows`),
      apiGet(`${base}/warnings`),
      apiGet(`${base}/decision-notes`),
      apiGet(`${base}/saved-snapshots`),
      apiGet(`/api/agencies/${context.agency.id}/offer-workspaces`),
    ])
    const items = contexts.items || []
    const chosenContextId = nextContextId || items[0]?.id || ""
    setSelectedContextId(chosenContextId)
    setState({
      ...context,
      base,
      summary,
      contexts: items,
      rows: rows.items || [],
      warnings: warnings.items || [],
      notes: notes.items || [],
      snapshots: snapshots.items || [],
      workspaces: workspaces.items || [],
    })
    if (!form.offer_workspace_id && workspaces.items?.[0]?.id) {
      setForm((current) => ({ ...current, offer_workspace_id: workspaces.items[0].id }))
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedContext = useMemo(
    () => state?.contexts?.find((item) => item.id === selectedContextId) || state?.contexts?.[0],
    [state, selectedContextId],
  )
  const contextRows = useMemo(() => state?.rows?.filter((item) => item.context_id === selectedContext?.id) || [], [state, selectedContext])
  const contextWarnings = useMemo(() => state?.warnings?.filter((item) => item.context_id === selectedContext?.id) || [], [state, selectedContext])
  const contextNotes = useMemo(() => state?.notes?.filter((item) => item.context_id === selectedContext?.id) || [], [state, selectedContext])
  const contextSnapshots = useMemo(() => state?.snapshots?.filter((item) => item.context_id === selectedContext?.id) || [], [state, selectedContext])
  const metrics = useMemo(() => [
    ["Contexts", state?.summary?.context_count],
    ["Airline rows", state?.summary?.airline_row_count],
    ["Warnings", state?.summary?.warning_count],
    ["Decision notes", state?.summary?.decision_note_count],
    ["Snapshots", state?.summary?.saved_snapshot_count],
  ], [state])

  async function buildContext(event) {
    event.preventDefault()
    setWorking("build")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`${state.base}/contexts/build`, buildPayload(form))
      setMessage(`Advisor context built for ${(result.context.airline_codes || []).join(", ")}.`)
      await load(result.context.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function evaluateContext() {
    if (!selectedContext) return
    setWorking("evaluate")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`${state.base}/contexts/${selectedContext.id}/evaluate`, {})
      setMessage(`Advisor evaluation created ${(result.airline_rows || []).length} offer-linked rows.`)
      await load(selectedContext.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function saveDecisionNote(event) {
    event.preventDefault()
    if (!selectedContext) return
    setWorking("note")
    setError("")
    setMessage("")
    try {
      await apiPost(`${state.base}/contexts/${selectedContext.id}/decision-notes`, {
        ...noteForm,
        airline_code: noteForm.airline_code || null,
      })
      setMessage("Manual decision note saved.")
      await load(selectedContext.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function saveSnapshot() {
    if (!selectedContext) return
    setWorking("snapshot")
    setError("")
    setMessage("")
    try {
      await apiPost(`${state.base}/contexts/${selectedContext.id}/saved-snapshots`, {
        snapshot_name: `${selectedContext.context_name} saved snapshot`,
      })
      setMessage("Offer advisor snapshot saved.")
      await load(selectedContext.id)
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
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Policy Advisor</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Offer-Linked Advisor Context</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only policy, mechanics, pricing, and warning context for offer workspaces.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Auto recommendation disabled</span>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[390px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={buildContext}>
                <h3 className="font-semibold text-slate-950">Build context</h3>
                <Select label="Offer workspace" value={form.offer_workspace_id} onChange={(value) => setForm({ ...form, offer_workspace_id: value })} options={(state?.workspaces || []).map((item) => [item.id, item.title || item.id])} />
                <Field label="Offer option ID" value={form.offer_option_id} onChange={(value) => setForm({ ...form, offer_option_id: value })} />
                <Field label="Context name" value={form.context_name} onChange={(value) => setForm({ ...form, context_name: value })} />
                <Field label="Airline codes" value={form.airline_codes} onChange={(value) => setForm({ ...form, airline_codes: value.toUpperCase() })} />
                <Field label="Domain code" value={form.domain_code} onChange={(value) => setForm({ ...form, domain_code: value })} />
                <Field label="Family code" value={form.family_code} onChange={(value) => setForm({ ...form, family_code: value })} />
                <Field label="Variant code" value={form.variant_code} onChange={(value) => setForm({ ...form, variant_code: value })} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "build" || !form.offer_workspace_id}>{working === "build" ? "Building..." : "Build advisor context"}</button>
              </form>

              <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Selected context</h3>
                <Select label="Context" value={selectedContext?.id || ""} onChange={setSelectedContextId} options={(state?.contexts || []).map((item) => [item.id, item.context_name || item.id])} />
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={evaluateContext} disabled={working === "evaluate" || !selectedContext}>{working === "evaluate" ? "Evaluating..." : "Evaluate advisor"}</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={saveSnapshot} disabled={working === "snapshot" || !selectedContext}>{working === "snapshot" ? "Saving..." : "Save snapshot"}</button>
                </div>
              </div>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={saveDecisionNote}>
                <h3 className="font-semibold text-slate-950">Decision note</h3>
                <Field label="Airline code" value={noteForm.airline_code} onChange={(value) => setNoteForm({ ...noteForm, airline_code: value.toUpperCase() })} />
                <Field label="Title" value={noteForm.note_title} onChange={(value) => setNoteForm({ ...noteForm, note_title: value })} />
                <TextArea label="Note" value={noteForm.note_body} onChange={(value) => setNoteForm({ ...noteForm, note_body: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "note" || !selectedContext}>{working === "note" ? "Saving..." : "Save manual note"}</button>
              </form>
            </div>

            <div className="space-y-4">
              <ContextSummary context={selectedContext} />
              <AirlineRows rows={contextRows} />
              <SimpleList title="Warnings" items={contextWarnings} fields={["warning_level", "airline_code", "warning_type", "message"]} />
              <SimpleList title="Decision notes" items={contextNotes} fields={["airline_code", "note_title", "note_status", "created_at"]} />
              <SimpleList title="Saved snapshots" items={contextSnapshots} fields={["snapshot_name", "advisor_result_id", "created_at"]} />
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function buildPayload(values) {
  return {
    offer_workspace_id: values.offer_workspace_id,
    offer_option_id: values.offer_option_id || null,
    context_name: values.context_name || null,
    airline_codes: splitCsv(values.airline_codes),
    domain_code: values.domain_code || null,
    family_code: values.family_code || null,
    variant_code: values.variant_code || null,
  }
}

function splitCsv(value) {
  return String(value || "").split(",").map((item) => item.trim()).filter(Boolean)
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

function ContextSummary({ context }) {
  if (!context) return <EmptyState title="No advisor context" body="No offer policy advisor context is selected." />
  const fields = [
    ["Workspace", context.offer_workspace_summary_json?.title || context.offer_workspace_id],
    ["Airlines", (context.airline_codes || []).join(", ")],
    ["Taxonomy", [context.domain_code, context.family_code, context.variant_code].filter(Boolean).join(" / ")],
    ["Comparison snapshot", context.policy_comparison_snapshot_id || "-"],
    ["Advisor result", context.advisor_result_id || "-"],
    ["Quote results", (context.quote_result_ids || []).length],
  ]
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-semibold text-slate-950">{context.context_name}</h3>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{context.context_status}</span>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {fields.map(([label, value]) => (
          <div key={label}>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
            <p className="mt-1 break-words text-sm text-slate-800">{value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function AirlineRows({ rows }) {
  if (!rows.length) return <EmptyState title="No airline rows" body="Evaluate the selected context to create offer-linked advisory rows." />
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">Airline comparison rows</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-[980px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              {["Airline", "Warning", "Complexity", "Manual contact", "EMD", "Pricing", "Quote result", "Advisor"].map((header) => <th className="px-3 py-2" key={header}>{header}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row) => (
              <tr key={row.id}>
                <td className="px-3 py-3 font-semibold text-slate-950">{row.airline_code}</td>
                <td className="px-3 py-3">{row.warning_level}</td>
                <td className="px-3 py-3">{row.operational_complexity_score ?? 0}</td>
                <td className="px-3 py-3">{row.manual_contact_required ? "Yes" : "No"}</td>
                <td className="px-3 py-3">{row.emd_required ? "Required" : "Not indicated"}</td>
                <td className="px-3 py-3">{row.pricing_summary || "-"}</td>
                <td className="px-3 py-3">{row.quote_result_id || "-"}</td>
                <td className="px-3 py-3">{row.advisor_summary || "-"}</td>
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
