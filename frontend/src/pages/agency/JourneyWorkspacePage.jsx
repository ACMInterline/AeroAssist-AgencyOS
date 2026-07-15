import { useEffect, useMemo, useState } from "react"
import ArrowRight from "lucide-react/dist/esm/icons/arrow-right.js"
import Clock3 from "lucide-react/dist/esm/icons/clock-3.js"
import GitBranch from "lucide-react/dist/esm/icons/git-branch.js"
import History from "lucide-react/dist/esm/icons/history.js"
import Plane from "lucide-react/dist/esm/icons/plane.js"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import Save from "lucide-react/dist/esm/icons/save.js"
import Settings2 from "lucide-react/dist/esm/icons/settings-2.js"
import ShieldCheck from "lucide-react/dist/esm/icons/shield-check.js"
import TriangleAlert from "lucide-react/dist/esm/icons/triangle-alert.js"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaultPresentation = {
  show_airline_logos: true,
  show_aircraft: true,
  show_terminals: true,
  show_booking_classes: false,
  show_connection_details: true,
  show_operational_warnings: true,
  show_service_details: true,
  show_price_breakdown: true,
  show_internal_information: true,
  client_safe_mode: false,
}

export default function JourneyWorkspacePage() {
  const [state, setState] = useState(null)
  const [selectedId, setSelectedId] = useState("")
  const [detail, setDetail] = useState(null)
  const [presentation, setPresentation] = useState(defaultPresentation)
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const sourceQuery = useMemo(() => new URLSearchParams(window.location.search), [])
  const sourceType = sourceQuery.get("source_entity_type") || ""
  const sourceId = sourceQuery.get("source_entity_id") || ""

  async function load(preferredId = selectedId) {
    const context = await loadCurrentAgency()
    const [response, summaryResponse] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/journeys`),
      apiGet(`/api/agencies/${context.agency.id}/journeys/summary`),
    ])
    const journeys = response.items || []
    const queryMatch = journeys.find((item) => item.source_entity_type.includes(sourceType) && item.source_entity_id === sourceId)
    const nextId = preferredId || queryMatch?.id || journeys[0]?.id || ""
    setState({ ...context, journeys, summary: summaryResponse.summary || {} })
    setSelectedId(nextId)
    if (nextId) {
      const full = await apiGet(`/api/agencies/${context.agency.id}/journeys/${nextId}`)
      setDetail(full)
      setPresentation({ ...defaultPresentation, ...(full.presentation || {}) })
    } else {
      setDetail(null)
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function selectJourney(id) {
    setSelectedId(id)
    setError("")
    const full = await apiGet(`/api/agencies/${state.agency.id}/journeys/${id}`)
    setDetail(full)
    setPresentation({ ...defaultPresentation, ...(full.presentation || {}) })
  }

  async function createFromSource() {
    if (!sourceType || !sourceId) return
    const routeType = sourceType.replace("_workspace", "").replace("_v2", "")
    const supported = { trip: "trip", offer: "offer", booking: "booking", ticket: "ticket", emd: "emd" }
    const key = Object.keys(supported).find((item) => routeType.includes(item))
    if (!key) {
      setError("This source type needs a manual Journey representation.")
      return
    }
    const created = await apiPost(`/api/agencies/${state.agency.id}/journeys/from-${supported[key]}/${encodeURIComponent(sourceId)}`, {})
    const journeyId = created.journey?.id
    setNotice(created.created === false ? "Existing Journey representation opened." : "Journey representation created from source metadata.")
    await load(journeyId)
  }

  async function createManual() {
    const created = await apiPost(`/api/agencies/${state.agency.id}/journeys`, {
      title: "New journey representation",
      source_entity_type: "manual_entry",
      source_entity_id: `manual:${Date.now()}`,
      status: "draft",
    })
    setNotice("Draft Journey representation created. Unknown route data remains flagged for review.")
    await load(created.journey.id)
  }

  async function createSnapshot() {
    const response = await apiPost(`/api/agencies/${state.agency.id}/journeys/${selectedId}/snapshots`, { snapshot_type: "journey_updated", finalize: true })
    setNotice(`Immutable snapshot v${response.snapshot.version_number} created.`)
    await selectJourney(selectedId)
  }

  async function savePresentation() {
    const response = await apiPut(`/api/agencies/${state.agency.id}/journeys/${selectedId}/presentation`, presentation)
    setPresentation({ ...defaultPresentation, ...response.presentation })
    setNotice("Presentation settings saved. Source operational records were not changed.")
  }

  const journey = detail?.journey
  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase text-blue-700">Daily Work</p>
              <h1 className="mt-2 text-2xl font-semibold text-slate-950">Journeys</h1>
              <p className="mt-1 max-w-4xl text-sm text-slate-600">Canonical itinerary presentations projected from operational records. Source records remain authoritative; unknown data stays visible and no availability, live price, booking, ticketing, provider, or publishing action runs here.</p>
            </div>
            <div className="flex gap-2">
              <button type="button" title="Create manual journey" onClick={() => createManual().catch((err) => setError(err.message))} className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-300 bg-white text-slate-700"><Plus className="h-4 w-4" /></button>
              <button type="button" title="Refresh journeys" onClick={() => load().catch((err) => setError(err.message))} className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-300 bg-white text-slate-700"><RefreshCw className="h-4 w-4" /></button>
            </div>
          </header>

          {sourceType && sourceId ? <section className="flex flex-wrap items-center justify-between gap-3 border-y border-blue-200 bg-blue-50 px-4 py-3"><div><p className="font-semibold text-blue-950">Source context ready</p><p className="text-sm text-blue-800">Create or open the Journey view for this {title(sourceType)} record.</p></div><button type="button" onClick={() => createFromSource().catch((err) => setError(err.message))} className="inline-flex items-center gap-2 rounded-md bg-blue-700 px-3 py-2 text-sm font-semibold text-white"><GitBranch className="h-4 w-4" />Create Journey Representation</button></section> : null}
          {notice ? <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</div> : null}
          {error ? <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <Metric label="Journeys" value={state?.journeys?.length || 0} />
            <Metric label="Options" value={state?.summary?.itinerary_option_count || 0} />
            <Metric label="Segments" value={state?.summary?.journey_segment_count || 0} />
            <Metric label="Snapshots" value={state?.summary?.snapshot_count || 0} />
            <Metric label="Review required" value={state?.summary?.manual_review_journey_count || 0} warning />
          </section>

          <div className="grid gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
            <aside>
              <div className="flex items-center justify-between"><h2 className="font-semibold text-slate-950">Journey list</h2><span className="text-sm text-slate-500">{state?.journeys?.length || 0}</span></div>
              <div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">
                {(state?.journeys || []).map((item) => <button type="button" onClick={() => selectJourney(item.id).catch((err) => setError(err.message))} className={`block w-full px-2 py-3 text-left ${selectedId === item.id ? "bg-blue-50" : "hover:bg-slate-50"}`} key={item.id}><p className="font-semibold text-slate-950">{item.title}</p><p className="mt-1 text-sm text-slate-600">{item.origin_airport_code || "Unknown"} → {item.destination_airport_code || "Unknown"}</p><div className="mt-2 flex items-center justify-between text-xs text-slate-500"><span>{title(item.source_entity_type)}</span><span>{item.completeness_score || 0}%</span></div></button>)}
              </div>
            </aside>

            {journey ? <JourneyDetail detail={detail} presentation={presentation} setPresentation={setPresentation} onSavePresentation={savePresentation} onCreateSnapshot={createSnapshot} onError={setError} /> : <EmptyState title="No journey selected" body="Create a representation from a canonical source record or start a manual draft." />}
          </div>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function JourneyDetail({ detail, presentation, setPresentation, onSavePresentation, onCreateSnapshot, onError }) {
  const journey = detail.journey
  const options = detail.itinerary_options || []
  return <main className="min-w-0 space-y-7">
    <section className="border-b border-slate-200 pb-5">
      <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase text-slate-500">{journey.journey_reference}</p><h2 className="mt-1 text-xl font-semibold text-slate-950">{journey.title}</h2><p className="mt-2 text-2xl font-semibold text-slate-950">{journey.origin_airport_code || "Unknown"} <ArrowRight className="mx-2 inline h-5 w-5 text-slate-400" /> {journey.destination_airport_code || "Unknown"}</p></div><div className="flex flex-wrap gap-2"><Badge value={journey.presentation_status} />{journey.manual_review_required ? <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-800 ring-1 ring-amber-200"><TriangleAlert className="h-3.5 w-3.5" />Review required</span> : <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-800 ring-1 ring-emerald-200"><ShieldCheck className="h-3.5 w-3.5" />Complete</span>}</div></div>
      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4"><Info label="Source context" value={title(journey.source_entity_type)} /><Info label="Passengers" value={(journey.passenger_ids || []).length || "Unknown"} /><Info label="Departure" value={dateText(journey.departure_date)} /><Info label="Completeness" value={`${journey.completeness_score || 0}%`} /></div>
      <div className="mt-4 flex flex-wrap gap-2"><a href={`/agency/journey-authoring?journey_id=${encodeURIComponent(journey.id)}`} className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800"><Plane className="h-4 w-4" />Edit Journey segments</a><a href={`/agency/journey-option-composition?journey_id=${encodeURIComponent(journey.id)}`} className="inline-flex items-center gap-2 rounded-md bg-blue-700 px-3 py-2 text-sm font-semibold text-white"><GitBranch className="h-4 w-4" />Compose itinerary options</a></div>
      {(journey.warning_codes || []).length ? <div className="mt-4 flex flex-wrap gap-2">{journey.warning_codes.map((item) => <Badge value={item} warning key={item} />)}</div> : null}
    </section>

    <section><div className="flex items-end justify-between"><div><h3 className="text-lg font-semibold text-slate-950">Itinerary options</h3><p className="mt-1 text-sm text-slate-600">Chronological projections with explicit provenance and unknown-data states.</p></div><span className="text-sm text-slate-500">{options.length}</span></div>{options.length ? <div className="mt-4 grid gap-4">{options.map((option) => <ItineraryOption option={option} detail={detail} key={option.id} />)}</div> : <EmptyState title="No itinerary options" body="Add an option or project segments from an existing operational source." />}</section>

    <section className="grid gap-6 lg:grid-cols-2">
      <ReferenceSection title="Fare brands" items={detail.fare_brands || []} empty="No fare-brand presentation attached." render={(item) => <div><div className="flex justify-between gap-3"><p className="font-semibold text-slate-950">{item.client_display_name || item.brand_name}</p><Badge value={item.data_status} /></div><p className="mt-2 text-sm text-slate-600">{item.cabin_code ? `${title(item.cabin_code)} · ` : ""}{item.currency && item.total_price != null ? `${item.currency} ${item.total_price}` : "Price not supplied"}</p><p className="mt-1 text-sm text-slate-600">Baggage: {item.baggage_summary || "Unknown"}</p><p className="mt-1 text-sm text-slate-600">Changes: {item.change_summary || "Unknown"}</p></div>} />
      <ReferenceSection title="Service requirements" items={detail.services || []} empty="No service presentation attached." render={(item) => <div><div className="flex flex-wrap items-center justify-between gap-2"><p className="font-semibold text-slate-950">{item.service_code} · {item.service_name}</p><Badge value={item.confirmation_status} /></div><p className="mt-2 text-sm text-slate-600">{item.client_safe_summary || "Client-safe summary not supplied."}</p><p className="mt-1 text-xs text-slate-500">Approval {yesNo(item.approval_required)} · Document {yesNo(item.document_required)} · EMD {yesNo(item.EMD_required)}</p></div>} />
    </section>

    <section className="grid gap-6 lg:grid-cols-2">
      <div><div className="flex items-center gap-2"><History className="h-4 w-4 text-blue-700" /><h3 className="text-lg font-semibold text-slate-950">Snapshots and versions</h3></div><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{(detail.snapshots || []).map((item) => <div className="flex items-center justify-between gap-3 py-3" key={item.id}><div><p className="font-semibold text-slate-950">Version {item.version_number} · {title(item.snapshot_type)}</p><p className="mt-1 text-xs text-slate-500">{item.content_hash?.slice(0, 14)}… · {item.immutable ? "Finalized and immutable" : "Draft"}</p></div><Badge value={item.immutable ? "immutable" : "draft"} /></div>)}{!(detail.snapshots || []).length ? <p className="py-4 text-sm text-slate-500">No snapshots yet.</p> : null}</div><button type="button" onClick={() => onCreateSnapshot().catch((err) => onError(err.message))} className="mt-3 inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-800"><History className="h-4 w-4" />Create immutable snapshot</button></div>
      <div><div className="flex items-center gap-2"><Settings2 className="h-4 w-4 text-blue-700" /><h3 className="text-lg font-semibold text-slate-950">Presentation settings</h3></div><div className="mt-3 grid gap-2 sm:grid-cols-2">{Object.keys(defaultPresentation).map((key) => <label className="flex items-center gap-2 border-b border-slate-200 py-2 text-sm text-slate-700" key={key}><input type="checkbox" checked={Boolean(presentation[key])} onChange={(event) => setPresentation({ ...presentation, [key]: event.target.checked })} /><span>{title(key)}</span></label>)}</div><button type="button" onClick={() => onSavePresentation().catch((err) => onError(err.message))} className="mt-3 inline-flex items-center gap-2 rounded-md bg-blue-700 px-3 py-2 text-sm font-semibold text-white"><Save className="h-4 w-4" />Save settings</button></div>
    </section>
  </main>
}

function ItineraryOption({ option, detail }) {
  const segments = (detail.segments || []).filter((item) => item.itinerary_option_id === option.id).sort((a, b) => (a.segment_number || 0) - (b.segment_number || 0))
  const connections = (detail.connections || []).filter((item) => item.itinerary_option_id === option.id)
  return <article className="rounded-md border border-slate-200 bg-white p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase text-blue-700">Option {option.option_number}</p><h4 className="mt-1 font-semibold text-slate-950">{option.title}</h4><p className="mt-1 text-sm text-slate-600">{minutes(option.total_elapsed_minutes)} total · {option.total_segment_count || segments.length} segments · {option.total_connection_count || connections.length} connections</p></div><div className="flex flex-wrap gap-2"><Badge value={option.status} />{option.manual_review_required ? <Badge value="manual review" warning /> : null}</div></div><div className="mt-5 border-l-2 border-blue-200 pl-5">{segments.map((segment, index) => <div key={segment.id}><Segment segment={segment} />{index < segments.length - 1 ? <Connection connection={connections.find((item) => item.inbound_segment_id === segment.id)} /> : null}</div>)}</div>{!segments.length ? <p className="mt-4 text-sm text-amber-800">No projected segments. Source data remains incomplete.</p> : null}<p className="mt-4 text-xs text-slate-500">Provenance: {title(option.source_provenance?.provenance_type)} · {title(option.source_provenance?.data_state)} · parsed data is not treated as verified automatically.</p></article>
}

function Segment({ segment }) {
  return <div className="relative pb-4"><Plane className="absolute -left-[31px] top-0 h-4 w-4 bg-white text-blue-700" /><div className="grid gap-3 sm:grid-cols-[1fr_auto_1fr]"><div><p className="text-2xl font-semibold text-slate-950">{segment.origin_airport_code || "???"}</p><p className="mt-1 text-sm text-slate-600">{dateTime(segment.departure_local || segment.departure_utc)}</p><p className="mt-1 text-xs text-slate-500">Terminal {segment.departure_terminal || "unknown"}</p></div><ArrowRight className="mt-2 hidden h-5 w-5 text-slate-400 sm:block" /><div className="sm:text-right"><p className="text-2xl font-semibold text-slate-950">{segment.destination_airport_code || "???"}</p><p className="mt-1 text-sm text-slate-600">{dateTime(segment.arrival_local || segment.arrival_utc)}</p><p className="mt-1 text-xs text-slate-500">Terminal {segment.arrival_terminal || "unknown"}</p></div></div><div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-600"><strong className="text-slate-950">{segment.marketing_carrier_code || "Airline unknown"} {segment.marketing_flight_number || ""}</strong><span>Operated by {segment.operating_carrier_code || "unknown"}</span><span>{segment.aircraft_display_name || segment.aircraft_code || "Aircraft unknown"}</span><span>{title(segment.cabin_code)}</span><span>{segment.booking_class_code ? `Class ${segment.booking_class_code}` : "Class unknown"}</span></div>{(segment.warning_codes || []).length ? <div className="mt-2 flex flex-wrap gap-2">{segment.warning_codes.map((item) => <Badge value={item} warning key={item} />)}</div> : null}</div>
}

function Connection({ connection }) {
  return <div className="mb-5 flex items-start gap-3 border-y border-slate-200 bg-slate-50 px-3 py-3"><Clock3 className="mt-0.5 h-4 w-4 text-slate-600" /><div><p className="font-semibold text-slate-800">{connection?.connection_minutes != null ? `${minutes(connection.connection_minutes)} connection` : "Connection time unknown"}</p><p className="mt-1 text-xs text-slate-500">{connection?.airport_change_required ? "Airport change requires manual review." : `At ${connection?.airport_code || "unknown airport"}`}{connection?.overnight ? " · Overnight" : ""}</p></div></div>
}

function ReferenceSection({ title: heading, items, empty, render }) {
  return <section><div className="flex justify-between"><h3 className="text-lg font-semibold text-slate-950">{heading}</h3><span className="text-sm text-slate-500">{items.length}</span></div><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{items.length ? items.map((item) => <div className="py-4" key={item.id}>{render(item)}</div>) : <p className="py-4 text-sm text-slate-500">{empty}</p>}</div></section>
}

function Metric({ label, value, warning }) { return <div className={`rounded-md border p-4 ${warning ? "border-amber-200 bg-amber-50" : "border-slate-200 bg-white"}`}><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div> }
function Info({ label, value }) { return <div><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-1 font-semibold text-slate-900">{value || "Unknown"}</p></div> }
function Badge({ value, warning }) { return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${warning ? "bg-amber-50 text-amber-800 ring-amber-200" : "bg-blue-50 text-blue-700 ring-blue-200"}`}>{title(value)}</span> }
function yesNo(value) { return value ? "required" : "not indicated" }
function title(value) { return String(value || "Unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) }
function dateText(value) { return value ? new Date(`${String(value).slice(0, 10)}T00:00:00`).toLocaleDateString() : "Unknown" }
function dateTime(value) { return value ? new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "Schedule unknown" }
function minutes(value) { if (value == null) return "Unknown"; const hours = Math.floor(value / 60); const minutesPart = value % 60; return hours ? `${hours}h ${minutesPart}m` : `${minutesPart}m` }
