import { useEffect, useMemo, useState } from "react"
import ArrowRight from "lucide-react/dist/esm/icons/arrow-right.js"
import Check from "lucide-react/dist/esm/icons/check.js"
import ClipboardCheck from "lucide-react/dist/esm/icons/clipboard-check.js"
import Eye from "lucide-react/dist/esm/icons/eye.js"
import FileStack from "lucide-react/dist/esm/icons/files.js"
import GitCompareArrows from "lucide-react/dist/esm/icons/git-compare-arrows.js"
import History from "lucide-react/dist/esm/icons/history.js"
import Plane from "lucide-react/dist/esm/icons/plane.js"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import Save from "lucide-react/dist/esm/icons/save.js"
import Send from "lucide-react/dist/esm/icons/send.js"
import ShieldAlert from "lucide-react/dist/esm/icons/shield-alert.js"
import Star from "lucide-react/dist/esm/icons/star.js"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { loadCurrentAgency } from "../../lib/agency"
import { apiGet, apiPost, apiPut } from "../../lib/api"

// Internal compatibility label: Client-safe preview.

const steps = ["Source", "Generate", "Itineraries", "Fare brands", "Suitability", "Wording", "Preview", "Preference", "Snapshot", "Review", "Next step"]

export default function JourneyComparisonPresentationWorkspacePage() {
  const query = useMemo(() => new URLSearchParams(window.location.search), [])
  const [state, setState] = useState(null)
  const [presentations, setPresentations] = useState([])
  const [selectedId, setSelectedId] = useState("")
  const [detail, setDetail] = useState(null)
  const [sourceType, setSourceType] = useState(query.get("composition_id") ? "composition" : query.get("offer_id") ? "offer" : query.get("journey_id") ? "journey" : "composition")
  const [sourceId, setSourceId] = useState(query.get("composition_id") || query.get("offer_id") || query.get("journey_id") || "")
  const [tab, setTab] = useState(query.get("view") === "client-preview" ? "client-preview" : "comparison")
  const [preview, setPreview] = useState(null)
  const [preferredReason, setPreferredReason] = useState("")
  const [wording, setWording] = useState({ client_title: "", client_intro_text: "", internal_notes: "" })
  const [handoff, setHandoff] = useState({ destination_type: "offer_workspace", destination_id: "" })
  const [handoffPreview, setHandoffPreview] = useState(null)
  const [notice, setNotice] = useState("")
  const [error, setError] = useState("")

  async function load(preferredId = selectedId) {
    const context = state || await loadCurrentAgency()
    const response = await apiGet(`/api/agencies/${context.agency.id}/journey-comparison-presentations?include_archived=true`)
    const queryId = query.get("presentation_id")
    const compositionId = query.get("composition_id")
    const match = compositionId ? response.items?.find((item) => item.composition_id === compositionId && !item.archived_at) : null
    const nextId = preferredId || queryId || match?.id || response.items?.find((item) => !item.archived_at)?.id || ""
    setState(context)
    setPresentations(response.items || [])
    setSelectedId(nextId)
    if (nextId) await loadDetail(context.agency.id, nextId)
    else setDetail(null)
  }

  async function loadDetail(agencyId, presentationId) {
    const response = await apiGet(`/api/agencies/${agencyId}/journey-comparison-presentations/${presentationId}`)
    setDetail(response)
    setWording({
      client_title: response.presentation.client_title || response.presentation.title || "",
      client_intro_text: response.presentation.client_intro_text || "",
      internal_notes: response.presentation.internal_notes || "",
    })
    setHandoff((current) => ({ ...current, destination_id: current.destination_id || response.presentation.offer_id || "" }))
    if (query.get("view") === "client-preview") {
      const previewResponse = await apiGet(`/api/agencies/${agencyId}/journey-comparison-presentations/${presentationId}/preview/client`)
      setPreview(previewResponse.client_safe_payload)
      setTab("client-preview")
    }
  }

  useEffect(() => { load().catch(fail(setError)) }, [])

  async function refresh() { await load(selectedId) }

  async function createFromSource() {
    if (!sourceId.trim()) throw new Error("Enter a source record ID.")
    const response = await apiPost(`/api/agencies/${state.agency.id}/journey-comparison-presentations/from-${sourceType}/${sourceId.trim()}`, {})
    const id = response.presentation.id
    setNotice("Offer comparison created from canonical itinerary options.")
    setSelectedId(id)
    await load(id)
  }

  async function action(path, body = {}) {
    const response = await apiPost(`${base()}${path}`, body)
    await refresh()
    return response
  }

  async function generate() { await action("/generate"); setNotice("Offer comparison refreshed from its approved source. Unknowns remain explicit.") }
  async function compare() { await action("/compare"); setNotice("Deterministic leaders and ties recalculated. No preferred option was selected automatically.") }

  async function saveWording() {
    await apiPut(base(), wording)
    setNotice("Client wording and internal notes saved in separate fields.")
    await refresh()
  }

  async function selectPreferred(optionId) {
    if (!preferredReason.trim()) throw new Error("Record the agent reason before choosing a preferred option.")
    await apiPut(`${base()}/preferred-option`, { option_id: optionId, reason: preferredReason.trim() })
    setPreferredReason("")
    setNotice("Preferred option recorded as an explicit agent decision, separate from system dimension leaders.")
    await refresh()
  }

  async function showPreview(mode) {
    const response = await apiGet(`${base()}/preview/${mode}`)
    setPreview(response.client_safe_payload || response.internal_payload)
    setTab(mode === "client" ? "client-preview" : "internal-preview")
  }

  async function snapshot() {
    const response = await action("/snapshots", { finalize: true })
    setNotice(`Immutable snapshot v${response.snapshot.version_number} finalized.`)
  }

  async function approve() {
    const snapshotId = detail.snapshots?.find((item) => item.finalized)?.id || detail.snapshots?.[0]?.id
    if (!snapshotId) throw new Error("Create a snapshot before review.")
    await action("/reviews", { snapshot_id: snapshotId, review_status: "approved", client_content_approved: true, pricing_approved: true, schedule_approved: true, service_assessment_approved: true, warnings_acknowledged: true })
    setNotice("Review approval recorded. Nothing was published or sent.")
  }

  async function prepareHandoff() {
    const response = await apiPost(`${base()}/handoff/preview`, clean(handoff))
    setHandoffPreview(response)
    setNotice("Next-step review prepared. No destination was modified.")
  }

  async function applyHandoff() {
    const response = await action("/handoff/apply", clean(handoff))
    setHandoffPreview(response)
    setNotice("Next-step link recorded. No offer publication, document rendering, messaging, or provider action occurred.")
  }

  function base() { return `/api/agencies/${state.agency.id}/journey-comparison-presentations/${selectedId}` }

  const presentation = detail?.presentation
  const comparison = detail?.comparison_results?.[0]
  const options = detail?.options || []
  const deliveryHref = presentation?.offer_id
    ? `/agency/offers/${encodeURIComponent(presentation.offer_id)}?section=delivery&presentation_id=${encodeURIComponent(selectedId)}`
    : "/agency/offers"

  return <AgencyLayout user={state?.me?.user} agency={state?.agency}>
    <ProtectedRoute loading={!state && !error} error={error}>
      <div className="space-y-6">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div><p className="text-sm font-semibold uppercase text-blue-700">Client Presentation</p><h1 className="mt-2 text-2xl font-semibold text-slate-950">Offer Comparison</h1><p className="mt-1 max-w-4xl text-sm text-slate-600">Turn canonical itinerary options into clear, reviewable offer comparisons. This workspace does not retrieve fares or availability, publish offers, create public links, send messages, or execute providers.</p></div>
          <div className="flex items-center gap-2"><a className="secondary-button" href={deliveryHref}><Send className="h-4 w-4" />Open Delivery & Responses</a><button type="button" title="Refresh workspace" onClick={() => refresh().catch(fail(setError))} className="icon-button"><RefreshCw className="h-4 w-4" /></button></div>
        </header>

        {notice ? <div className="border-y border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</div> : null}
        {error ? <div className="border-y border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

        <section className="grid gap-3 md:grid-cols-[190px_minmax(0,1fr)_auto]"><select className="field" value={sourceType} onChange={(event) => setSourceType(event.target.value)}><option value="composition">Itinerary option set</option><option value="journey">Itinerary</option><option value="offer">Offer Workspace</option></select><input className="field" value={sourceId} onChange={(event) => setSourceId(event.target.value)} placeholder={`${title(sourceType)} ID`} /><button type="button" onClick={() => createFromSource().catch(fail(setError))} className="primary-button"><Plus className="h-4 w-4" />Create presentation</button></section>

        <div className="overflow-x-auto border-y border-slate-200 py-3"><ol className="flex min-w-max items-center gap-2">{steps.map((step, index) => <li key={step} className="flex items-center gap-2"><span className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${index < progress(presentation, detail) ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600"}`}>{index + 1}</span><span className="text-xs font-semibold text-slate-700">{step}</span>{index < steps.length - 1 ? <ArrowRight className="h-3.5 w-3.5 text-slate-300" /> : null}</li>)}</ol></div>

        <div className="grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]">
          <aside><div className="flex items-center justify-between"><h2 className="font-semibold text-slate-950">Offer comparisons</h2><span className="text-sm text-slate-500">{presentations.length}</span></div><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{presentations.map((item) => <button key={item.id} type="button" onClick={() => { setSelectedId(item.id); loadDetail(state.agency.id, item.id).catch(fail(setError)) }} className={`block w-full px-2 py-3 text-left ${item.id === selectedId ? "bg-blue-50" : "hover:bg-slate-50"}`}><p className="font-semibold text-slate-950">{item.client_title || item.title}</p><p className="mt-1 text-xs text-slate-500">{title(item.status)} · {item.currency_code}</p></button>)}</div></aside>

          {presentation ? <main className="min-w-0 space-y-7">
            <section className="border-b border-slate-200 pb-5"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase text-slate-500">{title(presentation.status)} · {presentation.audience_type}</p><h2 className="mt-1 text-xl font-semibold text-slate-950">{presentation.client_title || presentation.title}</h2><p className="mt-2 text-sm text-slate-600">Itinerary option set {shortId(presentation.composition_id)} · {options.length} options · {detail.fare_brands?.length || 0} fare brands</p></div><div className="flex flex-wrap gap-2"><button type="button" onClick={() => generate().catch(fail(setError))} className="secondary-button"><RefreshCw className="h-4 w-4" />Generate</button><button type="button" onClick={() => compare().catch(fail(setError))} className="primary-button"><GitCompareArrows className="h-4 w-4" />Compare</button></div></div></section>

            <nav className="flex flex-wrap gap-2" aria-label="Presentation workspace views">{[["comparison", "Comparison"], ["wording", "Wording"], ["client-preview", "Client preview"], ["internal-preview", "Internal preview"], ["review", "Review & next step"]].map(([value, label]) => <button type="button" key={value} onClick={() => value === "client-preview" ? showPreview("client").catch(fail(setError)) : value === "internal-preview" ? showPreview("internal").catch(fail(setError)) : setTab(value)} className={tab === value ? "primary-button" : "secondary-button"}>{label}</button>)}</nav>

            {tab === "comparison" ? <>
              <section className="grid gap-4 lg:grid-cols-3">{options.map((option) => <OptionCard key={option.id} option={option} fares={(detail.fare_brands || []).filter((item) => item.option_projection_id === option.id)} segments={(detail.segments || []).filter((item) => item.option_projection_id === option.id)} connections={(detail.connections || []).filter((item) => item.option_projection_id === option.id)} services={(detail.service_suitability || []).filter((item) => item.option_projection_id === option.id)} leader={leaderLabels(comparison, option.id)} reason={preferredReason} setReason={setPreferredReason} onPreferred={(id) => selectPreferred(id).catch(fail(setError))} />)}</section>
              {!options.length ? <EmptyState title="No comparison options" body="Generate this presentation from its itinerary option set." /> : null}
              <ComparisonMatrix comparison={comparison} options={options} />
            </> : null}

            {tab === "wording" ? <section><div className="flex items-center gap-2"><Save className="h-5 w-5 text-blue-700" /><h3 className="text-lg font-semibold text-slate-950">Client wording and visibility</h3></div><p className="mt-1 text-sm text-slate-600">Client-safe copy remains separate from agent notes and evidence.</p><div className="mt-4 grid gap-3"><input className="field" value={wording.client_title} onChange={(event) => setWording({ ...wording, client_title: event.target.value })} placeholder="Client title" /><textarea className="field min-h-28" value={wording.client_intro_text} onChange={(event) => setWording({ ...wording, client_intro_text: event.target.value })} placeholder="Client introduction" /><textarea className="field min-h-28" value={wording.internal_notes} onChange={(event) => setWording({ ...wording, internal_notes: event.target.value })} placeholder="Internal agent notes (never included in client preview)" /><button type="button" onClick={() => saveWording().catch(fail(setError))} className="primary-button w-fit"><Save className="h-4 w-4" />Save wording</button></div></section> : null}

            {tab === "client-preview" ? <Preview payload={preview} client /> : null}
            {tab === "internal-preview" ? <Preview payload={preview} /> : null}

            {tab === "review" ? <section className="space-y-6"><div><h3 className="text-lg font-semibold text-slate-950">Review and release preparation</h3><p className="mt-1 text-sm text-slate-600">Protect an offer comparison version, record explicit approval, then prepare a controlled Offer or Document next step.</p></div><div className="grid gap-3 sm:grid-cols-3"><Action icon={History} label="Finalize snapshot" detail={`${detail.snapshots?.length || 0} versions`} onClick={() => snapshot().catch(fail(setError))} /><Action icon={ClipboardCheck} label="Approve review" detail={`${detail.reviews?.length || 0} reviews`} onClick={() => approve().catch(fail(setError))} /><Action icon={Eye} label="Open client preview" detail="Restricted content removed" onClick={() => showPreview("client").catch(fail(setError))} /></div><div className="border-y border-slate-200 py-5"><h4 className="font-semibold text-slate-950">Next workspace</h4><div className="mt-3 grid gap-3 md:grid-cols-[220px_minmax(0,1fr)_auto]"><select className="field" value={handoff.destination_type} onChange={(event) => setHandoff({ ...handoff, destination_type: event.target.value })}><option value="offer_workspace">Offer Workspace</option><option value="document_workspace">Document Workspace</option></select><input className="field" value={handoff.destination_id} onChange={(event) => setHandoff({ ...handoff, destination_id: event.target.value })} placeholder="Existing destination ID (optional for preview)" /><button type="button" onClick={() => prepareHandoff().catch(fail(setError))} className="secondary-button"><Send className="h-4 w-4" />Preview</button></div>{handoffPreview ? <div className="mt-4 bg-slate-50 p-4 text-sm"><p className="font-semibold text-slate-900">Integrity reference {shortId(handoffPreview.preview?.payload_hash || handoffPreview.handoff?.payload_hash)}</p><p className="mt-1 text-slate-600">No publication, rendering, sending, acceptance, booking, ticketing, EMD, or provider action is included.</p>{handoffPreview.can_apply ? <button type="button" onClick={() => applyHandoff().catch(fail(setError))} className="primary-button mt-3">Record next step</button> : null}</div> : null}</div></section> : null}
          </main> : <EmptyState title="No presentation selected" body="Open an itinerary option set to begin the client presentation workflow." />}
        </div>
      </div>
    </ProtectedRoute>
  </AgencyLayout>
}

function OptionCard({ option, fares, segments, connections, services, leader, reason, setReason, onPreferred }) {
  return <article className={`rounded-md border bg-white p-4 ${option.is_preferred ? "border-blue-500 ring-1 ring-blue-200" : "border-slate-200"}`}><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase text-blue-700">{option.option_label}</p><h3 className="mt-1 text-lg font-semibold text-slate-950">{option.origin || "Unknown"} <ArrowRight className="inline h-4 w-4" /> {option.destination || "Unknown"}</h3><p className="mt-1 text-sm text-slate-600">{option.carrier_summary || "Carrier unknown"}</p></div>{option.is_preferred ? <span className="rounded-full bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700"><Star className="mr-1 inline h-3 w-3" />Preferred</span> : null}</div>{leader.length ? <div className="mt-3 flex flex-wrap gap-1">{leader.map((item) => <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700" key={item}>{item}</span>)}</div> : null}<dl className="mt-4 grid grid-cols-2 gap-3 text-sm"><Value label="Departure" value={dateTime(option.departure_at)} /><Value label="Arrival" value={dateTime(option.arrival_at)} /><Value label="Total travel" value={duration(option.total_elapsed_minutes)} /><Value label="Flight time" value={duration(option.total_flight_minutes)} /><Value label="Stops" value={option.stop_count} /><Value label="Connections" value={duration(option.total_connection_minutes)} /></dl><div className="mt-4 flex flex-wrap gap-2"><Status value={`${option.unknown_value_count} unknown`} warning={option.unknown_value_count > 0} /><Status value={`${option.review_required_count} review`} warning={option.review_required_count > 0} /><Status value={`${option.blocking_warning_count} blockers`} danger={option.blocking_warning_count > 0} /></div><details className="mt-4 border-t border-slate-100 pt-3"><summary className="cursor-pointer text-sm font-semibold text-slate-800">Segments and connections</summary><div className="mt-3 space-y-3">{segments.map((segment) => <div key={segment.id} className="text-sm"><p className="font-semibold">{segment.marketing_carrier || "?"} {segment.flight_number || ""} · {segment.origin_airport_code || "???"} to {segment.destination_airport_code || "???"}</p><p className="text-slate-500">{dateTime(segment.departure_at)} · {segment.client_operated_by_text || "Operating carrier unknown"}</p></div>)}{connections.map((connection) => <p key={connection.id} className="text-sm text-amber-800">{connection.client_connection_text || `${duration(connection.connection_minutes)} connection`} · MCT {title(connection.minimum_connection_status)}</p>)}</div></details><details className="mt-3 border-t border-slate-100 pt-3"><summary className="cursor-pointer text-sm font-semibold text-slate-800">Fare brands ({fares.length})</summary><div className="mt-3 space-y-2">{fares.map((fare) => <div className="rounded-md bg-slate-50 p-3" key={fare.id}><div className="flex justify-between gap-3"><p className="font-semibold text-slate-900">{fare.client_brand_name}</p><p className="font-semibold text-slate-950">{money(fare.grand_total, fare.currency_code)}</p></div><p className="mt-1 text-xs text-slate-600">Baggage: {fare.baggage_summary || "Unknown"} · Change: {fare.change_summary || "Unknown"} · Refund: {fare.refund_summary || "Unknown"}</p>{fare.price_difference_from_lowest ? <p className="mt-1 text-xs text-slate-500">+{money(fare.price_difference_from_lowest, fare.currency_code)} from lowest</p> : null}</div>)}</div></details><details className="mt-3 border-t border-slate-100 pt-3"><summary className="cursor-pointer text-sm font-semibold text-slate-800">Service suitability ({services.length})</summary><div className="mt-3 space-y-2">{services.map((service) => <div key={service.id} className="text-sm"><p className="font-semibold">{service.service_name} · {title(service.suitability_status)}</p><p className="text-slate-600">{service.client_safe_summary}</p></div>)}{!services.length ? <p className="text-sm text-slate-500">Not assessed</p> : null}</div></details>{!option.is_preferred ? <div className="mt-4 border-t border-slate-100 pt-3"><input className="field" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Agent selection reason" /><button type="button" onClick={() => onPreferred(option.id)} className="secondary-button mt-2 w-full"><Star className="h-4 w-4" />Select explicitly</button></div> : null}</article>
}

function ComparisonMatrix({ comparison, options }) { if (!comparison) return <section className="border-y border-slate-200 py-4 text-sm text-slate-500">Generate a comparison to see dimension leaders, ties, and unresolved unknowns.</section>; return <section><h3 className="text-lg font-semibold text-slate-950">Comparison dimensions</h3><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left"><tr><th className="px-3 py-3">Dimension</th>{options.map((option) => <th className="px-3 py-3" key={option.id}>{option.option_label}</th>)}</tr></thead><tbody className="divide-y divide-slate-100">{(comparison.dimension_results || []).filter((item) => !item.internal_only).map((item) => <tr key={item.dimension_code}><th className="px-3 py-3 text-left font-semibold">{item.client_label || title(item.dimension_code)}</th>{options.map((option) => <td className="px-3 py-3" key={option.id}>{item.leader_option_ids?.includes(option.id) ? <span className="font-semibold text-emerald-700">Leader</span> : item.unknown_option_ids?.includes(option.id) ? <span className="font-semibold text-amber-700">Unknown</span> : "—"}</td>)}</tr>)}</tbody></table></div></section> }
function Preview({ payload, client = false }) { return <section><div className="flex items-center gap-2">{client ? <Eye className="h-5 w-5 text-blue-700" /> : <ShieldAlert className="h-5 w-5 text-amber-700" />}<h3 className="text-lg font-semibold text-slate-950">{client ? "Client Preview" : "Authorized Technical Preview"}</h3></div><p className="mt-1 text-sm text-slate-600">{client ? "Evidence IDs, source URLs, internal notes, supplier instructions, and restricted commercial details are removed." : "Operational provenance and internal review context stay here and never flow into the client view."}</p>{payload ? <pre className="mt-4 max-h-[620px] overflow-auto whitespace-pre-wrap bg-slate-50 p-4 text-xs text-slate-700">{JSON.stringify(payload, null, 2)}</pre> : <p className="mt-4 text-sm text-slate-500">Open this preview to load its current view.</p>}</section> }
function Action({ icon: Icon, label, detail, onClick }) { return <button type="button" onClick={onClick} className="rounded-md border border-slate-200 bg-white p-4 text-left hover:border-blue-300"><Icon className="h-5 w-5 text-blue-700" /><p className="mt-3 font-semibold text-slate-950">{label}</p><p className="mt-1 text-xs text-slate-500">{detail}</p></button> }
function Value({ label, value }) { return <div><dt className="text-xs font-semibold uppercase text-slate-500">{label}</dt><dd className="mt-1 font-semibold text-slate-900">{value ?? "Unknown"}</dd></div> }
function Status({ value, warning, danger }) { return <span className={`rounded-full px-2 py-1 text-xs font-semibold ${danger ? "bg-red-50 text-red-700" : warning ? "bg-amber-50 text-amber-700" : "bg-slate-100 text-slate-600"}`}>{value}</span> }
function leaderLabels(result, optionId) { if (!result) return []; const labels = [["lowest_price_option_id", "Lowest price"], ["fastest_option_id", "Fastest"], ["shortest_flight_time_option_id", "Shortest flight"], ["fewest_stops_option_id", "Fewest stops"], ["best_baggage_option_id", "Baggage leader"], ["best_flexibility_option_id", "Flexibility leader"], ["best_special_service_option_id", "Service suitability leader"], ["lowest_operational_risk_option_id", "Lowest identified risk"]]; return labels.filter(([key]) => result[key] === optionId).map(([, label]) => label) }
function progress(presentation, detail) { if (!presentation) return 0; if (detail?.handoffs?.length) return 11; if (detail?.reviews?.some((item) => item.review_status === "approved")) return 10; if (detail?.snapshots?.length) return 9; if (presentation.preferred_selected_by) return 8; if (detail?.comparison_results?.length) return 7; if (detail?.options?.length) return 3; return 1 }
function duration(minutes) { if (minutes === null || minutes === undefined) return "Unknown"; return `${Math.floor(minutes / 60)}h ${minutes % 60}m` }
function dateTime(value) { return value ? new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "Unknown" }
function money(value, currency = "EUR") { return value === null || value === undefined ? "Unknown" : new Intl.NumberFormat(undefined, { style: "currency", currency: currency || "EUR" }).format(value) }
function shortId(value) { return value ? String(value).slice(0, 12) : "Not linked" }
function title(value) { return String(value || "Unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) }
function clean(value) { return Object.fromEntries(Object.entries(value).filter(([, item]) => item !== "" && item !== null && item !== undefined)) }
function fail(setError) { return (err) => setError(err.message || String(err)) }
