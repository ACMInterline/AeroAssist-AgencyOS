import { useEffect, useState } from "react"
import InvoiceStatusBadge from "../../components/InvoiceStatusBadge"
import PaymentStatusBadge from "../../components/PaymentStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalInvoiceDetailPage({ invoiceId }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => { Promise.all([apiGet("/api/portal/me"), apiGet(`/api/portal/invoices/${invoiceId}`)]).then(([me, detail]) => setState({ me, ...detail })).catch((err) => setError(err.message)) }, [invoiceId])
  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3"><div><a className="text-sm font-medium text-blue-700" href="/portal/invoices">Back to invoices</a><p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state.invoice.invoice_number}</p><h2 className="text-2xl font-semibold text-slate-950">Invoice summary</h2></div><InvoiceStatusBadge status={state.invoice.status} /></div>
          <section className="grid gap-4 md:grid-cols-4"><Metric label="Total" value={`${state.invoice.total_amount} ${state.invoice.currency}`} /><Metric label="Paid" value={`${state.invoice.paid_amount} ${state.invoice.currency}`} /><Metric label="Due" value={`${state.invoice.due_amount} ${state.invoice.currency}`} /><Metric label="Due date" value={state.invoice.due_date || "Not set"} /></section>
          <Panel title="Line items"><Rows items={state.line_items} render={(item) => `${item.description} · ${item.total_amount} ${item.currency}`} /></Panel>
          <Panel title="Payments"><div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">{state.payments.length ? state.payments.map((item) => <div className="flex items-center justify-between gap-2 p-3 text-sm text-slate-700" key={item.id}><span>{item.amount} {item.currency} · {item.method?.replaceAll("_", " ")}</span><PaymentStatusBadge status={item.status} /></div>) : <div className="p-3 text-sm text-slate-500">No payments recorded.</div>}</div></Panel>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function Panel({ title, children }) { return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section> }
function Rows({ items, render }) { return <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">{items.length ? items.map((item) => <div className="p-3 text-sm text-slate-700" key={item.id}>{render(item)}</div>) : <div className="p-3 text-sm text-slate-500">No visible records.</div>}</div> }
function Metric({ label, value }) { return <div className="rounded-lg border border-slate-200 bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-lg font-semibold text-slate-950">{value}</p></div> }
