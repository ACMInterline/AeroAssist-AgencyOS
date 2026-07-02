import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaults = {
  decision_pack_id: "",
  export_name: "Offer decision review export",
  include_recipient_draft: false,
  recipient_name: "",
  recipient_email: "",
  subject: "",
  message_body: "Draft only. No automatic sending or public link was created.",
}

export default function OfferDecisionExportsPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaults)
  const [selectedExportId, setSelectedExportId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [working, setWorking] = useState(false)

  async function load(nextExportId = selectedExportId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/offer-decision-exports`
    const packsBase = `/api/agencies/${context.agency.id}/offer-decision-packs`
    const [summary, exportsResult, packs, artifacts, recipientDrafts, auditEvents] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/exports`),
      apiGet(`${packsBase}/packs`),
      apiGet(`${base}/artifacts`),
      apiGet(`${base}/recipient-drafts`),
      apiGet(`${base}/audit-events`),
    ])
    const exports = exportsResult.items || []
    const chosenExportId = nextExportId || exports[0]?.id || ""
    const detail = chosenExportId ? await apiGet(`${base}/exports/${chosenExportId}`) : null
    setSelectedExportId(chosenExportId)
    setState({
      ...context,
      base,
      summary,
      exports,
      packs: packs.items || [],
      artifacts: artifacts.items || [],
      recipientDrafts: recipientDrafts.items || [],
      auditEvents: auditEvents.items || [],
      detail,
    })
    if (!form.decision_pack_id && packs.items?.[0]?.id) {
      setForm((current) => ({ ...current, decision_pack_id: packs.items[0].id }))
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedExport = state?.detail?.export || state?.exports?.find((item) => item.id === selectedExportId)
  const metrics = useMemo(() => [
    ["Exports", state?.summary?.export_count],
    ["Sections", state?.summary?.section_count],
    ["Artifacts", state?.summary?.artifact_count],
    ["Recipient drafts", state?.summary?.recipient_draft_count],
    ["Audit events", state?.summary?.audit_event_count],
  ], [state])

  async function generateExport(event) {
    event.preventDefault()
    setWorking(true)
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`${state.base}/generate`, {
        decision_pack_id: form.decision_pack_id,
        export_name: form.export_name || null,
        include_recipient_draft: form.include_recipient_draft,
        recipient_name: form.recipient_name || null,
        recipient_email: form.recipient_email || null,
        subject: form.subject || null,
        message_body: form.message_body || null,
      })
      setMessage("Offer decision review export metadata generated.")
      await load(result.export.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking(false)
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Decision Exports</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Review Export Metadata</h2>
              <p className="mt-1 text-sm text-slate-600">Generate internal review export snapshots for decision packs, evidence, explanations, and timeline audit records.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">No public links</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">No automatic sending</span>
            </div>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[390px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={generateExport}>
                <h3 className="font-semibold text-slate-950">Generate export</h3>
                <Select label="Decision pack" value={form.decision_pack_id} onChange={(value) => setForm({ ...form, decision_pack_id: value })} options={(state?.packs || []).map((item) => [item.id, item.pack_name || item.id])} />
                <Field label="Export name" value={form.export_name} onChange={(value) => setForm({ ...form, export_name: value })} />
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input type="checkbox" checked={form.include_recipient_draft} onChange={(event) => setForm({ ...form, include_recipient_draft: event.target.checked })} />
                  Create unsent recipient draft
                </label>
                {form.include_recipient_draft ? (
                  <>
                    <Field label="Recipient name" value={form.recipient_name} onChange={(value) => setForm({ ...form, recipient_name: value })} />
                    <Field label="Recipient email" value={form.recipient_email} onChange={(value) => setForm({ ...form, recipient_email: value })} />
                    <Field label="Subject" value={form.subject} onChange={(value) => setForm({ ...form, subject: value })} />
                    <TextArea label="Draft message" value={form.message_body} onChange={(value) => setForm({ ...form, message_body: value })} />
                  </>
                ) : null}
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working || !form.decision_pack_id}>{working ? "Generating..." : "Generate export metadata"}</button>
              </form>

              <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Export records</h3>
                <Select label="Export" value={selectedExportId} onChange={(value) => load(value).catch((err) => setError(err.message))} options={(state?.exports || []).map((item) => [item.id, item.export_name || item.id])} />
              </div>
            </div>

            <div className="space-y-4">
              <ExportSummary exportRecord={selectedExport} />
              <SimpleList title="Sections" items={state?.detail?.sections || []} fields={["section_order", "section_key", "section_title", "record_count"]} />
              <SimpleList title="Artifacts" items={state?.detail?.artifacts || []} fields={["artifact_type", "filename", "file_generated", "public_link_created"]} />
              <SimpleList title="Recipient drafts" items={state?.detail?.recipient_drafts || []} fields={["recipient_type", "recipient_email", "delivery_status", "sent_at"]} />
              <SimpleList title="Audit events" items={state?.detail?.audit_events || []} fields={["event_type", "actor_type", "description", "created_at"]} />
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

function ExportSummary({ exportRecord }) {
  if (!exportRecord) return <EmptyState title="No export selected" body="Generate an offer decision export to review metadata artifacts." />
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{exportRecord.export_name || exportRecord.id}</h3>
      <div className="mt-3 grid gap-2 text-sm md:grid-cols-4">
        <Summary label="Status" value={exportRecord.export_status} />
        <Summary label="Sections" value={exportRecord.section_count ?? 0} />
        <Summary label="Artifacts" value={exportRecord.artifact_count ?? 0} />
        <Summary label="Public links" value={exportRecord.public_links_disabled ? "disabled" : "enabled"} />
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
