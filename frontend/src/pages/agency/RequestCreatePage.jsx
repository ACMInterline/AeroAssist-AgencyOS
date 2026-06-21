import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function RequestCreatePage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ client_id: "", title: "", status: "new", source: "staff_created", priority: "normal", route_summary: "", service_summary: "", internal_notes: "", client_visible_notes: "" })
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const clients = await apiGet(`/api/agencies/${context.agency.id}/clients`)
      setState({ ...context, clients: clients.items })
      setForm((current) => ({ ...current, client_id: clients.items[0]?.id || "" }))
    }
    load().catch((err) => setError(err.message))
  }, [])

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function submit(event) {
    event.preventDefault()
    const payload = Object.fromEntries(Object.entries(form).filter(([, value]) => value !== ""))
    const result = await apiPost(`/api/agencies/${state.agency.id}/requests`, payload)
    window.location.href = `/agency/requests/${result.request.id}`
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="mx-auto max-w-3xl space-y-6">
          <div>
            <a className="text-sm font-medium text-blue-700" href="/agency/requests">Back to requests</a>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Create request</h2>
            <p className="mt-1 text-sm text-slate-600">Create an inquiry/case. Passengers, intended segments, and services can be added after saving.</p>
          </div>
          <form className="grid gap-4 rounded-lg border border-slate-200 bg-white p-5" onSubmit={submit}>
            <label className="text-sm font-medium text-slate-700">
              Client
              <select required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.client_id} onChange={(event) => setField("client_id", event.target.value)}>
                {state?.clients?.map((client) => <option key={client.id} value={client.id}>{client.display_name}</option>)}
              </select>
            </label>
            <label className="text-sm font-medium text-slate-700">
              Title
              <input required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.title} onChange={(event) => setField("title", event.target.value)} />
            </label>
            <div className="grid gap-4 md:grid-cols-3">
              <label className="text-sm font-medium text-slate-700">
                Status
                <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.status} onChange={(event) => setField("status", event.target.value)}>
                  <option value="draft">Draft</option>
                  <option value="new">New</option>
                </select>
              </label>
              <label className="text-sm font-medium text-slate-700">
                Source
                <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.source} onChange={(event) => setField("source", event.target.value)}>
                  {["staff_created", "phone", "email", "whatsapp", "walk_in", "website_form", "client_portal", "imported"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
                </select>
              </label>
              <label className="text-sm font-medium text-slate-700">
                Priority
                <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.priority} onChange={(event) => setField("priority", event.target.value)}>
                  {["low", "normal", "high", "urgent"].map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>
            </div>
            <label className="text-sm font-medium text-slate-700">
              Route summary
              <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.route_summary} onChange={(event) => setField("route_summary", event.target.value)} />
            </label>
            <label className="text-sm font-medium text-slate-700">
              Service summary
              <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.service_summary} onChange={(event) => setField("service_summary", event.target.value)} />
            </label>
            <label className="text-sm font-medium text-slate-700">
              Internal notes
              <textarea className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" rows="3" value={form.internal_notes} onChange={(event) => setField("internal_notes", event.target.value)} />
            </label>
            <button className="justify-self-start rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Create request</button>
          </form>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
