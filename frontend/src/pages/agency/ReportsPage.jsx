import { useEffect, useState } from "react"
import ArrowRight from "lucide-react/dist/esm/icons/arrow-right.js"
import PageHeader from "../../components/PageHeader"
import ProtectedRoute from "../../components/ProtectedRoute"
import WorkspacePage from "../../components/WorkspacePage"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function ReportsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const [operations, finance] = await Promise.all([
        apiGet(`/api/agencies/${context.agency.id}/operations-command-center/summary`),
        apiGet(`/api/agencies/${context.agency.id}/finance/reporting`),
      ])
      setState({ ...context, operations: operations.summary || {}, finance })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const operations = state?.operations || {}
  const finance = state?.finance || {}

  return (
    <AgencyLayout agency={state?.agency} user={state?.me?.user}>
      <ProtectedRoute error={error} loading={!state && !error}>
        <WorkspacePage as="main" className="space-y-6">
          <PageHeader
            breadcrumbs={[{ label: "Dashboard", href: "/agency" }, { label: "Reports" }]}
            eyebrow="Operational and commercial overview"
            title="Reports"
            description="Review current workload, deadlines, departures, and posted commercial results, then open the source records for action."
          />

          <section aria-labelledby="operations-report-heading">
            <h2 className="text-base font-semibold text-slate-950" id="operations-report-heading">Operations</h2>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Metric href="/agency/work-queue" label="Open work" value={operations.current_operational_workload || 0} />
              <Metric href="/agency/deadlines" label="Due soon" value={operations.due_soon || 0} />
              <Metric href="/agency/deadlines" label="Overdue" value={operations.overdue || 0} tone="warning" />
              <Metric href="/agency/bookings" label="Bookings needing action" value={(operations.accepted_offers_awaiting_booking || 0) + (operations.bookings_awaiting_ticketing || 0)} />
              <Metric href="/agency/offers" label="Offers awaiting action" value={operations.offers_awaiting_action || 0} />
              <Metric href="/agency/document-workspaces" label="Approvals and documents" value={operations.service_approvals_documents || 0} />
              <Metric href="/agency/trips" label="Departures in 72 hours" value={operations.departures_next_72_hours || 0} />
              <Metric href="/agency/after-sales" label="After-sales cases" value={operations.after_sales_cases || 0} />
            </div>
          </section>

          <section aria-labelledby="finance-report-heading">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-base font-semibold text-slate-950" id="finance-report-heading">Posted commercial results</h2>
              <a className="inline-flex items-center gap-1 text-sm font-semibold text-blue-700" href="/agency/finance">Open Finance <ArrowRight aria-hidden="true" className="h-4 w-4" /></a>
            </div>
            {(finance.summaries || []).length ? (
              <div className="mt-3 grid gap-3 lg:grid-cols-2">
                {finance.summaries.map((summary) => (
                  <article className="rounded-lg border border-slate-200 bg-white p-5" key={summary.currency}>
                    <h3 className="font-semibold text-slate-950">{summary.currency}</h3>
                    <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                      <Fact label="Revenue" value={money(summary.revenue, summary.currency)} />
                      {finance.supplier_costs_visible ? <Fact label="Gross margin" value={money(summary.gross_margin, summary.currency)} /> : null}
                      <Fact label="Payments received" value={money(summary.payments_received, summary.currency)} />
                      <Fact label="Refund exposure" value={money(summary.refund_exposure, summary.currency)} />
                    </dl>
                  </article>
                ))}
              </div>
            ) : <p className="mt-3 rounded-lg border border-dashed border-slate-300 bg-white p-5 text-sm text-slate-600">Posted invoice, payment, credit, refund, and exchange activity will appear here.</p>}
          </section>
        </WorkspacePage>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Metric({ href, label, tone = "default", value }) {
  return (
    <a className={`rounded-lg border bg-white p-4 hover:border-blue-300 ${tone === "warning" && Number(value) > 0 ? "border-amber-300" : "border-slate-200"}`} href={href}>
      <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
      <span className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-blue-700">Open records <ArrowRight aria-hidden="true" className="h-3.5 w-3.5" /></span>
    </a>
  )
}

function Fact({ label, value }) {
  return <div><dt className="text-xs font-semibold text-slate-500">{label}</dt><dd className="mt-1 text-lg font-semibold text-slate-950">{value}</dd></div>
}

function money(value, currency) {
  return `${Number(value || 0).toFixed(2)} ${currency || ""}`.trim()
}
