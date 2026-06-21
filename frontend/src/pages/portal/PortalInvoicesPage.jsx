import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import InvoiceStatusBadge from "../../components/InvoiceStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalInvoicesPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => { Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/invoices")]).then(([me, data]) => setState({ me, items: data.items })).catch((err) => setError(err.message)) }, [])
  return <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}><ProtectedRoute loading={!state && !error} error={error}><div className="space-y-6"><Header title="Invoices" body="Manual invoice summaries. Online payments are not enabled." />{!state.items.length ? <EmptyState title="No invoices visible" body="Invoices will appear after your agency creates them." /> : <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">{state.items.map((item) => <a className="block p-4 text-sm hover:bg-slate-50" href={`/portal/invoices/${item.id}`} key={item.id}><span className="font-semibold text-slate-950">{item.invoice_number}</span><span className="mt-2 flex items-center gap-2 text-slate-600"><InvoiceStatusBadge status={item.status} />Total {item.total_amount} {item.currency} · Due {item.due_amount}</span></a>)}</div>}</div></ProtectedRoute></ClientPortalLayout>
}

function Header({ title, body }) { return <div><p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Client portal</p><h2 className="mt-2 text-2xl font-semibold text-slate-950">{title}</h2><p className="mt-1 text-sm text-slate-600">{body}</p></div> }
