import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import PaymentStatusBadge from "../../components/PaymentStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalPaymentsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => { Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/payments")]).then(([me, data]) => setState({ me, items: data.items })).catch((err) => setError(err.message)) }, [])
  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div><p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Client portal</p><h2 className="mt-2 text-2xl font-semibold text-slate-950">Payments</h2><p className="mt-1 text-sm text-slate-600">Payment summaries only. Online payment is not enabled.</p></div>
          {!state.items.length ? <EmptyState title="No payments visible" body="Manually recorded payment summaries will appear here." /> : <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">{state.items.map((item) => <div className="flex flex-wrap items-center justify-between gap-3 p-4 text-sm" key={item.id}><span>{item.amount} {item.currency} · {item.method?.replaceAll("_", " ")} · invoice {item.invoice_id?.slice(0, 8)}</span><PaymentStatusBadge status={item.status} /></div>)}</div>}
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}
