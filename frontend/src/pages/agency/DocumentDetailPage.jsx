import { useEffect, useState } from "react"
import DocumentPreviewFrame from "../../components/DocumentPreviewFrame"
import DocumentStatusBadge from "../../components/DocumentStatusBadge"
import DocumentTypeBadge from "../../components/DocumentTypeBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function DocumentDetailPage({ documentId }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const detail = await apiGet(`/api/agencies/${context.agency.id}/documents/${documentId}`)
    setState({ ...context, ...detail })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [documentId])

  async function archive() {
    await apiPost(`/api/agencies/${state.agency.id}/documents/${documentId}/archive`)
    await load()
  }

  const document = state?.document
  const sourceHref = document ? sourceLink(document) : "#"

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <a className="text-sm font-medium text-blue-700" href="/agency/documents">Back to documents</a>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">HTML document · Preview only</p>
              <h2 className="text-2xl font-semibold text-slate-950">{document.title}</h2>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <DocumentTypeBadge type={document.document_type} />
              <DocumentStatusBadge status={document.status} />
              <button className="rounded-md border border-rose-200 px-3 py-2 text-sm font-semibold text-rose-700" onClick={archive}>Archive</button>
            </div>
          </div>
          <section className="grid gap-4 lg:grid-cols-3">
            <Info title="Metadata" rows={[["Source", document.source_entity_type], ["Rendered", document.rendered_at ? new Date(document.rendered_at).toLocaleString() : "Not set"], ["Language", document.language], ["Client visible", document.client_visible ? "Yes" : "No"]]} />
            <Info title="Brand Snapshot" rows={[["Brand", document.brand_snapshot.brand_name], ["Primary", document.brand_snapshot.primary_color], ["Secondary", document.brand_snapshot.secondary_color], ["Font", document.brand_snapshot.font_family]]} />
            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Source</h3>
              <a className="mt-4 inline-flex rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-blue-700" href={sourceHref}>Open source record</a>
              <p className="mt-3 text-sm text-slate-600">Snapshot captured at render time. Main UI does not expose raw JSON.</p>
            </section>
          </section>
          <DocumentPreviewFrame html={document.rendered_html} />
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Timeline</h3>
            <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
              {state.timeline.map((item) => <div className="p-3 text-sm text-slate-700" key={item.id}>{item.title}{item.summary ? ` · ${item.summary}` : ""}</div>)}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function sourceLink(document) {
  if (document.source_entity_type === "offer") return `/agency/offers/${document.source_entity_id}`
  if (document.source_entity_type === "booking") return `/agency/bookings/${document.source_entity_id}`
  if (document.source_entity_type === "invoice") return `/agency/invoices/${document.source_entity_id}`
  return "/agency/bookings"
}

function Info({ title, rows }) {
  return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><dl className="mt-4 space-y-3 text-sm">{rows.map(([label, value]) => <div key={label}><dt className="font-medium text-slate-700">{label}</dt><dd className="mt-1 break-words text-slate-600">{value || "Not set"}</dd></div>)}</dl></section>
}
