import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function BookingCreatePage() {
  const [state, setState] = useState(null)
  const [source, setSource] = useState("offer")
  const [form, setForm] = useState({ client_id: "", offer_id: "", route_id: "", fare_id: "", pnr: "", booking_channel: "manual", currency: "EUR", total_amount: 0 })
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const clients = await apiGet(`/api/agencies/${context.agency.id}/clients`)
    const offers = await apiGet(`/api/agencies/${context.agency.id}/offers`)
    setState({ ...context, clients: clients.items, offers: offers.items, offerDetail: null })
    setForm((current) => ({ ...current, client_id: clients.items[0]?.id || "", offer_id: offers.items[0]?.id || "" }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    async function loadOffer() {
      if (!state?.agency?.id || !form.offer_id || source !== "offer") return
      const detail = await apiGet(`/api/agencies/${state.agency.id}/offers/${form.offer_id}`)
      setState((current) => ({ ...current, offerDetail: detail }))
      setForm((current) => ({ ...current, route_id: detail.routes[0]?.id || "", fare_id: detail.fare_options[0]?.id || "" }))
    }
    loadOffer().catch((err) => setError(err.message))
  }, [state?.agency?.id, form.offer_id, source])

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function submit(event) {
    event.preventDefault()
    if (source === "offer") {
      const result = await apiPost(`/api/agencies/${state.agency.id}/offers/${form.offer_id}/create-booking`, {
        selected_route_alternative_id: form.route_id || null,
        selected_fare_option_id: form.fare_id || null,
        pnr: form.pnr || null,
        booking_channel: form.booking_channel,
        status: "draft",
        accept_offer: true,
      })
      window.location.href = `/agency/bookings/${result.booking.id}`
      return
    }
    const result = await apiPost(`/api/agencies/${state.agency.id}/bookings`, {
      client_id: form.client_id,
      pnr: form.pnr || null,
      booking_channel: form.booking_channel,
      currency: form.currency,
      total_amount: Number(form.total_amount),
      amount_due: Number(form.total_amount),
      status: "draft",
    })
    window.location.href = `/agency/bookings/${result.booking.id}`
  }

  const selectedRouteFares = (state?.offerDetail?.fare_options || []).filter((fare) => !form.route_id || fare.route_alternative_id === form.route_id)

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="max-w-3xl space-y-6">
          <div>
            <a className="text-sm font-medium text-blue-700" href="/agency/bookings">Back to bookings</a>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Create booking</h2>
            <p className="mt-1 text-sm text-slate-600">Save a manual tracking record. No booking or ticketing integration is connected.</p>
          </div>
          <form className="space-y-5 rounded-lg border border-slate-200 bg-white p-5" onSubmit={submit}>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-sm font-medium text-slate-700">
                Source
                <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={source} onChange={(event) => setSource(event.target.value)}>
                  <option value="offer">From offer</option>
                  <option value="manual">Manual</option>
                </select>
              </label>
              <label className="text-sm font-medium text-slate-700">
                PNR
                <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.pnr} onChange={(event) => setField("pnr", event.target.value)} />
              </label>
            </div>
            {source === "offer" ? (
              <div className="grid gap-3">
                <label className="text-sm font-medium text-slate-700">
                  Offer
                  <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.offer_id} onChange={(event) => setField("offer_id", event.target.value)}>
                    {state.offers.map((offer) => <option key={offer.id} value={offer.id}>{offer.offer_reference} · {offer.title}</option>)}
                  </select>
                </label>
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="text-sm font-medium text-slate-700">
                    Route alternative
                    <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.route_id} onChange={(event) => setField("route_id", event.target.value)}>
                      {(state.offerDetail?.routes || []).map((route) => <option key={route.id} value={route.id}>{route.label} · {route.title}</option>)}
                    </select>
                  </label>
                  <label className="text-sm font-medium text-slate-700">
                    Fare option
                    <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.fare_id} onChange={(event) => setField("fare_id", event.target.value)}>
                      {selectedRouteFares.map((fare) => <option key={fare.id} value={fare.id}>{fare.label} · {fare.total_amount} {fare.currency}</option>)}
                    </select>
                  </label>
                </div>
              </div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-3">
                <label className="text-sm font-medium text-slate-700">
                  Client
                  <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.client_id} onChange={(event) => setField("client_id", event.target.value)}>
                    {state.clients.map((client) => <option key={client.id} value={client.id}>{client.display_name}</option>)}
                  </select>
                </label>
                <label className="text-sm font-medium text-slate-700">
                  Currency
                  <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.currency} onChange={(event) => setField("currency", event.target.value)} />
                </label>
                <label className="text-sm font-medium text-slate-700">
                  Total
                  <input type="number" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.total_amount} onChange={(event) => setField("total_amount", event.target.value)} />
                </label>
              </div>
            )}
            <label className="block text-sm font-medium text-slate-700">
              Channel
              <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.booking_channel} onChange={(event) => setField("booking_channel", event.target.value)}>
                {["manual", "gds", "airline_portal", "ota_affiliate", "direct_airline_website", "supplier_email", "phone", "mixed"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
              </select>
            </label>
            <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Save draft</button>
          </form>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
