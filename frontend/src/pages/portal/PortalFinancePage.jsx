import { useEffect, useState } from "react"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import PortalSummaryCard from "../../components/PortalSummaryCard"
import { PortalFacts, PortalPageHeader, PortalRecordList, PortalSection, formatDate, formatMoney } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalFinancePage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/finance")])
      .then(([me, finance]) => setState({ me, finance }))
      .catch((err) => setError(err.message))
  }, [])
  const finance = state?.finance || {}
  const summary = finance.summary || {}
  return <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}><ProtectedRoute loading={!state && !error} error={error}><div className="space-y-8"><PortalPageHeader eyebrow="Account" title="Finance" description="Invoices, balances, recorded payments, travel credits, and refunds." /><section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><PortalSummaryCard label="Outstanding" value={formatMoney(summary.outstanding_balance || 0, summary.currency)} /><PortalSummaryCard label="Invoices" value={summary.invoice_count || 0} /><PortalSummaryCard label="Recorded payments" value={summary.payment_count || 0} /><PortalSummaryCard label="Travel credits" value={formatMoney(summary.travel_credit_total || 0, summary.currency)} /></section><PortalSection title="Invoices"><PortalRecordList items={finance.invoices} emptyTitle="No invoices visible" emptyBody="Invoices shared by your agency will appear here.">{(item) => <div className="space-y-3"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-semibold text-slate-950">{item.invoice_number || item.reference || "Invoice"}</p><p className="text-sm text-slate-600">Issued {formatDate(item.issue_date || item.created_at)} · Due {formatDate(item.due_date)}</p></div><div className="text-right"><PortalStatusBadge status={item.status} /><p className="mt-1 font-semibold text-slate-950">{formatMoney(item.total_amount, item.currency)}</p></div></div>{item.lines?.length ? <PortalFacts rows={item.lines.map((line) => [line.description || "Invoice item", formatMoney(line.total_amount || line.amount, item.currency)])} /> : null}</div>}</PortalRecordList></PortalSection><div className="grid gap-8 lg:grid-cols-3"><PortalSection title="Payments"><FinanceRows items={finance.payments} empty="No payments recorded." /></PortalSection><PortalSection title="Travel credits"><FinanceRows items={finance.credits} empty="No travel credits recorded." /></PortalSection><PortalSection title="Refunds"><FinanceRows items={finance.refunds} empty="No refunds recorded." /></PortalSection></div><p className="border-t border-slate-200 pt-4 text-sm text-slate-500">Payments cannot be made through this portal.</p></div></ProtectedRoute></ClientPortalLayout>
}

function FinanceRows({ items, empty }) {
  return items?.length ? <div className="divide-y divide-slate-200 border-y border-slate-200">{items.map((item) => <div className="py-3" key={item.id}><div className="flex items-center justify-between gap-3"><p className="font-medium text-slate-950">{item.reference || item.payment_reference || item.credit_number || "Record"}</p><PortalStatusBadge status={item.status} /></div><p className="mt-1 text-sm text-slate-600">{formatMoney(item.amount || item.total_amount, item.currency)} · {formatDate(item.recorded_at || item.created_at)}</p></div>)}</div> : <p className="text-sm text-slate-500">{empty}</p>
}
