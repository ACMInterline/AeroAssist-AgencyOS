import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import InvoiceStatusBadge from "../../components/InvoiceStatusBadge"
import PaymentStatusBadge from "../../components/PaymentStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function InvoiceDetailPage({ invoiceId }) {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ description: "", line_type: "other", amount: 0, payment_amount: 0 })
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const detail = await apiGet(`/api/agencies/${context.agency.id}/invoices/${invoiceId}`)
    setState({ ...context, ...detail })
    setForm((current) => ({ ...current, payment_amount: detail.invoice.due_amount || 0 }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [invoiceId])

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function issue() {
    await apiPost(`/api/agencies/${state.agency.id}/invoices/${invoiceId}/issue`)
    await load()
  }

  async function voidInvoice() {
    await apiPost(`/api/agencies/${state.agency.id}/invoices/${invoiceId}/void`)
    await load()
  }

  async function addLine(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/invoices/${invoiceId}/line-items`, {
      booking_id: state.invoice.booking_id,
      line_type: form.line_type,
      description: form.description,
      quantity: 1,
      unit_amount: Number(form.amount),
      currency: state.invoice.currency,
      supplier_pass_through: ["airfare", "taxes", "airline_ancillary", "emd_fee"].includes(form.line_type),
      client_visible: true,
    })
    setForm((current) => ({ ...current, description: "", amount: 0 }))
    await load()
  }

  async function archiveLine(lineId) {
    await apiPost(`/api/agencies/${state.agency.id}/invoices/${invoiceId}/line-items/${lineId}/archive`)
    await load()
  }

  async function addPayment(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/payments`, {
      invoice_id: invoiceId,
      booking_id: state.invoice.booking_id,
      client_id: state.invoice.client_id,
      status: "received",
      method: "bank_transfer",
      amount: Number(form.payment_amount),
      currency: state.invoice.currency,
      reconciliation_status: "unreconciled",
      internal_notes: "Payment received manually. No payment gateway connected.",
    })
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
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <a className="text-sm font-medium text-blue-700" href="/agency/invoices">Back to invoices</a>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state.invoice.invoice_number}</p>
              <h2 className="text-2xl font-semibold text-slate-950">{state.client.display_name}</h2>
              <p className="mt-1 text-sm text-slate-600">No payment gateway connected. Payments are recorded manually.</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <InvoiceStatusBadge status={state.invoice.status} />
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium" onClick={issue}>Issue</button>
              <button className="rounded-md border border-rose-200 px-3 py-2 text-sm font-medium text-rose-700" onClick={voidInvoice}>Void</button>
            </div>
          </div>
          <section className="grid gap-4 md:grid-cols-4">
            <Metric label="Subtotal" value={`${state.invoice.subtotal_amount} ${state.invoice.currency}`} />
            <Metric label="Tax lines" value={`${state.invoice.tax_amount} ${state.invoice.currency}`} />
            <Metric label="Paid" value={`${state.invoice.paid_amount} ${state.invoice.currency}`} />
            <Metric label="Due" value={`${state.invoice.due_amount} ${state.invoice.currency}`} />
          </section>
          {state.booking ? <a className="inline-flex rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-blue-700" href={`/agency/bookings/${state.booking.id}`}>Open booking {state.booking.booking_reference}</a> : null}
          <Panel title="Line Items">
            <form className="grid gap-3 md:grid-cols-[180px_1fr_120px_auto]" onSubmit={addLine}>
              <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.line_type} onChange={(event) => setField("line_type", event.target.value)}>
                {["airfare", "taxes", "airline_ancillary", "agency_service_fee", "document_service_fee", "special_assistance_fee", "ticket_fee", "emd_fee", "discount", "markup", "other"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
              </select>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Description" value={form.description} onChange={(event) => setField("description", event.target.value)} />
              <input type="number" className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.amount} onChange={(event) => setField("amount", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Add line</button>
            </form>
            <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
              {state.line_items.map((item) => (
                <div className="flex flex-wrap items-center justify-between gap-3 p-3 text-sm" key={item.id}>
                  <span>{item.description} · {item.line_type.replaceAll("_", " ")} · {item.total_amount} {item.currency}</span>
                  {item.status === "active" ? <button className="text-rose-700" onClick={() => archiveLine(item.id)}>Archive</button> : <span className="text-slate-500">{item.status}</span>}
                </div>
              ))}
            </div>
          </Panel>
          <Panel title="Payments">
            <form className="grid gap-3 md:grid-cols-[1fr_auto]" onSubmit={addPayment}>
              <input type="number" className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.payment_amount} onChange={(event) => setField("payment_amount", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Record received payment</button>
            </form>
            {state.payments.length ? (
              <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                {state.payments.map((payment) => (
                  <div className="flex flex-wrap items-center justify-between gap-3 p-3 text-sm" key={payment.id}>
                    <span>{payment.amount} {payment.currency} · {payment.method.replaceAll("_", " ")} · {payment.reconciliation_status.replaceAll("_", " ")}</span>
                    <span className="flex items-center gap-2"><PaymentStatusBadge status={payment.status} /><button className="text-blue-700" onClick={() => markReconciled(payment.id)}>Mark reconciled</button></span>
                  </div>
                ))}
              </div>
            ) : <EmptyState title="No payments recorded" body="Record manual payments received outside AgencyOS." />}
          </Panel>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Panel({ title, children }) {
  return <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section>
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-lg font-semibold text-slate-950">{value}</p></div>
}
