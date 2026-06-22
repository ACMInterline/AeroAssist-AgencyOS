import { useEffect, useState } from "react"
import DocumentStatusBadge from "../../components/DocumentStatusBadge"
import DocumentTypeBadge from "../../components/DocumentTypeBadge"
import PortalSafeHtmlPreview from "../../components/PortalSafeHtmlPreview"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiDownload, apiGet, apiPost } from "../../lib/api"

export default function PortalDocumentDetailPage({ documentId }) {
  const [state, setState] = useState(null)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  async function load() {
    const [me, detail, exportsData] = await Promise.all([
      apiGet("/api/portal/me"),
      apiGet(`/api/portal/documents/${documentId}`),
      apiGet(`/api/portal/documents/${documentId}/exports`),
    ])
    setState({ me, document: detail.document, acknowledgement: detail.acknowledgement, exports: exportsData.items })
  }
  useEffect(() => { load().catch((err) => setError(err.message)) }, [documentId])
  async function acknowledge() {
    setError("")
    try {
      await apiPost(`/api/portal/documents/${documentId}/acknowledge`, { acknowledgement_type: "acknowledged", message: message || undefined })
      setMessage("")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }
  async function downloadExport(exportId) {
    setError("")
    try {
      await apiDownload(`/api/portal/document-exports/${exportId}/download`)
    } catch (err) {
      setError(err.message)
    }
  }
  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3"><div><a className="text-sm font-medium text-blue-700" href="/portal/documents">Back to documents</a><p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Read-only HTML preview</p><h2 className="text-2xl font-semibold text-slate-950">{state.document.title}</h2></div><div className="flex gap-2"><DocumentTypeBadge type={state.document.document_type} /><DocumentStatusBadge status={state.document.status} /></div></div>
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Acknowledgement</h3>
            {state.acknowledgement ? <p className="mt-3 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">Acknowledged on {state.acknowledgement.created_at}</p> : (
              <div className="mt-3 space-y-3">
                <textarea className="min-h-20 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Optional note" value={message} onChange={(event) => setMessage(event.target.value)} />
                <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="button" onClick={acknowledge}>Acknowledge document</button>
              </div>
            )}
            {error ? <p className="mt-3 rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
          </section>
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Available downloads</h3>
            <p className="mt-1 text-sm text-slate-600">Client-visible exports generated from the stored agency document snapshot.</p>
            <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
              {state.exports?.length ? state.exports.map((item) => (
                <div className="flex flex-wrap items-center justify-between gap-3 p-3 text-sm" key={item.id}>
                  <div>
                    <p className="font-medium text-slate-900">{item.filename}</p>
                    <p className="text-slate-500">{item.export_type.replaceAll("_", " ")} · {item.status}{item.file_size_bytes ? ` · ${item.file_size_bytes} bytes` : ""}</p>
                  </div>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-blue-700" type="button" onClick={() => downloadExport(item.id)}>Download</button>
                </div>
              )) : <p className="p-3 text-sm text-slate-500">No downloads are available yet.</p>}
            </div>
          </section>
          <PortalSafeHtmlPreview html={state.document.rendered_html} />
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}
