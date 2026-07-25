import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import PaymentStatusBadge from "../../components/PaymentStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import { useAuthorization } from "../../context/AuthorizationContext"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function PaymentsPage() {
  const authorization = useAuthorization()
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ search: "", status: "" })
  const [paymentForm, setPaymentForm] = useState({ client_id: "", amount: "", currency: "EUR", external_reference: "" })
  const [allocationForm, setAllocationForm] = useState({ payment_id: "", invoice_id: "", amount: "" })
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const [payments, invoices, clients] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/payments`),
      apiGet(`/api/agencies/${context.agency.id}/invoices`),
      apiGet(`/api/agencies/${context.agency.id}/clients`),
    ])
    setState({ ...context, payments: payments.items || [], invoices: invoices.items || [], clients: clients.items || [] })
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

  async function createPayment(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/payments`, {
      client_id: paymentForm.client_id,
      status: "received",
      method: "bank_transfer",
      amount: Number(paymentForm.amount),
      currency: paymentForm.currency.toUpperCase(),
      external_reference: paymentForm.external_reference || null,
      reconciliation_status: "unreconciled",
      internal_notes: "Manual receipt evidence. No payment gateway was executed.",
    })
    setPaymentForm({ client_id: "", amount: "", currency: "EUR", external_reference: "" })
    await load()
  }

  async function allocatePayment(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/payments/${allocationForm.payment_id}/allocations`, {
      invoice_id: allocationForm.invoice_id,
      amount: Number(allocationForm.amount),
      reason: "Manual allocation reviewed by finance operator.",
    })
    setAllocationForm({ payment_id: "", invoice_id: "", amount: "" })
    await load()
  }

  const canEdit = authorization.hasPermission("edit_commercial_ledger")
  const selectedPayment = (state?.payments || []).find((item) => item.id === allocationForm.payment_id)
  const eligibleInvoices = (state?.invoices || []).filter((invoice) =>
    ["issued", "partially_paid"].includes(invoice.status) &&
    invoice.due_amount > 0 &&
    invoice.client_id === selectedPayment?.client_id &&
    invoice.currency === selectedPayment?.currency
  )

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <a className="text-sm font-medium text-blue-700" href="/agency/finance">Finance & reports</a>
            <h2 className="text-2xl font-semibold text-slate-950">Payments</h2>
            <p className="mt-1 text-sm text-slate-600">Record received evidence and allocate it across eligible invoices. No payment gateway is connected or executed.</p>
          </div>
          {canEdit ? <section className="rounded-md border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Record received payment</h3>
            <form className="mt-4 grid gap-3 md:grid-cols-[minmax(180px,1fr)_140px_100px_minmax(180px,1fr)_auto]" onSubmit={createPayment}>
              <select required className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={paymentForm.client_id} onChange={(event) => setPaymentForm({ ...paymentForm, client_id: event.target.value })}>
                <option value="">Select client</option>
                {(state?.clients || []).map((client) => <option key={client.id} value={client.id}>{client.display_name}</option>)}
              </select>
              <input required min="0.01" step="0.01" type="number" className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Amount" value={paymentForm.amount} onChange={(event) => setPaymentForm({ ...paymentForm, amount: event.target.value })} />
              <input required maxLength={3} className="rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" value={paymentForm.currency} onChange={(event) => setPaymentForm({ ...paymentForm, currency: event.target.value })} />
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="External reference optional" value={paymentForm.external_reference} onChange={(event) => setPaymentForm({ ...paymentForm, external_reference: event.target.value })} />
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold">Record</button>
            </form>
          </section> : null}
          {canEdit ? <section className="rounded-md border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Allocate payment</h3>
            <form className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_140px_auto]" onSubmit={allocatePayment}>
              <select required className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={allocationForm.payment_id} onChange={(event) => setAllocationForm({ payment_id: event.target.value, invoice_id: "", amount: "" })}>
                <option value="">Select payment</option>
                {(state?.payments || []).filter((payment) => payment.status === "received" && payment.unallocated_amount > 0).map((payment) => <option key={payment.id} value={payment.id}>{payment.external_reference || payment.id} · {money(payment.unallocated_amount, payment.currency)} available</option>)}
              </select>
              <select required disabled={!selectedPayment} className="rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100" value={allocationForm.invoice_id} onChange={(event) => setAllocationForm({ ...allocationForm, invoice_id: event.target.value })}>
                <option value="">Select matching invoice</option>
                {eligibleInvoices.map((invoice) => <option key={invoice.id} value={invoice.id}>{invoice.invoice_number} · {money(invoice.due_amount, invoice.currency)} due</option>)}
              </select>
              <input required disabled={!allocationForm.invoice_id} min="0.01" step="0.01" max={Math.min(selectedPayment?.unallocated_amount || 0, eligibleInvoices.find((item) => item.id === allocationForm.invoice_id)?.due_amount || 0)} type="number" className="rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100" placeholder="Amount" value={allocationForm.amount} onChange={(event) => setAllocationForm({ ...allocationForm, amount: event.target.value })} />
              <button disabled={!allocationForm.invoice_id} className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-50">Allocate</button>
            </form>
            {selectedPayment && !eligibleInvoices.length ? <p className="mt-3 text-sm text-amber-700">No issued invoice for this client and currency currently has an outstanding balance.</p> : null}
          </section> : null}
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
                      <p className="mt-1 text-sm text-slate-600">{money(payment.amount, payment.currency)} received · {money(payment.allocated_amount, payment.currency)} allocated · {money(payment.unallocated_amount, payment.currency)} available</p>
                      <p className="mt-1 text-xs text-slate-500">{payment.method.replaceAll("_", " ")} · {payment.reconciliation_status.replaceAll("_", " ")}</p>
                    </div>
                    <PaymentStatusBadge status={payment.status} />
                  </div>
                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    {payment.invoice ? <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-blue-700" href={`/agency/invoices/${payment.invoice.id}`}>Open invoice</a> : null}
                    {(payment.allocations || []).map((allocation) => <a className="rounded-md border border-slate-200 px-3 py-2 text-sm text-blue-700" href={`/agency/invoices/${allocation.invoice_id}`} key={allocation.id}>{money(allocation.amount, allocation.currency)} allocated</a>)}
                    {canEdit && payment.status !== "received" ? <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium" onClick={() => markReceived(payment.id)}>Mark received</button> : null}
                    {canEdit && payment.reconciliation_status !== "reconciled" ? <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium" onClick={() => markReconciled(payment.id)}>Mark reconciled</button> : null}
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

function money(value, currency) {
  return `${Number(value || 0).toFixed(2)} ${currency || ""}`.trim()
}
