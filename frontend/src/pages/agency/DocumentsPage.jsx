import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const documentTypes = [
  "offer_summary",
  "offer_comparison",
  "trip_confirmation",
  "booking_confirmation",
  "pnr_mirror",
  "ticket_receipt",
  "emd_receipt",
  "service_confirmation",
  "medical_assistance_summary",
  "pet_travel_summary",
  "special_baggage_summary",
  "trip_change_summary",
  "exchange_quote",
  "exchange_confirmation",
  "refund_quote",
  "import_review_summary",
  "internal_case_summary",
]

const sourceTypes = [
  ["request", "Request"],
  ["trip", "Trip"],
  ["offer_workspace", "Offer workspace"],
  ["offer_option", "Offer option"],
  ["booking_workspace", "Booking workspace"],
  ["booking_record", "Booking record"],
  ["ticket_record", "Ticket record"],
  ["emd_record", "EMD record"],
  ["booking_import_draft", "Booking import draft"],
  ["trip_change_operation", "Trip change operation"],
  ["ticket_exchange_operation", "Ticket exchange operation"],
  ["emd_exchange_operation", "EMD exchange operation"],
  ["service_request", "Service request"],
  ["mixed_context", "Mixed context"],
]

const packageTypes = [
  "offer_package",
  "trip_package",
  "booking_package",
  "ticket_emd_package",
  "service_package",
  "change_exchange_package",
  "import_review_package",
  "internal_case_package",
  "custom",
]

function defaultForm() {
  const params = new URLSearchParams(window.location.search)
  return {
    document_type: params.get("document_type") || "trip_confirmation",
    source_context_type: params.get("source_context_type") || "trip",
    source_context_id: params.get("source_context_id") || "",
    template_id: "",
    render_format: "html",
    client_facing: false,
    notes: "",
  }
}

export default function DocumentsPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaultForm)
  const [packageForm, setPackageForm] = useState({ package_type: "trip_package", title: "", source_context_type: "trip", source_context_id: "", document_render_job_ids: [] })
  const [contextPreview, setContextPreview] = useState(null)
  const [selectedJob, setSelectedJob] = useState(null)
  const [error, setError] = useState("")
  const [working, setWorking] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const [templates, jobs, packages, oldDocuments, readiness] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/documents/templates`),
      apiGet(`/api/agencies/${context.agency.id}/documents/render-jobs`),
      apiGet(`/api/agencies/${context.agency.id}/documents/packages`),
      apiGet(`/api/agencies/${context.agency.id}/documents`),
      apiGet("/api/readiness"),
    ])
    setState({
      ...context,
      templates: templates.items || [],
      jobs: jobs.items || [],
      packages: packages.items || [],
      oldDocuments: oldDocuments.items || [],
      readiness: readiness.document_foundation || {},
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const matchingTemplates = useMemo(() => {
    return (state?.templates || []).filter((template) => (template.template_type || template.document_type) === form.document_type)
  }, [form.document_type, state])

  async function previewContext(event) {
    event.preventDefault()
    setWorking("preview")
    setError("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/documents/context-preview`, {
        source_context_type: form.source_context_type,
        source_context_id: form.source_context_id || null,
        source_context_ids_json: {},
      })
      setContextPreview(result.context)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function renderDocument(event) {
    event.preventDefault()
    setWorking("render")
    setError("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/documents/render-jobs`, {
        document_type: form.document_type,
        source_context_type: form.source_context_type,
        source_context_id: form.source_context_id || null,
        source_context_ids_json: {},
        template_id: form.template_id || null,
        render_format: form.render_format,
        render_context_json: {
          client_facing: form.client_facing,
          notes: form.notes,
        },
      })
      setSelectedJob(result.render_job)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function rerender(jobId) {
    setWorking(jobId)
    setError("")
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/documents/render-jobs/${jobId}/rerender`)
      setSelectedJob(result.render_job)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function createPackage(event) {
    event.preventDefault()
    setWorking("package")
    setError("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/documents/packages`, {
        ...packageForm,
        source_context_id: packageForm.source_context_id || null,
        source_context_ids_json: {},
      })
      setPackageForm({ package_type: "trip_package", title: "", source_context_type: "trip", source_context_id: "", document_render_job_ids: [] })
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function createShare(jobId) {
    setWorking(`share-${jobId}`)
    setError("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/documents/share-records`, {
        document_render_job_id: jobId,
        share_status: "ready",
        share_channel: "internal",
        recipient_snapshot_json: { mode: "internal_manual_record" },
      })
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  function togglePackageJob(jobId) {
    setPackageForm((current) => ({
      ...current,
      document_render_job_ids: current.document_render_job_ids.includes(jobId)
        ? current.document_render_job_ids.filter((item) => item !== jobId)
        : [...current.document_render_job_ids, jobId],
    }))
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Documents</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Document Foundation</h2>
              <p className="mt-1 text-sm text-slate-600">Generate internal HTML previews from operational records. Live delivery, e-signature, payment, invoice, and provider execution stay disabled.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/document-templates">Legacy templates</a>
              <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/document-storage">Storage</a>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-4 md:grid-cols-5">
            <Metric label="Render jobs" value={state?.jobs?.length || 0} />
            <Metric label="Packages" value={state?.packages?.length || 0} />
            <Metric label="Templates" value={state?.templates?.length || 0} />
            <Metric label="Share records" value={state?.readiness?.document_share_record_count || 0} />
            <Metric label="Legacy rendered" value={state?.oldDocuments?.length || 0} />
          </section>

          <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_380px]">
            <form className="space-y-4 rounded-lg border border-slate-200 bg-white p-5" onSubmit={renderDocument}>
              <div>
                <h3 className="font-semibold text-slate-950">Generate document</h3>
                <p className="mt-1 text-sm text-slate-600">Choose a document type and source record. Context preview is structured; raw JSON stays in Advanced.</p>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <Select label="Document type" value={form.document_type} options={documentTypes.map((value) => [value, label(value)])} onChange={(value) => setForm((current) => ({ ...current, document_type: value, template_id: "" }))} />
                <Select label="Source context type" value={form.source_context_type} options={sourceTypes} onChange={(value) => setForm((current) => ({ ...current, source_context_type: value }))} />
                <Field label="Source record id" value={form.source_context_id} onChange={(value) => setForm((current) => ({ ...current, source_context_id: value }))} />
                <Select label="Template optional" value={form.template_id} options={[["", "Default template"], ...matchingTemplates.map((template) => [template.id, template.title || template.name || template.template_key])]} onChange={(value) => setForm((current) => ({ ...current, template_id: value }))} />
                <Select label="Render format" value={form.render_format} options={[["html", "HTML"], ["markdown", "Markdown"], ["json", "JSON"], ["pdf", "PDF planned"]]} onChange={(value) => setForm((current) => ({ ...current, render_format: value }))} />
                <label className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700">
                  <input type="checkbox" checked={form.client_facing} onChange={(event) => setForm((current) => ({ ...current, client_facing: event.target.checked }))} />
                  Client-facing language
                </label>
                <TextArea label="Notes" value={form.notes} onChange={(value) => setForm((current) => ({ ...current, notes: value }))} />
              </div>
              <div className="flex flex-wrap gap-2">
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={previewContext} disabled={working === "preview"}>{working === "preview" ? "Previewing..." : "Preview context"}</button>
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "render"}>{working === "render" ? "Rendering..." : "Render document"}</button>
              </div>
              <details className="rounded-md border border-slate-200 bg-slate-50 p-3">
                <summary className="cursor-pointer text-sm font-semibold text-slate-950">Advanced context preview JSON</summary>
                <pre className="mt-3 max-h-72 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(contextPreview || {}, null, 2)}</pre>
              </details>
            </form>

            <form className="space-y-4 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createPackage}>
              <div>
                <h3 className="font-semibold text-slate-950">Document package</h3>
                <p className="mt-1 text-sm text-slate-600">Group rendered jobs into an internal operational package.</p>
              </div>
              <Select label="Package type" value={packageForm.package_type} options={packageTypes.map((value) => [value, label(value)])} onChange={(value) => setPackageForm((current) => ({ ...current, package_type: value }))} />
              <Field label="Title" value={packageForm.title} onChange={(value) => setPackageForm((current) => ({ ...current, title: value }))} />
              <Select label="Source context type" value={packageForm.source_context_type} options={sourceTypes} onChange={(value) => setPackageForm((current) => ({ ...current, source_context_type: value }))} />
              <Field label="Source record id" value={packageForm.source_context_id} onChange={(value) => setPackageForm((current) => ({ ...current, source_context_id: value }))} />
              <div className="max-h-56 space-y-2 overflow-auto rounded-md border border-slate-200 p-3">
                {state?.jobs?.length ? state.jobs.map((job) => (
                  <label className="flex gap-2 text-sm" key={job.id}>
                    <input type="checkbox" checked={packageForm.document_render_job_ids.includes(job.id)} onChange={() => togglePackageJob(job.id)} />
                    <span>{label(job.document_type)} · {job.source_context_id || "mixed"}</span>
                  </label>
                )) : <p className="text-sm text-slate-500">Render jobs appear here.</p>}
              </div>
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "package" || !packageForm.title}>{working === "package" ? "Creating..." : "Create package"}</button>
            </form>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-100 px-5 py-4">
              <h3 className="font-semibold text-slate-950">Render jobs</h3>
            </div>
            {state?.jobs?.length ? (
              <div className="divide-y divide-slate-100">
                {state.jobs.map((job) => (
                  <div className="grid gap-3 p-4 text-sm md:grid-cols-[1.2fr_1fr_120px_110px_220px]" key={job.id}>
                    <span>
                      <span className="block font-semibold text-slate-950">{label(job.document_type)}</span>
                      <span className="text-slate-600">{job.source_context_type} · {job.source_context_id || "mixed"}</span>
                    </span>
                    <span>{job.template_key || job.template_id || "Default template"}</span>
                    <span>{label(job.render_status)}</span>
                    <span>{job.warnings_json?.length || 0} warnings</span>
                    <span className="flex flex-wrap gap-2">
                      <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => setSelectedJob(job)}>Open preview</button>
                      <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => rerender(job.id)} disabled={working === job.id}>{working === job.id ? "Working..." : "Rerender"}</button>
                      <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => createShare(job.id)} disabled={working === `share-${job.id}`}>Share record</button>
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No document render jobs" body="Render a document from a supported operational source." />
            )}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-100 px-5 py-4">
              <h3 className="font-semibold text-slate-950">Document packages</h3>
            </div>
            {state?.packages?.length ? (
              <div className="divide-y divide-slate-100">
                {state.packages.map((item) => (
                  <div className="grid gap-3 p-4 text-sm md:grid-cols-[1.2fr_1fr_120px_120px]" key={item.id}>
                    <span><span className="block font-semibold text-slate-950">{item.title}</span><span className="text-slate-600">{label(item.package_type)}</span></span>
                    <span>{item.source_context_type} · {item.source_context_id || "mixed"}</span>
                    <span>{label(item.status)}</span>
                    <span>{item.document_render_job_ids?.length || 0} documents</span>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No document packages" body="Select render jobs and create a package." />
            )}
          </section>

          {selectedJob ? <RenderJobModal job={selectedJob} onClose={() => setSelectedJob(null)} /> : null}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function RenderJobModal({ job, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">
      <section className="flex max-h-[92vh] w-full max-w-6xl flex-col overflow-hidden rounded-lg bg-white shadow-xl">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 p-5">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Rendered HTML preview</p>
            <h3 className="text-xl font-semibold text-slate-950">{label(job.document_type)}</h3>
            <p className="mt-1 text-sm text-slate-600">{job.source_context_type} · {job.source_context_id || "mixed context"}</p>
          </div>
          <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={onClose}>Close</button>
        </div>
        <div className="grid min-h-0 flex-1 gap-4 overflow-auto p-5 lg:grid-cols-[minmax(0,1fr)_320px]">
          <iframe className="h-[70vh] w-full rounded-md border border-slate-200 bg-white" sandbox="" srcDoc={job.rendered_html || "<p>No preview</p>"} title="Document preview" />
          <aside className="space-y-4">
            <Info title="Status" rows={[["Status", label(job.render_status)], ["Format", label(job.render_format)], ["Warnings", job.warnings_json?.length || 0], ["Created", job.created_at ? new Date(job.created_at).toLocaleString() : "not set"]]} />
            <section className="rounded-md border border-slate-200 p-3">
              <h4 className="text-sm font-semibold text-slate-950">Rendered text</h4>
              <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-xs text-slate-700">{job.rendered_text || "No text fallback"}</pre>
            </section>
            <details className="rounded-md border border-slate-200 bg-slate-50 p-3">
              <summary className="cursor-pointer text-sm font-semibold text-slate-950">Advanced render context JSON</summary>
              <pre className="mt-3 max-h-64 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(job.render_context_json || {}, null, 2)}</pre>
            </details>
          </aside>
        </div>
      </section>
    </div>
  )
}

function Metric({ label: metricLabel, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{metricLabel}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div>
}

function Info({ title, rows }) {
  return (
    <section className="rounded-md border border-slate-200 p-3">
      <h4 className="text-sm font-semibold text-slate-950">{title}</h4>
      <div className="mt-2 space-y-2 text-sm">
        {rows.map(([key, value]) => <div className="flex justify-between gap-3" key={key}><span className="text-slate-500">{key}</span><span className="text-right font-medium text-slate-900">{value}</span></div>)}
      </div>
    </section>
  )
}

function Field({ label: fieldLabel, value, onChange }) {
  return <label className="text-sm font-medium text-slate-700">{fieldLabel}<input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function TextArea({ label: fieldLabel, value, onChange }) {
  return <label className="block text-sm font-medium text-slate-700 md:col-span-2">{fieldLabel}<textarea className="mt-1 min-h-20 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Select({ label: fieldLabel, value, options, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([option, optionLabel]) => <option value={option} key={option}>{optionLabel}</option>)}
      </select>
    </label>
  )
}

function label(value) {
  return String(value || "not set").replaceAll("_", " ")
}
