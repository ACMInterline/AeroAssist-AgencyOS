import { useEffect, useState } from "react"
import DocumentStatusBadge from "../../components/DocumentStatusBadge"
import DocumentTypeBadge from "../../components/DocumentTypeBadge"
import PortalSafeHtmlPreview from "../../components/PortalSafeHtmlPreview"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalDocumentDetailPage({ documentId }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => { Promise.all([apiGet("/api/portal/me"), apiGet(`/api/portal/documents/${documentId}`)]).then(([me, detail]) => setState({ me, document: detail.document })).catch((err) => setError(err.message)) }, [documentId])
  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3"><div><a className="text-sm font-medium text-blue-700" href="/portal/documents">Back to documents</a><p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Read-only HTML preview</p><h2 className="text-2xl font-semibold text-slate-950">{state.document.title}</h2></div><div className="flex gap-2"><DocumentTypeBadge type={state.document.document_type} /><DocumentStatusBadge status={state.document.status} /></div></div>
          <PortalSafeHtmlPreview html={state.document.rendered_html} />
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}
