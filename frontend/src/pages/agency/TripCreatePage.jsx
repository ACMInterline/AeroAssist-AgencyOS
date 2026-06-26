import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function TripCreatePage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ trip_title: "", trip_status: "draft", trip_type: "unknown", route_summary: "", date_summary: "", service_summary: "", operational_summary: "", internal_notes: "", client_visible_notes: "" })
  const [error, setError] = useState("")

  useEffect(() => {
    loadCurrentAgency().then(setState).catch((err) => setError(err.message))
  }, [])

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function submit(event) {
    event.preventDefault()
    const payload = Object.fromEntries(Object.entries(form).filter(([, value]) => value !== ""))
    const result = await apiPost(`/api/agencies/${state.agency.id}/trips`, payload)
    window.location.href = `/agency/trips/${result.trip.id}`
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <form className="space-y-6" onSubmit={submit}>
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <a className="text-sm font-medium text-blue-700" href="/agency/trips">Back to trips</a>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Create trip dossier</h2>
            <p className="mt-1 text-sm text-slate-600">Manual trip dossiers can be linked to requests later.</p>
          </div>
          <section className="grid gap-4 rounded-lg border border-slate-200 bg-white p-5 md:grid-cols-2">
            <Field label="Trip title" required value={form.trip_title} onChange={(value) => setField("trip_title", value)} />
            <Select label="Status" value={form.trip_status} onChange={(value) => setField("trip_status", value)} options={["draft", "planning", "quoted", "booked", "ticketed", "in_travel", "completed", "cancelled", "archived"]} />
            <Select label="Trip type" value={form.trip_type} onChange={(value) => setField("trip_type", value)} options={["one_way", "round_trip", "multi_city", "open_jaw", "complex", "unknown"]} />
            <Field label="Route summary" value={form.route_summary} onChange={(value) => setField("route_summary", value)} />
            <Field label="Date summary" value={form.date_summary} onChange={(value) => setField("date_summary", value)} />
            <Field label="Service summary" value={form.service_summary} onChange={(value) => setField("service_summary", value)} />
            <Textarea label="Operational summary" value={form.operational_summary} onChange={(value) => setField("operational_summary", value)} />
            <Textarea label="Internal notes" value={form.internal_notes} onChange={(value) => setField("internal_notes", value)} />
            <Textarea label="Client-visible notes" value={form.client_visible_notes} onChange={(value) => setField("client_visible_notes", value)} />
          </section>
          <div className="flex justify-end">
            <button className="aa-primary-action rounded-md px-4 py-2 text-sm font-semibold" type="submit">Create trip</button>
          </div>
        </form>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Field({ label, value, onChange, required }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<input required={required} className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Textarea({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700 md:col-span-2">{label}<textarea className="min-h-24 rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Select({ label, value, onChange, options }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<select className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option value={option} key={option}>{option.replaceAll("_", " ")}</option>)}</select></label>
}
