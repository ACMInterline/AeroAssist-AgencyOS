import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function RequestIntakeDetailPage({ intakeId }) {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ priority: "normal", assigned_to: "", triage_notes: "", internal_notes: "", client_visible_notes: "" })
  const [actionReason, setActionReason] = useState("")
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const detail = await apiGet(`/api/request-intakes/${intakeId}`)
    setState({ ...context, ...detail })
    setForm({
      priority: detail.intake.priority || "normal",
      assigned_to: detail.intake.assigned_to || "",
      triage_notes: detail.intake.triage_notes || "",
      internal_notes: detail.intake.internal_notes || "",
      client_visible_notes: detail.intake.client_visible_notes || "",
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [intakeId])

  async function saveTriage(event) {
    event.preventDefault()
    setError("")
    try {
      await apiPatch(`/api/request-intakes/${intakeId}/triage`, {
        priority: form.priority,
        assigned_to: form.assigned_to || undefined,
        triage_notes: form.triage_notes || undefined,
        internal_notes: form.internal_notes || undefined,
        client_visible_notes: form.client_visible_notes || undefined,
      })
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function runAction(action) {
    setError("")
    try {
      await apiPost(`/api/request-intakes/${intakeId}/${action}`, { reason: actionReason || undefined })
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function convert() {
    setError("")
    try {
      await apiPost(`/api/request-intakes/${intakeId}/convert`)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const intake = state?.intake
  const contact = intake?.contact_snapshot || {}
  const travel = intake?.travel_summary || {}
  const services = intake?.service_summary || {}
  const convertedId = state?.converted_request?.id || intake?.converted_request_id

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={!state ? error : ""}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <a className="text-sm font-medium text-blue-700" href="/agency/request-intakes">Back to intake queue</a>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{intake?.reference_code}</p>
              <h2 className="text-2xl font-semibold text-slate-950">{contact.name || "Request intake"}</h2>
              <p className="mt-1 text-sm text-slate-600">Status: {intake?.status} · Source: {intake?.source?.replaceAll("_", " ")}</p>
              {intake?.source === "agency_website" ? <p className="mt-2 rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">Website CMS form · {intake.source_site_slug}{intake.source_page_slug ? `/${intake.source_page_slug}` : ""}</p> : null}
            </div>
            <div className="flex flex-wrap gap-2">
              {convertedId ? <a className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" href={`/agency/requests/${convertedId}`}>Open request</a> : <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="button" onClick={convert}>Convert to request</button>}
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => runAction("reject")}>Reject</button>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => runAction("archive")}>Archive</button>
            </div>
          </div>
          {error ? <p className="rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
          <section className="grid gap-4 lg:grid-cols-3">
            <InfoCard title="Contact" rows={[["Name", contact.name], ["Email", contact.email || "Not provided"], ["Phone", contact.phone || "Not provided"], ["Organization", contact.organization || "None"]]} />
            <InfoCard title="Travel" rows={[["Origin", travel.origin || "Not set"], ["Destination", travel.destination || "Not set"], ["Departure", travel.departure_date || "Not set"], ["Return", travel.return_date || "Not set"], ["Passengers", travel.passenger_count || 1], ["Notes", travel.itinerary_notes || "None"]]} />
            <InfoCard title="Services" rows={[["Selected", (services.selected_service_categories || []).join(", ") || "None"], ["Mobility", yesNo(services.mobility_assistance)], ["Medical", yesNo(services.medical_travel)], ["Pet travel", yesNo(services.pet_travel)], ["Special baggage", yesNo(services.special_baggage)], ["Other", services.other_details || yesNo(services.other)]]} />
            {intake?.source === "agency_website" ? <InfoCard title="Website source" rows={[["Site slug", intake.source_site_slug || "Not set"], ["Page slug", intake.source_page_slug || "Not set"], ["Website profile", intake.source_website_profile_id || "Not set"], ["Page id", intake.source_website_page_id || "Not set"]]} /> : null}
          </section>
          <form className="space-y-4 rounded-lg border border-slate-200 bg-white p-5" onSubmit={saveTriage}>
            <h3 className="font-semibold text-slate-950">Triage</h3>
            <div className="grid gap-3 md:grid-cols-2">
              <label className="text-sm font-medium text-slate-700">Priority<select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value })}>{["low", "normal", "high", "urgent"].map((priority) => <option key={priority} value={priority}>{priority}</option>)}</select></label>
              <Field label="Assigned user id" value={form.assigned_to} onChange={(value) => setForm({ ...form, assigned_to: value })} />
            </div>
            <TextArea label="Triage notes" value={form.triage_notes} onChange={(value) => setForm({ ...form, triage_notes: value })} />
            <TextArea label="Internal notes" value={form.internal_notes} onChange={(value) => setForm({ ...form, internal_notes: value })} />
            <TextArea label="Client-visible notes" value={form.client_visible_notes} onChange={(value) => setForm({ ...form, client_visible_notes: value })} />
            <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Save triage</button>
          </form>
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Action note</h3>
            <TextArea label="Reason for reject/archive/duplicate" value={actionReason} onChange={setActionReason} />
            <button className="mt-3 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => runAction("mark-duplicate")}>Mark duplicate</button>
          </section>
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Payload preview</h3>
            <pre className="mt-3 max-h-80 overflow-auto rounded-md bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(intake?.canonical_payload || {}, null, 2)}</pre>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function yesNo(value) {
  return value ? "Yes" : "No"
}

function Field({ label, value, onChange }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function TextArea({ label, value, onChange }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<textarea className="mt-2 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} /></label>
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
