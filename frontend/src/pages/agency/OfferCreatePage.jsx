import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function OfferCreatePage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ request_id: "", title: "", currency: "EUR", expires_at: "" })
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const requests = await apiGet(`/api/agencies/${context.agency.id}/requests`)
      const queryRequestId = new URLSearchParams(window.location.search).get("requestId") || ""
      const request = requests.items.find((item) => item.id === queryRequestId)
      setState({ ...context, requests: requests.items })
      setForm((current) => ({
        ...current,
        request_id: queryRequestId,
        title: request ? `Offer for ${request.title}` : "",
      }))
    }
    load().catch((err) => setError(err.message))
  }, [])

  function setField(name, value) {
    const updates = { [name]: value }
    if (name === "request_id") {
      const request = state.requests.find((item) => item.id === value)
      updates.title = request ? `Offer for ${request.title}` : form.title
    }
    setForm((current) => ({ ...current, ...updates }))
  }

  async function submit(event) {
    event.preventDefault()
    setError("")
    const payload = {
      request_id: form.request_id,
      title: form.title,
      currency: form.currency,
      expires_at: form.expires_at ? new Date(`${form.expires_at}T23:59:59Z`).toISOString() : null,
    }
    try {
      const result = await apiPost(`/api/agencies/${state.agency.id}/offer-workspaces`, payload)
      window.location.href = `/agency/offers/${result.workspace.id}/builder`
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="mx-auto max-w-3xl space-y-6">
          <div>
            <a className="text-sm font-medium text-blue-700" href="/agency/offers">Back to offers</a>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Prepare offer</h2>
            <p className="mt-1 text-sm text-slate-600">Start a commercial proposal from a canonical travel request. Options remain editable until the offer is delivered.</p>
          </div>
          <form className="grid gap-4 rounded-lg border border-slate-200 bg-white p-5" onSubmit={submit}>
            <label className="text-sm font-medium text-slate-700">
              Request
              <select required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.request_id} onChange={(event) => setField("request_id", event.target.value)}>
                <option value="">Select request</option>
                {(state?.requests || []).map((request) => <option key={request.id} value={request.id}>{request.request_reference} · {request.title}</option>)}
              </select>
            </label>
            <label className="text-sm font-medium text-slate-700">
              Title
              <input required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.title} onChange={(event) => setField("title", event.target.value)} />
            </label>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="text-sm font-medium text-slate-700">
                Currency
                <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.currency} onChange={(event) => setField("currency", event.target.value)} />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Expires
                <input type="date" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.expires_at} onChange={(event) => setField("expires_at", event.target.value)} />
              </label>
            </div>
            <button className="justify-self-start rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Open offer builder</button>
          </form>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
