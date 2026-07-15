import { useEffect, useMemo, useState } from "react"
import Archive from "lucide-react/dist/esm/icons/archive.js"
import ArrowDown from "lucide-react/dist/esm/icons/arrow-down.js"
import ArrowRight from "lucide-react/dist/esm/icons/arrow-right.js"
import ArrowUp from "lucide-react/dist/esm/icons/arrow-up.js"
import Braces from "lucide-react/dist/esm/icons/braces.js"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import ClipboardPaste from "lucide-react/dist/esm/icons/clipboard-paste.js"
import Copy from "lucide-react/dist/esm/icons/copy.js"
import Eye from "lucide-react/dist/esm/icons/eye.js"
import GitBranch from "lucide-react/dist/esm/icons/git-branch.js"
import Plane from "lucide-react/dist/esm/icons/plane.js"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import Save from "lucide-react/dist/esm/icons/save.js"
import ShieldAlert from "lucide-react/dist/esm/icons/shield-alert.js"
import Sparkles from "lucide-react/dist/esm/icons/sparkles.js"
import Undo2 from "lucide-react/dist/esm/icons/undo-2.js"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const emptyFlight = {
  marketing_carrier_code: "", marketing_flight_number: "", operating_carrier_code: "",
  departure_airport_code: "", departure_local_datetime: "", departure_timezone: "",
  arrival_airport_code: "", arrival_local_datetime: "", arrival_timezone: "",
  departure_terminal: "", arrival_terminal: "", cabin: "", booking_class: "",
  fare_family_code: "", equipment_code: "", status_code: "", notes: "",
}

export default function JourneyAuthoringWorkspacePage() {
  const [state, setState] = useState(null)
  const [sessions, setSessions] = useState([])
  const [detail, setDetail] = useState(null)
  const [selectedId, setSelectedId] = useState("")
  const [paste, setPaste] = useState({ raw_text: "", source_type: "gds_cryptic", source_label: "", default_year: "" })
  const [flight, setFlight] = useState(emptyFlight)
  const [selectedSegments, setSelectedSegments] = useState([])
  const [bulkCabin, setBulkCabin] = useState("")
  const [preview, setPreview] = useState(null)
  const [applySettings, setApplySettings] = useState({ application_mode: "create_new_journey", journey_id: "", option_id: "" })
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const query = useMemo(() => new URLSearchParams(window.location.search), [])

  async function load(preferredId = selectedId) {
    const context = await loadCurrentAgency()
    const response = await apiGet(`/api/agencies/${context.agency.id}/journey-authoring?include_archived=true`)
    const querySession = query.get("session_id")
    const nextId = preferredId || querySession || response.items?.find((item) => item.status !== "archived")?.id || response.items?.[0]?.id || ""
    setState(context)
    setSessions(response.items || [])
    setSelectedId(nextId)
    if (nextId) setDetail(await apiGet(`/api/agencies/${context.agency.id}/journey-authoring/${nextId}`))
    else setDetail(null)
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  async function refreshDetail() {
    if (!selectedId) return load()
    const next = await apiGet(`/api/agencies/${state.agency.id}/journey-authoring/${selectedId}`)
    setDetail(next)
    const response = await apiGet(`/api/agencies/${state.agency.id}/journey-authoring?include_archived=true`)
    setSessions(response.items || [])
  }

  async function createSession() {
    const source = {
      trip_id: query.get("trip_id") || undefined,
      offer_id: query.get("offer_id") || undefined,
      booking_id: query.get("booking_id") || undefined,
      journey_id: query.get("journey_id") || undefined,
      parser_run_id: query.get("parser_run_id") || undefined,
      booking_import_draft_id: query.get("booking_import_draft_id") || undefined,
    }
    const response = await apiPost(`/api/agencies/${state.agency.id}/journey-authoring`, { title: "New itinerary authoring session", ...source })
    if (source.parser_run_id) await apiPost(`/api/agencies/${state.agency.id}/journey-authoring/${response.session.id}/import-parser-run`, { parser_run_id: source.parser_run_id })
    if (source.booking_import_draft_id) await apiPost(`/api/agencies/${state.agency.id}/journey-authoring/${response.session.id}/import-booking-draft`, { booking_import_draft_id: source.booking_import_draft_id })
    setNotice("Authoring session created. No production Journey record has been changed.")
    setSelectedSegments([])
    setPreview(null)
    await load(response.session.id)
  }

  async function selectSession(id) {
    setSelectedId(id)
    setSelectedSegments([])
    setPreview(null)
    setDetail(await apiGet(`/api/agencies/${state.agency.id}/journey-authoring/${id}`))
  }

  async function importText() {
    const payload = { ...paste, default_year: paste.default_year ? Number(paste.default_year) : undefined }
    const response = await apiPost(`/api/agencies/${state.agency.id}/journey-authoring/${selectedId}/import-text`, payload)
    setNotice(`${response.created_segments?.length || 0} segment drafts prepared. ${response.unparsed_lines?.length || 0} unresolved lines remain preserved.`)
    setPaste({ ...paste, raw_text: "" })
    await refreshDetail()
  }

  async function addFlight(payload = flight) {
    await apiPost(`/api/agencies/${state.agency.id}/journey-authoring/${selectedId}/segments`, clean(payload))
    setNotice("Flight draft saved. Missing information remains visible for review.")
    setFlight(emptyFlight)
    await refreshDetail()
  }

  async function saveSegment(segment, updates) {
    await apiPut(`/api/agencies/${state.agency.id}/journey-authoring/${selectedId}/segments/${segment.id}`, updates)
    setNotice("Segment saved with correction history and agent-confirmed provenance.")
    await refreshDetail()
  }

  async function archiveSegment(segmentId) {
    await apiPost(`/api/agencies/${state.agency.id}/journey-authoring/${selectedId}/segments/${segmentId}/archive`, {})
    await refreshDetail()
  }

  async function restoreSegment(segmentId) {
    await apiPost(`/api/agencies/${state.agency.id}/journey-authoring/${selectedId}/segments/${segmentId}/restore`, {})
    await refreshDetail()
  }

  async function duplicateSegment(segment) {
    const payload = Object.fromEntries(Object.keys(emptyFlight).map((key) => [key, segment[key] ?? ""]))
    payload.option_group_key = segment.option_group_key
    payload.leg_group_key = segment.leg_group_key
    await addFlight(payload)
  }

  async function moveSegment(segmentId, direction) {
    const active = (detail.segments || []).filter((item) => item.active !== false).sort((a, b) => a.sequence - b.sequence)
    const index = active.findIndex((item) => item.id === segmentId)
    const target = index + direction
    if (index < 0 || target < 0 || target >= active.length) return
    const ids = active.map((item) => item.id)
    ;[ids[index], ids[target]] = [ids[target], ids[index]]
    await apiPost(`/api/agencies/${state.agency.id}/journey-authoring/${selectedId}/segments/reorder`, { segment_ids: ids })
    await refreshDetail()
  }

  async function validate() {
    const response = await apiPost(`/api/agencies/${state.agency.id}/journey-authoring/${selectedId}/validate`, {})
    setNotice(response.summary.blocking ? `${response.summary.blocking} blocking findings require correction.` : "Validation complete. Completeness is not operational approval.")
    await refreshDetail()
  }

  async function enrich() {
    const response = await apiPost(`/api/agencies/${state.agency.id}/journey-authoring/${selectedId}/enrich`, {})
    setNotice(`${response.count} segments enriched from governed internal reference data. No external lookup ran.`)
    await refreshDetail()
  }

  async function bulkUpdate() {
    await apiPost(`/api/agencies/${state.agency.id}/journey-authoring/${selectedId}/segments/bulk-update`, { segment_ids: selectedSegments, updates: { cabin: bulkCabin } })
    setNotice(`${selectedSegments.length} segments updated.`)
    setSelectedSegments([])
    await refreshDetail()
  }

  async function previewApplication() {
    const response = await apiPost(`/api/agencies/${state.agency.id}/journey-authoring/${selectedId}/preview-application`, clean(applySettings))
    setPreview(response)
    await refreshDetail()
  }

  async function applyJourney() {
    const response = await apiPost(`/api/agencies/${state.agency.id}/journey-authoring/${selectedId}/apply-to-journey`, clean(applySettings))
    setNotice(`Applied through the canonical Journey service. ${response.created_record_ids?.length || 0} projection records created; no snapshot was published.`)
    setPreview(null)
    await refreshDetail()
  }

  const session = detail?.session
  const activeSegments = (detail?.segments || []).filter((item) => item.active !== false).sort((a, b) => a.sequence - b.sequence)
  const archivedSegments = (detail?.segments || []).filter((item) => item.active === false)
  const activeValidations = (detail?.validations || []).filter((item) => !item.resolved_at && !item.superseded_at)
  const connections = connectionPreview(activeSegments)

  return <AgencyLayout user={state?.me?.user} agency={state?.agency}>
    <ProtectedRoute loading={!state && !error} error={error}>
      <div className="space-y-6">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div><p className="text-sm font-semibold uppercase text-blue-700">Journey Engine</p><h1 className="mt-2 text-2xl font-semibold text-slate-950">Journey Authoring</h1><p className="mt-1 max-w-4xl text-sm text-slate-600">Build accurate itinerary drafts from pasted, parser, booking-import, existing Journey, or manual data. Raw source text is preserved; unknown values stay unknown; application is explicit.</p></div>
          <div className="flex gap-2"><button type="button" title="New authoring session" onClick={() => createSession().catch(fail(setError))} className="icon-button"><Plus className="h-4 w-4" /></button><button type="button" title="Refresh" onClick={() => refreshDetail().catch(fail(setError))} className="icon-button"><RefreshCw className="h-4 w-4" /></button></div>
        </header>

        <div className="border-y border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900"><strong>Governed preparation workspace.</strong> Validation and completeness do not approve an itinerary. This page does not search schedules, price, book, ticket, call providers, use AI, or publish client snapshots.</div>
        {notice ? <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</div> : null}
        {error ? <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

        <div className="grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]">
          <aside><div className="flex items-center justify-between"><h2 className="font-semibold text-slate-950">Working sessions</h2><span className="text-sm text-slate-500">{sessions.length}</span></div><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{sessions.map((item) => <button type="button" key={item.id} onClick={() => selectSession(item.id).catch(fail(setError))} className={`block w-full px-2 py-3 text-left ${item.id === selectedId ? "bg-blue-50" : "hover:bg-slate-50"}`}><p className="font-semibold text-slate-950">{item.title}</p><div className="mt-2 flex justify-between text-xs text-slate-500"><span>{title(item.status)}</span><span>{item.completeness_score || 0}%</span></div><p className="mt-1 text-xs text-slate-500">{item.blocking_errors_count || 0} blockers · {item.warnings_count || 0} warnings</p></button>)}</div></aside>

          {session ? <main className="min-w-0 space-y-7">
            <section className="border-b border-slate-200 pb-5"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase text-slate-500">{title(session.authoring_mode)} session</p><h2 className="mt-1 text-xl font-semibold text-slate-950">{session.title}</h2><p className="mt-2 text-sm text-slate-600">Last saved {dateTime(session.updated_at)}{session.journey_id ? " · Linked Journey ready" : " · Not yet linked to a Journey"}</p></div><Status value={session.status} /></div><div className="mt-4 grid gap-3 sm:grid-cols-4"><Metric label="Completeness" value={`${session.completeness_score || 0}%`} /><Metric label="Segments" value={activeSegments.length} /><Metric label="Blocking" value={session.blocking_errors_count || 0} danger /><Metric label="Warnings" value={session.warnings_count || 0} warning /></div></section>

            <section className="grid gap-6 lg:grid-cols-2">
              <div><div className="flex items-center gap-2"><ClipboardPaste className="h-4 w-4 text-blue-700" /><h3 className="font-semibold text-slate-950">Paste and normalize</h3></div><div className="mt-3 space-y-3"><textarea value={paste.raw_text} onChange={(event) => setPaste({ ...paste, raw_text: event.target.value })} rows="7" placeholder="Paste GDS, airline confirmation, email, website, or PDF-extracted itinerary text" className="field font-mono text-xs" /><div className="grid gap-2 sm:grid-cols-3"><Select value={paste.source_type} onChange={(value) => setPaste({ ...paste, source_type: value })} options={["gds_cryptic", "gds_graphical_text", "airline_confirmation", "agency_itinerary", "website_text", "email_text", "pdf_extracted_text", "other"]} /><input value={paste.source_label} onChange={(event) => setPaste({ ...paste, source_label: event.target.value })} placeholder="Source label" className="field" /><input value={paste.default_year} onChange={(event) => setPaste({ ...paste, default_year: event.target.value })} placeholder="Year, if known" inputMode="numeric" className="field" /></div><button type="button" disabled={!paste.raw_text.trim()} onClick={() => importText().catch(fail(setError))} className="primary-button"><Braces className="h-4 w-4" />Parse into editable drafts</button></div></div>
              <ManualFlight flight={flight} setFlight={setFlight} onAdd={() => addFlight().catch(fail(setError))} />
            </section>

            <details className="border-y border-slate-200 py-3"><summary className="cursor-pointer font-semibold text-slate-950">Preserved source material ({detail.sources?.length || 0})</summary><div className="mt-3 grid gap-4">{(detail.sources || []).map((source) => <div key={source.id} className="rounded-md border border-slate-200 bg-slate-50 p-4"><div className="flex flex-wrap justify-between gap-2"><div><p className="font-semibold text-slate-900">{source.source_label || title(source.source_type)}</p><p className="mt-1 text-xs text-slate-500">Imported {dateTime(source.imported_at)} · hash {source.source_hash?.slice(0, 12)}… · immutable raw source</p></div><button type="button" title="Copy preserved source" onClick={() => navigator.clipboard?.writeText(source.raw_text || "")} className="icon-button"><Copy className="h-4 w-4" /></button></div><pre className="mt-3 max-h-48 overflow-auto whitespace-pre-wrap text-xs text-slate-700">{source.raw_text || "No raw text was available from the linked source record."}</pre>{source.raw_payload?.unparsed_lines?.length ? <p className="mt-3 text-sm font-semibold text-amber-800">{source.raw_payload.unparsed_lines.length} unresolved lines preserved for manual review.</p> : null}</div>)}</div></details>

            <section><div className="flex flex-wrap items-end justify-between gap-3"><div><h3 className="text-lg font-semibold text-slate-950">Segment schedule</h3><p className="mt-1 text-sm text-slate-600">Edit airline schedule fields in local time. Timezones are explicit and local timestamps are never treated as UTC implicitly.</p></div><div className="flex flex-wrap gap-2"><button type="button" onClick={() => enrich().catch(fail(setError))} className="secondary-button"><Sparkles className="h-4 w-4" />Enrich internally</button><button type="button" onClick={() => validate().catch(fail(setError))} className="primary-button"><CheckCircle2 className="h-4 w-4" />Validate</button></div></div>
              {selectedSegments.length ? <div className="mt-3 flex flex-wrap items-center gap-2 border-y border-slate-200 bg-slate-50 px-3 py-2"><span className="text-sm font-semibold text-slate-700">{selectedSegments.length} selected</span><input value={bulkCabin} onChange={(event) => setBulkCabin(event.target.value)} placeholder="Cabin" className="field max-w-32" /><button type="button" disabled={!bulkCabin} onClick={() => bulkUpdate().catch(fail(setError))} className="secondary-button">Apply cabin</button></div> : null}
              {activeSegments.length ? <div className="mt-4 overflow-x-auto border-y border-slate-200"><table className="min-w-[1260px] w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-2 py-2"></th><th className="px-2 py-2">Seq</th><th className="px-2 py-2">Marketing flight</th><th className="px-2 py-2">Operating</th><th className="px-2 py-2">Departure</th><th className="px-2 py-2">Arrival</th><th className="px-2 py-2">Duration</th><th className="px-2 py-2">Cabin / RBD</th><th className="px-2 py-2">Review</th><th className="px-2 py-2">Actions</th></tr></thead><tbody className="divide-y divide-slate-200">{activeSegments.map((segment) => <SegmentRow key={segment.id} segment={segment} checked={selectedSegments.includes(segment.id)} onCheck={(checked) => setSelectedSegments(checked ? [...selectedSegments, segment.id] : selectedSegments.filter((id) => id !== segment.id))} onSave={saveSegment} onDuplicate={duplicateSegment} onArchive={archiveSegment} onMove={moveSegment} onError={setError} />)}</tbody></table></div> : <EmptyState title="No segment drafts" body="Paste itinerary text or add the first flight manually. Incomplete drafts are allowed." />}
              {archivedSegments.length ? <details className="mt-3"><summary className="cursor-pointer text-sm font-semibold text-slate-700">Archived drafts ({archivedSegments.length})</summary><div className="mt-2 divide-y divide-slate-200 border-y border-slate-200">{archivedSegments.map((item) => <div key={item.id} className="flex items-center justify-between py-2 text-sm"><span>{item.marketing_carrier_code || "Unknown"} {item.marketing_flight_number || ""} · {item.departure_airport_code || "???"} to {item.arrival_airport_code || "???"}</span><button type="button" title="Restore draft" onClick={() => restoreSegment(item.id).catch(fail(setError))} className="icon-button"><Undo2 className="h-4 w-4" /></button></div>)}</div></details> : null}
            </section>

            <section><h3 className="text-lg font-semibold text-slate-950">Journey timeline preview</h3><div className="mt-4 border-l-2 border-blue-200 pl-6">{activeSegments.map((segment, index) => <div key={segment.id}><div className="relative pb-5"><Plane className="absolute -left-[33px] h-4 w-4 bg-white text-blue-700" /><div className="flex flex-wrap items-baseline justify-between gap-3"><p className="font-semibold text-slate-950">{segment.marketing_carrier_code || "Carrier unknown"} {segment.marketing_flight_number || ""} · {segment.departure_airport_code || "???"} <ArrowRight className="mx-1 inline h-4 w-4" /> {segment.arrival_airport_code || "???"}</p><span className="text-sm text-slate-600">{duration(segment.scheduled_duration_minutes)}</span></div><p className="mt-1 text-sm text-slate-600">{localTime(segment.departure_local_datetime)} → {localTime(segment.arrival_local_datetime)} · {segment.cabin || "Cabin unknown"}/{segment.booking_class || "RBD unknown"}{segment.codeshare_indicator ? " · Codeshare review" : ""}{segment.overnight_indicator ? " · Date change" : ""}</p></div>{connections[index] ? <div className="mb-5 border-y border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">{connections[index].minutes == null ? "Connection time unresolved" : `${duration(connections[index].minutes)} connection`}{connections[index].gap ? " · Surface gap or airport change" : ""}</div> : null}</div>)}</div></section>

            <section className="grid gap-6 lg:grid-cols-2"><ValidationPanel validations={activeValidations} /><ProvenancePanel provenance={detail.provenance || []} corrections={detail.corrections || []} /></section>

            <section className="border-t border-slate-200 pt-5"><div className="flex items-center gap-2"><GitBranch className="h-5 w-5 text-blue-700" /><h3 className="text-lg font-semibold text-slate-950">Apply to canonical Journey</h3></div><p className="mt-1 text-sm text-slate-600">Preview first. Applying creates Phase 56.0 Journey projections with source links; finalized snapshots are immutable and no client snapshot is published.</p><div className="mt-4 grid gap-3 md:grid-cols-3"><Select value={applySettings.application_mode} onChange={(value) => setApplySettings({ ...applySettings, application_mode: value })} options={["create_new_journey", "create_new_option", "append_to_option", "replace_draft_option", "update_unfinalized_option"]} /><input value={applySettings.journey_id} onChange={(event) => setApplySettings({ ...applySettings, journey_id: event.target.value })} placeholder="Existing Journey ID when required" className="field" /><input value={applySettings.option_id} onChange={(event) => setApplySettings({ ...applySettings, option_id: event.target.value })} placeholder="Option ID when required" className="field" /></div><div className="mt-3 flex flex-wrap gap-2"><button type="button" onClick={() => previewApplication().catch(fail(setError))} className="secondary-button"><Eye className="h-4 w-4" />Preview Journey</button>{preview && !preview.blocking ? <button type="button" onClick={() => applyJourney().catch(fail(setError))} className="primary-button"><GitBranch className="h-4 w-4" />Apply to Journey</button> : null}{detail?.session?.journey_id ? <a href={`/agency/journey-option-composition?journey_id=${encodeURIComponent(detail.session.journey_id)}&authoring_session_id=${encodeURIComponent(detail.session.id)}`} className="secondary-button"><Sparkles className="h-4 w-4" />Compose itinerary options</a> : null}</div>{preview ? <div className={`mt-4 rounded-md border p-4 ${preview.blocking ? "border-red-200 bg-red-50" : "border-emerald-200 bg-emerald-50"}`}><p className="font-semibold text-slate-950">{preview.blocking ? "Application blocked" : "Ready for explicit application"}</p><p className="mt-1 text-sm text-slate-700">{preview.segment_count} segments · {preview.connections?.length || 0} calculated connections · {preview.validation_summary?.blocking || 0} blockers. {preview.target_reason || "Source references will be retained."}</p></div> : null}</section>
          </main> : <EmptyState title="Start an authoring session" body="Create a session to paste, import, normalize, validate, and explicitly apply itinerary segments." />}
        </div>
      </div>
    </ProtectedRoute>
  </AgencyLayout>
}

function ManualFlight({ flight, setFlight, onAdd }) {
  const field = (key, placeholder, type = "text") => <input type={type} value={flight[key]} onChange={(event) => setFlight({ ...flight, [key]: event.target.value })} placeholder={placeholder} className="field" />
  return <div><div className="flex items-center gap-2"><Plane className="h-4 w-4 text-blue-700" /><h3 className="font-semibold text-slate-950">Add flight manually</h3></div><div className="mt-3 grid gap-2 sm:grid-cols-2"><div className="grid grid-cols-[90px_1fr] gap-2">{field("marketing_carrier_code", "Airline")}{field("marketing_flight_number", "Flight")}</div>{field("operating_carrier_code", "Operating airline, if known")}<div className="grid grid-cols-[90px_1fr] gap-2">{field("departure_airport_code", "Origin")}{field("departure_local_datetime", "Departure local", "datetime-local")}</div>{field("departure_timezone", "Departure IANA timezone")}<div className="grid grid-cols-[90px_1fr] gap-2">{field("arrival_airport_code", "Destination")}{field("arrival_local_datetime", "Arrival local", "datetime-local")}</div>{field("arrival_timezone", "Arrival IANA timezone")}<div className="grid grid-cols-2 gap-2">{field("cabin", "Cabin")}{field("booking_class", "RBD")}</div><div className="grid grid-cols-2 gap-2">{field("fare_family_code", "Fare brand")}{field("equipment_code", "Equipment")}</div></div><button type="button" onClick={onAdd} className="mt-3 primary-button"><Plus className="h-4 w-4" />Add flight draft</button></div>
}

function SegmentRow({ segment, checked, onCheck, onSave, onDuplicate, onArchive, onMove, onError }) {
  const [edit, setEdit] = useState({ ...segment })
  useEffect(() => setEdit({ ...segment }), [segment.updated_at])
  const cell = (key, width = "w-24") => <input value={edit[key] || ""} onChange={(event) => setEdit({ ...edit, [key]: event.target.value })} className={`rounded border border-slate-300 px-2 py-1.5 text-sm ${width}`} />
  return <tr className={segment.blocking_errors?.length ? "bg-red-50/50" : "bg-white"}><td className="px-2 py-3"><input type="checkbox" checked={checked} onChange={(event) => onCheck(event.target.checked)} /></td><td className="px-2 py-3 font-semibold">{segment.sequence}</td><td className="px-2 py-3"><div className="flex gap-1">{cell("marketing_carrier_code", "w-14")}{cell("marketing_flight_number", "w-20")}</div></td><td className="px-2 py-3">{cell("operating_carrier_code", "w-16")}</td><td className="px-2 py-3"><div className="flex gap-1">{cell("departure_airport_code", "w-16")}<input type="datetime-local" value={toLocalInput(edit.departure_local_datetime)} onChange={(event) => setEdit({ ...edit, departure_local_datetime: event.target.value })} className="rounded border border-slate-300 px-2 py-1.5 text-sm w-44" /></div><div className="mt-1">{cell("departure_timezone", "w-44")}</div></td><td className="px-2 py-3"><div className="flex gap-1">{cell("arrival_airport_code", "w-16")}<input type="datetime-local" value={toLocalInput(edit.arrival_local_datetime)} onChange={(event) => setEdit({ ...edit, arrival_local_datetime: event.target.value })} className="rounded border border-slate-300 px-2 py-1.5 text-sm w-44" /></div><div className="mt-1">{cell("arrival_timezone", "w-44")}</div></td><td className="px-2 py-3 whitespace-nowrap">{duration(segment.scheduled_duration_minutes)}</td><td className="px-2 py-3"><div className="flex gap-1">{cell("cabin", "w-20")}{cell("booking_class", "w-14")}</div></td><td className="px-2 py-3"><p className="font-semibold">{segment.completeness_score || 0}%</p><p className="text-xs text-slate-500">{segment.blocking_errors?.length || 0} blocking · {segment.warnings?.length || 0} warnings</p></td><td className="px-2 py-3"><div className="flex gap-1"><button type="button" title="Save segment" onClick={() => onSave(segment, editablePayload(edit)).catch(fail(onError))} className="icon-button"><Save className="h-4 w-4" /></button><button type="button" title="Duplicate row" onClick={() => onDuplicate(segment).catch(fail(onError))} className="icon-button"><Copy className="h-4 w-4" /></button><button type="button" title="Move up" onClick={() => onMove(segment.id, -1).catch(fail(onError))} className="icon-button"><ArrowUp className="h-4 w-4" /></button><button type="button" title="Move down" onClick={() => onMove(segment.id, 1).catch(fail(onError))} className="icon-button"><ArrowDown className="h-4 w-4" /></button><button type="button" title="Archive draft" onClick={() => onArchive(segment.id).catch(fail(onError))} className="icon-button"><Archive className="h-4 w-4" /></button></div></td></tr>
}

function ValidationPanel({ validations }) {
  const groups = [
    ["Blocking errors", validations.filter((item) => item.blocking)],
    ["Schedule warnings", validations.filter((item) => item.category === "schedule" && !item.blocking)],
    ["Missing information", validations.filter((item) => item.category === "missing_information" && !item.blocking)],
    ["Operational review", validations.filter((item) => item.category === "operational_review" || item.category === "carrier")],
  ]
  return <section><div className="flex items-center gap-2"><ShieldAlert className="h-4 w-4 text-amber-700" /><h3 className="text-lg font-semibold text-slate-950">Validation</h3></div><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{groups.map(([label, items]) => <div className="py-3" key={label}><div className="flex justify-between"><p className="font-semibold text-slate-900">{label}</p><span className="text-sm text-slate-500">{items.length}</span></div>{items.slice(0, 5).map((item) => <p key={item.id} className={`mt-2 text-sm ${item.blocking ? "text-red-700" : "text-slate-600"}`}>{item.message}</p>)}</div>)}</div></section>
}

function ProvenancePanel({ provenance, corrections }) {
  return <section><h3 className="text-lg font-semibold text-slate-950">Provenance and corrections</h3><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{provenance.slice(0, 7).map((item) => <div key={item.id} className="py-3"><div className="flex justify-between gap-3"><p className="font-semibold text-slate-900">{title(item.field_name)}</p><Status value={item.value_status} /></div><p className="mt-1 text-xs text-slate-500">{title(item.source_type)} · confidence {item.parser_confidence == null ? "not supplied" : `${Math.round(item.parser_confidence * 100)}%`} · {dateTime(item.changed_at)}</p></div>)}{!provenance.length ? <p className="py-4 text-sm text-slate-500">Provenance appears as values are imported, enriched, or confirmed.</p> : null}</div><p className="mt-3 text-sm text-slate-600">{corrections.length} correction-history entries retained.</p></section>
}

function Metric({ label, value, warning, danger }) { return <div className={`rounded-md border p-3 ${danger ? "border-red-200 bg-red-50" : warning ? "border-amber-200 bg-amber-50" : "border-slate-200 bg-white"}`}><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-1 text-xl font-semibold text-slate-950">{value}</p></div> }
function Status({ value }) { return <span className="inline-flex h-fit rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700 ring-1 ring-blue-200">{title(value)}</span> }
function Select({ value, onChange, options }) { return <select value={value} onChange={(event) => onChange(event.target.value)} className="field">{options.map((item) => <option value={item} key={item}>{title(item)}</option>)}</select> }
function clean(value) { return Object.fromEntries(Object.entries(value).filter(([, item]) => item !== "" && item != null)) }
function editablePayload(value) { return clean(Object.fromEntries(Object.keys(emptyFlight).map((key) => [key, value[key]]))) }
function title(value) { return String(value || "Unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) }
function dateTime(value) { return value ? new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "Unknown" }
function localTime(value) { return value ? new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "Schedule unresolved" }
function duration(minutes) { if (minutes == null) return "Unresolved"; const hours = Math.floor(minutes / 60); const rest = minutes % 60; return hours ? `${hours}h ${rest}m` : `${rest}m` }
function toLocalInput(value) { return value ? String(value).slice(0, 16) : "" }
function fail(setError) { return (error) => setError(error.message) }
function connectionPreview(segments) { return segments.map((item, index) => { const next = segments[index + 1]; if (!next) return null; const end = item.arrival_utc ? new Date(item.arrival_utc) : null; const start = next.departure_utc ? new Date(next.departure_utc) : null; return { minutes: end && start ? Math.round((start - end) / 60000) : null, gap: item.arrival_airport_code && next.departure_airport_code && item.arrival_airport_code !== next.departure_airport_code } }) }
