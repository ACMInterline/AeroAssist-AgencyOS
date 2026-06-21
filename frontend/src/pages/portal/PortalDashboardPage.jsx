import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import PortalSummaryCard from "../../components/PortalSummaryCard"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalDashboardPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/dashboard")])
      .then(([me, dashboard]) => setState({ me, dashboard }))
      .catch((err) => setError(err.message))
  }, [])

  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Read-only portal preview</p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-950">{state.me.client.display_name}</h2>
                <p className="mt-2 text-sm text-slate-600">View agency-approved records. Acceptance, payments, uploads, messaging, and request submission are not enabled yet.</p>
              </div>
              <PortalStatusBadge status={state.me.portal_account.portal_status} />
            </div>
          </section>
          <section className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
            <PortalSummaryCard label="Requests" value={state.dashboard.counts.requests} href="/portal/requests" />
            <PortalSummaryCard label="Offers" value={state.dashboard.counts.offers} href="/portal/offers" />
            <PortalSummaryCard label="Bookings" value={state.dashboard.counts.bookings} href="/portal/bookings" />
            <PortalSummaryCard label="Documents" value={state.dashboard.counts.documents} href="/portal/documents" />
            <PortalSummaryCard label="Invoices" value={state.dashboard.counts.invoices} href="/portal/invoices" />
            <PortalSummaryCard label="Payments" value={state.dashboard.counts.payments} href="/portal/payments" />
          </section>
          <section className="grid gap-4 lg:grid-cols-2">
            <Latest title="Latest offers" items={state.dashboard.latest.offers} hrefBase="/portal/offers" label={(item) => `${item.offer_reference} · ${item.title}`} />
            <Latest title="Latest documents" items={state.dashboard.latest.documents} hrefBase="/portal/documents" label={(item) => `${item.title} · ${item.document_type.replaceAll("_", " ")}`} />
          </section>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function Latest({ title, items, hrefBase, label }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{title}</h3>
      {items.length ? <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">{items.map((item) => <a className="block p-3 text-sm text-blue-700" href={`${hrefBase}/${item.id}`} key={item.id}>{label(item)}</a>)}</div> : <EmptyState title="Nothing visible yet" body="Agency-approved client-visible records will appear here." />}
    </section>
  )
}
