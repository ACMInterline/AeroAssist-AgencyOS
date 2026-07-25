import { useEffect, useState } from "react"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalPageHeader, PortalRecordList, formatDateTime } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalCommunicationsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/communications")])
      .then(([me, data]) => setState({ me, items: data.items || [] }))
      .catch((err) => setError(err.message))
  }, [])
  return <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}><ProtectedRoute loading={!state && !error} error={error}><div className="space-y-6"><PortalPageHeader eyebrow="Shared conversations" title="Messages" description="Conversations with your travel agency linked to your travel records." /><PortalRecordList items={state?.items} emptyTitle="No conversations yet" emptyBody="Your agency will open a conversation when an operational response is needed." href={(item) => `/portal/communications/${item.id}`}>{(item) => <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(180px,0.5fr)_auto] sm:items-center"><div><p className="font-semibold text-slate-950">{item.subject || "Conversation"}</p><p className="mt-1 text-sm text-slate-600">{item.message_count || 0} message{item.message_count === 1 ? "" : "s"}</p></div><p className="text-sm text-slate-600">{formatDateTime(item.last_message_at || item.created_at)}</p><PortalStatusBadge status={item.status} /></div>}</PortalRecordList></div></ProtectedRoute></ClientPortalLayout>
}
