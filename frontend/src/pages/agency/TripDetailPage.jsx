import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function TripDetailPage({ tripId }) {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ trip_title: "", trip_status: "draft", trip_type: "unknown", operational_summary: "", internal_notes: "", client_visible_notes: "", link_request_id: "" })
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const detail = await apiGet(`/api/agencies/${context.agency.id}/trips/${tripId}`)
    const requests = await apiGet(`/api/agencies/${context.agency.id}/requests`)
    setState({ ...context, ...detail, requests: requests.items })
    setForm({
      trip_title: detail.trip.trip_title || "",
      trip_status: detail.trip.trip_status || "draft",
      trip_type: detail.trip.trip_type || "unknown",
      operational_summary: detail.trip.operational_summary || "",
      internal_notes: detail.trip.internal_notes || "",
      client_visible_notes: detail.trip.client_visible_notes || "",
      link_request_id: "",
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [tripId])

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function save(event) {
    event.preventDefault()
    await apiPut(`/api/agencies/${state.agency.id}/trips/${tripId}`, {
      trip_title: form.trip_title,
      trip_status: form.trip_status,
      trip_type: form.trip_type,
      operational_summary: form.operational_summary,
      internal_notes: form.internal_notes,
      client_visible_notes: form.client_visible_notes,
    })
    await load()
  }

  async function linkRequest(event) {
    event.preventDefault()
    if (!form.link_request_id) return
    await apiPost(`/api/agencies/${state.agency.id}/trips/${tripId}/link-request/${form.link_request_id}`)
    await load()
  }

  async function unlinkRequest(requestId) {
    await apiPost(`/api/agencies/${state.agency.id}/trips/${tripId}/unlink-request/${requestId}`)
    await load()
  }

  async function rebuild() {
    await apiPost(`/api/agencies/${state.agency.id}/trips/${tripId}/rebuild-summary`)
    await load()
  }

  async function archive() {
    await apiPost(`/api/agencies/${state.agency.id}/trips/${tripId}/archive`)
    await load()
  }

  const unlinkedRequests = (state?.requests || []).filter((request) => !request.trip_id || request.trip_id === tripId)

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <a className="text-sm font-medium text-blue-700" href="/agency/trips">Back to trips</a>
                <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state?.trip?.trip_reference}</p>
                <h2 className="text-3xl font-semibold tracking-tight text-slate-950">{state?.trip?.trip_title}</h2>
                <p className="mt-1 text-sm text-slate-600">{state?.trip?.route_summary || "Route pending"} · {state?.trip?.date_summary || "Dates pending"}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={rebuild}>Rebuild summary</button>
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={archive}>Archive</button>
              </div>
            </div>
          </div>

          <section className="grid gap-4 lg:grid-cols-4">
            <Metric label="Status" value={state?.trip?.trip_status?.replaceAll("_", " ")} />
            <Metric label="Passengers" value={state?.trip?.passenger_count ?? 0} />
            <Metric label="Segments" value={state?.trip?.segment_count ?? 0} />
            <Metric label="Services" value={state?.trip?.service_count ?? 0} />
          </section>

          <form className="grid gap-4 rounded-lg border border-slate-200 bg-white p-5 md:grid-cols-3" onSubmit={save}>
            <Field label="Trip title" value={form.trip_title} onChange={(value) => setField("trip_title", value)} />
            <Select label="Status" value={form.trip_status} onChange={(value) => setField("trip_status", value)} options={["draft", "planning", "quoted", "booked", "ticketed", "in_travel", "completed", "cancelled", "archived"]} />
            <Select label="Trip type" value={form.trip_type} onChange={(value) => setField("trip_type", value)} options={["one_way", "round_trip", "multi_city", "open_jaw", "complex", "unknown"]} />
            <Textarea label="Operational summary" value={form.operational_summary} onChange={(value) => setField("operational_summary", value)} />
            <Textarea label="Internal notes" value={form.internal_notes} onChange={(value) => setField("internal_notes", value)} />
            <Textarea label="Client-visible notes" value={form.client_visible_notes} onChange={(value) => setField("client_visible_notes", value)} />
            <div className="md:col-span-3">
              <button className="aa-primary-action rounded-md px-4 py-2 text-sm font-semibold" type="submit">Save trip</button>
            </div>
          </form>

          <Panel title="Linked requests">
            <form className="flex flex-wrap gap-2" onSubmit={linkRequest}>
              <select className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.link_request_id} onChange={(event) => setField("link_request_id", event.target.value)}>
                <option value="">Select request</option>
                {unlinkedRequests.map((request) => <option key={request.id} value={request.id}>{request.request_reference} · {request.title}</option>)}
              </select>
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Link request</button>
            </form>
            <List items={state?.linked_requests} empty="No linked requests" render={(request) => (
              <div className="flex flex-wrap items-center justify-between gap-2">
                <a className="font-medium text-blue-700" href={`/agency/requests/${request.id}`}>{request.request_reference} · {request.title}</a>
                <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => unlinkRequest(request.id)}>Unlink</button>
              </div>
            )} />
          </Panel>

          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Passengers"><List items={state?.passengers} empty="No trip passengers copied yet" render={(item) => `${item.display_name} · ${item.passenger_type.replaceAll("_", " ")}${item.assistance_summary ? ` · ${item.assistance_summary}` : ""}`} /></Panel>
            <Panel title="Segments"><List items={state?.segments} empty="No trip segments copied yet" render={(item) => `${item.segment_order}. ${item.origin_airport_code} to ${item.destination_airport_code}${item.departure_date ? ` · ${item.departure_date}` : ""}${item.flight_number ? ` · ${item.flight_number}` : ""}`} /></Panel>
          </section>
          <Panel title="Services"><List items={state?.services} empty="No trip services copied yet" render={(item) => `${item.service_code} · ${item.service_label} · ${item.status.replaceAll("_", " ")} · ${item.passenger_ids.length} pax / ${item.segment_ids.length} seg`} /></Panel>
          <Panel title="Special Services">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-950">Passenger service checks</p>
                <p className="mt-1 text-sm text-slate-600">Rules evaluation and SSR/OSI previews for this trip.</p>
              </div>
              <a className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" href={`/agency/trips/${tripId}/special-services`}>Open Special Services</a>
            </div>
          </Panel>

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            {["Offers", "Bookings", "Tickets / EMDs", "Documents", "Invoices / Payments"].map((title) => <FuturePanel title={title} key={title} />)}
          </section>

          <Panel title="Timeline"><List items={state?.timeline} empty="No trip timeline events yet" render={(item) => `${item.title}${item.summary ? ` · ${item.summary}` : ""}`} /></Panel>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div>
}

function Panel({ title, children }) {
  return <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section>
}

function FuturePanel({ title }) {
  return <section className="rounded-lg border border-dashed border-slate-300 bg-white p-4"><h3 className="text-sm font-semibold text-slate-950">{title}</h3><p className="mt-2 text-xs text-slate-500">Future phase. This dossier can anchor the workflow later, but no functionality is active here yet.</p></section>
}

function List({ items, empty, render }) {
  if (!items?.length) return <EmptyState title={empty} body="Trip dossier records appear here after requests are linked or conversion runs." />
  return <div className="divide-y divide-slate-100 rounded-md border border-slate-200 bg-white">{items.map((item) => <div className="p-3 text-sm leading-6 text-slate-700" key={item.id}>{render(item)}</div>)}</div>
}

function Field({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<input className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Textarea({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700 md:col-span-3">{label}<textarea className="min-h-20 rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Select({ label, value, onChange, options }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<select className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option value={option} key={option}>{option.replaceAll("_", " ")}</option>)}</select></label>
}
