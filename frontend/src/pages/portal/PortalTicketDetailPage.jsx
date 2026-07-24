import { useEffect, useState } from "react"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalFacts, PortalPageHeader, PortalRecordList, PortalSection, PortalTimeline, formatDate, formatMoney, titleCase } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalTicketDetailPage({ ticketId }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet(`/api/portal/tickets/${ticketId}`)])
      .then(([me, detail]) => setState({ me, ...detail }))
      .catch((err) => setError(err.message))
  }, [ticketId])

  const ticket = state?.ticket || {}
  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-8">
          <PortalPageHeader eyebrow="Ticket" title={ticket.ticket_number || "Ticket pending"} description={ticket.passenger_name || ticket.passenger?.display_name || "Passenger"} status={ticket.status} backHref="/portal/tickets" backLabel="Back to tickets" />
          <PortalSection title="Ticket details"><PortalFacts columns={3} rows={[["Passenger", ticket.passenger_name || ticket.passenger?.display_name], ["Validating carrier", ticket.validating_carrier], ["Issue date", formatDate(ticket.issue_date)], ["Total", formatMoney(ticket.total_amount, ticket.currency)], ["Coupon summary", ticket.coupon_summary], ["Status", titleCase(ticket.status)]]} /></PortalSection>
          <PortalSection title="Flight coupons">
            <PortalRecordList items={state?.coupons} emptyTitle="No coupon details" emptyBody="Coupon status will appear when it is available.">
              {(item) => <div className="grid gap-2 sm:grid-cols-[80px_minmax(0,1fr)_minmax(180px,0.7fr)_auto] sm:items-center"><p className="font-semibold text-blue-800">Coupon {item.coupon_number}</p><div><p className="font-semibold text-slate-950">{item.origin || "TBC"} to {item.destination || "TBC"}</p><p className="text-sm text-slate-600">{item.marketing_carrier || item.operating_carrier || "Carrier pending"} {item.flight_number || ""}</p></div><p className="text-sm text-slate-600">{item.fare_basis || "Fare basis not shown"} · {item.cabin || item.booking_class || "Cabin pending"}</p><PortalStatusBadge status={item.status} /></div>}
            </PortalRecordList>
          </PortalSection>
          <div className="grid gap-8 lg:grid-cols-2">
            <PortalSection title="Refund status"><LedgerRows items={state?.refunds} amountLabel="Refund" /></PortalSection>
            <PortalSection title="Exchange status"><LedgerRows items={state?.exchanges} amountLabel="Exchange" /></PortalSection>
          </div>
          <PortalSection title="Documents"><PortalRecordList items={state?.documents} emptyTitle="No ticket documents" emptyBody="Visible receipts and ticket documents will appear here." href={(item) => `/portal/documents/${item.id}`}>{(item) => <div className="flex flex-wrap items-center justify-between gap-3"><p className="font-semibold text-slate-950">{item.title}</p><PortalStatusBadge status={item.status} /></div>}</PortalRecordList></PortalSection>
          <PortalSection title="Ticket timeline"><PortalTimeline items={state?.timeline} /></PortalSection>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function LedgerRows({ items, amountLabel }) {
  return items?.length ? <div className="divide-y divide-slate-200 border-y border-slate-200">{items.map((item) => <div className="flex flex-wrap items-center justify-between gap-3 py-3" key={item.id}><div><p className="font-medium text-slate-950">{amountLabel} {item.reference || item.id}</p><p className="text-sm text-slate-600">{formatDate(item.recorded_at || item.created_at)}</p></div><div className="text-right"><PortalStatusBadge status={item.status} /><p className="mt-1 text-sm text-slate-600">{formatMoney(item.amount || item.total_amount, item.currency)}</p></div></div>)}</div> : <p className="text-sm text-slate-500">No {amountLabel.toLowerCase()} record is linked.</p>
}
