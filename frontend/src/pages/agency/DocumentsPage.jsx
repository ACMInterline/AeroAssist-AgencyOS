import { useEffect, useState } from "react"
import DocumentStatusBadge from "../../components/DocumentStatusBadge"
import DocumentTypeBadge from "../../components/DocumentTypeBadge"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function DocumentsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ document_type: "", source_entity_type: "", status: "" })
  const [error, setError] = useState("")

  async function load(next = filters) {
    const context = await loadCurrentAgency()
    const query = new URLSearchParams()
    Object.entries(next).forEach(([key, value]) => {
      if (value) query.set(key, value)
    })
    const documents = await apiGet(`/api/agencies/${context.agency.id}/documents?${query.toString()}`)
    setState({ ...context, documents: documents.items })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function updateFilter(name, value) {
    const next = { ...filters, [name]: value }
    setFilters(next)
    await load(next)
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Documents</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Rendered HTML Documents</h2>
              <p className="mt-1 text-sm text-slate-600">Agency-generated previews from captured snapshots. No PDF, email, or portal publishing.</p>
            </div>
            <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/document-templates">Templates</a>
          </div>
          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-5 md:grid-cols-3">
            <Select label="Document type" value={filters.document_type} onChange={(value) => updateFilter("document_type", value)} options={["", "offer_summary", "booking_confirmation", "itinerary_summary", "ticket_receipt_summary", "emd_receipt_summary", "invoice_summary", "service_summary"]} />
            <Select label="Source" value={filters.source_entity_type} onChange={(value) => updateFilter("source_entity_type", value)} options={["", "offer", "booking", "ticket", "emd", "invoice", "request"]} />
            <Select label="Status" value={filters.status} onChange={(value) => updateFilter("status", value)} options={["", "rendered", "draft", "superseded", "archived"]} />
          </section>
          {!state.documents.length ? <EmptyState title="No rendered documents" body="Render document previews from offer, booking, ticket, EMD, or invoice detail pages." /> : (
            <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
              {state.documents.map((document) => (
                <a className="grid gap-3 p-4 text-sm hover:bg-slate-50 md:grid-cols-[1fr_170px_120px_150px]" href={`/agency/documents/${document.id}`} key={document.id}>
                  <span>
                    <span className="block font-semibold text-slate-950">{document.title}</span>
                    <span className="text-slate-600">{document.client?.display_name || "No client"} · {document.source_entity_type} · {document.source_entity_id.slice(0, 8)}</span>
                  </span>
                  <DocumentTypeBadge type={document.document_type} />
                  <DocumentStatusBadge status={document.status} />
                  <span className="text-slate-600">{document.rendered_at ? new Date(document.rendered_at).toLocaleString() : "Not rendered"}</span>
                </a>
              ))}
            </div>
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Select({ label, value, onChange, options }) {
  return (
    <label className="text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => <option value={option} key={option}>{option ? option.replaceAll("_", " ") : "Any"}</option>)}
      </select>
    </label>
  )
}
