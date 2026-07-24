import { useEffect, useState } from "react"
import Save from "lucide-react/dist/esm/icons/save.js"
import Send from "lucide-react/dist/esm/icons/send.js"
import XCircle from "lucide-react/dist/esm/icons/circle-x.js"
import EmptyState from "../../components/EmptyState"
import RequestStatusBadge from "../../components/RequestStatusBadge"
import { PortalFacts, PortalPageHeader, PortalSection, PortalTimeline, titleCase } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"

export default function PortalRequestDetailPage({ requestId }) {
  const [state, setState] = useState(null)
  const [message, setMessage] = useState("")
  const [draft, setDraft] = useState({ title: "", client_notes: "" })
  const [cancelReason, setCancelReason] = useState("")
  const [notice, setNotice] = useState("")
  const [error, setError] = useState("")

  async function load() {
    const [me, detail] = await Promise.all([apiGet("/api/portal/me"), apiGet(`/api/portal/requests/${requestId}`)])
    setState({ me, ...detail })
    setDraft({ title: detail.request.title || "", client_notes: detail.request.client_notes || "" })
  }
  useEffect(() => { load().catch((err) => setError(err.message)) }, [requestId])

  async function sendMessage(event) {
    event.preventDefault()
    if (!message.trim()) return
    await act(async () => {
      await apiPost(`/api/portal/requests/${requestId}/messages`, { message_text: message.trim(), requires_follow_up: true })
      setMessage("")
      setNotice("Message recorded for your travel agency.")
      await load()
    })
  }

  async function saveDraft(event) {
    event.preventDefault()
    await act(async () => {
      await apiPatch(`/api/portal/requests/${requestId}`, draft)
      setNotice("Draft request updated.")
      await load()
    })
  }

  async function cancel() {
    if (cancelReason.trim().length < 3) {
      setError("Please provide a cancellation reason.")
      return
    }
    await act(async () => {
      await apiPost(`/api/portal/requests/${requestId}/cancel`, { reason: cancelReason.trim() })
      setCancelReason("")
      setNotice("Request cancelled before processing.")
      await load()
    })
  }

  async function act(operation) {
    setError("")
    setNotice("")
    try {
      await operation()
    } catch (err) {
      setError(err.message)
    }
  }

  const request = state?.request || {}
  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-8">
          <PortalPageHeader eyebrow={request.request_reference} title={request.title || "Travel request"} description={request.route_summary || "Route details pending"} status={request.status} backHref="/portal/requests" backLabel="Back to requests" actions={<a className="secondary-button" href="/portal/documents">Documents</a>} />
          {notice ? <p className="border-y border-emerald-200 bg-emerald-50 px-3 py-3 text-sm text-emerald-800" role="status">{notice}</p> : null}
          {error ? <p className="border-y border-rose-200 bg-rose-50 px-3 py-3 text-sm text-rose-800" role="alert">{error}</p> : null}

          <PortalSection title="Request progress">
            <PortalFacts columns={3} rows={[["Status", titleCase(request.status)], ["Priority", titleCase(request.priority)], ["Departure", request.requested_departure_date], ["Return", request.requested_return_date], ["Passengers", request.passenger_count], ["Services", request.service_count]]} />
          </PortalSection>

          {request.editable ? (
            <PortalSection title="Edit draft">
              <form className="grid gap-4" onSubmit={saveDraft}>
                <label className="text-sm font-medium text-slate-700">Request title<input className="field mt-2" maxLength={180} required value={draft.title} onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))} /></label>
                <label className="text-sm font-medium text-slate-700">Notes<textarea className="field mt-2 min-h-28" maxLength={4000} value={draft.client_notes} onChange={(event) => setDraft((current) => ({ ...current, client_notes: event.target.value }))} /></label>
                <button className="primary-button w-fit" type="submit"><Save aria-hidden="true" className="h-4 w-4" />Save draft</button>
              </form>
            </PortalSection>
          ) : null}

          <div className="grid gap-8 lg:grid-cols-2">
            <PortalSection title="Passengers"><Rows items={state?.passengers} empty="No passengers linked." render={(item) => `${item.snapshot_display_name || "Passenger"} · ${titleCase(item.snapshot_passenger_type)} · ${titleCase(item.status)}`} /></PortalSection>
            <PortalSection title="Requested services"><Rows items={state?.services} empty="No services requested." render={(item) => `${item.service_name || item.service_code || "Service"} · ${titleCase(item.status)}`} /></PortalSection>
          </div>

          <PortalSection title="Messages">
            <Rows items={state?.messages} empty="No shared messages." render={(item) => `${item.sender_type === "client" ? "You" : "Agency"} · ${item.message_text}`} />
            <form className="mt-4 flex flex-col gap-3 sm:flex-row" onSubmit={sendMessage}>
              <label className="sr-only" htmlFor="request-message">Message</label>
              <textarea className="field min-h-20 flex-1" id="request-message" maxLength={4000} required value={message} onChange={(event) => setMessage(event.target.value)} />
              <button className="primary-button h-fit" type="submit"><Send aria-hidden="true" className="h-4 w-4" />Send</button>
            </form>
          </PortalSection>

          <PortalSection title="Request timeline"><PortalTimeline items={state?.timeline} /></PortalSection>

          {request.cancellable ? (
            <PortalSection title="Cancel request" description="Cancellation is available only before agency processing starts.">
              <div className="flex flex-col gap-3 sm:flex-row">
                <label className="sr-only" htmlFor="cancel-reason">Cancellation reason</label>
                <input className="field flex-1" id="cancel-reason" maxLength={1000} placeholder="Reason for cancellation" value={cancelReason} onChange={(event) => setCancelReason(event.target.value)} />
                <button className="secondary-button border-rose-300 text-rose-700" type="button" onClick={cancel}><XCircle aria-hidden="true" className="h-4 w-4" />Cancel request</button>
              </div>
            </PortalSection>
          ) : null}
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function Rows({ items, empty, render }) {
  return items?.length ? <div className="divide-y divide-slate-200 border-y border-slate-200">{items.map((item) => <p className="py-3 text-sm text-slate-700" key={item.id}>{render(item)}</p>)}</div> : <EmptyState title={empty} body="Only records shared within this request are shown." />
}
