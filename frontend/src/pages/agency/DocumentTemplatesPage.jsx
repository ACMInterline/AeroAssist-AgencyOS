import { useEffect, useState } from "react"
import DocumentStatusBadge from "../../components/DocumentStatusBadge"
import DocumentTypeBadge from "../../components/DocumentTypeBadge"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function DocumentTemplatesPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ document_type: "offer_summary", name: "", description: "", language: "en" })
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const templates = await apiGet(`/api/agencies/${context.agency.id}/document-templates`)
    setState({ ...context, templates: templates.items })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function createTemplate(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/document-templates`, {
      ...form,
      template_scope: "agency_custom",
      status: "active",
      version: 1,
      template_config: { layout: "clean_printable_html", show_preview_label: true },
    })
    setForm({ document_type: "offer_summary", name: "", description: "", language: "en" })
    await load()
  }

  async function archiveTemplate(id) {
    await apiPost(`/api/agencies/${state.agency.id}/document-templates/${id}/archive`)
    await load()
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <a className="text-sm font-medium text-blue-700" href="/agency/documents">Back to documents</a>
            <p className="mt-2 text-sm font-semibold uppercase tracking-wide text-blue-700">Document Templates</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Template Metadata</h2>
            <p className="mt-1 text-sm text-slate-600">Basic metadata/config only. No drag-and-drop builder or advanced editor.</p>
          </div>
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Create Agency Template</h3>
            <form className="mt-4 grid gap-3 md:grid-cols-[190px_1fr_1fr_100px_auto]" onSubmit={createTemplate}>
              <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.document_type} onChange={(event) => setForm((current) => ({ ...current, document_type: event.target.value }))}>
                {["offer_summary", "booking_confirmation", "itinerary_summary", "ticket_receipt_summary", "emd_receipt_summary", "invoice_summary", "service_summary"].map((type) => <option key={type}>{type}</option>)}
              </select>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Template name" value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} />
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Description" value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} />
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.language} onChange={(event) => setForm((current) => ({ ...current, language: event.target.value }))} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Create</button>
            </form>
          </section>
          {!state.templates.length ? <EmptyState title="No templates" body="Platform defaults and agency templates appear here." /> : (
            <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
              {state.templates.map((template) => (
                <div className="grid gap-3 p-4 text-sm md:grid-cols-[1fr_170px_130px_100px_auto]" key={template.id}>
                  <span><span className="block font-semibold text-slate-950">{template.name}</span><span className="text-slate-600">{template.description || "No description"} · {template.template_scope.replaceAll("_", " ")}</span></span>
                  <DocumentTypeBadge type={template.document_type} />
                  <DocumentStatusBadge status={template.status} />
                  <span className="text-slate-600">v{template.version}</span>
                  {template.agency_id ? <button className="text-rose-700" onClick={() => archiveTemplate(template.id)}>Archive</button> : <span className="text-slate-500">Platform default</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
