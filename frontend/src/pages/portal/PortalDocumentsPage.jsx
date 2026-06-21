import { useEffect, useState } from "react"
import DocumentStatusBadge from "../../components/DocumentStatusBadge"
import DocumentTypeBadge from "../../components/DocumentTypeBadge"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalDocumentsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => { Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/documents")]).then(([me, data]) => setState({ me, items: data.items })).catch((err) => setError(err.message)) }, [])
  return <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}><ProtectedRoute loading={!state && !error} error={error}><div className="space-y-6"><Header title="Documents" body="HTML previews only. No PDF download, email, or share links." />{!state.items.length ? <EmptyState title="No documents visible" body="Client-visible rendered documents will appear here." /> : <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">{state.items.map((item) => <a className="grid gap-2 p-4 text-sm hover:bg-slate-50 md:grid-cols-[1fr_180px_120px]" href={`/portal/documents/${item.id}`} key={item.id}><span className="font-semibold text-slate-950">{item.title}</span><DocumentTypeBadge type={item.document_type} /><DocumentStatusBadge status={item.status} /></a>)}</div>}</div></ProtectedRoute></ClientPortalLayout>
}

function Header({ title, body }) { return <div><p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Client portal</p><h2 className="mt-2 text-2xl font-semibold text-slate-950">{title}</h2><p className="mt-1 text-sm text-slate-600">{body}</p></div> }
