import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import RequestStatusBadge from "../../components/RequestStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalRequestDetailPage({ requestId }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => { Promise.all([apiGet("/api/portal/me"), apiGet(`/api/portal/requests/${requestId}`)]).then(([me, detail]) => setState({ me, ...detail })).catch((err) => setError(err.message)) }, [requestId])
  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3"><div><a className="text-sm font-medium text-blue-700" href="/portal/requests">Back to requests</a><p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state.request.request_reference}</p><h2 className="text-2xl font-semibold text-slate-950">{state.request.title}</h2></div><RequestStatusBadge status={state.request.status} /></div>
          <section className="grid gap-4 md:grid-cols-3"><Info title="Overview" rows={[["Route", state.request.route_summary], ["Services", state.request.service_summary], ["Departure", state.request.requested_departure_date], ["Return", state.request.requested_return_date]]} /><Info title="Notes" rows={[["Client notes", state.request.client_notes], ["Agency note", state.request.client_visible_notes]]} /><Info title="Counts" rows={[["Passengers", state.passengers.length], ["Services", state.services.length], ["Messages", state.messages.length]]} /></section>
          <Panel title="Messages"><Rows items={state.messages} empty="No client-visible messages" render={(item) => item.message_text} /></Panel>
          <Panel title="Timeline"><Rows items={state.timeline} empty="No client-visible timeline events" render={(item) => `${item.title}${item.summary ? ` · ${item.summary}` : ""}`} /></Panel>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function Panel({ title, children }) { return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section> }
function Rows({ items, empty, render }) { return items.length ? <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">{items.map((item) => <div className="p-3 text-sm text-slate-700" key={item.id}>{render(item)}</div>)}</div> : <EmptyState title={empty} body="Only client-visible records appear in the portal." /> }
function Info({ title, rows }) { return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><dl className="mt-4 space-y-3 text-sm">{rows.map(([label, value]) => <div key={label}><dt className="font-medium text-slate-700">{label}</dt><dd className="mt-1 text-slate-600">{value || "Not set"}</dd></div>)}</dl></section> }
