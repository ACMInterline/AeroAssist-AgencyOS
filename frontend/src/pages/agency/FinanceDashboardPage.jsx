import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import PageHeader from "../../components/PageHeader"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function FinanceDashboardPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  const params = new URLSearchParams(window.location.search)
  const tripId = params.get("trip_id") || ""
  const bookingId = params.get("booking_id") || ""

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const scope = tripId ? `?trip_id=${encodeURIComponent(tripId)}` : bookingId ? `?booking_id=${encodeURIComponent(bookingId)}` : ""
      const [report, transactions] = await Promise.all([
        apiGet(`/api/agencies/${context.agency.id}/finance/reporting${scope}`),
        apiGet(`/api/agencies/${context.agency.id}/finance/ledger/transactions${scope}`),
      ])
      setState({ ...context, report, transactions: transactions.items || [] })
    }
    load().catch((err) => setError(err.message))
  }, [bookingId, tripId])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <PageHeader
            breadcrumbs={[{ label: "Operations", href: "/agency" }, { label: "Finance" }]}
            eyebrow={tripId || bookingId ? "Scoped commercial ledger" : "Commercial ledger"}
            title="Finance & reports"
            description={tripId ? "Posted commercial evidence for the selected Trip." : bookingId ? "Posted commercial evidence for the selected Booking." : "Invoice, payment, supplier-cost, credit, refund, and exchange reporting derived from posted ledger evidence."}
            actions={<div className="flex flex-wrap gap-2"><a className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" href="/agency/invoices">Invoices</a><a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/payments">Payments</a>{state?.report?.supplier_costs_visible ? <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/supplier-costs">Supplier costs</a> : null}</div>}
          />

          {(state?.report?.summaries || []).length ? state.report.summaries.map((summary) => (
            <section className="space-y-3" key={summary.currency}>
              <div className="flex items-center justify-between"><h3 className="font-semibold text-slate-950">{summary.currency} ledger</h3><span className="text-xs font-medium text-slate-500">Posted evidence only</span></div>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <Metric label="Revenue" value={amount(summary.revenue, summary.currency)} />
                {state.report.supplier_costs_visible ? <Metric label="Supplier costs" value={amount(summary.supplier_costs, summary.currency)} /> : null}
                {state.report.supplier_costs_visible ? <Metric label="Gross margin" value={amount(summary.gross_margin, summary.currency)} /> : null}
                <Metric label="Payments received" value={amount(summary.payments_received, summary.currency)} />
                <Metric label="Refund exposure" value={amount(summary.refund_exposure, summary.currency)} />
                <Metric label="Exchange exposure" value={amount(summary.exchange_exposure, summary.currency)} />
              </div>
            </section>
          )) : <EmptyState title="No posted commercial activity" body="Draft invoices and unconfirmed supplier costs do not become reportable ledger facts until an authorized operator posts them." />}

          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Outstanding invoices">
              <RecordList items={state?.report?.outstanding_invoices} empty="No invoice balances are outstanding." render={(item) => <a className="font-medium text-blue-700" href={`/agency/invoices/${item.invoice_id}`}>{item.invoice_id} · {item.amount}</a>} />
            </Panel>
            <Panel title="Unallocated payments">
              <RecordList items={state?.report?.outstanding_payments} empty="No received payment balance is waiting for allocation." render={(item) => <span>{item.payment_id} · {amount(item.unallocated_amount, item.currency)}</span>} />
            </Panel>
          </section>

          <Panel title="Recent ledger activity">
            <RecordList
              items={(state?.transactions || []).slice(0, 12)}
              empty="No ledger transactions have been posted."
              render={(item) => <div className="flex flex-wrap items-center justify-between gap-2"><span className="font-medium text-slate-900">{label(item.entry_type)}</span><span className="text-slate-600">{item.direction === "decrease" ? "-" : ""}{amount(item.amount, item.currency)}</span></div>}
            />
          </Panel>

          <p className="text-xs text-slate-500">AeroAssist records reviewed commercial evidence only. It does not execute payments, file taxes, or synchronize external accounting systems.</p>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Metric({ label: metricLabel, value }) {
  return <div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{metricLabel}</p><p className="mt-2 text-xl font-semibold text-slate-950">{value}</p></div>
}

function Panel({ title, children }) {
  return <section className="rounded-md border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><div className="mt-4">{children}</div></section>
}

function RecordList({ items = [], empty, render }) {
  if (!items.length) return <p className="text-sm text-slate-600">{empty}</p>
  return <div className="divide-y divide-slate-100">{items.map((item, index) => <div className="py-3 text-sm" key={item.id || item.invoice_id || item.payment_id || index}>{render(item)}</div>)}</div>
}

function amount(value, currency) {
  return `${Number(value || 0).toFixed(2)} ${currency || ""}`.trim()
}

function label(value) {
  return String(value || "unknown").replaceAll("_", " ")
}
