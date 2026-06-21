import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import OfferStatusBadge from "../../components/OfferStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function OfferDetailPage({ offerId }) {
  const [state, setState] = useState(null)
  const [forms, setForms] = useState({
    passenger_id: "",
    route_title: "",
    route_summary: "",
    carrier_summary: "",
    segment_route_id: "",
    origin_airport_code: "",
    destination_airport_code: "",
    marketing_airline_code: "",
    flight_number: "",
    fare_route_id: "",
    fare_label: "Standard",
    base_fare_amount: 0,
    taxes_amount: 0,
    airline_fees_amount: 0,
    agency_service_fee_amount: 0,
    price_fare_id: "",
    price_description: "",
    price_amount: 0,
    service_code: "",
    service_name: "",
  })
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const detail = await apiGet(`/api/agencies/${context.agency.id}/offers/${offerId}`)
    const passengers = await apiGet(`/api/agencies/${context.agency.id}/passengers`)
    setState({ ...context, ...detail, agencyPassengers: passengers.items })
    setForms((current) => ({
      ...current,
      passenger_id: passengers.items[0]?.id || "",
      segment_route_id: detail.routes[0]?.id || "",
      fare_route_id: detail.routes[0]?.id || "",
      price_fare_id: detail.fare_options[0]?.id || "",
    }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [offerId])

  function setField(name, value) {
    setForms((current) => ({ ...current, [name]: value }))
  }

  async function addPassenger(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/offers/${offerId}/passengers`, { passenger_id: forms.passenger_id, is_primary_traveler: state.passengers.length === 0 })
    await load()
  }

  async function addRoute(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/offers/${offerId}/route-alternatives`, {
      sequence: state.routes.length + 1,
      label: String.fromCharCode(65 + state.routes.length),
      title: forms.route_title,
      route_summary: forms.route_summary,
      carrier_summary: forms.carrier_summary,
      source_channel: "manual",
      status: "draft",
    })
    setForms((current) => ({ ...current, route_title: "", route_summary: "", carrier_summary: "" }))
    await load()
  }

  async function addSegment(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/offers/${offerId}/route-alternatives/${forms.segment_route_id}/segments`, {
      sequence: state.segments.filter((segment) => segment.route_alternative_id === forms.segment_route_id).length + 1,
      marketing_airline_code: forms.marketing_airline_code,
      flight_number: forms.flight_number,
      origin_airport_code: forms.origin_airport_code,
      destination_airport_code: forms.destination_airport_code,
    })
    setForms((current) => ({ ...current, origin_airport_code: "", destination_airport_code: "", marketing_airline_code: "", flight_number: "" }))
    await load()
  }

  async function addFare(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/offers/${offerId}/route-alternatives/${forms.fare_route_id}/fare-options`, {
      sequence: state.fare_options.filter((fare) => fare.route_alternative_id === forms.fare_route_id).length + 1,
      label: forms.fare_label,
      branded_fare_name: forms.fare_label,
      status: "complete",
      currency: state.offer.currency,
      base_fare_amount: Number(forms.base_fare_amount),
      taxes_amount: Number(forms.taxes_amount),
      airline_fees_amount: Number(forms.airline_fees_amount),
      agency_service_fee_amount: Number(forms.agency_service_fee_amount),
      refundable_status: "unknown",
      changeability_status: "unknown",
    })
    await load()
  }

  async function addPriceLine(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/offers/${offerId}/fare-options/${forms.price_fare_id}/price-lines`, {
      line_type: "other",
      description: forms.price_description,
      quantity: 1,
      unit_amount: Number(forms.price_amount),
      currency: state.offer.currency,
      client_visible: true,
    })
    setForms((current) => ({ ...current, price_description: "", price_amount: 0 }))
    await load()
  }

  async function addServiceCheck(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/offers/${offerId}/service-checks`, {
      service_code: forms.service_code,
      service_name: forms.service_name,
      support_status: "needs_airline_confirmation",
      client_visible_summary: "Service support must be confirmed manually.",
      requires_airline_confirmation: true,
    })
    setForms((current) => ({ ...current, service_code: "", service_name: "" }))
    await load()
  }

  async function sendOffer() {
    await apiPost(`/api/agencies/${state.agency.id}/offers/${offerId}/send`)
    await load()
  }

  async function renderOfferSummary() {
    const result = await apiPost(`/api/agencies/${state.agency.id}/offers/${offerId}/render-document`, { document_type: "offer_summary" })
    window.location.href = `/agency/documents/${result.document.id}`
  }

  const routeById = Object.fromEntries((state?.routes || []).map((route) => [route.id, route]))
  const validToSend = (state?.routes || []).length > 0 && (state?.fare_options || []).length > 0

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <a className="text-sm font-medium text-blue-700" href="/agency/offers">Back to offers</a>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state.offer.offer_reference}</p>
              <h2 className="text-2xl font-semibold text-slate-950">{state.offer.title}</h2>
              <p className="mt-1 text-sm text-slate-600">Manually researched option. Price must be verified before ticketing.</p>
            </div>
            <OfferStatusBadge status={state.offer.status} />
          </div>
          <div className="rounded-lg border border-blue-100 bg-blue-50 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-blue-950">Post-offer operations</h3>
                <p className="mt-1 text-sm text-blue-800">Create a manual booking tracking record from this offer. No reservation or ticketing integration is connected.</p>
              </div>
              <a className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" href="/agency/bookings/new">Create booking</a>
              <button className="rounded-md border border-blue-200 bg-white px-4 py-2 text-sm font-semibold text-blue-700" onClick={renderOfferSummary}>Render offer summary</button>
            </div>
          </div>
          <AirlineIntelLinkPanel
            title="Search policy/service notes"
            airlineCode={state.segments.find((segment) => segment.marketing_airline_code)?.marketing_airline_code}
            serviceCodes={state.service_checks.map((service) => service.service_code)}
          />
          <section className="grid gap-4 lg:grid-cols-3">
            <InfoCard title="Overview" rows={[
              ["Client", state.client.display_name],
              ["Source", state.offer.source.replaceAll("_", " ")],
              ["Currency", state.offer.currency],
              ["Routes", state.offer.route_alternative_count],
              ["Fare options", state.offer.fare_option_count],
            ]} />
            <InfoCard title="Totals" rows={[
              ["Minimum", state.offer.total_min_amount ?? "n/a"],
              ["Maximum", state.offer.total_max_amount ?? "n/a"],
              ["Valid until", state.offer.valid_until || "Not set"],
            ]} />
            <InfoCard title="Notes" rows={[
              ["Intro", state.offer.client_visible_intro || "None"],
              ["Terms", state.offer.client_visible_terms || "None"],
              ["Internal", state.offer.internal_notes || "None"],
            ]} />
          </section>
          <Panel title="Passengers">
            <form className="flex gap-2" onSubmit={addPassenger}>
              <select className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" value={forms.passenger_id} onChange={(event) => setField("passenger_id", event.target.value)}>
                {state.agencyPassengers.map((passenger) => <option key={passenger.id} value={passenger.id}>{passenger.display_name}</option>)}
              </select>
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Add passenger</button>
            </form>
            <List items={state.passengers} empty="No offer passengers yet" render={(item) => `${item.snapshot_display_name} · ${item.snapshot_passenger_type}`} />
          </Panel>
          <Panel title="Route Alternatives">
            <form className="grid gap-3 md:grid-cols-[1fr_1fr_1fr_auto]" onSubmit={addRoute}>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Title" value={forms.route_title} onChange={(event) => setField("route_title", event.target.value)} />
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Route summary" value={forms.route_summary} onChange={(event) => setField("route_summary", event.target.value)} />
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Carrier summary" value={forms.carrier_summary} onChange={(event) => setField("carrier_summary", event.target.value)} />
              <button disabled={state.routes.length >= 3} className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white disabled:bg-slate-300" type="submit">Add route</button>
            </form>
            <List items={state.routes} empty="No route alternatives yet" render={(item) => `${item.label}. ${item.title} · ${item.source_channel.replaceAll("_", " ")} · ${item.connection_quality.replaceAll("_", " ")}`} />
          </Panel>
          <Panel title="Segments">
            <form className="grid gap-3 md:grid-cols-[1fr_1fr_1fr_1fr_auto]" onSubmit={addSegment}>
              <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={forms.segment_route_id} onChange={(event) => setField("segment_route_id", event.target.value)}>
                {state.routes.map((route) => <option key={route.id} value={route.id}>{route.label} · {route.title}</option>)}
              </select>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Airline code" value={forms.marketing_airline_code} onChange={(event) => setField("marketing_airline_code", event.target.value)} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Origin" value={forms.origin_airport_code} onChange={(event) => setField("origin_airport_code", event.target.value)} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Destination" value={forms.destination_airport_code} onChange={(event) => setField("destination_airport_code", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Add</button>
            </form>
            <List items={state.segments} empty="No segments yet" render={(item) => `${routeById[item.route_alternative_id]?.label || "Route"} · ${item.marketing_airline_code}${item.flight_number || ""} ${item.origin_airport_code}-${item.destination_airport_code}`} />
          </Panel>
          <Panel title="Fare Options / Pricing">
            <form className="grid gap-3 md:grid-cols-[1fr_1fr_100px_100px_100px_100px_auto]" onSubmit={addFare}>
              <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={forms.fare_route_id} onChange={(event) => setField("fare_route_id", event.target.value)}>
                {state.routes.map((route) => <option key={route.id} value={route.id}>{route.label} · {route.title}</option>)}
              </select>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={forms.fare_label} onChange={(event) => setField("fare_label", event.target.value)} />
              {["base_fare_amount", "taxes_amount", "airline_fees_amount", "agency_service_fee_amount"].map((field) => <input key={field} type="number" className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={forms[field]} onChange={(event) => setField(field, event.target.value)} />)}
              <button disabled={state.fare_options.filter((fare) => fare.route_alternative_id === forms.fare_route_id).length >= 3} className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white disabled:bg-slate-300" type="submit">Add fare</button>
            </form>
            <List items={state.fare_options} empty="No fare options yet" render={(item) => `${routeById[item.route_alternative_id]?.label || "Route"} · ${item.label} · ${item.total_amount} ${item.currency}${item.is_recommended ? " · recommended" : ""}`} />
          </Panel>
          <Panel title="Price Lines">
            <form className="grid gap-3 md:grid-cols-[1fr_1fr_120px_auto]" onSubmit={addPriceLine}>
              <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={forms.price_fare_id} onChange={(event) => setField("price_fare_id", event.target.value)}>
                {state.fare_options.map((fare) => <option key={fare.id} value={fare.id}>{fare.label} · {fare.total_amount}</option>)}
              </select>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Description" value={forms.price_description} onChange={(event) => setField("price_description", event.target.value)} />
              <input type="number" className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={forms.price_amount} onChange={(event) => setField("price_amount", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Add line</button>
            </form>
            <List items={state.price_lines} empty="No price lines yet" render={(item) => `${item.description} · ${item.total_amount} ${item.currency} · ${item.line_type.replaceAll("_", " ")}`} />
          </Panel>
          <Panel title="Service Support">
            <form className="grid gap-3 md:grid-cols-[120px_1fr_auto]" onSubmit={addServiceCheck}>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Code" value={forms.service_code} onChange={(event) => setField("service_code", event.target.value)} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Service name" value={forms.service_name} onChange={(event) => setField("service_name", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Add check</button>
            </form>
            <List items={state.service_checks} empty="No service support checks yet" render={(item) => `${item.service_code} · ${item.service_name} · ${item.support_status.replaceAll("_", " ")}`} />
          </Panel>
          <Panel title="Client Preview">
            <p className="text-sm text-slate-600">Internal preview only. No public/share URL and no client acceptance yet.</p>
            <div className="mt-4 grid gap-3">
              {state.routes.map((route) => (
                <div className="rounded-md border border-slate-200 p-4" key={route.id}>
                  <h4 className="font-semibold text-slate-950">{route.label}. {route.title}</h4>
                  <p className="mt-1 text-sm text-slate-600">{route.route_summary || "Route summary not set"}</p>
                  <div className="mt-3 grid gap-2 md:grid-cols-3">
                    {state.fare_options.filter((fare) => fare.route_alternative_id === route.id).map((fare) => (
                      <div className="rounded-md bg-slate-50 p-3 text-sm" key={fare.id}>
                        <p className="font-medium text-slate-900">{fare.label}</p>
                        <p className="mt-1 text-slate-600">{fare.total_amount} {fare.currency}</p>
                        <p className="mt-1 text-slate-500">{fare.baggage_summary || "Baggage notes not set"}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Panel>
          <Panel title="Send Panel">
            <ul className="space-y-2 text-sm text-slate-600">
              <li>Route alternative present: {state.routes.length ? "yes" : "no"}</li>
              <li>Fare option present: {state.fare_options.length ? "yes" : "no"}</li>
              <li>Send marks offer as sent and snapshots current content.</li>
              <li>Actual email/client portal delivery is not implemented yet.</li>
            </ul>
            <button disabled={!validToSend || state.offer.status === "sent"} className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300" onClick={sendOffer}>
              Send and snapshot
            </button>
          </Panel>
          <Panel title="Timeline">
            <List items={state.timeline} empty="No offer timeline events yet" render={(item) => `${item.title}${item.summary ? ` · ${item.summary}` : ""}`} />
          </Panel>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Panel({ title, children }) {
  return <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section>
}

function List({ items, empty, render }) {
  if (!items?.length) return <EmptyState title={empty} body="Add manually researched content when available." />
  return <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">{items.map((item) => <div className="p-3 text-sm text-slate-700" key={item.id}>{render(item)}</div>)}</div>
}

function InfoCard({ title, rows }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{title}</h3>
      <dl className="mt-4 space-y-3 text-sm">
        {rows.map(([label, value]) => <div key={label}><dt className="font-medium text-slate-700">{label}</dt><dd className="mt-1 text-slate-600">{value}</dd></div>)}
      </dl>
    </div>
  )
}

function AirlineIntelLinkPanel({ title, airlineCode, serviceCodes }) {
  const primaryService = serviceCodes.find(Boolean)
  const query = new URLSearchParams()
  if (airlineCode) query.set("airline", airlineCode)
  if (primaryService) query.set("service_code", primaryService)
  return (
    <section className="rounded-lg border border-cyan-100 bg-cyan-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-cyan-950">{title}</h3>
          <p className="mt-1 text-sm text-cyan-800">Manual lookup only. No feasibility or pricing automation is applied.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <a className="rounded-md bg-cyan-700 px-3 py-2 text-sm font-semibold text-white" href={`/agency/airline-intelligence?${query.toString()}`}>Open search</a>
          {["PETC", "AVIH", "WCHR", "WCHS", "WCHC", "UMNR"].map((code) => <a className="rounded-md border border-cyan-200 bg-white px-2 py-1 text-xs font-semibold text-cyan-800" href={`/agency/airline-intelligence?service_code=${code}`} key={code}>{code}</a>)}
        </div>
      </div>
    </section>
  )
}
