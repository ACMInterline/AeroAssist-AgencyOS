import { useEffect, useState } from "react"
import ArrowRight from "lucide-react/dist/esm/icons/arrow-right.js"
import ClipboardPlus from "lucide-react/dist/esm/icons/clipboard-plus.js"
import EmptyState from "../../components/EmptyState"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import PortalSummaryCard from "../../components/PortalSummaryCard"
import { PortalRecordList, PortalSection, formatDate, formatDateTime, formatMoney, titleCase } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalDashboardPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/workspace/dashboard")])
      .then(([me, dashboard]) => setState({ me, dashboard }))
      .catch((err) => setError(err.message))
  }, [])

  const passenger = state?.dashboard?.subject_type === "passenger"
  const subject = passenger ? state?.me?.passenger : state?.me?.client
  const dashboard = state?.dashboard || {}
  const counts = dashboard.counts || {}

  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-8">
          <header className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 pb-5">
            <div>
              <p className="text-xs font-semibold uppercase text-blue-700">{passenger ? "Your journey workspace" : "Your travel workspace"}</p>
              <h2 className="mt-1 text-2xl font-semibold text-slate-950">Welcome, {subject?.display_name || "traveller"}</h2>
              <p className="mt-2 text-sm text-slate-600">{passenger ? "Your trips, travel documents, assistance, and actions in one place." : "Requests, travel options, trips, documents, and account actions in one place."}</p>
            </div>
            <div className="flex items-center gap-2">
              <PortalStatusBadge status={state?.me?.portal_account?.portal_status} />
              {!passenger ? <a className="primary-button" href="/portal/requests/new"><ClipboardPlus aria-hidden="true" className="h-4 w-4" />New request</a> : null}
            </div>
          </header>

          <section aria-label="Workspace summary" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6">
            <PortalSummaryCard label="Upcoming trips" value={counts.upcoming_trips || 0} href="/portal/trips" />
            {!passenger ? <PortalSummaryCard label="Pending offers" value={counts.pending_offers || 0} href="/portal/travel-options" /> : null}
            <PortalSummaryCard label="Action required" value={counts.action_required || 0} href="/portal/notifications" />
            <PortalSummaryCard label="Documents" value={counts.documents || 0} href="/portal/documents" />
            <PortalSummaryCard label="Messages" value={counts.communications || 0} href="/portal/communications" />
            <PortalSummaryCard label={passenger ? "Assistance" : "Service requests"} value={counts.service_requests || 0} href="/portal/assistance" />
          </section>

          <div className="grid gap-8 xl:grid-cols-2">
            <PortalSection title={passenger ? "My trips" : "Upcoming trips"} action={<TextLink href="/portal/trips" label="View trips" />}>
              <PortalRecordList items={dashboard.upcoming_trips} emptyTitle="No upcoming trips" emptyBody="Confirmed journey records will appear here." href={(item) => `/portal/trips/${item.id}`}>
                {(item) => <Record title={item.title || item.trip_reference} meta={`${item.route_summary || "Route pending"} · ${formatDate(item.next_departure)}`} status={item.status} />}
              </PortalRecordList>
            </PortalSection>

            {!passenger ? (
              <PortalSection title="Pending offers" action={<TextLink href="/portal/travel-options" label="Review options" />}>
                <PortalRecordList items={dashboard.pending_offers} emptyTitle="No offers need a decision" emptyBody="Released travel options will appear here." href={(item) => `/portal/travel-options/${item.id}`}>
                  {(item) => <Record title={item.title || item.delivery_code} meta={`Available until ${formatDateTime(item.expires_at)}`} status={item.status} />}
                </PortalRecordList>
              </PortalSection>
            ) : (
              <PortalSection title="My tickets" action={<TextLink href="/portal/tickets" label="View tickets" />}>
                <PortalRecordList items={dashboard.tickets} emptyTitle="No tickets visible" emptyBody="Issued ticket records linked to you will appear here." href={(item) => `/portal/tickets/${item.id}`}>
                  {(item) => <Record title={item.ticket_number || "Ticket pending"} meta={`${item.passenger_name || "Passenger"} · ${item.validating_carrier || "Carrier pending"}`} status={item.status} />}
                </PortalRecordList>
              </PortalSection>
            )}

            <PortalSection title="Action required" action={<TextLink href="/portal/notifications" label="View all actions" />}>
              <PortalRecordList items={dashboard.action_required} emptyTitle="Nothing needs your attention" emptyBody="Deadlines, approvals, and requested information will appear here.">
                {(item) => <Record title={titleCase(item.title || item.type)} meta={item.summary || formatDateTime(item.due_at || item.created_at)} status={item.status} />}
              </PortalRecordList>
            </PortalSection>

            <PortalSection title={passenger ? "My assistance" : "Service requests"} action={<TextLink href="/portal/assistance" label="View services" />}>
              <PortalRecordList items={dashboard.service_requests} emptyTitle="No assistance requests visible" emptyBody="Passenger services linked to current trips will appear here.">
                {(item) => <Record title={item.service_label || item.service_code} meta={titleCase(item.service_family)} status={item.status} />}
              </PortalRecordList>
            </PortalSection>

            <PortalSection title="Recent communications" action={<TextLink href="/portal/communications" label="Open messages" />}>
              <PortalRecordList items={dashboard.recent_communications} emptyTitle="No messages yet" emptyBody="Conversations shared by your agency will appear here." href={(item) => `/portal/communications/${item.id}`}>
                {(item) => <Record title={item.subject || item.title || "Conversation"} meta={item.last_message_preview || formatDateTime(item.last_message_at)} status={item.status} />}
              </PortalRecordList>
            </PortalSection>

            <PortalSection title="Recent documents" action={<TextLink href="/portal/documents" label="Open documents" />}>
              <PortalRecordList items={dashboard.recent_documents} emptyTitle="No documents visible" emptyBody="Travel documents and requested uploads will appear here." href={(item) => `/portal/documents/${item.id}`}>
                {(item) => <Record title={item.title} meta={`${titleCase(item.type)} · ${formatDate(item.deadline)}`} status={item.status} />}
              </PortalRecordList>
            </PortalSection>

            <PortalSection title="Recent timeline" action={<TextLink href="/portal/timeline" label="View timeline" />}>
              <PortalRecordList items={dashboard.recent_timeline} emptyTitle="No journey activity yet" emptyBody="Shared journey updates will appear here.">
                {(item) => <Record title={item.summary || titleCase(item.event_type)} meta={formatDateTime(item.occurred_at)} status={item.status} />}
              </PortalRecordList>
            </PortalSection>

            {!passenger ? (
              <PortalSection title="Outstanding payments" action={<TextLink href="/portal/finance" label="Open finance" />}>
                <div className="grid gap-3 sm:grid-cols-2">
                  <Metric label="Outstanding balance" value={formatMoney(dashboard.outstanding_payments?.outstanding_balance || 0, dashboard.outstanding_payments?.currency)} />
                  <Metric label="Travel credits" value={formatMoney(dashboard.outstanding_payments?.travel_credit_total || 0, dashboard.outstanding_payments?.currency)} />
                </div>
                {dashboard.travel_credits?.length ? <p className="mt-3 text-sm text-slate-600">{dashboard.travel_credits.length} credit record{dashboard.travel_credits.length === 1 ? "" : "s"} available.</p> : null}
              </PortalSection>
            ) : (
              <PortalSection title="Travel profile" action={<TextLink href="/portal/profile" label="Review profile" />}>
                <dl className="grid gap-3 sm:grid-cols-2">
                  <Metric label="Passenger type" value={titleCase(dashboard.travel_profile?.passenger_type)} />
                  <Metric label="Preferred language" value={dashboard.travel_profile?.primary_language || "Not set"} />
                </dl>
              </PortalSection>
            )}
          </div>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function Record({ title, meta, status }) {
  return <div className="flex flex-wrap items-start justify-between gap-2"><div><p className="font-medium text-slate-950">{title || "Untitled record"}</p><p className="mt-1 text-sm text-slate-600">{meta}</p></div>{status ? <PortalStatusBadge status={status} /> : null}</div>
}

function TextLink({ href, label }) {
  return <a className="inline-flex items-center gap-1 text-sm font-semibold text-blue-700" href={href}>{label}<ArrowRight aria-hidden="true" className="h-4 w-4" /></a>
}

function Metric({ label, value }) {
  return <div className="border-l-2 border-blue-200 pl-3"><dt className="text-xs font-semibold uppercase text-slate-500">{label}</dt><dd className="mt-1 text-lg font-semibold text-slate-950">{value}</dd></div>
}
