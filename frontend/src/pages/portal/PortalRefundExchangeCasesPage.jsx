import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import RefundExchangeStatusBadge from "../../components/RefundExchangeStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalRefundExchangeCasesPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/refund-exchange-cases")])
      .then(([me, data]) => setState({ me, items: data.items }))
      .catch((err) => setError(err.message))
  }, [])

  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Client portal</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Refunds / Exchanges</h2>
            <p className="mt-1 text-sm text-slate-600">Read-only tracking for manual refund/exchange follow-up.</p>
          </div>
          {!state.items.length ? <EmptyState title="No cases visible" body="No refund/exchange cases are visible yet." /> : (
            <div className="space-y-4">
              {state.items.map((item) => (
                <a className="block rounded-lg border border-slate-200 bg-white p-4 hover:bg-slate-50" href={`/portal/refunds-exchanges/${item.id}`} key={item.id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{item.case_reference}</p>
                      <p className="mt-1 text-sm text-slate-700">{item.case_type} · {item.reason_category || "Reason not set"} {item.booking ? `· ${item.booking.booking_reference}` : ""}</p>
                      <p className="mt-1 text-sm text-slate-500">Client-visible summary: {item.client_visible_summary || "No summary yet"}</p>
                    </div>
                    <RefundExchangeStatusBadge status={item.status} />
                  </div>
                  <div className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-2">
                    <p>Due from client: {item.estimated_total_due_from_client || 0} {item.currency}</p>
                    <p>Due to client: {item.estimated_total_due_to_client || 0} {item.currency}</p>
                    <p>Final due from client: {item.final_total_due_from_client || 0} {item.currency}</p>
                    <p>Final due to client: {item.final_total_due_to_client || 0} {item.currency}</p>
                  </div>
                </a>
              ))}
            </div>
          )}
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}
