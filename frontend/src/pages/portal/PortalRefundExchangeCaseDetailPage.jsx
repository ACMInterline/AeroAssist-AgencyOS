import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import RefundExchangeStatusBadge from "../../components/RefundExchangeStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalRefundExchangeCaseDetailPage({ caseId }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet(`/api/portal/refund-exchange-cases/${caseId}`)])
      .then(([me, detail]) => setState({ me, ...detail }))
      .catch((err) => setError(err.message))
  }, [caseId])

  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <a className="text-sm font-medium text-blue-700" href="/portal/refunds-exchanges">Back to refunds/exchanges</a>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state?.case_reference}</p>
              <h2 className="mt-1 text-2xl font-semibold text-slate-950">{state?.case_type?.replaceAll("_", " ")}</h2>
              <p className="mt-1 text-sm text-slate-600">Client-visible updates and statuses only.</p>
            </div>
            <RefundExchangeStatusBadge status={state?.status} />
          </div>

          <section className="grid gap-4 lg:grid-cols-3">
            <Info title="Overview" rows={[["Case", state?.case_reference], ["Type", state?.case_type], ["Priority", state?.priority], ["Reason", state?.reason_category], ["Reason date", state?.updated_at?.slice(0, 10)]]} />
            <Info title="Client-visible summary" rows={[["Summary", state?.client_visible_summary || "Not yet set"], ["Supplier ref", state?.supplier_reference || "Not set"], ["Booking", state?.booking?.booking_reference || "No booking"]]} />
            <Info title="Amounts" rows={[["Estimated due from client", `${state?.estimated_total_due_from_client || 0} ${state?.currency}`], ["Estimated due to client", `${state?.estimated_total_due_to_client || 0} ${state?.currency}`], ["Final due from client", `${state?.final_total_due_from_client || 0} ${state?.currency}`], ["Final due to client", `${state?.final_total_due_to_client || 0} ${state?.currency}`]]} />
          </section>

          <Panel title="Client-visible financial lines">
            <Rows title="lines" items={state?.financial_lines} empty="No client-visible lines yet" render={(line) => `${line.line_type.replaceAll("_", " ")} · ${line.amount} ${line.currency} · ${line.direction}`} />
          </Panel>

          <section className="grid gap-4 md:grid-cols-2">
            <Panel title="Client-visible items">
              <Rows title="items" items={state?.items} empty="No client-visible items yet" render={(item) => `${item.item_type.replaceAll("_", " ")} · ${item.description}`} />
            </Panel>
            <Panel title="Timeline">
              <Rows title="timeline events" items={state?.timeline} empty="No timeline entries yet" render={(item) => `${item.title}${item.summary ? ` · ${item.summary}` : ""}`} />
            </Panel>
          </section>

          <Panel title="Client-visible messages">
            <Rows title="messages" items={state?.messages} empty="No messages yet" render={(item) => item.message_text} />
          </Panel>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function Info({ title, rows }) {
  return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><dl className="mt-4 space-y-3 text-sm">{rows.map(([label, value]) => <div key={label}><dt className="font-medium text-slate-700">{label}</dt><dd className="mt-1 text-slate-600">{value || "n/a"}</dd></div>)}</dl></section>
}

function Panel({ title, children }) {
  return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section>
}

function Rows({ title, items, empty, render }) {
  if (!items?.length) return <EmptyState title={empty} body={`No ${title} yet`} />
  return <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">{items.map((item) => <div className="p-3 text-sm text-slate-700" key={item.id}>{render(item)}</div>)}</div>
}
