import { useEffect, useState } from "react"
import BellRing from "lucide-react/dist/esm/icons/bell-ring.js"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalPageHeader, PortalPill, PortalRecordList, formatDateTime, titleCase } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalNotificationsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/notifications")])
      .then(([me, data]) => setState({ me, items: data.items || [] }))
      .catch((err) => setError(err.message))
  }, [])
  return <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}><ProtectedRoute loading={!state && !error} error={error}><div className="space-y-6"><PortalPageHeader eyebrow="Attention centre" title="Actions & Notifications" description="Information, deadlines, approvals, and items requiring your attention." /><PortalRecordList items={state?.items} emptyTitle="No notifications" emptyBody="There are no current actions or travel updates." href={(item) => item.timeline_link || "/portal/timeline"}>{(item) => <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(180px,0.5fr)_auto] sm:items-center"><div className="flex min-w-0 gap-3"><BellRing aria-hidden="true" className="mt-1 h-4 w-4 shrink-0 text-blue-700" /><div><p className="font-semibold text-slate-950">{item.title || titleCase(item.type)}</p><p className="mt-1 text-sm text-slate-600">{item.summary}</p></div></div><div className="flex flex-wrap gap-2"><PortalPill tone={item.type === "deadline" || item.type === "warning" ? "amber" : "blue"}>{titleCase(item.type)}</PortalPill><span className="text-sm text-slate-500">{formatDateTime(item.due_at || item.created_at)}</span></div><PortalStatusBadge status={item.status} /></div>}</PortalRecordList></div></ProtectedRoute></ClientPortalLayout>
}
