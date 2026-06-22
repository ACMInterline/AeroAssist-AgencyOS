import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet, apiPost } from "../../lib/api"

export default function PortalRequestCreatePage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ title: "", route_summary: "", requested_departure_date: "", requested_return_date: "", requested_services: "", client_notes: "", passenger_ids: [] })
  const [error, setError] = useState("")
  const [success, setSuccess] = useState(null)

  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/passengers")])
      .then(([me, passengers]) => setState({ me, passengers: passengers.items }))
      .catch((err) => setError(err.message))
  }, [])

  function togglePassenger(passengerId) {
    setForm((current) => ({
      ...current,
      passenger_ids: current.passenger_ids.includes(passengerId)
        ? current.passenger_ids.filter((id) => id !== passengerId)
        : [...current.passenger_ids, passengerId],
    }))
  }

  async function submit(event) {
    event.preventDefault()
    setError("")
    try {
      const result = await apiPost("/api/portal/requests", {
        title: form.title,
        route_summary: form.route_summary || undefined,
        requested_departure_date: form.requested_departure_date || undefined,
        requested_return_date: form.requested_return_date || undefined,
        passenger_ids: form.passenger_ids,
        requested_services: form.requested_services.split("\n").map((item) => item.trim()).filter(Boolean),
        client_notes: form.client_notes || undefined,
      })
      setSuccess(result.request)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error && !state ? error : ""}>
        <div className="space-y-6">
          <div>
            <a className="text-sm font-medium text-blue-700" href="/portal/requests">Back to requests</a>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">New request</h2>
          </div>
          {success ? (
            <section className="rounded-lg border border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-900">
              Request submitted. <a className="font-semibold underline" href={`/portal/requests/${success.id}`}>Open {success.request_reference}</a>
            </section>
          ) : (
            <form className="space-y-5 rounded-lg border border-slate-200 bg-white p-6" onSubmit={submit}>
              <Field label="Title" value={form.title} onChange={(value) => setForm({ ...form, title: value })} required />
              <Field label="Route summary" value={form.route_summary} onChange={(value) => setForm({ ...form, route_summary: value })} />
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Departure date" type="date" value={form.requested_departure_date} onChange={(value) => setForm({ ...form, requested_departure_date: value })} />
                <Field label="Return date" type="date" value={form.requested_return_date} onChange={(value) => setForm({ ...form, requested_return_date: value })} />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-700">Passengers</p>
                <div className="mt-2 grid gap-2 sm:grid-cols-2">
                  {state.passengers.map((passenger) => (
                    <label className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm" key={passenger.id}>
                      <input type="checkbox" checked={form.passenger_ids.includes(passenger.id)} onChange={() => togglePassenger(passenger.id)} />
                      {passenger.display_name}
                    </label>
                  ))}
                </div>
              </div>
              <TextArea label="Requested services" value={form.requested_services} onChange={(value) => setForm({ ...form, requested_services: value })} />
              <TextArea label="Notes" value={form.client_notes} onChange={(value) => setForm({ ...form, client_notes: value })} />
              {error ? <p className="rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
              <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Submit request</button>
            </form>
          )}
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function Field({ label, value, onChange, type = "text", required = false }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type={type} value={value} required={required} onChange={(event) => onChange(event.target.value)} /></label>
}

function TextArea({ label, value, onChange }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<textarea className="mt-2 min-h-28 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}
