import { useEffect, useState } from "react"
import Send from "lucide-react/dist/esm/icons/send.js"
import { PortalPageHeader, PortalSection, formatDateTime, titleCase } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet, apiPost } from "../../lib/api"

export default function PortalCommunicationDetailPage({ threadId }) {
  const [state, setState] = useState(null)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [sending, setSending] = useState(false)

  async function load() {
    const [me, detail] = await Promise.all([apiGet("/api/portal/me"), apiGet(`/api/portal/communications/${threadId}`)])
    setState({ me, ...detail })
  }
  useEffect(() => { load().catch((err) => setError(err.message)) }, [threadId])

  async function send(event) {
    event.preventDefault()
    if (!message.trim()) return
    setSending(true)
    setError("")
    try {
      await apiPost(`/api/portal/communications/${threadId}/messages`, {
        plain_text: message.trim(),
        idempotency_key: `portal-${threadId}-${Date.now()}`,
      })
      setMessage("")
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setSending(false)
    }
  }

  const thread = state?.thread || {}
  return <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}><ProtectedRoute loading={!state && !error} error={error}><div className="space-y-8"><PortalPageHeader eyebrow="Conversation" title={thread.subject || "Messages"} description={`${thread.message_count || 0} shared messages`} status={thread.status} backHref="/portal/communications" backLabel="Back to messages" /><PortalSection title="Conversation"><div className="space-y-3" aria-live="polite">{state?.messages?.map((item) => <article className={`max-w-3xl border-l-2 px-4 py-3 ${item.sender_type?.includes("portal") ? "ml-auto border-blue-500 bg-blue-50" : "border-slate-300 bg-white"}`} key={item.id}><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-sm font-semibold text-slate-950">{item.sender_display || titleCase(item.sender_type)}</p><time className="text-xs text-slate-500">{formatDateTime(item.created_at)}</time></div><p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{item.plain_text}</p>{item.attachment_ids?.length ? <p className="mt-2 text-xs text-slate-500">{item.attachment_ids.length} attachment reference{item.attachment_ids.length === 1 ? "" : "s"}</p> : null}</article>)}</div></PortalSection>{thread.status !== "closed" ? <form className="border-t border-slate-200 pt-5" onSubmit={send}><label className="text-sm font-semibold text-slate-950" htmlFor="portal-message">Reply</label><textarea className="field mt-2 min-h-28" id="portal-message" maxLength={4000} required value={message} onChange={(event) => setMessage(event.target.value)} />{error ? <p className="mt-2 text-sm text-rose-700" role="alert">{error}</p> : null}<button className="primary-button mt-3" disabled={sending || !message.trim()} type="submit"><Send aria-hidden="true" className="h-4 w-4" />{sending ? "Sending..." : "Send reply"}</button></form> : null}<PortalSection title="Attachments"><div className="divide-y divide-slate-200 border-y border-slate-200">{state?.attachments?.length ? state.attachments.map((item) => item.document_id ? <a className="block py-3 text-sm font-medium text-blue-700" href={`/portal/documents/${item.document_id}`} key={item.id}>{item.title || "Document"}</a> : <p className="py-3 text-sm text-slate-600" key={item.id}>{item.title || "Attachment reference"}</p>) : <p className="py-3 text-sm text-slate-500">No attachments.</p>}</div></PortalSection></div></ProtectedRoute></ClientPortalLayout>
}
