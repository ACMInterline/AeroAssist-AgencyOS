import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import RequestStatusBadge from "../../components/RequestStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalRequestsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => { Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/requests")]).then(([me, data]) => setState({ me, items: data.items })).catch((err) => setError(err.message)) }, [])
  return <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}><ProtectedRoute loading={!state && !error} error={error}><ListPage title="Requests" body="Read-only request status and client-visible notes." items={state?.items || []} href="/portal/requests" render={(item) => <><span className="font-semibold text-slate-950">{item.request_reference} · {item.title}</span><span className="flex items-center gap-2 text-slate-600"><RequestStatusBadge status={item.status} />{item.route_summary || "Route not set"}</span></>} /></ProtectedRoute></ClientPortalLayout>
}

function ListPage({ title, body, items, href, render }) {
  return <div className="space-y-6"><div><p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Client portal</p><h2 className="mt-2 text-2xl font-semibold text-slate-950">{title}</h2><p className="mt-1 text-sm text-slate-600">{body}</p></div>{!items.length ? <EmptyState title={`No ${title.toLowerCase()} visible`} body="Your agency controls which records are visible here." /> : <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">{items.map((item) => <a className="block p-4 text-sm hover:bg-slate-50" href={`${href}/${item.id}`} key={item.id}>{render(item)}</a>)}</div>}</div>
}
