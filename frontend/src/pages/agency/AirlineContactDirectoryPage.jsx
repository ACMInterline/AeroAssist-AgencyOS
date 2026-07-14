import { useEffect, useState } from "react"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import Clock3 from "lucide-react/dist/esm/icons/clock-3.js"
import Search from "lucide-react/dist/esm/icons/search.js"
import History from "lucide-react/dist/esm/icons/history.js"
import TriangleAlert from "lucide-react/dist/esm/icons/triangle-alert.js"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { loadCurrentAgency } from "../../lib/agency"
import { apiGet, apiPost } from "../../lib/api"

function Metric({ label, value }) {
  return <div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value || 0}</p></div>
}

function Status({ children }) {
  return <span className="inline-flex rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{String(children || "unknown").replaceAll("_", " ")}</span>
}

export default function AirlineContactDirectoryPage() {
  const [state, setState] = useState(null)
  const [finder, setFinder] = useState({ airline_code: "", desk_type: "general_agency_support", country: "", airport: "", service_code: "" })
  const [result, setResult] = useState(null)
  const [templateType, setTemplateType] = useState("policy_clarification")
  const [composed, setComposed] = useState(null)
  const [interactionSummary, setInteractionSummary] = useState("")
  const [notice, setNotice] = useState("")
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const payload = await apiGet(`/api/agencies/${context.agency.id}/airline-contact-directory`)
    setState({ ...context, ...payload })
  }

  async function findDesk(event) {
    event.preventDefault()
    setError("")
    setNotice("")
    try {
      const payload = await apiPost(`/api/agencies/${state.agency.id}/airline-contact-directory/find-desk`, finder)
      setResult(payload)
    } catch (err) { setError(err.message) }
  }

  async function compose(event) {
    event.preventDefault()
    setError("")
    try {
      const payload = await apiPost(`/api/agencies/${state.agency.id}/airline-contact-directory/compose`, {
        airline_code: finder.airline_code,
        template_type: templateType,
        desk_type: finder.desk_type,
        contact_directory_entry_id: result?.selected?.contact?.id,
        values: { airline_code: finder.airline_code, airport: finder.airport, service_code: finder.service_code },
      })
      setComposed(payload)
    } catch (err) { setError(err.message) }
  }

  async function logInteraction(event) {
    event.preventDefault()
    setError("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/airline-contact-directory/interactions`, {
        airline_code: finder.airline_code,
        contact_directory_entry_id: result?.selected?.contact?.id,
        contact_channel_id: result?.selected?.channels?.[0]?.id,
        communication_template_id: composed?.template?.id,
        desk_type: finder.desk_type,
        channel_type: result?.selected?.channels?.[0]?.channel_type,
        interaction_summary: interactionSummary,
        internal_instruction_snapshot: composed?.messages?.internal_instructions,
        supplier_message_snapshot: composed?.messages?.supplier_facing_message,
        client_status_message_snapshot: composed?.messages?.client_facing_status_message,
        required_information_snapshot: composed?.required_information || [],
        sent_externally: false,
      })
      setInteractionSummary("")
      setNotice("Interaction history recorded. AeroAssist did not send a message.")
      await load()
    } catch (err) { setError(err.message) }
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  const selected = result?.selected

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header>
            <p className="text-sm font-semibold uppercase text-blue-700">Published operational contact guidance</p>
            <h1 className="mt-1 text-2xl font-semibold text-slate-950">Airline Contact Directory</h1>
            <p className="mt-1 max-w-5xl text-sm text-slate-600">Find the governed desk, channel, operating hours, required information, and escalation path for an airline interaction.</p>
            <p className="mt-2 text-sm font-medium text-amber-800">Advisory only. Confirm stale or unverified records before use. AeroAssist records interaction history but never sends supplier or client messages from this workspace.</p>
          </header>

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5"><Metric label="Airlines" value={state?.summary?.airline_count} /><Metric label="Contacts" value={state?.summary?.contact_count} /><Metric label="Channels" value={state?.summary?.channel_count} /><Metric label="Templates" value={state?.summary?.template_count} /><Metric label="Needs review" value={state?.summary?.stale_contact_count} /></section>

          <form className="grid gap-3 border-y border-slate-200 py-4 sm:grid-cols-2 lg:grid-cols-6" onSubmit={findDesk}>
            <input required maxLength="3" className="rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" placeholder="Airline code" value={finder.airline_code} onChange={(event) => setFinder({ ...finder, airline_code: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={finder.desk_type} onChange={(event) => setFinder({ ...finder, desk_type: event.target.value })}>{state?.filters?.desk_types?.map((item) => <option value={item} key={item}>{item.replaceAll("_", " ")}</option>)}</select>
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" placeholder="Country / market" value={finder.country} onChange={(event) => setFinder({ ...finder, country: event.target.value })} />
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" placeholder="Airport" value={finder.airport} onChange={(event) => setFinder({ ...finder, airport: event.target.value })} />
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" placeholder="Service code" value={finder.service_code} onChange={(event) => setFinder({ ...finder, service_code: event.target.value })} />
            <button className="inline-flex items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white"><Search className="h-4 w-4" />Find desk</button>
          </form>

          {selected ? <section className="grid gap-6 lg:grid-cols-[1.35fr_1fr]"><div><div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-lg font-semibold text-slate-950">{selected.contact.contact_name}</h2><p className="text-sm text-slate-500">{selected.contact.airline_code} · {selected.contact.desk_type?.replaceAll("_", " ")}</p></div><Status>{selected.contact.verification_status}</Status></div><div className="mt-4 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[650px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Channel</th><th className="px-3 py-2">Contact</th><th className="px-3 py-2">Language</th><th className="px-3 py-2">Agency ID</th></tr></thead><tbody>{selected.channels?.map((item) => <tr className="border-t border-slate-200" key={item.id}><td className="px-3 py-3 font-semibold">{item.channel_type?.replaceAll("_", " ")}</td><td className="px-3 py-3">{item.contact_value || item.phone_number || item.public_url || item.channel_reference_value || "Reference required"}</td><td className="px-3 py-3">{item.language_codes?.join(", ") || "Unknown"}</td><td className="px-3 py-3">{item.agency_identifier_required ? "Required" : "Not recorded"}</td></tr>)}</tbody></table></div></div><aside className="space-y-4"><div className="border-y border-slate-200 py-4"><div className="flex items-center gap-2"><Clock3 className="h-4 w-4 text-blue-600" /><h2 className="font-semibold text-slate-950">Operating hours</h2></div><p className="mt-2 text-sm text-slate-600">{selected.availability?.reason}</p><p className="mt-2"><Status>{selected.availability?.current_status}</Status></p><p className="mt-2 text-xs text-slate-500">{selected.availability?.timezone || "Timezone unknown"} · {selected.availability?.local_time ? new Date(selected.availability.local_time).toLocaleString() : "Current time unavailable"}</p></div><div className="border-b border-slate-200 pb-4"><h2 className="font-semibold text-slate-950">Required information</h2><ul className="mt-2 space-y-1 text-sm text-slate-600">{selected.contact.required_information?.map((item) => <li key={item}>• {item}</li>)}{!selected.contact.required_information?.length ? <li>No governed checklist recorded.</li> : null}</ul></div><div><h2 className="font-semibold text-slate-950">Escalation recommendation</h2><p className="mt-2 text-sm text-slate-600">{selected.escalation_recommendation?.path_name || "No published escalation path."}</p><p className="mt-1 text-xs text-slate-500">Manual only; no automatic escalation.</p></div></aside></section> : null}

          {result?.warnings?.length ? <section className="space-y-2">{result.warnings.map((item) => <div className="flex gap-2 border-y border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900" key={item}><TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />{item}</div>)}</section> : null}

          {selected ? <section className="grid gap-6 lg:grid-cols-2"><form onSubmit={compose}><h2 className="font-semibold text-slate-950">Communication template</h2><div className="mt-3 flex gap-2"><select className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" value={templateType} onChange={(event) => setTemplateType(event.target.value)}>{state?.filters?.template_types?.map((item) => <option value={item} key={item}>{item.replaceAll("_", " ")}</option>)}</select><button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Prepare</button></div>{composed ? <div className="mt-4 space-y-4 border-y border-slate-200 py-4 text-sm"><div><p className="text-xs font-semibold uppercase text-slate-500">Internal instruction</p><p className="mt-1 text-slate-600">{composed.messages?.internal_instructions || "None"}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Supplier-facing message</p><p className="mt-1 whitespace-pre-wrap text-slate-600">{composed.messages?.supplier_facing_message}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Client-facing status</p><p className="mt-1 text-slate-600">{composed.messages?.client_facing_status_message || "None"}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Checklist</p><p className="mt-1 text-slate-600">{composed.required_information?.join(", ") || "No required information recorded"}</p>{composed.missing_information?.length ? <p className="mt-2 text-amber-800">Missing: {composed.missing_information.join(", ")}</p> : <p className="mt-2 inline-flex items-center gap-1 text-emerald-700"><CheckCircle2 className="h-4 w-4" />Required information supplied</p>}</div></div> : null}</form><form onSubmit={logInteraction}><h2 className="font-semibold text-slate-950">Interaction history</h2><p className="mt-2 text-sm text-slate-600">Record a supplier interaction completed outside AeroAssist and preserve its operational links.</p><textarea required rows="6" className="mt-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="What happened, what response is expected, and what needs follow-up?" value={interactionSummary} onChange={(event) => setInteractionSummary(event.target.value)} /><button className="mt-2 inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700"><History className="h-4 w-4" />Record interaction</button>{notice ? <p className="mt-3 text-sm font-medium text-emerald-700">{notice}</p> : null}</form></section> : null}

          <section><h2 className="font-semibold text-slate-950">Recent interaction history</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.interactions?.slice(0, 8).map((item) => <div className="grid gap-2 py-3 text-sm sm:grid-cols-[110px_170px_1fr_160px]" key={item.id}><p className="font-semibold">{item.airline_code}</p><p>{item.desk_type?.replaceAll("_", " ") || "Supplier contact"}</p><p className="text-slate-600">{item.interaction_summary}</p><p className="text-slate-500">{item.occurred_at ? new Date(item.occurred_at).toLocaleString() : "Time unknown"}</p></div>)}</div></section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
