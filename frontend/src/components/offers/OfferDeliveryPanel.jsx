import { useEffect, useMemo, useState } from "react"
import Archive from "lucide-react/dist/esm/icons/archive.js"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import Eye from "lucide-react/dist/esm/icons/eye.js"
import FileStack from "lucide-react/dist/esm/icons/files.js"
import History from "lucide-react/dist/esm/icons/history.js"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import Send from "lucide-react/dist/esm/icons/send.js"
import ShieldCheck from "lucide-react/dist/esm/icons/shield-check.js"
import UserPlus from "lucide-react/dist/esm/icons/user-plus.js"
import EmptyState from "../EmptyState"
import { loadCurrentAgency } from "../../lib/agency"
import { apiGet, apiPost, apiPut } from "../../lib/api"

const tabs = ["Overview", "Recipients", "Versions", "Client Preview", "Responses", "Questions", "Next Steps", "History"]

export default function OfferDeliveryPanel({ agency: suppliedAgency, offerId = "", initialDeliveryId = "", clientId = "", passengerId = "", presentationId = "", showHeader = true }) {
  const query = useMemo(() => new URLSearchParams(window.location.search), [])
  const offerContextId = offerId || query.get("offer_id") || ""
  const [agency, setAgency] = useState(suppliedAgency || null)
  const [items, setItems] = useState([])
  const [selectedId, setSelectedId] = useState(initialDeliveryId || query.get("delivery_id") || "")
  const [detail, setDetail] = useState(null)
  const [tab, setTab] = useState("Overview")
  const [source, setSource] = useState({
    presentation_id: presentationId || query.get("presentation_id") || "",
    client_id: clientId || query.get("client_id") || "",
    passenger_ids: passengerId || query.get("passenger_id") ? [passengerId || query.get("passenger_id")] : [],
    expires_at: "",
  })
  const [filters, setFilters] = useState({ status: "", client_id: clientId || query.get("client_id") || "", passenger_id: passengerId || query.get("passenger_id") || "", expiry: "" })
  const [recipient, setRecipient] = useState({ display_name: "", email_reference: "", portal_user_id: "", recipient_role: "client" })
  const [preview, setPreview] = useState(null)
  const [notice, setNotice] = useState("")
  const [error, setError] = useState("")

  async function resolveAgency() {
    if (agency) return agency
    if (suppliedAgency) return suppliedAgency
    return (await loadCurrentAgency()).agency
  }

  async function load(preferredId = selectedId) {
    const currentAgency = await resolveAgency()
    setAgency(currentAgency)
    if (!offerContextId) return
    const params = new URLSearchParams({ include_archived: "true", offer_id: offerContextId, ...clean(filters) })
    const response = await apiGet(`/api/agencies/${currentAgency.id}/offer-deliveries?${params}`)
    const nextId = preferredId || response.items?.[0]?.id || ""
    setItems(response.items || [])
    setSelectedId(nextId)
    if (nextId) await loadDetail(currentAgency.id, nextId)
    else setDetail(null)
  }

  async function loadDetail(agencyId, id) {
    setDetail(await apiGet(`/api/agencies/${agencyId}/offer-deliveries/${id}`))
  }

  useEffect(() => { load().catch(fail(setError)) }, [offerContextId])

  function base(suffix = "") { return `/api/agencies/${agency.id}/offer-deliveries/${selectedId}${suffix}` }
  async function refresh() { await load(selectedId) }

  async function createDelivery() {
    if (!offerContextId) throw new Error("Open delivery from an Offer Workspace.")
    if (!source.client_id.trim()) throw new Error("Select the client record before preparing delivery.")
    const body = clean({ ...source, offer_id: offerContextId })
    const response = source.presentation_id.trim()
      ? await apiPost(`/api/agencies/${agency.id}/offer-deliveries/from-presentation/${source.presentation_id.trim()}`, body)
      : await apiPost(`/api/agencies/${agency.id}/offer-deliveries/from-offer/${offerContextId}`, body)
    setSelectedId(response.delivery.id)
    setNotice("Draft offer delivery prepared from the approved comparison. Nothing was released or sent.")
    await load(response.delivery.id)
  }

  async function saveDelivery(payload) {
    await apiPut(base(), payload)
    setNotice("Offer delivery preparation saved. Released versions remain unchanged.")
    await refresh()
  }

  async function addRecipient() {
    if (!recipient.display_name.trim()) throw new Error("Recipient name is required.")
    await apiPost(base("/recipients"), clean(recipient))
    setRecipient({ display_name: "", email_reference: "", portal_user_id: "", recipient_role: "client" })
    setNotice("Authorized recipient added. No invitation message was sent.")
    await refresh()
  }

  async function validateAndRelease(version) {
    const validation = await apiPost(base(`/versions/${version.id}/validate`), {})
    if (!validation.can_release) throw new Error(validation.findings.map((item) => item.message).join(" "))
    await apiPost(base(`/versions/${version.id}/release`), { release_notes: "Explicit agency release" })
    setNotice(`Version ${version.version_number} released to authorized portal recipients. No external message was sent.`)
    await refresh()
  }

  async function createVersion() {
    await apiPost(base("/versions"), {})
    setNotice("New draft version prepared from the approved offer comparison.")
    await refresh()
  }

  async function showPreview(mode) {
    const response = await apiGet(base(`/preview/${mode}`))
    setPreview(mode === "client" ? response.client_safe_payload : response)
    setTab(mode === "client" ? "Client Preview" : "Overview")
  }

  async function acceptance(action) {
    const response = await apiPost(base(`/acceptance-handoff/${action}`), {})
    setNotice(action === "preview" ? `Acceptance review ${response.can_apply ? "is ready" : "has blockers"}.` : "Selection passed explicitly to Offer Acceptance. No booking was created.")
    await refresh()
  }

  async function document(action) {
    await apiPost(base(`/document-handoff/${action}`), {})
    setNotice(action === "preview" ? "Offer document preparation preview is ready." : "Offer document package linked. No file was sent or publicly shared.")
    await refresh()
  }

  async function revoke() {
    await apiPost(base("/revoke"), {})
    setNotice("Delivery and recipient access revoked without deleting history.")
    await refresh()
  }

  async function archiveDelivery() {
    await apiPost(base("/archive"), {})
    setNotice("Delivery archived without deleting released versions or history.")
    await load("")
  }

  async function supersede(version) {
    const replacement = detail?.versions?.find((item) => item.status === "draft" && item.id !== version.id)
    if (!replacement) throw new Error("Create a replacement draft version before superseding this version.")
    await apiPost(base(`/versions/${version.id}/supersede`), { superseded_by_version_id: replacement.id })
    setNotice(`Version ${version.version_number} superseded by draft version ${replacement.version_number}.`)
    await refresh()
  }

  if (!offerContextId) {
    return <section className="rounded-md border border-amber-200 bg-amber-50 p-5"><h2 className="font-semibold text-amber-950">Offer context required</h2><p className="mt-2 text-sm text-amber-900">Delivery & Responses belongs to an Offer Workspace. Open an offer to prepare or review a client delivery.</p><a className="secondary-button mt-4" href="/agency/offers">Open Offers</a></section>
  }

  const delivery = detail?.delivery
  const latestDraft = detail?.versions?.find((item) => item.status === "draft")
  return <div className="space-y-6">
    {showHeader ? <header className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-sm font-semibold uppercase text-blue-700">Offer Workspace</p><h1 className="mt-2 text-2xl font-semibold text-slate-950">Offer Delivery</h1><p className="mt-1 max-w-4xl text-sm text-slate-600">Release a reviewed offer comparison to authenticated recipients and record their responses. No live fares, provider calls, public links, payments, bookings, tickets, or automatic messages are used.</p></div><button type="button" title="Refresh offer delivery" className="icon-button" onClick={() => refresh().catch(fail(setError))}><RefreshCw className="h-4 w-4" /></button></header> : null}
    {notice ? <div className="border-y border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</div> : null}
    {error ? <div className="border-y border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
    <section className="grid gap-3 border-y border-slate-200 py-4 md:grid-cols-2 xl:grid-cols-[180px_minmax(0,1fr)_minmax(0,1fr)_180px_auto]"><select className="field" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}><option value="">All statuses</option><option value="draft">Draft</option><option value="released">Released</option><option value="viewed">Viewed</option><option value="accepted">Accepted</option><option value="declined">Declined</option><option value="change_requested">Changes requested</option><option value="revoked">Revoked</option></select><input className="field" value={filters.client_id} onChange={(event) => setFilters({ ...filters, client_id: event.target.value })} placeholder="Client reference" /><input className="field" value={filters.passenger_id} onChange={(event) => setFilters({ ...filters, passenger_id: event.target.value })} placeholder="Passenger reference" /><select className="field" value={filters.expiry} onChange={(event) => setFilters({ ...filters, expiry: event.target.value })}><option value="">Any expiry</option><option value="active">Active</option><option value="expired">Expired</option></select><button type="button" className="secondary-button" onClick={() => load("").catch(fail(setError))}><RefreshCw className="h-4 w-4" />Apply</button></section>
    <section className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_220px_auto]"><input className="field" value={source.presentation_id} onChange={(event) => setSource({ ...source, presentation_id: event.target.value })} placeholder="Approved comparison reference (optional)" /><input className="field" value={source.client_id} onChange={(event) => setSource({ ...source, client_id: event.target.value })} placeholder="Client record reference" /><input className="field" type="datetime-local" value={source.expires_at} onChange={(event) => setSource({ ...source, expires_at: event.target.value })} aria-label="Offer expiry" /><button type="button" className="primary-button" onClick={() => createDelivery().catch(fail(setError))}><Plus className="h-4 w-4" />Prepare delivery</button></section>
    <div className="grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]">
      <aside><div className="flex items-center justify-between"><h2 className="font-semibold text-slate-950">Released offers</h2><span className="text-sm text-slate-500">{items.length}</span></div><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{items.map((item) => <button type="button" key={item.id} onClick={() => { setSelectedId(item.id); loadDetail(agency.id, item.id).catch(fail(setError)) }} className={`block w-full px-2 py-3 text-left ${item.id === selectedId ? "bg-blue-50" : "hover:bg-slate-50"}`}><p className="font-semibold text-slate-950">{item.title}</p><p className="mt-1 text-xs text-slate-500">{item.delivery_code} · {title(item.status)}</p><p className="mt-1 text-xs text-slate-500">Expires {dateTime(item.expires_at)}</p></button>)}</div></aside>
      {delivery ? <main className="min-w-0 space-y-6">
        <section className="border-b border-slate-200 pb-5"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase text-slate-500">{delivery.delivery_code} · {title(delivery.status)}</p><h2 className="mt-1 text-xl font-semibold text-slate-950">{delivery.title}</h2><p className="mt-2 text-sm text-slate-600">Offer {short(delivery.offer_id)} · Client {short(delivery.client_id)}</p></div><div className="flex flex-wrap gap-2"><button type="button" className="secondary-button" onClick={() => showPreview("client").catch(fail(setError))}><Eye className="h-4 w-4" />Client Preview</button><button type="button" className="secondary-button" onClick={() => revoke().catch(fail(setError))}><Archive className="h-4 w-4" />Revoke</button><button type="button" className="secondary-button" onClick={() => archiveDelivery().catch(fail(setError))}><Archive className="h-4 w-4" />Archive</button></div></div></section>
        <nav className="flex flex-wrap gap-2" aria-label="Offer delivery views">{tabs.map((item) => <button type="button" className={tab === item ? "primary-button" : "secondary-button"} key={item} onClick={() => setTab(item)}>{item}</button>)}</nav>
        {tab === "Overview" ? <Overview delivery={delivery} detail={detail} save={saveDelivery} internal={() => showPreview("internal")} /> : null}
        {tab === "Recipients" ? <Recipients items={detail.recipients || []} form={recipient} setForm={setRecipient} add={addRecipient} /> : null}
        {tab === "Versions" ? <Versions items={detail.versions || []} create={createVersion} release={validateAndRelease} supersede={supersede} onError={fail(setError)} /> : null}
        {tab === "Client Preview" ? <ClientPreview data={preview || latestDraft?.client_payload || detail.versions?.[0]?.client_payload} /> : null}
        {tab === "Responses" ? <Related title="Client responses" items={[...(detail.interactions || []), ...(detail.decisions || [])]} /> : null}
        {tab === "Questions" ? <Related title="Client questions" items={detail.questions || []} /> : null}
        {tab === "Next Steps" ? <NextSteps acceptance={acceptance} document={document} detail={detail} /> : null}
        {tab === "History" ? <Related title="Offer delivery history" items={detail.audit_events || []} /> : null}
      </main> : <EmptyState title="No delivery selected" body="Prepare delivery from an approved offer comparison and canonical client record." />}
    </div>
  </div>
}

function Overview({ delivery, detail, save, internal }) {
  const [form, setForm] = useState(deliveryForm(delivery))
  useEffect(() => setForm(deliveryForm(delivery)), [delivery.id])
  const stats = [["Versions", detail.versions?.length], ["Recipients", detail.recipients?.length], ["Views", detail.interactions?.length], ["Decisions", detail.decisions?.length], ["Questions", detail.questions?.length], ["Documents", detail.documents?.length]]
  return <div className="space-y-6"><section className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">{stats.map(([label, value]) => <Metric key={label} label={label} value={value || 0} />)}</section><section><div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-blue-700" /><h3 className="text-lg font-semibold text-slate-950">Client wording</h3></div><div className="mt-4 grid gap-3"><input className="field" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /><div className="grid gap-3 sm:grid-cols-2"><label className="text-sm font-medium text-slate-700">Language<input className="field mt-1 w-full" value={form.language_code} onChange={(event) => setForm({ ...form, language_code: event.target.value })} placeholder="en" /></label><label className="text-sm font-medium text-slate-700">Expires at<input className="field mt-1 w-full" type="datetime-local" value={form.expires_at} onChange={(event) => setForm({ ...form, expires_at: event.target.value })} /></label></div><textarea className="field min-h-24" value={form.client_intro} onChange={(event) => setForm({ ...form, client_intro: event.target.value })} placeholder="Client introduction" /><textarea className="field min-h-24" value={form.client_footer} onChange={(event) => setForm({ ...form, client_footer: event.target.value })} placeholder="Contact instructions" /><div className="flex gap-2"><button type="button" className="primary-button" onClick={() => save(form).catch(() => null)}>Save preparation</button><button type="button" className="secondary-button" onClick={() => internal().catch(() => null)}><Eye className="h-4 w-4" />Internal Review</button></div></div></section></div>
}

function Recipients({ items, form, setForm, add }) { return <section><div className="flex items-center gap-2"><UserPlus className="h-5 w-5 text-blue-700" /><h3 className="text-lg font-semibold text-slate-950">Authorized recipients</h3></div><p className="mt-1 text-sm text-slate-600">Recipients must already have an authorized client portal identity. No reusable public link is created.</p><div className="mt-4 grid gap-3 md:grid-cols-4"><input className="field" value={form.display_name} onChange={(event) => setForm({ ...form, display_name: event.target.value })} placeholder="Display name" /><input className="field" value={form.email_reference} onChange={(event) => setForm({ ...form, email_reference: event.target.value })} placeholder="Portal email" /><input className="field" value={form.portal_user_id} onChange={(event) => setForm({ ...form, portal_user_id: event.target.value })} placeholder="Portal account reference" /><button type="button" className="primary-button" onClick={() => add().catch(() => null)}><UserPlus className="h-4 w-4" />Authorize</button></div><div className="mt-5 divide-y divide-slate-200 border-y border-slate-200">{items.map((item) => <div className="grid gap-2 py-3 text-sm md:grid-cols-[1fr_180px_160px]" key={item.id}><span className="font-semibold text-slate-950">{item.display_name}</span><span>{title(item.recipient_role)}</span><span>{title(item.access_status)}</span></div>)}</div></section> }
function Versions({ items, create, release, supersede, onError }) { const hasDraft = items.some((item) => item.status === "draft"); return <section><div className="flex flex-wrap items-center justify-between gap-3"><div><h3 className="text-lg font-semibold text-slate-950">Offer versions</h3><p className="mt-1 text-sm text-slate-600">Changes require a new version; released versions are never edited in place.</p></div><button type="button" className="secondary-button" onClick={() => create().catch(onError)}><Plus className="h-4 w-4" />New draft version</button></div><div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">{items.map((item) => <div className="grid gap-3 py-4 md:grid-cols-[100px_150px_minmax(0,1fr)_auto]" key={item.id}><span className="font-semibold">Version {item.version_number}</span><span>{title(item.status)}</span><span className="text-sm text-slate-500">{item.released_at ? `Released ${dateTime(item.released_at)}` : "Awaiting release"}</span>{item.status === "draft" ? <button type="button" className="primary-button" onClick={() => release(item).catch(onError)}><Send className="h-4 w-4" />Release</button> : item.status === "released" && hasDraft ? <button type="button" className="secondary-button" onClick={() => supersede(item).catch(onError)}>Supersede</button> : <span className="inline-flex items-center gap-1 text-sm text-emerald-700"><CheckCircle2 className="h-4 w-4" />Protected</span>}</div>)}</div></section> }
function ClientPreview({ data }) { if (!data) return <EmptyState title="No client preview" body="Create a draft version to review what the client will see." />; return <section><h3 className="text-lg font-semibold text-slate-950">Client Preview</h3><p className="mt-1 text-sm text-slate-600">Internal notes, costs, margins, evidence, and staff-only information are removed.</p><div className="mt-4 grid gap-4 lg:grid-cols-3">{(data.options || []).map((option) => <article className="rounded-md border border-slate-200 bg-white p-4" key={option.id}><p className="text-xs font-semibold uppercase text-blue-700">{option.option_label}</p><h4 className="mt-1 font-semibold text-slate-950">{option.origin || "Unknown"} to {option.destination || "Unknown"}</h4><p className="mt-2 text-sm text-slate-600">{option.carrier_summary || "Carrier details unknown"}</p><p className="mt-2 text-sm">{duration(option.total_elapsed_minutes)} · {option.stop_count ?? "Unknown"} stops</p></article>)}</div></section> }
function NextSteps({ acceptance, document, detail }) { return <section className="grid gap-6 lg:grid-cols-2"><ActionPanel icon={CheckCircle2} title="Offer Acceptance" body="Review and explicitly apply the selected released option through the existing Offer Acceptance workflow. No booking is created automatically." buttons={[["Review", () => acceptance("preview")], ["Apply", () => acceptance("apply")]]} count={detail.acceptance_handoffs?.length || 0} /><ActionPanel icon={FileStack} title="Offer Documents" body="Prepare documents from the protected released version through the existing Document Workspace. No public link or message is sent." buttons={[["Review", () => document("preview")], ["Prepare", () => document("apply")]]} count={detail.documents?.length || 0} /></section> }
function ActionPanel({ icon: Icon, title: heading, body, buttons, count }) { return <article className="border-y border-slate-200 py-5"><div className="flex items-center gap-2"><Icon className="h-5 w-5 text-blue-700" /><h3 className="font-semibold text-slate-950">{heading}</h3></div><p className="mt-2 text-sm text-slate-600">{body}</p><p className="mt-3 text-sm font-semibold">{count} recorded</p><div className="mt-4 flex gap-2">{buttons.map(([label, action]) => <button type="button" className={label === "Review" ? "secondary-button" : "primary-button"} key={label} onClick={() => action().catch(() => null)}>{label}</button>)}</div></article> }
function Related({ title: heading, items }) { return <section><div className="flex items-center gap-2"><History className="h-5 w-5 text-blue-700" /><h3 className="text-lg font-semibold text-slate-950">{heading}</h3></div>{items.length ? <div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">{items.map((item) => <div className="py-3 text-sm" key={item.id}><p className="font-semibold text-slate-950">{title(item.event_type || item.interaction_type || item.decision_type || item.status)}</p><p className="mt-1 text-slate-600">{item.summary || item.message_text || item.client_comment || "Activity recorded"}</p><p className="mt-1 text-xs text-slate-500">{dateTime(item.occurred_at || item.submitted_at || item.created_at)}</p></div>)}</div> : <EmptyState title="Nothing recorded" body="Client activity will appear after an authorized recipient opens the released offer." />}</section> }
function Metric({ label, value }) { return <div className="rounded-md border border-slate-200 bg-white p-3"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-1 text-xl font-semibold text-slate-950">{value}</p></div> }
function title(value) { return String(value || "Unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) }
function dateTime(value) { return value ? new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "Not set" }
function duration(value) { if (value === null || value === undefined) return "Duration unknown"; return `${Math.floor(value / 60)}h ${value % 60}m` }
function short(value) { return value ? String(value).slice(0, 12) : "Not linked" }
function deliveryForm(delivery) { return { title: delivery.title || "", client_intro: delivery.client_intro || "", client_footer: delivery.client_footer || "", language_code: delivery.language_code || "en", expires_at: delivery.expires_at ? String(delivery.expires_at).slice(0, 16) : "" } }
function clean(value) { return Object.fromEntries(Object.entries(value).filter(([, item]) => item !== "" && item !== null && item !== undefined)) }
function fail(setError) { return (err) => setError(err.message || String(err)) }
