import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import InvoiceStatusBadge from "../../components/InvoiceStatusBadge"
import OperationalCollaborationPanel from "../../components/OperationalCollaborationPanel"
import PaymentStatusBadge from "../../components/PaymentStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import WorkflowContinuityPanel from "../../components/WorkflowContinuityPanel"
import { useAuthorization } from "../../context/AuthorizationContext"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function InvoiceDetailPage({ invoiceId }) {
  const authorization = useAuthorization()
  const [state, setState] = useState(null)
  const [form, setForm] = useState({
    description: "",
    line_type: "service",
    amount: 0,
    payment_amount: 0,
    cancellation_reason: "",
    credit_amount: 0,
    credit_reason: "",
  })
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

  async function cancelInvoice() {
    await apiPost(`/api/agencies/${state.agency.id}/invoices/${invoiceId}/cancel`, {
      reason: form.cancellation_reason,
    })
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
      supplier_pass_through: ["ticket", "emd", "supplier_fee"].includes(form.line_type),
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

  async function createCredit(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/finance/credit-notes`, {
      invoice_id: invoiceId,
      reason: form.credit_reason,
      amount: Number(form.credit_amount),
      description: form.credit_reason,
    })
    setForm((current) => ({ ...current, credit_amount: 0, credit_reason: "" }))
    await load()
  }

  async function issueCredit(creditNoteId) {
    await apiPost(`/api/agencies/${state.agency.id}/finance/credit-notes/${creditNoteId}/issue`)
    await load()
  }

  async function renderInvoiceSummary() {
    const result = await apiPost(`/api/agencies/${state.agency.id}/invoices/${invoiceId}/render-document`, { document_type: "invoice_summary" })
    window.location.href = `/agency/documents/${result.document.id}`
  }

  const invoice = state?.invoice || {}
  const lineItems = state?.line_items || []
  const payments = state?.payments || []
  const allocations = state?.payment_allocations || []
  const creditNotes = state?.credit_notes || []
  const canEdit = authorization.hasPermission("edit_commercial_ledger")
  const invoiceReady = Boolean(lineItems.length)
  const bookingWorkspaceId = state?.invoice?.booking_workspace_id || state?.booking_workspace?.id

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <a className="text-sm font-medium text-blue-700" href="/agency/invoices">Back to invoices</a>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{invoice.invoice_number}</p>
              <h2 className="text-2xl font-semibold text-slate-950">{state?.client?.display_name}</h2>
              <p className="mt-1 text-sm text-slate-600">Commercial evidence only. AeroAssist does not execute payments or alter booking, ticket, or EMD records.</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <InvoiceStatusBadge status={invoice.status} />
              <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium" href={`/agency/after-sales?invoice_id=${encodeURIComponent(invoiceId)}`}>Open after-sales case</a>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium" onClick={renderInvoiceSummary}>Render invoice summary</button>
              {canEdit && invoice.status === "draft" ? <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium" onClick={issue}>Issue</button> : null}
            </div>
          </div>
          <WorkflowContinuityPanel
            breadcrumbs={[{ label: "Documents", href: state?.booking_workspace?.booking_reference ? `/agency/document-workspaces?booking_reference=${encodeURIComponent(state.booking_workspace.booking_reference)}` : "/agency/document-workspaces" }, { label: "Finance", href: "/agency/invoices" }]}
            currentLabel={state?.invoice?.invoice_number || "Invoice"}
            status={invoice.status}
            validation={invoiceReady ? { state: invoice.due_amount > 0 ? "warning" : "ready", label: invoice.due_amount > 0 ? "Balance outstanding" : "Financial record ready", reason: invoice.due_amount > 0 ? "Outstanding balance remains visible before servicing decisions." : "Invoice lines and payment state are available for after-sales review." } : { state: "blocked", label: "Invoice line required", reason: "Add at least one reviewed line before continuing to after sales." }}
            previous={{ label: "Previous: documents", href: state?.booking_workspace?.booking_reference ? `/agency/document-workspaces?booking_reference=${encodeURIComponent(state.booking_workspace.booking_reference)}` : "/agency/document-workspaces" }}
            next={{ label: "Continue to after sales", href: invoiceReady ? `/agency/after-sales?invoice_id=${encodeURIComponent(invoiceId)}${bookingWorkspaceId ? `&booking_workspace_id=${encodeURIComponent(bookingWorkspaceId)}` : ""}` : undefined, enabled: invoiceReady, reason: "A reviewed invoice line is required." }}
            relatedRecords={[
              { label: "Booking", value: state?.booking_workspace?.workspace_number || state?.booking_record?.pnr_locator || state?.booking?.booking_reference || "none", href: bookingWorkspaceId ? `/agency/booking-workspaces/${bookingWorkspaceId}` : undefined },
              { label: "Lines", value: lineItems.length },
              { label: "Payments", value: payments.length },
              { label: "Credits", value: creditNotes.length },
            ]}
          />
          <section className="grid gap-4 md:grid-cols-4">
            <Metric label="Invoice total" value={money(invoice.total_amount, invoice.currency)} />
            <Metric label="Credits" value={money(invoice.credited_amount, invoice.currency)} />
            <Metric label="Allocated" value={money(invoice.paid_amount, invoice.currency)} />
            <Metric label="Due" value={money(invoice.due_amount, invoice.currency)} />
          </section>
          {state?.booking ? <a className="inline-flex rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-blue-700" href={`/agency/bookings/${state.booking.id}`}>Open booking {state.booking.booking_reference}</a> : null}
          <Panel title="Line Items">
            {canEdit && invoice.status === "draft" ? <form className="grid gap-3 md:grid-cols-[180px_1fr_120px_auto]" onSubmit={addLine}>
              <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.line_type} onChange={(event) => setField("line_type", event.target.value)}>
                {["ticket", "emd", "service", "agency_fee", "supplier_fee", "manual_fee", "tax", "discount", "adjustment"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
              </select>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Description" value={form.description} onChange={(event) => setField("description", event.target.value)} />
              <input type="number" step="0.01" className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.amount} onChange={(event) => setField("amount", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Add line</button>
            </form> : <p className="text-sm text-slate-600">Issued invoice lines are immutable. Corrections are recorded with credit notes.</p>}
            <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
              {lineItems.map((item) => (
                <div className="flex flex-wrap items-center justify-between gap-3 p-3 text-sm" key={item.id}>
                  <span>{item.description} · {item.line_type.replaceAll("_", " ")} · {item.total_amount} {item.currency}</span>
                  {canEdit && invoice.status === "draft" && item.status === "active" ? <button className="text-rose-700" onClick={() => archiveLine(item.id)}>Archive</button> : <span className="text-slate-500">{item.status}</span>}
                </div>
              ))}
            </div>
          </Panel>
          <Panel title="Payment allocations">
            {canEdit && ["issued", "partially_paid"].includes(invoice.status) && invoice.due_amount > 0 ? <form className="grid gap-3 md:grid-cols-[1fr_auto]" onSubmit={addPayment}>
              <input type="number" min="0.01" step="0.01" max={invoice.due_amount} className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.payment_amount} onChange={(event) => setField("payment_amount", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Record received payment</button>
            </form> : null}
            {payments.length ? (
              <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                {payments.map((payment) => (
                  <div className="flex flex-wrap items-center justify-between gap-3 p-3 text-sm" key={payment.id}>
                    <span>{money(payment.amount, payment.currency)} received · {money(payment.allocated_amount, payment.currency)} allocated · {payment.method.replaceAll("_", " ")}</span>
                    <span className="flex items-center gap-2"><PaymentStatusBadge status={payment.status} />{canEdit && payment.reconciliation_status !== "reconciled" ? <button className="text-blue-700" onClick={() => markReconciled(payment.id)}>Mark reconciled</button> : <span className="text-slate-500">{payment.reconciliation_status.replaceAll("_", " ")}</span>}</span>
                  </div>
                ))}
              </div>
            ) : <EmptyState title="No payments recorded" body="Record manual payments received outside AgencyOS." />}
            {allocations.length ? <p className="mt-3 text-xs text-slate-500">{allocations.length} immutable allocation {allocations.length === 1 ? "entry" : "entries"} settle this invoice.</p> : null}
          </Panel>
          <Panel title="Credit notes">
            {canEdit && ["issued", "partially_paid", "paid"].includes(invoice.status) ? <form className="grid gap-3 md:grid-cols-[1fr_140px_auto]" onSubmit={createCredit}>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Reason for credit" value={form.credit_reason} onChange={(event) => setField("credit_reason", event.target.value)} />
              <input required type="number" min="0.01" step="0.01" max={invoice.total_amount - invoice.credited_amount} className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.credit_amount} onChange={(event) => setField("credit_amount", event.target.value)} />
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold">Create credit</button>
            </form> : null}
            {creditNotes.length ? <div className="divide-y divide-slate-100 rounded-md border border-slate-200">{creditNotes.map((credit) => <div className="flex flex-wrap items-center justify-between gap-3 p-3 text-sm" key={credit.id}><span>{credit.credit_note_number} · {credit.reason} · {money(credit.total_amount, credit.currency)}</span><span className="flex items-center gap-2 capitalize">{credit.status}{canEdit && credit.status === "draft" ? <button className="text-blue-700" onClick={() => issueCredit(credit.id)}>Issue credit</button> : null}</span></div>)}</div> : <p className="text-sm text-slate-600">No non-destructive credits recorded.</p>}
          </Panel>
          {canEdit && ["draft", "issued"].includes(invoice.status) && invoice.paid_amount === 0 ? <Panel title="Cancel invoice">
            <div className="grid gap-3 md:grid-cols-[1fr_auto]">
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Required cancellation reason" value={form.cancellation_reason} onChange={(event) => setField("cancellation_reason", event.target.value)} />
              <button className="rounded-md border border-rose-200 px-3 py-2 text-sm font-medium text-rose-700 disabled:opacity-50" disabled={!form.cancellation_reason.trim()} onClick={cancelInvoice} type="button">Cancel invoice</button>
            </div>
          </Panel>
          : null}
          <OperationalCollaborationPanel
            agencyId={state.agency.id}
            entityId={invoiceId}
            entityLabel={invoice.invoice_number || "Invoice"}
            entityType="invoice"
          />
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

function money(value, currency) {
  return `${Number(value || 0).toFixed(2)} ${currency || ""}`.trim()
}
