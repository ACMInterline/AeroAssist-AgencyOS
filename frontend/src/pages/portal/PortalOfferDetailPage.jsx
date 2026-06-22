import { useEffect, useState } from "react"
import OfferStatusBadge from "../../components/OfferStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet, apiPost } from "../../lib/api"

export default function PortalOfferDetailPage({ offerId }) {
  const [state, setState] = useState(null)
  const [reason, setReason] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  async function load() {
    const [me, detail] = await Promise.all([apiGet("/api/portal/me"), apiGet(`/api/portal/offers/${offerId}`)])
    setState({ me, ...detail })
  }
  useEffect(() => { load().catch((err) => setError(err.message)) }, [offerId])
  async function decide(decision) {
    setError("")
    setMessage("")
    try {
      await apiPost(`/api/portal/offers/${offerId}/${decision}`, { reason: reason || undefined })
      setMessage(decision === "accept" ? "Offer accepted for agency review. This did not create a booking or ticket." : "Offer rejected and sent to the agency for review.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }
  const canDecide = state && !["accepted", "rejected", "expired", "withdrawn", "archived"].includes(state.offer.status)
  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3"><div><a className="text-sm font-medium text-blue-700" href="/portal/offers">Back to offers</a><p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state.offer.offer_reference}</p><h2 className="text-2xl font-semibold text-slate-950">{state.offer.title}</h2><p className="mt-1 text-sm text-slate-600">A decision sends this offer to agency staff for manual follow-up. It does not book or ticket automatically.</p></div><OfferStatusBadge status={state.offer.status} /></div>
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Decision</h3>
            <textarea className="mt-3 min-h-20 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Optional reason or note" value={reason} onChange={(event) => setReason(event.target.value)} disabled={!canDecide} />
            <div className="mt-3 flex flex-wrap gap-3">
              <button className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" type="button" disabled={!canDecide} onClick={() => decide("accept")}>Accept for review</button>
              <button className="rounded-md border border-rose-200 px-4 py-2 text-sm font-semibold text-rose-700 disabled:opacity-50" type="button" disabled={!canDecide} onClick={() => decide("reject")}>Reject</button>
            </div>
            {message ? <p className="mt-3 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p> : null}
            {error ? <p className="mt-3 rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
          </section>
          <section className="grid gap-4 md:grid-cols-3"><Info title="Overview" rows={[["Valid until", state.offer.valid_until], ["Currency", state.offer.currency], ["Minimum", state.offer.total_min_amount], ["Maximum", state.offer.total_max_amount]]} /><Info title="Intro" rows={[["Message", state.offer.client_visible_intro], ["Terms", state.offer.client_visible_terms]]} /><Info title="Counts" rows={[["Routes", state.routes.length], ["Fares", state.fare_options.length], ["Services", state.service_checks.length]]} /></section>
          <Panel title="Routes"><Rows items={state.routes} render={(item) => `${item.label}. ${item.title} · ${item.route_summary || "Route summary not set"}`} /></Panel>
          <Panel title="Segments"><Rows items={state.segments} render={(item) => `${item.marketing_airline_code}${item.flight_number || ""} ${item.origin_airport_code}-${item.destination_airport_code} · ${item.cabin || "cabin n/a"}`} /></Panel>
          <Panel title="Fare options"><Rows items={state.fare_options} render={(item) => `${item.label} · ${item.total_amount} ${item.currency} · ${item.baggage_summary || "Baggage not set"}`} /></Panel>
          <Panel title="Price lines"><Rows items={state.price_lines} render={(item) => `${item.description} · ${item.total_amount} ${item.currency}`} /></Panel>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function Panel({ title, children }) { return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section> }
function Rows({ items, render }) { return <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">{items.length ? items.map((item) => <div className="p-3 text-sm text-slate-700" key={item.id}>{render(item)}</div>) : <div className="p-3 text-sm text-slate-500">No visible records.</div>}</div> }
function Info({ title, rows }) { return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><dl className="mt-4 space-y-3 text-sm">{rows.map(([label, value]) => <div key={label}><dt className="font-medium text-slate-700">{label}</dt><dd className="mt-1 text-slate-600">{value || "Not set"}</dd></div>)}</dl></section> }
