import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function OfferCreatePage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ mode: "manual", request_id: "", client_id: "", title: "", source: "manual", currency: "EUR", valid_until: "", client_visible_intro: "", client_visible_terms: "Price must be verified before ticketing." })
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const clients = await apiGet(`/api/agencies/${context.agency.id}/clients`)
      const requests = await apiGet(`/api/agencies/${context.agency.id}/requests`)
      const queryRequestId = new URLSearchParams(window.location.search).get("requestId") || ""
      const request = requests.items.find((item) => item.id === queryRequestId)
      setState({ ...context, clients: clients.items, requests: requests.items })
      setForm((current) => ({
        ...current,
        mode: queryRequestId ? "request" : "manual",
        request_id: queryRequestId,
        client_id: request?.client_id || clients.items[0]?.id || "",
        title: request ? `Offer for ${request.title}` : "",
        source: queryRequestId ? "request" : "manual",
      }))
    }
    load().catch((err) => setError(err.message))
  }, [])

  function setField(name, value) {
    const updates = { [name]: value }
    if (name === "request_id") {
      const request = state.requests.find((item) => item.id === value)
      updates.client_id = request?.client_id || form.client_id
      updates.title = request ? `Offer for ${request.title}` : form.title
    }
    setForm((current) => ({ ...current, ...updates }))
  }

  async function submit(event) {
    event.preventDefault()
    const common = {
      title: form.title,
      currency: form.currency,
      valid_until: form.valid_until || undefined,
      client_visible_intro: form.client_visible_intro || undefined,
      client_visible_terms: form.client_visible_terms || undefined,
    }
    const result = form.mode === "request"
      ? await apiPost(`/api/agencies/${state.agency.id}/requests/${form.request_id}/create-offer`, common)
      : await apiPost(`/api/agencies/${state.agency.id}/offers`, { ...common, client_id: form.client_id, source: form.source })
    window.location.href = `/agency/offers/${result.offer.id}`
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="mx-auto max-w-3xl space-y-6">
          <div>
            <a className="text-sm font-medium text-blue-700" href="/agency/offers">Back to offers</a>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Create manual offer</h2>
            <p className="mt-1 text-sm text-slate-600">Create a proposal from a request or directly from a client. Fare search is manual and external.</p>
          </div>
          <form className="grid gap-4 rounded-lg border border-slate-200 bg-white p-5" onSubmit={submit}>
            <label className="text-sm font-medium text-slate-700">
              Source
              <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.mode} onChange={(event) => setField("mode", event.target.value)}>
                <option value="manual">Manual / client profile</option>
                <option value="request">From request</option>
              </select>
            </label>
            {form.mode === "request" ? (
              <label className="text-sm font-medium text-slate-700">
                Request
                <select required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.request_id} onChange={(event) => setField("request_id", event.target.value)}>
                  <option value="">Select request</option>
                  {state.requests.map((request) => <option key={request.id} value={request.id}>{request.request_reference} · {request.title}</option>)}
                </select>
              </label>
            ) : (
              <label className="text-sm font-medium text-slate-700">
                Client
                <select required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.client_id} onChange={(event) => setField("client_id", event.target.value)}>
                  {state.clients.map((client) => <option key={client.id} value={client.id}>{client.display_name}</option>)}
                </select>
              </label>
            )}
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
                Valid until
                <input type="date" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={form.valid_until} onChange={(event) => setField("valid_until", event.target.value)} />
              </label>
            </div>
            <label className="text-sm font-medium text-slate-700">
              Client intro
              <textarea className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" rows="3" value={form.client_visible_intro} onChange={(event) => setField("client_visible_intro", event.target.value)} />
            </label>
            <label className="text-sm font-medium text-slate-700">
              Client terms
              <textarea className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" rows="2" value={form.client_visible_terms} onChange={(event) => setField("client_visible_terms", event.target.value)} />
            </label>
            <button className="justify-self-start rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit">Save draft</button>
          </form>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
