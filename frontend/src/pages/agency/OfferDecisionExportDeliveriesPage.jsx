import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaults = {
  export_id: "",
  preview_id: "",
  release_readiness_id: "",
  title: "Manual delivery handoff metadata",
  delivery_method: "manual_email",
  recipient_name: "Client reviewer",
  recipient_email: "Metadata only. No sending.",
  attachment_filename: "decision-export.pdf metadata",
  instruction_title: "Manual handoff note",
  instruction_body: "Human agent reviews the metadata package outside AgencyOS. No automatic sending or public link is created.",
}

export default function OfferDecisionExportDeliveriesPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaults)
  const [selectedHandoffId, setSelectedHandoffId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [working, setWorking] = useState("")

  async function load(nextHandoffId = selectedHandoffId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/offer-decision-export-deliveries`
    const exportBase = `/api/agencies/${context.agency.id}/offer-decision-exports`
    const previewBase = `/api/agencies/${context.agency.id}/offer-decision-export-previews`
    const releaseBase = `/api/agencies/${context.agency.id}/offer-decision-export-releases`
    const [summary, handoffsResult, exportsResult, previewsResult, readinessResult] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/handoffs`),
      apiGet(`${exportBase}/exports`),
      apiGet(`${previewBase}/previews`),
      apiGet(`${releaseBase}/readiness`),
    ])
    const handoffs = handoffsResult.items || []
    const chosenHandoffId = nextHandoffId || handoffs[0]?.id || ""
    const detail = chosenHandoffId ? await apiGet(`${base}/handoffs/${chosenHandoffId}`) : null
    setSelectedHandoffId(chosenHandoffId)
    setState({
      ...context,
      base,
      summary,
      handoffs,
      exports: exportsResult.items || [],
      previews: previewsResult.items || [],
      readiness: readinessResult.items || [],
      detail,
    })
    const firstExport = exportsResult.items?.[0]
    const firstPreview = previewsResult.items?.[0]
    const firstReadiness = readinessResult.items?.[0]
    setForm((current) => ({
      ...current,
      export_id: current.export_id || firstReadiness?.export_id || firstPreview?.export_id || firstExport?.id || "",
      preview_id: current.preview_id || firstReadiness?.preview_id || firstPreview?.id || "",
      release_readiness_id: current.release_readiness_id || firstReadiness?.id || "",
    }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedHandoff = state?.detail?.handoff || state?.handoffs?.find((item) => item.id === selectedHandoffId)
  const firstRecipient = state?.detail?.recipients?.[0]
  const firstInstruction = state?.detail?.instructions?.[0]
  const metrics = useMemo(() => [
    ["Handoffs", state?.summary?.handoff_count],
    ["Recipients", state?.summary?.recipient_count],
    ["Attachments", state?.summary?.attachment_count],
    ["Instructions", state?.summary?.instruction_count],
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

  function createHandoff(event) {
    event.preventDefault()
    runAction("handoff", async () => {
      const result = await apiPost(`${state.base}/handoffs`, {
        export_id: form.export_id,
        preview_id: form.preview_id || null,
        release_readiness_id: form.release_readiness_id || null,
        title: form.title || null,
        delivery_method: form.delivery_method,
      })
      setMessage("Manual handoff metadata created.")
      await load(result.handoff.id)
    })
  }

  function addRecipient(event) {
    event.preventDefault()
    if (!selectedHandoffId) return
    runAction("recipient", async () => {
      await apiPost(`${state.base}/handoffs/${selectedHandoffId}/recipients`, {
        recipient_type: "client",
        display_name: form.recipient_name,
        email_metadata: form.recipient_email,
        delivery_method: form.delivery_method,
        notes: "Recipient metadata only. AgencyOS did not send email or SMS.",
      })
      setMessage("Recipient metadata added.")
      await load(selectedHandoffId)
    })
  }

  function addAttachment(event) {
    event.preventDefault()
    if (!selectedHandoffId) return
    runAction("attachment", async () => {
      await apiPost(`${state.base}/handoffs/${selectedHandoffId}/attachments`, {
        preview_id: selectedHandoff?.preview_id || form.preview_id || null,
        filename: form.attachment_filename,
        file_type: "pdf_metadata",
        source_type: "preview_metadata",
        size_label: "metadata only",
      })
      setMessage("Attachment metadata added.")
      await load(selectedHandoffId)
    })
  }

  function addInstruction(event) {
    event.preventDefault()
    if (!selectedHandoffId) return
    runAction("instruction", async () => {
      await apiPost(`${state.base}/handoffs/${selectedHandoffId}/instructions`, {
        instruction_type: "compliance_note",
        title: form.instruction_title,
        body: form.instruction_body,
        required: true,
      })
      setMessage("Instruction added.")
      await load(selectedHandoffId)
    })
  }

  function markPrepared() {
    if (!selectedHandoffId) return
    runAction("prepared", async () => {
      await apiPatch(`${state.base}/handoffs/${selectedHandoffId}/status`, {
        status: "prepared",
        status_reason: "Metadata handoff prepared for human action outside AgencyOS.",
      })
      setMessage("Handoff status recorded.")
      await load(selectedHandoffId)
    })
  }

  function completeInstruction() {
    if (!firstInstruction) return
    runAction("complete", async () => {
      await apiPatch(`${state.base}/instructions/${firstInstruction.id}/completion`, {
        completed: true,
      })
      setMessage("Instruction completion metadata recorded.")
      await load(selectedHandoffId)
    })
  }

  function completeRecipient() {
    if (!firstRecipient) return
    runAction("recipient-status", async () => {
      await apiPatch(`${state.base}/recipients/${firstRecipient.id}/status`, {
        delivery_status: "manually_completed",
        notes: "Human action was recorded manually; AgencyOS did not send anything.",
      })
      setMessage("Recipient status metadata recorded.")
      await load(selectedHandoffId)
    })
  }

  function createSnapshot() {
    if (!selectedHandoffId) return
    runAction("snapshot", async () => {
      await apiPost(`${state.base}/handoffs/${selectedHandoffId}/snapshots`, {
        snapshot_type: selectedHandoff?.status === "held" ? "held" : "prepared",
      })
      setMessage("Immutable handoff snapshot created.")
      await load(selectedHandoffId)
    })
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Decision Export Handoffs</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Manual Delivery Handoff Metadata</h2>
              <p className="mt-1 text-sm text-slate-600">Prepare human-controlled handoff metadata after release readiness without sending, public links, or real PDF delivery.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Manual only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">No public links</span>
            </div>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[410px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createHandoff}>
                <h3 className="font-semibold text-slate-950">Create handoff</h3>
                <Select label="Decision export" value={form.export_id} onChange={(value) => setForm({ ...form, export_id: value })} options={(state?.exports || []).map((item) => [item.id, item.export_name || item.id])} />
                <Select label="Release readiness" value={form.release_readiness_id} onChange={(value) => {
                  const chosen = state?.readiness?.find((item) => item.id === value)
                  setForm({ ...form, release_readiness_id: value, export_id: chosen?.export_id || form.export_id, preview_id: chosen?.preview_id || form.preview_id })
                }} options={(state?.readiness || []).map((item) => [item.id, `${item.readiness_name || item.id} / ${item.readiness_status}`])} />
                <Field label="Title" value={form.title} onChange={(value) => setForm({ ...form, title: value })} />
                <Select label="Manual method" value={form.delivery_method} onChange={(value) => setForm({ ...form, delivery_method: value })} options={[
                  ["manual_email", "Manual email"],
                  ["manual_portal_upload", "Manual portal upload"],
                  ["manual_print", "Manual print"],
                  ["manual_other", "Manual other"],
                ]} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "handoff" || !form.export_id}>{working === "handoff" ? "Creating..." : "Create metadata handoff"}</button>
              </form>

              <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Handoff records</h3>
                <Select label="Handoff" value={selectedHandoffId} onChange={(value) => load(value).catch((err) => setError(err.message))} options={(state?.handoffs || []).map((item) => [item.id, `${item.title || item.id} / ${item.status}`])} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={markPrepared} disabled={!selectedHandoffId || working === "prepared"}>{working === "prepared" ? "Recording..." : "Record prepared status"}</button>
              </div>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addRecipient}>
                <h3 className="font-semibold text-slate-950">Recipient metadata</h3>
                <Field label="Display name" value={form.recipient_name} onChange={(value) => setForm({ ...form, recipient_name: value })} />
                <Field label="Email metadata" value={form.recipient_email} onChange={(value) => setForm({ ...form, recipient_email: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="submit" disabled={!selectedHandoffId || working === "recipient"}>{working === "recipient" ? "Adding..." : "Add recipient metadata"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addAttachment}>
                <h3 className="font-semibold text-slate-950">Attachment metadata</h3>
                <Field label="Filename metadata" value={form.attachment_filename} onChange={(value) => setForm({ ...form, attachment_filename: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="submit" disabled={!selectedHandoffId || working === "attachment"}>{working === "attachment" ? "Adding..." : "Add attachment metadata"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addInstruction}>
                <h3 className="font-semibold text-slate-950">Instructions</h3>
                <Field label="Instruction title" value={form.instruction_title} onChange={(value) => setForm({ ...form, instruction_title: value })} />
                <TextArea label="Instruction body" value={form.instruction_body} onChange={(value) => setForm({ ...form, instruction_body: value })} />
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="submit" disabled={!selectedHandoffId || working === "instruction"}>{working === "instruction" ? "Adding..." : "Add instruction"}</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={completeInstruction} disabled={!firstInstruction || working === "complete"}>Record instruction completion</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={completeRecipient} disabled={!firstRecipient || working === "recipient-status"}>Record recipient completion</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={createSnapshot} disabled={!selectedHandoffId || working === "snapshot"}>{working === "snapshot" ? "Creating..." : "Create immutable snapshot"}</button>
                </div>
              </form>
            </div>

            <div className="space-y-4">
              <HandoffSummary handoff={selectedHandoff} />
              <SimpleList title="Recipients" items={state?.detail?.recipients || []} fields={["recipient_type", "display_name", "delivery_method", "delivery_status"]} />
              <SimpleList title="Attachments" items={state?.detail?.attachments || []} fields={["filename", "file_type", "public_link_created", "real_file_delivered"]} />
              <SimpleList title="Instructions" items={state?.detail?.instructions || []} fields={["instruction_type", "title", "required", "completed"]} />
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

function HandoffSummary({ handoff }) {
  if (!handoff) return <EmptyState title="No handoff selected" body="Create a metadata handoff from an approved export release readiness record." />
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{handoff.title || handoff.id}</h3>
      <div className="mt-3 grid gap-2 text-sm md:grid-cols-4">
        <Summary label="Status" value={handoff.status} />
        <Summary label="Recipients" value={handoff.recipient_count ?? 0} />
        <Summary label="Attachments" value={handoff.attachment_count ?? 0} />
        <Summary label="Snapshots" value={handoff.snapshot_count ?? 0} />
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
