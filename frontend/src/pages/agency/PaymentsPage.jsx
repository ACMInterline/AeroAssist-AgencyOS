import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import PaymentStatusBadge from "../../components/PaymentStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function PaymentsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ search: "", status: "" })
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const payments = await apiGet(`/api/agencies/${context.agency.id}/payments`)
    setState({ ...context, payments: payments.items })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const filtered = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.payments || []).filter((payment) => {
      const matchesSearch = !search || [payment.external_reference, payment.invoice?.invoice_number, payment.client?.display_name].some((value) => String(value || "").toLowerCase().includes(search))
      return matchesSearch && (!filters.status || payment.status === filters.status)
    })
  }, [filters, state])

  async function markReceived(paymentId) {
    await apiPost(`/api/agencies/${state.agency.id}/payments/${paymentId}/mark-received`)
    await load()
  }

  async function markReconciled(paymentId) {
    await apiPost(`/api/agencies/${state.agency.id}/payments/${paymentId}/mark-reconciled`)
    await load()
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Payment Tracking</p>
            <h2 className="text-2xl font-semibold text-slate-950">Payments</h2>
            <p className="mt-1 text-sm text-slate-600">Manual payment records only. No payment gateway connected.</p>
          </div>
          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-2">
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search payments" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">All statuses</option>
              {["pending", "received", "failed", "refunded", "partially_refunded", "cancelled"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
            </select>
          </section>
          {filtered.length ? (
            <div className="grid gap-4">
              {filtered.map((payment) => (
                <section className="rounded-lg border border-slate-200 bg-white p-5" key={payment.id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{payment.invoice?.invoice_number || "Invoice"}</p>
                      <h3 className="mt-1 font-semibold text-slate-950">{payment.client?.display_name || "Client"}</h3>
                      <p className="mt-1 text-sm text-slate-600">{payment.amount} {payment.currency} · {payment.method.replaceAll("_", " ")} · {payment.reconciliation_status.replaceAll("_", " ")}</p>
                    </div>
                    <PaymentStatusBadge status={payment.status} />
                  </div>
                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    {payment.invoice ? <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-blue-700" href={`/agency/invoices/${payment.invoice.id}`}>Open invoice</a> : null}
                    <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium" onClick={() => markReceived(payment.id)}>Mark received</button>
                    <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium" onClick={() => markReconciled(payment.id)}>Mark reconciled</button>
                  </div>
                </section>
              ))}
            </div>
          ) : (
            <EmptyState title="No payments found" body="Payments are created from invoice or booking detail." />
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
