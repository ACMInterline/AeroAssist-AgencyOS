import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaults = {
  export_id: "",
  render_profile: "internal_review",
  template_profile: "metadata_preview",
  reviewed_by: "",
}

export default function OfferDecisionExportPreviewsPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaults)
  const [selectedPreviewId, setSelectedPreviewId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [working, setWorking] = useState("")

  async function load(nextPreviewId = selectedPreviewId) {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/offer-decision-export-previews`
    const exportBase = `/api/agencies/${context.agency.id}/offer-decision-exports`
    const [summary, previewsResult, exportsResult, validations, snapshots] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/previews`),
      apiGet(`${exportBase}/exports`),
      apiGet(`${base}/validations`),
      apiGet(`${base}/snapshots`),
    ])
    const previews = previewsResult.items || []
    const chosenPreviewId = nextPreviewId || previews[0]?.id || ""
    const detail = chosenPreviewId ? await apiGet(`${base}/previews/${chosenPreviewId}`) : null
    setSelectedPreviewId(chosenPreviewId)
    setState({
      ...context,
      base,
      summary,
      previews,
      exports: exportsResult.items || [],
      validations: validations.items || [],
      snapshots: snapshots.items || [],
      detail,
    })
    if (!form.export_id && exportsResult.items?.[0]?.id) {
      setForm((current) => ({ ...current, export_id: exportsResult.items[0].id }))
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedPreview = state?.detail?.preview || state?.previews?.find((item) => item.id === selectedPreviewId)
  const metrics = useMemo(() => [
    ["Previews", state?.summary?.preview_count],
    ["Sections", state?.summary?.section_count],
    ["Blocks", state?.summary?.block_count],
    ["Validations", state?.summary?.validation_count],
    ["Snapshots", state?.summary?.snapshot_count],
  ], [state])

  async function generatePreview(event) {
    event.preventDefault()
    setWorking("generate")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`${state.base}/generate`, {
        export_id: form.export_id,
        render_profile: form.render_profile,
        template_profile: form.template_profile,
        reviewed_by: form.reviewed_by || null,
      })
      setMessage("Render preview metadata generated.")
      await load(result.preview.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function validatePreview() {
    if (!selectedPreviewId) return
    setWorking("validate")
    setError("")
    setMessage("")
    try {
      await apiPost(`${state.base}/previews/${selectedPreviewId}/validate`, {
        internal_reviewer: form.reviewed_by || selectedPreview?.reviewed_by || "agency-reviewer",
      })
      setMessage("Preview metadata validation recorded.")
      await load(selectedPreviewId)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function saveSnapshot() {
    if (!selectedPreviewId) return
    setWorking("snapshot")
    setError("")
    setMessage("")
    try {
      await apiPost(`${state.base}/previews/${selectedPreviewId}/snapshots`, {
        snapshot_name: `Preview snapshot ${new Date().toLocaleString()}`,
      })
      setMessage("Immutable preview snapshot saved.")
      await load(selectedPreviewId)
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
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Offer Decision Export Previews</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Render Preview Metadata</h2>
              <p className="mt-1 text-sm text-slate-600">Review structured render previews before any real document delivery exists.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">PDF delivery disabled</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">No public links</span>
            </div>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[390px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={generatePreview}>
                <h3 className="font-semibold text-slate-950">Generate preview</h3>
                <Select label="Offer decision export" value={form.export_id} onChange={(value) => setForm({ ...form, export_id: value })} options={(state?.exports || []).map((item) => [item.id, item.export_name || item.id])} />
                <Field label="Render profile" value={form.render_profile} onChange={(value) => setForm({ ...form, render_profile: value })} />
                <Field label="Template profile" value={form.template_profile} onChange={(value) => setForm({ ...form, template_profile: value })} />
                <Field label="Internal reviewer" value={form.reviewed_by} onChange={(value) => setForm({ ...form, reviewed_by: value })} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "generate" || !form.export_id}>{working === "generate" ? "Generating..." : "Generate preview metadata"}</button>
              </form>

              <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Preview records</h3>
                <Select label="Preview" value={selectedPreviewId} onChange={(value) => load(value).catch((err) => setError(err.message))} options={(state?.previews || []).map((item) => [item.id, `${item.render_profile} / ${item.preview_status}`])} />
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={validatePreview} disabled={!selectedPreviewId || working === "validate"}>{working === "validate" ? "Validating..." : "Validate metadata"}</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-60" type="button" onClick={saveSnapshot} disabled={!selectedPreviewId || working === "snapshot"}>{working === "snapshot" ? "Saving..." : "Save snapshot"}</button>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <PreviewSummary preview={selectedPreview} />
              <SimpleList title="Sections" items={state?.detail?.sections || []} fields={["section_order", "section_key", "section_title", "block_count"]} />
              <SimpleList title="Blocks" items={state?.detail?.blocks || []} fields={["section_key", "block_type", "block_title", "source_record_type"]} />
              <SimpleList title="Validations" items={state?.detail?.validations || []} fields={["validation_key", "validation_status", "severity", "message"]} />
              <SimpleList title="Snapshots" items={state?.detail?.snapshots || []} fields={["snapshot_name", "immutable", "saved_by", "saved_at"]} />
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

function PreviewSummary({ preview }) {
  if (!preview) return <EmptyState title="No preview selected" body="Generate a render preview from an offer decision export." />
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{preview.render_profile || preview.id}</h3>
      <div className="mt-3 grid gap-2 text-sm md:grid-cols-4">
        <Summary label="Status" value={preview.preview_status} />
        <Summary label="Sections" value={preview.section_count ?? 0} />
        <Summary label="Blocks" value={preview.block_count ?? 0} />
        <Summary label="PDF delivery" value={preview.real_pdf_delivery_disabled ? "disabled" : "enabled"} />
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
